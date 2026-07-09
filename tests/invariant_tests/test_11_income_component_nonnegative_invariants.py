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


def test_breakdown_by_class_components_are_never_negative(make_case):
    core, cfg = run_case(make_case, second_person_enabled=True)

    for key, arr in core["breakdown_by_class"].items():
        assert np.all(arr >= -EPS), key


def test_reported_interest_and_dividend_series_are_never_negative(make_case):
    core, cfg = run_case(make_case)

    assert np.all(core["bond_interest"] >= -EPS)
    assert np.all(core["cash_interest"] >= -EPS)
    assert np.all(core["qualified_dividends"] >= -EPS)


def test_net_income_never_exceeds_gross_income(make_case):
    core, cfg = run_case(make_case, second_person_enabled=True)

    assert np.all(core["gross_income"] + EPS >= core["net_income"])