# test_gui_init.py

from __future__ import annotations

from types import ModuleType
import sys
import os
import tkinter as tk
from tkinter import ttk
from datetime import datetime

import pytest

#pytest.skip("Skipping GUI tests for now", allow_module_level=True)



@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    root.withdraw()
    yield root
    root.destroy()


def _install_stub_modules(monkeypatch):
    """
    gui_init imports many modules. For unit tests, we stub the minimum needed
    so that importing src.warpsimlab.gui.gui_init succeeds without requiring the
    whole GUI stack.
    """
    # --- src.warpsimlab.utils.constants (wildcard import) ---
    consts = ModuleType("src.warpsimlab.utils.constants")
    # Provide the DEFAULT_* names referenced during __init__ (even if tests don't run __init__)
    for name in [
        "DEFAULT_HUSBAND_AGE",
        "DEFAULT_HUSBAND_RETIRE",
        "DEFAULT_HUSBAND_INCOME",
        "DEFAULT_HUSBAND_SOC",
        "DEFAULT_HUSBAND_SOC_AGE",
        "DEFAULT_HUSBAND_PENSION",
        "DEFAULT_HUSBAND_PENSION_AGE",
        "DEFAULT_HUSBAND_ANNUITY",
        "DEFAULT_HUSBAND_ANNUITY_AGE",
        "DEFAULT_HUSBAND_401K_CONTRIB",
        "DEFAULT_HUSBAND_401K_MATCH",
        "DEFAULT_WIFE_AGE",
        "DEFAULT_WIFE_RETIRE",
        "DEFAULT_WIFE_INCOME",
        "DEFAULT_WIFE_SOC",
        "DEFAULT_WIFE_SOC_AGE",
        "DEFAULT_WIFE_PENSION",
        "DEFAULT_WIFE_PENSION_AGE",
        "DEFAULT_WIFE_ANNUITY",
        "DEFAULT_WIFE_ANNUITY_AGE",
        "DEFAULT_WIFE_401K_CONTRIB",
        "DEFAULT_WIFE_401K_MATCH",
        "DEFAULT_EQUITY_PRE_H",
        "DEFAULT_EQUITY_POST_H",
        "DEFAULT_BOND_PRE_H",
        "DEFAULT_BOND_POST_H",
        "DEFAULT_CASH_PRE_H",
        "DEFAULT_CASH_POST_H",
        "DEFAULT_REAL_ESTATE_H",
        "DEFAULT_EQUITY_PRE_W",
        "DEFAULT_EQUITY_POST_W",
        "DEFAULT_BOND_PRE_W",
        "DEFAULT_BOND_POST_W",
        "DEFAULT_CASH_PRE_W",
        "DEFAULT_CASH_POST_W",
        "DEFAULT_REAL_ESTATE_W",
    ]:
        setattr(consts, name, 0)
    monkeypatch.setitem(sys.modules, "src.warpsimlab.utils.constants", consts)

    # --- stubs for other GUI / utility imports ---
    def stub_mod(name: str, **attrs):
        m = ModuleType(name)
        for k, v in attrs.items():
            setattr(m, k, v)
        monkeypatch.setitem(sys.modules, name, m)
        return m

    # Mixins
    stub_mod("src.warpsimlab.gui.gui_run", PortfolioSimulatorGUI_RunMixin=type("RunMixin", (), {}))
    stub_mod("src.warpsimlab.gui.gui_io", PortfolioSimulatorGUI_IOMixin=type("IOMixin", (), {}))

    # Frames / classes referenced
    stub_mod("src.warpsimlab.gui.gui_main", MainHomeFrame=type("MainHomeFrame", (), {}))
    stub_mod("src.warpsimlab.gui.gui_tutorial", TutorialFrame=type("TutorialFrame", (), {}))
    stub_mod("src.warpsimlab.gui.gui_expenses_taxes", ExpensesTaxesFrame=type("ExpensesTaxesFrame", (), {}))
    stub_mod("src.warpsimlab.gui.gui_market_simulation_combined", MarketSimulationCombinedFrame=type("MarketSimulationCombinedFrame", (), {}))

    # Scenario controller
    stub_mod("src.warpsimlab.gui.gui_scenarioController", ScenarioController=type("ScenarioController", (), {"__init__": lambda self, gui: None}))

    # Person/portfolio/dataclasses + other gui modules imported with wildcard
    stub_mod("src.warpsimlab.gui.gui_person")
    stub_mod("src.warpsimlab.gui.gui_portfolio")
    stub_mod("src.warpsimlab.gui.gui_historicalData")
    stub_mod("src.warpsimlab.gui.gui_portfolioSimulation")
    stub_mod("src.warpsimlab.gui.gui_simulationControls")
    stub_mod("src.warpsimlab.gui.gui_retirement")
    stub_mod("src.warpsimlab.gui.gui_scenarioSnapshots")

    # io_utils wildcard
    stub_mod("src.warpsimlab.utils.io_utils")

    # Portfolio class import
    stub_mod("src.warpsimlab.dataClasses.portfolio", Portfolio=type("Portfolio", (), {"__init__": lambda self, **k: None}))
    stub_mod(
        "src.warpsimlab.dataClasses.dynamicExpenses",
        DynamicExpenses=type(
            "DynamicExpenses",
            (),
            {
                "__init__": lambda self: None,
                "add_expense": lambda self, **kwargs: None,
            },
        ),
    )


@pytest.fixture
def gui_init_mod(monkeypatch):
    _install_stub_modules(monkeypatch)
    from src.warpsimlab.gui import gui_init as mod
    return mod

