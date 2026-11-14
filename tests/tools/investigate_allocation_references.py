"""Read-only numerical investigation for the allocation redesign handoff."""

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

from src.warpsimlab.dataClasses.portfolioState import PortfolioState
from src.warpsimlab.sim.engines import portfolioEngine
from tests.deterministic_tests.test_numerical_references import _without_legacy_allocation_defaults
from tests.numerical_reference_helpers import ATOL, RTOL, compare_core, describe_tree, load_reference, read_json
from tests.numerical_reference_scenarios import CASES, DATA, build_case, run_case


BUCKETS = (("eq_pre", "bd_pre", "cs_pre"), ("eq_post", "bd_post", "cs_post"),
    ("eq_roth", "bd_roth", "cs_roth"), ("hsa_eq", "hsa_bd", "hsa_cs"))
INPUT_BUCKETS = (("equity_pre", "bond_pre", "cash_pre"), ("equity_post", "bond_post", "cash_post"),
    ("equity_roth", "bond_roth", "cash_roth"), ("hsa_equity", "hsa_bond", "hsa_cash"))


def independent_replay(name, legacy=False):
    """Replace only allocation operations with direct dollar-and-weight arithmetic.

    The old household policy must reproduce accepted outputs before the new
    per-category policy can be used to corroborate a reference change.
    Targets live in a separate test ledger; no production ratio/merge code is used.
    """
    targets = {}
    household = None
    if legacy and not name.startswith("s6_"):
        case = build_case(name)
        config = case["sim_config"]
        if config.sim_initial_allocation_mode == "original-allocation" and not name.startswith("s3_"):
            amounts = np.zeros(3)
            owners = [case["husband_portfolio"]]
            if config.second_person_enabled:
                owners.append(case["wife_portfolio"])

            for owner in owners:
                for attrs in INPUT_BUCKETS:
                    for index, attr in enumerate(attrs):
                        amounts[index] += getattr(owner, attr, 0.0)
            household = amounts / sum(amounts)

    def create(portfolio, sim_config=None, run_context=None):
        values = {}
        for attrs, inputs in zip(BUCKETS, INPUT_BUCKETS):
            for attr, source in zip(attrs, inputs):
                values[attr] = getattr(portfolio, source, 0.0)
        values["re_post"] = 0.0
        if sim_config.include_realestate:
            values["re_post"] = portfolio.real_estate

        state = PortfolioState(**values)
        ledger = []
        mode = sim_config.sim_initial_allocation_mode
        for attrs in BUCKETS:
            amounts = np.array([values[attrs[0]], values[attrs[1]], values[attrs[2]]])
            total = sum(amounts)
            weights = np.zeros(3)
            if total:
                weights = amounts / total

            if household is not None:
                weights = household.copy()
            elif mode == "custom":
                weights = np.array((sim_config.custom_stock, sim_config.custom_bonds, sim_config.custom_cash))
            elif mode in ("30-30-40", "50-30-20", "70-20-10"):
                weights = np.array(tuple(map(float, mode.split("-")))) / 100

            ledger.append(weights)
            for attr, weight in zip(attrs, weights):
                setattr(state, attr, total * weight)
        targets[id(state)] = (state, ledger, mode)
        return state

    def rebalance(state, sim_config, run_context=None):
        for attrs, weights in zip(BUCKETS, targets[id(state)][1]):
            if sum(weights) == 0:
                continue

            total = sum(getattr(state, attr) for attr in attrs)
            for attr, weight in zip(attrs, weights):
                setattr(state, attr, total * weight)

    def transfer(deceased, survivor):
        for index, attrs in enumerate(BUCKETS):
            left = np.array([getattr(survivor, attrs[0]), getattr(survivor, attrs[1]), getattr(survivor, attrs[2])])
            right = np.array([getattr(deceased, attrs[0]), getattr(deceased, attrs[1]), getattr(deceased, attrs[2])])
            left_total, right_total = sum(left), sum(right)
            if not legacy and targets[id(survivor)][2] == "original-allocation" and left_total + right_total:
                left_weights = targets[id(survivor)][1][index]
                right_weights = targets[id(deceased)][1][index]
                if sum(left_weights) == 0 and left_total:
                    left_weights = left / left_total

                if sum(right_weights) == 0 and right_total:
                    right_weights = right / right_total

                targets[id(survivor)][1][index] = (
                    left_weights * left_total + right_weights * right_total) / (left_total + right_total)
                targets[id(deceased)][1][index] = np.zeros(3)
            for attr, amount in zip(attrs, left + right):
                setattr(survivor, attr, amount)
                setattr(deceased, attr, 0.0)
        survivor.re_post += deceased.re_post
        deceased.re_post = 0.0

    with patch.object(portfolioEngine, "create_sim_portfolio", create), \
            patch.object(portfolioEngine, "rebalance", rebalance), \
            patch.object(portfolioEngine, "transfer_portfolio_to_survivor", transfer):
        return run_case(name)[0]


