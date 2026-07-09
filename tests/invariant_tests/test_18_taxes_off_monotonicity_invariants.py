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


def test_taxes_off_has_total_assets_at_least_as_high_as_taxes_on(make_case):
    taxed_core, taxed_cfg = run_case(
        make_case,
        calculate_income_taxes=True,
        years_to_simulate=5,
        second_person_enabled=True,
    )

    untaxed_core, untaxed_cfg = run_case(
        make_case,
        calculate_income_taxes=False,
        years_to_simulate=5,
        second_person_enabled=True,
    )

    assert np.all(untaxed_core["total_assets"] >= taxed_core["total_assets"] - EPS)


def test_taxes_off_has_net_income_at_least_as_high_as_taxes_on(make_case):
    taxed_core, taxed_cfg = run_case(
        make_case,
        calculate_income_taxes=True,
        years_to_simulate=5,
        second_person_enabled=True,
    )

    untaxed_core, untaxed_cfg = run_case(
        make_case,
        calculate_income_taxes=False,
        years_to_simulate=5,
        second_person_enabled=True,
    )

    assert np.all(untaxed_core["net_income"] >= taxed_core["net_income"] - EPS)


def test_taxes_off_has_zero_taxes_and_no_lower_net_profit(make_case):
    taxed_core, taxed_cfg = run_case(
        make_case,
        calculate_income_taxes=True,
        years_to_simulate=5,
    )

    untaxed_core, untaxed_cfg = run_case(
        make_case,
        calculate_income_taxes=False,
        calculate_payroll_taxes=False,
        years_to_simulate=5,
    )

    assert np.allclose(untaxed_core["taxes"], 0.0)
    assert np.all(untaxed_core["net_profit"] >= taxed_core["net_profit"] - EPS)