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


def test_work_income_stops_at_retirement_boundary_for_husband(make_case):
    core, cfg = run_case(
        make_case,
        second_person_enabled=False,
        husband_age=60,
        husband_retire_age=63,
        husband_income=100_000.0,
        husband_annual_401k_contribution=10_000.0,
        husband_annual_employer_match=5_000.0,
        years_to_simulate=5,
        calculate_income_taxes=False,
        include_rmd=False,
    )

    work = core["breakdown_by_class"]["work"][0]

    assert work[1] > 0.0
    assert work[2] > 0.0
    assert np.allclose(work[3:], 0.0)


def test_ira_401k_contributions_stop_at_retirement_boundary_for_husband(make_case):
    core, cfg = run_case(
        make_case,
        second_person_enabled=False,
        husband_age=60,
        husband_retire_age=63,
        husband_income=100_000.0,
        husband_annual_401k_contribution=10_000.0,
        husband_annual_employer_match=5_000.0,
        years_to_simulate=5,
        calculate_income_taxes=False,
        include_rmd=False,
    )

    ira_401k = core["ira_401k"][0]

    assert ira_401k[1] > 0.0
    assert ira_401k[2] > 0.0
    assert np.allclose(ira_401k[3:], 0.0)


def test_work_income_and_ira_401k_stop_at_retirement_boundary_for_wife(make_case):
    core, cfg = run_case(
        make_case,
        second_person_enabled=True,
        husband_income=0.0,
        husband_ss=0.0,
        husband_pension=0.0,
        husband_annuity=0.0,
        husband_annual_401k_contribution=0.0,
        husband_annual_employer_match=0.0,
        wife_age=60,
        wife_retire_age=62,
        wife_income=80_000.0,
        wife_ss=0.0,
        wife_pension=0.0,
        wife_annuity=0.0,
        wife_annual_401k_contribution=8_000.0,
        wife_annual_employer_match=4_000.0,
        years_to_simulate=5,
        calculate_income_taxes=False,
        include_rmd=False,
    )

    work = core["breakdown_by_class"]["work"][0]
    ira_401k = core["ira_401k"][0]

    assert work[1] > 0.0
    assert np.allclose(work[2:], 0.0)

    assert ira_401k[1] > 0.0
    assert np.allclose(ira_401k[2:], 0.0)