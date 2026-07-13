# test_gui_portfolioSimulation.py

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

#pytest.skip("Skipping GUI tests for now", allow_module_level=True)


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk not available: {e}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def mod_no_tooltip(monkeypatch):
    from src.warpsimlab.gui import gui_portfolioSimulation as mod

    class DummyTooltip:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(mod, "Tooltip", DummyTooltip, raising=True)
    return mod


def _base_settings():
    return {
        "start_year": 2025,
        "years_to_simulate": 30,
        "num_sims": 500,
        "use_fund_expenses": True,
        "fund_expense": 0.75,
        "initial_allocation_mode": "dont-rebalance",
        "custom_stock": 60.0,
        "custom_bonds": 30.0,
        "custom_cash": 10.0,
    }


def test_init_sets_stringvars_from_settings(tk_root, mod_no_tooltip):
    mod = mod_no_tooltip

    settings = _base_settings()
    sim_vars = {"_settings_dict": settings}

    frame = mod.PortfolioSimulationEditFrame(tk_root, sim_vars)
    frame.pack()

    assert frame.start_year_var.get() == frame._format_sim_field("start_year", settings["start_year"])
    assert frame.years_to_simulate_var.get() == frame._format_sim_field("years_to_simulate", settings["years_to_simulate"])
    assert frame.sims_var.get() == frame._format_sim_field("num_sims", settings["num_sims"])
    assert frame.use_fund_expenses_var.get() is True
    assert frame.fund_expense_var.get() == frame._format_sim_field("fund_expense", settings["fund_expense"])
    assert frame.initial_allocation_mode_var.get() == settings["initial_allocation_mode"]

def test_bind_var_updates_settings_and_ignores_invalid(tk_root, mod_no_tooltip):
    mod = mod_no_tooltip

    settings = _base_settings()
    sim_vars = {"_settings_dict": settings}

    frame = mod.PortfolioSimulationEditFrame(tk_root, sim_vars)
    frame.pack()

    assert frame._validate_sim_field("2030", "start_year") is True
    tk_root.update()
    tk_root.update_idletasks()
    assert settings["start_year"] == 2030
    assert frame.start_year_var.get() == frame._format_sim_field("start_year", 2030)

    assert frame._validate_sim_field("35", "years_to_simulate") is True
    tk_root.update()
    tk_root.update_idletasks()
    assert settings["years_to_simulate"] == 35
    assert frame.years_to_simulate_var.get() == frame._format_sim_field("years_to_simulate", 35)

    assert frame._validate_sim_field("1500", "num_sims") is True
    tk_root.update()
    tk_root.update_idletasks()
    assert settings["num_sims"] == 1500
    assert frame.sims_var.get() == frame._format_sim_field("num_sims", 1500)

    assert frame._validate_sim_field("1.25", "fund_expense") is True
    tk_root.update()
    tk_root.update_idletasks()
    assert settings["fund_expense"] == pytest.approx(1.25)
    assert frame.fund_expense_var.get() == frame._format_sim_field("fund_expense", 1.25)

    prev = settings["years_to_simulate"]
    assert frame._validate_sim_field("nope", "years_to_simulate") is True
    tk_root.update()
    tk_root.update_idletasks()
    assert settings["years_to_simulate"] == prev
    assert frame.years_to_simulate_var.get() == frame._format_sim_field("years_to_simulate", prev)

    prev_f = settings["fund_expense"]
    assert frame._validate_sim_field("bad", "fund_expense") is True
    tk_root.update()
    tk_root.update_idletasks()
    assert settings["fund_expense"] == prev_f
    assert frame.fund_expense_var.get() == frame._format_sim_field("fund_expense", prev_f)

