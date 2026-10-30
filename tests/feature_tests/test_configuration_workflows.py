"""Saved financial plans remain executable across edits, modes and failures."""

import copy
import json
from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.gui import gui_io
from src.warpsimlab.sim.simulation import run_pipeline
from tests.architectural_helpers import assert_tree_equal, public_input_tree
from tests.feature_tests.workflow_helpers import inputs_from_gui, make_gui


@pytest.fixture
def dialogs(monkeypatch):
    errors = []
    monkeypatch.setattr(gui_io.messagebox, "showinfo", lambda *a, **k: None)
    monkeypatch.setattr(gui_io.messagebox, "showerror", lambda *a, **k: errors.append(a))
    return errors


@pytest.mark.parametrize("market", ["deterministic", "monte_carlo", "historical_windows"])
def test_edit_save_load_and_rerun_complete_financial_plan(tmp_path, monkeypatch, dialogs, market):
    couple = True
    gui = make_gui(tmp_path, second_person_enabled=couple,
        tax_filing_status="Married filing jointly" if couple else "Single",
        results_mode="fill" if market == "deterministic" else "risk_analysis",
        risk_analysis_mode="historical_windows" if market == "historical_windows" else "monte_carlo")
    path = tmp_path / "plan.json"
    monkeypatch.setattr(gui_io.filedialog, "asksaveasfilename", lambda **kw: str(path))
    before = run_pipeline(**inputs_from_gui(gui))["core"]
    # Edit a visible financial input and ensure the saved plan is the edited one.
    gui.husband.retire_age = 71
    gui.expensesDict.add_expense(2027, 1234, 2028, "Dental", True)
    edited = run_pipeline(**inputs_from_gui(gui))["core"]
    assert not np.array_equal(before["total_assets"], edited["total_assets"])
    gui.save_values_to_json()
    document = json.loads(path.read_text())
    assert document["DEFAULT_HUSBAND_RETIRE"] == 71
    assert document["EXPENSES"][-1]["is_hsa_eligible"] is True
    # Financial files persist financial inputs, not market assumptions or all
    # simulation controls. Preserve this documented separation on reload.
    reloaded = make_gui(tmp_path, second_person_enabled=couple,
        tax_filing_status="Married filing jointly" if couple else "Single",
        results_mode=gui.simulation_controls["results_mode"],
        risk_analysis_mode=gui.simulation_controls["risk_analysis_mode"])
    reloaded.husband.income = 1
    reloaded.special_income_streams.clear()
    reloaded.roth_flows.clear()
    reloaded.expensesDict.expenses.clear()
    reloaded._load_from_json(path)
    assert not dialogs
    assert reloaded.loaded_data_file == str(path)
    assert reloaded._load_recent_data_dirs() == [tmp_path]
    assert_tree_equal(run_pipeline(**inputs_from_gui(reloaded))["core"], edited)
    assert_tree_equal(run_pipeline(**inputs_from_gui(reloaded))["core"], edited)


def test_basic_advanced_basic_switch_runs_visible_finances_without_losing_truth(tmp_path):
    gui = make_gui(tmp_path)
    truth = public_input_tree([gui.husband, gui.wife, gui.husband_portfolio, gui.wife_portfolio])
    outputs = {}
    for mode in ("Basic", "Advanced", "Basic"):
        gui.mode_var = SimpleNamespace(get=lambda: mode)
        case = inputs_from_gui(gui)
        result = run_pipeline(**case)["core"]
        if mode == "Basic":
            assert case["husband"].pension == 0
            assert case["husband"].ss_age == case["husband"].retire_age
            initial = gui.husband_portfolio.cash_post + gui.wife_portfolio.cash_post
            assert result["total_assets"][0, 0] == initial
        if mode in outputs:
            assert_tree_equal(result, outputs[mode])
        outputs[mode] = copy.deepcopy(result)
        assert_tree_equal(public_input_tree([gui.husband, gui.wife,
            gui.husband_portfolio, gui.wife_portfolio]), truth)
    assert not np.array_equal(outputs["Basic"]["total_assets"], outputs["Advanced"]["total_assets"])


@pytest.mark.parametrize("payload", ["{broken json", '{"WARPSIMLAB_METADATA": {"file_type": "wrong"}}'])
def test_rejected_file_then_valid_load_preserves_runnable_plan(tmp_path, monkeypatch, dialogs, payload):
    gui = make_gui(tmp_path)
    expected = run_pipeline(**inputs_from_gui(gui))["core"]
    good, bad = tmp_path / "good.json", tmp_path / "bad.json"
    monkeypatch.setattr(gui_io.filedialog, "asksaveasfilename", lambda **kw: str(good))
    gui.save_values_to_json()
    bad.write_text(payload)
    gui._load_from_json(bad)
    assert len(dialogs) == 1
    assert_tree_equal(run_pipeline(**inputs_from_gui(gui))["core"], expected)
    gui._load_from_json(good)
    assert len(dialogs) == 1
    assert_tree_equal(run_pipeline(**inputs_from_gui(gui))["core"], expected)


def test_single_person_gui_can_execute_year_by_year_report(tmp_path, monkeypatch, dialogs):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    gui = make_gui(tmp_path, second_person_enabled=False, tax_filing_status="Single")
    # Use the actual GUI action and dispatcher, not a substituted financial runner.
    gui.run_simulation_from_gui("year_by_year_report")
    assert not dialogs
    assert len(list(tmp_path.rglob("*.html"))) == 1


def test_cancelled_save_and_failed_destination_allow_save_retry(tmp_path, monkeypatch, dialogs):
    gui = make_gui(tmp_path)
    expected = run_pipeline(**inputs_from_gui(gui))["core"]
    monkeypatch.setattr(gui_io.filedialog, "asksaveasfilename", lambda **kw: "")
    gui.save_values_to_json()
    assert not list(tmp_path.iterdir())
    monkeypatch.setattr(gui_io.filedialog, "asksaveasfilename", lambda **kw: str(tmp_path))
    gui.save_values_to_json()  # A directory cannot be opened as a JSON file.
    assert len(dialogs) == 1
    path = tmp_path / "retry.json"
    monkeypatch.setattr(gui_io.filedialog, "asksaveasfilename", lambda **kw: str(path))
    gui.save_values_to_json()
    assert path.is_file()
    assert len(dialogs) == 1
    assert_tree_equal(run_pipeline(**inputs_from_gui(gui))["core"], expected)


def test_rejected_financial_contents_preserve_existing_person(tmp_path, dialogs):
    gui = make_gui(tmp_path)
    original_age = gui.husband.age
    path = tmp_path / "invalid_contents.json"
    path.write_text(json.dumps({
        "WARPSIMLAB_METADATA": {"file_type": "financial_data", "schema_version": 2},
        "DEFAULT_HUSBAND_AGE": 99, "DEFAULT_LONGEVITY_MODE": "invalid"}))
    gui._load_from_json(path)
    assert len(dialogs) == 1
    assert "Invalid longevity mode" in dialogs[0][1]
    assert gui.husband.age == original_age
