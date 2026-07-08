# run_sim_summary_report.py

from datetime import datetime
import os

from src.warpsimlab.reports.report_plot_helpers import (
    save_cumulative_operating_balance_report_plot,
    save_income_projection_report_plot,
    save_portfolio_projection_report_plot,
)

from .simulation import run_pipeline
from src.warpsimlab.reports.report_data import SummaryReportData
from src.warpsimlab.reports.summary_report import generate_summary_report


def _get_report_option(report_options, path, default=False):
    target = report_options

    for key in path:
        if not isinstance(target, dict) or key not in target:
            return default
        target = target[key]

    return target


def _as_float(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _array_value(results, key, index, default=0.0):
    values = results.get(key)
    if values is None:
        return default
    try:
        return _as_float(values[index], default=default)
    except (IndexError, TypeError, ValueError):
        return default


def _clamp_index(index, length):
    if length <= 0:
        return 0
    return min(max(int(index), 0), length - 1)


def _rate_fraction_to_percent(value):
    if value is None:
        return None
    return _as_float(value) * 100.0


def _build_report_warnings(report_options):
    return []


def _build_projection_period_label(sim_config):
    start_year = getattr(sim_config, "start_year", None)
    years = getattr(sim_config, "years_to_simulate", None)

    if start_year is None or years is None:
        return "N/A"

    try:
        start_year = int(start_year)
        years = int(years)
        end_year = start_year + years
        return f"{start_year}-{end_year} ({years} Years)"
    except (TypeError, ValueError):
        return "N/A"


def _build_report_basis_label(sim_config):
    plot_mode = getattr(sim_config, "plot_mode", None)

    if plot_mode == "real":
        return "Real Dollars (Inflation Adjusted)"

    if plot_mode == "raw":
        return "Raw Dollars (Future Nominal Values)"

    return "N/A"


def _build_portfolio_milestone(results, index):
    pre_tax_assets = _array_value(results, "pre_tax_assets", index)
    post_tax_assets = _array_value(results, "post_tax_assets", index)
    roth_assets = _array_value(results, "roth_assets", index)
    hsa_assets = _array_value(results, "hsa_assets", index)
    real_estate = _array_value(results, "real_estate", index)

    total_portfolio = (
        pre_tax_assets
        + post_tax_assets
        + roth_assets
        + hsa_assets
    )

    return {
        "Year": _array_value(results, "year", index),
        "Pre-Tax Assets": pre_tax_assets,
        "Post-Tax Assets": post_tax_assets,
        "Roth Assets": roth_assets,
        "HSA Assets": hsa_assets,
        "Total Portfolio": total_portfolio,
        "Real Estate": real_estate,
        "Total Assets": total_portfolio + real_estate,
    }
    

def _build_income_milestone(results, index):
    pensions_and_annuities = (
        _array_value(results, "pensions", index)
        + _array_value(results, "annuities", index)
    )

    return {
        "Year": _array_value(results, "year", index),
        "Wages": _array_value(results, "wages", index),
        "RMD": _array_value(results, "rmd", index),
        "Social Security": _array_value(results, "social_security", index),
        "Pensions & Annuities": pensions_and_annuities,
        "Gross Income": _array_value(results, "gross_income", index),
        "401k or IRA Contribution": _array_value(results, "ira_401k", index),
        "Taxes": _array_value(results, "taxes", index),
        "Tax Bracket": _array_value(results, "tax_bracket", index),
        "Net Income": _array_value(results, "net_income", index),
        "Household Expenses": _array_value(results, "expenses", index),
        "Net Cash Flow": _array_value(results, "net_cash_flow", index),
        "Fund Expenses": _array_value(results, "fund_expenses", index),
    }


def _calculate_retirement_index(results, husband, wife, sim_config):
    years = results.get("year", [])
    length = len(years)

    if getattr(sim_config, "second_person_enabled", False):
        retirement_index = max(
            getattr(husband, "retire_age", 0) - getattr(husband, "age", 0),
            getattr(wife, "retire_age", 0) - getattr(wife, "age", 0),
        )
    else:
        retirement_index = (
            getattr(husband, "retire_age", 0)
            - getattr(husband, "age", 0)
        )

    return _clamp_index(retirement_index, length)


def _build_portfolio_milestones(results, husband, wife, sim_config):
    years = results.get("year", [])
    length = len(years)
    retirement_index = _calculate_retirement_index(results, husband, wife, sim_config)

    return {
        "Start of Simulation": _build_portfolio_milestone(
            results,
            _clamp_index(0, length),
        ),
        "Retirement": _build_portfolio_milestone(
            results,
            retirement_index,
        ),
        "End of Simulation": _build_portfolio_milestone(
            results,
            _clamp_index(length - 1, length),
        ),
    }


def _build_income_milestones(results, husband, wife, sim_config):
    years = results.get("year", [])
    length = len(years)
    retirement_index = _calculate_retirement_index(results, husband, wife, sim_config)

    start_index = 1 if length > 1 else 0
    before_retirement_index = _clamp_index(retirement_index - 1, length)
    after_retirement_index = _clamp_index(retirement_index + 1, length)
    end_index = _clamp_index(length - 1, length)

    return {
        "Start Simulation": _build_income_milestone(results, start_index),
        "Year Before Retirement": _build_income_milestone(
            results,
            before_retirement_index,
        ),
        "Year After Retirement": _build_income_milestone(
            results,
            after_retirement_index,
        ),
        "End Simulation": _build_income_milestone(results, end_index),
    }


def _build_simulation_totals(results, simulated_shortfall_rate=None):
    pre_tax_assets = results.get("pre_tax_assets", [])
    post_tax_assets = results.get("post_tax_assets", [])

    roth_assets = results.get("roth_assets")
    if roth_assets is None:
        roth_assets = [0.0] * len(pre_tax_assets)

    hsa_assets = results.get("hsa_assets")
    if hsa_assets is None:
        hsa_assets = [0.0] * len(pre_tax_assets)

    length = min(
        len(pre_tax_assets),
        len(post_tax_assets),
        len(roth_assets),
        len(hsa_assets),
    )

    total_portfolio = [
        _as_float(pre_tax_assets[i])
        + _as_float(post_tax_assets[i])
        + _as_float(roth_assets[i])
        + _as_float(hsa_assets[i])
        for i in range(length)
    ]

    if total_portfolio:
        portfolio_start = float(total_portfolio[0])
        portfolio_end = float(total_portfolio[-1])
        maximum_portfolio = float(max(total_portfolio))
        minimum_portfolio = float(min(total_portfolio))
    else:
        portfolio_start = 0.0
        portfolio_end = 0.0
        maximum_portfolio = 0.0
        minimum_portfolio = 0.0

    if simulated_shortfall_rate is None:
        simulated_shortfall_rate = results.get("simulated_shortfall_rate")

    return {
        "Portfolio Start": portfolio_start,
        "Portfolio End": portfolio_end,
        "Maximum Portfolio": maximum_portfolio,
        "Minimum Portfolio": minimum_portfolio,
        "Total Income": float(sum(results.get("gross_income", []))),
        "Taxes Paid": float(sum(results.get("taxes", []))),
        "Household Expenses": float(sum(results.get("expenses", []))),
        "Net Cash Flow": float(sum(results.get("net_cash_flow", []))),
        "Fund Expenses": float(sum(results.get("fund_expenses", []))),
        "Simulated Shortfall Rate": simulated_shortfall_rate,
    }


def _build_simulation_snapshot(sim_config):
    projection_end_year = (
        int(getattr(sim_config, "start_year", 0))
        + int(getattr(sim_config, "years_to_simulate", 0))
    )

    return {
        "Start Year": getattr(sim_config, "start_year", None),
        "Years Simulated": getattr(sim_config, "years_to_simulate", None),
        "Projection End Year": projection_end_year,
        "Inflation Rate": _rate_fraction_to_percent(
            getattr(sim_config, "inflation_rate", None)
        ),
        "Plot Mode": getattr(sim_config, "plot_mode", None),
        "Second Person Enabled": getattr(sim_config, "second_person_enabled", None),
        "Taxes Enabled": getattr(sim_config, "calculate_income_taxes", None),
        "Payroll Taxes Enabled": getattr(sim_config, "calculate_payroll_taxes", None),
        "State Taxes Enabled": getattr(sim_config, "calculate_state_taxes", None),
        "State of Residence": getattr(sim_config, "state_of_residence", None),
        "Withdrawal Strategy": getattr(sim_config, "retirement_withdraw_mode", None),
        "Rebalance Strategy": getattr(sim_config, "sim_rebalance", None),
        "Fund Expenses Enabled": getattr(sim_config, "use_fund_expenses", None),
    }


def _value_or_na(value):
    return "N/A" if value is None else value


def _friendly_label(value):
    labels = {
        "pathBasedAnnualSampling": "Path-Based Annual Sampling",
        "rollingHistoricalWindows": "Rolling Historical Windows",
        "rolling_overlapping_all": "Rolling Overlapping Windows",
        "maintain-current-allocation": "Maintain Current Allocation",
        "none": "None",
        "None": "None",
        "Off": "Off",
    }
    return labels.get(value, value)


def _portfolio_amount(portfolio, *attrs):
    if portfolio is None:
        return 0.0

    total = 0.0
    for attr in attrs:
        total += _as_float(getattr(portfolio, attr, 0.0))
    return total


def _portfolio_value(portfolio, attr):
    if portfolio is None:
        return 0.0

    return _as_float(getattr(portfolio, attr, 0.0))


def _portfolio_total(portfolio, attrs):
    return sum(_portfolio_value(portfolio, attr) for attr in attrs)


def _build_portfolio_inputs(husband_portfolio, wife_portfolio, sim_config):
    show_wife = (
        getattr(sim_config, "second_person_enabled", False)
        and wife_portfolio is not None
    )

    portfolio_columns = ["Asset / Account Type", "Husband"]
    if show_wife:
        portfolio_columns.append("Wife")
    portfolio_columns.append("Total")

    asset_rows = [
        ("Stocks Pre-Tax", ["equity_pre"]),
        ("Stocks Post-Tax", ["equity_post"]),
        ("Stocks Roth", ["equity_roth"]),

        ("Bonds Pre-Tax", ["bond_pre"]),
        ("Bonds Post-Tax", ["bond_post"]),
        ("Bonds Roth", ["bond_roth"]),

        ("Cash Pre-Tax", ["cash_pre"]),
        ("Cash Post-Tax", ["cash_post"]),
        ("Cash Roth", ["cash_roth"]),

        ("HSA", ["hsa_cash", "hsa_equity", "hsa_bond"]),

        ("Real Estate", ["real_estate"]),

        (
            "Total Portfolio",
            [
                "equity_pre", "equity_post", "equity_roth",
                "bond_pre", "bond_post", "bond_roth",
                "cash_pre", "cash_post", "cash_roth",
                "hsa_cash", "hsa_equity", "hsa_bond",
            ],
        ),
        (
            "Total Assets",
            [
                "equity_pre", "equity_post", "equity_roth",
                "bond_pre", "bond_post", "bond_roth",
                "cash_pre", "cash_post", "cash_roth",
                "hsa_cash", "hsa_equity", "hsa_bond",
                "real_estate",
            ],
        ),
    ]

    rows = []

    for label, attrs in asset_rows:
        husband_value = _portfolio_total(husband_portfolio, attrs)
        wife_value = _portfolio_total(wife_portfolio, attrs) if show_wife else 0.0
        total_value = husband_value + wife_value

        row = [
            label,
            _fmt_assumption_currency(husband_value),
        ]

        if show_wife:
            row.append(_fmt_assumption_currency(wife_value))

        row.append(_fmt_assumption_currency(total_value))
        rows.append(row)

    return {
        "Starting Portfolio Inputs": {
            "type": "table",
            "columns": portfolio_columns,
            "rows": rows,
        },
        "Portfolio Settings": {
            "Fund Expenses Enabled": getattr(sim_config, "use_fund_expenses", None),
            "Fund Expense Rate": _rate_fraction_to_percent(
                getattr(sim_config, "fund_expense", None)
            ),
            "Rebalance Strategy": _friendly_label(getattr(sim_config, "sim_rebalance", None)),
            "Rebalance Every Year": getattr(sim_config, "rebalance_every_year", None),
        },
    }


def _build_household_retirement_table(husband, wife, sim_config):
    show_wife = (
        getattr(sim_config, "second_person_enabled", False)
        and wife is not None
    )

    if show_wife:
        columns = ["Field", "Husband", "Wife", "Total"]
    else:
        columns = ["Field", "Husband"]

    fields = [
        ("Current Age", "age", _fmt_assumption_number, False),
        ("Retirement Age", "retire_age", _fmt_assumption_number, False),
        ("Salary / Wages", "income", _fmt_assumption_currency, True),
        ("Social Security Amount", "ss", _fmt_assumption_currency, True),
        ("Social Security Start Age", "ss_age", _fmt_assumption_number, False),
        ("Pension Amount", "pension", _fmt_assumption_currency, True),
        ("Pension Start Age", "pension_age", _fmt_assumption_number, False),
        ("Annuity Amount", "annuity", _fmt_assumption_currency, True),
        ("Annuity Start Age", "annuity_age", _fmt_assumption_number, False),
        ("401k / IRA Contribution", "annual_401k_contribution", _fmt_assumption_currency, True),
        ("Employer Match", "annual_employer_match", _fmt_assumption_currency, True),
    ]

    rows = []

    for field_label, attr, formatter, include_total in fields:
        husband_raw = getattr(husband, attr, None)
        row = [
            field_label,
            formatter(husband_raw),
        ]

        if show_wife:
            wife_raw = getattr(wife, attr, None)
            row.append(formatter(wife_raw))

            if include_total:
                total = _as_float(husband_raw) + _as_float(wife_raw)
                row.append(_fmt_assumption_currency(total))
            else:
                row.append("")

        rows.append(row)

    return {
        "type": "table",
        "columns": columns,
        "rows": rows,
    }


def _build_expense_rows(expenses):
    if expenses is None:
        return []

    if hasattr(expenses, "get_expenses"):
        raw_expenses = expenses.get_expenses()
    elif isinstance(expenses, list):
        raw_expenses = expenses
    else:
        raw_expenses = []

    rows = []
    for expense in raw_expenses:
        if not isinstance(expense, dict):
            continue

        rows.append(
            {
                "Description": expense.get("comment") or "Expense",
                "Start Year": expense.get("start_year"),
                "End Year": expense.get("end_year") or "Ongoing",
                "Annual Amount": expense.get("cost"),
            }
        )

    return rows


def _selected_visuals(options, visual_map):
    selected = []

    for option_key, label in visual_map:
        if options.get(option_key, False):
            selected.append(label)

    return ", ".join(selected) if selected else "None selected"


def _build_withdrawal_assumptions(sim_config):
    if getattr(sim_config, "always_use_expense_mode", False):
        return None

    mode = getattr(sim_config, "retirement_withdraw_mode", None)
    normalized_mode = str(mode or "").lower()

    assumptions = {
        "Withdrawal Method": _friendly_label(mode),
    }

    if "percent" in normalized_mode or "percentage" in normalized_mode:
        assumptions["Annual Withdrawal Rate"] = getattr(
            sim_config,
            "retirement_withdraw_pct",
            None,
        )

    if "dollar" in normalized_mode:
        assumptions["Fixed Annual Withdrawal"] = getattr(
            sim_config,
            "retirement_withdraw_dollars",
            None,
        )

    return assumptions


def _build_sequence_of_returns_assumptions(sim_config):
    if not getattr(sim_config, "sequence_risk_enabled", False):
        return None

    return {
        "Enabled": True,
        "Scenario Timing": getattr(sim_config, "sequence_risk_timing", None),
        "Scenario Length": getattr(sim_config, "sequence_risk_length", None),
        "Scenario Depth": getattr(sim_config, "sequence_risk_depth", None),
    }


def _build_withdrawal_settings(sim_config):
    withdrawal_mode = getattr(sim_config, "retirement_withdraw_mode", None)
    normalized_mode = str(withdrawal_mode or "").lower()

    settings = {
        "Withdrawal Mode": _friendly_label(withdrawal_mode),
        "Always Use Expense Mode": getattr(sim_config, "always_use_expense_mode", None),
    }

    if "percent" in normalized_mode or "percentage" in normalized_mode:
        settings["Withdrawal Percent"] = getattr(
            sim_config,
            "retirement_withdraw_pct",
            None,
        )
    elif "dollar" in normalized_mode:
        settings["Withdrawal Dollar Amount"] = getattr(
            sim_config,
            "retirement_withdraw_dollars",
            None,
        )

    settings["Scenario Expense Multiplier"] = getattr(
        sim_config,
        "scenario_expense_multiplier",
        None,
    )

    return settings


def _build_assumptions_summary(
    husband,
    wife,
    husband_portfolio,
    wife_portfolio,
    expenses,
    sim_config,
    report_options,
):
    household = _build_household_retirement_table(
        husband,
        wife,
        sim_config,
    )

    withdrawal_assumptions = _build_withdrawal_assumptions(sim_config)
    sequence_assumptions = _build_sequence_of_returns_assumptions(sim_config)

    assumptions = {
        "Household & Retirement": household,

        "Portfolio Inputs": _build_portfolio_inputs(
            husband_portfolio,
            wife_portfolio,
            sim_config,
        ),

        "Expense Inputs": {
            "type": "table",
            "empty_message": "No additional expense entries.",
            "rows": _build_expense_rows(expenses),
        },

        "Market & Inflation Assumptions": {
            "Inflation Rate": _rate_fraction_to_percent(
                getattr(sim_config, "inflation_rate", None)
            ),
            "Equity / Stock Mean Return": _rate_fraction_to_percent(
                getattr(sim_config, "eq_mean", None)
            ),
            "Bond Mean Return": _rate_fraction_to_percent(
                getattr(sim_config, "bd_mean", None)
            ),
            "Cash Mean Return": _rate_fraction_to_percent(
                getattr(sim_config, "cs_mean", None)
            ),
            "Real Estate Mean Return": _rate_fraction_to_percent(
                getattr(sim_config, "re_mean", None)
            ),
            "Equity / Stock Standard Deviation": _rate_fraction_to_percent(
                getattr(sim_config, "eq_std", None)
            ),
            "Bond Standard Deviation": _rate_fraction_to_percent(
                getattr(sim_config, "bd_std", None)
            ),
            "Cash Standard Deviation": _rate_fraction_to_percent(
                getattr(sim_config, "cs_std", None)
            ),
            "Real Estate Standard Deviation": _rate_fraction_to_percent(
                getattr(sim_config, "re_std", None)
            ),
            "Sequence Risk Enabled": getattr(
                sim_config,
                "sequence_risk_enabled",
                None,
            ),
        },

        "Tax Assumptions": {
            "Tax Filing Status": getattr(sim_config, "tax_filing_status", None),
            "Calculate Income Taxes": getattr(sim_config, "calculate_income_taxes", None),
            "Calculate Payroll Taxes": getattr(sim_config, "calculate_payroll_taxes", None),
            "Calculate State Taxes": getattr(sim_config, "calculate_state_taxes", None),
            "State of Residence": getattr(sim_config, "state_of_residence", None),
            "Include RMDs": getattr(sim_config, "include_rmd", None),
        },
    }

    if withdrawal_assumptions is not None:
        assumptions["Withdrawals Automatically Calculated"] = withdrawal_assumptions

    if sequence_assumptions is not None:
        assumptions["Sequence-of-Returns Scenario"] = sequence_assumptions

    return assumptions


def _get_report_output_folder():
    return os.path.join(
        os.path.expanduser("~"),
        "Desktop",
        "WARPSimLab",
        "Reports",
    )


def _safe_report_id(report_id):
    return "".join(
        ch if ch.isalnum() or ch in {"-", "_"} else "_"
        for ch in str(report_id)
    )

def _save_portfolio_plot_with_temporary_modes(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
    *,
    output_folder,
    filename,
    subplot_mode,
    sim_type,
    monte_carlo_mode=None,
    force_num_sims=None,
):
    original_subplot_mode = getattr(sim_config, "subplot_mode", None)
    original_sim_type = getattr(sim_config, "sim_type", None)
    original_monte_carlo_mode = getattr(sim_config, "monte_carlo_mode", None)
    original_include_realestate = getattr(sim_config, "include_realestate", None)

    try:
        sim_config.subplot_mode = subplot_mode
        sim_config.sim_type = sim_type

        if monte_carlo_mode is not None:
            sim_config.monte_carlo_mode = monte_carlo_mode

        # Risk reports measure depletion of liquid/investment portfolio assets.
        # Real estate is excluded by default to match Monte Carlo and Historical Window plots.
        sim_config.include_realestate = False

        p = run_pipeline(
            husband_portfolio,
            wife_portfolio,
            husband,
            wife,
            expenses,
            sim_config,
            force_num_sims=force_num_sims,
        )

        image_path = save_portfolio_projection_report_plot(
            output_folder=output_folder,
            filename=filename,
            years_list=p["years_list"],
            portfolio_plot_data=p["portfolio_plot_data"],
            sim_config=sim_config,
            husband=husband,
            wife=wife,
            summary_results=None,
        )

        return {
            "image_path": image_path,
            "simulated_shortfall_rate": getattr(
                p["portfolio_plot_data"],
                "simulated_shortfall_rate",
                None,
            ),
        }

    finally:
        sim_config.subplot_mode = original_subplot_mode
        sim_config.sim_type = original_sim_type
        sim_config.monte_carlo_mode = original_monte_carlo_mode
        sim_config.include_realestate = original_include_realestate


def _save_income_plot_with_temporary_modes(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
    *,
    output_folder,
    filename,
    subplot_mode,
    sim_type,
    force_num_sims=1,
):
    original_subplot_mode = getattr(sim_config, "subplot_mode", None)
    original_sim_type = getattr(sim_config, "sim_type", None)

    try:
        sim_config.subplot_mode = subplot_mode
        sim_config.sim_type = sim_type

        p = run_pipeline(
            husband_portfolio,
            wife_portfolio,
            husband,
            wife,
            expenses,
            sim_config,
            force_num_sims=force_num_sims,
        )
        breakdown = p["breakdown_by_class"]

        income_keys = [
            "work",
            "pension",
            "annuity",
            "ss",
            "special_income",
        ]

        cashflow_extra_keys = [
            "rmd",
            "withdrawal",
            "cash_interest",
            "bond_interest",
            "qualified_dividends",
        ]

        if sim_type == "income_sim":
            plot_breakdown = {
                key: breakdown[key].copy()
                for key in income_keys
            }

        elif sim_type == "cashflow_sim":
            plot_breakdown = {
                "income": sum(breakdown[key] for key in income_keys)
            }

            for key in cashflow_extra_keys:
                plot_breakdown[key] = breakdown[key].copy()

        else:
            raise ValueError(f"Unsupported report income plot sim_type: {sim_type}")

        plot_total = sum(plot_breakdown[key] for key in plot_breakdown)

        return save_income_projection_report_plot(
            output_folder=output_folder,
            filename=filename,
            years_to_simulate=p["years"],
            net_profit=p["net_profit"],
            net_income=plot_total,
            breakdown=plot_breakdown,
            taxes=p["taxes"],
            expenses=p["expense_amt"],
            husband=husband,
            wife=wife,
            sim_config=sim_config,
        )

    finally:
        sim_config.subplot_mode = original_subplot_mode
        sim_config.sim_type = original_sim_type


def _build_report_plot_assets(
    p,
    report_options,
    report_id,
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
    warnings,
):
    output_folder = _get_report_output_folder()
    safe_report_id = _safe_report_id(report_id)
    assets_folder = os.path.join(
        output_folder,
        f"executive_summary_{safe_report_id}_assets",
    )

    plot_assets = {}
    report_shortfall_rate = None

    if _get_report_option(
        report_options,
        ["portfolio_visuals", "include_normal_projection"],
        False,
    ):
        try:
            plot_result = _save_portfolio_plot_with_temporary_modes(
                husband_portfolio,
                wife_portfolio,
                husband,
                wife,
                expenses,
                sim_config,
                output_folder=assets_folder,
                filename="portfolio_projection.png",
                subplot_mode="fill",
                sim_type="portfolio_sim",
                monte_carlo_mode=None,
                force_num_sims=1,
            )
            image_path = plot_result["image_path"]
            report_shortfall_rate = plot_result.get("simulated_shortfall_rate")
            
            plot_assets["portfolio_projection"] = {
                "path": image_path,
                "title": "Portfolio Projection",
                "alt": "Portfolio projection over the simulated period",
            }

        except Exception as exc:
            warnings.append(
                f"Portfolio projection plot could not be generated: {exc}"
            )

    if _get_report_option(
        report_options,
        ["portfolio_visuals", "include_subcategories_projection"],
        False,
    ):
        try:
            plot_result  = _save_portfolio_plot_with_temporary_modes(
                husband_portfolio,
                wife_portfolio,
                husband,
                wife,
                expenses,
                sim_config,
                output_folder=assets_folder,
                filename="subcategories_projection.png",
                subplot_mode="sub_categories",
                sim_type="portfolio_sim",
                force_num_sims=1,
            )
            image_path = plot_result["image_path"]

            plot_assets["subcategories_projection"] = {
                "path": image_path,
                "title": "Portfolio Subcategories",
                "alt": "Portfolio projection by asset subcategory",
            }

        except Exception as exc:
            warnings.append(
                f"Portfolio subcategories plot could not be generated: {exc}"
            )

    if _get_report_option(
        report_options,
        ["income_visuals", "include_normal_income"],
        False,
    ):
        try:
            image_path = _save_income_plot_with_temporary_modes(
                husband_portfolio,
                wife_portfolio,
                husband,
                wife,
                expenses,
                sim_config,
                output_folder=assets_folder,
                filename="income_projection.png",
                subplot_mode="fill",
                sim_type="income_sim",
                force_num_sims=1,
            )

            plot_assets["income_projection"] = {
                "path": image_path,
                "title": "Income Projection",
                "alt": "Income projection over the simulated period",
            }

        except Exception as exc:
            warnings.append(
                f"Income projection plot could not be generated: {exc}"
            )

    if _get_report_option(
        report_options,
        ["income_visuals", "include_subcategories_income"],
        False,
    ):
        try:
            image_path = _save_income_plot_with_temporary_modes(
                husband_portfolio,
                wife_portfolio,
                husband,
                wife,
                expenses,
                sim_config,
                output_folder=assets_folder,
                filename="income_subcategories.png",
                subplot_mode="sub_categories",
                sim_type="income_sim",
                force_num_sims=1,
            )

            plot_assets["income_subcategories"] = {
                "path": image_path,
                "title": "Income Source Breakdown",
                "alt": "Income projection broken down by income source",
            }

        except Exception as exc:
            warnings.append(
                f"Income subcategory plot could not be generated: {exc}"
            )

    if _get_report_option(
        report_options,
        ["cashflow_visuals", "include_normal_cashflow"],
        False,
    ):
        try:
            image_path = _save_income_plot_with_temporary_modes(
                husband_portfolio,
                wife_portfolio,
                husband,
                wife,
                expenses,
                sim_config,
                output_folder=assets_folder,
                filename="cashflow_projection.png",
                subplot_mode="fill",
                sim_type="cashflow_sim",
                force_num_sims=1,
            )

            plot_assets["cashflow_projection"] = {
                "path": image_path,
                "title": "Cashflow Projection",
                "alt": "Cashflow projection over the simulated period",
            }

        except Exception as exc:
            warnings.append(
                f"Cashflow projection plot could not be generated: {exc}"
            )

    if _get_report_option(
        report_options,
        ["cashflow_visuals", "include_subcategories_cashflow"],
        False,
    ):
        try:
            image_path = _save_income_plot_with_temporary_modes(
                husband_portfolio,
                wife_portfolio,
                husband,
                wife,
                expenses,
                sim_config,
                output_folder=assets_folder,
                filename="cashflow_subcategories.png",
                subplot_mode="sub_categories",
                sim_type="cashflow_sim",
                force_num_sims=1,
            )

            plot_assets["cashflow_subcategories"] = {
                "path": image_path,
                "title": "Cashflow Breakdown",
                "alt": "Cashflow projection broken down by source",
            }

        except Exception as exc:
            warnings.append(
                f"Cashflow subcategory plot could not be generated: {exc}"
            )

    if _get_report_option(
        report_options,
        ["operating_balance_visuals", "include_cumulative_operating_balance"],
        True,
    ):
        try:
            image_path = save_cumulative_operating_balance_report_plot(
                output_folder=assets_folder,
                filename="cumulative_operating_balance.png",
                years_to_simulate=p["years"],
                net_profit=p["net_profit"],
                portfolio_plot_data=p["portfolio_plot_data"],
                husband=husband,
                wife=wife,
                sim_config=sim_config,
            )

            plot_assets["cumulative_operating_balance"] = {
                "path": image_path,
                "title": "Cumulative Operating Balance",
                "alt": "Cumulative operating balance over the simulated period",
            }

        except Exception as exc:
            warnings.append(
                f"Cumulative operating balance plot could not be generated: {exc}"
            )

    if _get_report_option(
        report_options,
        ["portfolio_visuals", "include_monte_carlo_analysis"],
        False,
    ):
        try:
            plot_result = _save_portfolio_plot_with_temporary_modes(
                husband_portfolio,
                wife_portfolio,
                husband,
                wife,
                expenses,
                sim_config,
                output_folder=assets_folder,
                filename="monte_carlo_analysis.png",
                subplot_mode="monte_carlo",
                sim_type="portfolio_sim",
                monte_carlo_mode="pathBasedAnnualSampling",
                force_num_sims=None,
            )
            image_path = plot_result["image_path"]

            plot_assets["monte_carlo_analysis"] = {
                "path": image_path,
                "title": "Monte Carlo Analysis",
                "alt": "Monte Carlo portfolio projection range",
            }

        except Exception as exc:
            warnings.append(f"Monte Carlo plot could not be generated: {exc}")

    if _get_report_option(
        report_options,
        ["portfolio_visuals", "include_historical_windows_analysis"],
        False,
    ):
        try:
            plot_result = _save_portfolio_plot_with_temporary_modes(
                husband_portfolio,
                wife_portfolio,
                husband,
                wife,
                expenses,
                sim_config,
                output_folder=assets_folder,
                filename="historical_windows_analysis.png",
                subplot_mode="monte_carlo",
                sim_type="portfolio_sim",
                monte_carlo_mode="rollingHistoricalWindows",
                force_num_sims=None,
            )
            image_path = plot_result["image_path"]

            plot_assets["historical_windows_analysis"] = {
                "path": image_path,
                "title": "Historical Windows Analysis",
                "alt": "Historical rolling-window portfolio projection range",
            }

        except Exception as exc:
            warnings.append(f"Historical Windows plot could not be generated: {exc}")

    return plot_assets, report_shortfall_rate

def _fmt_assumption_currency(value):
    if value is None:
        return "N/A"

    amount = _as_float(value)

    if amount < 0:
        return f"-${abs(amount):,.0f}"

    return f"${amount:,.0f}"


def _fmt_assumption_number(value):
    if value is None:
        return "N/A"

    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_assumption_percent_from_fraction(value):
    if value is None:
        return "N/A"

    return f"{_as_float(value) * 100.0:.2f}%"


def build_summary_report_data_from_pipeline(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
):
    original_include_realestate = sim_config.include_realestate

    try:
        sim_config.include_realestate = True

        p = run_pipeline(
            husband_portfolio,
            wife_portfolio,
            husband,
            wife,
            expenses,
            sim_config,
            force_num_sims=1,
        )
    finally:
        sim_config.include_realestate = original_include_realestate

    results = p["summary_results"]
    report_options = dict(getattr(sim_config, "report_options", {}) or {})

    generated_timestamp = datetime.now()
    visible_report_id = generated_timestamp.strftime("%Y-%m-%d %H:%M:%S")

    warnings = _build_report_warnings(report_options)

    plot_assets, report_shortfall_rate = _build_report_plot_assets(
        p=p,
        report_options=report_options,
        report_id=visible_report_id,
        husband_portfolio=husband_portfolio,
        wife_portfolio=wife_portfolio,
        husband=husband,
        wife=wife,
        expenses=expenses,
        sim_config=sim_config,
        warnings=warnings,
    )

    return SummaryReportData(
        report_options=report_options,
        report_metadata={
            "Report Title": "WARPSimLab Executive Summary Report",
            "Generated Timestamp": visible_report_id,
            "Report ID": visible_report_id,
            "Report Type": "summary_report",
            "Output Format": report_options.get("output_format", "HTML"),
            "Projection Period": _build_projection_period_label(sim_config),
            "Report Basis": _build_report_basis_label(sim_config),
        },
        simulation_snapshot=_build_simulation_snapshot(sim_config),
        results_summary={
            "portfolio_milestones": _build_portfolio_milestones(
                results,
                husband,
                wife,
                sim_config,
            ),
            "income_milestones": _build_income_milestones(
                results,
                husband,
                wife,
                sim_config,
            ),
            "simulation_totals": _build_simulation_totals(
                results,
                simulated_shortfall_rate=report_shortfall_rate,
            ),
        },

        assumptions_summary=_build_assumptions_summary(
            husband,
            wife,
            husband_portfolio,
            wife_portfolio,
            expenses,
            sim_config,
            report_options,
        ),

        monte_carlo_summary=None,
        historical_windows_summary=None,
        plot_assets=plot_assets,
        warnings=warnings,
    )


def run_sim_summary_report(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
):
    report_data = build_summary_report_data_from_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
    )

    return generate_summary_report(report_data)