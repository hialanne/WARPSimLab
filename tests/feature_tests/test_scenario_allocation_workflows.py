"""Scenario allocation through real GUI configuration and financial execution."""

import copy
from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.gui.scenario import gui_scenarioState as mod
from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.engines import monteCarloEngine, portfolioEngine
from src.warpsimlab.sim.simulation import run_pipeline
from tests.architectural_helpers import assert_tree_equal, make_person, make_portfolio
from tests.feature_tests.workflow_helpers import inputs_from_gui, make_gui
from tests.module_tests.gui.scenario.test_scenario_allocation_redesign import BUCKETS, STATE_BUCKETS, asset_values


def allocation_session(tmp_path, rebalance=True, amounts=(334, 333, 333)):
    gui = make_gui(tmp_path, second_person_enabled=True, always_use_expense_mode=True,
                   calculate_simulated_shortfall_rate=False, overlay_profit_loss=False)
    gui.husband = make_person(age=60, retire_age=65, ss_age=67)
    gui.wife = make_person(age=58, retire_age=65, ss_age=67)
    gui.husband_portfolio = make_portfolio(equity_pre=amounts[0], bond_post=amounts[1], cash_roth=amounts[2])
    gui.wife_portfolio = make_portfolio(hsa_equity=amounts[0], cash_pre=amounts[2], bond_roth=amounts[1])
    gui.simulation_settings["rebalance_every_year"] = rebalance
    gui.simulation_controls["rebalance_every_year"] = not rebalance
    gui.simulation_controls["manual_expenses"] = True
    state = mod.ScenarioSessionState()
    manager = mod.ScenarioStateManager(gui, state)
    manager.build_snapshots_from_truth()
    stocks, bonds, cash = mod.compute_portfolio_percentages(state.baseline_portfolio_snapshots)
    values = SimpleNamespace(husband_ret_age=65, husband_ss_age=67, wife_ret_age=65, wife_ss_age=67,
        inflation=gui.inflation, fund_expense=gui.simulation_settings["fund_expense"],
        stocks=stocks, bonds=bonds, cash=cash, dynamic_value=100,
        calculate_real_dollars=False, enable_annotations=False)
    manager.apply_control_values(values)
    manager.capture_baseline_from_scenario()
    return manager, gui, state, values


@pytest.mark.parametrize("rebalance", [False, True])
def test_snapshot_rebalancing_comes_from_simulation_settings(tmp_path, rebalance):
    _, gui, state, _ = allocation_session(tmp_path, rebalance)
    assert gui.simulation_controls["rebalance_every_year"] is not rebalance
    assert state.baseline_retirement_snapshots.rebalance_every_year is rebalance
    assert state.retirement_snapshots.rebalance_every_year is rebalance


