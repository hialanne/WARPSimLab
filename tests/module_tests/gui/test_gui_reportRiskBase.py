from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from src.warpsimlab.gui.gui_reportRiskBase import RiskReportBaseFrame


class DummyParentGUI:
    def __init__(self):
        self.edit_main_home_calls = 0
        self.run_calls = []

    def edit_main_home(self):
        self.edit_main_home_calls += 1

    def run_simulation_from_gui(self, *, sim_type):
        self.run_calls.append(sim_type)


class TestRiskReportFrame(RiskReportBaseFrame):
    REPORT_NAME = "Test Risk Report"
    RUN_SIM_TYPE = "test_risk_report"
    DESCRIPTION = "Test risk report description."
    METHOD_NOTE = "Test method note."

    DEFAULT_OPTIONS = {
        "general": {
            "include_executive_summary": True,
            "include_method_explanation": True,
        },
        "analysis": {
            "include_portfolio_projection": True,
            "include_portfolio_sustainability": True,
            "include_method_specific": True,
            "include_percentile_table": True,
        },
        "output": {
            "generate_html": True,
            "generate_csv": False,
        },
    }

    def _build_method_specific_analysis_options(self, parent, row):
        return self._add_check_path_to_frame(
            parent,
            "Include method specific analysis",
            ["analysis", "include_method_specific"],
            row,
        )

    def _build_method_specific_options(self, parent, row):
        row = self._add_section_label_to_frame(parent, "Method Specific", row)
        row = self._add_check_path_to_frame(
            parent,
            "Enable custom option",
            ["custom", "enabled"],
            row,
        )
        return row


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


def test_normalize_options_starts_from_defaults_and_applies_overrides():
    frame = object.__new__(TestRiskReportFrame)

    normalized = frame._normalize_options(
        {
            "analysis": {
                "include_percentile_table": False,
            },
            "output": {
                "generate_csv": True,
            },
        }
    )

    assert normalized == {
        "general": {
            "include_executive_summary": True,
            "include_method_explanation": True,
        },
        "analysis": {
            "include_portfolio_projection": True,
            "include_portfolio_sustainability": True,
            "include_method_specific": True,
            "include_percentile_table": False,
        },
        "output": {
            "generate_html": True,
            "generate_csv": True,
        },
    }


def test_normalize_options_ignores_non_dict_report_options():
    frame = object.__new__(TestRiskReportFrame)

    normalized = frame._normalize_options(None)

    assert normalized == TestRiskReportFrame.DEFAULT_OPTIONS
    assert normalized is not TestRiskReportFrame.DEFAULT_OPTIONS
    assert normalized["general"] is not TestRiskReportFrame.DEFAULT_OPTIONS["general"]


def test_normalize_options_deep_copies_defaults():
    frame = object.__new__(TestRiskReportFrame)

    normalized = frame._normalize_options({})

    normalized["general"]["include_executive_summary"] = False

    assert TestRiskReportFrame.DEFAULT_OPTIONS["general"]["include_executive_summary"] is True


def test_deep_update_preserves_unspecified_nested_values():
    frame = object.__new__(RiskReportBaseFrame)

    target = {
        "general": {
            "a": True,
            "b": True,
        },
        "output": {
            "html": True,
        },
    }

    source = {
        "general": {
            "b": False,
        },
        "new_section": {
            "x": 1,
        },
    }

    frame._deep_update(target, source)

    assert target == {
        "general": {
            "a": True,
            "b": False,
        },
        "output": {
            "html": True,
        },
        "new_section": {
            "x": 1,
        },
    }


def test_set_option_path_in_dict_creates_nested_dictionaries():
    frame = object.__new__(RiskReportBaseFrame)
    options = {}

    frame._set_option_path_in_dict(
        options,
        ["analysis", "nested", "enabled"],
        True,
    )

    assert options == {
        "analysis": {
            "nested": {
                "enabled": True,
            }
        }
    }


def test_get_option_path_returns_existing_value_or_default():
    frame = object.__new__(RiskReportBaseFrame)
    frame.working_options = {
        "analysis": {
            "include_percentile_table": True,
        }
    }

    assert frame._get_option_path(["analysis", "include_percentile_table"], False) is True
    assert frame._get_option_path(["analysis", "missing"], "fallback") == "fallback"
    assert frame._get_option_path(["missing", "value"], "fallback") == "fallback"


def test_set_option_path_updates_working_options():
    frame = object.__new__(RiskReportBaseFrame)
    frame.working_options = {}

    frame._set_option_path(["output", "generate_csv"], True)

    assert frame.working_options == {
        "output": {
            "generate_csv": True,
        }
    }


