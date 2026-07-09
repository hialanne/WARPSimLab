# tests/test_market_return_sampler_validation.py

import numpy as np

import pytest
pytest.skip("Skipping test_market_return_sampler_validation due to slow running", allow_module_level=True)



from tests.feature_tests.monteCarlo.helpers_validation import (
    assert_sampler_matches_targets,
    make_sim_config,
    sample_many_return_vectors,
)


def test_path_based_correlated_sampler_matches_targets():
    sim_config = make_sim_config(
        monte_carlo_mode="pathBasedAnnualSampling",
        use_correlated_returns=True,
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
    )

    draws = sample_many_return_vectors(sim_config, sample_size=100_000, seed=123)
    assert draws.shape == (100_000, 4)

    assert_sampler_matches_targets(
        sim_config,
        draws,
        mean_atol=0.003,
        std_atol=0.003,
        corr_atol=0.03,
    )


def test_path_based_uncorrelated_sampler_matches_identity_corr():
    sim_config = make_sim_config(
        monte_carlo_mode="pathBasedAnnualSampling",
        use_correlated_returns=False,
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
    )

    draws = sample_many_return_vectors(sim_config, sample_size=100_000, seed=456)
    assert draws.shape == (100_000, 4)

    assert_sampler_matches_targets(
        sim_config,
        draws,
        mean_atol=0.003,
        std_atol=0.003,
        corr_atol=0.02,
    )


def test_independent_annual_sampler_matches_identity_corr():
    sim_config = make_sim_config(
        monte_carlo_mode="independentAnnualSampling",
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
    )

    draws = sample_many_return_vectors(sim_config, sample_size=100_000, seed=789)
    assert draws.shape == (100_000, 4)

    assert_sampler_matches_targets(
        sim_config,
        draws,
        mean_atol=0.003,
        std_atol=0.003,
        corr_atol=0.02,
    )


def test_return_sampler_outputs_decimal_scale_not_percentage_scale():
    sim_config = make_sim_config(
        eq_mean=0.07,
        bd_mean=0.03,
        cs_mean=0.02,
        re_mean=0.05,
        monte_carlo_mode="independentAnnualSampling",
    )

    draws = sample_many_return_vectors(sim_config, sample_size=20_000, seed=999)
    empirical_mean = np.mean(draws, axis=0)

    assert np.all(empirical_mean < 1.0), empirical_mean
    assert np.all(empirical_mean > -1.0), empirical_mean