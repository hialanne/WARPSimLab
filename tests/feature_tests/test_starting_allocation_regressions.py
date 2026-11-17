"""Starting allocations through GUI execution and Scenario Explorer."""

import copy
from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.gui import gui_run
from src.warpsimlab.gui.scenario import gui_scenarioState as scenario
from src.warpsimlab.sim.engines import monteCarloEngine, portfolioEngine
from src.warpsimlab.sim.simulation import run_pipeline
from tests.architectural_helpers import assert_tree_equal, public_input_tree
from tests.feature_tests.workflow_helpers import make_gui
from tests.module_tests.gui.scenario.test_scenario_allocation_redesign import BUCKETS, asset_values, mixed_household

MODES = ("dont-rebalance", "30-30-40", "50-30-20", "70-20-10", "custom")
TARGETS = {"30-30-40": (30, 30, 40), "50-30-20": (50, 30, 20),
           "70-20-10": (70, 20, 10), "custom": (43.25, 31.125, 25.625)}


def starting_session(tmp_path, mode, rebalance, ui_mode="Advanced", couple=True):
    gui = make_gui(tmp_path, second_person_enabled=couple, always_use_expense_mode=True, include_realestate=False)
    household = mixed_household()
    gui.husband_portfolio, gui.wife_portfolio = household["husband"], household["wife"]
    gui.mode_var = SimpleNamespace(get=lambda: ui_mode)
    gui.simulation_settings.update(initial_allocation_mode=mode, rebalance_every_year=rebalance,
        custom_stock=43.25, custom_bonds=31.125, custom_cash=25.625)
    # Keep benefit activation ages unchanged when Explorer reapplies controls.
    gui.husband.pension_age = gui.husband.annuity_age = gui.husband.retire_age
    gui.wife.pension_age = gui.wife.annuity_age = gui.wife.retire_age
    state = scenario.ScenarioSessionState()
    manager = scenario.ScenarioStateManager(gui, state)
    manager.build_snapshots_from_truth()
    stocks, bonds, cash = scenario.compute_portfolio_percentages(state.portfolio_snapshots)
    values = SimpleNamespace(husband_ret_age=gui.husband.retire_age, husband_ss_age=gui.husband.ss_age,
        wife_ret_age=gui.wife.retire_age, wife_ss_age=gui.wife.ss_age, inflation=gui.inflation,
        fund_expense=gui.simulation_settings["fund_expense"], stocks=stocks, bonds=bonds, cash=cash,
        dynamic_value=100, calculate_real_dollars=False, enable_annotations=False)
    manager.apply_control_values(values)
    manager.capture_baseline_from_scenario()
    return gui, manager, state, values


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("rebalance", [False, True])
@pytest.mark.parametrize("ui_mode", ["Basic", "Advanced"])
@pytest.mark.parametrize("couple", [False, True])
def test_gui_and_explorer_starting_holdings(tmp_path, monkeypatch, mode, rebalance, ui_mode, couple):
    gui, manager, state, values = starting_session(tmp_path, mode, rebalance, ui_mode, couple)
    truth = copy.deepcopy((vars(gui.husband_portfolio), vars(gui.wife_portfolio)))
    calls = []
    monkeypatch.setattr(gui_run, "run_simulation", lambda **kwargs: calls.append(kwargs))
    gui.run_simulation_from_gui("portfolio_sim")
    assert len(calls) == 1
    regular = calls[0]
    actual = {"husband": regular["husband_portfolio"]}
    if couple:
        actual["wife"] = regular["wife_portfolio"]
    else:
        assert regular["wife_portfolio"] is None
    originals = {"husband": gui._portfolio_for_sim(gui.husband_portfolio)}
    if couple:
        originals["wife"] = gui._portfolio_for_sim(gui.wife_portfolio)
    total = sum(asset_values(originals))
    if mode in TARGETS:
        expected = []
        for percent in TARGETS[mode]:
            expected.append(total * percent / 100)
        assert asset_values(actual) == pytest.approx(expected, rel=1e-14, abs=1e-10)
    for owner, portfolio in actual.items():
        assert vars(portfolio) == vars(state.baseline_portfolio_snapshots[owner])
        for fields in BUCKETS:
            before, after = [], []
            for field in fields:
                before.append(getattr(originals[owner], field))
                after.append(getattr(portfolio, field))
            assert sum(after) == pytest.approx(sum(before), abs=1e-10)
            assert min(after) >= 0
        assert portfolio.real_estate == originals[owner].real_estate
        if mode == "dont-rebalance":
            assert vars(portfolio) == vars(originals[owner])
    captured = []

    def capture(husband_portfolio, wife_portfolio, *args):
        captured.append(copy.deepcopy({"husband": husband_portfolio, "wife": wife_portfolio}))
        return {"marker": [len(captured)]}

    monkeypatch.setattr(scenario, "run_pipeline", capture)
    manager.compute_baseline_results(False, "fill")
    baseline_results = copy.deepcopy(state.baseline_results)
    manager.compute_scenario_results(False, "fill")
    for owner in actual:
        assert vars(captured[0][owner]) == vars(actual[owner])
        assert vars(captured[1][owner]) == vars(actual[owner])
    initial = values.stocks, values.bonds, values.cash
    for _ in range(10):
        values.stocks, values.bonds, values.cash = 60, 25, 15
        manager.apply_control_values(values)
        manager.compute_scenario_results(False, "fill")
        if len(captured) == 3:
            first_changed = copy.deepcopy(captured[-1])
        else:
            for owner in actual:
                assert vars(captured[-1][owner]) == vars(first_changed[owner])
        values.stocks, values.bonds, values.cash = initial
        manager.apply_control_values(values)
        manager.compute_scenario_results(False, "fill")
        for owner in actual:
            assert vars(captured[-1][owner]) == vars(actual[owner])
    assert_tree_equal(public_input_tree(state.baseline_results), public_input_tree(baseline_results))
    assert (vars(gui.husband_portfolio), vars(gui.wife_portfolio)) == truth


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("rebalance", [False, True])
def test_annual_rebalancing_uses_adjusted_account_ratios(tmp_path, monkeypatch, mode, rebalance):
    gui, _, _, _ = starting_session(tmp_path, mode, rebalance)
    calls = []
    monkeypatch.setattr(gui_run, "run_simulation", lambda **kwargs: calls.append(kwargs))
    gui.run_simulation_from_gui("portfolio_sim")
    inputs = calls[0]
    config = inputs["sim_config"]
    portfolio = inputs["husband_portfolio"]
    state = portfolioEngine.create_sim_portfolio(portfolio, config)
    from tests.module_tests.gui.scenario.test_scenario_allocation_redesign import STATE_BUCKETS
    ratios = []
    for sources, fields in zip(BUCKETS, STATE_BUCKETS):
        original = []
        for source, field, growth in zip(sources, fields, (1.2, 0.95, 1.01)):
            amount = getattr(portfolio, source)
            assert getattr(state, field) == amount
            original.append(amount)
            setattr(state, field, amount * growth)
        ratios.append(original)
    if rebalance:
        portfolioEngine.rebalance(state, config)
    for original, fields in zip(ratios, STATE_BUCKETS):
        after = []
        for field in fields:
            after.append(getattr(state, field))
        if rebalance:
            expected = []
            for amount in original:
                expected.append(sum(after) * amount / sum(original))
            assert after == pytest.approx(expected, abs=1e-10)
        else:
            for amount, actual, growth in zip(original, after, (1.2, 0.95, 1.01)):
                assert actual == amount * growth
    assert ratios[0] != ratios[1]


