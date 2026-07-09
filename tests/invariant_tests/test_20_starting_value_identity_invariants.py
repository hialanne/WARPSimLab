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

    return result["core"], sim_config, husband_portfolio, wife_portfolio


def test_year_zero_pre_tax_and_post_tax_match_initial_inputs_single_person(make_case):
    core, cfg, husband_portfolio, wife_portfolio = run_case(
        make_case,
        second_person_enabled=False,
        include_realestate=False,
        husband_equity_pre=300000.0,
        husband_bond_pre=100000.0,
        husband_cash_pre=25000.0,
        husband_equity_post=150000.0,
        husband_bond_post=50000.0,
        husband_cash_post=25000.0,
    )

    expected_pre_tax = (
        husband_portfolio.equity_pre
        + husband_portfolio.bond_pre
        + husband_portfolio.cash_pre
    )
    expected_post_tax = (
        husband_portfolio.equity_post
        + husband_portfolio.bond_post
        + husband_portfolio.cash_post
    )

    np.testing.assert_allclose(core["pre_tax_assets"][0, 0], expected_pre_tax, rtol=0.0, atol=1e-8)
    np.testing.assert_allclose(core["post_tax_assets"][0, 0], expected_post_tax, rtol=0.0, atol=1e-8)
    np.testing.assert_allclose(core["total_assets"][0, 0], expected_pre_tax + expected_post_tax, rtol=0.0, atol=1e-8)


def test_year_zero_total_assets_match_initial_inputs_with_real_estate_and_second_person(make_case):
    core, cfg, husband_portfolio, wife_portfolio = run_case(
        make_case,
        second_person_enabled=True,
        include_realestate=True,
        husband_equity_pre=300000.0,
        husband_bond_pre=100000.0,
        husband_cash_pre=25000.0,
        husband_equity_post=150000.0,
        husband_bond_post=50000.0,
        husband_cash_post=25000.0,
        husband_real_estate=200000.0,
        wife_equity_pre=200000.0,
        wife_bond_pre=75000.0,
        wife_cash_pre=20000.0,
        wife_equity_post=100000.0,
        wife_bond_post=40000.0,
        wife_cash_post=20000.0,
        wife_real_estate=125000.0,
    )

    expected_pre_tax = (
        husband_portfolio.equity_pre
        + husband_portfolio.bond_pre
        + husband_portfolio.cash_pre
        + wife_portfolio.equity_pre
        + wife_portfolio.bond_pre
        + wife_portfolio.cash_pre
    )
    expected_post_tax = (
        husband_portfolio.equity_post
        + husband_portfolio.bond_post
        + husband_portfolio.cash_post
        + wife_portfolio.equity_post
        + wife_portfolio.bond_post
        + wife_portfolio.cash_post
    )
    expected_real_estate = husband_portfolio.real_estate + wife_portfolio.real_estate

    np.testing.assert_allclose(core["pre_tax_assets"][0, 0], expected_pre_tax, rtol=0.0, atol=1e-8)
    np.testing.assert_allclose(core["post_tax_assets"][0, 0], expected_post_tax, rtol=0.0, atol=1e-8)
    np.testing.assert_allclose(core["real_estate"][0, 0], expected_real_estate, rtol=0.0, atol=1e-8)
    np.testing.assert_allclose(
        core["total_assets"][0, 0],
        expected_pre_tax + expected_post_tax + expected_real_estate,
        rtol=0.0,
        atol=1e-8,
    )


def test_year_zero_cash_matches_initial_cash_inputs(make_case):
    core, cfg, husband_portfolio, wife_portfolio = run_case(
        make_case,
        second_person_enabled=True,
        husband_cash_pre=11111.0,
        husband_cash_post=22222.0,
        wife_cash_pre=33333.0,
        wife_cash_post=44444.0,
    )

    expected_cash = (
        husband_portfolio.cash_pre
        + husband_portfolio.cash_post
        + wife_portfolio.cash_pre
        + wife_portfolio.cash_post
    )

    np.testing.assert_allclose(core["cash"][0, 0], expected_cash, rtol=0.0, atol=1e-8)