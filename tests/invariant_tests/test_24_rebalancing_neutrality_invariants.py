import numpy as np

from src.warpsimlab.sim.engines import portfolioEngine
from src.warpsimlab.sim.simulation import run_pipeline


COMMON_PIPELINE_OVERRIDES = {
    "second_person_enabled": True,
    "eq_mean": 0.04,
    "bd_mean": 0.04,
    "cs_mean": 0.04,
    "re_mean": 0.04,
    "eq_std": 0.0,
    "bd_std": 0.0,
    "cs_std": 0.0,
    "re_std": 0.0,
    "post_tax_equity_dividend_yield": 0.0,
    "post_tax_bond_interest_yield": 0.0,
    "post_tax_cash_interest_yield": 0.0,
    "calculate_income_taxes": False,
    "calculate_payroll_taxes": False,
    "calculate_state_taxes": False,
    "use_fund_expenses": False,
    "include_realestate": False,
    "years_to_simulate": 5,
}


def run_case(make_case, **overrides):
    husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config = (
        make_case(**overrides)
    )

    result = run_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
    )

    return result["core"], sim_config


def run_rebalancing_pair(make_case, **extra_overrides):
    dont_core, _ = run_case(
        make_case,
        **COMMON_PIPELINE_OVERRIDES,
        **extra_overrides,
        sim_initial_allocation_mode="dont-rebalance",
        rebalance_every_year=False,
    )

    reb_core, _ = run_case(
        make_case,
        **COMMON_PIPELINE_OVERRIDES,
        **extra_overrides,
        sim_initial_allocation_mode="maintain-current-allocation",
        rebalance_every_year=True,
    )

    return dont_core, reb_core


def test_rebalancing_does_not_change_total_assets_for_non_taxable_accounts_when_returns_match(
    make_case,
):
    """
    With no taxable assets, equal equity/bond/cash returns make annual
    rebalancing neutral to total household assets.

    Taxable accounts are excluded because positive taxable bond and cash
    returns are modeled as current income rather than retained account growth.
    """
    dont_core, reb_core = run_rebalancing_pair(
        make_case,
        husband_equity_post=0.0,
        husband_bond_post=0.0,
        husband_cash_post=0.0,
        wife_equity_post=0.0,
        wife_bond_post=0.0,
        wife_cash_post=0.0,

        husband_income=0.0,
        husband_ss=0.0,
        husband_pension=0.0,
        husband_annuity=0.0,
        husband_annual_401k_contribution=0.0,
        husband_annual_employer_match=0.0,

        wife_income=0.0,
        wife_ss=0.0,
        wife_pension=0.0,
        wife_annuity=0.0,
        wife_annual_401k_contribution=0.0,
        wife_annual_employer_match=0.0,

        annual_expense=0.0,
    )

    np.testing.assert_allclose(
        dont_core["total_assets"],
        reb_core["total_assets"],
        rtol=0.0,
        atol=1e-8,
    )


def test_rebalancing_does_not_change_pre_tax_assets_when_all_asset_class_returns_match(
    make_case,
):
    dont_core, reb_core = run_rebalancing_pair(make_case)

    np.testing.assert_allclose(
        dont_core["pre_tax_assets"],
        reb_core["pre_tax_assets"],
        rtol=0.0,
        atol=1e-8,
    )


def test_rebalance_operation_preserves_post_tax_account_value(make_case):
    """
    The rebalance operation itself may redistribute taxable assets among
    equity, bonds, and cash, but it must not create or destroy account value.

    This deliberately tests portfolioEngine.rebalance() directly. A multi-year
    pipeline comparison would also include WARPSimLab's distinct taxable
    cash-flow treatment for equity, bond, and cash returns.
    """
    (
        husband_portfolio,
        wife_portfolio,
        _husband,
        _wife,
        _expenses,
        sim_config,
    ) = make_case(
        second_person_enabled=True,
        include_realestate=False,
        sim_initial_allocation_mode="dont-rebalance",
    )

    h_port = portfolioEngine.create_sim_portfolio(husband_portfolio, sim_config)
    w_port = portfolioEngine.create_sim_portfolio(wife_portfolio, sim_config)

    husband_before = h_port.total_value_post
    wife_before = w_port.total_value_post
    household_before = husband_before + wife_before

    sim_config.sim_initial_allocation_mode = "custom"
    sim_config.custom_stock = 0.20
    sim_config.custom_bonds = 0.30
    sim_config.custom_cash = 0.50

    portfolioEngine.rebalance(h_port, sim_config)
    portfolioEngine.rebalance(w_port, sim_config)

    np.testing.assert_allclose(
        h_port.total_value_post,
        husband_before,
        rtol=0.0,
        atol=1e-8,
    )
    np.testing.assert_allclose(
        w_port.total_value_post,
        wife_before,
        rtol=0.0,
        atol=1e-8,
    )
    np.testing.assert_allclose(
        h_port.total_value_post + w_port.total_value_post,
        household_before,
        rtol=0.0,
        atol=1e-8,
    )
