import numpy as np

from src.warpsimlab.sim.simulation import run_pipeline


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


def test_core_yearly_series_have_expected_shapes(make_case):
    core, cfg = run_case(make_case, years_to_simulate=6)

    expected_shape = (1, cfg.years_to_simulate + 1)

    assert core["year"].shape == expected_shape
    assert core["total_assets"].shape == expected_shape
    assert core["pre_tax_assets"].shape == expected_shape
    assert core["post_tax_assets"].shape == expected_shape
    assert core["cash"].shape == expected_shape
    assert core["bonds"].shape == expected_shape
    assert core["real_estate"].shape == expected_shape
    assert core["gross_income"].shape == expected_shape
    assert core["net_income"].shape == expected_shape
    assert core["net_profit"].shape == expected_shape
    assert core["taxes"].shape == expected_shape
    assert core["tax_bracket"].shape == expected_shape
    assert core["expense_amt"].shape == expected_shape
    assert core["ira_401k"].shape == expected_shape
    assert core["fund_expenses"].shape == expected_shape
    assert core["net_income_husband"].shape == expected_shape
    assert core["net_income_wife"].shape == expected_shape
    assert core["bond_interest"].shape == expected_shape
    assert core["cash_interest"].shape == expected_shape
    assert core["qualified_dividends"].shape == expected_shape
    assert core["federal_ordinary_tax"].shape == expected_shape
    assert core["federal_qualified_dividend_tax"].shape == expected_shape
    assert core["state_income_tax"].shape == expected_shape
    assert core["emergency_pre_tax_used"].shape == expected_shape
    assert core["final_tax_delta"].shape == expected_shape
    assert core["final_tax_delta_deducted"].shape == expected_shape
    assert core["final_tax_delta_uncovered"].shape == expected_shape

    for key, arr in core["breakdown_by_class"].items():
        assert arr.shape == expected_shape, key


def test_year_series_starts_at_start_year_and_advances_by_one(make_case):
    core, cfg = run_case(make_case, start_year=2032, years_to_simulate=5)

    expected_years = np.arange(cfg.start_year, cfg.start_year + cfg.years_to_simulate + 1)
    np.testing.assert_array_equal(core["year"][0], expected_years)


def test_all_yearly_series_share_same_time_dimension(make_case):
    core, cfg = run_case(make_case, years_to_simulate=7)

    expected_len = cfg.years_to_simulate + 1

    non_yearly_keys = {
        "breakdown_by_class",
        "sequence_risk_active",
        "sequence_risk_start_year",
        "sequence_risk_end_year",
        "historical_window_start_year",
        "historical_window_end_year",
    }

    for key, value in core.items():
        if key in non_yearly_keys:
            continue
        assert value.shape[1] == expected_len, key

    for key, arr in core["breakdown_by_class"].items():
        assert arr.shape[1] == expected_len, key