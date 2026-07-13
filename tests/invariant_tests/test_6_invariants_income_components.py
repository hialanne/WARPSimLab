import numpy as np

from src.warpsimlab.sim.simulation import run_pipeline


def run_case(make_case, **overrides):
    hp, wp, h, w, e, cfg = make_case(**overrides)

    result = run_pipeline(
        hp,
        wp,
        h,
        w,
        e,
        cfg,
    )

    return result["core"], cfg


def test_qualified_dividends_non_negative(make_case):
    core, cfg = run_case(make_case)

    qd = core["breakdown_by_class"]["qualified_dividends"]

    assert np.all(qd >= 0.0)


def test_qualified_dividends_not_exceed_total_income(make_case):
    core, cfg = run_case(make_case)

    breakdown = core["breakdown_by_class"]

    total_income = (
        breakdown["work"]
        + breakdown["pension"]
        + breakdown["annuity"]
        + breakdown["ss"]
        + breakdown["rmd"]
        + breakdown["withdrawal"]
        + breakdown["bond_interest"]
        + breakdown["cash_interest"]
        + breakdown["qualified_dividends"]
    )

    assert np.all(breakdown["qualified_dividends"] <= total_income + 1e-8)


def test_gross_income_identity(make_case):
    core, cfg = run_case(
        make_case,
        husband_annual_employer_match=0.0,
        wife_annual_employer_match=0.0,
    )

    breakdown = core["breakdown_by_class"]

    component_sum = (
        breakdown["work"]
        + breakdown["pension"]
        + breakdown["annuity"]
        + breakdown["ss"]
        + breakdown["rmd"]
        + breakdown["withdrawal"]
        + breakdown["bond_interest"]
        + breakdown["cash_interest"]
        + breakdown["qualified_dividends"]
    )

    np.testing.assert_allclose(
        core["gross_income"],
        component_sum
        + core["ira_401k"]
        + core["emergency_pre_tax_used"],
        rtol=0.0,
        atol=1e-8,
    )