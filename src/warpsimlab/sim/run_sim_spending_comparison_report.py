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
    deterministic_pipeline_result,
    historical_pipeline_result,
):
    deterministic_core = deterministic_pipeline_result["core"]
    historical_core = historical_pipeline_result["core"]

    # ---------------------------------------------------------
    # Deterministic financial quantities
    # ---------------------------------------------------------

    deterministic_total_assets = np.asarray(
        deterministic_core["total_assets"],
        dtype=float,
    )

    deterministic_expenses = np.asarray(
        deterministic_core["expense_amt"],
        dtype=float,
    )

    deterministic_taxes = np.asarray(
        deterministic_core["taxes"],
        dtype=float,
    )

    deterministic_cash_flow_shortfall = np.asarray(
        deterministic_core["cash_flow_shortfall"],
        dtype=float,
    )

    deterministic_uncovered_expense = np.asarray(
        deterministic_core["uncovered_expense"],
        dtype=float,
    )

    deterministic_ending_portfolio = float(
        deterministic_total_assets[0, -1]
    )

    deterministic_first_year_expenses = (
        float(deterministic_expenses[0, 1])
        if deterministic_expenses.shape[1] > 1
        else 0.0
    )

    deterministic_lifetime_expenses = float(
        np.sum(deterministic_expenses[0])
    )

    deterministic_lifetime_taxes = float(
        np.sum(deterministic_taxes[0])
    )

    deterministic_lifetime_cash_flow_shortfall = float(
        np.sum(deterministic_cash_flow_shortfall[0])
    )

    deterministic_lifetime_uncovered_expense = float(
        np.sum(deterministic_uncovered_expense[0])
    )

    # ---------------------------------------------------------
    # Historical Window risk quantities
    # ---------------------------------------------------------

    historical_total_assets = np.asarray(
        historical_core["total_assets"],
        dtype=float,
    )

    historical_years = np.asarray(
        historical_core["year"][0]
    )

    historical_ending_portfolios = (
        historical_total_assets[:, -1]
    )

    return {
        "spending_percentage": float(spending_percentage),

        "scenario_expense_multiplier": (
            float(spending_percentage) / 100.0
        ),

        "is_current_spending": (
            float(spending_percentage) == 100.0
        ),

        # Deterministic quantities
        "deterministic_ending_portfolio": (
            deterministic_ending_portfolio
        ),
        "deterministic_first_year_expenses": (
            deterministic_first_year_expenses
        ),
        "deterministic_lifetime_expenses": (
            deterministic_lifetime_expenses
        ),
        "deterministic_lifetime_taxes": (
            deterministic_lifetime_taxes
        ),
        "deterministic_lifetime_cash_flow_shortfall": (
            deterministic_lifetime_cash_flow_shortfall
        ),
        "deterministic_lifetime_uncovered_expense": (
            deterministic_lifetime_uncovered_expense
        ),

        # Historical Window risk quantities
        "depletion": _build_depletion_statistics(
            historical_total_assets,
            historical_years,
        ),

        "ending_portfolio": _distribution(
            historical_ending_portfolios
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
        # Spending Comparison evaluates the investment portfolio.
        # Real estate is excluded to match the existing portfolio
        # risk analysis.
        sim_config.include_realestate = False

        # The report calculates depletion directly from the
        # Historical Window run.
        sim_config.show_simulated_shortfall_rate = False

        # Prevent run_pipeline() from launching unrelated
        # overlay simulations for every comparison case.
        sim_config.overlay_tax_impacts = False
        sim_config.overlay_fund_expense_impacts = False

        for spending_percentage in spending_percentages:
            sim_config.scenario_expense_multiplier = (
                float(spending_percentage) / 100.0
            )

            # -------------------------------------------------
            # Deterministic projection
            # -------------------------------------------------

            sim_config.subplot_mode = "fill"
            sim_config.sim_type = "portfolio_sim"

            deterministic_pipeline_result = run_pipeline(
                husband_portfolio,
                wife_portfolio,
                husband,
                wife,
                expenses,
                sim_config,
                force_num_sims=1,
            )

            # -------------------------------------------------
            # Historical Window risk analysis
            # -------------------------------------------------

            sim_config.subplot_mode = "monte_carlo"
            sim_config.sim_type = "portfolio_sim"
            sim_config.monte_carlo_mode = (
                "rollingHistoricalWindows"
            )

            historical_pipeline_result = run_pipeline(
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
                    deterministic_pipeline_result,
                    historical_pipeline_result,
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