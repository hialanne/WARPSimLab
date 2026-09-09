# test_gui_scenarioState.py

from types import SimpleNamespace

from src.warpsimlab.gui.scenario import gui_scenarioState as mod


class DummyValue:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


def _make_person(retire_age=67, ss_age=67):
    return SimpleNamespace(retire_age=retire_age, ss_age=ss_age)


def _make_portfolio(value):
    return SimpleNamespace(value=value)


def _make_main_gui(second_person_enabled=False):
    return SimpleNamespace(
        simulation_controls={"second_person_enabled": second_person_enabled, "include_realestate": False},
        simulation_settings={"fund_expense": 0.55},
        husband=_make_person(65, 67),
        wife=_make_person(63, 66),
        husband_portfolio=_make_portfolio(100),
        wife_portfolio=_make_portfolio(200),
        inflation=3.25,
        expensesDict={"expense": 1234},
    )


def _make_controller(main_gui):
    return SimpleNamespace(
        main_gui=main_gui,
        person_snapshots={},
        portfolio_snapshots={},
        retirement_snapshots=None,
        sliders_frame=None,
        baseline_results=None,
        scenario_results=None,
        include_realestate_var=DummyValue(False),
        plot_style="portfolio",
    )


def test_build_snapshots_from_truth_single_person_creates_independent_copies():
    main_gui = _make_main_gui(second_person_enabled=False)
    controller = _make_controller(main_gui)
    manager = mod.ScenarioStateManager(controller)

    manager.build_snapshots_from_truth()

    assert set(controller.person_snapshots) == {"husband"}
    assert set(controller.portfolio_snapshots) == {"husband"}
    assert controller.person_snapshots["husband"] is not main_gui.husband
    assert controller.portfolio_snapshots["husband"] is not main_gui.husband_portfolio
    assert controller.retirement_snapshots.delta_inflation == 0.0
    assert controller.retirement_snapshots.fund_expense == 0.55
    assert controller.retirement_snapshots.historical_data_multiplier == 100.0

def test_build_snapshots_from_truth_second_person_includes_wife():
    main_gui = _make_main_gui(second_person_enabled=True)
    controller = _make_controller(main_gui)
    manager = mod.ScenarioStateManager(controller)

    manager.build_snapshots_from_truth()

    assert set(controller.person_snapshots) == {"husband", "wife"}
    assert set(controller.portfolio_snapshots) == {"husband", "wife"}
    assert controller.person_snapshots["wife"] is not main_gui.wife
    assert controller.portfolio_snapshots["wife"] is not main_gui.wife_portfolio


def test_clone_result_inputs_returns_deep_copies():
    main_gui = _make_main_gui()
    controller = _make_controller(main_gui)
    manager = mod.ScenarioStateManager(controller)

    persons = {"husband": _make_person(65, 67)}
    portfolios = {"husband": _make_portfolio(100)}
    retirement = SimpleNamespace(inflation=3.0)

    persons_copy, portfolios_copy, retirement_copy = manager.clone_result_inputs(persons, portfolios, retirement)

    assert persons_copy == persons
    assert portfolios_copy["husband"].value == 100
    assert retirement_copy.inflation == 3.0
    assert persons_copy is not persons
    assert persons_copy["husband"] is not persons["husband"]
    assert portfolios_copy is not portfolios
    assert portfolios_copy["husband"] is not portfolios["husband"]
    assert retirement_copy is not retirement


def test_compute_results_from_inputs_uses_copies_and_returns_simulation_inputs(monkeypatch):
    main_gui = _make_main_gui(second_person_enabled=False)
    controller = _make_controller(main_gui)
    manager = mod.ScenarioStateManager(controller)

    persons = {"husband": _make_person(65, 67)}
    portfolios = {"husband": _make_portfolio(100)}
    retirement = SimpleNamespace(inflation=3.0)
    sim_config = SimpleNamespace(second_person_enabled=False)
    pipeline_calls = {}

    def build_simulation_from_gui(**kwargs):
        assert kwargs["sim_type"] == "portfolio_sim"
        assert kwargs["use_snapshots"] is True
        assert kwargs["retirement_snapshots"] is not retirement
        return sim_config

    def fake_run_pipeline(husband_portfolio, wife_portfolio, husband, wife, expenses_dict, received_sim_config):
        pipeline_calls["husband_portfolio"] = husband_portfolio
        pipeline_calls["husband"] = husband
        pipeline_calls["wife_portfolio"] = wife_portfolio
        pipeline_calls["wife"] = wife
        pipeline_calls["expenses_dict"] = expenses_dict
        pipeline_calls["sim_config"] = received_sim_config
        return {"result": 42}

    main_gui.build_simulation_from_gui = build_simulation_from_gui
    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline)

    result = manager.compute_results_from_inputs(persons, portfolios, retirement, False)

    assert result["sim_config"].include_realestate is False
    assert result["p"] == {"result": 42}
    assert result["sim_config"] is sim_config
    assert result["husband"] is not persons["husband"]
    assert result["wife"] is None
    assert result["retirement_snapshots"] is not retirement
    assert pipeline_calls["husband_portfolio"] is not portfolios["husband"]
    assert pipeline_calls["husband"] is result["husband"]
    assert pipeline_calls["wife_portfolio"] is None
    assert pipeline_calls["wife"] is None
    assert pipeline_calls["expenses_dict"] is main_gui.expensesDict
    assert pipeline_calls["sim_config"] is sim_config