def test_path_key_joins_path_with_dots():
    frame = object.__new__(RiskReportBaseFrame)

    assert frame._path_key(["analysis", "include_percentile_table"]) == "analysis.include_percentile_table"


def test_constructor_builds_labels_and_checkbuttons(tk_root):
    parent_gui = DummyParentGUI()
    options = {}

    frame = TestRiskReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )
    frame.pack()

    labels = _label_texts(frame)
    checkbuttons = _checkbutton_texts(frame)

    assert "Test Risk Report" in labels
    assert "Test risk report description." in labels
    assert "Test method note." in labels
    assert "General" in labels
    assert "Analysis" in labels
    assert "Output" in labels
    assert "Method Specific" in labels
    assert "Desktop \\ WARPSimLab \\ Reports" in labels

    assert "Include executive summary" in checkbuttons
    assert "Include method explanation" in checkbuttons
    assert "Include Portfolio Projection" in checkbuttons
    assert "Include Portfolio Sustainability Analysis" in checkbuttons
    assert "Include method specific analysis" in checkbuttons
    assert "Include Percentile Portfolio Table" in checkbuttons
    assert "Generate HTML report" in checkbuttons
    assert "Generate CSV export" in checkbuttons
    assert "Enable custom option" in checkbuttons


def test_constructor_uses_explicit_title_when_provided(tk_root):
    parent_gui = DummyParentGUI()

    frame = TestRiskReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
        title="Explicit Title",
    )
    frame.pack()

    labels = _label_texts(frame)

    assert "Explicit Title" in labels
    assert "Test Risk Report" not in labels


def test_constructor_normalizes_report_options_and_creates_vars(tk_root):
    parent_gui = DummyParentGUI()

    frame = TestRiskReportFrame(
        tk_root,
        report_options={
            "output": {
                "generate_csv": True,
            },
            "custom": {
                "enabled": True,
            },
        },
        parent_gui=parent_gui,
    )

    assert frame.working_options["output"]["generate_html"] is True
    assert frame.working_options["output"]["generate_csv"] is True
    assert frame.working_options["custom"]["enabled"] is True

    expected_var_keys = {
        "general.include_executive_summary",
        "general.include_method_explanation",
        "analysis.include_portfolio_projection",
        "analysis.include_portfolio_sustainability",
        "analysis.include_method_specific",
        "analysis.include_percentile_table",
        "output.generate_html",
        "output.generate_csv",
        "custom.enabled",
    }

    assert set(frame.vars) == expected_var_keys
    assert frame.vars["output.generate_csv"].get() is True
    assert frame.vars["custom.enabled"].get() is True


def test_checkbox_trace_updates_working_options(tk_root):
    parent_gui = DummyParentGUI()

    frame = TestRiskReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame.working_options["output"]["generate_csv"] is False

    frame.vars["output.generate_csv"].set(True)
    tk_root.update_idletasks()

    assert frame.working_options["output"]["generate_csv"] is True


def test_apply_changes_copies_working_options_and_runs_report(tk_root):
    parent_gui = DummyParentGUI()
    options = {
        "output": {
            "generate_csv": False,
        }
    }

    frame = TestRiskReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    frame.vars["output.generate_csv"].set(True)
    tk_root.update_idletasks()

    frame.apply_changes()

    assert options["output"]["generate_csv"] is True
    assert parent_gui.edit_main_home_calls == 1
    assert parent_gui.run_calls == ["test_risk_report"]

    # Confirm caller options are not sharing nested dicts with working_options.
    frame.working_options["output"]["generate_csv"] = False
    assert options["output"]["generate_csv"] is True


def test_cancel_changes_resets_working_options_and_vars_without_running_report(tk_root):
    parent_gui = DummyParentGUI()
    options = {
        "output": {
            "generate_csv": False,
        }
    }

    frame = TestRiskReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    frame.vars["output.generate_csv"].set(True)
    tk_root.update_idletasks()

    assert frame.working_options["output"]["generate_csv"] is True

    frame.cancel_changes()

    assert frame.working_options["output"]["generate_csv"] is False
    assert frame.vars["output.generate_csv"].get() is False

    assert options["output"]["generate_csv"] is False
    assert parent_gui.edit_main_home_calls == 1
    assert parent_gui.run_calls == []


def test_base_method_specific_hooks_return_row_unchanged():
    frame = object.__new__(RiskReportBaseFrame)
    parent = object()

    assert frame._build_method_specific_options(parent, 3) == 3
    assert frame._build_method_specific_analysis_options(parent, 4) == 4