"""Lossless core schema/NPZ reading and strict, coordinate-aware comparisons.

This module never writes reference files. Capture is a separate manual command.
"""

import json

import numpy as np


ATOL = 1e-8
RTOL = 1e-13
EXACT_FLOAT_FIELDS = {"year", "tax_bracket", "survivor_expense_factor"}
SENTINEL_FIELDS = {"federal_bracket_lower_threshold", "federal_bracket_upper_threshold"}


def describe_tree(value, arrays, path=""):
    """Describe all containers/leaves; reject opaque objects rather than omit them."""
    if type(value) is dict:
        return {"kind": "dict", "children": {
            key: describe_tree(item, arrays, f"{path}.{key}".lstrip("."))
            for key, item in value.items()
        }}
    if isinstance(value, np.ndarray):
        if value.dtype.kind not in "biufUS":
            raise TypeError(f"{path}: unsupported dtype {value.dtype}")
        arrays[path] = value
        return dict(kind="array", key=path, dtype=value.dtype.str, shape=list(value.shape))
    if type(value) in (int, bool, str, float) or value is None:
        return dict(kind="scalar", type=type(value).__name__, value=value)
    raise TypeError(f"{path}: unsupported result {type(value)}")


def load_reference(directory, name, entry):
    """Validate persisted schema and exact NPZ contents with pickle disabled."""
    with np.load(directory / "outputs" / f"{name}.npz", allow_pickle=False) as data:
        used = set()

        def restore(node):
            if node["kind"] == "dict":
                return {key: restore(child) for key, child in node["children"].items()}
            if node["kind"] == "scalar":
                value = node["value"]
                assert type(value).__name__ == node["type"], f"{name}: corrupt scalar schema"
                return value
            assert node["kind"] == "array", f"{name}: unknown schema node"
            key = node["key"]
            used.add(key)
            array = data[key]
            assert array.dtype.str == node["dtype"], f"{name}.{key}: reference dtype"
            assert list(array.shape) == node["shape"], f"{name}.{key}: reference shape"
            assert array.dtype.kind in "biufUS", f"{name}.{key}: unsupported reference dtype"
            return array.copy()

        result = restore(entry["schema"])
        assert used == set(data.files), f"{name}: unexpected/missing NPZ fields"
    return result


def compare_core(actual, expected, *, case, start_year, historical_windows=None):
    """Compare every leaf, with exact structure and explicit finite float bounds."""
    def compare(a, e, field):
        label = f"{case}.{field}".rstrip(".")
        assert type(a) is type(e), f"{label}: type {type(a).__name__} != {type(e).__name__}"
        if isinstance(e, dict):
            assert a.keys() == e.keys(), (
                f"{label}: missing={sorted(e.keys() - a.keys())}, added={sorted(a.keys() - e.keys())}")
            for key in e:
                compare(a[key], e[key], f"{field}.{key}".lstrip("."))
            return
        if not isinstance(e, np.ndarray):
            assert a == e, f"{label}: actual={a!r}, expected={e!r}"
            return
        assert a.shape == e.shape, f"{label}: shape {a.shape} != {e.shape}"
        assert a.dtype == e.dtype, f"{label}: dtype {a.dtype} != {e.dtype}"
        exact = e.dtype.kind != "f" or field in EXACT_FLOAT_FIELDS
        if e.dtype.kind == "f":
            finite = np.isfinite(a) & np.isfinite(e)
            good = (np.isnan(a) & np.isnan(e)) | ((a == e) & ~finite)
            delta = np.zeros(e.shape)
            delta[finite] = np.abs(a[finite] - e[finite])
            bound = np.zeros(e.shape) if exact else ATOL + RTOL * np.abs(e)
            good[finite] = delta[finite] <= bound[finite]
            if field in SENTINEL_FIELDS:
                bound[e == -1.0] = 0.0
                good[e == -1.0] = a[e == -1.0] == -1.0
        else:
            good = a == e
            finite = np.zeros(e.shape, dtype=bool)
            delta = bound = np.zeros(e.shape)
        if np.all(good):
            return
        details = []
        for index in np.argwhere(~good)[:3]:
            coord = tuple(index)
            location = f"index={coord}"
            if e.ndim >= 1:
                location += f", path={index[0]}"
                if historical_windows is not None and historical_windows[index[0]] >= 0:
                    location += f", historical_window={historical_windows[index[0]]}"
            if e.ndim == 2:
                location += f", year_index={index[1]}, calendar_year={start_year + index[1]}"
            difference = delta[coord] if finite[coord] else "nonfinite/exact mismatch"
            details.append(f"{location}: actual={a[coord]!r}, expected={e[coord]!r}, "
                           f"abs_diff={difference}, allowed={bound[coord]}")
        raise AssertionError(
            f"{label}: {np.count_nonzero(~good)} mismatches; "
            f"max_finite_abs_diff={np.max(delta, initial=0)}\n" + "\n".join(details))

    compare(actual, expected, "")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))
