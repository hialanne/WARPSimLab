from dataclasses import dataclass
from types import SimpleNamespace

import pytest
import tkinter as tk
import tkinter.font as tkfont


@dataclass
class DummyPerson:
    retire_age: int = 67
    ss_age: int = 67


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
    fund_expense: float = 0.5
    scenario_expense_multiplier: float | None = None
    scenario_withdraw_pct: float | None = None


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk unavailable in this environment: {exc}")

    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def slider_module(monkeypatch):
    from src.warpsimlab.gui.scenario import gui_scenarioSliders as mod

    class DummyTooltip:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(mod, "Tooltip", DummyTooltip)
    return mod


def _make_main_gui(expense_mode=True, withdraw_pct=4.0):
    return SimpleNamespace(
        inflation=3.0,
        simulation_controls={
            "always_use_expense_mode": expense_mode,
            "retirement_withdraw_pct": withdraw_pct,
        },
    )


def _make_frame(
    mod,
    tk_root,
    *,
    expense_mode=True,
    withdraw_pct=4.0,
    show_wife=False,
    show_enable_overrides_checkbox=False,
    husband=None,
    wife=None,
    husband_portfolio=None,
    wife_portfolio=None,
    snapshots=None,
):
    if husband is None:
        husband = DummyPerson()

    if husband_portfolio is None:
        husband_portfolio = DummyPortfolio(equity_pre=60, bond_pre=30, cash_pre=10)

    if snapshots is None:
        snapshots = DummySnapshots()

    persons = {"husband": husband}
    portfolio = {"husband": husband_portfolio}

    if show_wife:
        if wife is None:
            wife = DummyPerson(retire_age=65, ss_age=66)
        if wife_portfolio is None:
            wife_portfolio = DummyPortfolio()

        persons["wife"] = wife
        portfolio["wife"] = wife_portfolio

    main_gui = _make_main_gui(expense_mode=expense_mode, withdraw_pct=withdraw_pct)

    frame = mod.ScenarioSlidersFrame(
        tk_root, main_gui=main_gui, persons=persons, portfolio=portfolio, retirement_snapshots=snapshots,
        show_enable_overrides_checkbox=show_enable_overrides_checkbox, show_wife=show_wife
    )
    frame.pack()

    return frame


def _font_weight(widget):
    return tkfont.Font(font=widget.cget("font")).actual("weight")


def test_initializes_husband_controls_from_person(slider_module, tk_root):
    husband = DummyPerson(retire_age=64, ss_age=68)
    frame = _make_frame(slider_module, tk_root, husband=husband)

    assert frame.tmp_ret_age_h.get() == 64
    assert frame.tmp_ss_age_h.get() == 68
    assert frame.husband_label_var.get() == "Husband Retirement Age: 64"
    assert frame.husband_ss_label_var.get() == "Husband Social Security Age: 68"

    frame.destroy()


def test_omits_wife_controls_when_wife_hidden(slider_module, tk_root):
    frame = _make_frame(slider_module, tk_root, show_wife=False)

    assert frame.wife is None
    assert frame.tmp_ret_age_w is None
    assert frame.tmp_ss_age_w is None
    assert frame.wife_slider is None
    assert frame.wife_ss_slider is None

    frame.destroy()


def test_initializes_wife_controls_when_enabled(slider_module, tk_root):
    wife = DummyPerson(retire_age=63, ss_age=66)
    frame = _make_frame(slider_module, tk_root, show_wife=True, wife=wife)

    assert frame.tmp_ret_age_w.get() == 63
    assert frame.tmp_ss_age_w.get() == 66
    assert frame.wife_label_var.get() == "Wife Retirement Age: 63"
    assert frame.wife_ss_label_var.get() == "Wife Social Security Age: 66"

    frame.destroy()


def test_initializes_economic_controls_from_inputs(slider_module, tk_root):
    snapshots = DummySnapshots(fund_expense=0.75)
    frame = _make_frame(slider_module, tk_root, snapshots=snapshots)

    assert frame.inflation_value.get() == pytest.approx(3.0)
    assert frame.fund_expense_value.get() == pytest.approx(0.75)

    frame.destroy()


def test_initializes_portfolio_percentages_from_combined_portfolio(slider_module, tk_root):
    husband_portfolio = DummyPortfolio(equity_pre=40, bond_pre=20, cash_pre=10)
    wife_portfolio = DummyPortfolio(equity_pre=20, bond_pre=10)

    frame = _make_frame(
        slider_module, tk_root, show_wife=True,
        husband_portfolio=husband_portfolio, wife_portfolio=wife_portfolio
    )

    assert frame.stocks_percent.get() == pytest.approx(60.0)
    assert frame.bonds_percent.get() == pytest.approx(30.0)
    assert frame.cash_percent.get() == pytest.approx(10.0)

    frame.destroy()


