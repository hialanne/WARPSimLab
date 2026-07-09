from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.sim.engines import monteCarloEngine


@dataclass
class SimConfigFactory:
    subplot_mode: str = "monte_carlo"
    sim_type: str = "portfolio_sim"
    monte_carlo_mode: str = "pathBasedAnnualSampling"
    use_correlated_returns: bool = True

    eq_mean: float = 0.10
    bd_mean: float = 0.04
    cs_mean: float = 0.02
    re_mean: float = 0.03

    eq_std: float = 0.15
    bd_std: float = 0.07
    cs_std: float = 0.01
    re_std: float = 0.10

    return_correlation_matrix: np.ndarray | None = None

    def build(self, **overrides) -> SimpleNamespace:
        data = {
            "subplot_mode": self.subplot_mode,
            "sim_type": self.sim_type,
            "monte_carlo_mode": self.monte_carlo_mode,
            "use_correlated_returns": self.use_correlated_returns,
            "eq_mean": self.eq_mean,
            "bd_mean": self.bd_mean,
            "cs_mean": self.cs_mean,
            "re_mean": self.re_mean,
            "eq_std": self.eq_std,
            "bd_std": self.bd_std,
            "cs_std": self.cs_std,
            "re_std": self.re_std,
            "return_correlation_matrix": (
                self.return_correlation_matrix
                if self.return_correlation_matrix is not None
                else np.array(
                    [
                        [1.00, -0.20, 0.00, 0.55],
                        [-0.20, 1.00, 0.20, 0.10],
                        [0.00, 0.20, 1.00, 0.05],
                        [0.55, 0.10, 0.05, 1.00],
                    ],
                    dtype=float,
                )
            ),
        }
        data.update(overrides)
        return SimpleNamespace(**data)


@pytest.fixture
def sim_factory() -> SimConfigFactory:
    return SimConfigFactory()


def test_prepare_market_path_sampling_sets_expected_arrays_for_correlated_mode(sim_factory):
    sim_config = sim_factory.build(
        subplot_mode="monte_carlo",
        use_correlated_returns=True,
    )

    monteCarloEngine.prepare_market_path_sampling(sim_config)

    assert np.allclose(
        sim_config._mc_means,
        np.array([sim_config.eq_mean, sim_config.bd_mean, sim_config.cs_mean, sim_config.re_mean]),
    )
    assert np.allclose(
        sim_config._mc_std_devs,
        np.array([sim_config.eq_std, sim_config.bd_std, sim_config.cs_std, sim_config.re_std]),
    )

    expected_cov = monteCarloEngine.build_covariance_matrix(
        sim_config._mc_std_devs,
        sim_config.return_correlation_matrix,
    )

    assert sim_config._mc_cov_matrix.shape == (4, 4)
    assert np.allclose(sim_config._mc_cov_matrix, expected_cov)
    assert sim_config._mc_cholesky.shape == (4, 4)
    assert np.allclose(
        sim_config._mc_cholesky @ sim_config._mc_cholesky.T,
        expected_cov,
    )


def test_prepare_market_path_sampling_non_monte_carlo_leaves_covariance_unset(sim_factory):
    sim_config = sim_factory.build(
        subplot_mode="summary",
        use_correlated_returns=True,
    )

    monteCarloEngine.prepare_market_path_sampling(sim_config)

    assert np.allclose(
        sim_config._mc_means,
        np.array([sim_config.eq_mean, sim_config.bd_mean, sim_config.cs_mean, sim_config.re_mean]),
    )
    assert np.allclose(
        sim_config._mc_std_devs,
        np.array([sim_config.eq_std, sim_config.bd_std, sim_config.cs_std, sim_config.re_std]),
    )
    assert sim_config._mc_cov_matrix is None
    assert sim_config._mc_cholesky is None


def test_prepare_market_path_sampling_uncorrelated_leaves_covariance_unset(sim_factory):
    sim_config = sim_factory.build(
        subplot_mode="monte_carlo",
        use_correlated_returns=False,
    )

    monteCarloEngine.prepare_market_path_sampling(sim_config)

    assert np.allclose(
        sim_config._mc_means,
        np.array([sim_config.eq_mean, sim_config.bd_mean, sim_config.cs_mean, sim_config.re_mean]),
    )
    assert np.allclose(
        sim_config._mc_std_devs,
        np.array([sim_config.eq_std, sim_config.bd_std, sim_config.cs_std, sim_config.re_std]),
    )
    assert sim_config._mc_cov_matrix is None
    assert sim_config._mc_cholesky is None


