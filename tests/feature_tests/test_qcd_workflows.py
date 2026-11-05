"""Configured charity survives financial-file and GUI configuration boundaries."""

import copy
import json

from src.warpsimlab.gui import gui_io
from src.warpsimlab.sim.simulation import run_pipeline
from tests.architectural_helpers import assert_tree_equal
from tests.feature_tests.workflow_helpers import inputs_from_gui, make_gui


def test_qcd_settings_round_trip_and_run_without_aliasing(tmp_path, monkeypatch):
    gui = make_gui(tmp_path, always_use_expense_mode=True)
    gui.qcd_settings["husband"].update(enabled=True, amount=5_000, start_age=71, end_age=75)
    gui.qcd_settings["wife"].update(enabled=True, mode="Percent of RMD", percent=50, start_age=73)
    settings = copy.deepcopy(gui.qcd_settings)
    expected = run_pipeline(**inputs_from_gui(gui))["core"]
    assert expected["qcd_husband"].sum() > 0
    assert expected["qcd_wife"].sum() > 0
    path = tmp_path / "qcd_plan.json"
    errors = []
    monkeypatch.setattr(gui_io.filedialog, "asksaveasfilename", lambda **kwargs: str(path))
    monkeypatch.setattr(gui_io.messagebox, "showinfo", lambda *args, **kwargs: None)
    monkeypatch.setattr(gui_io.messagebox, "showerror", lambda *args, **kwargs: errors.append(args))
    gui.save_values_to_json()
    document = json.loads(path.read_text())
    assert document["QCD_SETTINGS"] == settings
    assert document["INCLUDE_RMD"] is True
    reloaded = make_gui(tmp_path, always_use_expense_mode=True)
    reloaded._load_from_json(path)
    assert errors == []
    assert reloaded.qcd_settings == settings
    config = inputs_from_gui(reloaded)["sim_config"]
    assert config.qcd_settings == settings
    config.qcd_settings["husband"]["amount"] = 1
    assert reloaded.qcd_settings == settings
    assert gui.qcd_settings == settings
    assert_tree_equal(run_pipeline(**inputs_from_gui(reloaded))["core"], expected)
