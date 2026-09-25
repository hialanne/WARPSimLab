from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.gui.gui_settings import SUMMARY_DIALOG_AUTOMATIC, SUMMARY_DIALOG_MAXIMIZED
from src.warpsimlab.outputDialogs.summaryDialog import summaryDialog as mod
from src.warpsimlab.outputDialogs.summaryDialog.summaryCashFlow import build_cash_flow_tab
from src.warpsimlab.outputDialogs.summaryDialog.summaryIncome import build_income_tab
from src.warpsimlab.outputDialogs.summaryDialog.summaryOverview import build_summary_tab
from src.warpsimlab.outputDialogs.summaryDialog.summaryPortfolio import build_portfolio_tab


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")

    root.withdraw()
    yield root
    root.destroy()


def _make_summary_settings(**overrides):
    settings = {
        "sizing_mode": SUMMARY_DIALOG_AUTOMATIC,
        "remember_geometry": False,
        "last_geometry": None,
        "last_maximized": False,
    }
    settings.update(overrides)
    return {"summary_dialog": settings}


def _make_results():
    years = np.array([2025, 2026, 2027, 2028])

    def values(*items):
        return np.array(items, dtype=float)

    return {
        "year": years,
        "pre_tax_assets": values(100000, 90000, 80000, 70000),
        "post_tax_assets": values(50000, 48000, 46000, 44000),
        "roth_assets": values(10000, 12000, 14000, 16000),
        "hsa_assets": values(5000, 5500, 6000, 6500),
        "real_estate": values(200000, 205000, 210000, 215000),
        "total_assets": values(365000, 360500, 356000, 351500),

        "wages": values(80000, 80000, 0, 0),
        "employee_401k_contributions": values(10000, 10000, 0, 0),
        "hsa_employee_contributions": values(2000, 2000, 0, 0),
        "rmd": values(0, 0, 0, 5000),
        "social_security": values(0, 0, 30000, 30000),
        "pensions": values(0, 0, 12000, 12000),
        "annuities": values(0, 0, 6000, 6000),
        "special_income": values(0, 1000, 0, 0),
        "bond_interest": values(1000, 1000, 1000, 1000),
        "cash_interest": values(500, 500, 500, 500),
        "qualified_equity_distributions": values(750, 750, 750, 750),
        "withdrawal": values(0, 0, 10000, 10000),
        "emergency_pre_tax_used": values(0, 0, 0, 0),
        "gross_income": values(94250, 95250, 59750, 64750),

        "taxes": values(15000, 15000, 8000, 9000),
        "tax_bracket": values(0.22, 0.22, 0.12, 0.12),
        "net_income": values(67250, 68250, 51750, 55750),
        "hsa_employer_contributions": values(1000, 1000, 0, 0),
        "roth_ira_contributions": values(0, 0, 0, 0),
        "roth_workplace_contributions": values(0, 0, 0, 0),
        "hsa_qualified_withdrawals": values(0, 0, 1000, 1000),
        "hsa_taxable_withdrawals": values(0, 0, 0, 0),
        "expenses": values(50000, 50000, 50000, 50000),
        "net_cash_flow": values(18250, 19250, 2750, 6750),
        "fund_expenses": values(1000, 950, 900, 850),
        "funding_gap": values(0, 0, 0, 0),
        "simulated_shortfall_rate": 0.0,
    }


def _make_tab_dialog():
    results = _make_results()

    dialog = SimpleNamespace(
        results=results,
        husband=SimpleNamespace(age=60, retire_age=62),
        wife=SimpleNamespace(age=59, retire_age=63),
        sim_config=SimpleNamespace(
            second_person_enabled=True,
            always_use_expense_mode=True,
            eq_mean=0.07,
            bd_mean=0.03,
            cs_mean=0.02,
            inflation_rate=0.025,
            fund_expense=0.001,
        ),
        _report_header_font=("Arial", 14, "bold"),
        _report_body_font=("Courier New", 12),
        _report_body_bold_font=("Courier New", 12, "bold"),
    )

    def get_display_indices():
        return [1, 1, 3, 3]

    def add_year_headers(tab, column_indices, header_font):
        for col in range(5):
            tk.Label(tab, text=str(col), font=header_font).grid(row=0, column=col)

    dialog._get_display_indices = get_display_indices
    dialog._add_year_headers = add_year_headers

    return dialog