def extend_disabled_qcd(expected):
    for owner in ("husband", "wife"):
        expected["qcd_" + owner] = np.zeros_like(expected["rmd_" + owner])
        expected["qcd_rmd_offset_" + owner] = np.zeros_like(expected["rmd_" + owner])
        expected["taxable_rmd_" + owner] = expected["rmd_" + owner].copy()


def differences(actual, expected, path=""):
    result = []
    if isinstance(expected, dict):
        for key in expected.keys() | actual.keys():
            location = f"{path}.{key}".lstrip(".")
            if key not in actual or key not in expected:
                result.append(dict(field=location, expected=expected.get(key), actual=actual.get(key)))
            else:
                result.extend(differences(actual[key], expected[key], location))
    elif actual != expected:
        result.append(dict(field=path, expected=expected, actual=actual))
    return result


def main():
    manifest = read_json(DATA / "manifest.json")
    findings = {}
    for name in CASES:
        actual, inputs = run_case(name)
        frozen = read_json(DATA / "inputs" / f"{name}.json")
        expected = load_reference(DATA, name, manifest["cases"][name])
        extend_disabled_qcd(expected)
        entry = manifest["cases"][name]
        old_policy = independent_replay(name, legacy=True)
        compare_core(old_policy, expected, case=name + ".legacy_replay", start_year=entry["start_year"])
        independent = independent_replay(name)
        compare_core(actual, independent, case=name + ".independent_replay", start_year=entry["start_year"])
        current_arrays, expected_arrays = {}, {}
        describe_tree(actual, current_arrays)
        describe_tree(expected, expected_arrays)
        changes = []
        for field, values in expected_arrays.items():
            current = current_arrays[field]
            if values.dtype.kind == "f":
                equal = (current == values) | (np.isnan(current) & np.isnan(values))
            else:
                equal = current == values

            if not np.all(equal):
                coordinates = np.argwhere(~equal)
                examples = []
                for coordinate in coordinates:
                    index = tuple(coordinate)
                    examples.append(dict(index=coordinate.tolist(), expected=values[index].item(), actual=current[index].item()))
                outside = int(np.count_nonzero(~equal))
                if values.dtype.kind == "f":
                    outside = int(np.count_nonzero(~np.isclose(current, values, atol=ATOL, rtol=RTOL, equal_nan=True)))

                changes.append(dict(field=field, outside_tolerance=outside, values=examples))
        input_changes = differences(_without_legacy_allocation_defaults(inputs), _without_legacy_allocation_defaults(frozen))
        for change in differences(inputs, frozen):
            if change["field"].endswith("sim_initial_allocation_mode"):
                input_changes.append(change)
        findings[name] = dict(inputs=input_changes, outputs=changes)
        print(name, len(changes), "changed fields; input differences:", findings[name]["inputs"])
    Path("tests/allocation_reference_investigation.json").write_text(json.dumps(findings, indent=2) + "\n")


if __name__ == "__main__":
    main()