@pytest.mark.parametrize("rebalance", [False, True])
def test_slider_roundtrips_use_fresh_original_holdings_and_preserve_original_results(tmp_path, monkeypatch, rebalance):
    manager, gui, state, values = allocation_session(tmp_path, rebalance)
    baseline = copy.deepcopy(state.baseline_portfolio_snapshots)
    gui_before = copy.deepcopy((vars(gui.husband_portfolio), vars(gui.wife_portfolio)))
    calls = []

    def capture(husband_portfolio, wife_portfolio, husband, wife, expenses, config):
        portfolios = {"husband": husband_portfolio, "wife": wife_portfolio}
        assert config.sim_initial_allocation_mode == "original-allocation"
        assert config.rebalance_every_year is rebalance
        calls.append(copy.deepcopy(portfolios))
        # A pipeline consuming or mutating inputs must not leak into later runs.
        husband_portfolio.equity_pre = -999
        return {"holdings": copy.deepcopy(calls[-1])}

    monkeypatch.setattr(mod, "run_pipeline", capture)
    manager.compute_baseline_results(False, "fill")
    saved_results = copy.deepcopy(state.baseline_results["p"])
    manager.compute_scenario_results(False, "fill")
    for owner in baseline:
        assert vars(calls[0][owner]) == vars(baseline[owner])
        assert vars(calls[1][owner]) == vars(baseline[owner])
    initial_stocks, initial_bonds = values.stocks, values.bonds
    assert (initial_stocks, initial_bonds) == (33, 33)
    assert asset_values(baseline) == [668, 666, 666]
    for stocks, bonds in [(50, 33), (33, 45), (60, 20), (50, 33), (33, 33)]:
        values.stocks, values.bonds, values.cash = stocks, bonds, 100 - stocks - bonds
        manager.apply_control_values(values)
        manager.compute_scenario_results(False, "fill")
        totals = asset_values(calls[-1])
        if (stocks, bonds) == (33, 33):
            for owner in baseline:
                assert vars(calls[-1][owner]) == vars(baseline[owner])
        else:
            target_stock = 33.4
            target_bond = 33.3
            if stocks != initial_stocks:
                target_stock = stocks

            if bonds != initial_bonds:
                target_bond = bonds

            assert totals == pytest.approx([20 * target_stock, 20 * target_bond, 20 * (100 - target_stock - target_bond)])
        for owner in baseline:
            assert vars(state.baseline_portfolio_snapshots[owner]) == vars(baseline[owner])
            assert vars(state.portfolio_snapshots[owner]) == vars(baseline[owner])
            assert vars(state.baseline_results["p"]["holdings"][owner]) == vars(saved_results["holdings"][owner])
    for owner in baseline:
        assert vars(calls[2][owner]) == vars(calls[5][owner])
    assert (vars(gui.husband_portfolio), vars(gui.wife_portfolio)) == gui_before


@pytest.mark.parametrize("changed_asset,amounts,target", [("stocks", (604, 394, 2), 61),
    ("bonds", (394, 604, 2), 61)])
def test_slider_boundary_with_unchanged_exact_other_asset_has_valid_target(tmp_path, monkeypatch, changed_asset, amounts, target):
    manager, _, state, values = allocation_session(tmp_path, amounts=amounts)
    # Valid displayed sliders total 100, but retaining the other exact percentage
    # would exceed 100. The UI needs a defined feasible allocation at this boundary.
    setattr(values, changed_asset, target)
    values.cash = 100 - values.stocks - values.bonds
    assert values.cash == 0
    manager.apply_control_values(values)
    monkeypatch.setattr(mod, "run_pipeline", lambda *args: {})
    manager.compute_scenario_results(False, "fill")
    assert state.scenario_results["sim_config"].sim_initial_allocation_mode == "original-allocation"


@pytest.mark.parametrize("rebalance", [False, True])
def test_normal_and_unchanged_explorer_historical_windows_match(tmp_path, monkeypatch, rebalance):
    manager, gui, state, _ = allocation_session(tmp_path, rebalance)
    years = np.arange(2000, 2010)
    returns = dict(years=years, eq=np.array([-0.4, 0.2, 0.1, -0.1, 0.3, 0.04, -0.2, 0.1, 0.05, 0.02]),
                   bd=np.linspace(-0.03, 0.05, 10), cs=np.linspace(0, 0.02, 10), re=np.zeros(10))
    inflation = dict(years=years.copy(), inflation=np.full(10, 0.025))
    monkeypatch.setattr(monteCarloEngine, "load_historical_asset_returns_csv", lambda filename: returns)
    monkeypatch.setattr(monteCarloEngine, "load_historical_inflation_csv", lambda filename: inflation)
    gui.simulation_controls.update(results_mode="risk_analysis", risk_analysis_mode="historical_windows",
        inflation_mode="nominal", calculate_simulated_shortfall_rate=True)
    gui.expensesDict = DynamicExpenses()
    gui.expensesDict.add_expense(2027, 240)
    gui.special_income_streams, gui.roth_flows = [], []
    normal_inputs = inputs_from_gui(gui)
    assert normal_inputs["sim_config"].sim_initial_allocation_mode == "original-allocation"
    normal = run_pipeline(**normal_inputs)
    assert not np.array_equal(normal["core"]["total_assets"][0], normal["core"]["total_assets"][1])
    manager.compute_baseline_results(False, "historical_risk")
    changed = manager.compute_scenario_results(False, "historical_risk")["p"]
    for candidate in (state.baseline_results["p"], changed):
        assert normal["core"]["historical_window_start_year"].tolist() == [2000, 2001, 2002]
        assert_tree_equal(candidate["core"], normal["core"])
        assert_tree_equal(candidate["portfolio_plot_data"].percentiles, normal["portfolio_plot_data"].percentiles)
        assert candidate["summary_results"]["simulated_shortfall_rate"] == normal["summary_results"]["simulated_shortfall_rate"]
        expected_depleted = np.count_nonzero(np.any(normal["core"]["total_assets"] <= 0, axis=1))
        actual_depleted = np.count_nonzero(np.any(candidate["core"]["total_assets"] <= 0, axis=1))
        assert actual_depleted == expected_depleted


