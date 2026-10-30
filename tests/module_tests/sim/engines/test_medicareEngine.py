"""Boundaries of the simulator's annual Medicare/IRMAA planning model."""

from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.sim.engines import expenseEngine, medicareEngine


def make_config(*, inflation_rate=0.0, start_year=2026):
    config = SimpleNamespace(
        start_year=start_year, years_to_simulate=4,
        inflation_rate=inflation_rate, inflation_delta=0.0,
        results_mode="baseline", sim_type="portfolio_sim",
    )
    expenseEngine.initialize_expense_engine_for_simulation(config)
    medicareEngine.initialize_medicare_engine_for_simulation(config)
    return config


@pytest.mark.parametrize("single,thresholds", [
    (True, (109_000, 137_000, 171_000, 205_000, 500_000)),
    (False, (218_000, 274_000, 342_000, 410_000, 750_000)),
])
@pytest.mark.parametrize("index", range(5))
@pytest.mark.parametrize("offset", [-0.01, 0.0, 0.01])
def test_irmaa_tiers_include_upper_boundary(single, thresholds, index, offset):
    expected_level = index + (offset > 0.0)
    assert medicareEngine.get_irmaa_level(
        thresholds[index] + offset, 0, single, make_config()
    ) == expected_level


@pytest.mark.parametrize("level,monthly_b,monthly_d", [
    (0, 0.0, 0.0), (1, 81.16, 14.50), (2, 202.90, 37.50),
    (3, 324.64, 60.40), (4, 446.38, 83.30), (5, 486.96, 91.00),
])
def test_person_irmaa_is_annual_surcharge_and_starts_at_medicare_age(
    level, monthly_b, monthly_d,
):
    person = SimpleNamespace(medicare_start_age=65)
    config = make_config()
    assert medicareEngine.calculate_person_irmaa(person, 64, level, 0, config) == 0.0
    assert medicareEngine.calculate_person_irmaa(person, 65, level, 0, config) == pytest.approx(
        12 * (monthly_b + monthly_d)
    )


@pytest.mark.parametrize("single,threshold_2027,top", [
    (True, 120_000, 500_000), (False, 240_000, 750_000),
])
def test_inflation_rounds_lower_thresholds_but_freezes_top_through_2027(
    single, threshold_2027, top,
):
    config = make_config(inflation_rate=0.10)
    assert medicareEngine.get_irmaa_level(threshold_2027, 1, single, config) == 0
    assert medicareEngine.get_irmaa_level(threshold_2027 + 0.01, 1, single, config) == 1
    assert medicareEngine.get_irmaa_level(top, 1, single, config) == 4
    assert medicareEngine.get_irmaa_level(top + 0.01, 1, single, config) == 5
    # After the freeze, only one year's growth applies to the top threshold.
    top_2028 = round(top * 1.10)
    assert medicareEngine.get_irmaa_level(top_2028, 2, single, config) == 4
    assert medicareEngine.get_irmaa_level(top_2028 + 0.01, 2, single, config) == 5


@pytest.mark.parametrize("historical,available,expected", [
    (None, False, None), (float("nan"), False, None),
    (-100.0, True, 0.0), (125_000.0, True, 125_000.0),
])
@pytest.mark.parametrize("year,key", [(1, "two_years_prior"), (2, "one_year_prior")])
def test_historical_lookback_distinguishes_missing_from_zero(year, key, historical, available, expected):
    config = SimpleNamespace(historical_magi={key: historical})
    magi, found = medicareEngine.get_irmaa_lookback_magi(year, 0, {}, config)
    assert found is available
    if available:
        assert magi == expected
    else:
        assert np.isnan(magi)


def test_simulated_lookback_uses_same_path_two_years_prior_and_its_filing_status():
    results = {
        "magi": np.array([[0, 110_000, 220_000, 0], [0, 330_000, 440_000, 0]]),
        "filing_status_single": np.array([[False, False, True, True], [True, True, True, True]]),
    }
    config = SimpleNamespace(tax_filing_status="Married filing jointly")
    assert medicareEngine.get_irmaa_lookback_magi(3, 1, results, config) == (330_000, True)
    assert medicareEngine.get_irmaa_lookback_magi(4, 0, results, config) == (220_000, True)
    assert not medicareEngine.get_irmaa_lookback_filing_status_single(3, 0, results, config)
    assert medicareEngine.get_irmaa_lookback_filing_status_single(4, 0, results, config)


def test_magi_includes_taxable_flows_once_and_adds_exempt_interest_without_deduction():
    income = {
        "by_class": dict(work=10_000, pension=2_000, annuity=3_000, ss=4_000,
                         rmd=5_000, bond_interest=600, cash_interest=700,
                         qualified_equity_distributions=800, special_income=99_000,
                         roth_conversion=9_000),
        "taxable_special_income": 1_000, "non_taxable_special_income": 98_000,
        "tax_exempt_interest": 400,
    }
    # Special income and conversions have separate taxable inputs: do not count
    # their reporting-class entries again, or include non-taxable special income.
    assert medicareEngine.calculate_modeled_agi(income, 6_000, 7_000, 9_000) == 49_100
    assert medicareEngine.calculate_irmaa_magi(income, 6_000, 7_000, 9_000) == 49_500


def test_later_simulation_start_anchors_surcharges_to_2026_constants():
    person = SimpleNamespace(medicare_start_age=65)
    config = make_config(start_year=2028, inflation_rate=0.10)
    assert medicareEngine.calculate_person_irmaa(person, 65, 1, 1, config) == pytest.approx(
        1_147.92 * 1.10 ** 3
    )
    # Top threshold grows from the end of its 2027 freeze, not from 2026.
    assert medicareEngine.get_irmaa_level(605_000, 1, True, config) == 4
    assert medicareEngine.get_irmaa_level(605_000.01, 1, True, config) == 5
