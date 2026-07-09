# tests/test_deterministic_mode_validation.py

import numpy as np

from src.warpsimlab.sim import run_sim_core
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios
from src.warpsimlab.sim.engines.monteCarloEngine import generate_market_path
from tests.feature_tests.monteCarlo.helpers_validation import (
    assert_all_paths_identical,
    install_minimal_core_engine_mocks,
    make_dummy_people,
    make_sim_config,
)


def test_generate_market_path_returns_constant_means_when_monte_carlo_is_off():
    sim_config = make_sim_config(
        subplot_mode="summary",   # anything except "monte_carlo"
        sim_type="portfolio_sim",
        years_to_simulate=5,
        eq_mean=0.07,
        bd_mean=0.03,
        cs_mean=0.02,
        re_mean=0.05,
    )

    path = generate_market_path(sim_config, years_to_simulate=5)

    np.testing.assert_allclose(path["eq"][1:], np.full(5, 0.07), atol=0.0, rtol=0.0)
    np.testing.assert_allclose(path["bd"][1:], np.full(5, 0.03), atol=0.0, rtol=0.0)
    np.testing.assert_allclose(path["cs"][1:], np.full(5, 0.02), atol=0.0, rtol=0.0)
    np.testing.assert_allclose(path["re"][1:], np.full(5, 0.05), atol=0.0, rtol=0.0)


def test_simulate_yearly_portfolios_all_paths_identical_when_monte_carlo_is_off(monkeypatch):
    install_minimal_core_engine_mocks(run_sim_core, monkeypatch)

    sim_config = make_sim_config(
        subplot_mode="summary",
        sim_type="portfolio_sim",
        years_to_simulate=6,
        num_sims=5,
        second_person_enabled=False,
        include_realestate=True,
        plot_mode="raw",
        monte_carlo_mode="pathBasedAnnualSampling",
    )

    husband, wife = make_dummy_people()

    results = simulate_yearly_portfolios(
        husband_portfolio=None,
        wife_portfolio=None,
        husband=husband,
        wife=wife,
        expenses=None,
        sim_config=sim_config,
        num_sims=5,
    )

    assert_all_paths_identical(results["total_assets"])
    assert_all_paths_identical(results["pre_tax_assets"])
    assert_all_paths_identical(results["post_tax_assets"])
    assert_all_paths_identical(results["cash"])
    assert_all_paths_identical(results["bonds"])
    assert_all_paths_identical(results["real_estate"])


def test_deterministic_mode_validation_is_strict_about_shape():
    paths = np.array(
        [
            [100.0, 107.0, 114.49],
            [100.0, 107.0, 114.49],
            [100.0, 107.0, 114.49],
        ]
    )

    assert paths.shape == (3, 3)
    assert_all_paths_identical(paths, atol=1e-12)