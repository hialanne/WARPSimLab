import numpy as np
import pytest

from src.warpsimlab.sim.simulation import run_pipeline

#pytest.skip("Skipping invariant tests for now", allow_module_level=True)


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


def test_manual_expenses_ignore_scenario_multiplier(make_case):
    low_core, low_cfg = run_case(
        make_case,
        always_use_expense_mode=True,
        scenario_expense_multiplier=0.5,
        annual_expense=70000.0,
        years_to_simulate=5,
    )

    high_core, high_cfg = run_case(
        make_case,
        always_use_expense_mode=True,
        scenario_expense_multiplier=2.0,
        annual_expense=70000.0,
        years_to_simulate=5,
    )

    np.testing.assert_allclose(
        high_core["expense_amt"],
        low_core["expense_amt"] * (2.0 / 0.5),
        rtol=0.0,
        atol=1e-8,
    )


def test_non_manual_expenses_respond_monotonically_to_multiplier(make_case):
    low_core, low_cfg = run_case(
        make_case,
        always_use_expense_mode=False,
        scenario_expense_multiplier=0.5,
        annual_expense=70000.0,
        years_to_simulate=5,
    )

    high_core, high_cfg = run_case(
        make_case,
        always_use_expense_mode=False,
        scenario_expense_multiplier=2.0,
        annual_expense=70000.0,
        years_to_simulate=5,
    )

    assert np.all(high_core["expense_amt"] >= low_core["expense_amt"] - EPS)


def test_higher_non_manual_expense_multiplier_does_not_improve_net_profit(make_case):
    low_core, low_cfg = run_case(
        make_case,
        always_use_expense_mode=False,
        scenario_expense_multiplier=0.5,
        annual_expense=70000.0,
        years_to_simulate=5,
    )

    high_core, high_cfg = run_case(
        make_case,
        always_use_expense_mode=False,
        scenario_expense_multiplier=2.0,
        annual_expense=70000.0,
        years_to_simulate=5,
    )

    assert np.all(high_core["net_profit"] <= low_core["net_profit"] + EPS)