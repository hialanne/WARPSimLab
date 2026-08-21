from __future__ import annotations

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

    def edit_blank():
        calls.append(("edit_blank", None))

    def run_simulation_from_gui(*, sim_type):
        calls.append(("run_simulation_from_gui", sim_type))

    return SimpleNamespace(
        calls=calls,
        edit_blank=edit_blank,
        run_simulation_from_gui=run_simulation_from_gui,
    )


@pytest.fixture
def mod():
    from src.warpsimlab.gui import gui_reportSpendingComparison as mod

    return mod


def test_normalize_options_uses_defaults(tk_root, parent_gui, mod):
    frame = mod.SpendingComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame.working_options["spending_percentages"] == [
        70,
        80,
        90,
        100,
        110,
        120,
        130,
    ]
    assert frame.working_options["output"]["generate_html"] is True
    assert frame.working_options["output"]["open_report_in_browser"] is False


def test_normalize_options_preserves_supplied_values(tk_root, parent_gui, mod):
    options = {
        "spending_percentages": [80, 100, 120],
        "output": {
            "open_report_in_browser": True,
        },
    }

    frame = mod.SpendingComparisonReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    assert frame.working_options["spending_percentages"] == [80, 100, 120]
    assert frame.working_options["output"]["generate_html"] is True
    assert frame.working_options["output"]["open_report_in_browser"] is True


def test_format_percentage(tk_root, parent_gui, mod):
    frame = mod.SpendingComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame._format_percentage(100.0) == "100"
    assert frame._format_percentage(87.5) == "87.5"
    assert frame._format_percentage(87.25) == "87.25"


def test_parse_spending_percentages_sorts_and_ignores_blanks(tk_root, parent_gui, mod):
    frame = mod.SpendingComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    values = ["120", "", "80", "100", "", "", ""]

    for var, value in zip(frame.spending_vars, values):
        var.set(value)

    assert frame._parse_spending_percentages() == [80.0, 100.0, 120.0]


def test_parse_spending_percentages_rejects_invalid_number(tk_root, parent_gui, mod):
    frame = mod.SpendingComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    frame.spending_vars[0].set("bad")

    with pytest.raises(ValueError, match="not a valid spending percentage"):
        frame._parse_spending_percentages()


def test_parse_spending_percentages_rejects_zero(tk_root, parent_gui, mod):
    frame = mod.SpendingComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    frame.spending_vars[0].set("0")

    with pytest.raises(ValueError, match="greater than zero"):
        frame._parse_spending_percentages()


def test_parse_spending_percentages_requires_two_values(tk_root, parent_gui, mod):
    frame = mod.SpendingComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    for var in frame.spending_vars:
        var.set("")

    frame.spending_vars[0].set("100")

    with pytest.raises(ValueError, match="at least two"):
        frame._parse_spending_percentages()


def test_parse_spending_percentages_rejects_duplicates(tk_root, parent_gui, mod):
    frame = mod.SpendingComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    for var in frame.spending_vars:
        var.set("")

    frame.spending_vars[0].set("100")
    frame.spending_vars[1].set("100")

    with pytest.raises(ValueError, match="Duplicate spending percentages"):
        frame._parse_spending_percentages()


def test_parse_spending_percentages_requires_current_spending(tk_root, parent_gui, mod):
    frame = mod.SpendingComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    for var in frame.spending_vars:
        var.set("")

    frame.spending_vars[0].set("80")
    frame.spending_vars[1].set("120")

    with pytest.raises(ValueError, match="100% Current Spending"):
        frame._parse_spending_percentages()


def test_apply_changes_updates_options_and_runs_report(tk_root, parent_gui, mod):
    options = {}

    frame = mod.SpendingComparisonReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    values = ["120", "100", "80", "", "", "", ""]

    for var, value in zip(frame.spending_vars, values):
        var.set(value)

    frame.open_browser_var.set(True)

    frame.apply_changes()

    assert options["spending_percentages"] == [80.0, 100.0, 120.0]
    assert options["output"]["open_report_in_browser"] is True
    assert parent_gui.calls == [
        ("edit_blank", None),
        ("run_simulation_from_gui", "spending_comparison_report"),
    ]


def test_apply_changes_invalid_input_does_not_run_report(tk_root, parent_gui, mod, monkeypatch):
    options = {}
    errors = []

    frame = mod.SpendingComparisonReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    monkeypatch.setattr(
        mod.messagebox,
        "showerror",
        lambda title, message, parent=None: errors.append((title, message)),
    )

    for var in frame.spending_vars:
        var.set("")

    frame.spending_vars[0].set("80")
    frame.spending_vars[1].set("120")

    frame.apply_changes()

    assert len(errors) == 1
    assert "100% Current Spending" in errors[0][1]
    assert parent_gui.calls == []


def test_cancel_changes_restores_working_options_and_closes(tk_root, parent_gui, mod):
    options = {
        "spending_percentages": [80, 100, 120],
        "output": {
            "open_report_in_browser": True,
        },
    }

    frame = mod.SpendingComparisonReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    frame.working_options["spending_percentages"] = [50, 100, 150]

    frame.cancel_changes()

    assert frame.working_options["spending_percentages"] == [80, 100, 120]
    assert frame.working_options["output"]["open_report_in_browser"] is True
    assert parent_gui.calls == [("edit_blank", None)]