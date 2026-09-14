from types import SimpleNamespace

import pytest

from src.warpsimlab.gui.scenario import gui_scenarioState as mod


def _make_person(age=60, retire_age=67, ss_age=67, ss=2000.0, pension=500.0, annuity=250.0):
    return SimpleNamespace(
        age=age, retire_age=retire_age, ss_age=ss_age, ss=ss, pension=pension, annuity=annuity,
        pension_age=retire_age, annuity_age=retire_age
    )


def _make_portfolio(equity_pre=0.0, equity_post=0.0, bond_pre=0.0, bond_post=0.0, cash_pre=0.0, cash_post=0.0):
    return SimpleNamespace(
        equity_pre=equity_pre, equity_post=equity_post, bond_pre=bond_pre, bond_post=bond_post,
        cash_pre=cash_pre, cash_post=cash_post
    )


def _make_main_gui(second_person_enabled=False, expense_mode=True):
    gui = SimpleNamespace(
        simulation_controls={
            "second_person_enabled": second_person_enabled,
            "always_use_expense_mode": expense_mode,
            "retirement_withdraw_pct": 4.0,
        },
        simulation_settings={"fund_expense": 0.55},
        husband=_make_person(age=60, retire_age=65, ss_age=67),
        wife=_make_person(age=58, retire_age=63, ss_age=66),
        husband_portfolio=_make_portfolio(equity_pre=60, bond_pre=30, cash_pre=10),
        wife_portfolio=_make_portfolio(equity_pre=30, bond_pre=15, cash_pre=5),
        inflation=3.25,
        expensesDict={"expense": 1234},
    )
    return gui


def _make_manager(second_person_enabled=False, expense_mode=True):
    main_gui = _make_main_gui(second_person_enabled=second_person_enabled, expense_mode=expense_mode)
    session_state = mod.ScenarioSessionState()
    manager = mod.ScenarioStateManager(main_gui, session_state)
    return manager, main_gui, session_state


