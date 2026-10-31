"""Sprint 1 configuration ownership and construction contracts."""

from dataclasses import MISSING, fields, replace
import inspect

import numpy as np
import pytest

from src.warpsimlab.sim.simulationObject import PathContext, RunContext, SimData, SimulationConfig
from src.warpsimlab.sim.validation import SimulationValidationError, validate_simulation_inputs
from tests.architectural_helpers import assert_tree_equal
from tests.feature_tests.workflow_helpers import inputs_from_gui, make_gui


def test_schema_and_required_inputs_match_approved_design(scenario_builders):
    initial = scenario_builders.make_config()
    required = {name for name, p in inspect.signature(SimulationConfig).parameters.items() if p.default is p.empty}
    declared = {f.name for f in fields(SimulationConfig) if f.default is MISSING and f.default_factory is MISSING}
    assert required == {
        "start_year", "years_to_simulate", "inflation_rate", "num_sims", "fund_expense", "use_fund_expenses",
        "inflation_mode", "results_mode", "include_rmd", "calculate_income_taxes", "calculate_payroll_taxes",
        "tax_filing_status", "calculate_state_taxes", "state_of_residence", "second_person_enabled",
        "eq_mean", "bd_mean", "cs_mean", "eq_std", "bd_std", "cs_std"}
    assert declared == required
    assert len(fields(SimulationConfig)) == 76
    assert len(fields(RunContext)) == 25
    assert len(fields(PathContext)) == 11
    assert [f.name for f in fields(SimData)] == ["config", "run", "path"]
    inputs = {name: getattr(initial, name) for name in required}
    config = SimulationConfig(**inputs)
    assert set(vars(config)) == {field.name for field in fields(SimulationConfig)}
    assert config.sim_initial_allocation_mode == "none"
    assert config.re_mean == 3.0
    assert config.re_std == 5.0
    assert config.post_tax_equity_dividend_yield == 0.015
    assert config.post_tax_bond_interest_yield == max(0.0, config.bd_mean)
    assert config.post_tax_cash_interest_yield == config.cs_mean
    assert config.historical_window_stride == 1
    assert config.risk_analysis_mode == "monte_carlo"
    assert config.return_asset_order == ("eq", "bd", "cs", "re")
    assert all(p.kind is p.KEYWORD_ONLY for p in inspect.signature(SimulationConfig).parameters.values())
    assert not {"root", "husband_portfolio", "wife_portfolio"} & vars(config).keys()
    assert not any(name.startswith("_") for name in vars(config))
    with pytest.raises(TypeError):
        SimulationConfig()
    with pytest.raises(TypeError):
        SimulationConfig(*inputs.values())


@pytest.mark.parametrize("show,calculate,expected", [(False, None, False), (True, None, True), (False, True, True), (True, False, False)])
def test_shortfall_controls_are_independent(scenario_builders, show, calculate, expected):
    initial = scenario_builders.make_config()
    required = {name: getattr(initial, name) for name, p in inspect.signature(SimulationConfig).parameters.items() if p.default is p.empty}
    config = SimulationConfig(**required, show_simulated_shortfall_rate=show, calculate_simulated_shortfall_rate=calculate)
    assert config.show_simulated_shortfall_rate is show
    assert config.calculate_simulated_shortfall_rate is expected
    snapshot = replace(config, show_simulated_shortfall_rate=not show)
    assert snapshot.calculate_simulated_shortfall_rate is expected


@pytest.mark.parametrize("name", ["historical_magi", "special_income_streams", "roth_flows", "report_options",
    "user_annotation_strings", "scenario_explorer_annotations"])
def test_nested_inputs_and_replacements_are_independent(tmp_path, name):
    config = make_gui(tmp_path).build_simulation_from_gui("portfolio_sim")
    payload = [{"nested": [1]}]
    if name in {"historical_magi", "report_options"}:
        payload = {"nested": [1]}
    first = replace(config, **{name: payload})
    second = replace(first)
    assert_tree_equal(getattr(first, name), payload)
    assert_tree_equal(getattr(second, name), payload)
    nested = payload
    if isinstance(payload, list):
        nested = payload[0]
    nested["nested"].append(2)
    first_nested = getattr(first, name)
    second_nested = getattr(second, name)
    if isinstance(first_nested, list):
        first_nested = first_nested[0]
        second_nested = second_nested[0]
    assert first_nested["nested"] == [1]
    first_nested["nested"].append(3)
    assert second_nested["nested"] == [1]