@pytest.mark.parametrize("mode", ["dont-rebalance", "50-30-20", "custom"])
@pytest.mark.parametrize("rebalance", [False, True])
@pytest.mark.parametrize("ui_mode", ["Basic", "Advanced"])
def test_actual_gui_historical_results_match_explorer(tmp_path, monkeypatch, mode, rebalance, ui_mode):
    gui, manager, state, _ = starting_session(tmp_path, mode, rebalance, ui_mode)
    years = np.arange(2000, 2010)
    returns = dict(years=years, eq=np.array([-.4, .2, .1, -.1, .3, .04, -.2, .1, .05, .02]),
        bd=np.linspace(-.03, .05, 10), cs=np.linspace(0, .02, 10), re=np.zeros(10))
    inflation = dict(years=years.copy(), inflation=np.full(10, .025))
    monkeypatch.setattr(monteCarloEngine, "load_historical_asset_returns_csv", lambda filename: returns)
    monkeypatch.setattr(monteCarloEngine, "load_historical_inflation_csv", lambda filename: inflation)
    gui.simulation_controls.update(results_mode="risk_analysis", risk_analysis_mode="historical_windows",
        inflation_mode="nominal", calculate_simulated_shortfall_rate=True)
    normal = []

    def execute(**inputs):
        inputs.pop("root")
        normal.append(run_pipeline(**inputs))

    monkeypatch.setattr(gui_run, "run_simulation", execute)
    gui.run_simulation_from_gui("portfolio_sim")
    assert len(normal) == 1
    manager.compute_baseline_results(False, "historical_risk")
    manager.compute_scenario_results(False, "historical_risk")
    for candidate in (state.baseline_results["p"], state.scenario_results["p"]):
        assert_tree_equal(candidate["core"], normal[0]["core"])
        assert_tree_equal(candidate["portfolio_plot_data"].percentiles, normal[0]["portfolio_plot_data"].percentiles)
        assert candidate["summary_results"]["simulated_shortfall_rate"] == normal[0]["summary_results"]["simulated_shortfall_rate"]
        depleted = np.any(candidate["core"]["total_assets"] <= 0, axis=1)
        expected = np.any(normal[0]["core"]["total_assets"] <= 0, axis=1)
        assert np.count_nonzero(depleted) == np.count_nonzero(expected)