def _make_control_values(**overrides):
    values = {
        "husband_ret_age": 66,
        "husband_ss_age": 68,
        "wife_ret_age": None,
        "wife_ss_age": None,
        "inflation": 4.0,
        "fund_expense": 0.75,
        "market_adjustment": 90.0,
        "stocks": 65.0,
        "bonds": 25.0,
        "cash": 10.0,
        "dynamic_value": 125.0,
        "calculate_real_dollars": True,
        "enable_annotations": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _make_summary(total_assets=100000, depletion_rate=5.0, net_cash_flow=1000, funding_gap=None, taxes=None,
                  pre_tax=40000, post_tax=30000, roth=20000, hsa=10000):
    if funding_gap is None:
        funding_gap = [100, 200]
    if taxes is None:
        taxes = [1000, 2000]

    return {
        "total_assets": [90000, total_assets],
        "simulated_shortfall_rate": depletion_rate,
        "net_cash_flow": [500, net_cash_flow],
        "funding_gap": funding_gap,
        "taxes": taxes,
        "pre_tax_assets": [35000, pre_tax],
        "post_tax_assets": [25000, post_tax],
        "roth_assets": [15000, roth],
        "hsa_assets": [5000, hsa],
    }


def _make_result(summary=None, wife=None, expense_mode=True, dynamic_value=1.25):
    if summary is None:
        summary = _make_summary()

    if expense_mode:
        scenario_expense_multiplier = dynamic_value
        retirement_withdraw_pct = 4.0
    else:
        scenario_expense_multiplier = 1.0
        retirement_withdraw_pct = dynamic_value

    return {
        "p": {"summary_results": summary},
        "sim_config": SimpleNamespace(
            always_use_expense_mode=expense_mode, scenario_expense_multiplier=scenario_expense_multiplier,
            retirement_withdraw_pct=retirement_withdraw_pct, inflation_rate=0.03, fund_expense=0.005,
            custom_stock=0.60, custom_bonds=0.30, custom_cash=0.10
        ),
        "retirement_snapshots": SimpleNamespace(historical_data_multiplier=95.0),
        "husband": _make_person(age=60, retire_age=65, ss_age=67),
        "wife": wife,
    }


def test_compute_portfolio_percentages_single_person():
    portfolio = {
        "husband": _make_portfolio(equity_pre=40, equity_post=20, bond_pre=20, bond_post=10, cash_pre=5, cash_post=5)
    }

    stocks, bonds, cash = mod.compute_portfolio_percentages(portfolio)

    assert stocks == 60
    assert bonds == 30
    assert cash == 10


def test_compute_portfolio_percentages_combines_both_people():
    portfolio = {
        "husband": _make_portfolio(equity_pre=40, bond_pre=20, cash_pre=10),
        "wife": _make_portfolio(equity_pre=20, bond_pre=5, cash_pre=5),
    }

    stocks, bonds, cash = mod.compute_portfolio_percentages(portfolio)

    assert stocks == 60
    assert bonds == 25
    assert cash == 15


def test_compute_portfolio_percentages_zero_total_defaults_to_cash():
    portfolio = {"husband": _make_portfolio()}

    stocks, bonds, cash = mod.compute_portfolio_percentages(portfolio)

    assert stocks == 0
    assert bonds == 0
    assert cash == 100


def test_session_state_starts_empty():
    state = mod.ScenarioSessionState()

    assert state.baseline_person_snapshots is None
    assert state.baseline_portfolio_snapshots is None
    assert state.baseline_retirement_snapshots is None
    assert state.person_snapshots is None
    assert state.portfolio_snapshots is None
    assert state.retirement_snapshots is None
    assert state.baseline_results is None
    assert state.scenario_results is None


def test_build_snapshots_from_truth_single_person_creates_independent_state():
    manager, main_gui, state = _make_manager(second_person_enabled=False)

    manager.build_snapshots_from_truth()

    assert set(state.baseline_person_snapshots) == {"husband"}
    assert set(state.baseline_portfolio_snapshots) == {"husband"}
    assert set(state.person_snapshots) == {"husband"}
    assert set(state.portfolio_snapshots) == {"husband"}

    assert state.baseline_person_snapshots["husband"] is not main_gui.husband
    assert state.person_snapshots["husband"] is not state.baseline_person_snapshots["husband"]
    assert state.baseline_portfolio_snapshots["husband"] is not main_gui.husband_portfolio
    assert state.portfolio_snapshots["husband"] is not state.baseline_portfolio_snapshots["husband"]

    assert state.baseline_retirement_snapshots.fund_expense == 0.55
    assert state.baseline_retirement_snapshots.historical_data_multiplier == 100.0
    assert state.retirement_snapshots is not state.baseline_retirement_snapshots


def test_build_snapshots_from_truth_second_person_includes_wife():
    manager, main_gui, state = _make_manager(second_person_enabled=True)

    manager.build_snapshots_from_truth()

    assert set(state.baseline_person_snapshots) == {"husband", "wife"}
    assert set(state.baseline_portfolio_snapshots) == {"husband", "wife"}
    assert set(state.person_snapshots) == {"husband", "wife"}
    assert set(state.portfolio_snapshots) == {"husband", "wife"}
    assert state.person_snapshots["wife"] is not main_gui.wife
    assert state.portfolio_snapshots["wife"] is not main_gui.wife_portfolio


def test_capture_baseline_from_scenario_creates_independent_copies():
    manager, _, state = _make_manager()
    manager.build_snapshots_from_truth()

    state.person_snapshots["husband"].retire_age = 70
    state.portfolio_snapshots["husband"].equity_pre = 123
    state.retirement_snapshots.fund_expense = 1.25

    manager.capture_baseline_from_scenario()

    assert state.baseline_person_snapshots["husband"].retire_age == 70
    assert state.baseline_portfolio_snapshots["husband"].equity_pre == 123
    assert state.baseline_retirement_snapshots.fund_expense == 1.25

    assert state.baseline_person_snapshots is not state.person_snapshots
    assert state.baseline_portfolio_snapshots is not state.portfolio_snapshots
    assert state.baseline_retirement_snapshots is not state.retirement_snapshots


def test_apply_control_values_updates_scenario_state_expense_mode(monkeypatch):
    manager, main_gui, state = _make_manager(expense_mode=True)
    manager.build_snapshots_from_truth()
    manager.capture_baseline_from_scenario()

    annotation_args = {}

    def fake_annotations(**kwargs):
        annotation_args.update(kwargs)
        return [["annotation"]]

    monkeypatch.setattr(mod, "build_scenario_explorer_annotations", fake_annotations)

    values = _make_control_values(husband_ret_age=66, husband_ss_age=68, dynamic_value=125.0)
    manager.apply_control_values(values)

    retirement = state.retirement_snapshots
    husband = state.person_snapshots["husband"]

    assert retirement.calculate_real_dollars is True
    assert retirement.delta_inflation == pytest.approx(0.75)
    assert retirement.fund_expense == pytest.approx(0.75)
    assert retirement.historical_data_multiplier == pytest.approx(90.0)
    assert retirement.custom_stock_percent == pytest.approx(65.0)
    assert retirement.custom_bonds_percent == pytest.approx(25.0)
    assert retirement.custom_cash_percent == pytest.approx(10.0)
    assert retirement.scenario_expense_multiplier == pytest.approx(1.25)
    assert retirement.use_snapshot_annotations is True
    assert retirement.annotation_strings == [["annotation"]]

    assert husband.retire_age == 66
    assert husband.ss_age == 68
    assert husband.ss == pytest.approx(2160.0)
    assert husband.pension == main_gui.husband.pension
    assert husband.annuity == main_gui.husband.annuity
    assert husband.pension_age == 66
    assert husband.annuity_age == 66

    assert annotation_args["baseline_stocks"] == 60
    assert annotation_args["baseline_bonds"] == 30
    assert annotation_args["baseline_cash"] == 10
    assert annotation_args["stocks"] == 65.0
    assert annotation_args["bonds"] == 25.0
    assert annotation_args["cash"] == 10.0


def test_apply_control_values_updates_withdrawal_mode(monkeypatch):
    manager, _, state = _make_manager(expense_mode=False)
    manager.build_snapshots_from_truth()
    manager.capture_baseline_from_scenario()

    monkeypatch.setattr(mod, "build_scenario_explorer_annotations", lambda **kwargs: [])

    values = _make_control_values(dynamic_value=5.5)
    manager.apply_control_values(values)

    assert state.retirement_snapshots.scenario_withdraw_pct == pytest.approx(5.5)


def test_apply_control_values_updates_wife_when_enabled(monkeypatch):
    manager, _, state = _make_manager(second_person_enabled=True)
    manager.build_snapshots_from_truth()
    manager.capture_baseline_from_scenario()

    monkeypatch.setattr(mod, "build_scenario_explorer_annotations", lambda **kwargs: [])

    values = _make_control_values(wife_ret_age=64, wife_ss_age=67)
    manager.apply_control_values(values)

    wife = state.person_snapshots["wife"]

    assert wife.retire_age == 64
    assert wife.ss_age == 67
    assert wife.pension_age == 64
    assert wife.annuity_age == 64


def test_clone_result_inputs_returns_deep_copies():
    manager, _, _ = _make_manager()

    persons = {"husband": _make_person()}
    portfolios = {"husband": _make_portfolio(equity_pre=100)}
    retirement = SimpleNamespace(fund_expense=0.5)

    persons_copy, portfolios_copy, retirement_copy = manager.clone_result_inputs(persons, portfolios, retirement)

    assert persons_copy is not persons
    assert persons_copy["husband"] is not persons["husband"]
    assert portfolios_copy is not portfolios
    assert portfolios_copy["husband"] is not portfolios["husband"]
    assert retirement_copy is not retirement

    assert persons_copy["husband"].retire_age == persons["husband"].retire_age
    assert portfolios_copy["husband"].equity_pre == 100
    assert retirement_copy.fund_expense == 0.5


def test_compute_results_from_inputs_uses_copies_and_explicit_options(monkeypatch):
    manager, main_gui, _ = _make_manager(second_person_enabled=False)

    persons = {"husband": _make_person()}
    portfolios = {"husband": _make_portfolio(equity_pre=100)}
    retirement = SimpleNamespace(fund_expense=0.5)
    sim_config = SimpleNamespace(second_person_enabled=False)
    pipeline_args = {}

    def build_simulation_from_gui(**kwargs):
        assert kwargs["sim_type"] == "portfolio_sim"
        assert kwargs["use_snapshots"] is True
        assert kwargs["retirement_snapshots"] is not retirement
        return sim_config

    def fake_run_pipeline(husband_portfolio, wife_portfolio, husband, wife, expenses_dict, received_sim_config):
        pipeline_args["husband_portfolio"] = husband_portfolio
        pipeline_args["wife_portfolio"] = wife_portfolio
        pipeline_args["husband"] = husband
        pipeline_args["wife"] = wife
        pipeline_args["expenses_dict"] = expenses_dict
        pipeline_args["sim_config"] = received_sim_config
        return {"result": 42}

    main_gui.build_simulation_from_gui = build_simulation_from_gui
    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline)

    result = manager.compute_results_from_inputs(persons, portfolios, retirement, True, "fill")

    assert result["p"] == {"result": 42}
    assert result["husband"] is not persons["husband"]
    assert result["wife"] is None
    assert result["retirement_snapshots"] is not retirement

    assert sim_config.results_mode == "fill"
    assert sim_config.include_realestate is True

    assert pipeline_args["husband_portfolio"] is not portfolios["husband"]
    assert pipeline_args["wife_portfolio"] is None
    assert pipeline_args["husband"] is result["husband"]
    assert pipeline_args["wife"] is None
    assert pipeline_args["expenses_dict"] is main_gui.expensesDict
    assert pipeline_args["sim_config"] is sim_config


