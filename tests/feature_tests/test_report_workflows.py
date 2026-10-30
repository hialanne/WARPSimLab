"""Real GUI configuration -> dispatch -> finance -> report files, without a browser."""

import csv
import copy
from pathlib import Path
import re

import numpy as np
import pytest

from src.warpsimlab.sim.simulation import run_pipeline, run_simulation
from tests.architectural_helpers import assert_tree_equal, public_input_tree, user_config_tree
from tests.feature_tests.workflow_helpers import inputs_from_gui, make_gui


@pytest.fixture
def report_home(tmp_path, monkeypatch):
    # Covers both os.path.expanduser and Path.home without replacing reporting.
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("MPLBACKEND", "Agg")
    import matplotlib
    matplotlib.use("Agg")
    import webbrowser
    def unexpected_browser(*args, **kwargs):
        pytest.fail("Headless report requested a browser")
    monkeypatch.setattr(webbrowser, "open", unexpected_browser)
    return tmp_path


@pytest.mark.parametrize("sim_type,title", [
    ("summary_report", "Executive Summary"),
    ("year_by_year_report", "Year-by-Year"),
    ("tax_report", "Tax and Medicare"),
    ("monte_carlo_risk_report", "Monte Carlo"),
    ("historical_window_risk_report", "Historical Window"),
    ("asset_allocation_comparison_report", "Asset Allocation"),
    ("spending_comparison_report", "Spending"),
    ("retirement_ss_comparison_report", "Retirement"),
])
def test_gui_built_reports_write_real_artifacts_and_allow_clean_rerun(report_home, sim_type, title):
    gui = make_gui(report_home)
    case = inputs_from_gui(gui, sim_type)
    config = case["sim_config"]
    before = user_config_tree(config)
    domain = public_input_tree({k: v for k, v in case.items() if k != "sim_config"})
    expected = copy.deepcopy(run_pipeline(**case)["core"])
    result = run_simulation(**case)
    assert result.success, result.errors
    path = Path(result.report_path)
    assert path.is_relative_to(report_home)
    assert path.suffix == ".html"
    html = path.read_text(encoding="utf-8")
    assert title.lower() in html.lower()
    assert "2026" in html
    # Broken report images are observable failures even when HTML creation succeeds.
    for source in re.findall(r'<img[^>]+src=["\']([^"\']+)', html):
        image_path = path.parent / source
        assert image_path.is_file(), source
        assert image_path.stat().st_size > 0
    assert_tree_equal(user_config_tree(config), before, "report restores user controls")
    assert_tree_equal(public_input_tree({k: v for k, v in case.items() if k != "sim_config"}), domain)
    assert_tree_equal(run_pipeline(**case)["core"], expected, "rerun after report")


def test_year_by_year_export_reconciles_live_finances_and_survivor_events(report_home):
    gui = make_gui(report_home)
    case = inputs_from_gui(gui, "year_by_year_report")
    pipeline = run_pipeline(**case)
    result = run_simulation(**case)
    assert result.success, result.errors
    files = list(Path(result.output_folder).glob("*.csv"))
    assert len(files) == 1
    with files[0].open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    summary = pipeline["summary_results"]
    assert len(rows) == len(summary["year"])
    columns = {"Total Assets": "total_assets", "Social Security": "social_security",
        "Special Income": "special_income", "Medicare Cost": "medicare_cost",
        "IRMAA": "irmaa", "Qualified HSA Withdrawal": "hsa_qualified_withdrawals",
        "Taxes": "taxes", "Household Expenses": "expenses", "HSA Assets": "hsa_assets"}
    for label, key in columns.items():
        np.testing.assert_allclose([float(row[label]) for row in rows], summary[key], rtol=1e-12, atol=1e-8)
    assert any(row["Life Event"] == "Husband Died" for row in rows)
    assert any(row["Filing Status"] == "Single" for row in rows)
    for key in ("social_security", "special_income", "medicare_cost", "irmaa", "hsa_qualified_withdrawals"):
        assert np.any(summary[key] > 0), key


def test_invalid_gui_input_then_correction_generates_report(report_home, monkeypatch):
    from src.warpsimlab.gui import gui_run
    gui = make_gui(report_home)
    errors = []
    monkeypatch.setattr(gui_run.messagebox, "showerror", lambda *a, **kw: errors.append(a))
    gui.simulation_settings["years_to_simulate"] = "invalid"
    gui.run_simulation_from_gui("year_by_year_report")
    assert len(errors) == 1
    assert errors[0][0] == "Simulation Input Error"
    assert not list(report_home.rglob("*.html"))
    gui.simulation_settings["years_to_simulate"] = 8
    gui.run_simulation_from_gui("year_by_year_report")
    assert len(errors) == 1
    assert len(list(report_home.rglob("*.html"))) == 1


def test_pending_invalid_editor_blocks_run_until_corrected(report_home):
    from types import SimpleNamespace
    gui = make_gui(report_home)
    valid = False
    def validate(*args):
        gui.root._warpsimlab_validation_failed = not valid
    entry = SimpleNamespace(winfo_class=lambda: "TEntry", tk=SimpleNamespace(call=validate), _w="entry")
    gui.root.focus_get = lambda: entry
    gui.run_simulation_from_gui("year_by_year_report")
    assert not list(report_home.rglob("*.html"))
    valid = True
    gui.run_simulation_from_gui("year_by_year_report")
    assert len(list(report_home.rglob("*.html"))) == 1


@pytest.mark.parametrize("sim_type", ["income_sim", "cashflow_sim"])
def test_income_workflow_draws_and_exports_real_results(report_home, monkeypatch, sim_type):
    import matplotlib.pyplot as plt
    gui = make_gui(report_home, output_csv="Output", csv_output_dir=str(report_home),
                   annotate_plots=False)
    case = inputs_from_gui(gui, sim_type)
    expected = run_pipeline(**case)
    shown = []
    monkeypatch.setattr(plt, "show", lambda *a, **kw: shown.append(True))
    try:
        run_simulation(**case)
        assert shown
        with (report_home / "income_simulation.csv").open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len(expected["years_list"])
        for key in ("net_income", "net_profit", "taxes"):
            np.testing.assert_allclose([float(row[key]) for row in rows], expected[key])
        assert any(float(row["ss"]) > 0 for row in rows)
    finally:
        plt.close("all")


def test_failed_report_write_can_be_retried_without_changing_finances(report_home, monkeypatch):
    from src.warpsimlab.reports import year_by_year_report
    gui = make_gui(report_home)
    case = inputs_from_gui(gui, "year_by_year_report")
    expected = copy.deepcopy(run_pipeline(**case)["core"])
    # The report creates its output directory before catching write errors.
    # Exercise a failed file write inside a valid output folder instead.
    with monkeypatch.context() as patch:
        def fail_write(*args, **kwargs):
            raise OSError("injected report destination unavailable")
        patch.setattr(year_by_year_report, "_write_html", fail_write)
        result = run_simulation(**case)
    assert not result.success
    assert "destination unavailable" in " ".join(result.errors)
    assert_tree_equal(run_pipeline(**case)["core"], expected)
    result = run_simulation(**case)
    assert result.success, result.errors
    assert Path(result.report_path).is_file()
    assert_tree_equal(run_pipeline(**case)["core"], expected)