@pytest.mark.parametrize("expense_mode", [False, True])
@pytest.mark.parametrize("rebalance", [False, True])
def test_real_scenario_execution_initializes_adjusted_holdings_and_rebalances_account_ratios(
    tmp_path, monkeypatch, expense_mode, rebalance,
):
    manager, gui, _, values = allocation_session(tmp_path, rebalance)
    gui.simulation_settings.update(years_to_simulate=1, fixed_years_to_simulate=1, use_fund_expenses=False)
    gui.simulation_controls.update(always_use_expense_mode=expense_mode, manual_expenses=expense_mode, calculate_income_taxes=False,
        calculate_payroll_taxes=False, calculate_state_taxes=False, include_rmd=False,
        retirement_withdraw_mode="Off",
        post_tax_equity_dividend_yield=0, post_tax_bond_interest_yield=0, post_tax_cash_interest_yield=0)
    gui.expensesDict = DynamicExpenses()
    gui.special_income_streams, gui.roth_flows = [], []
    gui.eq_mean, gui.bd_mean, gui.cs_mean = 20, -5, 1
    values.stocks, values.bonds, values.cash = 60, 25, 15
    values.husband_ret_age, values.wife_ret_age = 60, 58
    manager.apply_control_values(values)
    created, rebalanced = [], []
    original_create = portfolioEngine.create_sim_portfolio
    original_rebalance = portfolioEngine.rebalance

    def capture_create(portfolio, sim_config=None, run_context=None):
        state = original_create(portfolio, sim_config, run_context=run_context)
        for source_fields, state_fields in zip(BUCKETS, STATE_BUCKETS):
            for source, target in zip(source_fields, state_fields):
                assert getattr(state, target) == getattr(portfolio, source)
        created.append(copy.deepcopy(portfolio))
        return state

    def capture_rebalance(state, sim_config, run_context=None):
        before = copy.deepcopy(state)
        totals = []
        for fields in STATE_BUCKETS:
            total = 0
            for field in fields:
                total += getattr(state, field)
            totals.append(total)
        result = original_rebalance(state, sim_config, run_context=run_context)
        for bucket, fields, total in zip(("pre", "post", "roth", "hsa"), STATE_BUCKETS, totals):
            ratio_total = 0
            for asset in ("eq", "bd", "cs"):
                ratio_total += getattr(state, f"{asset}_ratio_{bucket}")
            for asset, field in zip(("eq", "bd", "cs"), fields):
                if ratio_total > 0:
                    assert getattr(state, field) == pytest.approx(total * getattr(state, f"{asset}_ratio_{bucket}"))
                else:
                    assert getattr(state, field) == getattr(before, field)
        rebalanced.append(state)
        return result

    monkeypatch.setattr(portfolioEngine, "create_sim_portfolio", capture_create)
    monkeypatch.setattr(portfolioEngine, "rebalance", capture_rebalance)
    manager.compute_scenario_results(False, "fill")
    assert len(created) == 2
    assert asset_values({"husband": created[0], "wife": created[1]}) == pytest.approx([1200, 500, 300])
    if rebalance:
        assert len(rebalanced) == 2
    else:
        assert rebalanced == []
