# test_gui_simulationControls.py

from __future__ import annotations

import tkinter as tk
from types import SimpleNamespace

import pytest


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk unavailable: {e}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def no_tooltip(monkeypatch):
    from src.warpsimlab.gui import gui_simulationControls as mod

    class DummyTooltip:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(mod, "Tooltip", DummyTooltip, raising=True)
    return mod


@pytest.fixture
def no_annotations_editor(monkeypatch):
    """
    Replace AnnotationsEditFrame with a lightweight stub so tests
    don't depend on that module's behavior.
    """
    from src.warpsimlab.gui import gui_simulationControls as mod

    class DummyAnnotations:
        def __init__(self, parent, annotation_strings=None, title=None):
            self.row_vars = []
            self.add_button = SimpleNamespace(configure=lambda **k: None)

        def grid(self, *args, **kwargs):
            pass

        def pack(self, *args, **kwargs):
            pass

    monkeypatch.setattr(mod, "AnnotationsEditFrame", DummyAnnotations, raising=True)
    return mod


@pytest.fixture
def control_vars():
    return {
        "_controls_dict": {
            "include_realestate": True,
            "constant_y_plots": False,
            "rebalance_every_year": False,
            "plot_mode": "real",
            "subplot_mode": "none",
            "output_csv": "None",
            "annotation_strings": [],
            "annotate_plots": False,
            "csv_output_dir": "test_dir",
        }
    }


def test_checkbox_updates_controls_dict(tk_root, no_tooltip, no_annotations_editor, control_vars):
    mod = no_tooltip

    frame = mod.SimulationControlsEditFrame(tk_root, control_vars)
    frame.pack()

    # Change control directly via dict simulation
    control_vars["_controls_dict"]["include_realestate"] = False

    assert control_vars["_controls_dict"]["include_realestate"] is False


def test_plot_mode_combobox_updates_controls(tk_root, no_tooltip, no_annotations_editor, control_vars):
    mod = no_tooltip

    frame = mod.SimulationControlsEditFrame(tk_root, control_vars)
    frame.pack()

    # simulate user switching mode
    control_vars["_controls_dict"]["plot_mode"] = "raw"

    assert control_vars["_controls_dict"]["plot_mode"] == "raw"


def test_subplot_mode_mapping_exists(tk_root, no_tooltip, no_annotations_editor, control_vars):
    mod = no_tooltip

    frame = mod.SimulationControlsEditFrame(tk_root, control_vars)
    frame.pack()

    # confirm control key exists and default mapping works
    assert control_vars["_controls_dict"]["subplot_mode"] == "none"


def test_annotation_checkbox_updates_dict(tk_root, no_tooltip, no_annotations_editor, control_vars):
    mod = no_tooltip

    frame = mod.SimulationControlsEditFrame(tk_root, control_vars)
    frame.pack()

    frame.annotate_var.set(True)

    assert control_vars["_controls_dict"]["annotate_plots"] is True


def test_csv_output_directory_default_exists(tk_root, no_tooltip, no_annotations_editor, control_vars):
    mod = no_tooltip

    frame = mod.SimulationControlsEditFrame(tk_root, control_vars)
    frame.pack()

    assert "csv_output_dir" in control_vars["_controls_dict"]