import numpy as np

from src.warpsimlab.sim.simulation import run_pipeline


def run_case(make_case, **overrides):
    husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config = make_case(**overrides)

    result = run_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
    )

    return result["core"], sim_config


def test_rebalancing_does_not_change_total_assets_when_all_asset_class_returns_match(make_case):
    dont_core, dont_cfg = run_case(
        make_case,
        sim_rebalance="dont-rebalance",
        rebalance_every_year=False,
        second_person_enabled=True,
        eq_mean=0.04,
        bd_mean=0.04,
        cs_mean=0.04,
        re_mean=0.04,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_std=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        calculate_income_taxes=False,
        calculate_state_taxes=False,
        use_fund_expenses=False,
        include_realestate=False,
        years_to_simulate=5,
    )

    reb_core, reb_cfg = run_case(
        make_case,
        sim_rebalance="maintain-current-allocation",
        rebalance_every_year=True,
        second_person_enabled=True,
        eq_mean=0.04,
        bd_mean=0.04,
        cs_mean=0.04,
        re_mean=0.04,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_std=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        calculate_income_taxes=False,
        calculate_state_taxes=False,
        use_fund_expenses=False,
        include_realestate=False,
        years_to_simulate=5,
    )

    np.testing.assert_allclose(
        dont_core["total_assets"],
        reb_core["total_assets"],
        rtol=0.0,
        atol=1e-8,
    )


def test_rebalancing_does_not_change_pre_tax_assets_when_all_asset_class_returns_match(make_case):
    dont_core, dont_cfg = run_case(
        make_case,
        sim_rebalance="dont-rebalance",
        rebalance_every_year=False,
        second_person_enabled=True,
        eq_mean=0.04,
        bd_mean=0.04,
        cs_mean=0.04,
        re_mean=0.04,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_std=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        calculate_income_taxes=False,
        calculate_state_taxes=False,
        use_fund_expenses=False,
        include_realestate=False,
        years_to_simulate=5,
    )

    reb_core, reb_cfg = run_case(
        make_case,
        sim_rebalance="maintain-current-allocation",
        rebalance_every_year=True,
        second_person_enabled=True,
        eq_mean=0.04,
        bd_mean=0.04,
        cs_mean=0.04,
        re_mean=0.04,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_std=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        calculate_income_taxes=False,
        calculate_state_taxes=False,
        use_fund_expenses=False,
        include_realestate=False,
        years_to_simulate=5,
    )

    np.testing.assert_allclose(
        dont_core["pre_tax_assets"],
        reb_core["pre_tax_assets"],
        rtol=0.0,
        atol=1e-8,
    )


def test_rebalancing_does_not_change_post_tax_assets_when_all_asset_class_returns_match(make_case):
    dont_core, dont_cfg = run_case(
        make_case,
        sim_rebalance="dont-rebalance",
        rebalance_every_year=False,
        second_person_enabled=True,
        eq_mean=0.04,
        bd_mean=0.04,
        cs_mean=0.04,
        re_mean=0.04,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_std=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        calculate_income_taxes=False,
        calculate_state_taxes=False,
        use_fund_expenses=False,
        include_realestate=False,
        years_to_simulate=5,
    )

    reb_core, reb_cfg = run_case(
        make_case,
        sim_rebalance="maintain-current-allocation",
        rebalance_every_year=True,
        second_person_enabled=True,
        eq_mean=0.04,
        bd_mean=0.04,
        cs_mean=0.04,
        re_mean=0.04,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_std=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        calculate_income_taxes=False,
        calculate_state_taxes=False,
        use_fund_expenses=False,
        include_realestate=False,
        years_to_simulate=5,
    )

    np.testing.assert_allclose(
        dont_core["post_tax_assets"],
        reb_core["post_tax_assets"],
        rtol=0.0,
        atol=1e-8,
    )