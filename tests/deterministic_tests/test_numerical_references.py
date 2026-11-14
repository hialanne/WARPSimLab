"""Accepted financial outputs, including independently checked allocation changes."""

from functools import lru_cache

import numpy as np
import pytest

from tests.numerical_reference_helpers import (
    ATOL, RTOL, compare_core, load_reference, read_json,
)
from tests.numerical_reference_scenarios import CASES, DATA, activation_checks, run_case


REVISED_CASES = ("s1_single", "s2_married_nominal", "s2_married_real", "s2_married_raw",
    "s4_correlated", "s4_uncorrelated", "s5_historical_nominal", "s5_historical_real")
ALLOCATION_DATA = DATA.parent / "allocation_redesign"


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
            elif key == "qcd_settings":
                for owner in ("husband", "wife"):
                    assert item[owner] == dict(enabled=False, mode="Fixed Amount", amount=0.0,
                                               percent=0.0, start_age=70.5, end_age=None)

                assert set(item) == {"husband", "wife"}
            elif is_config and key == "root":
                assert item is None
            elif is_config and key in portfolio_inputs:
                assert item == portfolio_inputs[key], f"Redundant portfolio differs from explicit inputs: {key}"
            elif key == "sim_initial_allocation_mode" and item in {
                    "none", "dont-rebalance", "maintain-current-allocation"}:
                projected[key] = "original-allocation"
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
    # A broken withdrawal case must not prevent expense cases from being compared.
    return lru_cache(maxsize=None)(run_case)


@pytest.mark.parametrize("name", CASES)
def test_complete_core_matches_accepted_reference(name, manifest, current_results):
    actual, inputs = current_results(name)
    frozen_inputs = read_json(DATA / "inputs" / f"{name}.json")
    assert _without_legacy_allocation_defaults(inputs) == _without_legacy_allocation_defaults(frozen_inputs), name
    entry = manifest["cases"][name]
    checks = activation_checks(name, actual)
    assert all(checks.values()), f"{name}: inactive mechanisms: {[k for k, v in checks.items() if not v]}"
    assert checks == entry["activation"], f"{name}: activation contract changed"
    directory = DATA
    if name in REVISED_CASES:
        directory = ALLOCATION_DATA

    expected = load_reference(directory, name, entry)
    # Extend only the new disabled-QCD schema; every approved numerical leaf remains unchanged.
    for owner in ("husband", "wife"):
        expected["qcd_" + owner] = np.zeros_like(expected["rmd_" + owner])
        expected["qcd_rmd_offset_" + owner] = np.zeros_like(expected["rmd_" + owner])
        expected["taxable_rmd_" + owner] = expected["rmd_" + owner].copy()

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
        assert not np.array_equal(current_results(left)[0]["total_assets"],
                                  current_results(right)[0]["total_assets"]), (left, right)
