# run_sim_asset_allocation_comparison_report.py

import os
from datetime import datetime

import numpy as np

from .simulation import run_pipeline
from .engines import diagnosticEngine

from src.warpsimlab.reports.report_data import AssetAllocationComparisonReportData
from src.warpsimlab.reports.asset_allocation_comparison_report import generate_asset_allocation_comparison_report
from src.warpsimlab.reports.report_common import get_report_output_folder, safe_report_id
from src.warpsimlab.reports.report_plot_helpers import save_portfolio_projection_report_plot


def _build_report_metadata(sim_config):
    start_year = int(getattr(sim_config, "start_year", 0))
    years = int(getattr(sim_config, "years_to_simulate", 0))
    end_year = start_year + years
    now = datetime.now()

    return {
        "Report Title": "Asset Allocation Comparison Report",
        "Generated Timestamp": now.isoformat(timespec="seconds"),
        "Projection Period": f"{start_year}-{end_year} ({years} Years)",
        "Report Basis": (
            "Real Dollars (Inflation Adjusted)"
            if getattr(sim_config, "plot_mode", None) == "real"
            else "Raw Dollars (Future Nominal Values)"
        ),
        "Report ID": now.strftime("%Y-%m-%d_%H_%M_%S"),
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
    depleted_mask = np.any(total_assets <= 0.0, axis=1)
    depleted_count = int(np.sum(depleted_mask))
    depleted_percent = 100.0 * depleted_count / scenario_count if scenario_count > 0 else 0.0

    depletion_years = []

    for path in total_assets[depleted_mask]:
        indices = np.where(path <= 0.0)[0]

        if len(indices) == 0:
            continue

        index = int(indices[0])

        try:
            depletion_years.append(int(years[index]))
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
        "windows_reaching_zero_percent": float(depleted_percent),
        "earliest_reaching_zero_year": earliest_year,
        "median_reaching_zero_year": median_year,
        "latest_reaching_zero_year": latest_year,
    }


def _portfolio_components(portfolio):
    if portfolio is None:
        return 0.0, 0.0, 0.0

    equity = (
        float(getattr(portfolio, "equity_pre", 0.0))
        + float(getattr(portfolio, "equity_post", 0.0))
        + float(getattr(portfolio, "equity_roth", 0.0))
        + float(getattr(portfolio, "hsa_equity", 0.0))
    )

    bonds = (
        float(getattr(portfolio, "bond_pre", 0.0))
        + float(getattr(portfolio, "bond_post", 0.0))
        + float(getattr(portfolio, "bond_roth", 0.0))
        + float(getattr(portfolio, "hsa_bond", 0.0))
    )

    cash = (
        float(getattr(portfolio, "cash_pre", 0.0))
        + float(getattr(portfolio, "cash_post", 0.0))
        + float(getattr(portfolio, "cash_roth", 0.0))
        + float(getattr(portfolio, "hsa_cash", 0.0))
    )

    return equity, bonds, cash


def _current_household_allocation(husband_portfolio, wife_portfolio, sim_config):
    h_equity, h_bonds, h_cash = _portfolio_components(husband_portfolio)

    w_equity = 0.0
    w_bonds = 0.0
    w_cash = 0.0

    if getattr(sim_config, "second_person_enabled", False) and wife_portfolio is not None:
        w_equity, w_bonds, w_cash = _portfolio_components(wife_portfolio)

    total_equity = h_equity + w_equity
    total_bonds = h_bonds + w_bonds
    total_cash = h_cash + w_cash
    total = total_equity + total_bonds + total_cash

    if total <= 0.0:
        return {
            "equity": 0.0,
            "bonds": 0.0,
            "cash": 1.0,
        }

    return {
        "equity": total_equity / total,
        "bonds": total_bonds / total,
        "cash": total_cash / total,
    }


