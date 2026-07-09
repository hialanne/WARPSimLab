# test_gui_scenarioSliders.py

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import tkinter as tk
import pytest

#pytest.skip("Skipping GUI tests for now", allow_module_level=True)



@dataclass
class DummyPerson:
    retire_age: int
    ss: float = 2000.0
    pension: float = 500.0
    annuity: float = 250.0
    ss_age: int = 67
    pension_age: int = 67
    annuity_age: int = 67


@dataclass
class DummyPortfolio:
    equity_pre: float = 0.0
    equity_post: float = 0.0
    bond_pre: float = 0.0
    bond_post: float = 0.0
    cash_pre: float = 0.0
    cash_post: float = 0.0


@dataclass
class DummySnapshots:
    inflation: float = 3.0
    fund_expense: float = 0.5
    historical_data_multiplier: float = 100.0
    scenario_expense_multiplier: float | None = None
    scenario_withdraw_pct: float | None = None


@pytest.fixture
def tk_root():
    """Hidden Tk root. Skip if Tk isn't available."""
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk unavailable in this environment: {e}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def no_tooltip(monkeypatch):
    """Disable Tooltip side-effects (event binds / timers)."""
    from src.warpsimlab.gui import gui_scenarioSliders as mod

    class DummyTooltip:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(mod, "Tooltip", DummyTooltip, raising=True)
    return mod


@pytest.fixture
def main_gui_manual_expenses():
    return SimpleNamespace(
        simulation_controls={
            "manual_expenses": True,
            "retirement_withdraw_pct": 4.0,
        },
        husband=DummyPerson(retire_age=67),
        wife=DummyPerson(retire_age=67),
    )


@pytest.fixture
def main_gui_withdraw_mode():
    return SimpleNamespace(
        simulation_controls={
            "manual_expenses": False,
            "retirement_withdraw_pct": 4.25,
        },
        husband=DummyPerson(retire_age=67),
        wife=DummyPerson(retire_age=67),
    )


def _make_frame(
    mod,
    tk_root,
    *,
    main_gui,
    show_enable_overrides_checkbox: bool,
    show_wife: bool,
    h_person: DummyPerson | None = None,
    w_person: DummyPerson | None = None,
    h_port: DummyPortfolio | None = None,
    w_port: DummyPortfolio | None = None,
    snapshots: DummySnapshots | None = None,
    baseline_persons: dict | None = None,
):
    h_person = h_person or DummyPerson(retire_age=67)
    persons = {"husband": h_person}
    if show_wife:
        persons["wife"] = (w_person or DummyPerson(retire_age=67))

    portfolio = {"husband": (h_port or DummyPortfolio())}
    if show_wife:
        portfolio["wife"] = (w_port or DummyPortfolio())

    snapshots = snapshots or DummySnapshots()

    if baseline_persons is None:
        baseline_persons = {"husband": h_person}
        if show_wife:
            baseline_persons["wife"] = persons["wife"]

    frame = mod.ScenarioSlidersFrame(
        tk_root,
        main_gui=main_gui,
        persons=persons,
        portfolio=portfolio,
        retirement_snapshots=snapshots,
        show_enable_overrides_checkbox=show_enable_overrides_checkbox,
        allow_main_gui_override_flag=True,
        show_wife=show_wife,
        baseline_persons=baseline_persons,
    )
    frame.pack()
    return frame, persons, portfolio, snapshots


def test_initial_portfolio_percents_zero_total_defaults_to_all_cash(tk_root, no_tooltip, main_gui_manual_expenses):
    mod = no_tooltip

    frame, _, _, _ = _make_frame(
        mod,
        tk_root,
        main_gui=main_gui_manual_expenses,
        show_enable_overrides_checkbox=False,
        show_wife=False,
        h_port=DummyPortfolio(),  # all zeros
    )

    assert frame.stocks_percent.get() == 0
    assert frame.bonds_percent.get() == 0
    assert frame.cash_percent.get() == 100


def test_update_stocks_label_reduces_bonds_when_cash_would_go_negative(tk_root, no_tooltip, main_gui_manual_expenses):
    mod = no_tooltip

    frame, _, _, _ = _make_frame(
        mod,
        tk_root,
        main_gui=main_gui_manual_expenses,
        show_enable_overrides_checkbox=False,
        show_wife=False,
    )

    frame.stocks_percent.set(80)
    frame.bonds_percent.set(30)  # would imply cash = -10
    frame._update_stocks_label()

    # When cash < 0, code reduces bonds first by the negative cash amount. :contentReference[oaicite:1]{index=1}
    assert round(frame.stocks_percent.get()) == 80
    assert round(frame.bonds_percent.get()) == 20
    assert frame.cash_percent.get() == 0

    assert "Percent Stock: 80%" in frame.stocks_label_var.get()
    assert "Percent Bonds: 20%" in frame.bonds_label_var.get()
    assert "Percent Cash" in frame.cash_label_var.get()


