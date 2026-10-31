"""Accepted pre-refactor financial outputs; no generation/update execution path."""

import numpy as np
import pytest

from tests.numerical_reference_helpers import (
    ATOL, RTOL, compare_core, load_reference, read_json,
)
from tests.numerical_reference_scenarios import CASES, DATA, activation_checks, run_case


def _without_legacy_allocation_defaults(value, portfolio_inputs=None):
    """Project approved ownership removals after checking their frozen redundant values."""
    if portfolio_inputs is None:
        source = value.get("session", {}).get("truth", value)
        portfolio_inputs = {key: source.get(key) for key in ("husband_portfolio", "wife_portfolio")}
    if isinstance(value, dict):
        projected = {}
        is_config = {"years_to_simulate", "inflation_rate", "results_mode"} <= value.keys()
        for key, item in value.items():
            if key in {"household_eq_target", "household_bd_target", "household_cs_target"}:
                assert item is None, f"Unexpected prepared allocation in frozen inputs: {key}={item}"
            elif is_config and key == "root":
                assert item is None
            elif is_config and key in portfolio_inputs:
                assert item == portfolio_inputs[key], f"Redundant portfolio differs from explicit inputs: {key}"
            else:
                projected[key] = _without_legacy_allocation_defaults(item, portfolio_inputs)
        return projected
    if isinstance(value, list):
        return [_without_legacy_allocation_defaults(item, portfolio_inputs) for item in value]
    return value


@pytest.fixture(scope="module")
def manifest():
    document = read_json(DATA / "manifest.json")
    assert document["format_version"] == 1
    assert document["comparison"] == dict(atol=ATOL, rtol=RTOL)
    assert set(document["cases"]) == set(CASES)
    return document


@pytest.fixture(scope="module")
def current_results():
    return {name: run_case(name) for name in CASES}


@pytest.mark.parametrize("name", CASES)
def test_complete_core_matches_accepted_reference(name, manifest, current_results):
    actual, inputs = current_results[name]
    frozen_inputs = read_json(DATA / "inputs" / f"{name}.json")
    assert _without_legacy_allocation_defaults(inputs) == _without_legacy_allocation_defaults(frozen_inputs), name
    entry = manifest["cases"][name]
    checks = activation_checks(name, actual)
    assert all(checks.values()), f"{name}: inactive mechanisms: {[k for k, v in checks.items() if not v]}"
    assert checks == entry["activation"], f"{name}: activation contract changed"
    expected = load_reference(DATA, name, entry)
    assert actual["total_assets"].shape == (entry["path_count"], entry["retained_year_count"])
    compare_core(actual, expected, case=name, start_year=entry["start_year"],
                 historical_windows=expected["historical_window_start_year"])


def test_variants_exercise_different_financial_results(current_results):
    for left, right in [
        ("s2_married_nominal", "s2_married_real"),
        ("s4_correlated", "s4_uncorrelated"),
        ("s5_historical_nominal", "s5_historical_real"),
        ("s6_baseline", "s6_modified"),
    ]:
        assert not np.array_equal(current_results[left][0]["total_assets"],
                                  current_results[right][0]["total_assets"]), (left, right)
