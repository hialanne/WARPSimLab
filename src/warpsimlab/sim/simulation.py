# simulation.py

import numpy as np

from src.warpsimlab.plots.portfolioPlotData import PortfolioPlotData
from .run_sim_core import simulate_yearly_portfolios
from .engines.statsCollector import compute_portfolio_statistics, optional_stats
from .run_sim_risk_reports import (run_sim_historical_window_risk_report,run_sim_monte_carlo_risk_report,)


def _is_historical_window_mode(sim_config):
    return (
        sim_config.subplot_mode == "monte_carlo"
        and getattr(sim_config, "monte_carlo_mode", "pathBasedAnnualSampling") == "rollingHistoricalWindows"
        and sim_config.sim_type == "portfolio_sim"
    )


def _extract_income_single_run(core):
    """
    Extract single-run (0th sim) income arrays for plotting.
    """
    net_income = core["net_income"][0]
    net_profit = core["net_profit"][0]
    breakdown = {k: v[0] for k, v in core["breakdown_by_class"].items()}
    taxes = core["taxes"][0]
    expense_amt = core["expense_amt"][0]
    return net_income, net_profit, breakdown, taxes, expense_amt


def _extract_summary_single_run(core, simulated_shortfall_rate=None):
    """
    Build the summary_results dict exactly as run_sim_summary.py currently does.
    """
    r = core
    return {
        "year": r["year"][0],
        "total_assets": r["total_assets"][0],
        "pre_tax_assets": r["pre_tax_assets"][0],
        "post_tax_assets": r["post_tax_assets"][0],
        "roth_assets": r["roth_assets"][0],
        "hsa_assets": r["hsa_assets"][0],
        "real_estate": r["real_estate"][0],
        "gross_income": r["gross_income"][0],
        "net_income": r["net_income"][0],
        "taxes": r["taxes"][0],
        "payroll_tax": r["payroll_tax"][0],
        "social_security_payroll_tax": r["social_security_payroll_tax"][0],
        "medicare_tax": r["medicare_tax"][0],
        "additional_medicare_tax": r["additional_medicare_tax"][0],
        "tax_bracket": r["tax_bracket"][0],
        "federal_ordinary_tax": r["federal_ordinary_tax"][0],
        "federal_qualified_dividend_tax": r["federal_qualified_dividend_tax"][0],
        "state_income_tax": r["state_income_tax"][0],
        "emergency_pre_tax_used": r["emergency_pre_tax_used"][0],
        "final_tax_delta": r["final_tax_delta"][0],
        "final_tax_delta_deducted": r["final_tax_delta_deducted"][0],
        "final_tax_delta_uncovered": r["final_tax_delta_uncovered"][0],
        "roth_withdrawals": r["roth_withdrawals"][0],
        "hsa_withdrawals": r["hsa_withdrawals"][0],
        "expenses": r["expense_amt"][0],
        "net_cash_flow": r["net_profit"][0],
        "wages": r["breakdown_by_class"]["work"][0],
        "rmd": r["breakdown_by_class"]["rmd"][0],
        "ira_401k": r["ira_401k"][0],
        "roth_ira_contributions": (
            r["roth_ira_contributions"][0]
        ),
        "roth_workplace_contributions": (
            r["roth_workplace_contributions"][0]
        ),
        "roth_conversions": (
            r["roth_conversions"][0]
        ),
        "roth_total_flows": (
            r["roth_total_flows"][0]
        ),
        "social_security": r["breakdown_by_class"]["ss"][0],
        "pensions": r["breakdown_by_class"]["pension"][0],
        "annuities": r["breakdown_by_class"]["annuity"][0],
        "withdrawal": r["breakdown_by_class"]["withdrawal"][0],
        "fund_expenses": r["fund_expenses"][0],
        "bond_interest": r["breakdown_by_class"]["bond_interest"][0],
        "cash_interest": r["breakdown_by_class"]["cash_interest"][0],
        "qualified_dividends": r["breakdown_by_class"]["qualified_dividends"][0],
        "simulated_shortfall_rate": simulated_shortfall_rate,
    }