def test_zero_portfolio_defaults_to_all_cash(slider_module, tk_root):
    frame = _make_frame(slider_module, tk_root, husband_portfolio=DummyPortfolio())

    assert frame.stocks_percent.get() == pytest.approx(0.0)
    assert frame.bonds_percent.get() == pytest.approx(0.0)
    assert frame.cash_percent.get() == pytest.approx(100.0)

    frame.destroy()


def test_stock_change_reduces_bonds_when_cash_would_be_negative(slider_module, tk_root):
    frame = _make_frame(slider_module, tk_root)

    frame.stocks_percent.set(80)
    frame.bonds_percent.set(30)
    frame._update_stocks_label()

    assert frame.stocks_percent.get() == pytest.approx(80.0)
    assert frame.bonds_percent.get() == pytest.approx(20.0)
    assert frame.cash_percent.get() == pytest.approx(0.0)
    assert frame.stocks_label_var.get() == "Stock: 80%"
    assert frame.bonds_label_var.get() == "Bonds: 20%"
    assert frame.cash_label_var.get() == "Cash (calculated): 0%"

    frame.destroy()


def test_bond_change_reduces_stocks_when_cash_would_be_negative(slider_module, tk_root):
    frame = _make_frame(slider_module, tk_root)

    frame.stocks_percent.set(80)
    frame.bonds_percent.set(30)
    frame._update_bonds_label()

    assert frame.stocks_percent.get() == pytest.approx(70.0)
    assert frame.bonds_percent.get() == pytest.approx(30.0)
    assert frame.cash_percent.get() == pytest.approx(0.0)
    assert frame.stocks_label_var.get() == "Stock: 70%"
    assert frame.bonds_label_var.get() == "Bonds: 30%"

    frame.destroy()


def test_inflation_callback_rounds_value_and_updates_label(slider_module, tk_root):
    frame = _make_frame(slider_module, tk_root)

    frame._update_inflation_label("4.26")

    assert frame.inflation_value.get() == pytest.approx(4.3)
    assert frame.inflation_label_var.get() == "Inflation Rate (%): 4.3"

    frame.destroy()


def test_fund_expense_callback_updates_label(slider_module, tk_root):
    frame = _make_frame(slider_module, tk_root)

    frame._update_fund_expenses_label("0.875")

    assert frame.fund_expense_label_var.get() == "Fund Expenses (%): 0.88"

    frame.destroy()


def test_expense_mode_dynamic_slider_initializes_default(slider_module, tk_root):
    frame = _make_frame(slider_module, tk_root, expense_mode=True)

    assert float(frame.dynamic_slider.cget("from")) == pytest.approx(50.0)
    assert float(frame.dynamic_slider.cget("to")) == pytest.approx(200.0)
    assert frame.dynamic_value.get() == pytest.approx(100.0)
    assert frame.dynamic_label_var.get() == "Expense Multiplier: 100%"

    frame.destroy()


def test_expense_mode_dynamic_slider_uses_snapshot_value(slider_module, tk_root):
    snapshots = DummySnapshots(scenario_expense_multiplier=1.25)
    frame = _make_frame(slider_module, tk_root, expense_mode=True, snapshots=snapshots)

    assert frame.dynamic_value.get() == pytest.approx(125.0)
    assert frame.dynamic_label_var.get() == "Expense Multiplier: 125%"

    frame.destroy()


def test_expense_mode_dynamic_callback_changes_ui_only(slider_module, tk_root):
    snapshots = DummySnapshots(scenario_expense_multiplier=1.0)
    frame = _make_frame(slider_module, tk_root, expense_mode=True, snapshots=snapshots)

    frame._update_dynamic_slider_label("125.4")

    assert frame.dynamic_value.get() == pytest.approx(125.0)
    assert frame.dynamic_label_var.get() == "Expense Multiplier: 125%"
    assert snapshots.scenario_expense_multiplier == pytest.approx(1.0)

    frame.destroy()


def test_withdrawal_mode_dynamic_slider_initializes_default(slider_module, tk_root):
    frame = _make_frame(slider_module, tk_root, expense_mode=False, withdraw_pct=4.25)

    assert float(frame.dynamic_slider.cget("from")) == pytest.approx(0.0)
    assert float(frame.dynamic_slider.cget("to")) == pytest.approx(10.0)
    assert frame.dynamic_value.get() == pytest.approx(4.25)
    assert frame.dynamic_label_var.get() == "Withdrawal: 4.2%"

    frame.destroy()


