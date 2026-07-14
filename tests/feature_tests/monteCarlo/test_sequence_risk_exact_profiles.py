from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.sim.engines import monteCarloEngine


def _sequence_config(
    *,
    timing="Early downturn",
    enabled=True,
    offset=0,
    length="Medium",
    depth="Moderate",
):
    return SimpleNamespace(
        sequence_risk_enabled=enabled,
        sequence_risk_timing=timing,
        sequence_risk_start_year_offset=offset,
        sequence_risk_length=length,
        sequence_risk_depth=depth,
    )


def _market_path(years):
    return {
        "eq": np.linspace(0.10, 0.10 + 0.01 * years, years + 1),
        "bd": np.linspace(0.04, 0.04 + 0.01 * years, years + 1),
        "cs": np.linspace(0.01, 0.01 + 0.001 * years, years + 1),
        "re": np.linspace(0.06, 0.06 + 0.01 * years, years + 1),
    }


def test_early_sequence_risk_starts_at_first_withdrawal_year():
    config = _sequence_config(timing="Early downturn")

    start_year = monteCarloEngine._resolve_sequence_risk_start_year(
        sim_config=config,
        years_to_simulate=12,
        withdrawal_start_year=4,
    )

    assert start_year == 4


def test_mid_sequence_risk_uses_remaining_withdrawal_horizon():
    config = _sequence_config(timing="Mid-retirement downturn")

    start_year = monteCarloEngine._resolve_sequence_risk_start_year(
        sim_config=config,
        years_to_simulate=12,
        withdrawal_start_year=4,
    )

    assert start_year == 8


def test_late_sequence_risk_uses_three_quarter_withdrawal_horizon():
    config = _sequence_config(timing="Late downturn")

    start_year = monteCarloEngine._resolve_sequence_risk_start_year(
        sim_config=config,
        years_to_simulate=12,
        withdrawal_start_year=4,
    )

    assert start_year == 10


def test_custom_sequence_risk_offset_is_clamped_to_simulation_bounds():
    config = _sequence_config(timing="Custom", offset=-99)

    lower_start = monteCarloEngine._resolve_sequence_risk_start_year(
        sim_config=config,
        years_to_simulate=12,
        withdrawal_start_year=4,
    )
    config.sequence_risk_start_year_offset = 99
    upper_start = monteCarloEngine._resolve_sequence_risk_start_year(
        sim_config=config,
        years_to_simulate=12,
        withdrawal_start_year=4,
    )

    assert lower_start == 1
    assert upper_start == 12


def test_severe_medium_overlay_replaces_expected_assets_and_preserves_cash():
    market_path = _market_path(years=5)
    original_cash = market_path["cs"].copy()
    config = _sequence_config(length="Medium", depth="Severe")

    adjusted, metadata = monteCarloEngine.apply_sequence_risk_overlay(
        market_path,
        config,
        years_to_simulate=5,
        withdrawal_start_year=2,
    )

    assert adjusted["eq"][2:5] == pytest.approx([-0.35, -0.21, -0.07])
    assert adjusted["bd"][2:5] == pytest.approx([-0.10, -0.06, -0.02])
    assert adjusted["re"][2:5] == pytest.approx([-0.20, -0.12, -0.04])
    assert adjusted["cs"] == pytest.approx(original_cash)
    assert adjusted["eq"][[0, 1, 5]] == pytest.approx(
        market_path["eq"][[0, 1, 5]]
    )
    assert metadata == {
        "enabled": True,
        "applied": True,
        "start_year": 2,
        "end_year": 4,
        "length_years": 3,
        "timing": "Early downturn",
        "depth": "Severe",
    }


def test_long_overlay_truncates_cleanly_at_end_of_horizon():
    market_path = _market_path(years=5)
    config = _sequence_config(length="Long", depth="Moderate")

    adjusted, metadata = monteCarloEngine.apply_sequence_risk_overlay(
        market_path,
        config,
        years_to_simulate=5,
        withdrawal_start_year=4,
    )

    assert adjusted["eq"][4:6] == pytest.approx([-0.20, -0.14])
    assert adjusted["bd"][4:6] == pytest.approx([-0.05, -0.035])
    assert adjusted["re"][4:6] == pytest.approx([-0.10, -0.07])
    assert metadata["start_year"] == 4
    assert metadata["end_year"] == 5
    assert metadata["length_years"] == 2


def test_disabled_overlay_returns_original_object_and_unapplied_metadata():
    market_path = _market_path(years=5)
    config = _sequence_config(enabled=False, depth="Severe")

    adjusted, metadata = monteCarloEngine.apply_sequence_risk_overlay(
        market_path,
        config,
        years_to_simulate=5,
        withdrawal_start_year=2,
    )

    assert adjusted is market_path
    assert metadata == {
        "enabled": False,
        "applied": False,
        "start_year": None,
        "end_year": None,
        "length_years": 0,
        "timing": "Early downturn",
        "depth": "Severe",
    }


def test_singular_correlated_covariance_factor_reconstructs_covariance():
    standard_deviations = np.array([0.15, 0.0, 0.01, 0.10])
    correlation = np.array(
        [
            [1.0, 0.0, 0.2, 0.4],
            [0.0, 1.0, 0.0, 0.0],
            [0.2, 0.0, 1.0, 0.1],
            [0.4, 0.0, 0.1, 1.0],
        ]
    )
    covariance = monteCarloEngine.build_covariance_matrix(
        standard_deviations,
        correlation,
    )

    factor = monteCarloEngine.build_covariance_factor(covariance)

    assert np.linalg.matrix_rank(covariance) == 3
    assert factor.shape == (4, 4)
    assert factor @ factor.T == pytest.approx(covariance, abs=1e-12)
    assert factor[1] == pytest.approx(np.zeros(4), abs=1e-12)
