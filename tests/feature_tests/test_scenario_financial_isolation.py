"""Scenario Explorer ownership with its real config builder and financial pipeline.

The GUI mixin is instantiated without Tk widgets; no simulation or cloning
functions are mocked. These tests protect financial state rather than display.
"""

import copy
from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.gui.gui_run import PortfolioSimulatorGUI_RunMixin
from src.warpsimlab.gui.scenario.gui_scenarioState import ScenarioSessionState, ScenarioStateManager
from tests.architectural_helpers import assert_tree_equal, make_execution_case, public_input_tree


def make_session(expense_mode):
    case = make_execution_case(always_use_expense_mode=expense_mode)
    config = case["sim_config"]
    gui = PortfolioSimulatorGUI_RunMixin()
    for name in ["husband", "wife", "husband_portfolio", "wife_portfolio"]:
        setattr(gui, name, case[name])
    gui.expensesDict = case["expenses"]
    gui.simulation_controls = {
        name: copy.deepcopy(value) for name, value in vars(config).items()
        if not name.startswith("_")
    }
    gui.simulation_controls["manual_expenses"] = expense_mode
    gui.simulation_settings = dict(start_year=2026, years_to_simulate=8,
                                   num_sims=3, fund_expense=0.2, use_fund_expenses=True)
    gui.inflation = config.inflation_rate * 100
    for name in ["eq_mean", "bd_mean", "cs_mean", "re_mean", "eq_std", "bd_std", "cs_std", "re_std"]:
        setattr(gui, name, getattr(config, name) * 100)
    gui.historical_magi = copy.deepcopy(config.historical_magi)
    gui.special_income_streams = copy.deepcopy(config.special_income_streams)
    gui.roth_flows = copy.deepcopy(config.roth_flows)
    gui.root = None
    gui.warpsimlab_version = "test"
    gui.loaded_data_file = None
    gui.mode_var = SimpleNamespace(get=lambda: "Advanced")
    state = ScenarioSessionState()
    manager = ScenarioStateManager(gui, state)
    manager.build_snapshots_from_truth()
    # Follow the controller's session initialization: apply initial controls,
    # then capture the baseline before applying the modified slider values.
    values = SimpleNamespace(
        husband_ret_age=70, husband_ss_age=70, wife_ret_age=68, wife_ss_age=68,
        inflation=gui.inflation, fund_expense=0.2, stocks=64, bonds=24, cash=12,
        dynamic_value=100 if expense_mode else 5.0,
        calculate_real_dollars=False, enable_annotations=True,
    )
    manager.apply_control_values(values)
    manager.capture_baseline_from_scenario()
    values.husband_ret_age = 71
    values.wife_ret_age = 69
    values.wife_ss_age = 69
    values.inflation = 4.0
    values.fund_expense = 0.35
    values.stocks, values.bonds, values.cash = 65, 25, 10
    values.dynamic_value = 120 if expense_mode else 6.5
    manager.apply_control_values(values)
    return manager, gui, state


def session_input_tree(gui, state):
    truth_names = ["husband", "wife", "husband_portfolio", "wife_portfolio", "expensesDict",
                   "simulation_controls", "simulation_settings", "historical_magi",
                   "special_income_streams", "roth_flows"]
    snapshot_names = ["baseline_person_snapshots", "baseline_portfolio_snapshots",
                      "baseline_retirement_snapshots", "person_snapshots",
                      "portfolio_snapshots", "retirement_snapshots"]
    return public_input_tree(dict(
        truth={name: getattr(gui, name) for name in truth_names},
        snapshots={name: getattr(state, name) for name in snapshot_names},
    ))


