from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from src.warpsimlab.gui.gui_reportYearByYearDetails import (
    YearByYearDetailsReportFrame,
)


class DummyParentGUI:
    def __init__(self):
        self.edit_main_home_calls = 0
        self.run_calls = []

    def edit_main_home(self):
        self.edit_main_home_calls += 1

    def run_simulation_from_gui(self, *, sim_type):
        self.run_calls.append(sim_type)


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk not available: {e}")

    root.withdraw()
    yield root
    root.destroy()


def _label_texts(widget: tk.Misc) -> list[str]:
    out = []

    def walk(parent):
        for child in parent.winfo_children():
            if isinstance(child, ttk.Label):
                try:
                    out.append(child.cget("text"))
                except tk.TclError:
                    pass
            walk(child)

    walk(widget)
    return out


def _checkbutton_texts(widget: tk.Misc) -> list[str]:
    out = []

    def walk(parent):
        for child in parent.winfo_children():
            if isinstance(child, ttk.Checkbutton):
                try:
                    out.append(child.cget("text"))
                except tk.TclError:
                    pass
            walk(child)

    walk(widget)
    return out


def _radiobutton_texts(widget: tk.Misc) -> list[str]:
    out = []

    def walk(parent):
        for child in parent.winfo_children():
            if isinstance(child, ttk.Radiobutton):
                try:
                    out.append(child.cget("text"))
                except tk.TclError:
                    pass
            walk(child)

    walk(widget)
    return out


def test_default_options_have_expected_values():
    assert YearByYearDetailsReportFrame.DEFAULT_OPTIONS == {
        "generate_html": True,
        "generate_csv": True,
        "table_detail": "Compact",
        "insert_5_year_breaks": True,
    }


def test_normalize_options_starts_from_defaults_and_applies_known_overrides():
    frame = object.__new__(YearByYearDetailsReportFrame)

    normalized = frame._normalize_options(
        {
            "generate_csv": False,
            "table_detail": "Detailed",
            "insert_5_year_breaks": False,
        }
    )

    assert normalized == {
        "generate_html": True,
        "generate_csv": False,
        "table_detail": "Detailed",
        "insert_5_year_breaks": False,
    }


def test_normalize_options_ignores_unknown_keys():
    frame = object.__new__(YearByYearDetailsReportFrame)

    normalized = frame._normalize_options(
        {
            "generate_html": False,
            "unknown": True,
        }
    )

    assert normalized == {
        "generate_html": False,
        "generate_csv": True,
        "table_detail": "Compact",
        "insert_5_year_breaks": True,
    }
    assert "unknown" not in normalized


def test_normalize_options_ignores_non_dict_input():
    frame = object.__new__(YearByYearDetailsReportFrame)

    normalized = frame._normalize_options(None)

    assert normalized == YearByYearDetailsReportFrame.DEFAULT_OPTIONS
    assert normalized is not YearByYearDetailsReportFrame.DEFAULT_OPTIONS


def test_normalize_options_deep_copies_defaults():
    frame = object.__new__(YearByYearDetailsReportFrame)

    normalized = frame._normalize_options({})
    normalized["generate_html"] = False

    assert YearByYearDetailsReportFrame.DEFAULT_OPTIONS["generate_html"] is True


def test_set_option_path_in_dict_creates_nested_dictionaries():
    frame = object.__new__(YearByYearDetailsReportFrame)
    options = {}

    frame._set_option_path_in_dict(
        options,
        ["nested", "enabled"],
        True,
    )

    assert options == {
        "nested": {
            "enabled": True,
        }
    }


def test_get_option_path_returns_existing_value_or_default():
    frame = object.__new__(YearByYearDetailsReportFrame)
    frame.working_options = {
        "generate_html": True,
        "table_detail": "Detailed",
    }

    assert frame._get_option_path(["generate_html"], False) is True
    assert frame._get_option_path(["table_detail"], "Compact") == "Detailed"
    assert frame._get_option_path(["missing"], "fallback") == "fallback"
    assert frame._get_option_path(["missing", "nested"], "fallback") == "fallback"


def test_set_option_path_updates_working_options():
    frame = object.__new__(YearByYearDetailsReportFrame)
    frame.working_options = {}

    frame._set_option_path(["generate_csv"], False)

    assert frame.working_options == {
        "generate_csv": False,
    }


def test_path_key_joins_path_with_dots():
    frame = object.__new__(YearByYearDetailsReportFrame)

    assert frame._path_key(["table_detail"]) == "table_detail"
    assert frame._path_key(["nested", "enabled"]) == "nested.enabled"