def _build_portfolio_plot_data(core, sim_config):
    """
    Construct PortfolioPlotData using the same logic currently in:
    - run_sim_portfolio.py
    - gui_scenarioController.py (scenario path)
    """
    years = sim_config.years_to_simulate
    years_list = np.arange(0, years + 1)

    total_assets = core["total_assets"]
    cash = core["cash"]
    bonds = core["bonds"]
    real_estate = core["real_estate"]
    pre_tax_assets = core["pre_tax_assets"]
    post_tax_assets = core["post_tax_assets"]
    roth_assets = core.get("roth_assets")
    hsa_assets = core.get("hsa_assets")

    percentiles = compute_portfolio_statistics(total_assets, years, sim_config.inflation_rate)

    cash_series = None
    bonds_series = None
    realestate_series = None
    pre_tax_series = None
    post_tax_series = None
    roth_series = None
    hsa_series = None

    if sim_config.subplot_mode == "sub_categories":
        cash_series = optional_stats(cash, years, sim_config.inflation_rate, enabled=True)
        bonds_series = optional_stats(bonds, years, sim_config.inflation_rate, enabled=True)

        if sim_config.include_realestate:
            realestate_series = optional_stats(real_estate, years, sim_config.inflation_rate, enabled=True)
        else:
            realestate_series = np.zeros(years + 1)

    elif sim_config.subplot_mode == "pre_post_tax":
        pre_tax_series = optional_stats(pre_tax_assets, years, sim_config.inflation_rate, enabled=True)
        post_tax_series = optional_stats(post_tax_assets, years, sim_config.inflation_rate, enabled=True)
        roth_series = optional_stats(roth_assets, years, sim_config.inflation_rate, enabled=roth_assets is not None)
        hsa_series = optional_stats(hsa_assets, years, sim_config.inflation_rate, enabled=hsa_assets is not None)

        if sim_config.include_realestate:
            realestate_series = optional_stats(real_estate, years, sim_config.inflation_rate, enabled=True)

    return PortfolioPlotData(
        years=years_list,
        percentiles=percentiles,
        cash=cash_series,
        bonds=bonds_series,
        realestate=realestate_series,
        pre_tax_assets=pre_tax_series,
        post_tax_assets=post_tax_series,
        roth_assets=roth_series,
        hsa_assets=hsa_series,
        raw_total_assets=total_assets,
    )


def _run_overlay_total_assets_line(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config):
    """
    Deterministic (num_sims=1) overlay line for total assets.
    Core handles plot_mode 'real' deflation internally.
    """
    overlay_core = simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        num_sims=1,
    )
    return overlay_core["total_assets"][0]


def _calculate_shortfall_rate_from_total_assets(total_assets):
    total_assets = np.asarray(total_assets)

    if total_assets.ndim != 2:
        raise ValueError(f"Expected 2D total_assets array, got shape {total_assets.shape}")

    path_mins = np.min(total_assets, axis=1)
    failed_mask = np.any(total_assets <= 0.0, axis=1)

    #print("[SHORTFALL DEBUG]")
    #print("shape:", total_assets.shape)
    #print("min overall:", np.min(total_assets))
    #print("failed count:", np.sum(failed_mask))
    #print("failed pct:", failed_mask.mean() * 100.0)
    #print("path mins sorted first 20:", np.sort(path_mins)[:20])

    return float(failed_mask.mean() * 100.0)


def _compute_simulated_shortfall_rate(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
    num_sims=1000,
):
    """
    Run Monte Carlo paths and compute the fraction of scenarios that ever
    reach a portfolio balance of 0 or below at any simulated year.
    Returns a percentage in the range [0.0, 100.0].
    """
    if num_sims <= 0:
        raise ValueError("num_sims must be > 0 for simulated shortfall rate")

    original_subplot_mode = sim_config.subplot_mode
    original_sim_type = sim_config.sim_type

    try:
        # Force the helper run to use the same Monte Carlo path-selection
        # logic as the portfolio simulation, including rolling historical windows.
        sim_config.subplot_mode = "monte_carlo"
        sim_config.sim_type = "portfolio_sim"

        mc_core = simulate_yearly_portfolios(
            husband_portfolio,
            wife_portfolio,
            husband,
            wife,
            expenses,
            sim_config,
            num_sims=num_sims,
        )
    finally:
        sim_config.subplot_mode = original_subplot_mode
        sim_config.sim_type = original_sim_type

    total_assets = np.asarray(mc_core["total_assets"])
    if total_assets.ndim != 2:
        raise ValueError(f"Expected 2D total_assets array, got shape {total_assets.shape}")

    failed_mask = np.any(total_assets <= 0.0, axis=1)
    return float(failed_mask.mean() * 100.0)


