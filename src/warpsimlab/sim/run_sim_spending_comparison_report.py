# run_sim_spending_comparison_report.py

import numpy as np

from .simulation import run_pipeline
from datetime import datetime

from src.warpsimlab.reports.report_data import (
    SpendingComparisonReportData,
)

from src.warpsimlab.reports.spending_comparison_report import (
    generate_spending_comparison_report,
)


def _build_report_metadata(sim_config):
    start_year = int(
        getattr(sim_config, "start_year", 0)
    )

    years = int(
        getattr(sim_config, "years_to_simulate", 0)
    )

    end_year = start_year + years

    now = datetime.now()

    return {
        "Report Title": "Spending Comparison Report",
        "Generated Timestamp": now.isoformat(
            timespec="seconds"
        ),
        "Projection Period": (
            f"{start_year}-{end_year} "
            f"({years} Years)"
        ),
        "Report Basis": (
            "Real Dollars (Inflation Adjusted)"
            if getattr(
                sim_config,
                "plot_mode",
                None,
            ) == "real"
            else "Raw Dollars (Future Nominal Values)"
        ),
        "Report ID": now.strftime(
            "%Y-%m-%d_%H_%M_%S"
        ),
    }


def _distribution(values):
    values = np.asarray(values, dtype=float)

    if values.size == 0:
        return {
            "minimum": 0.0,
            "10th_percentile": 0.0,
            "25th_percentile": 0.0,
            "median": 0.0,
            "75th_percentile": 0.0,
            "90th_percentile": 0.0,
            "maximum": 0.0,
        }

    return {
        "minimum": float(np.min(values)),
        "10th_percentile": float(np.percentile(values, 10)),
        "25th_percentile": float(np.percentile(values, 25)),
        "median": float(np.median(values)),
        "75th_percentile": float(np.percentile(values, 75)),
        "90th_percentile": float(np.percentile(values, 90)),
        "maximum": float(np.max(values)),
    }


def _build_depletion_statistics(total_assets, years):
    total_assets = np.asarray(total_assets, dtype=float)
    years = np.asarray(years)

    scenario_count = int(total_assets.shape[0])

    depleted_mask = np.any(
        total_assets <= 0.0,
        axis=1,
    )

    depleted_count = int(np.sum(depleted_mask))

    depleted_percent = (
        100.0 * depleted_count / scenario_count
        if scenario_count > 0
        else 0.0
    )

    depletion_years = []

    for path in total_assets[depleted_mask]:
        indices = np.where(path <= 0.0)[0]

        if len(indices) == 0:
            continue

        index = int(indices[0])

        try:
            depletion_years.append(
                int(years[index])
            )
        except (IndexError, TypeError, ValueError):
            pass

    if depletion_years:
        earliest_year = int(min(depletion_years))
        median_year = int(np.median(depletion_years))
        latest_year = int(max(depletion_years))
    else:
        earliest_year = None
        median_year = None
        latest_year = None

    return {
        "historical_window_count": scenario_count,
        "windows_reaching_zero_count": depleted_count,
        "windows_reaching_zero_percent": float(
            depleted_percent
        ),
        "earliest_reaching_zero_year": earliest_year,
        "median_reaching_zero_year": median_year,
        "latest_reaching_zero_year": latest_year,
    }


def _build_case_result(
    spending_percentage,
    pipeline_result,
):
    core = pipeline_result["core"]

    total_assets = np.asarray(
        core["total_assets"],
        dtype=float,
    )

    years = np.asarray(
        core["year"][0]
    )

    ending_portfolios = total_assets[:, -1]

    minimum_portfolios = np.min(
        total_assets,
        axis=1,
    )

    expense_values = np.asarray(
        core["expense_amt"],
        dtype=float,
    )

    first_year_expenses = (
        expense_values[:, 1]
        if expense_values.shape[1] > 1
        else np.zeros(expense_values.shape[0], dtype=float)
    )

    lifetime_expenses = np.sum(
        expense_values,
        axis=1,
    )

    lifetime_taxes = np.sum(
        np.asarray(core["taxes"], dtype=float),
        axis=1,
    )

    lifetime_cash_flow_shortfall = np.sum(
        np.asarray(
            core["cash_flow_shortfall"],
            dtype=float,
        ),
        axis=1,
    )

    lifetime_uncovered_expense = np.sum(
        np.asarray(
            core["uncovered_expense"],
            dtype=float,
        ),
        axis=1,
    )

    return {
        "spending_percentage": float(spending_percentage),
        "scenario_expense_multiplier": (
            float(spending_percentage) / 100.0
        ),
        "is_current_spending": (
            float(spending_percentage) == 100.0
        ),

        "depletion": _build_depletion_statistics(
            total_assets,
            years,
        ),

        "ending_portfolio": _distribution(
            ending_portfolios
        ),

        "minimum_portfolio": _distribution(
            minimum_portfolios
        ),

        "first_year_expenses": _distribution(
            first_year_expenses
        ),

        "lifetime_expenses": _distribution(
            lifetime_expenses
        ),

        "lifetime_taxes": _distribution(
            lifetime_taxes
        ),

        "lifetime_cash_flow_shortfall": _distribution(
            lifetime_cash_flow_shortfall
        ),

        "lifetime_uncovered_expense": _distribution(
            lifetime_uncovered_expense
        ),
    }