def _make_bare_dialog(tk_root, summary_settings):
    dialog = mod.SummaryDialog.__new__(mod.SummaryDialog)
    dialog.master = tk_root
    dialog.sim_config = SimpleNamespace(root=tk_root)
    dialog._scaling_root = dialog
    dialog._warpsimlab_gui_scale = 1.0

    dialog.winfo_screenwidth = tk_root.winfo_screenwidth
    dialog.winfo_screenheight = tk_root.winfo_screenheight

    tk_root._warpsimlab_display_settings = summary_settings

    return dialog


def test_get_display_indices_single_person():
    dialog = mod.SummaryDialog.__new__(mod.SummaryDialog)
    dialog.results = {"year": np.arange(2025, 2036)}
    dialog.husband = SimpleNamespace(age=60, retire_age=65)
    dialog.wife = None
    dialog.sim_config = SimpleNamespace(second_person_enabled=False)

    assert dialog._get_display_indices() == [1, 4, 6, 10]


def test_get_display_indices_uses_later_retirement_for_couple():
    dialog = mod.SummaryDialog.__new__(mod.SummaryDialog)
    dialog.results = {"year": np.arange(2025, 2041)}
    dialog.husband = SimpleNamespace(age=60, retire_age=65)
    dialog.wife = SimpleNamespace(age=58, retire_age=66)
    dialog.sim_config = SimpleNamespace(second_person_enabled=True)

    assert dialog._get_display_indices() == [1, 7, 9, 15]


def test_summary_startup_maximized(monkeypatch, tk_root):
    settings = _make_summary_settings(sizing_mode=SUMMARY_DIALOG_MAXIMIZED)
    dialog = _make_bare_dialog(tk_root, settings)

    calls = []
    monkeypatch.setattr(mod, "set_window_maximized", lambda window: calls.append("maximized"))

    dialog._apply_summary_startup_settings(1100, 750)

    assert calls == ["maximized"]


def test_remembered_maximized_geometry_has_priority(monkeypatch, tk_root):
    settings = _make_summary_settings(
        sizing_mode=SUMMARY_DIALOG_AUTOMATIC,
        remember_geometry=True,
        last_maximized=True,
    )
    dialog = _make_bare_dialog(tk_root, settings)

    calls = []
    monkeypatch.setattr(mod, "set_window_maximized", lambda window: calls.append("maximized"))

    dialog._apply_summary_startup_settings(1100, 750)

    assert calls == ["maximized"]


def test_remembered_normal_geometry_has_priority(monkeypatch, tk_root):
    settings = _make_summary_settings(
        sizing_mode=SUMMARY_DIALOG_MAXIMIZED,
        remember_geometry=True,
        last_geometry="1000x700+20+30",
        last_maximized=False,
    )
    dialog = _make_bare_dialog(tk_root, settings)

    normal_calls = []
    geometry_calls = []

    monkeypatch.setattr(mod, "geometry_is_visible", lambda *args: True)
    monkeypatch.setattr(mod, "set_window_normal", lambda window: normal_calls.append(True))
    dialog.geometry = geometry_calls.append

    dialog._apply_summary_startup_settings(1100, 750)

    assert normal_calls == [True]
    assert geometry_calls == ["1000x700+20+30"]


def test_invalid_remembered_geometry_falls_back_to_selected_mode(monkeypatch, tk_root):
    settings = _make_summary_settings(
        sizing_mode=SUMMARY_DIALOG_MAXIMIZED,
        remember_geometry=True,
        last_geometry="1000x700+20+30",
        last_maximized=False,
    )
    dialog = _make_bare_dialog(tk_root, settings)

    calls = []

    monkeypatch.setattr(mod, "geometry_is_visible", lambda *args: False)
    monkeypatch.setattr(mod, "set_window_maximized", lambda window: calls.append("maximized"))

    dialog._apply_summary_startup_settings(1100, 750)

    assert calls == ["maximized"]


def test_save_summary_geometry_does_nothing_when_disabled(monkeypatch, tk_root):
    settings = _make_summary_settings(remember_geometry=False)
    dialog = _make_bare_dialog(tk_root, settings)

    saved = []
    monkeypatch.setattr(mod, "save_display_settings", lambda value: saved.append(value))

    dialog._save_summary_geometry()

    assert saved == []


