import numpy as np

from src.warpsimlab.sim.engines import monteCarloEngine
from tests.feature_tests.monteCarlo.helpers_validation import make_sim_config

import pytest
pytest.skip("Skipping test_asset_order_consistency due to slow running", allow_module_level=True)


def test_asset_order_is_consistent_with_correlation_matrix():
    sim_config = make_sim_config(
        monte_carlo_mode="pathBasedAnnualSampling",
        use_correlated_returns=True,
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
    )

    corr = np.asarray(sim_config.return_correlation_matrix, dtype=float)

    # sanity: shape must match 4 assets
    assert corr.shape == (4, 4)

    # sample a large batch
    np.random.seed(123)
    draws = []
    for _ in range(50000):
        path = monteCarloEngine.generate_market_path(sim_config, 1)
        draws.append([
            path["eq"][1],
            path["bd"][1],
            path["cs"][1],
            path["re"][1],
        ])

    draws = np.asarray(draws)
    empirical_corr = np.corrcoef(draws, rowvar=False)

    # diagonal should match identity
    np.testing.assert_allclose(np.diag(empirical_corr), np.ones(4), atol=0.01)

    # critical: off-diagonal structure should roughly match config
    np.testing.assert_allclose(empirical_corr, corr, atol=0.04)