@pytest.fixture
def patched_soft_disable(gui_init_mod, monkeypatch):
    def fake_set_tk_button_soft_disabled(button, enabled, real_command, noop_command=None):
        button.configure(
            state="normal" if enabled else "disabled",
            style="Big.TButton" if enabled else "BigFaded.TButton",
            command=real_command if enabled else noop_command,
            fg="black" if enabled else "gray60",
            relief="raised" if enabled else "flat",
        )

    monkeypatch.setattr(
        gui_init_mod,
        "set_tk_button_soft_disabled",
        fake_set_tk_button_soft_disabled,
        raising=True,
    )

class DummyBtn:
    def __init__(self):
        self.props = {}

    def configure(self, **kwargs):
        self.props.update(kwargs)

    def cget(self, key):
        return self.props.get(key)


def _make_gui_instance(gui_init_mod, tk_root):
    GUI = gui_init_mod.PortfolioSimulatorGUI
    inst = GUI.__new__(GUI)
    inst.root = tk_root
    inst.mode_var = tk.StringVar(master=tk_root, value="Basic")
    inst.legal_accepted = False

    # buttons used by current _apply_mode_to_top_buttons / _apply_mode_to_results_button
    inst.home_button = DummyBtn()
    inst.cashflow_button = DummyBtn()
    inst.balance_sheet_button = DummyBtn()
    inst.edit_retirement_button = DummyBtn()
    inst.simulation_button = DummyBtn()
    inst.results_button = DummyBtn()

    # still used by test_apply_mode_to_tab_labels
    inst.edit_portfolio_button = DummyBtn()

    # menus used by current code
    class DummyMenu:
        def __init__(self):
            self.calls = []

        def entryconfig(self, index, **kwargs):
            self.calls.append((index, kwargs))

        def delete(self, *args, **kwargs):
            pass

        def add_command(self, *args, **kwargs):
            pass

        def add_separator(self, *args, **kwargs):
            pass

    inst.cashflow_menu = DummyMenu()
    inst.results_menu = DummyMenu()
    inst._cashflow_taxes_index = 0

    # callback targets referenced by set_tk_button_soft_disabled
    inst._show_home_menu = lambda: None
    inst._show_cashflow_menu = lambda: None
    inst._show_balance_sheet_menu = lambda: None
    inst._show_simulation_menu = lambda: None
    inst._show_results_menu = lambda: None
    inst._cmd_edit_retirement_controls = lambda: None

    # scenario controller used by _rebuild_results_menu in Advanced mode
    class DummyScenarioController:
        def start_or_focus(self):
            pass

    inst.scenario_controller = DummyScenarioController()

    # container used by _on_mode_changed / _on_second_person_changed
    inst.edit_frame_container = ttk.Frame(tk_root)
    ttk.Label(inst.edit_frame_container, text="child").pack()

    # methods invoked downstream
    inst.edit_main_home_called = 0
    inst.edit_person_data_called = 0
    inst.sync_tax_called = 0

    inst.edit_main_home = lambda: setattr(inst, "edit_main_home_called", inst.edit_main_home_called + 1)
    inst.edit_person_data = lambda: setattr(inst, "edit_person_data_called", inst.edit_person_data_called + 1)
    inst._sync_tax_status_from_second_person = lambda: setattr(inst, "sync_tax_called", inst.sync_tax_called + 1)

    return inst


def test_advanced_only(gui_init_mod, tk_root):
    inst = _make_gui_instance(gui_init_mod, tk_root)

    inst.mode_var.set("Basic")
    assert inst._advanced_only() is False

    inst.mode_var.set("Advanced")
    assert inst._advanced_only() is True


def test_on_mode_changed_destroys_editor_children_and_calls_home(gui_init_mod, tk_root):
    inst = _make_gui_instance(gui_init_mod, tk_root)

    # Ensure container has children before
    assert len(inst.edit_frame_container.winfo_children()) > 0

    inst._on_mode_changed()

    # Children should be destroyed
    assert len(inst.edit_frame_container.winfo_children()) == 0
    # Home called once
    assert inst.edit_main_home_called == 1


def test_on_second_person_changed_syncs_tax_and_rebuilds_person_editor(gui_init_mod, tk_root):
    inst = _make_gui_instance(gui_init_mod, tk_root)

    assert len(inst.edit_frame_container.winfo_children()) > 0

    inst._on_second_person_changed()

    assert inst.sync_tax_called == 1
    assert len(inst.edit_frame_container.winfo_children()) == 0
    assert inst.edit_person_data_called == 1


def test_init_vars_loads_market_data_and_defaults(gui_init_mod, monkeypatch, tk_root):
    inst = _make_gui_instance(gui_init_mod, tk_root)

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

    # gui_init references load_market_data from wildcard import; patch on module
    monkeypatch.setattr(gui_init_mod, "load_market_data", lambda *a, **k: fake_market, raising=False)

    # Stabilize expanduser for deterministic default path
    monkeypatch.setattr(os.path, "expanduser", lambda p: "C:\\Users\\TestUser", raising=True)

    inst._init_vars()

    assert inst.eq_mean == 8
    assert inst.bd_mean == 4
    assert inst.cs_mean == 2
    assert inst.re_mean == 3
    assert inst.inflation == 2
    assert inst.historical_market == "25_year_data"

    # default dicts exist and contain key defaults
    assert inst.simulation_settings["years_to_simulate"] == 30
    assert inst.simulation_controls["plot_mode"] == "real"
    assert inst.simulation_controls["overlay_profit_loss"] is True
    assert inst.simulation_controls["user_annotation_strings"] == []
    assert "csv_output_dir" in inst.simulation_controls