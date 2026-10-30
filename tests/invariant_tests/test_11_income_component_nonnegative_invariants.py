import numpy as np

from tests.architectural_helpers import run_invariant_case as run_case


EPS = 1e-9


def test_breakdown_by_class_components_are_never_negative(make_case):
    core, cfg = run_case(make_case, second_person_enabled=True)

    for key, arr in core["breakdown_by_class"].items():
        assert np.all(arr >= -EPS), key


def test_reported_interest_and_dividend_series_are_never_negative(make_case):
    core, cfg = run_case(make_case)

    assert np.all(core["bond_interest"] >= -EPS)
    assert np.all(core["cash_interest"] >= -EPS)
    assert np.all(core["qualified_equity_distributions"] >= -EPS)


def test_net_income_never_exceeds_gross_income(make_case):
    core, cfg = run_case(make_case, second_person_enabled=True)

    assert np.all(core["gross_income"] + EPS >= core["net_income"])