def test_withdrawal_mode_dynamic_slider_uses_snapshot_value(slider_module, tk_root):
    snapshots = DummySnapshots(scenario_withdraw_pct=5.5)
    frame = _make_frame(slider_module, tk_root, expense_mode=False, snapshots=snapshots)

    assert frame.dynamic_value.get() == pytest.approx(5.5)
    assert frame.dynamic_label_var.get() == "Withdrawal: 5.5%"

    frame.destroy()


def test_withdrawal_mode_dynamic_callback_changes_ui_only(slider_module, tk_root):
    snapshots = DummySnapshots(scenario_withdraw_pct=4.0)
    frame = _make_frame(slider_module, tk_root, expense_mode=False, snapshots=snapshots)

    frame._update_dynamic_slider_label("6.54")

    assert frame.dynamic_value.get() == pytest.approx(6.5)
    assert frame.dynamic_label_var.get() == "Withdrawal: 6.5%"
    assert snapshots.scenario_withdraw_pct == pytest.approx(4.0)

    frame.destroy()


def test_override_checkbox_disables_controls(slider_module, tk_root):
    frame = _make_frame(slider_module, tk_root, show_enable_overrides_checkbox=True)

    assert frame.enable_overrides.get() is False
    assert frame.husband_slider.instate(["disabled"])
    assert frame.husband_ss_slider.instate(["disabled"])
    assert frame.inflation_slider.instate(["disabled"])
    assert frame.fund_expense_slider.instate(["disabled"])
    assert frame.stocks_slider.instate(["disabled"])
    assert frame.bonds_slider.instate(["disabled"])
    assert str(frame.husband_label.cget("foreground")) == "gray"
    assert str(frame.cash_label.cget("foreground")) == "gray"

    frame.destroy()


def test_enabling_overrides_enables_controls(slider_module, tk_root):
    frame = _make_frame(slider_module, tk_root, show_enable_overrides_checkbox=True)

    frame.enable_overrides.set(True)
    frame._update_slider_state()

    assert not frame.husband_slider.instate(["disabled"])
    assert not frame.inflation_slider.instate(["disabled"])
    assert not frame.stocks_slider.instate(["disabled"])
    assert str(frame.husband_label.cget("foreground")) == ""
    assert str(frame.cash_label.cget("foreground")) == ""

    frame.destroy()


def test_scenario_mode_starts_with_controls_enabled(slider_module, tk_root):
    frame = _make_frame(slider_module, tk_root, show_enable_overrides_checkbox=False)

    assert frame.enable_overrides.get() is True
    assert frame.enable_overrides_cb is None
    assert not frame.husband_slider.instate(["disabled"])
    assert not frame.stocks_slider.instate(["disabled"])

    frame.destroy()


def test_changed_control_highlighting_tracks_baseline(slider_module, tk_root):
    frame = _make_frame(slider_module, tk_root)

    assert _font_weight(frame.inflation_label) == "normal"

    frame.inflation_value.set(4.0)
    tk_root.update_idletasks()

    assert _font_weight(frame.inflation_label) == "bold"

    frame.inflation_value.set(3.0)
    tk_root.update_idletasks()

    assert _font_weight(frame.inflation_label) == "normal"

    frame.destroy()


def test_get_values_returns_current_single_person_controls(slider_module, tk_root):
    frame = _make_frame(slider_module, tk_root, expense_mode=True)

    frame.tmp_ret_age_h.set(66)
    frame.tmp_ss_age_h.set(68)
    frame.inflation_value.set(4.0)
    frame.fund_expense_value.set(0.75)
    frame.stocks_percent.set(65)
    frame.bonds_percent.set(25)
    frame.cash_percent.set(10)
    frame.dynamic_value.set(125)
    frame.calculate_real_dollars.set(False)
    frame.enable_annotations.set(False)

    values = frame.get_values()

    assert isinstance(values, slider_module.ScenarioControlValues)
    assert values.husband_ret_age == 66
    assert values.husband_ss_age == 68
    assert values.wife_ret_age is None
    assert values.wife_ss_age is None
    assert values.inflation == pytest.approx(4.0)
    assert values.fund_expense == pytest.approx(0.75)
    assert values.stocks == pytest.approx(65.0)
    assert values.bonds == pytest.approx(25.0)
    assert values.cash == pytest.approx(10.0)
    assert values.dynamic_value == pytest.approx(125.0)
    assert values.calculate_real_dollars is False
    assert values.enable_annotations is False

    frame.destroy()


def test_get_values_returns_wife_controls_when_present(slider_module, tk_root):
    frame = _make_frame(slider_module, tk_root, show_wife=True)

    frame.tmp_ret_age_w.set(64)
    frame.tmp_ss_age_w.set(67)

    values = frame.get_values()

    assert values.wife_ret_age == 64
    assert values.wife_ss_age == 67

    frame.destroy()