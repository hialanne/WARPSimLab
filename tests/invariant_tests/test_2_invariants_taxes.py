import numpy as np

from tests.architectural_helpers import run_invariant_case as run_case

EPS = 1e-9


def test_all_tax_outputs_non_negative(make_case):
    core, cfg = run_case(make_case)

    assert np.all(core["taxes"] >= -EPS)
    assert np.all(core["federal_ordinary_tax"] >= -EPS)
    assert np.all(core["federal_qualified_dividend_tax"] >= -EPS)
    assert np.all(core["state_income_tax"] >= -EPS)
    assert np.all(core["final_tax_delta"] >= -EPS)
    assert np.all(core["final_tax_delta_deducted"] >= -EPS)
    assert np.all(core["final_tax_delta_uncovered"] >= -EPS)


def test_tax_outputs_zero_when_taxes_disabled(make_case):
    core, cfg = run_case(make_case, calculate_income_taxes=False, calculate_payroll_taxes=False,)

    assert np.allclose(core["taxes"], 0.0)
    assert np.allclose(core["federal_ordinary_tax"], 0.0)
    assert np.allclose(core["federal_qualified_dividend_tax"], 0.0)
    assert np.allclose(core["state_income_tax"], 0.0)
    assert np.allclose(core["final_tax_delta"], 0.0)
    assert np.allclose(core["final_tax_delta_deducted"], 0.0)
    assert np.allclose(core["final_tax_delta_uncovered"], 0.0)
    assert np.allclose(core["payroll_tax"], 0.0)
    assert np.allclose(core["social_security_payroll_tax"], 0.0)
    assert np.allclose(core["medicare_tax"], 0.0)
    assert np.allclose(core["additional_medicare_tax"], 0.0)


def test_income_plus_taxes_equals_total_income_components(make_case):
    core, cfg = run_case(make_case)

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
        + breakdown["qualified_equity_distributions"]
    )

    np.testing.assert_allclose(
        core["net_income"] + core["taxes"],
        component_sum,
        rtol=0.0,
        atol=1e-8,
    )