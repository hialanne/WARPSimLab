import numpy as np
import pytest

from src.warpsimlab.sim.engines import monteCarloEngine
from tests.feature_tests.monteCarlo.helpers_validation import make_sim_config


def test_path_based_generate_market_path_returns_expected_shapes():
    sim_config = make_sim_config(
        monte_carlo_mode="pathBasedAnnualSampling",
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
    )

    monteCarloEngine.prepare_market_path_sampling(sim_config)
    path = monteCarloEngine.generate_market_path(sim_config, years_to_simulate=12)

    for key in ("eq", "bd", "cs", "re"):
        assert path[key].shape == (13,)
        assert path[key][0] == 0.0
        assert np.all(np.isfinite(path[key][1:]))


def test_independent_mode_generate_market_path_returns_finite_values():
    sim_config = make_sim_config(
        monte_carlo_mode="pathBasedAnnualSampling",
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
        use_correlated_returns=False,
    )

    monteCarloEngine.prepare_market_path_sampling(sim_config)
    path = monteCarloEngine.generate_market_path(sim_config, years_to_simulate=12)

    for key in ("eq", "bd", "cs", "re"):
        assert path[key].shape == (13,)
        assert path[key][0] == 0.0
        assert np.all(np.isfinite(path[key][1:]))


def test_independent_mode_one_year_returns_are_numeric():
    sim_config = make_sim_config(
        monte_carlo_mode="pathBasedAnnualSampling",
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
        use_correlated_returns=False,
    )

    monteCarloEngine.prepare_market_path_sampling(sim_config)
    path = monteCarloEngine.generate_market_path(sim_config, years_to_simulate=1)

    year_returns = {
        "eq": path["eq"][1],
        "bd": path["bd"][1],
        "cs": path["cs"][1],
        "re": path["re"][1],
    }

    assert set(year_returns.keys()) == {"eq", "bd", "cs", "re"}
    for value in year_returns.values():
        assert np.isscalar(value)
        assert np.isfinite(value)


def test_generate_market_path_requires_prepared_sampling_data():
    sim_config = make_sim_config(
        monte_carlo_mode="pathBasedAnnualSampling",
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
    )

    sim_config._mc_means = None
    sim_config._mc_std_devs = None

    with pytest.raises(RuntimeError, match="Monte Carlo sampling data not prepared"):
        monteCarloEngine.generate_market_path(sim_config, years_to_simulate=5)