def test_toggle_fund_expense_entry_enables_and_disables(tk_root, mod_no_tooltip):
    mod = mod_no_tooltip

    settings = _base_settings()
    sim_vars = {"_settings_dict": settings}

    frame = mod.PortfolioSimulationEditFrame(tk_root, sim_vars)
    frame.pack()

    # Starts enabled because use_fund_expenses True
    assert str(frame.fund_expense_entry.cget("state")) == "normal"

    frame.use_fund_expenses_var.set(False)
    frame._toggle_fund_expense_entry()
    assert str(frame.fund_expense_entry.cget("state")) == "disabled"

    frame.use_fund_expenses_var.set(True)
    frame._toggle_fund_expense_entry()
    assert str(frame.fund_expense_entry.cget("state")) == "normal"


def test_toggle_custom_entries_shows_and_hides_custom_block(tk_root, mod_no_tooltip):
    mod = mod_no_tooltip

    settings = _base_settings()
    settings["initial_allocation_mode"] = "dont-rebalance"
    sim_vars = {"_settings_dict": settings}

    frame = mod.PortfolioSimulationEditFrame(tk_root, sim_vars)
    frame.pack()

    # Not custom => widgets should not be mapped
    assert frame.custom_stock_label.winfo_manager() == ""
    assert frame.custom_stock_entry.winfo_manager() == ""
    assert frame.custom_bonds_label.winfo_manager() == ""
    assert frame.custom_cash_entry.winfo_manager() == ""
    # Switch to custom => widgets should be gridded/mapped
    frame.initial_allocation_mode_var.set("custom")
    frame.toggle_custom_entries()

    print("root ismapped:", tk_root.winfo_ismapped())
    print("label manager:", frame.custom_stock_label.winfo_manager())
    print("label grid_info:", frame.custom_stock_label.grid_info())
    print("label ismapped:", frame.custom_stock_label.winfo_ismapped())



    assert frame.custom_stock_label.winfo_manager() == "grid"
    assert frame.custom_stock_entry.winfo_manager() == "grid"

    assert frame.custom_bonds_label.winfo_manager() == "grid"
    assert frame.custom_bonds_entry.winfo_manager() == "grid"

    assert frame.custom_cash_label.winfo_manager() == "grid"
    assert frame.custom_cash_entry.winfo_manager() == "grid"

    # Switch away from custom => widgets should be hidden again
    frame.initial_allocation_mode_var.set("70-20-10")
    frame.toggle_custom_entries()

    assert frame.custom_stock_label.winfo_manager() == ""
    assert frame.custom_stock_entry.winfo_manager() == ""
    assert frame.custom_bonds_label.winfo_manager() == ""
    assert frame.custom_cash_entry.winfo_manager() == ""


def test_custom_percent_vars_update_settings_when_custom_selected(tk_root, mod_no_tooltip):
    mod = mod_no_tooltip

    settings = _base_settings()
    settings["initial_allocation_mode"] = "custom"
    sim_vars = {"_settings_dict": settings}

    frame = mod.PortfolioSimulationEditFrame(tk_root, sim_vars)
    frame.pack()

    frame.initial_allocation_mode_var.set("custom")
    frame.toggle_custom_entries()

    assert frame._validate_sim_field("55.5", "custom_stock") is True
    tk_root.update()
    tk_root.update_idletasks()

    assert frame._validate_sim_field("33.0", "custom_bonds") is True
    tk_root.update()
    tk_root.update_idletasks()

    assert frame._validate_sim_field("11.5", "custom_cash") is True
    tk_root.update()
    tk_root.update_idletasks()

    assert settings["custom_stock"] == pytest.approx(55.5)
    assert settings["custom_bonds"] == pytest.approx(33.0)
    assert settings["custom_cash"] == pytest.approx(11.5)

    assert frame.custom_stock_var.get() == frame._format_sim_field("custom_stock", 55.5)
    assert frame.custom_bonds_var.get() == frame._format_sim_field("custom_bonds", 33.0)
    assert frame.custom_cash_var.get() == frame._format_sim_field("custom_cash", 11.5)