def test_save_summary_geometry_records_normal_geometry(monkeypatch, tk_root):
    settings = _make_summary_settings(remember_geometry=True)
    dialog = _make_bare_dialog(tk_root, settings)

    dialog.update_idletasks = lambda: None
    dialog.winfo_geometry = lambda: "1200x800+40+50"

    monkeypatch.setattr(mod, "window_is_maximized", lambda window: False)

    saved = []
    monkeypatch.setattr(mod, "save_display_settings", lambda value: saved.append(value))

    dialog._save_summary_geometry()

    summary = settings["summary_dialog"]

    assert summary["last_maximized"] is False
    assert summary["last_geometry"] == "1200x800+40+50"
    assert saved == [settings]


def test_save_summary_geometry_records_maximized_state(monkeypatch, tk_root):
    settings = _make_summary_settings(
        remember_geometry=True,
        last_geometry="1000x700+10+20",
    )
    dialog = _make_bare_dialog(tk_root, settings)

    dialog.update_idletasks = lambda: None
    monkeypatch.setattr(mod, "window_is_maximized", lambda window: True)
    monkeypatch.setattr(mod, "save_display_settings", lambda value: None)

    dialog._save_summary_geometry()

    assert settings["summary_dialog"]["last_maximized"] is True
    assert settings["summary_dialog"]["last_geometry"] == "1000x700+10+20"


def test_summary_configure_debounces_resize_events():
    dialog = mod.SummaryDialog.__new__(mod.SummaryDialog)
    dialog._summary_scale_after_id = None

    scheduled = []
    cancelled = []

    dialog.after = lambda delay, callback: scheduled.append((delay, callback)) or "after-id"
    dialog.after_cancel = cancelled.append

    event = SimpleNamespace(widget=dialog)

    dialog._on_summary_configure(event)

    assert dialog._summary_scale_after_id == "after-id"
    assert scheduled[0][0] == 50
    assert cancelled == []

    dialog._on_summary_configure(event)

    assert cancelled == ["after-id"]
    assert len(scheduled) == 2


def test_update_summary_scale_changes_scale_and_generates_event():
    dialog = mod.SummaryDialog.__new__(mod.SummaryDialog)

    dialog._summary_scale_after_id = "after-id"
    dialog._summary_reference_width = 1000
    dialog._summary_reference_height = 500
    dialog._warpsimlab_gui_scale = 1.0
    dialog._scaling_root = dialog

    dialog.winfo_width = lambda: 1500
    dialog.winfo_height = lambda: 750

    events = []
    dialog.event_generate = lambda name, **kwargs: events.append((name, kwargs))

    dialog._update_summary_scale()

    assert dialog._summary_scale_after_id is None
    assert dialog._warpsimlab_gui_scale == 1.5
    assert events == [("<<WARPSimLabScaleChanged>>", {"when": "tail"})]


def test_update_summary_scale_ignores_insignificant_change():
    dialog = mod.SummaryDialog.__new__(mod.SummaryDialog)

    dialog._summary_scale_after_id = "after-id"
    dialog._summary_reference_width = 1000
    dialog._summary_reference_height = 500
    dialog._warpsimlab_gui_scale = 1.0
    dialog._scaling_root = dialog

    dialog.winfo_width = lambda: 1005
    dialog.winfo_height = lambda: 502

    events = []
    dialog.event_generate = lambda name, **kwargs: events.append(name)

    dialog._update_summary_scale()

    assert dialog._summary_scale_after_id is None
    assert dialog._warpsimlab_gui_scale == 1.0
    assert events == []


def test_close_dialog_saves_before_destroy():
    dialog = mod.SummaryDialog.__new__(mod.SummaryDialog)

    calls = []
    dialog._save_summary_geometry = lambda: calls.append("save")
    dialog.destroy = lambda: calls.append("destroy")

    dialog._close_dialog()

    assert calls == ["save", "destroy"]


def test_portfolio_tab_builds(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_tab_dialog()

    tab = build_portfolio_tab(dialog, notebook)

    assert tab.winfo_exists()
    assert len(notebook.tabs()) == 1


def test_income_tab_builds(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_tab_dialog()

    tab = build_income_tab(dialog, notebook)

    assert tab.winfo_exists()
    assert len(notebook.tabs()) == 1


def test_cash_flow_tab_builds(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_tab_dialog()

    tab = build_cash_flow_tab(dialog, notebook)

    assert tab.winfo_exists()
    assert len(notebook.tabs()) == 1


def test_summary_tab_builds(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_tab_dialog()

    tab = build_summary_tab(dialog, notebook)

    assert tab.winfo_exists()
    assert len(notebook.tabs()) == 1