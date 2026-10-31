"""Configuration stays unchanged during primary, secondary and report execution."""

from copy import deepcopy
import importlib

import numpy as np
import pytest

from src.warpsimlab.sim import simulation
from src.warpsimlab.sim.simulationObject import SimulationConfig
from tests.architectural_helpers import assert_tree_equal, make_execution_case
from tests.feature_tests.test_report_workflows import report_home
from tests.feature_tests.workflow_helpers import inputs_from_gui, make_gui


def mutable_ids(value):
    result = set()
    if isinstance(value, (dict, list, np.ndarray)):
        result.add(id(value))
    if isinstance(value, dict):
        for item in value.values():
            result.update(mutable_ids(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            result.update(mutable_ids(item))
    return result


@pytest.mark.parametrize("report_type", ["summary_report", "year_by_year_report", "tax_report",
    "monte_carlo_risk_report", "historical_window_risk_report", "asset_allocation_comparison_report",
    "spending_comparison_report", "retirement_ss_comparison_report"])
def test_complete_reports_never_mutate_origin_or_prior_execution_snapshots(report_home, monkeypatch, report_type):
    gui = make_gui(report_home)
    case = inputs_from_gui(gui, report_type)
    origin = case["sim_config"]
    origin_before = deepcopy(vars(origin))
    origin_mutables = mutable_ids(vars(origin))
    executions = []
    original_pipeline = simulation.run_pipeline
    original_core = simulation.simulate_yearly_portfolios

    def check_prior():
        assert_tree_equal(vars(origin), origin_before)
        for config, before in executions:
            assert_tree_equal(vars(config), before)

    def pipeline(*args, **kwargs):
        config = kwargs.get("sim_config")
        if config is None:
            config = args[5]
        check_prior()
        assert isinstance(config, SimulationConfig)
        assert config is not origin
        assert not origin_mutables & mutable_ids(vars(config))
        executions.append((config, deepcopy(vars(config))))
        result = original_pipeline(*args, **kwargs)
        check_prior()
        return result

    def core(*args, **kwargs):
        check_prior()
        result = original_core(*args, **kwargs)
        check_prior()
        return result

    monkeypatch.setattr(simulation, "simulate_yearly_portfolios", core)
    monkeypatch.setattr(simulation, "run_pipeline", pipeline)
    for name in ["summary_report", "year_by_year_report", "tax_report", "risk_reports",
        "asset_allocation_comparison_report", "spending_comparison_report", "retirement_ss_comparison_report"]:
        module = importlib.import_module(f"src.warpsimlab.sim.run_sim_{name}")
        if hasattr(module, "run_pipeline"):
            monkeypatch.setattr(module, "run_pipeline", pipeline)
    result = simulation.run_simulation(**case)
    assert result.success, result.errors
    assert executions
    check_prior()


@pytest.mark.parametrize("fail_secondary", [False, True])
def test_pipeline_secondary_snapshots_are_detached_even_during_failures(monkeypatch, fail_secondary):
    case = make_execution_case(results_mode="fill", overlay_tax_impacts=True,
        overlay_fund_expense_impacts=True, show_simulated_shortfall_rate=True,
        calculate_simulated_shortfall_rate=True)
    origin = case["sim_config"]
    before = deepcopy(vars(origin))
    original = simulation.simulate_yearly_portfolios
    executions = []

    def execute(*args, **kwargs):
        config = kwargs.get("sim_config")
        if config is None:
            config = args[5]
        assert_tree_equal(vars(origin), before)
        for prior, snapshot in executions:
            assert_tree_equal(vars(prior), snapshot)
        if executions:
            assert config is not origin
            assert not mutable_ids(vars(origin)) & mutable_ids(vars(config))
        executions.append((config, deepcopy(vars(config))))
        if fail_secondary and len(executions) == 2:
            raise RuntimeError("secondary execution failed")
        return original(*args, **kwargs)

    monkeypatch.setattr(simulation, "simulate_yearly_portfolios", execute)
    if fail_secondary:
        with pytest.raises(RuntimeError, match="secondary execution failed"):
            simulation.run_pipeline(**case)
    else:
        result = simulation.run_pipeline(**case)
        assert result["portfolio_plot_data"].simulated_shortfall_rate is not None
        assert len(executions) == 5
    assert_tree_equal(vars(origin), before)
    for config, snapshot in executions:
        assert_tree_equal(vars(config), snapshot)


def test_gui_passes_root_explicitly_and_snapshots_do_not_share_gui_truth(tmp_path, monkeypatch):
    from src.warpsimlab.gui import gui_run

    gui = make_gui(tmp_path)
    captured = {}
    monkeypatch.setattr(gui_run, "run_simulation", lambda **kwargs: captured.update(kwargs))
    gui.run_simulation_from_gui("summary_sim")
    assert captured["root"] is gui.root
    config = captured["sim_config"]
    assert isinstance(config, SimulationConfig)
    assert not {"root", "husband_portfolio", "wife_portfolio"} & vars(config).keys()
    gui.special_income_streams[0]["amount"] += 1
    assert config.special_income_streams[0]["amount"] != gui.special_income_streams[0]["amount"]


@pytest.mark.parametrize("report_type,module_name", [
    ("summary_report", "summary_report"), ("year_by_year_report", "year_by_year_report"),
    ("tax_report", "tax_report"), ("monte_carlo_risk_report", "risk_reports"),
    ("historical_window_risk_report", "risk_reports"),
    ("asset_allocation_comparison_report", "asset_allocation_comparison_report"),
    ("spending_comparison_report", "spending_comparison_report"),
    ("retirement_ss_comparison_report", "retirement_ss_comparison_report")])
def test_report_failure_preserves_origin_during_the_failing_call(tmp_path, monkeypatch, report_type, module_name):
    gui = make_gui(tmp_path)
    case = inputs_from_gui(gui, report_type)
    origin = case["sim_config"]
    before = deepcopy(vars(origin))

    def fail(*args, **kwargs):
        assert_tree_equal(vars(origin), before)
        assert args[5] is not origin
        assert not mutable_ids(vars(origin)) & mutable_ids(vars(args[5]))
        raise RuntimeError("report pipeline failed")

    module = importlib.import_module(f"src.warpsimlab.sim.run_sim_{module_name}")
    monkeypatch.setattr(simulation, "run_pipeline", fail)
    if hasattr(module, "run_pipeline"):
        monkeypatch.setattr(module, "run_pipeline", fail)
    with pytest.raises(RuntimeError, match="report pipeline failed"):
        simulation.run_simulation(**case)
    assert_tree_equal(vars(origin), before)


@pytest.mark.parametrize("mode,module_name,presentation", [
    ("income_sim", "income", "plot_yearly_income"),
    ("operating_balance_sim", "operating_balance", "plot_operating_balance"),
    ("portfolio_sim", "portfolio", "plot_portfolio_projection"),
    ("summary_sim", "summary", "SummaryDialog")])
def test_explicit_root_reaches_the_presentation_boundary(monkeypatch, mode, module_name, presentation):
    module = importlib.import_module(f"src.warpsimlab.sim.run_sim_{module_name}")
    roots = []
    monkeypatch.setattr(module, presentation, lambda *args, **kwargs: roots.append(kwargs["root"]))
    root = object()
    case = make_execution_case(sim_type=mode)
    before = deepcopy(vars(case["sim_config"]))
    simulation.run_simulation(**case, root=root)
    assert roots == [root]
    assert_tree_equal(vars(case["sim_config"]), before)