def test_compute_results_from_inputs_passes_wife_when_enabled(monkeypatch):
    main_gui = _make_main_gui(second_person_enabled=True)
    controller = _make_controller(main_gui)
    manager = mod.ScenarioStateManager(controller)

    persons = {"husband": _make_person(65, 67), "wife": _make_person(63, 66)}
    portfolios = {"husband": _make_portfolio(100), "wife": _make_portfolio(200)}
    retirement = SimpleNamespace(inflation=3.0)
    main_gui.build_simulation_from_gui = lambda **kwargs: SimpleNamespace(second_person_enabled=True)

    pipeline_calls = {}

    def fake_run_pipeline(husband_portfolio, wife_portfolio, husband, wife, expenses_dict, sim_config):
        pipeline_calls["wife"] = wife
        pipeline_calls["wife_portfolio"] = wife_portfolio
        return {"result": 42}

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline)

    result = manager.compute_results_from_inputs(persons, portfolios, retirement, False)

    assert result["wife"] is not None
    assert result["wife"] is not persons["wife"]
    assert pipeline_calls["wife"] is result["wife"]
    assert pipeline_calls["wife_portfolio"] is not portfolios["wife"]


def test_compute_baseline_results_uses_copies_of_current_snapshots(monkeypatch):
    main_gui = _make_main_gui()
    controller = _make_controller(main_gui)
    manager = mod.ScenarioStateManager(controller)

    controller.person_snapshots = {"husband": _make_person(65, 67)}
    controller.portfolio_snapshots = {"husband": _make_portfolio(100)}
    controller.retirement_snapshots = SimpleNamespace(inflation=3.0)
    received = {}

    def fake_compute(persons, portfolios, retirement, include_realestate):
        received["persons"] = persons
        received["portfolios"] = portfolios
        received["retirement"] = retirement
        received["include_realestate"] = include_realestate
        return {"baseline": True}

    monkeypatch.setattr(manager, "compute_results_from_inputs", fake_compute)

    manager.compute_baseline_results()

    assert received["include_realestate"] is False
    assert controller.baseline_results == {"baseline": True}
    assert received["persons"] is not controller.person_snapshots
    assert received["persons"]["husband"] is not controller.person_snapshots["husband"]
    assert received["portfolios"] is not controller.portfolio_snapshots
    assert received["portfolios"]["husband"] is not controller.portfolio_snapshots["husband"]
    assert received["retirement"] is not controller.retirement_snapshots


def test_compute_scenario_results_uses_current_snapshots_and_returns_result(monkeypatch):
    main_gui = _make_main_gui()
    controller = _make_controller(main_gui)
    manager = mod.ScenarioStateManager(controller)

    controller.person_snapshots = {"husband": _make_person(65, 67)}
    controller.portfolio_snapshots = {"husband": _make_portfolio(100)}
    controller.retirement_snapshots = SimpleNamespace(inflation=3.0)
    received = {}

    def fake_compute(persons, portfolios, retirement, include_realestate):
        received["persons"] = persons
        received["portfolios"] = portfolios
        received["retirement"] = retirement
        received["include_realestate"] = include_realestate
        return {"scenario": True}

    monkeypatch.setattr(manager, "compute_results_from_inputs", fake_compute)

    result = manager.compute_scenario_results()

    assert received["include_realestate"] is False
    assert result == {"scenario": True}
    assert controller.scenario_results is result
    assert received["persons"] is controller.person_snapshots
    assert received["portfolios"] is controller.portfolio_snapshots
    assert received["retirement"] is controller.retirement_snapshots