@pytest.mark.parametrize("expense_mode", [False, True])
@pytest.mark.parametrize("plot_style", ["fill", "risk_analysis"])
@pytest.mark.parametrize("order", [("baseline", "scenario"), ("scenario", "baseline")])
def test_baseline_and_modified_scenarios_are_independent_with_real_execution(
    expense_mode, plot_style, order,
):
    manager, gui, state = make_session(expense_mode)
    source_before = session_input_tree(gui, state)

    def evaluate(which):
        if which == "baseline":
            manager.compute_baseline_results(True, plot_style)
            return state.baseline_results
        return manager.compute_scenario_results(True, plot_style)

    outputs = {which: evaluate(which) for which in order}
    saved = {which: copy.deepcopy(result["p"]["core"]) for which, result in outputs.items()}
    assert not np.array_equal(saved["baseline"]["total_assets"], saved["scenario"]["total_assets"])
    assert_tree_equal(session_input_tree(gui, state), source_before, "truth and snapshots after execution")
    # Opposite evaluation order must preserve both comprehensive financial results.
    for which in reversed(order):
        assert_tree_equal(evaluate(which)["p"]["core"], saved[which], which)
        assert_tree_equal(outputs[which]["p"]["core"], saved[which], f"previous {which} results")
    fresh_manager, _, fresh_state = make_session(expense_mode)
    fresh_manager.compute_baseline_results(True, plot_style)
    fresh_manager.compute_scenario_results(True, plot_style)
    assert_tree_equal(fresh_state.baseline_results["p"]["core"], saved["baseline"])
    assert_tree_equal(fresh_state.scenario_results["p"]["core"], saved["scenario"])
    # Returned scenario financial arrays and nested copied annotations are not
    # storage for either baseline output or saved session/truth inputs.
    scenario = state.scenario_results
    assert not np.shares_memory(scenario["p"]["core"]["total_assets"],
                                state.baseline_results["p"]["core"]["total_assets"])
    scenario["p"]["core"]["total_assets"][...] = -1
    scenario["retirement_snapshots"].annotation_strings[0][0]["text"] = "changed returned copy"
    assert_tree_equal(state.baseline_results["p"]["core"], saved["baseline"])
    assert_tree_equal(session_input_tree(gui, state), source_before)
    assert_tree_equal(evaluate("scenario")["p"]["core"], saved["scenario"])


@pytest.mark.parametrize("expense_mode", [False, True])
def test_comparison_view_reconciles_real_results_and_reopened_session(expense_mode):
    manager, gui, state = make_session(expense_mode)
    assert manager.build_results_view_model() is None
    manager.compute_baseline_results(True, "fill")
    assert manager.build_results_view_model() is None
    manager.compute_scenario_results(True, "fill")
    comparison = manager.build_results_view_model()
    for metrics, result in [(comparison.original_metrics, state.baseline_results),
                            (comparison.changed_metrics, state.scenario_results)]:
        summary = result["p"]["summary_results"]
        assert metrics.ending_portfolio == summary["total_assets"][-1]
        assert metrics.lifetime_taxes == pytest.approx(sum(summary["taxes"]))
        assert metrics.lifetime_funding_gap == pytest.approx(sum(summary["funding_gap"]))
        for name, key in [("ending_pre_tax", "pre_tax_assets"),
                          ("ending_after_tax", "post_tax_assets"),
                          ("ending_roth", "roth_assets"), ("ending_hsa", "hsa_assets")]:
            assert getattr(metrics, name) == summary[key][-1]
    assert comparison.original_assumptions.husband_retire_age == 70
    assert comparison.changed_assumptions.husband_retire_age == 71
    assert comparison.changed_assumptions.dynamic_value == (120 if expense_mode else 6.5)
    saved = copy.deepcopy(state.baseline_results["p"]["core"])
    # Closing and reopening starts from current main-window truth, not previous
    # slider edits or mutable returned comparison data.
    reopened = ScenarioStateManager(gui, ScenarioSessionState())
    reopened.build_snapshots_from_truth()
    assert reopened.session_state.person_snapshots["husband"].retire_age == 70
    assert reopened.session_state.baseline_results is None
    comparison.changed_metrics.ending_portfolio = -1
    assert_tree_equal(state.baseline_results["p"]["core"], saved)
    assert manager.build_results_view_model().changed_metrics.ending_portfolio != -1
