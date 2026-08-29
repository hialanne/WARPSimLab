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
        husband=SimpleNamespace(
            age=60,
            retire_age=67,
            ss_age=67,
        ),
        wife=SimpleNamespace(
            age=58,
            retire_age=67,
            ss_age=65,
        ),
        simulation_controls={
            "enable_second_person": True,
        },
    )


@pytest.fixture
def mod():
    from src.warpsimlab.gui.reports import gui_reportRetirementSSComparison as mod

    return mod


def test_normalize_options_uses_defaults(tk_root, parent_gui, mod):
    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame.working_options["retirement_ages"] == [62, 64, 66, 68, 70]
    assert frame.working_options["social_security_ages"] == [62, 64, 66, 68, 70]
    assert frame.working_options["output"]["generate_html"] is True
    assert frame.working_options["output"]["open_report_in_browser"] is False


def test_normalize_options_preserves_supplied_values(tk_root, parent_gui, mod):
    options = {
        "retirement_ages": [60, 65, 70],
        "social_security_ages": [62, 67, 70],
        "output": {
            "open_report_in_browser": True,
        },
    }

    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    assert frame.working_options["retirement_ages"] == [60, 65, 70]
    assert frame.working_options["social_security_ages"] == [62, 67, 70]
    assert frame.working_options["output"]["generate_html"] is True
    assert frame.working_options["output"]["open_report_in_browser"] is True


def test_years_until(tk_root, parent_gui, mod):
    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame._years_until(60, 67) == 7
    assert frame._years_until(58, 65) == 7


def test_household_retirement_age_single_person(tk_root, parent_gui, mod):
    parent_gui.simulation_controls["enable_second_person"] = False

    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame.current_retirement_age == 67


def test_household_retirement_age_uses_event_occurring_last(tk_root, parent_gui, mod):
    parent_gui.husband = SimpleNamespace(
        age=60,
        retire_age=67,
        ss_age=67,
    )

    parent_gui.wife = SimpleNamespace(
        age=50,
        retire_age=60,
        ss_age=62,
    )

    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    # Husband retires in 7 years.
    # Wife retires in 10 years.
    assert frame.current_retirement_age == 60


def test_household_retirement_age_tie_uses_larger_age(tk_root, parent_gui, mod):
    parent_gui.husband = SimpleNamespace(
        age=60,
        retire_age=67,
        ss_age=67,
    )

    parent_gui.wife = SimpleNamespace(
        age=55,
        retire_age=62,
        ss_age=62,
    )

    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame.current_retirement_age == 67


def test_household_ss_age_single_person(tk_root, parent_gui, mod):
    parent_gui.simulation_controls["enable_second_person"] = False

    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame.current_ss_age == 67


def test_household_ss_age_uses_event_occurring_last(tk_root, parent_gui, mod):
    parent_gui.husband = SimpleNamespace(
        age=60,
        retire_age=67,
        ss_age=67,
    )

    parent_gui.wife = SimpleNamespace(
        age=50,
        retire_age=60,
        ss_age=62,
    )

    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    # Husband starts SS in 7 years.
    # Wife starts SS in 12 years.
    assert frame.current_ss_age == 62


def test_household_ss_age_tie_uses_larger_age(tk_root, parent_gui, mod):
    parent_gui.husband = SimpleNamespace(
        age=60,
        retire_age=67,
        ss_age=67,
    )

    parent_gui.wife = SimpleNamespace(
        age=55,
        retire_age=62,
        ss_age=62,
    )

    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame.current_ss_age == 67


def test_parse_age_values_sorts_and_ignores_blanks(tk_root, parent_gui, mod):
    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    values = ["70", "", "62", "67", ""]

    for var, value in zip(frame.social_security_age_vars, values):
        var.set(value)

    result = frame._parse_age_values(
        frame.social_security_age_vars,
        "Social Security",
        62,
        70,
    )

    assert result == [62, 67, 70]


def test_parse_age_values_rejects_non_integer(tk_root, parent_gui, mod):
    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    frame.social_security_age_vars[0].set("bad")

    with pytest.raises(ValueError, match="not a valid social security age"):
        frame._parse_age_values(
            frame.social_security_age_vars,
            "Social Security",
            62,
            70,
        )


