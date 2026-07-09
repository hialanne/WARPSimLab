import numpy as np
import pytest

from src.warpsimlab.sim.engines.monteCarloEngine import validate_correlation_matrix


def test_validate_correlation_matrix_accepts_valid_matrix():
    corr = np.array([
        [1.00, -0.20, 0.00, 0.55],
        [-0.20, 1.00, 0.20, 0.10],
        [0.00, 0.20, 1.00, 0.05],
        [0.55, 0.10, 0.05, 1.00],
    ], dtype=float)

    validate_correlation_matrix(corr)


def test_validate_correlation_matrix_rejects_wrong_shape():
    corr = np.eye(3)
    with pytest.raises(ValueError, match="shape"):
        validate_correlation_matrix(corr)


def test_validate_correlation_matrix_rejects_non_symmetric():
    corr = np.array([
        [1.0, 0.2, 0.0, 0.0],
        [0.1, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])
    with pytest.raises(ValueError, match="symmetric"):
        validate_correlation_matrix(corr)


def test_validate_correlation_matrix_rejects_bad_diagonal():
    corr = np.eye(4)
    corr[2, 2] = 0.9
    with pytest.raises(ValueError, match="diagonal"):
        validate_correlation_matrix(corr)


def test_validate_correlation_matrix_rejects_out_of_range_entries():
    corr = np.eye(4)
    corr[0, 1] = 1.2
    corr[1, 0] = 1.2
    with pytest.raises(ValueError, match="between -1 and 1"):
        validate_correlation_matrix(corr)


def test_validate_correlation_matrix_rejects_non_psd():
    corr = np.array([
        [1.0, 0.9, 0.9, -0.9],
        [0.9, 1.0, -0.9, 0.9],
        [0.9, -0.9, 1.0, 0.9],
        [-0.9, 0.9, 0.9, 1.0],
    ], dtype=float)

    eigvals = np.linalg.eigvalsh(corr)
    assert np.min(eigvals) < 0.0

    with pytest.raises(ValueError, match="positive semidefinite"):
        validate_correlation_matrix(corr)
