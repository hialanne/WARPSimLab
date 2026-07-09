from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from src.warpsimlab.gui.gui_reportTaxes import TaxReportFrame


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


def test_default_options_have_expected_output_and_sections():
    assert TaxReportFrame.DEFAULT_OPTIONS == {
        "output": {
            "generate_html": True,
            "generate_csv": False,
        },
        "sections": {
            "include_roth_analysis": True,
            "include_hsa_analysis": True,
            "include_rmd_analysis": True,
            "include_educational_commentary": True,
        },
    }


def test_normalize_options_starts_from_defaults_and_applies_known_section_overrides():
    frame = object.__new__(TaxReportFrame)

    normalized = frame._normalize_options(
        {
            "output": {
                "generate_csv": True,
            },
            "sections": {
                "include_hsa_analysis": False,
                "include_educational_commentary": False,
            },
        }
    )

    assert normalized == {
        "output": {
            "generate_html": True,
            "generate_csv": True,
        },
        "sections": {
            "include_roth_analysis": True,
            "include_hsa_analysis": False,
            "include_rmd_analysis": True,
            "include_educational_commentary": False,
        },
    }


def test_normalize_options_ignores_non_dict_input():
    frame = object.__new__(TaxReportFrame)

    normalized = frame._normalize_options(None)

    assert normalized == TaxReportFrame.DEFAULT_OPTIONS
    assert normalized is not TaxReportFrame.DEFAULT_OPTIONS
    assert normalized["output"] is not TaxReportFrame.DEFAULT_OPTIONS["output"]
    assert normalized["sections"] is not TaxReportFrame.DEFAULT_OPTIONS["sections"]


def test_normalize_options_ignores_unknown_top_level_sections():
    frame = object.__new__(TaxReportFrame)

    normalized = frame._normalize_options(
        {
            "output": {
                "generate_csv": True,
            },
            "unknown": {
                "value": True,
            },
        }
    )

    assert "unknown" not in normalized
    assert normalized["output"]["generate_csv"] is True


def test_normalize_options_ignores_non_dict_known_sections():
    frame = object.__new__(TaxReportFrame)

    normalized = frame._normalize_options(
        {
            "output": "bad",
            "sections": None,
        }
    )

    assert normalized == TaxReportFrame.DEFAULT_OPTIONS


def test_normalize_options_deep_copies_defaults():
    frame = object.__new__(TaxReportFrame)

    normalized = frame._normalize_options({})

    normalized["output"]["generate_html"] = False
    normalized["sections"]["include_roth_analysis"] = False

    assert TaxReportFrame.DEFAULT_OPTIONS["output"]["generate_html"] is True
    assert TaxReportFrame.DEFAULT_OPTIONS["sections"]["include_roth_analysis"] is True


def test_set_option_path_in_dict_creates_nested_dictionaries():
    frame = object.__new__(TaxReportFrame)
    options = {}

    frame._set_option_path_in_dict(
        options,
        ["sections", "include_roth_analysis"],
        False,
    )

    assert options == {
        "sections": {
            "include_roth_analysis": False,
        }
    }


def test_get_option_path_returns_existing_value_or_default():
    frame = object.__new__(TaxReportFrame)
    frame.working_options = {
        "output": {
            "generate_html": True,
        }
    }

    assert frame._get_option_path(["output", "generate_html"], False) is True
    assert frame._get_option_path(["output", "generate_csv"], "fallback") == "fallback"
    assert frame._get_option_path(["missing", "value"], "fallback") == "fallback"


def test_set_option_path_updates_working_options():
    frame = object.__new__(TaxReportFrame)
    frame.working_options = {}

    frame._set_option_path(["output", "generate_csv"], True)

    assert frame.working_options == {
        "output": {
            "generate_csv": True,
        }
    }


def test_path_key_joins_path_with_dots():
    frame = object.__new__(TaxReportFrame)

    assert frame._path_key(["sections", "include_hsa_analysis"]) == "sections.include_hsa_analysis"


