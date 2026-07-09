import numpy as np
import pytest

from src.warpsimlab.sim.engines.monteCarloEngine import build_covariance_matrix


def test_build_covariance_matrix_matches_expected_formula():
    std_devs = np.array([0.15, 0.06, 0.01, 0.12], dtype=float)
    corr = np.array([
        [1.00, -0.20, 0.00, 0.55],
        [-0.20, 1.00, 0.20, 0.10],
        [0.00, 0.20, 1.00, 0.05],
        [0.55, 0.10, 0.05, 1.00],
    ], dtype=float)

    cov = build_covariance_matrix(std_devs, corr)

    expected = np.diag(std_devs) @ corr @ np.diag(std_devs)

    np.testing.assert_allclose(cov, expected, atol=1e-12, rtol=0.0)


def test_build_covariance_matrix_is_symmetric():
    std_devs = np.array([0.15, 0.06, 0.01, 0.12], dtype=float)
    corr = np.array([
        [1.00, -0.20, 0.00, 0.55],
        [-0.20, 1.00, 0.20, 0.10],
        [0.00, 0.20, 1.00, 0.05],
        [0.55, 0.10, 0.05, 1.00],
    ], dtype=float)

    cov = build_covariance_matrix(std_devs, corr)

    np.testing.assert_allclose(cov, cov.T, atol=1e-12, rtol=0.0)
    np.testing.assert_allclose(np.diag(cov), std_devs ** 2, atol=1e-12, rtol=0.0)


def test_build_covariance_matrix_rejects_bad_std_shape():
    corr = np.eye(4)
    bad_std = np.array([0.15, 0.06, 0.01], dtype=float)

    with pytest.raises(ValueError, match="shape"):
        build_covariance_matrix(bad_std, corr)