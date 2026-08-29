# test_gui_init.py

import os

from src.warpsimlab.gui import gui_init


def _make_gui():
    return gui_init.PortfolioSimulatorGUI.__new__(gui_init.PortfolioSimulatorGUI)


class DummyRoot:
    def __init__(self):
        self.destroy_called = 0

    def destroy(self):
        self.destroy_called += 1


class DummyScenarioController:
    def __init__(self, active=False):
        self.session_active = active
        self.capture_called = 0

    def capture_current_layout(self):
        self.capture_called += 1


def test_gui_class_contains_expected_mixins():
    bases = gui_init.PortfolioSimulatorGUI.__bases__

    assert gui_init.PortfolioSimulatorGUI_DisplayMixin in bases
    assert gui_init.PortfolioSimulatorGUI_NavigationMixin in bases
    assert gui_init.PortfolioSimulatorGUI_EditorsMixin in bases
    assert gui_init.PortfolioSimulatorGUI_ReportsMixin in bases
    assert gui_init.PortfolioSimulatorGUI_RunMixin in bases
    assert gui_init.PortfolioSimulatorGUI_IOMixin in bases


def test_init_vars_loads_market_data_and_defaults(monkeypatch):
    gui = _make_gui()

    fake_market = {
        "eq_mean": 8,
        "bd_mean": 4,
        "cs_mean": 2,
        "re_mean": 3,
        "eq_std": 10,
        "bd_std": 6,
        "cs_std": 1,
        "re_std": 7,
        "inflation": 2,
    }

    monkeypatch.setattr(gui_init, "load_market_data", lambda: fake_market)
    monkeypatch.setattr(os.path, "expanduser", lambda path: "C:\\Users\\TestUser")

    gui._init_vars()

    assert gui.eq_mean == 8
    assert gui.bd_mean == 4
    assert gui.cs_mean == 2
    assert gui.re_mean == 3

    assert gui.eq_std == 10
    assert gui.bd_std == 6
    assert gui.cs_std == 1
    assert gui.re_std == 7

    assert gui.inflation == 2
    assert gui.historical_market == "25_year_data"

    assert gui.simulation_settings["years_to_simulate"] == gui_init.DEFAULT_YEARS
    assert gui.simulation_settings["num_sims"] == gui_init.DEFAULT_SIMULATIONS
    assert gui.simulation_settings["fund_expense"] == gui_init.DEFAULT_FUND_EXPENSE

    assert gui.simulation_controls["plot_mode"] == "real"
    assert gui.simulation_controls["overlay_profit_loss"] is True
    assert gui.simulation_controls["user_annotation_strings"] == []
    assert gui.simulation_controls["state_of_residence"] == gui_init.DEFAULT_STATE_OF_RESIDENCE
    assert gui.simulation_controls["csv_output_dir"] == "C:\\Users\\TestUser\\Desktop\\WARPSimLab"

    assert "executive_summary" in gui.report_options
    assert "year_by_year_details" in gui.report_options
    assert "historical_window_risk" in gui.report_options
    assert "monte_carlo_risk" in gui.report_options
    assert "tax_report" in gui.report_options
    assert "spending_comparison" in gui.report_options
    assert "asset_allocation_comparison" in gui.report_options
    assert "retirement_ss_comparison" in gui.report_options

    assert gui.special_income_streams == [dict(stream) for stream in gui_init.DEFAULT_SPECIAL_INCOME_STREAMS]
    assert gui.roth_flows == [dict(flow) for flow in gui_init.DEFAULT_ROTH_FLOWS]


def test_close_application_saves_active_scenario_layout(monkeypatch):
    gui = _make_gui()
    gui.root = DummyRoot()
    gui.display_settings = {"test": True}
    gui.scenario_controller = DummyScenarioController(active=True)

    geometry_calls = []
    settings_calls = []

    gui._save_main_window_geometry = lambda: geometry_calls.append(True)
    monkeypatch.setattr(gui_init, "save_display_settings", lambda settings: settings_calls.append(settings))

    gui._close_application()

    assert gui.scenario_controller.capture_called == 1
    assert geometry_calls == [True]
    assert settings_calls == [gui.display_settings]
    assert gui.root.destroy_called == 1


def test_close_application_handles_inactive_scenario(monkeypatch):
    gui = _make_gui()
    gui.root = DummyRoot()
    gui.display_settings = {}
    gui.scenario_controller = DummyScenarioController(active=False)

    gui._save_main_window_geometry = lambda: None
    monkeypatch.setattr(gui_init, "save_display_settings", lambda settings: None)

    gui._close_application()

    assert gui.scenario_controller.capture_called == 0
    assert gui.root.destroy_called == 1


def test_close_application_handles_missing_scenario_controller(monkeypatch):
    gui = _make_gui()
    gui.root = DummyRoot()
    gui.display_settings = {}

    gui._save_main_window_geometry = lambda: None
    monkeypatch.setattr(gui_init, "save_display_settings", lambda settings: None)

    gui._close_application()

    assert gui.root.destroy_called == 1