def _derive_allocation(equity_ratio, current_allocation):
    equity_ratio = float(equity_ratio)
    non_equity_ratio = 1.0 - equity_ratio

    current_bonds = float(current_allocation["bonds"])
    current_cash = float(current_allocation["cash"])
    current_non_equity = current_bonds + current_cash

    if current_non_equity <= 1e-12:
        if non_equity_ratio <= 1e-12:
            return {
                "equity": equity_ratio,
                "bonds": 0.0,
                "cash": 0.0,
            }

        raise ValueError(
            "Asset Allocation Comparison cannot derive bond and cash allocations because "
            "the current portfolio contains no bonds or cash."
        )

    bond_share = current_bonds / current_non_equity
    cash_share = current_cash / current_non_equity

    return {
        "equity": equity_ratio,
        "bonds": non_equity_ratio * bond_share,
        "cash": non_equity_ratio * cash_share,
    }


def _build_case_result(
    allocation,
    deterministic_pipeline_result,
    historical_pipeline_result,
    *,
    is_current_allocation=False,
    highlight_only=False,
):
    deterministic_core = deterministic_pipeline_result["core"]
    historical_core = historical_pipeline_result["core"]
    historical_portfolio_plot_data = historical_pipeline_result["portfolio_plot_data"]

    # ---------------------------------------------------------
    # Deterministic financial quantities
    # ---------------------------------------------------------

    deterministic_total_assets = np.asarray(deterministic_core["total_assets"], dtype=float)
    deterministic_ending_portfolio = float(deterministic_total_assets[0, -1])

    # ---------------------------------------------------------
    # Historical Window risk quantities
    # ---------------------------------------------------------

    historical_total_assets = np.asarray(historical_core["total_assets"], dtype=float)
    historical_years = np.asarray(historical_core["year"][0])
    historical_ending_portfolios = historical_total_assets[:, -1]

    return {
        "equity_percentage": 100.0 * allocation["equity"],
        "bond_percentage": 100.0 * allocation["bonds"],
        "cash_percentage": 100.0 * allocation["cash"],
        "is_current_allocation": bool(is_current_allocation),
        "highlight_only": bool(highlight_only),

        # Deterministic quantity
        "deterministic_ending_portfolio": deterministic_ending_portfolio,

        # Historical Window risk quantities
        "depletion": _build_depletion_statistics(historical_total_assets, historical_years),
        "ending_portfolio": _distribution(historical_ending_portfolios),
        "historical_portfolio_plot_data": historical_portfolio_plot_data,
    }


def _find_historical_plot_cases(cases, current_equity_percentage, sim_config=None):
    target_percentages = {
        "minus_20": max(0.0, current_equity_percentage - 20.0),
        "current": current_equity_percentage,
        "plus_20": min(100.0, current_equity_percentage + 20.0),
    }

    plot_cases = {}

    for key, target_percentage in target_percentages.items():
        if key == "current":
            matching_case = next(
                (case for case in cases if case.get("is_current_allocation", False)),
                None,
            )
        else:
            matching_case = next(
                (
                    case
                    for case in cases
                    if not case.get("is_current_allocation", False)
                    and abs(float(case["equity_percentage"]) - target_percentage) < 1e-9
                ),
                None,
            )

        if matching_case is None:
            diagnosticEngine.raise_internal_error("Could not find requested historical asset-allocation plot case.", sim_config,
                                                  context={"target_percentage": target_percentage, "case_key": key,
                                                           "current_equity_percentage": current_equity_percentage,
                                                           "available_case_count": len(cases)})

        plot_cases[key] = matching_case

    return plot_cases


def _build_shared_historical_plot_limits(plot_cases, sim_config=None):
    x_min = None
    x_max = None
    y_max = 0.0

    for case in plot_cases.values():
        plot_data = case["historical_portfolio_plot_data"]
        years = np.asarray(plot_data.years, dtype=float)

        if years.size == 0:
            diagnosticEngine.raise_internal_error("Historical asset-allocation plot data contains no years.", sim_config,
                                                  context={"case_equity_percentage": case.get("equity_percentage")})

        case_x_min = float(np.min(years))
        case_x_max = float(np.max(years))

        x_min = case_x_min if x_min is None else min(x_min, case_x_min)
        x_max = case_x_max if x_max is None else max(x_max, case_x_max)

        pct99 = np.asarray(plot_data.percentiles["pct99"], dtype=float)

        if pct99.size == 0:
            diagnosticEngine.raise_internal_error("Historical asset-allocation plot data contains no 99th percentile values.", sim_config,
                                                  context={"case_equity_percentage": case.get("equity_percentage")})

        y_max = max(y_max, float(np.max(pct99)))

    # Leave modest visual space above the outer probability band.
    if y_max > 0.0:
        y_max *= 1.05
    else:
        y_max = 1.0

    return {
        "x_min": x_min,
        "x_max": x_max,
        "y_min": 0.0,
        "y_max": y_max,
    }


