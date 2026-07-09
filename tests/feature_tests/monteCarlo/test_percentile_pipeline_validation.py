# tests/test_percentile_pipeline_validation.py

import numpy as np

from src.warpsimlab.sim import simulation as simulation_module
from tests.feature_tests.monteCarlo.helpers_validation import (
    build_synthetic_core,
    extract_median_series,
    make_sim_config,
)


def test_pipeline_median_matches_raw_path_median(monkeypatch):
    sim_config = make_sim_config(
        years_to_simulate=4,
        num_sims=5,
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
        overlay_tax_impacts=False,
        overlay_fund_expense_impacts=False,
    )

    raw_total_assets = np.array(
        [
            [100, 110, 120, 130, 140],
            [100, 108, 116, 124, 132],
            [100, 111, 121, 131, 141],
            [100, 109, 118, 127, 136],
            [100, 112, 124, 136, 148],
        ],
        dtype=float,
    )
    expected_median = np.median(raw_total_assets, axis=0)
    synthetic_core = build_synthetic_core(raw_total_assets)

    monkeypatch.setattr(
        simulation_module,
        "simulate_yearly_portfolios",
        lambda *args, **kwargs: synthetic_core,
    )

    result = simulation_module.run_pipeline(
        husband_portfolio=None,
        wife_portfolio=None,
        husband=None,
        wife=None,
        expenses=None,
        sim_config=sim_config,
    )

    plot_data = result["portfolio_plot_data"]

    np.testing.assert_allclose(plot_data.raw_total_assets, raw_total_assets, atol=0.0, rtol=0.0)

    observed_median = extract_median_series(plot_data.percentiles)
    np.testing.assert_allclose(observed_median, expected_median, atol=1e-12, rtol=0.0)


def test_pipeline_preserves_raw_total_assets_shape(monkeypatch):
    sim_config = make_sim_config(
        years_to_simulate=3,
        num_sims=4,
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
    )

    raw_total_assets = np.array(
        [
            [100, 101, 102, 103],
            [100, 102, 104, 106],
            [100, 103, 106, 109],
            [100, 104, 108, 112],
        ],
        dtype=float,
    )
    synthetic_core = build_synthetic_core(raw_total_assets)

    monkeypatch.setattr(
        simulation_module,
        "simulate_yearly_portfolios",
        lambda *args, **kwargs: synthetic_core,
    )

    result = simulation_module.run_pipeline(
        husband_portfolio=None,
        wife_portfolio=None,
        husband=None,
        wife=None,
        expenses=None,
        sim_config=sim_config,
    )

    plot_data = result["portfolio_plot_data"]

    assert plot_data.raw_total_assets.shape == (sim_config.num_sims, sim_config.years_to_simulate + 1)
    assert len(result["years_list"]) == sim_config.years_to_simulate + 1
    assert plot_data.raw_total_assets.shape[1] == len(result["years_list"])


def test_pipeline_does_not_assert_mean_equals_median(monkeypatch):
    sim_config = make_sim_config(
        years_to_simulate=4,
        num_sims=5,
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
    )

    raw_total_assets = np.array(
        [
            [100,  80,  64,  51.2,  40.96],
            [100, 100, 100, 100.0, 100.00],
            [100, 110, 121, 133.1, 146.41],
            [100, 120, 144, 172.8, 207.36],
            [100, 170, 289, 491.3, 835.21],
        ],
        dtype=float,
    )
    synthetic_core = build_synthetic_core(raw_total_assets)

    monkeypatch.setattr(
        simulation_module,
        "simulate_yearly_portfolios",
        lambda *args, **kwargs: synthetic_core,
    )

    result = simulation_module.run_pipeline(
        husband_portfolio=None,
        wife_portfolio=None,
        husband=None,
        wife=None,
        expenses=None,
        sim_config=sim_config,
    )

    observed_median = extract_median_series(result["portfolio_plot_data"].percentiles)
    expected_median = np.median(raw_total_assets, axis=0)
    mean_path = np.mean(raw_total_assets, axis=0)

    np.testing.assert_allclose(observed_median, expected_median, atol=1e-12, rtol=0.0)
    assert not np.allclose(mean_path, expected_median, atol=1e-12, rtol=0.0)