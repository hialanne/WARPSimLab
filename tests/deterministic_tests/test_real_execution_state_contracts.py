import copy

import numpy as np
import pytest

from src.warpsimlab.sim.simulation import run_pipeline
from tests.architectural_helpers import (
    assert_tree_equal, make_execution_case, public_input_tree, user_config_tree,
)


@pytest.mark.parametrize("allocation", ["none", "maintain-current-allocation"])
@pytest.mark.parametrize("expense_mode", [False, True])
def test_real_preparation_and_overlays_preserve_user_configuration(allocation, expense_mode):
    case = make_execution_case(
        sim_initial_allocation_mode=allocation, always_use_expense_mode=expense_mode,
        overlay_tax_impacts=True, overlay_fund_expense_impacts=True,
    )
    config = case["sim_config"]
    config_before = user_config_tree(config)
    domain_before = public_input_tree({key: value for key, value in case.items() if key != "sim_config"})
    first = run_pipeline(**case)
    assert_tree_equal(user_config_tree(config), config_before, "user config after overlays")
    second = run_pipeline(**case)
    assert_tree_equal(user_config_tree(config), config_before, "user config after reuse")
    assert_tree_equal(public_input_tree({key: value for key, value in case.items() if key != "sim_config"}),
                      domain_before, "domain inputs")
    assert_tree_equal(second["core"], first["core"])
    for name in ["median_without_taxes", "median_without_fund_expenses",
                 "median_without_taxes_or_fund_expenses"]:
        np.testing.assert_array_equal(getattr(second["portfolio_plot_data"], name),
                                      getattr(first["portfolio_plot_data"], name))


@pytest.mark.parametrize("expense_mode", [False, True])
@pytest.mark.parametrize("inflation_mode", ["nominal", "real"])
def test_reused_and_fresh_inputs_reproduce_every_core_array(expense_mode, inflation_mode):
    case = make_execution_case(always_use_expense_mode=expense_mode, inflation_mode=inflation_mode)
    first = run_pipeline(**case)
    saved = copy.deepcopy(first["core"])
    repeated = run_pipeline(**case)
    fresh = run_pipeline(**make_execution_case(
        always_use_expense_mode=expense_mode, inflation_mode=inflation_mode,
    ))
    assert_tree_equal(first["core"], saved, "earlier results after reuse")
    assert_tree_equal(repeated["core"], saved, "reused inputs")
    assert_tree_equal(fresh["core"], saved, "fresh equivalent inputs")
    assert_tree_equal(repeated["summary_results"], first["summary_results"], "summary")
    assert_tree_equal(fresh["summary_results"], first["summary_results"], "fresh summary")
    # Guard against an accidentally trivial scenario or missing transition.
    assert np.any(saved["taxes"] > 0)
    assert np.any(saved["roth_conversions"] > 0)
    assert np.any(saved["survivor_state"])
    assert saved["husband_death_event"].sum() == 1
    assert saved["wife_death_event"].sum() == 1


def test_returned_results_are_detached_from_other_runs_and_nested_user_inputs():
    case = make_execution_case(always_use_expense_mode=True)
    before = user_config_tree(case["sim_config"])
    first = run_pipeline(**case)["core"]
    second = run_pipeline(**case)["core"]
    saved_second = copy.deepcopy(second)
    for key, value in first.items():
        if isinstance(value, dict):
            arrays = value.items()
            other = second[key]
        elif isinstance(value, np.ndarray):
            arrays = [(key, value)]
            other = second
        else:
            continue
        for name, array in arrays:
            assert not np.shares_memory(array, other[name]), f"{key}.{name}"
            array[...] = 0
    assert_tree_equal(second, saved_second)
    assert_tree_equal(user_config_tree(case["sim_config"]), before)
    assert_tree_equal(run_pipeline(**case)["core"], saved_second)
