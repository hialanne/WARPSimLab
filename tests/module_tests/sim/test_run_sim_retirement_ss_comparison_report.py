from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.sim import run_sim_retirement_ss_comparison_report as mod


def test_clamp_social_security_age_limits_range():
    assert mod._clamp_social_security_age(50) == 62
    assert mod._clamp_social_security_age(62) == 62
    assert mod._clamp_social_security_age(67) == 67
    assert mod._clamp_social_security_age(70) == 70
    assert mod._clamp_social_security_age(80) == 70


def test_years_until_event_uses_current_age():
    person = SimpleNamespace(
        age=60,
        retire_age=67,
    )

    assert mod._years_until_event(
        person,
        "retire_age",
    ) == 7


def test_household_event_age_single_person_returns_husband_age():
    husband = SimpleNamespace(
        age=60,
        retire_age=67,
    )

    wife = SimpleNamespace(
        age=50,
        retire_age=70,
    )

    result = mod._household_event_age(
        husband,
        wife,
        False,
        "retire_age",
    )

    assert result == 67


def test_household_event_age_uses_person_whose_event_occurs_last():
    husband = SimpleNamespace(
        age=60,
        retire_age=67,
    )

    wife = SimpleNamespace(
        age=50,
        retire_age=60,
    )

    result = mod._household_event_age(
        husband,
        wife,
        True,
        "retire_age",
    )

    # Husband retires in 7 years.
    # Wife retires in 10 years.
    assert result == 60


def test_household_event_age_tie_uses_larger_event_age():
    husband = SimpleNamespace(
        age=60,
        retire_age=67,
    )

    wife = SimpleNamespace(
        age=55,
        retire_age=62,
    )

    result = mod._household_event_age(
        husband,
        wife,
        True,
        "retire_age",
    )

    assert result == 67


def test_adjust_social_security_from_full_retirement_age_to_age_70():
    baseline = SimpleNamespace(
        ss_age=67,
        ss=12000.0,
    )

    person = SimpleNamespace(
        ss_age=67,
        ss=12000.0,
    )

    mod._adjust_social_security(
        person,
        baseline,
        year_shift=3,
    )

    assert person.ss_age == 70
    assert person.ss == pytest.approx(14880.0)


def test_adjust_social_security_clamps_to_age_62():
    baseline = SimpleNamespace(
        ss_age=67,
        ss=12000.0,
    )

    person = SimpleNamespace(
        ss_age=67,
        ss=12000.0,
    )

    mod._adjust_social_security(
        person,
        baseline,
        year_shift=-20,
    )

    assert person.ss_age == 62
    assert person.ss == pytest.approx(8400.0)


def test_adjust_social_security_zero_shift_leaves_values_unchanged():
    baseline = SimpleNamespace(
        ss_age=67,
        ss=12000.0,
    )

    person = SimpleNamespace(
        ss_age=67,
        ss=12000.0,
    )

    mod._adjust_social_security(
        person,
        baseline,
        year_shift=0,
    )

    assert person.ss_age == 67
    assert person.ss == pytest.approx(12000.0)


def test_build_case_persons_shifts_couple_without_modifying_originals():
    husband = SimpleNamespace(
        age=60,
        retire_age=67,
        ss_age=67,
        ss=12000.0,
    )

    wife = SimpleNamespace(
        age=58,
        retire_age=65,
        ss_age=65,
        ss=10000.0,
    )

    case_husband, case_wife = mod._build_case_persons(
        husband,
        wife,
        True,
        retirement_shift=2,
        social_security_shift=1,
    )

    assert case_husband.retire_age == 69
    assert case_husband.ss_age == 68

    assert case_wife.retire_age == 67
    assert case_wife.ss_age == 66

    assert husband.retire_age == 67
    assert husband.ss_age == 67

    assert wife.retire_age == 65
    assert wife.ss_age == 65

    assert case_husband is not husband
    assert case_wife is not wife


def test_build_case_persons_single_person_does_not_create_wife():
    husband = SimpleNamespace(
        age=60,
        retire_age=67,
        ss_age=67,
        ss=12000.0,
    )

    wife = SimpleNamespace(
        age=58,
        retire_age=65,
        ss_age=65,
        ss=10000.0,
    )

    case_husband, case_wife = mod._build_case_persons(
        husband,
        wife,
        False,
        retirement_shift=1,
        social_security_shift=1,
    )

    assert case_husband.retire_age == 68
    assert case_husband.ss_age == 68
    assert case_wife is None


def test_deterministic_portfolio_at_retirement_single_person():
    total_assets = np.array(
        [
            [100.0, 110.0, 120.0, 130.0, 140.0],
        ]
    )

    husband = SimpleNamespace(
        age=60,
        retire_age=63,
    )

    result = mod._deterministic_portfolio_at_retirement(
        total_assets,
        husband,
        None,
        False,
    )

    assert result == pytest.approx(130.0)


def test_deterministic_portfolio_at_retirement_couple_uses_later_retirement():
    total_assets = np.array(
        [
            [100.0, 110.0, 120.0, 130.0, 140.0, 150.0],
        ]
    )

    husband = SimpleNamespace(
        age=60,
        retire_age=63,
    )

    wife = SimpleNamespace(
        age=50,
        retire_age=55,
    )

    result = mod._deterministic_portfolio_at_retirement(
        total_assets,
        husband,
        wife,
        True,
    )

    assert result == pytest.approx(150.0)


def test_deterministic_portfolio_at_retirement_clamps_to_simulation_end():
    total_assets = np.array(
        [
            [100.0, 110.0, 120.0],
        ]
    )

    husband = SimpleNamespace(
        age=60,
        retire_age=80,
    )

    result = mod._deterministic_portfolio_at_retirement(
        total_assets,
        husband,
        None,
        False,
    )

    assert result == pytest.approx(120.0)


def test_deterministic_portfolio_at_retirement_rejects_non_2d_array():
    husband = SimpleNamespace(
        age=60,
        retire_age=65,
    )

    with pytest.raises(
        ValueError,
        match="Expected a 2D deterministic portfolio array",
    ):
        mod._deterministic_portfolio_at_retirement(
            np.array([100.0, 90.0]),
            husband,
            None,
            False,
        )


def test_deterministic_lifetime_total_sums_first_deterministic_path():
    values = np.array(
        [
            [0.0, 100.0, 200.0, 300.0],
        ]
    )

    assert mod._deterministic_lifetime_total(
        values
    ) == pytest.approx(600.0)


def test_deterministic_lifetime_total_rejects_non_2d_array():
    with pytest.raises(
        ValueError,
        match="Expected a 2D deterministic array",
    ):
        mod._deterministic_lifetime_total(
            np.array([1.0, 2.0, 3.0])
        )


def test_build_depletion_statistics_tracks_first_depletion():
    total_assets = np.array(
        [
            [100.0, 80.0, 0.0, 0.0],
            [100.0, 90.0, 70.0, 60.0],
            [100.0, 0.0, 0.0, 0.0],
            [100.0, 110.0, 120.0, 130.0],
        ]
    )

    years = np.array(
        [2026, 2027, 2028, 2029]
    )

    result = mod._build_depletion_statistics(
        total_assets,
        years,
    )

    assert result["historical_window_count"] == 4
    assert result["reaching_zero_count"] == 2
    assert result["reaching_zero_percent"] == pytest.approx(50.0)
    assert result["earliest_reaching_zero_year"] == pytest.approx(2027.0)
    assert result["median_reaching_zero_year"] == pytest.approx(2027.5)
    assert result["latest_reaching_zero_year"] == pytest.approx(2028.0)