def test_compute_results_from_inputs_configures_historical_risk(monkeypatch):
    manager, main_gui, _ = _make_manager()
    main_gui.build_simulation_from_gui = lambda **kwargs: SimpleNamespace(second_person_enabled=False)
    monkeypatch.setattr(mod, "run_pipeline", lambda *args: {"result": 42})

    persons = {"husband": _make_person()}
    portfolios = {"husband": _make_portfolio(equity_pre=100)}
    retirement = SimpleNamespace()

    result = manager.compute_results_from_inputs(persons, portfolios, retirement, False, "historical_risk")
    sim_config = result["sim_config"]

    assert sim_config.results_mode == "risk_analysis"
    assert sim_config.risk_analysis_mode == "historical_windows"
    assert sim_config.risk_analysis_plot_style == "fill"
    assert sim_config.include_realestate is False


def test_compute_results_from_inputs_passes_wife_when_enabled(monkeypatch):
    manager, main_gui, _ = _make_manager(second_person_enabled=True)
    main_gui.build_simulation_from_gui = lambda **kwargs: SimpleNamespace(second_person_enabled=True)

    pipeline_args = {}

    def fake_run_pipeline(husband_portfolio, wife_portfolio, husband, wife, expenses_dict, sim_config):
        pipeline_args["wife"] = wife
        pipeline_args["wife_portfolio"] = wife_portfolio
        return {"result": 42}

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline)

    persons = {"husband": _make_person(), "wife": _make_person(age=58)}
    portfolios = {
        "husband": _make_portfolio(equity_pre=100),
        "wife": _make_portfolio(equity_pre=50),
    }

    result = manager.compute_results_from_inputs(persons, portfolios, SimpleNamespace(), False, "fill")

    assert result["wife"] is not None
    assert result["wife"] is not persons["wife"]
    assert pipeline_args["wife"] is result["wife"]
    assert pipeline_args["wife_portfolio"] is not portfolios["wife"]