def test_generate_market_path_non_monte_carlo_returns_constant_means(sim_factory):
    sim_config = sim_factory.build(
        subplot_mode="summary",
        sim_type="portfolio_sim",
    )

    years_to_simulate = 5
    path = monteCarloEngine.generate_market_path(sim_config, years_to_simulate)

    assert set(path.keys()) == {"eq", "bd", "cs", "re"}

    expected_by_key = {
        "eq": sim_config.eq_mean,
        "bd": sim_config.bd_mean,
        "cs": sim_config.cs_mean,
        "re": sim_config.re_mean,
    }

    for key, expected in expected_by_key.items():
        assert path[key].shape == (years_to_simulate + 1,)
        assert path[key][0] == 0.0
        assert np.allclose(path[key][1:], expected)


def test_generate_market_path_path_based_correlated_has_expected_shapes(sim_factory):
    np.random.seed(12345)

    sim_config = sim_factory.build(
        monte_carlo_mode="pathBasedAnnualSampling",
        use_correlated_returns=True,
    )
    monteCarloEngine.prepare_market_path_sampling(sim_config)

    years_to_simulate = 7
    path = monteCarloEngine.generate_market_path(sim_config, years_to_simulate)

    for key in ("eq", "bd", "cs", "re"):
        assert path[key].shape == (years_to_simulate + 1,)
        assert path[key][0] == 0.0
        assert np.all(np.isfinite(path[key][1:]))


def test_generate_market_path_path_based_uncorrelated_has_expected_shapes(sim_factory):
    np.random.seed(54321)

    sim_config = sim_factory.build(
        monte_carlo_mode="pathBasedAnnualSampling",
        use_correlated_returns=False,
    )
    monteCarloEngine.prepare_market_path_sampling(sim_config)

    years_to_simulate = 6
    path = monteCarloEngine.generate_market_path(sim_config, years_to_simulate)

    for key in ("eq", "bd", "cs", "re"):
        assert path[key].shape == (years_to_simulate + 1,)
        assert path[key][0] == 0.0
        assert np.all(np.isfinite(path[key][1:]))


def test_prepare_market_path_sampling_rejects_independent_annual_sampling(sim_factory):
    sim_config = sim_factory.build(
        monte_carlo_mode="independentAnnualSampling",
        use_correlated_returns=False,
    )

    with pytest.raises(ValueError, match="Unsupported monte_carlo_mode: independentAnnualSampling"):
        monteCarloEngine.prepare_market_path_sampling(sim_config)


def test_generate_market_path_independent_mode_returns_nan_placeholders(sim_factory):
    sim_config = sim_factory.build(
        monte_carlo_mode="independentAnnualSampling",
        use_correlated_returns=False,
    )

    years_to_simulate = 4
    path = monteCarloEngine.generate_market_path(sim_config, years_to_simulate)

    for key in ("eq", "bd", "cs", "re"):
        assert path[key].shape == (years_to_simulate + 1,)
        assert path[key][0] == 0.0
        assert np.all(np.isnan(path[key][1:]))


def test_generate_market_path_requires_prepared_sampling_data(sim_factory):
    sim_config = sim_factory.build(
        subplot_mode="monte_carlo",
        use_correlated_returns=False,
    )
    sim_config._mc_means = None
    sim_config._mc_std_devs = None

    with pytest.raises(RuntimeError, match="Monte Carlo sampling data not prepared"):
        monteCarloEngine.generate_market_path(sim_config, years_to_simulate=3)


def test_generate_market_path_correlated_requires_prepared_cholesky(sim_factory):
    sim_config = sim_factory.build(
        subplot_mode="monte_carlo",
        use_correlated_returns=True,
    )
    sim_config._mc_means = np.array(
        [sim_config.eq_mean, sim_config.bd_mean, sim_config.cs_mean, sim_config.re_mean],
        dtype=float,
    )
    sim_config._mc_std_devs = np.array(
        [sim_config.eq_std, sim_config.bd_std, sim_config.cs_std, sim_config.re_std],
        dtype=float,
    )
    sim_config._mc_cholesky = None

    with pytest.raises(RuntimeError, match="Cholesky factor not prepared"):
        monteCarloEngine.generate_market_path(sim_config, years_to_simulate=3)