def run_pipeline(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config, *, force_num_sims=None):
    """
    Returns a dict with:
      - years, years_list
      - core (raw)
      - net_income, net_profit, breakdown_by_class, taxes, expense_amt
      - summary_results
      - portfolio_plot_data (with overlays attached when enabled)
    """
    years = sim_config.years_to_simulate
    years_list = np.arange(0, years + 1)

    # Centralized sim count policy (matches existing portfolio behavior)
    num_sims = sim_config.num_sims if force_num_sims is None else int(force_num_sims)
    if sim_config.subplot_mode != "monte_carlo":
        num_sims = 1

    # Note:
    # In rollingHistoricalWindows mode, simulate_yearly_portfolios()
    # will internally override the effective simulation count to the
    # number of valid overlapping historical windows.

    # Baseline core run
    core = simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        num_sims=num_sims,
    )

    # Extract views
    net_income, net_profit, breakdown, taxes, expense_amt = _extract_income_single_run(core)
    portfolio_plot_data = _build_portfolio_plot_data(core, sim_config)

    simulated_shortfall_rate = None

    simulated_shortfall_rate = None

    if sim_config.show_simulated_shortfall_rate:
        primary_run_is_multi_path_portfolio = (
            sim_config.subplot_mode == "monte_carlo"
            and sim_config.sim_type == "portfolio_sim"
        )

        if primary_run_is_multi_path_portfolio:
            simulated_shortfall_rate = _calculate_shortfall_rate_from_total_assets(
                core["total_assets"]
            )
        elif sim_config.sim_type != "cashflow_sim":
            simulated_shortfall_rate = _compute_simulated_shortfall_rate(
                husband_portfolio,
                wife_portfolio,
                husband,
                wife,
                expenses,
                sim_config,
                num_sims=1000,
            )

        portfolio_plot_data.simulated_shortfall_rate = simulated_shortfall_rate

    summary_results = _extract_summary_single_run(
        core,
        simulated_shortfall_rate=simulated_shortfall_rate,
    )

    # Attach overlay lines (same toggles as existing portfolio runner)
    if getattr(sim_config, "overlay_tax_impacts", False):
        original = sim_config.calculate_income_taxes
        sim_config.calculate_income_taxes = False
        try:
            portfolio_plot_data.median_without_taxes = _run_overlay_total_assets_line(
                husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config
            )
        finally:
            sim_config.calculate_income_taxes = original

    if getattr(sim_config, "overlay_fund_expense_impacts", False):
        original = sim_config.use_fund_expenses
        sim_config.use_fund_expenses = False
        try:
            portfolio_plot_data.median_without_fund_expenses = _run_overlay_total_assets_line(
                husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config
            )
        finally:
            sim_config.use_fund_expenses = original

    if getattr(sim_config, "overlay_tax_impacts", False) and getattr(sim_config, "overlay_fund_expense_impacts", False):
        orig_tax = sim_config.calculate_income_taxes
        orig_fund = sim_config.use_fund_expenses
        sim_config.calculate_income_taxes = False
        sim_config.use_fund_expenses = False
        try:
            portfolio_plot_data.median_without_taxes_or_fund_expenses = _run_overlay_total_assets_line(
                husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config
            )
        finally:
            sim_config.calculate_income_taxes = orig_tax
            sim_config.use_fund_expenses = orig_fund

    return {
        "years": years,
        "years_list": years_list,
        "core": core,
        "net_income": net_income,
        "net_profit": net_profit,
        "breakdown_by_class": breakdown,
        "taxes": taxes,
        "expense_amt": expense_amt,
        "summary_results": summary_results,
        "portfolio_plot_data": portfolio_plot_data,
    }


def run_simulation(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config):
    """
    Dispatcher. Pattern A: import mode runners inside the function
    to avoid circular imports when runners later import run_pipeline.
    """
    # Import locally (Pattern A)
    from .run_sim_portfolio import run_sim_portfolio
    from .run_sim_income import run_sim_income
    from .run_sim_summary import run_sim_summary
    from .run_sim_operating_balance import run_sim_operating_balance
    from .run_sim_summary_report import run_sim_summary_report
    from .run_sim_year_by_year_report import run_sim_year_by_year_report
    from .run_sim_tax_report import run_sim_tax_report

    # debug_dump_simulation(sim_config)

    if sim_config.sim_type in {"income_sim", "cashflow_sim"}:
        return run_sim_income(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config)

    if sim_config.sim_type == "operating_balance_sim":
        return run_sim_operating_balance(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config)

    if sim_config.sim_type == "portfolio_sim":
        return run_sim_portfolio(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config)

    if sim_config.sim_type == "summary_sim":
        return run_sim_summary(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config)

    if sim_config.sim_type == "summary_report":
        return run_sim_summary_report(
            husband_portfolio,
            wife_portfolio,
            husband,
            wife,
            expenses,
            sim_config
        )

    if sim_config.sim_type == "year_by_year_report":
        return run_sim_year_by_year_report(
            husband_portfolio,
            wife_portfolio,
            husband,
            wife,
            expenses,
            sim_config
        )

    if sim_config.sim_type == "tax_report":
        return run_sim_tax_report(
            husband_portfolio,
            wife_portfolio,
            husband,
            wife,
            expenses,
            sim_config
        )

    if sim_config.sim_type == "historical_window_risk_report":
        return run_sim_historical_window_risk_report(
            husband_portfolio,
            wife_portfolio,
            husband,
            wife,
            expenses,
            sim_config,
        )

    if sim_config.sim_type == "monte_carlo_risk_report":
        return run_sim_monte_carlo_risk_report(
            husband_portfolio,
            wife_portfolio,
            husband,
            wife,
            expenses,
            sim_config,
        )
