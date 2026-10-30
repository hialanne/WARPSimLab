import numpy as np

from tests.feature_tests.monteCarlo.helpers_validation import make_sim_config, sample_many_return_vectors


def test_asset_order_is_consistent_with_correlation_matrix():
    sim_config = make_sim_config(
        use_correlated_returns=True,
        results_mode="risk_analysis",
        sim_type="portfolio_sim",
    )

    corr = np.asarray(sim_config.return_correlation_matrix, dtype=float)

    # sanity: shape must match 4 assets
    assert corr.shape == (4, 4)

    # sample a large batch
    draws = sample_many_return_vectors(sim_config, sample_size=50_000, seed=123)
    empirical_corr = np.corrcoef(draws, rowvar=False)

    # diagonal should match identity
    np.testing.assert_allclose(np.diag(empirical_corr), np.ones(4), atol=0.01)

    # critical: off-diagonal structure should roughly match config
    np.testing.assert_allclose(empirical_corr, corr, atol=0.04)