def test_update_bonds_label_reduces_stocks_when_cash_would_go_negative(tk_root, no_tooltip, main_gui_manual_expenses):
    mod = no_tooltip

    frame, _, _, _ = _make_frame(
        mod,
        tk_root,
        main_gui=main_gui_manual_expenses,
        show_enable_overrides_checkbox=False,
        show_wife=False,
    )

    frame.stocks_percent.set(80)
    frame.bonds_percent.set(30)  # would imply cash = -10
    frame._update_bonds_label()

    # When cash < 0 in bonds update, code reduces stocks by the negative cash. :contentReference[oaicite:2]{index=2}
    assert round(frame.stocks_percent.get()) == 70
    assert round(frame.bonds_percent.get()) == 30
    assert frame.cash_percent.get() == 0

    assert "Percent Stock: 70%" in frame.stocks_label_var.get()
    assert "Percent Bonds: 30%" in frame.bonds_label_var.get()


def test_update_slider_state_disables_and_grays_controls(tk_root, no_tooltip, main_gui_manual_expenses):
    mod = no_tooltip

    frame, _, _, _ = _make_frame(
        mod,
        tk_root,
        main_gui=main_gui_manual_expenses,
        show_enable_overrides_checkbox=True,  # starts False per init path :contentReference[oaicite:3]{index=3}
        show_wife=False,
    )

    # Initial state should be disabled/gray when checkbox shown. :contentReference[oaicite:4]{index=4}
    assert frame.husband_slider.instate(["disabled"])
    assert frame.inflation_slider.instate(["disabled"])
    assert frame.fund_expense_slider.instate(["disabled"])
    assert frame.market_adjustment_slider.instate(["disabled"])
    assert frame.stocks_slider.instate(["disabled"])
    assert frame.bonds_slider.instate(["disabled"])
    assert str(frame.husband_label.cget("foreground")) == "gray"
    assert str(frame.cash_label.cget("foreground")) == "gray"
    # Enable and re-apply
    frame.enable_overrides.set(True)
    frame._update_slider_state()

    assert not frame.husband_slider.instate(["disabled"])
    assert str(frame.husband_label.cget("foreground")) == "black"
    assert str(frame.cash_label.cget("foreground")) == "black"

def test_adjust_retirement_benefits_year_by_year_clamps_ages_and_scales_ss(tk_root, no_tooltip, main_gui_manual_expenses):
    mod = no_tooltip

    frame, persons, _, _ = _make_frame(
        mod,
        tk_root,
        main_gui=main_gui_manual_expenses,
        show_enable_overrides_checkbox=False,
        show_wife=False,
        h_person=DummyPerson(retire_age=55, ss=2000.0, pension=111.0, annuity=222.0),
        baseline_persons={"husband": DummyPerson(retire_age=75, ss=2480.0, pension=111.0, annuity=222.0)},
    )

    snapshot = persons["husband"]
    baseline = frame.baseline_persons["husband"]

    frame.adjust_retirement_benefits_year_by_year(snapshot, baseline)

    # Baseline age clamps to 70; snapshot age clamps to 62. :contentReference[oaicite:5]{index=5}
    # baseline_factor(70)=1.24, new_factor(62)=0.70 => baseline_pia=2480/1.24=2000 => new_ss=2000*0.70=1400
    assert snapshot.ss == 1400.00
    assert snapshot.pension == baseline.pension
    assert snapshot.annuity == baseline.annuity
    assert snapshot.ss_age == snapshot.retire_age
    assert snapshot.pension_age == snapshot.retire_age
    assert snapshot.annuity_age == snapshot.retire_age


def test_dynamic_slider_manual_expenses_config_and_update_stores_multiplier(tk_root, no_tooltip, main_gui_manual_expenses):
    mod = no_tooltip

    snapshots = DummySnapshots(scenario_expense_multiplier=None)
    frame, _, _, snaps = _make_frame(
        mod,
        tk_root,
        main_gui=main_gui_manual_expenses,
        show_enable_overrides_checkbox=False,
        show_wife=False,
        snapshots=snapshots,
    )

    # Manual mode config: from 50 to 150, default value 100 if None. :contentReference[oaicite:6]{index=6}
    assert float(frame.dynamic_slider.cget("from")) == 50.0
    assert float(frame.dynamic_slider.cget("to")) == 150.0
    assert round(frame.dynamic_value.get()) == 100
    assert "Expense Multiplier" in frame.dynamic_label_var.get()

    # Update stores multiplier (val/100). :contentReference[oaicite:7]{index=7}
    frame._update_dynamic_slider_label("125")
    assert snaps.scenario_expense_multiplier == 1.25
    assert "125%" in frame.dynamic_label_var.get()


def test_dynamic_slider_withdraw_mode_config_and_update_stores_withdraw_pct(tk_root, no_tooltip, main_gui_withdraw_mode):
    mod = no_tooltip

    snapshots = DummySnapshots(scenario_withdraw_pct=None)
    frame, _, _, snaps = _make_frame(
        mod,
        tk_root,
        main_gui=main_gui_withdraw_mode,
        show_enable_overrides_checkbox=False,
        show_wife=False,
        snapshots=snapshots,
    )

    # Withdraw mode config: from 0 to 10, default value from main_gui controls. :contentReference[oaicite:8]{index=8}
    assert float(frame.dynamic_slider.cget("from")) == 0.0
    assert float(frame.dynamic_slider.cget("to")) == 10.0
    assert abs(frame.dynamic_value.get() - 4.25) < 1e-9
    assert "Withdrawal" in frame.dynamic_label_var.get()

    frame._update_dynamic_slider_label("6.5")
    assert snaps.scenario_withdraw_pct == 6.5
    assert "6.50%" in frame.dynamic_label_var.get()