def _generate_historical_allocation_plots(
    cases,
    current_equity_percentage,
    sim_config,
    husband,
    wife,
    report_id,
):
    plot_cases = _find_historical_plot_cases(cases, current_equity_percentage, sim_config)
    shared_limits = _build_shared_historical_plot_limits(plot_cases, sim_config)

    output_folder = get_report_output_folder()
    safe_id = safe_report_id(report_id)
    assets_folder = os.path.join(output_folder, f"asset_allocation_comparison_{safe_id}_assets")

    plot_assets = {}

    filenames = {
        "current": "historical_windows_current.png",
        "minus_20": "historical_windows_minus_20.png",
        "plus_20": "historical_windows_plus_20.png",
    }

    for key in ("current", "minus_20", "plus_20"):
        case = plot_cases[key]
        plot_data = case["historical_portfolio_plot_data"]

        image_path = save_portfolio_projection_report_plot(
            output_folder=assets_folder,
            filename=filenames[key],
            years_list=plot_data.years,
            portfolio_plot_data=plot_data,
            sim_config=sim_config,
            husband=husband,
            wife=wife,
            x_min=shared_limits["x_min"],
            x_max=shared_limits["x_max"],
            y_min=shared_limits["y_min"],
            y_max=shared_limits["y_max"],
        )

        plot_assets[key] = {
            "path": image_path,
            "equity_percentage": case["equity_percentage"],
        }

    return plot_assets


