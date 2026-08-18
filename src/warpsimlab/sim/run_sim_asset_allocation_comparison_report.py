# run_sim_asset_allocation_comparison_report.py

import numpy as np

from .simulation import run_pipeline

from datetime import datetime

from src.warpsimlab.reports.report_data import (
    AssetAllocationComparisonReportData,
)

from src.warpsimlab.reports.asset_allocation_comparison_report import (
    generate_asset_allocation_comparison_report,
)


def _build_report_metadata(sim_config):
    start_year = int(
        getattr(
            sim_config,
            "start_year",
            0,
        )
    )

    years = int(
        getattr(
            sim_config,
            "years_to_simulate",
            0,
        )
    )

    end_year = (
        start_year + years
    )

    now = datetime.now()

    return {
        "Report Title": (
            "Asset Allocation Comparison Report"
        ),
        "Generated Timestamp": (
            now.isoformat(
                timespec="seconds"
            )
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
            else (
                "Raw Dollars "
                "(Future Nominal Values)"
            )
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
        "10th_percentile": float(
            np.percentile(values, 10)
        ),
        "25th_percentile": float(
            np.percentile(values, 25)
        ),
        "median": float(
            np.median(values)
        ),
        "75th_percentile": float(
            np.percentile(values, 75)
        ),
        "90th_percentile": float(
            np.percentile(values, 90)
        ),
        "maximum": float(
            np.max(values)
        ),
    }


def _build_depletion_statistics(
    total_assets,
    years,
):
    total_assets = np.asarray(
        total_assets,
        dtype=float,
    )

    years = np.asarray(years)

    scenario_count = int(
        total_assets.shape[0]
    )

    depleted_mask = np.any(
        total_assets <= 0.0,
        axis=1,
    )

    depleted_count = int(
        np.sum(depleted_mask)
    )

    depleted_percent = (
        100.0
        * depleted_count
        / scenario_count
        if scenario_count > 0
        else 0.0
    )

    depletion_years = []

    for path in total_assets[depleted_mask]:
        indices = np.where(
            path <= 0.0
        )[0]

        if len(indices) == 0:
            continue

        index = int(indices[0])

        try:
            depletion_years.append(
                int(years[index])
            )
        except (
            IndexError,
            TypeError,
            ValueError,
        ):
            pass

    if depletion_years:
        earliest_year = int(
            min(depletion_years)
        )

        median_year = int(
            np.median(depletion_years)
        )

        latest_year = int(
            max(depletion_years)
        )
    else:
        earliest_year = None
        median_year = None
        latest_year = None

    return {
        "historical_window_count": scenario_count,
        "windows_reaching_zero_count": (
            depleted_count
        ),
        "windows_reaching_zero_percent": (
            float(depleted_percent)
        ),
        "earliest_reaching_zero_year": (
            earliest_year
        ),
        "median_reaching_zero_year": (
            median_year
        ),
        "latest_reaching_zero_year": (
            latest_year
        ),
    }


def _portfolio_components(portfolio):
    if portfolio is None:
        return 0.0, 0.0, 0.0

    equity = (
        float(
            getattr(
                portfolio,
                "equity_pre",
                0.0,
            )
        )
        + float(
            getattr(
                portfolio,
                "equity_post",
                0.0,
            )
        )
        + float(
            getattr(
                portfolio,
                "equity_roth",
                0.0,
            )
        )
        + float(
            getattr(
                portfolio,
                "hsa_equity",
                0.0,
            )
        )
    )

    bonds = (
        float(
            getattr(
                portfolio,
                "bond_pre",
                0.0,
            )
        )
        + float(
            getattr(
                portfolio,
                "bond_post",
                0.0,
            )
        )
        + float(
            getattr(
                portfolio,
                "bond_roth",
                0.0,
            )
        )
        + float(
            getattr(
                portfolio,
                "hsa_bond",
                0.0,
            )
        )
    )

    cash = (
        float(
            getattr(
                portfolio,
                "cash_pre",
                0.0,
            )
        )
        + float(
            getattr(
                portfolio,
                "cash_post",
                0.0,
            )
        )
        + float(
            getattr(
                portfolio,
                "cash_roth",
                0.0,
            )
        )
        + float(
            getattr(
                portfolio,
                "hsa_cash",
                0.0,
            )
        )
    )

    return equity, bonds, cash


def _current_household_allocation(
    husband_portfolio,
    wife_portfolio,
    sim_config,
):
    h_equity, h_bonds, h_cash = (
        _portfolio_components(
            husband_portfolio
        )
    )

    w_equity = 0.0
    w_bonds = 0.0
    w_cash = 0.0

    if (
        getattr(
            sim_config,
            "second_person_enabled",
            False,
        )
        and wife_portfolio is not None
    ):
        (
            w_equity,
            w_bonds,
            w_cash,
        ) = _portfolio_components(
            wife_portfolio
        )

    total_equity = (
        h_equity + w_equity
    )

    total_bonds = (
        h_bonds + w_bonds
    )

    total_cash = (
        h_cash + w_cash
    )

    total = (
        total_equity
        + total_bonds
        + total_cash
    )

    if total <= 0.0:
        return {
            "equity": 0.0,
            "bonds": 0.0,
            "cash": 1.0,
        }

    return {
        "equity": (
            total_equity / total
        ),
        "bonds": (
            total_bonds / total
        ),
        "cash": (
            total_cash / total
        ),
    }


def _derive_allocation(
    equity_ratio,
    current_allocation,
):
    equity_ratio = float(
        equity_ratio
    )

    non_equity_ratio = (
        1.0 - equity_ratio
    )

    current_bonds = float(
        current_allocation["bonds"]
    )

    current_cash = float(
        current_allocation["cash"]
    )

    current_non_equity = (
        current_bonds
        + current_cash
    )

    if current_non_equity <= 1e-12:
        if non_equity_ratio <= 1e-12:
            return {
                "equity": equity_ratio,
                "bonds": 0.0,
                "cash": 0.0,
            }

        raise ValueError(
            "Asset Allocation Comparison cannot "
            "derive bond and cash allocations because "
            "the current portfolio contains no bonds "
            "or cash."
        )

    bond_share = (
        current_bonds
        / current_non_equity
    )

    cash_share = (
        current_cash
        / current_non_equity
    )

    return {
        "equity": equity_ratio,
        "bonds": (
            non_equity_ratio
            * bond_share
        ),
        "cash": (
            non_equity_ratio
            * cash_share
        ),
    }


def _build_case_result(
    allocation,
    pipeline_result,
    *,
    is_current_allocation=False,
    highlight_only=False,
):
    core = pipeline_result["core"]

    total_assets = np.asarray(
        core["total_assets"],
        dtype=float,
    )

    years = np.asarray(
        core["year"][0]
    )

    ending_portfolios = (
        total_assets[:, -1]
    )

    minimum_portfolios = np.min(
        total_assets,
        axis=1,
    )

    lifetime_expenses = np.sum(
        np.asarray(
            core["expense_amt"],
            dtype=float,
        ),
        axis=1,
    )

    lifetime_taxes = np.sum(
        np.asarray(
            core["taxes"],
            dtype=float,
        ),
        axis=1,
    )

    lifetime_cash_flow_shortfall = (
        np.sum(
            np.asarray(
                core[
                    "cash_flow_shortfall"
                ],
                dtype=float,
            ),
            axis=1,
        )
    )

    lifetime_uncovered_expense = (
        np.sum(
            np.asarray(
                core[
                    "uncovered_expense"
                ],
                dtype=float,
            ),
            axis=1,
        )
    )

    return {
        "equity_percentage": (
            100.0
            * allocation["equity"]
        ),
        "bond_percentage": (
            100.0
            * allocation["bonds"]
        ),
        "cash_percentage": (
            100.0
            * allocation["cash"]
        ),
        "is_current_allocation": bool(
            is_current_allocation
        ),
        "highlight_only": bool(
            highlight_only
        ),
        "depletion": (
            _build_depletion_statistics(
                total_assets,
                years,
            )
        ),

        "ending_portfolio": (
            _distribution(
                ending_portfolios
            )
        ),

        "minimum_portfolio": (
            _distribution(
                minimum_portfolios
            )
        ),

        "lifetime_expenses": (
            _distribution(
                lifetime_expenses
            )
        ),

        "lifetime_taxes": (
            _distribution(
                lifetime_taxes
            )
        ),

        "lifetime_cash_flow_shortfall": (
            _distribution(
                lifetime_cash_flow_shortfall
            )
        ),

        "lifetime_uncovered_expense": (
            _distribution(
                lifetime_uncovered_expense
            )
        ),
    }


def run_sim_asset_allocation_comparison_report(
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

    equity_percentages = (
        report_options.get(
            "equity_percentages",
            [],
        )
    )

    requested_equity_percentages = [
        float(value)
        for value in equity_percentages
    ]

    current_allocation = (
        _current_household_allocation(
            husband_portfolio,
            wife_portfolio,
            sim_config,
        )
    )

    current_equity_percentage = (
        100.0 * current_allocation["equity"]
    )

    highlight_equity_percentages = [
        max(
            0.0,
            current_equity_percentage - 20.0,
        ),
        min(
            100.0,
            current_equity_percentage + 20.0,
        ),
    ]

    simulation_equity_percentages = list(
        requested_equity_percentages
    )

    for equity_percentage in highlight_equity_percentages:
        if not any(
            abs(
                equity_percentage - existing_percentage
            ) < 1e-9
            for existing_percentage
            in simulation_equity_percentages
        ):
            simulation_equity_percentages.append(
                equity_percentage
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

    original_show_simulated_shortfall_rate = (
        getattr(
            sim_config,
            "show_simulated_shortfall_rate",
            None,
        )
    )

    original_initial_allocation_mode = (
        getattr(
            sim_config,
            "sim_initial_allocation_mode",
            None,
        )
    )

    original_custom_stock = getattr(
        sim_config,
        "custom_stock",
        0.0,
    )

    original_custom_bonds = getattr(
        sim_config,
        "custom_bonds",
        0.0,
    )

    original_custom_cash = getattr(
        sim_config,
        "custom_cash",
        0.0,
    )

    original_overlay_tax_impacts = (
        getattr(
            sim_config,
            "overlay_tax_impacts",
            False,
        )
    )

    original_overlay_fund_expense_impacts = (
        getattr(
            sim_config,
            "overlay_fund_expense_impacts",
            False,
        )
    )

    cases = []

    try:
        sim_config.subplot_mode = (
            "monte_carlo"
        )

        sim_config.sim_type = (
            "portfolio_sim"
        )

        sim_config.monte_carlo_mode = (
            "rollingHistoricalWindows"
        )

        # Match existing Historical Window
        # risk-report semantics.
        sim_config.include_realestate = False

        sim_config.show_simulated_shortfall_rate = (
            False
        )

        # Prevent run_pipeline() from performing
        # additional overlay simulations for
        # every ensemble member.
        sim_config.overlay_tax_impacts = False

        sim_config.overlay_fund_expense_impacts = (
            False
        )

        # All comparison cases use the same
        # allocation semantics.
        sim_config.sim_initial_allocation_mode = (
            "custom"
        )

        for equity_percentage in simulation_equity_percentages:
            allocation = _derive_allocation(
                float(equity_percentage)
                / 100.0,
                current_allocation,
            )

            sim_config.custom_stock = (
                allocation["equity"]
            )

            sim_config.custom_bonds = (
                allocation["bonds"]
            )

            sim_config.custom_cash = (
                allocation["cash"]
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

            highlight_only = not any(
                abs(
                    float(equity_percentage)
                    - requested_percentage
                ) < 1e-9
                for requested_percentage
                in requested_equity_percentages
            )

            cases.append(
                _build_case_result(
                    allocation,
                    pipeline_result,
                    is_current_allocation=False,
                    highlight_only=highlight_only,
                )
            )

        # Run the user's actual current allocation
        # as the baseline case.
        sim_config.custom_stock = (
            current_allocation["equity"]
        )

        sim_config.custom_bonds = (
            current_allocation["bonds"]
        )

        sim_config.custom_cash = (
            current_allocation["cash"]
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
                current_allocation,
                pipeline_result,
                is_current_allocation=True,
            )
        )

    finally:
        sim_config.subplot_mode = (
            original_subplot_mode
        )

        sim_config.sim_type = (
            original_sim_type
        )

        sim_config.monte_carlo_mode = (
            original_monte_carlo_mode
        )

        sim_config.include_realestate = (
            original_include_realestate
        )

        sim_config.show_simulated_shortfall_rate = (
            original_show_simulated_shortfall_rate
        )

        sim_config.sim_initial_allocation_mode = (
            original_initial_allocation_mode
        )

        sim_config.custom_stock = (
            original_custom_stock
        )

        sim_config.custom_bonds = (
            original_custom_bonds
        )

        sim_config.custom_cash = (
            original_custom_cash
        )

        sim_config.overlay_tax_impacts = (
            original_overlay_tax_impacts
        )

        sim_config.overlay_fund_expense_impacts = (
            original_overlay_fund_expense_impacts
        )

    cases.sort(
        key=lambda case: (
            case["equity_percentage"],
            1
            if case[
                "is_current_allocation"
            ]
            else 0,
        )
    )

    report_current_allocation = {
        "equity_percentage": (
            100.0
            * current_allocation[
                "equity"
            ]
        ),
        "bond_percentage": (
            100.0
            * current_allocation[
                "bonds"
            ]
        ),
        "cash_percentage": (
            100.0
            * current_allocation[
                "cash"
            ]
        ),
    }

    report_data = (
        AssetAllocationComparisonReportData(
            report_options=report_options,
            report_metadata=(
                _build_report_metadata(
                    sim_config
                )
            ),
            current_allocation=(
                report_current_allocation
            ),
            comparison_cases=cases,
            warnings=[],
        )
    )

    return (
        generate_asset_allocation_comparison_report(
            report_data
        )
    )
