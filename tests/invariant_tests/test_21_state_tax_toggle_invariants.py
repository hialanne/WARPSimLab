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


def test_state_income_tax_is_zero_when_state_taxes_disabled(make_case):
    core, cfg = run_case(
        make_case,
        calculate_income_taxes=True,
        calculate_state_taxes=False,
        state_of_residence="CA",
        second_person_enabled=True,
        years_to_simulate=5,
    )

    assert np.allclose(core["state_income_tax"], 0.0)


def test_total_taxes_with_state_taxes_disabled_are_no_higher(make_case):
    state_on_core, state_on_cfg = run_case(
        make_case,
        calculate_income_taxes=True,
        calculate_state_taxes=True,
        state_of_residence="CA",
        second_person_enabled=True,
        years_to_simulate=5,
    )

    state_off_core, state_off_cfg = run_case(
        make_case,
        calculate_income_taxes=True,
        calculate_state_taxes=False,
        state_of_residence="CA",
        second_person_enabled=True,
        years_to_simulate=5,
    )

    assert np.all(state_off_core["taxes"] <= state_on_core["taxes"] + EPS)
    assert np.all(state_on_core["state_income_tax"] >= -EPS)


def test_net_income_with_state_taxes_disabled_is_no_lower(make_case):
    state_on_core, state_on_cfg = run_case(
        make_case,
        calculate_income_taxes=True,
        calculate_state_taxes=True,
        state_of_residence="CA",
        second_person_enabled=True,
        years_to_simulate=5,
    )

    state_off_core, state_off_cfg = run_case(
        make_case,
        calculate_income_taxes=True,
        calculate_state_taxes=False,
        state_of_residence="CA",
        second_person_enabled=True,
        years_to_simulate=5,
    )

    assert np.all(state_off_core["net_income"] >= state_on_core["net_income"] - EPS)