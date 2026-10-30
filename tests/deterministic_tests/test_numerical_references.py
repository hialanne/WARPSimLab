"""Accepted pre-refactor financial outputs; no generation/update execution path."""

import numpy as np
import pytest

from tests.numerical_reference_helpers import (
    ATOL, RTOL, compare_core, load_reference, read_json,
)
from tests.numerical_reference_scenarios import CASES, DATA, activation_checks, run_case


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
    assert inputs == frozen_inputs, f"{name}: scenario inputs changed; investigate, do not recapture"
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