def run_sim_spending_comparison_report(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
):
    report_options = getattr(
        sim_config,
        "report_options",
        {},
    )

    spending_percentages = report_options.get(
        "spending_percentages",
        [],
    )

    original_subplot_mode = getattr(
        sim_config,
        "subplot_mode",
        None,
    )

    original_sim_type = getattr(
        sim_config,
        "sim_type",
        None,
    )

    original_monte_carlo_mode = getattr(
        sim_config,
        "monte_carlo_mode",
        None,
    )

    original_include_realestate = getattr(
        sim_config,
        "include_realestate",
        None,
    )

    original_show_simulated_shortfall_rate = getattr(
        sim_config,
        "show_simulated_shortfall_rate",
        None,
    )

    original_expense_multiplier = getattr(
        sim_config,
        "scenario_expense_multiplier",
        1.0,
    )

    original_overlay_tax_impacts = getattr(
        sim_config,
        "overlay_tax_impacts",
        False,
    )

    original_overlay_fund_expense_impacts = getattr(
        sim_config,
        "overlay_fund_expense_impacts",
        False,
    )

    cases = []

    try:
        sim_config.subplot_mode = "monte_carlo"
        sim_config.sim_type = "portfolio_sim"
        sim_config.monte_carlo_mode = (
            "rollingHistoricalWindows"
        )

        # Match the existing Historical Window risk analysis.
        sim_config.include_realestate = False

        # We calculate depletion statistics directly from the
        # primary Historical Window run.
        sim_config.show_simulated_shortfall_rate = False

        # Prevent run_pipeline() from launching additional
        # deterministic overlay simulations for each case.
        sim_config.overlay_tax_impacts = False
        sim_config.overlay_fund_expense_impacts = False

        for spending_percentage in spending_percentages:
            sim_config.scenario_expense_multiplier = (
                float(spending_percentage) / 100.0
            )

            pipeline_result = run_pipeline(
                husband_portfolio,
                wife_portfolio,
                husband,
                wife,
                expenses,
                sim_config,
                force_num_sims=None,
            )

            cases.append(
                _build_case_result(
                    spending_percentage,
                    pipeline_result,
                )
            )

    finally:
        sim_config.subplot_mode = original_subplot_mode
        sim_config.sim_type = original_sim_type
        sim_config.monte_carlo_mode = (
            original_monte_carlo_mode
        )
        sim_config.include_realestate = (
            original_include_realestate
        )
        sim_config.show_simulated_shortfall_rate = (
            original_show_simulated_shortfall_rate
        )
        sim_config.scenario_expense_multiplier = (
            original_expense_multiplier
        )
        sim_config.overlay_tax_impacts = (
            original_overlay_tax_impacts
        )
        sim_config.overlay_fund_expense_impacts = (
            original_overlay_fund_expense_impacts
        )

    #print("diagnostics in run_sim_spending_comparison_report.py")
    #for case in cases:
    #    print(
    #        case["spending_percentage"],
    #        case["depletion"]["windows_reaching_zero_percent"],
    #        case["ending_portfolio"]["median"],
    #        case["lifetime_expenses"]["median"],
    #    )

    report_data = SpendingComparisonReportData(
        report_options=report_options,
        report_metadata=_build_report_metadata(
            sim_config
        ),
        comparison_cases=cases,
        baseline_percentage=100.0,
        warnings=[],
    )

    return generate_spending_comparison_report(
        report_data
    )