def test_validate_correlation_matrix_accepts_valid_matrix():
    corr = np.array(
        [
            [1.0, 0.2, 0.0, 0.1],
            [0.2, 1.0, -0.1, 0.0],
            [0.0, -0.1, 1.0, 0.3],
            [0.1, 0.0, 0.3, 1.0],
        ],
        dtype=float,
    )

    monteCarloEngine.validate_correlation_matrix(corr)


def test_validate_correlation_matrix_rejects_bad_shape():
    corr = np.eye(3)

    with pytest.raises(ValueError, match=r"shape \(4, 4\)"):
        monteCarloEngine.validate_correlation_matrix(corr)


def test_validate_correlation_matrix_rejects_non_symmetric_matrix():
    corr = np.array(
        [
            [1.0, 0.1, 0.0, 0.0],
            [0.2, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )

    with pytest.raises(ValueError, match="symmetric"):
        monteCarloEngine.validate_correlation_matrix(corr)


def test_validate_correlation_matrix_rejects_bad_diagonal():
    corr = np.array(
        [
            [0.9, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )

    with pytest.raises(ValueError, match="diagonal"):
        monteCarloEngine.validate_correlation_matrix(corr)


def test_validate_correlation_matrix_rejects_out_of_range_values():
    corr = np.array(
        [
            [1.0, 1.2, 0.0, 0.0],
            [1.2, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )

    with pytest.raises(ValueError, match="between -1 and 1"):
        monteCarloEngine.validate_correlation_matrix(corr)


def test_validate_correlation_matrix_rejects_not_positive_semidefinite():
    corr = np.array(
        [
            [1.0, -0.9, -0.9, -0.9],
            [-0.9, 1.0, -0.9, -0.9],
            [-0.9, -0.9, 1.0, -0.9],
            [-0.9, -0.9, -0.9, 1.0],
        ],
        dtype=float,
    )

    with pytest.raises(ValueError, match="positive semidefinite"):
        monteCarloEngine.validate_correlation_matrix(corr)


def test_build_covariance_matrix_returns_expected_matrix():
    std_devs = np.array([0.15, 0.07, 0.01, 0.10], dtype=float)
    corr = np.array(
        [
            [1.0, 0.2, 0.0, 0.1],
            [0.2, 1.0, 0.3, 0.0],
            [0.0, 0.3, 1.0, 0.4],
            [0.1, 0.0, 0.4, 1.0],
        ],
        dtype=float,
    )

    cov = monteCarloEngine.build_covariance_matrix(std_devs, corr)
    expected = np.diag(std_devs) @ corr @ np.diag(std_devs)

    assert cov.shape == (4, 4)
    assert np.allclose(cov, expected)
    assert np.allclose(cov, cov.T)


def test_build_covariance_matrix_rejects_bad_std_dev_shape():
    std_devs = np.array([0.15, 0.07, 0.01], dtype=float)
    corr = np.eye(4)

    with pytest.raises(ValueError, match=r"shape \(4,\)"):
        monteCarloEngine.build_covariance_matrix(std_devs, corr)


def test_build_covariance_matrix_rejects_invalid_correlation_matrix():
    std_devs = np.array([0.15, 0.07, 0.01, 0.10], dtype=float)
    corr = np.array(
        [
            [1.0, 2.0, 0.0, 0.0],
            [2.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )

    with pytest.raises(ValueError):
        monteCarloEngine.build_covariance_matrix(std_devs, corr)


def test_debug_validate_correlated_sampling_runs_for_valid_inputs(sim_factory, capsys):
    np.random.seed(321)

    sim_config = sim_factory.build(
        use_correlated_returns=True,
    )

    monteCarloEngine.debug_validate_correlated_sampling(sim_config, sample_size=200)

    captured = capsys.readouterr()
    assert "Target correlation matrix:" in captured.out
    assert "Empirical correlation matrix:" in captured.out