def test_compute_baseline_results_uses_baseline_state(monkeypatch):
    manager, _, state = _make_manager()
    manager.build_snapshots_from_truth()

    received = {}

    def fake_compute(persons, portfolios, retirement, include_realestate, plot_style):
        received["persons"] = persons
        received["portfolios"] = portfolios
        received["retirement"] = retirement
        received["include_realestate"] = include_realestate
        received["plot_style"] = plot_style
        return {"baseline": True}

    monkeypatch.setattr(manager, "compute_results_from_inputs", fake_compute)

    manager.compute_baseline_results(True, "sub_categories")

    assert state.baseline_results == {"baseline": True}
    assert received["persons"] is state.baseline_person_snapshots
    assert received["portfolios"] is state.baseline_portfolio_snapshots
    assert received["retirement"] is state.baseline_retirement_snapshots
    assert received["include_realestate"] is True
    assert received["plot_style"] == "sub_categories"


def test_compute_scenario_results_uses_current_state_and_returns_result(monkeypatch):
    manager, _, state = _make_manager()
    manager.build_snapshots_from_truth()

    received = {}

    def fake_compute(persons, portfolios, retirement, include_realestate, plot_style):
        received["persons"] = persons
        received["portfolios"] = portfolios
        received["retirement"] = retirement
        received["include_realestate"] = include_realestate
        received["plot_style"] = plot_style
        return {"scenario": True}

    monkeypatch.setattr(manager, "compute_results_from_inputs", fake_compute)

    result = manager.compute_scenario_results(False, "pre_post_tax")

    assert result == {"scenario": True}
    assert state.scenario_results is result
    assert received["persons"] is state.person_snapshots
    assert received["portfolios"] is state.portfolio_snapshots
    assert received["retirement"] is state.retirement_snapshots
    assert received["include_realestate"] is False
    assert received["plot_style"] == "pre_post_tax"


