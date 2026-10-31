"""Path state is isolated while preserving financial initialization dependencies."""

from copy import deepcopy
from dataclasses import fields
import weakref

import numpy as np
import pytest

from src.warpsimlab.sim import run_sim_core
from src.warpsimlab.sim.engines import diagnosticEngine, expenseEngine, incomeEngine, medicareEngine
from src.warpsimlab.sim.engines import monteCarloEngine, rothEngine, taxEngine, withdrawalEngine
from src.warpsimlab.sim.simulation import run_pipeline
from src.warpsimlab.sim.simulationObject import PathContext, RunContext, SimData, SimulationConfig
from tests.architectural_helpers import assert_tree_equal, make_execution_case


def config_case(**overrides):
    case = make_execution_case(**overrides)
    legacy = case["sim_config"]
    case["sim_config"] = SimulationConfig(**{field.name: getattr(legacy, field.name) for field in fields(SimulationConfig)})
    return case


@pytest.mark.parametrize("historical", [False, True])
def test_path_identity_initialization_order_and_nested_cache_isolation(monkeypatch, historical):
    options = dict(results_mode="risk_analysis", years_to_simulate=3)
    loads = []
    if historical:
        years = np.arange(2000, 2006)
        returns = dict(years=years, eq=np.full(6, 0.04), bd=np.full(6, 0.02),
            cs=np.full(6, 0.01), re=np.full(6, 0.03))
        inflation = dict(years=years.copy(), inflation=np.array([0.01, 0.03, -0.01, 0.07, 0.02, 0.04]))

        def load_returns(filename):
            loads.append("returns")
            return returns

        def load_inflation(filename):
            loads.append("inflation")
            return inflation

        monkeypatch.setattr(monteCarloEngine, "load_historical_asset_returns_csv", load_returns)
        monkeypatch.setattr(monteCarloEngine, "load_historical_inflation_csv", load_inflation)
        options.update(risk_analysis_mode="historical_windows", historical_window_start_year=2001,
            historical_window_stop_year=2003, historical_window_stride=2)
    case = config_case(**options)
    config = case["sim_config"]
    before = deepcopy(vars(config))
    wrappers, calls = [], []
    original_wrapper = run_sim_core.SimData

    def wrap(actual_config, run, path):
        data = original_wrapper(actual_config, run, path)
        wrappers.append(data)
        return data

    def observe(module, name, label):
        original = getattr(module, name)

        def initialize(*args, **kwargs):
            path = kwargs["path_context"]
            calls.append((label, path))
            assert_tree_equal(vars(config), before)
            if historical:
                assert path.active_historical_sim_index == len(wrappers) - 1
            else:
                assert path.active_historical_sim_index is None
            if label == "tax":
                assert path.inflation_factors is None
                assert path.tax_year_cache == []
            if label == "medicare":
                assert path.expense_inflation_factors is not None
                assert path.medicare_inflation_factors is None
            if label == "roth":
                assert path.roth_scheduled_flows == []
                assert path.roth_inflation_factor_cache == {}
            return original(*args, **kwargs)

        monkeypatch.setattr(module, name, initialize)

    monkeypatch.setattr(run_sim_core, "SimData", wrap)
    observe(taxEngine, "initialize_tax_engine_for_simulation", "tax")
    observe(incomeEngine, "initialize_income_engine_for_simulation", "income")
    observe(expenseEngine, "initialize_expense_engine_for_simulation", "expense")
    observe(medicareEngine, "initialize_medicare_engine_for_simulation", "medicare")
    observe(rothEngine, "initialize_roth_engine_for_simulation", "roth")
    result, run = run_pipeline(**case, return_run_context=True)
    count = case["sim_config"].num_sims
    if historical:
        count = 2
        assert loads == ["returns", "inflation"]
        np.testing.assert_array_equal(run.hist_window_start_indices, [1, 3])
        np.testing.assert_array_equal(result["core"]["historical_window_start_year"], [2001, 2003])
    assert len(wrappers) == count
    assert len({id(data) for data in wrappers}) == count
    assert len({id(data.path) for data in wrappers}) == count
    assert all(data.config is config and data.run is run for data in wrappers)
    assert [name for name, _ in calls] == ["tax", "income", "expense", "medicare", "roth"] * count
    for data in wrappers:
        path = data.path
        assert path.medicare_inflation_factors == path.expense_inflation_factors
        assert path.medicare_inflation_factors is not path.expense_inflation_factors
        assert len({id(row) for row in path.tax_year_cache}) == config.years_to_simulate + 1
        assert len({id(row) for row in path.roth_scheduled_flows}) == config.years_to_simulate + 1
        for flow_type in rothEngine.ROTH_FLOW_TYPES:
            assert len({id(row[flow_type]) for row in path.roth_scheduled_flows}) == config.years_to_simulate + 1
    first, second = wrappers[0].path, wrappers[1].path
    assert first.income_inflation_factors is not second.income_inflation_factors
    assert first.tax_year_cache is not second.tax_year_cache
    assert first.roth_inflation_factor_cache is not second.roth_inflation_factor_cache
    second_schedule = deepcopy(second.roth_scheduled_flows)
    first.tax_year_cache[1]["test-only"] = {"marker": True}
    first.roth_scheduled_flows[1][rothEngine.ROTH_CONVERSION]["husband"] += 1
    assert "test-only" not in second.tax_year_cache[1]
    assert second.roth_scheduled_flows == second_schedule
    if historical:
        assert first.income_inflation_factors != second.income_inflation_factors
    assert_tree_equal(vars(config), before)