def test_constructor_builds_labels_checkbuttons_and_radiobuttons(tk_root):
    parent_gui = DummyParentGUI()

    frame = YearByYearDetailsReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )
    frame.pack()

    labels = _label_texts(frame)
    checkbuttons = _checkbutton_texts(frame)
    radiobuttons = _radiobutton_texts(frame)

    assert "Year-by-Year Details" in labels
    assert (
        "Select the outputs and table detail level for the "
        "Year-by-Year Details report."
    ) in labels
    assert "Desktop \\ WARPSimLab \\ Reports" in labels
    assert "Output" in labels
    assert "Layout" in labels
    assert "Table Detail" in labels
    assert (
        "Compact: fewer high-level columns.\n"
        "Detailed: expanded income, tax, cash-flow, and portfolio columns."
    ) in labels

    assert "Generate HTML report" in checkbuttons
    assert "Generate CSV export" in checkbuttons
    assert "Insert visual break every 5 years" in checkbuttons

    assert "Compact" in radiobuttons
    assert "Detailed" in radiobuttons


def test_constructor_uses_explicit_title(tk_root):
    parent_gui = DummyParentGUI()

    frame = YearByYearDetailsReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
        title="Explicit Yearly Title",
    )
    frame.pack()

    labels = _label_texts(frame)

    assert "Explicit Yearly Title" in labels
    assert "Year-by-Year Details" not in labels


def test_constructor_normalizes_report_options_and_creates_vars(tk_root):
    parent_gui = DummyParentGUI()

    frame = YearByYearDetailsReportFrame(
        tk_root,
        report_options={
            "generate_csv": False,
            "table_detail": "Detailed",
            "insert_5_year_breaks": False,
        },
        parent_gui=parent_gui,
    )

    assert frame.working_options == {
        "generate_html": True,
        "generate_csv": False,
        "table_detail": "Detailed",
        "insert_5_year_breaks": False,
    }

    expected_var_keys = {
        "generate_html",
        "generate_csv",
        "insert_5_year_breaks",
        "table_detail",
    }

    assert set(frame.vars) == expected_var_keys

    assert frame.vars["generate_html"].get() is True
    assert frame.vars["generate_csv"].get() is False
    assert frame.vars["insert_5_year_breaks"].get() is False
    assert frame.vars["table_detail"].get() == "Detailed"


def test_checkbox_trace_updates_working_options(tk_root):
    parent_gui = DummyParentGUI()

    frame = YearByYearDetailsReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame.working_options["generate_csv"] is True

    frame.vars["generate_csv"].set(False)
    tk_root.update_idletasks()

    assert frame.working_options["generate_csv"] is False


def test_table_detail_trace_updates_working_options(tk_root):
    parent_gui = DummyParentGUI()

    frame = YearByYearDetailsReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame.working_options["table_detail"] == "Compact"

    frame.vars["table_detail"].set("Detailed")
    tk_root.update_idletasks()

    assert frame.working_options["table_detail"] == "Detailed"


def test_apply_changes_copies_working_options_and_runs_year_by_year_report(tk_root):
    parent_gui = DummyParentGUI()
    options = {
        "generate_csv": True,
        "table_detail": "Compact",
    }

    frame = YearByYearDetailsReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    frame.vars["generate_csv"].set(False)
    frame.vars["table_detail"].set("Detailed")
    tk_root.update_idletasks()

    frame.apply_changes()

    assert options == {
        "generate_html": True,
        "generate_csv": False,
        "table_detail": "Detailed",
        "insert_5_year_breaks": True,
    }

    assert parent_gui.edit_main_home_calls == 1
    assert parent_gui.run_calls == ["year_by_year_report"]

    frame.working_options["generate_csv"] = True
    assert options["generate_csv"] is False


def test_cancel_changes_resets_working_options_and_vars_without_running_report(tk_root):
    parent_gui = DummyParentGUI()
    options = {
        "generate_csv": True,
        "table_detail": "Compact",
        "insert_5_year_breaks": True,
    }

    frame = YearByYearDetailsReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    frame.vars["generate_csv"].set(False)
    frame.vars["table_detail"].set("Detailed")
    frame.vars["insert_5_year_breaks"].set(False)
    tk_root.update_idletasks()

    assert frame.working_options["generate_csv"] is False
    assert frame.working_options["table_detail"] == "Detailed"
    assert frame.working_options["insert_5_year_breaks"] is False

    frame.cancel_changes()

    assert frame.working_options == {
        "generate_html": True,
        "generate_csv": True,
        "table_detail": "Compact",
        "insert_5_year_breaks": True,
    }

    assert frame.vars["generate_html"].get() is True
    assert frame.vars["generate_csv"].get() is True
    assert frame.vars["table_detail"].get() == "Compact"
    assert frame.vars["insert_5_year_breaks"].get() is True

    assert options == {
        "generate_csv": True,
        "table_detail": "Compact",
        "insert_5_year_breaks": True,
    }

    assert parent_gui.edit_main_home_calls == 1
    assert parent_gui.run_calls == []