def run_sim_asset_allocation_comparison_report(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
):
    report_options = getattr(sim_config, "report_options", {})

    equity_percentages = report_options.get("equity_percentages", [])
    requested_equity_percentages = [float(value) for value in equity_percentages]

    current_allocation = _current_household_allocation(husband_portfolio, wife_portfolio, sim_config)
    current_equity_percentage = 100.0 * current_allocation["equity"]

    highlight_equity_percentages = [
        max(0.0, current_equity_percentage - 20.0),
        min(100.0, current_equity_percentage + 20.0),
    ]

    simulation_equity_percentages = list(requested_equity_percentages)

    for equity_percentage in highlight_equity_percentages:
        if not any(
            abs(equity_percentage - existing_percentage) < 1e-9
            for existing_percentage in simulation_equity_percentages
        ):
            simulation_equity_percentages.append(equity_percentage)

    original_subplot_mode = getattr(sim_config, "subplot_mode", None)
    original_sim_type = getattr(sim_config, "sim_type", None)
    original_monte_carlo_mode = getattr(sim_config, "monte_carlo_mode", None)
    original_monte_carlo_plot_style = getattr(sim_config, "monte_carlo_plot_style", "fill")
    original_include_realestate = getattr(sim_config, "include_realestate", None)
    original_show_simulated_shortfall_rate = getattr(sim_config, "show_simulated_shortfall_rate", None)
    original_calculate_shortfall_rate = sim_config.calculate_simulated_shortfall_rate
    original_initial_allocation_mode = getattr(sim_config, "sim_initial_allocation_mode", None)
    original_custom_stock = getattr(sim_config, "custom_stock", 0.0)
    original_custom_bonds = getattr(sim_config, "custom_bonds", 0.0)
    original_custom_cash = getattr(sim_config, "custom_cash", 0.0)
    original_overlay_tax_impacts = getattr(sim_config, "overlay_tax_impacts", False)
    original_overlay_fund_expense_impacts = getattr(sim_config, "overlay_fund_expense_impacts", False)
    original_historical_window_stride = sim_config.historical_window_stride

    cases = []

    try:
        # Asset Allocation Comparison operates on the investable portfolio.
        # Real estate is excluded from both deterministic and Historical Window comparisons.
        sim_config.include_realestate = False

        # Depletion is calculated directly from the Historical Window results.
        sim_config.show_simulated_shortfall_rate = False
        sim_config.calculate_simulated_shortfall_rate = False
        sim_config.monte_carlo_plot_style = "fill"

        # Prevent run_pipeline() from performing unrelated overlay simulations for every case.
        sim_config.overlay_tax_impacts = False
        sim_config.overlay_fund_expense_impacts = False

        # All comparison cases use the same custom allocation semantics.
        sim_config.sim_initial_allocation_mode = "custom"

        for equity_percentage in simulation_equity_percentages:
            allocation = _derive_allocation(float(equity_percentage) / 100.0, current_allocation)

            sim_config.custom_stock = allocation["equity"]
            sim_config.custom_bonds = allocation["bonds"]
            sim_config.custom_cash = allocation["cash"]

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
            sim_config.monte_carlo_mode = "rollingHistoricalWindows"

            # Comparison allocations use a subset of Historical Windows for speed.
            sim_config.historical_window_stride = 2
            #sim_config.historical_window_stride = 4

            historical_pipeline_result = run_pipeline(
                husband_portfolio,
                wife_portfolio,
                husband,
                wife,
                expenses,
                sim_config,
                force_num_sims=None,
            )

            highlight_only = not any(
                abs(float(equity_percentage) - requested_percentage) < 1e-9
                for requested_percentage in requested_equity_percentages
            )

            cases.append(
                _build_case_result(
                    allocation,
                    deterministic_pipeline_result,
                    historical_pipeline_result,
                    is_current_allocation=False,
                    highlight_only=highlight_only,
                )
            )

        # -----------------------------------------------------
        # User's actual current allocation
        # -----------------------------------------------------

        sim_config.custom_stock = current_allocation["equity"]
        sim_config.custom_bonds = current_allocation["bonds"]
        sim_config.custom_cash = current_allocation["cash"]

        # Deterministic projection

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

        # Historical Window risk analysis

        sim_config.subplot_mode = "monte_carlo"
        sim_config.sim_type = "portfolio_sim"
        sim_config.monte_carlo_mode = "rollingHistoricalWindows"

        # Current allocation is the baseline and uses all Historical Windows.
        sim_config.historical_window_stride = 1

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
                current_allocation,
                deterministic_pipeline_result,
                historical_pipeline_result,
                is_current_allocation=True,
            )
        )

        report_metadata = _build_report_metadata(sim_config)

        historical_plot_assets = _generate_historical_allocation_plots(
            cases=cases,
            current_equity_percentage=current_equity_percentage,
            sim_config=sim_config,
            husband=husband,
            wife=wife,
            report_id=report_metadata["Report ID"],
        )

    finally:
        sim_config.subplot_mode = original_subplot_mode
        sim_config.sim_type = original_sim_type
        sim_config.monte_carlo_mode = original_monte_carlo_mode
        sim_config.monte_carlo_plot_style = original_monte_carlo_plot_style
        sim_config.include_realestate = original_include_realestate
        sim_config.show_simulated_shortfall_rate = original_show_simulated_shortfall_rate
        sim_config.calculate_simulated_shortfall_rate = original_calculate_shortfall_rate
        sim_config.sim_initial_allocation_mode = original_initial_allocation_mode
        sim_config.custom_stock = original_custom_stock
        sim_config.custom_bonds = original_custom_bonds
        sim_config.custom_cash = original_custom_cash
        sim_config.overlay_tax_impacts = original_overlay_tax_impacts
        sim_config.overlay_fund_expense_impacts = original_overlay_fund_expense_impacts
        sim_config.historical_window_stride = original_historical_window_stride

    cases.sort(key=lambda case: (case["equity_percentage"], 1 if case["is_current_allocation"] else 0))

    report_current_allocation = {
        "equity_percentage": 100.0 * current_allocation["equity"],
        "bond_percentage": 100.0 * current_allocation["bonds"],
        "cash_percentage": 100.0 * current_allocation["cash"],
    }

    report_data = AssetAllocationComparisonReportData(
        report_options=report_options,
        report_metadata=report_metadata,
        current_allocation=report_current_allocation,
        comparison_cases=cases,
        historical_plot_assets=historical_plot_assets,
        warnings=[],
    )

    return generate_asset_allocation_comparison_report(report_data)

