"""Comparator corruption and sensitivity checks, independent of the simulator."""

import copy

import numpy as np
import pytest

from tests.numerical_reference_helpers import (
    ATOL, RTOL, compare_core, describe_tree, load_reference,
)


def compare(actual, expected):
    compare_core(actual, expected, case="sensitivity", start_year=2026,
                 historical_windows=np.array([2000]))


def test_float_bounds_are_strict_and_reference_relative():
    expected = {"assets": np.array([[0., 1_000_000.]])}
    bound = ATOL + RTOL * expected["assets"]
    compare({"assets": expected["assets"] + 0.99 * bound}, expected)
    for index in [0, 1]:
        actual = copy.deepcopy(expected)
        actual["assets"][0, index] += 1.01 * bound[0, index]
        with pytest.raises(AssertionError, match=f"calendar_year={2026 + index}"):
            compare(actual, expected)


@pytest.mark.parametrize("field", ["year", "tax_bracket", "survivor_expense_factor",
                                   "federal_bracket_lower_threshold",
                                   "federal_bracket_upper_threshold"])
def test_discrete_floats_and_negative_sentinels_are_exact(field):
    value = -1. if "threshold" in field else 1.
    with pytest.raises(AssertionError):
        compare({field: np.array([[value + 1e-12]])}, {field: np.array([[value]])})


@pytest.mark.parametrize("dtype", [bool, np.int64])
def test_integer_and_boolean_values_are_exact(dtype):
    with pytest.raises(AssertionError):
        compare({"mask": np.array([[1]], dtype=dtype)}, {"mask": np.array([[0]], dtype=dtype)})


def test_nan_and_infinity_positions_and_signs():
    expected = {"health": np.array([[np.nan, np.inf, -np.inf, 0.]])}
    compare(copy.deepcopy(expected), expected)
    for index, replacement in [(0, 0.), (1, -np.inf), (2, np.nan), (3, np.nan)]:
        actual = copy.deepcopy(expected)
        actual["health"][0, index] = replacement
        with pytest.raises(AssertionError):
            compare(actual, expected)


@pytest.mark.parametrize("mutation", ["added", "missing", "shape", "dtype", "scalar_type"])
def test_structure_changes_fail(mutation):
    expected = {"breakdown_by_class": {"work": np.zeros((1, 3))}, "effective_years": 2}
    actual = copy.deepcopy(expected)
    nested = actual["breakdown_by_class"]
    if mutation == "added":
        nested["new"] = np.zeros((1, 3))
    elif mutation == "missing":
        del nested["work"]
    elif mutation == "shape":
        nested["work"] = np.zeros((3,))
    elif mutation == "dtype":
        nested["work"] = nested["work"].astype(np.float32)
    else:
        actual["effective_years"] = 2.
    with pytest.raises(AssertionError):
        compare(actual, expected)


@pytest.mark.parametrize("year_index", [0, 2])
def test_nested_diagnostics_identify_year_zero_and_terminal_year(year_index):
    expected = {"breakdown_by_class": {"work": np.zeros((1, 3))}}
    actual = copy.deepcopy(expected)
    actual["breakdown_by_class"]["work"][0, year_index] = .01
    with pytest.raises(AssertionError) as failure:
        compare(actual, expected)
    message = str(failure.value)
    for text in ["sensitivity.breakdown_by_class.work", "path=0", "historical_window=2000",
                 f"year_index={year_index}", f"calendar_year={2026 + year_index}",
                 "abs_diff=", "allowed=", "1 mismatches"]:
        assert text in message


def test_lossless_schema_roundtrip_and_corrupt_npz_rejection(tmp_path):
    tree = {"nested": {"health": np.array([[np.nan, -1.]])},
            "alive": np.array([[True, False]]), "effective_years": 1}
    arrays = {}
    schema = describe_tree(tree, arrays)
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    target = outputs / "case.npz"
    np.savez_compressed(target, **arrays)
    compare(load_reference(tmp_path, "case", {"schema": schema}), tree)
    np.savez_compressed(target, **arrays, unexpected=np.array([1]))
    with pytest.raises(AssertionError, match="NPZ fields"):
        load_reference(tmp_path, "case", {"schema": schema})
    np.savez_compressed(target, **{**arrays, "alive": arrays["alive"].astype(int)})
    with pytest.raises(AssertionError, match="reference dtype"):
        load_reference(tmp_path, "case", {"schema": schema})


def test_runtime_objects_are_rejected_and_missing_reference_is_an_error(tmp_path):
    with pytest.raises(TypeError):
        describe_tree({"cache": object()}, {})
    with pytest.raises(TypeError):
        describe_tree({"cache": np.array([object()], dtype=object)}, {})
    with pytest.raises(FileNotFoundError):
        load_reference(tmp_path, "missing", {"schema": {}})
