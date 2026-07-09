import numpy as np

from src.warpsimlab.sim.simulation import run_pipeline


EPS = 1e-9


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


def test_fund_expenses_are_zero_when_disabled(make_case):
    core, cfg = run_case(
        make_case,
        use_fund_expenses=False,
        fund_expense=0.02,
        years_to_simulate=5,
    )

    assert np.allclose(core["fund_expenses"], 0.0)


def test_fund_expenses_are_non_negative_when_enabled(make_case):
    core, cfg = run_case(
        make_case,
        use_fund_expenses=True,
        fund_expense=0.02,
        years_to_simulate=5,
    )

    assert np.all(core["fund_expenses"] >= -EPS)


def test_total_assets_with_fund_expenses_disabled_are_at_least_as_high(make_case):
    core_on, cfg_on = run_case(
        make_case,
        use_fund_expenses=True,
        fund_expense=0.02,
        years_to_simulate=5,
        eq_mean=0.05,
        bd_mean=0.02,
        cs_mean=0.01,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
    )

    core_off, cfg_off = run_case(
        make_case,
        use_fund_expenses=False,
        fund_expense=0.02,
        years_to_simulate=5,
        eq_mean=0.05,
        bd_mean=0.02,
        cs_mean=0.01,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
    )

    assert np.all(core_off["total_assets"] >= core_on["total_assets"] - EPS)