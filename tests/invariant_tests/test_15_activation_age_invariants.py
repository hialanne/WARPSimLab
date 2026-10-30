import numpy as np

from tests.architectural_helpers import run_invariant_case as run_case


def test_social_security_starts_no_earlier_than_configured_age(make_case):
    core, cfg = run_case(
        make_case,
        husband_age=60,
        husband_ss_age=67,
        husband_ss=24_000.0,
        years_to_simulate=10,
        calculate_income_taxes=False,
        include_rmd=False,
        second_person_enabled=False,
    )

    ss = core["breakdown_by_class"]["ss"][0]

    assert np.allclose(ss[:7], 0.0)
    assert np.all(ss[7:] >= 0.0)
    assert np.any(ss[7:] > 0.0)


def test_pension_starts_no_earlier_than_configured_age(make_case):
    core, cfg = run_case(
        make_case,
        husband_age=60,
        husband_pension_age=65,
        husband_pension=12_000.0,
        years_to_simulate=8,
        calculate_income_taxes=False,
        include_rmd=False,
        second_person_enabled=False,
    )

    pension = core["breakdown_by_class"]["pension"][0]

    assert np.allclose(pension[:5], 0.0)
    assert np.all(pension[5:] >= 0.0)
    assert np.any(pension[5:] > 0.0)


def test_annuity_starts_no_earlier_than_configured_age(make_case):
    core, cfg = run_case(
        make_case,
        husband_age=60,
        husband_annuity_age=66,
        husband_annuity=8_000.0,
        years_to_simulate=8,
        calculate_income_taxes=False,
        include_rmd=False,
        second_person_enabled=False,
    )

    annuity = core["breakdown_by_class"]["annuity"][0]

    assert np.allclose(annuity[:6], 0.0)
    assert np.all(annuity[6:] >= 0.0)
    assert np.any(annuity[6:] > 0.0)