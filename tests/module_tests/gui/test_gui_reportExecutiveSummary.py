# test_gui_reportExecutiveSummary.py

from __future__ import annotations

import copy
import tkinter as tk
from types import SimpleNamespace

import pytest


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
def parent_gui():
    calls = []

    def edit_main_home():
        calls.append(("edit_main_home", None))

    def run_simulation_from_gui(*, sim_type):
        calls.append(("run_simulation_from_gui", sim_type))

    return SimpleNamespace(
        calls=calls,
        edit_main_home=edit_main_home,
        run_simulation_from_gui=run_simulation_from_gui,
    )


@pytest.fixture
def mod():
    from src.warpsimlab.gui import gui_reportExecutiveSummary as mod

    return mod


def test_normalize_options_uses_defaults_for_missing_values(tk_root, parent_gui, mod):
    options = {}

    frame = mod.ExecutiveSummaryReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    expected = copy.deepcopy(mod.ExecutiveSummaryReportFrame.DEFAULT_OPTIONS)
    assert frame.working_options == expected


def test_normalize_options_merges_nested_current_options(tk_root, parent_gui, mod):
    options = {
        "portfolio_visuals": {
            "include_normal_projection": False,
            "include_monte_carlo_analysis": True,
        },
        "income_visuals": {
            "include_subcategories_income": True,
        },
        "output_format": "PDF",
    }

    frame = mod.ExecutiveSummaryReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    assert frame.working_options["portfolio_visuals"]["include_normal_projection"] is False
    assert frame.working_options["portfolio_visuals"]["include_monte_carlo_analysis"] is True
    assert frame.working_options["portfolio_visuals"]["include_subcategories_projection"] is False
    assert frame.working_options["income_visuals"]["include_subcategories_income"] is True
    assert frame.working_options["output_format"] == "PDF"


def test_normalize_options_migrates_legacy_flat_options(tk_root, parent_gui, mod):
    options = {
        "include_portfolio_plot": False,
        "include_income_plot": False,
        "include_operating_balance_plot": True,
        "include_historical_windows": True,
        "include_monte_carlo": True,
        "include_simulation_summary": False,
        "include_assumptions_appendix": False,
        "output_format": "PDF",
    }

    frame = mod.ExecutiveSummaryReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    assert frame.working_options["portfolio_visuals"]["include_normal_projection"] is False
    assert frame.working_options["income_visuals"]["include_normal_income"] is False
    assert frame.working_options["cash_flow_visuals"]["include_cumulative_operating_balance"] is True
    assert frame.working_options["portfolio_visuals"]["include_historical_windows_analysis"] is True
    assert frame.working_options["portfolio_visuals"]["include_monte_carlo_analysis"] is True
    assert frame.working_options["include_simulation_summary"] is False
    assert frame.working_options["include_assumptions_appendix"] is False
    assert frame.working_options["output_format"] == "PDF"


def test_boolean_var_updates_working_options(tk_root, parent_gui, mod):
    options = {}

    frame = mod.ExecutiveSummaryReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    key = "portfolio_visuals.include_subcategories_projection"
    assert frame.working_options["portfolio_visuals"]["include_subcategories_projection"] is False

    frame.vars[key].set(True)
    tk_root.update_idletasks()

    assert frame.working_options["portfolio_visuals"]["include_subcategories_projection"] is True


def test_output_format_var_updates_working_options(tk_root, parent_gui, mod):
    options = {}

    frame = mod.ExecutiveSummaryReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    assert frame.working_options["output_format"] == "HTML"

    frame.vars["output_format"].set("PDF")
    tk_root.update_idletasks()

    assert frame.working_options["output_format"] == "PDF"


def test_apply_changes_writes_options_and_runs_summary_report(tk_root, parent_gui, mod):
    options = {}

    frame = mod.ExecutiveSummaryReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    frame.vars["include_simulation_summary"].set(False)
    frame.vars["output_format"].set("PDF")
    tk_root.update_idletasks()

    frame.apply_changes()

    assert options["include_simulation_summary"] is False
    assert options["output_format"] == "PDF"
    assert parent_gui.calls == [
        ("edit_main_home", None),
        ("run_simulation_from_gui", "summary_report"),
    ]


def test_apply_changes_deep_copies_working_options(tk_root, parent_gui, mod):
    options = {}

    frame = mod.ExecutiveSummaryReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    frame.apply_changes()

    frame.working_options["portfolio_visuals"]["include_normal_projection"] = False

    assert options["portfolio_visuals"]["include_normal_projection"] is True


def test_cancel_changes_restores_vars_from_original_options(tk_root, parent_gui, mod):
    options = {
        "include_simulation_summary": True,
        "portfolio_visuals": {
            "include_normal_projection": True,
        },
        "output_format": "HTML",
    }

    frame = mod.ExecutiveSummaryReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    frame.vars["include_simulation_summary"].set(False)
    frame.vars["portfolio_visuals.include_normal_projection"].set(False)
    frame.vars["output_format"].set("PDF")
    tk_root.update_idletasks()

    frame.cancel_changes()

    assert frame.vars["include_simulation_summary"].get() is True
    assert frame.vars["portfolio_visuals.include_normal_projection"].get() is True
    assert frame.vars["output_format"].get() == "HTML"
    assert frame.working_options["include_simulation_summary"] is True
    assert frame.working_options["portfolio_visuals"]["include_normal_projection"] is True
    assert frame.working_options["output_format"] == "HTML"
    assert parent_gui.calls == [("edit_main_home", None)]