def test_parse_age_values_rejects_out_of_range(tk_root, parent_gui, mod):
    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    frame.social_security_age_vars[0].set("71")

    with pytest.raises(ValueError, match="between 62 and 70"):
        frame._parse_age_values(
            frame.social_security_age_vars,
            "Social Security",
            62,
            70,
        )


def test_parse_age_values_requires_two_values(tk_root, parent_gui, mod):
    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    for var in frame.retirement_age_vars:
        var.set("")

    frame.retirement_age_vars[0].set("67")

    with pytest.raises(ValueError, match="at least two retirement ages"):
        frame._parse_age_values(
            frame.retirement_age_vars,
            "Retirement",
            55,
            75,
        )


def test_parse_age_values_rejects_duplicates(tk_root, parent_gui, mod):
    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    for var in frame.retirement_age_vars:
        var.set("")

    frame.retirement_age_vars[0].set("67")
    frame.retirement_age_vars[1].set("67")

    with pytest.raises(ValueError, match="Duplicate retirement ages"):
        frame._parse_age_values(
            frame.retirement_age_vars,
            "Retirement",
            55,
            75,
        )


def test_apply_changes_updates_options_and_runs_report(tk_root, parent_gui, mod):
    options = {}

    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    retirement_values = ["70", "60", "65", "", ""]
    ss_values = ["70", "62", "67", "", ""]

    for var, value in zip(frame.retirement_age_vars, retirement_values):
        var.set(value)

    for var, value in zip(frame.social_security_age_vars, ss_values):
        var.set(value)

    frame.open_browser_var.set(True)

    frame.apply_changes()

    assert options["retirement_ages"] == [60, 65, 70]
    assert options["social_security_ages"] == [62, 67, 70]
    assert options["output"]["open_report_in_browser"] is True

    assert parent_gui.calls == [
        ("edit_blank", None),
        ("run_simulation_from_gui", "retirement_ss_comparison_report"),
    ]


def test_apply_changes_invalid_retirement_age_does_not_run_report(
    tk_root,
    parent_gui,
    mod,
    monkeypatch,
):
    options = {}
    errors = []

    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    monkeypatch.setattr(
        mod.messagebox,
        "showerror",
        lambda title, message, parent=None: errors.append((title, message)),
    )

    frame.retirement_age_vars[0].set("-1")

    frame.apply_changes()

    assert len(errors) == 1
    assert "between 0 and 100" in errors[0][1]
    assert parent_gui.calls == []


def test_apply_changes_invalid_ss_age_does_not_run_report(
    tk_root,
    parent_gui,
    mod,
    monkeypatch,
):
    options = {}
    errors = []

    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    for var in frame.retirement_age_vars:
        var.set("")

    frame.retirement_age_vars[0].set("60")
    frame.retirement_age_vars[1].set("70")

    for var in frame.social_security_age_vars:
        var.set("")

    frame.social_security_age_vars[0].set("61")
    frame.social_security_age_vars[1].set("67")

    frame.retirement_age_vars[0].set("60")
    frame.retirement_age_vars[1].set("70")

    frame.social_security_age_vars[0].set("61")

    monkeypatch.setattr(
        mod.messagebox,
        "showerror",
        lambda title, message, parent=None: errors.append((title, message)),
    )

    frame.apply_changes()

    assert len(errors) == 1
    assert "between 62 and 70" in errors[0][1]
    assert parent_gui.calls == []


def test_cancel_changes_restores_working_options_and_closes(tk_root, parent_gui, mod):
    options = {
        "retirement_ages": [60, 65, 70],
        "social_security_ages": [62, 67, 70],
        "output": {
            "open_report_in_browser": True,
        },
    }

    frame = mod.RetirementSSComparisonReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    frame.working_options["retirement_ages"] = [55, 75]
    frame.working_options["social_security_ages"] = [62, 70]

    frame.cancel_changes()

    assert frame.working_options["retirement_ages"] == [60, 65, 70]
    assert frame.working_options["social_security_ages"] == [62, 67, 70]
    assert frame.working_options["output"]["open_report_in_browser"] is True
    assert parent_gui.calls == [("edit_blank", None)]