def test_constructor_builds_labels_and_checkbuttons(tk_root):
    parent_gui = DummyParentGUI()

    frame = TaxReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )
    frame.pack()

    labels = _label_texts(frame)
    checkbuttons = _checkbutton_texts(frame)

    assert "Tax Report" in labels
    assert (
        "Select the outputs and optional sections to include in the Tax Report. "
        "The report explains how taxes evolve over the simulation lifetime."
    ) in labels
    assert (
        "Tax calculation settings (Federal, State, Payroll, Filing Status, etc.) "
        "are configured under Cash Flow - Taxes."
    ) in labels
    assert "Desktop \\ WARPSimLab \\ Reports" in labels
    assert "Output" in labels
    assert "Sections" in labels

    assert "HTML Report" in checkbuttons
    assert "CSV Export" in checkbuttons
    assert "Include Roth Analysis" in checkbuttons
    assert "Include HSA Analysis" in checkbuttons
    assert "Include RMD Analysis" in checkbuttons
    assert "Include Educational Commentary" in checkbuttons


def test_constructor_uses_explicit_title(tk_root):
    parent_gui = DummyParentGUI()

    frame = TaxReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
        title="Explicit Tax Title",
    )
    frame.pack()

    labels = _label_texts(frame)

    assert "Explicit Tax Title" in labels
    assert "Tax Report" not in labels


def test_constructor_normalizes_report_options_and_creates_vars(tk_root):
    parent_gui = DummyParentGUI()

    frame = TaxReportFrame(
        tk_root,
        report_options={
            "output": {
                "generate_csv": True,
            },
            "sections": {
                "include_hsa_analysis": False,
            },
        },
        parent_gui=parent_gui,
    )

    assert frame.working_options["output"]["generate_html"] is True
    assert frame.working_options["output"]["generate_csv"] is True
    assert frame.working_options["sections"]["include_roth_analysis"] is True
    assert frame.working_options["sections"]["include_hsa_analysis"] is False

    expected_var_keys = {
        "output.generate_html",
        "output.generate_csv",
        "sections.include_roth_analysis",
        "sections.include_hsa_analysis",
        "sections.include_rmd_analysis",
        "sections.include_educational_commentary",
    }

    assert set(frame.vars) == expected_var_keys
    assert frame.vars["output.generate_csv"].get() is True
    assert frame.vars["sections.include_hsa_analysis"].get() is False


def test_checkbox_trace_updates_working_options(tk_root):
    parent_gui = DummyParentGUI()

    frame = TaxReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame.working_options["output"]["generate_csv"] is False

    frame.vars["output.generate_csv"].set(True)
    tk_root.update_idletasks()

    assert frame.working_options["output"]["generate_csv"] is True


def test_apply_changes_copies_working_options_and_runs_tax_report(tk_root):
    parent_gui = DummyParentGUI()
    options = {
        "output": {
            "generate_csv": False,
        }
    }

    frame = TaxReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    frame.vars["output.generate_csv"].set(True)
    tk_root.update_idletasks()

    frame.apply_changes()

    assert options["output"]["generate_csv"] is True
    assert parent_gui.edit_main_home_calls == 1
    assert parent_gui.run_calls == ["tax_report"]

    # Confirm caller options do not share nested dicts with working_options.
    frame.working_options["output"]["generate_csv"] = False
    assert options["output"]["generate_csv"] is True


def test_cancel_changes_resets_working_options_and_vars_without_running_report(tk_root):
    parent_gui = DummyParentGUI()
    options = {
        "output": {
            "generate_csv": False,
        },
        "sections": {
            "include_roth_analysis": True,
        },
    }

    frame = TaxReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    frame.vars["output.generate_csv"].set(True)
    frame.vars["sections.include_roth_analysis"].set(False)
    tk_root.update_idletasks()

    assert frame.working_options["output"]["generate_csv"] is True
    assert frame.working_options["sections"]["include_roth_analysis"] is False

    frame.cancel_changes()

    assert frame.working_options["output"]["generate_csv"] is False
    assert frame.working_options["sections"]["include_roth_analysis"] is True
    assert frame.vars["output.generate_csv"].get() is False
    assert frame.vars["sections.include_roth_analysis"].get() is True

    assert options["output"]["generate_csv"] is False
    assert options["sections"]["include_roth_analysis"] is True

    assert parent_gui.edit_main_home_calls == 1
    assert parent_gui.run_calls == []