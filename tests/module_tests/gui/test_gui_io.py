# test_gui_io.py
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from src.warpsimlab.gui.gui_io import PortfolioSimulatorGUI_IOMixin

import pytest


from src.warpsimlab.gui.gui_io import PortfolioSimulatorGUI_IOMixin

def _make_dummy_gui(tmp_path: Path):
    class DummyGUI(PortfolioSimulatorGUI_IOMixin):
        pass

    gui = DummyGUI()

    # Minimal people
    gui.husband = SimpleNamespace(
        age=40,
        retire_age=67,
        income="100000",
        ss="2000",
        ss_age=67,
        pension="500",
        pension_age=67,
        pension_inflation_adjustment_pct=0.0,
        annuity="250",
        annuity_age=67,
        annual_401k_contribution="10000",
        annual_employer_match="5000",
        annual_hsa_contribution="3000",
        annual_hsa_employer_contribution="1000",
    )
    gui.wife = SimpleNamespace(
        age=40,
        retire_age=67,
        income="80000",
        ss="1800",
        ss_age=67,
        pension="400",
        pension_age=67,
        pension_inflation_adjustment_pct=0.0,
        annuity="200",
        annuity_age=67,
        annual_401k_contribution="8000",
        annual_employer_match="4000",
        annual_hsa_contribution="2500",
        annual_hsa_employer_contribution="750",
    )

    # Minimal portfolios
    gui.husband_portfolio = SimpleNamespace(
        equity_pre=1.0,
        equity_post=2.0,
        equity_roth=2.5,

        bond_pre=3.0,
        bond_post=4.0,
        bond_roth=4.5,

        cash_pre=5.0,
        cash_post=6.0,
        cash_roth=6.5,

        hsa_cash=7.0,
        hsa_equity=8.0,
        hsa_bond=9.0,

        real_estate=10.0,
    )

    gui.wife_portfolio = SimpleNamespace(
        equity_pre=10.0,
        equity_post=20.0,
        equity_roth=25.0,

        bond_pre=30.0,
        bond_post=40.0,
        bond_roth=45.0,

        cash_pre=50.0,
        cash_post=60.0,
        cash_roth=65.0,

        hsa_cash=70.0,
        hsa_equity=80.0,
        hsa_bond=90.0,

        real_estate=100.0,
    )

    # Expenses holder
    class DummyExpenses:
        def __init__(self):
            self.expenses = []

        def add_expense(self, start_year, cost, end_year=None, comment=""):
            self.expenses.append(
                {
                    "start_year": start_year,
                    "end_year": end_year,
                    "cost": cost,
                    "comment": comment,
                }
            )

    gui.expensesDict = DummyExpenses()

    gui.special_income_streams = []
    gui.roth_flows = []

    gui.simulation_controls = {
        "second_person_enabled": 0,
        "state_of_residence": "Colorado",
    }
    gui.simulation_settings = {"years_to_simulate": 30, "num_sims": 500, "fund_expense": 0.0}

    gui.second_person_enabled = SimpleNamespace(get=lambda: False)
    gui.root = SimpleNamespace(update_idletasks=lambda: None)
    gui.edit_frame_container = None

    return gui


def test_load_examples_from_json_loads_financial_data_average(
    monkeypatch,
    tmp_path,
):
    from src.warpsimlab.gui import gui_io as mod

    gui = _make_dummy_gui(tmp_path)

    example_dir = (
        tmp_path
        / "src"
        / "warpsimlab"
        / "exampleFiles"
    )
    example_dir.mkdir(parents=True, exist_ok=True)

    example_file = example_dir / "financialDataAverage.json"
    example_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_IOMixin,
        "_get_examples_directory",
        lambda self: str(example_dir),
        raising=True,
    )

    dialog_args = {}

    def fake_askopenfilename(**kwargs):
        dialog_args.update(kwargs)
        return str(example_file)

    monkeypatch.setattr(
        mod.filedialog,
        "askopenfilename",
        fake_askopenfilename,
        raising=True,
    )

    loaded = {}

    def fake_load_from_json(self, file_path):
        loaded["path"] = Path(file_path)

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_IOMixin,
        "_load_from_json",
        fake_load_from_json,
        raising=True,
    )

    mod.PortfolioSimulatorGUI_IOMixin.load_examples_from_json(gui)

    assert Path(dialog_args["initialdir"]) == example_dir
    assert loaded["path"] == example_file


def test_load_values_from_json_prompts_when_default_missing(monkeypatch, tmp_path):
    """
    If default file does not exist, load_values_from_json should prompt.
    """
    from src.warpsimlab.gui import gui_io as mod

    gui = _make_dummy_gui(tmp_path)

    default_dir = tmp_path / "WARPSimLab"
    default_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_IOMixin,
        "get_default_warpsimlab_dir",
        lambda self: default_dir,
        raising=True,
    )

    chosen = tmp_path / "chosen.json"
    chosen.write_text("{}")

    monkeypatch.setattr(mod.filedialog, "askopenfilename", lambda **kwargs: str(chosen), raising=True)

    loaded = {}

    def fake_load_from_json(self, file_path):
        loaded["path"] = Path(file_path)

    monkeypatch.setattr(mod.PortfolioSimulatorGUI_IOMixin, "_load_from_json", fake_load_from_json, raising=True)

    mod.PortfolioSimulatorGUI_IOMixin.load_values_from_json(gui)

    assert loaded["path"] == chosen