@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("scale", [0.0, 0.000123, 1.0, 1234567.89123])
def test_starting_conversion_pure_accounts_and_unrelated_attributes(mode, scale):
    from tests.architectural_helpers import make_portfolio, make_simulation

    portfolios = {"husband": make_portfolio(equity_pre=100 * scale, bond_post=200 * scale,
        cash_roth=300 * scale, hsa_cash=40 * scale, real_estate=777),
        "wife": make_portfolio(cash_pre=60 * scale, equity_post=70 * scale,
        bond_roth=80 * scale, real_estate=888)}
    portfolios["husband"].note = {"unchanged": [1, 2, 3]}
    before = copy.deepcopy(portfolios)
    config = make_simulation(sim_initial_allocation_mode=mode,
        custom_stock=.4325, custom_bonds=.31125, custom_cash=.25625)
    changed = portfolioEngine.apply_starting_allocation(portfolios, config)
    assert changed is (mode != "dont-rebalance")
    total = sum(asset_values(before))
    if mode in TARGETS:
        expected = []
        for percent in TARGETS[mode]:
            expected.append(total * percent / 100)
        assert asset_values(portfolios) == pytest.approx(expected, rel=1e-14, abs=1e-12)
    for owner, portfolio in portfolios.items():
        old_attributes, new_attributes = vars(before[owner]).copy(), vars(portfolio).copy()
        for fields in BUCKETS:
            old, new = [], []
            for field in fields:
                old.append(old_attributes.pop(field))
                new.append(new_attributes.pop(field))
            assert sum(new) == pytest.approx(sum(old), rel=1e-14, abs=1e-12)
            assert min(new) >= 0
        assert old_attributes == new_attributes
        if mode == "dont-rebalance" or scale == 0:
            assert vars(portfolio) == vars(before[owner])


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("rebalance", [False, True])
def test_financial_core_applies_annual_rebalancing_for_every_starting_mode(tmp_path, monkeypatch, mode, rebalance):
    from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
    from tests.architectural_helpers import make_person, make_simulation
    from tests.module_tests.gui.scenario.test_scenario_allocation_redesign import STATE_BUCKETS

    gui, _, state, _ = starting_session(tmp_path, mode, rebalance)
    portfolios = state.baseline_portfolio_snapshots
    config = make_simulation(second_person_enabled=True, rebalance_every_year=rebalance,
        sim_initial_allocation_mode="original-allocation", eq_mean=.20, bd_mean=-.05, cs_mean=.01)
    created, rebalanced = [], []
    original_create, original_rebalance = portfolioEngine.create_sim_portfolio, portfolioEngine.rebalance

    def capture_create(portfolio, sim_config=None, run_context=None):
        result = original_create(portfolio, sim_config, run_context=run_context)
        created.append(result)
        return result

    def capture_rebalance(portfolio, sim_config, run_context=None):
        totals = []
        for fields in STATE_BUCKETS:
            total = 0.0
            for field in fields:
                total += getattr(portfolio, field)
            totals.append(total)
        result = original_rebalance(portfolio, sim_config, run_context=run_context)
        for bucket, fields, total in zip(("pre", "post", "roth", "hsa"), STATE_BUCKETS, totals):
            for asset, field in zip(("eq", "bd", "cs"), fields):
                ratio = getattr(portfolio, f"{asset}_ratio_{bucket}")
                assert getattr(portfolio, field) == pytest.approx(total * ratio)
        rebalanced.append(portfolio)
        return result

    monkeypatch.setattr(portfolioEngine, "create_sim_portfolio", capture_create)
    monkeypatch.setattr(portfolioEngine, "rebalance", capture_rebalance)
    run_pipeline(portfolios["husband"], portfolios["wife"], make_person(), make_person(), DynamicExpenses(), config)
    assert len(created) == 2
    if rebalance:
        assert len(rebalanced) == 2
    else:
        assert rebalanced == []
        # The mixed pre-tax account must drift under unequal deterministic returns.
        before = portfolios["husband"]
        initial_total = before.equity_pre + before.bond_pre + before.cash_pre
        after = created[0]
        final_total = after.eq_pre + after.bd_pre + after.cs_pre
        assert after.eq_pre / final_total != pytest.approx(before.equity_pre / initial_total)
    # Distinct source accounts retain distinct annual targets.
    assert created[0].eq_ratio_pre != pytest.approx(created[0].eq_ratio_post)