def test_build_results_view_model_returns_none_until_both_results_exist():
    manager, _, state = _make_manager()

    assert manager.build_results_view_model() is None

    state.baseline_results = _make_result()

    assert manager.build_results_view_model() is None


def test_build_results_view_model_extracts_metrics_and_assumptions():
    manager, _, state = _make_manager()

    state.baseline_results = _make_result(
        summary=_make_summary(total_assets=100000, depletion_rate=5.0, net_cash_flow=1000, funding_gap=[100, 200],
                              taxes=[1000, 2000], pre_tax=40000, post_tax=30000, roth=20000, hsa=10000),
        expense_mode=True, dynamic_value=1.0
    )
    state.scenario_results = _make_result(
        summary=_make_summary(total_assets=200000, depletion_rate=2.0, net_cash_flow=3000, funding_gap=[10, 20],
                              taxes=[2000, 3000], pre_tax=80000, post_tax=60000, roth=40000, hsa=20000),
        wife=_make_person(age=58, retire_age=64, ss_age=67), expense_mode=True, dynamic_value=1.25
    )

    view_model = manager.build_results_view_model()

    assert isinstance(view_model, mod.ScenarioResultsViewModel)

    assert view_model.original_metrics.ending_portfolio == 100000
    assert view_model.original_metrics.depletion_rate == 5.0
    assert view_model.original_metrics.lifetime_funding_gap == 300
    assert view_model.original_metrics.lifetime_taxes == 3000

    assert view_model.changed_metrics.ending_portfolio == 200000
    assert view_model.changed_metrics.ending_cash_flow == 3000
    assert view_model.changed_metrics.ending_pre_tax == 80000
    assert view_model.changed_metrics.ending_hsa == 20000

    assert view_model.original_assumptions.dynamic_label == "Expense Multiplier"
    assert view_model.original_assumptions.dynamic_value == pytest.approx(100.0)
    assert view_model.original_assumptions.inflation_rate == pytest.approx(3.0)
    assert view_model.original_assumptions.fund_expense == pytest.approx(0.5)
    assert view_model.original_assumptions.stock == pytest.approx(60.0)
    assert view_model.original_assumptions.bonds == pytest.approx(30.0)
    assert view_model.original_assumptions.cash == pytest.approx(10.0)

    assert view_model.original_assumptions.wife_age is None
    assert view_model.changed_assumptions.wife_age == 58
    assert view_model.changed_assumptions.wife_retire_age == 64
    assert view_model.changed_assumptions.wife_ss_age == 67


def test_build_results_view_model_uses_withdrawal_rate_in_withdrawal_mode():
    manager, _, state = _make_manager()

    state.baseline_results = _make_result(expense_mode=False, dynamic_value=4.0)
    state.scenario_results = _make_result(expense_mode=False, dynamic_value=5.5)

    view_model = manager.build_results_view_model()

    assert view_model.original_assumptions.dynamic_label == "Withdrawal Rate"
    assert view_model.original_assumptions.dynamic_value == pytest.approx(4.0)
    assert view_model.changed_assumptions.dynamic_label == "Withdrawal Rate"
    assert view_model.changed_assumptions.dynamic_value == pytest.approx(5.5)