def test_load_values_from_json_cancel(monkeypatch, tmp_path):
    """
    Canceling the open dialog should return without calling _load_from_json.
    """
    from src.warpsimlab.gui import gui_io as mod

    gui = _make_dummy_gui(tmp_path)

    default_dir = tmp_path / "WARPSimLab"
    default_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_IOMixin,
        "get_default_warpsimlab_dir",
        lambda self: default_dir,
        raising=True,
    )

    monkeypatch.setattr(mod.filedialog, "askopenfilename", lambda **kwargs: "", raising=True)

    called = {"n": 0}

    def fake_load_from_json(self, file_path):
        called["n"] += 1

    monkeypatch.setattr(mod.PortfolioSimulatorGUI_IOMixin, "_load_from_json", fake_load_from_json, raising=True)

    mod.PortfolioSimulatorGUI_IOMixin.load_values_from_json(gui)

    assert called["n"] == 0


def test_save_values_to_json_cancel(monkeypatch, tmp_path):
    """
    If asksaveasfilename returns empty string, save_values_to_json should return without saving.
    """
    from src.warpsimlab.gui import gui_io as mod

    gui = _make_dummy_gui(tmp_path)

    default_dir = tmp_path / "WARPSimLab"
    default_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_IOMixin,
        "get_default_warpsimlab_dir",
        lambda self: default_dir,
        raising=True,
    )

    monkeypatch.setattr(mod.filedialog, "asksaveasfilename", lambda **kwargs: "", raising=True)

    saved = {"n": 0}

    monkeypatch.setattr(mod, "save_financial_data_to_file", lambda *a, **k: saved.__setitem__("n", saved["n"] + 1), raising=True)

    mod.PortfolioSimulatorGUI_IOMixin.save_values_to_json(gui)

    assert saved["n"] == 0


def test_save_values_to_json_writes_expected_keys(monkeypatch, tmp_path):
    """
    Verify save_values_to_json calls save_financial_data_to_file with a dict containing key fields.
    """
    from src.warpsimlab.gui import gui_io as mod

    gui = _make_dummy_gui(tmp_path)

    default_dir = tmp_path / "WARPSimLab"
    default_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_IOMixin,
        "get_default_warpsimlab_dir",
        lambda self: default_dir,
        raising=True,
    )

    out_file = tmp_path / "savedFinancialData.json"
    monkeypatch.setattr(mod.filedialog, "asksaveasfilename", lambda **kwargs: str(out_file), raising=True)

    # Avoid GUI popups
    monkeypatch.setattr(mod.messagebox, "showinfo", lambda *a, **k: None, raising=True)
    monkeypatch.setattr(mod.messagebox, "showerror", lambda *a, **k: None, raising=True)

    captured = {}

    def fake_save(path, data):
        captured["path"] = Path(path)
        captured["data"] = data

    monkeypatch.setattr(mod, "save_financial_data_to_file", fake_save, raising=True)

    mod.PortfolioSimulatorGUI_IOMixin.save_values_to_json(gui)

    assert captured["path"] == out_file
    data = captured["data"]

    # A few representative keys
    assert "DEFAULT_HUSBAND_AGE" in data
    assert "DEFAULT_EQUITY_PRE_H" in data
    assert data["DEFAULT_EQUITY_ROTH_H"] == pytest.approx(2.5)
    assert data["DEFAULT_BOND_ROTH_H"] == pytest.approx(4.5)
    assert data["DEFAULT_CASH_ROTH_H"] == pytest.approx(6.5)

    assert data["DEFAULT_HSA_CASH_H"] == pytest.approx(7.0)
    assert data["DEFAULT_HSA_EQUITY_H"] == pytest.approx(8.0)
    assert data["DEFAULT_HSA_BOND_H"] == pytest.approx(9.0)
    assert "DEFAULT_ENABLE_SECOND_PERSON" in data
    assert "DEFAULT_YEARS" in data
    assert "DEFAULT_SIMULATIONS" in data
    assert "DEFAULT_FUND_EXPENSE" in data
    assert "EXPENSES" in data
    assert "SPECIAL_INCOME_STREAMS" in data
    assert data["SPECIAL_INCOME_STREAMS"] == []

    assert data["DEFAULT_HUSBAND_HSA_CONTRIB"] == pytest.approx(3000.0)
    assert data["DEFAULT_HUSBAND_HSA_EMPLOYER_CONTRIB"] == pytest.approx(1000.0)