def test_tax_year_cache_keeps_both_filing_statuses_and_reuses_entries():
    config = config_case()["sim_config"]
    run, first, second = RunContext(), PathContext(), PathContext()
    taxEngine.prepare_tax_run_context(config, run)
    for path in (first, second):
        taxEngine.initialize_tax_engine_for_simulation(config, run_context=run, path_context=path)
    joint = taxEngine.prepare_tax_year_cache(1, config, False, run_context=run, path_context=first)
    single = taxEngine.prepare_tax_year_cache(1, config, True, run_context=run, path_context=first)
    assert first.tax_year_cache[1] == {"Other": joint, "Single": single}
    assert joint is not single
    assert joint["ordinary_standard_deduction"] != single["ordinary_standard_deduction"]
    assert taxEngine.prepare_tax_year_cache(1, config, False, run_context=run, path_context=first) is joint
    assert taxEngine.prepare_tax_year_cache(1, config, True, run_context=run, path_context=first) is single
    assert second.tax_year_cache[1] == {}


def test_retirement_base_is_captured_on_first_withdrawal_for_each_path(monkeypatch):
    observations = []
    original = withdrawalEngine.calculate_retirement_withdrawal

    def withdraw(*args, **kwargs):
        path = kwargs["path_context"]
        before = path.ret_withdraw_base_dollars
        initial_portfolio = args[0].total_value + args[1].total_value
        result = original(*args, **kwargs)
        observations.append((path, args[4], before, path.ret_withdraw_base_dollars, initial_portfolio))
        return result

    monkeypatch.setattr(withdrawalEngine, "calculate_retirement_withdrawal", withdraw)
    case = config_case(results_mode="risk_analysis")
    run_pipeline(**case)
    first_calls = [row for row in observations if row[2] is None]
    assert len(first_calls) == case["sim_config"].num_sims
    assert all(year == 2 for _, year, _, _, _ in first_calls)
    for path, _, _, captured, portfolio in first_calls:
        assert captured == portfolio * case["sim_config"].retirement_withdraw_pct / 100.0
        assert path.ret_withdraw_base_dollars == captured
    assert all(before == after for _, _, before, after, _ in observations if before is not None)


def test_completed_core_does_not_retain_path_or_wrapper_objects(monkeypatch):
    paths, wrappers = [], []

    def new_path():
        path = PathContext()
        paths.append(weakref.ref(path))
        return path

    def new_data(config, run, path):
        data = SimData(config, run, path)
        wrappers.append(weakref.ref(data))
        return data

    monkeypatch.setattr(run_sim_core, "PathContext", new_path)
    monkeypatch.setattr(run_sim_core, "SimData", new_data)
    case = config_case(results_mode="risk_analysis")
    run_pipeline(**case)
    run_pipeline(**case)
    assert len(paths) == len(wrappers) == 2 * case["sim_config"].num_sims
    assert all(reference() is None for reference in paths + wrappers)


def test_failed_path_preparation_cannot_contaminate_a_later_execution(monkeypatch):
    case = config_case(results_mode="risk_analysis")
    expected = run_pipeline(**case)["core"]
    before = deepcopy(vars(case["sim_config"]))
    paths = []
    original = rothEngine.initialize_roth_engine_for_simulation

    def initialize(config, husband, wife, run_context=None, path_context=None):
        paths.append(path_context)
        result = original(config, husband, wife, run_context=run_context, path_context=path_context)
        if len(paths) == 2:
            path_context.roth_scheduled_flows[1][rothEngine.ROTH_CONVERSION]["total"] = 999999
            raise RuntimeError("failed path preparation")
        return result

    monkeypatch.setattr(rothEngine, "initialize_roth_engine_for_simulation", initialize)
    with pytest.raises(RuntimeError, match="failed path preparation"):
        run_pipeline(**case)
    contaminated = paths[-1]
    recovered = run_pipeline(**case)["core"]
    assert_tree_equal(recovered, expected)
    assert_tree_equal(vars(case["sim_config"]), before)
    assert all(path is not contaminated for path in paths[2:])


def test_path_diagnostics_keep_selection_and_exclude_financial_caches(diagnostic_home):
    path = PathContext(active_historical_sim_index=2, ret_withdraw_base_dollars=123.0,
        tax_year_cache=[{"secret": 1}], roth_scheduled_flows=[{"secret": 2}])
    filename = diagnosticEngine._write_diagnostic_report("test", None, {}, [], path_context=path)
    assert filename is not None
    report = filename.read_text(encoding="utf-8")
    assert "Path Context" in report
    assert "active_historical_sim_index: 2" in report
    assert "ret_withdraw_base_dollars: 123.0" in report
    assert "tax_year_cache:" not in report
    assert "roth_scheduled_flows:" not in report
