import numpy as np

from src.warpsimlab.sim.engines import monteCarloEngine
from tests.feature_tests.monteCarlo.helpers_validation import make_sim_config


def test_generate_market_path_is_reproducible_with_fixed_seed():
    sim_config = make_sim_config(
        monte_carlo_mode="pathBasedAnnualSampling",
        use_correlated_returns=True,
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
    )

    monteCarloEngine.prepare_market_path_sampling(sim_config)

    sim_config._mc_rng = np.random.default_rng(123)
    path1 = monteCarloEngine.generate_market_path(
        sim_config,
        years_to_simulate=10,
    )

    sim_config._mc_rng = np.random.default_rng(123)
    path2 = monteCarloEngine.generate_market_path(
        sim_config,
        years_to_simulate=10,
    )

    for key in ("eq", "bd", "cs", "re"):
        np.testing.assert_allclose(path1[key], path2[key], atol=0.0, rtol=0.0)


def test_generate_market_path_changes_with_different_seed():
    sim_config = make_sim_config(
        monte_carlo_mode="pathBasedAnnualSampling",
        use_correlated_returns=True,
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
    )

    monteCarloEngine.prepare_market_path_sampling(sim_config)

    sim_config._mc_rng = np.random.default_rng(123)
    path1 = monteCarloEngine.generate_market_path(
        sim_config,
        years_to_simulate=10,
    )

    sim_config._mc_rng = np.random.default_rng(124)
    path2 = monteCarloEngine.generate_market_path(
        sim_config,
        years_to_simulate=10,
    )

    # Only need to check one series to confirm randomness differs
    assert not np.allclose(path1["eq"], path2["eq"])


def test_path_based_uncorrelated_mode_is_reproducible_with_fixed_seed():
    sim_config = make_sim_config(
        monte_carlo_mode="pathBasedAnnualSampling",
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
        use_correlated_returns=False,
    )

    monteCarloEngine.prepare_market_path_sampling(sim_config)

    sim_config._mc_rng = np.random.default_rng(999)
    seq1 = [
        monteCarloEngine.generate_market_path(
            sim_config,
            years_to_simulate=1,
        )
        for _ in range(5)
    ]

    sim_config._mc_rng = np.random.default_rng(999)
    seq2 = [
        monteCarloEngine.generate_market_path(
            sim_config,
            years_to_simulate=1,
        )
        for _ in range(5)
    ]

    for p1, p2 in zip(seq1, seq2):
        for key in ("eq", "bd", "cs", "re"):
            assert p1[key][1] == p2[key][1]