def test_matrix_copy_and_resolved_yields_survive_replacement(tmp_path):
    config = make_gui(tmp_path).build_simulation_from_gui("portfolio_sim")
    matrix = config.return_correlation_matrix.copy()
    first = replace(config, return_correlation_matrix=matrix, bd_mean=-0.02, post_tax_bond_interest_yield=None)
    second = replace(first, bd_mean=0.08, cs_mean=0.05)
    assert first.post_tax_bond_interest_yield == 0.0
    assert second.post_tax_bond_interest_yield == 0.0
    assert second.post_tax_cash_interest_yield == first.post_tax_cash_interest_yield
    assert first.post_tax_equity_dividend_yield == 0.015
    matrix[0, 0] = 9
    assert first.return_correlation_matrix[0, 0] == 1
    first.return_correlation_matrix[0, 0] = 8
    assert second.return_correlation_matrix[0, 0] == 1
    assert not np.shares_memory(first.return_correlation_matrix, second.return_correlation_matrix)


def test_path_cache_defaults_are_independent_and_wrapper_keeps_references(tmp_path):
    config = make_gui(tmp_path).build_simulation_from_gui("portfolio_sim")
    first, second = PathContext(), PathContext()
    first.tax_year_cache.append({"Single": {"value": 1}})
    first.roth_scheduled_flows.append({"conversion": 2})
    first.roth_inflation_factor_cache["factor"] = [1.0]
    assert second.tax_year_cache == []
    assert second.roth_scheduled_flows == []
    assert second.roth_inflation_factor_cache == {}
    run = RunContext()
    data = SimData(config, run, first)
    assert data.config is config
    assert data.run is run
    assert data.path is first
    assert run.hist_num_windows == 0
    assert all(getattr(run, f.name) is None for f in fields(run) if f.name != "hist_num_windows")


def test_config_defaults_are_independent(scenario_builders):
    initial = scenario_builders.make_config()
    required = {name: getattr(initial, name) for name, p in inspect.signature(SimulationConfig).parameters.items() if p.default is p.empty}
    first, second = SimulationConfig(**required), SimulationConfig(**required)
    first.historical_magi["one_year_prior"] = 12
    first.special_income_streams.append({"amount": 1})
    first.roth_flows.append({"amount": 2})
    first.report_options["output"] = {}
    first.user_annotation_strings.append("user")
    first.scenario_explorer_annotations.append("scenario")
    first.return_correlation_matrix[0, 0] = 8
    assert second.historical_magi == {"two_years_prior": None, "one_year_prior": None}
    assert second.special_income_streams == []
    assert second.roth_flows == []
    assert second.report_options == {}
    assert second.user_annotation_strings == []
    assert second.scenario_explorer_annotations == []
    assert second.return_correlation_matrix[0, 0] == 1


def test_gui_assembly_does_not_require_presentation_or_portfolios(tmp_path):
    gui = make_gui(tmp_path)
    del gui.root
    del gui.husband_portfolio
    del gui.wife_portfolio
    config = gui.build_simulation_from_gui("portfolio_sim")
    assert isinstance(config, SimulationConfig)


def test_gui_config_snapshots_match_and_detach_inputs(tmp_path):
    gui = make_gui(tmp_path)
    initial = gui.build_simulation_from_gui("portfolio_sim")
    config = gui.build_simulation_from_gui("portfolio_sim")
    assert isinstance(initial, SimulationConfig)
    assert isinstance(config, SimulationConfig)
    for field in fields(SimulationConfig):
        assert_tree_equal(getattr(config, field.name), getattr(initial, field.name))
    assert not {"root", "husband_portfolio", "wife_portfolio"} & vars(config).keys()
    gui.special_income_streams[0]["amount"] += 123
    assert config.special_income_streams[0]["amount"] != gui.special_income_streams[0]["amount"]


@pytest.mark.parametrize("override", [{}, {"num_sims": 0}, {"eq_std": -1}, {"calculate_income_taxes": "yes"},
    {"historical_window_stride": 0}, {"historical_magi": {"wrong": 1}}, {"special_income_streams": [{}]},
    {"roth_flows": [{}]}, {"sim_initial_allocation_mode": "custom", "custom_stock": 0.9, "custom_cash": 0.9}])
def test_validation_results_match_independent_snapshots(tmp_path, override):
    gui = make_gui(tmp_path)
    case = inputs_from_gui(gui)
    initial = case["sim_config"]
    config = gui.build_simulation_from_gui("portfolio_sim")
    errors = []
    for candidate in (initial, config):
        for name, value in override.items():
            setattr(candidate, name, value)
        case["sim_config"] = candidate
        try:
            validate_simulation_inputs(**case)
        except SimulationValidationError as exc:
            errors.append(str(exc))
        else:
            errors.append(None)
    assert errors[0] == errors[1]
    if override:
        assert errors[0] is not None
    else:
        assert errors[0] is None
