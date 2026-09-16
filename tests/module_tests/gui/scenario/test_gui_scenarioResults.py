from types import SimpleNamespace

import pytest
import tkinter as tk

from src.warpsimlab.gui.scenario import gui_scenarioResults as mod


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk unavailable in this environment: {exc}")

    root.withdraw()
    yield root
    root.destroy()


def _make_metrics(
    ending_portfolio=100000,
    depletion_rate=5.0,
    ending_cash_flow=1000,
    lifetime_funding_gap=500,
    lifetime_taxes=10000,
    ending_pre_tax=40000,
    ending_after_tax=30000,
    ending_roth=20000,
    ending_hsa=10000,
):
    return SimpleNamespace(
        ending_portfolio=ending_portfolio,
        depletion_rate=depletion_rate,
        ending_cash_flow=ending_cash_flow,
        lifetime_funding_gap=lifetime_funding_gap,
        lifetime_taxes=lifetime_taxes,
        ending_pre_tax=ending_pre_tax,
        ending_after_tax=ending_after_tax,
        ending_roth=ending_roth,
        ending_hsa=ending_hsa,
    )


def _make_assumptions(
    husband_age=60,
    husband_retire_age=65,
    husband_ss_age=67,
    wife_age=None,
    wife_retire_age=None,
    wife_ss_age=None,
    inflation_rate=3.0,
    fund_expense=0.5,
    market_adjustment=100.0,
    dynamic_label="Expense Multiplier",
    dynamic_value=100.0,
    stock=60.0,
    bonds=30.0,
    cash=10.0,
):
    return SimpleNamespace(
        husband_age=husband_age,
        husband_retire_age=husband_retire_age,
        husband_ss_age=husband_ss_age,
        wife_age=wife_age,
        wife_retire_age=wife_retire_age,
        wife_ss_age=wife_ss_age,
        inflation_rate=inflation_rate,
        fund_expense=fund_expense,
        market_adjustment=market_adjustment,
        dynamic_label=dynamic_label,
        dynamic_value=dynamic_value,
        stock=stock,
        bonds=bonds,
        cash=cash,
    )


def _make_view_model(
    original_metrics=None,
    changed_metrics=None,
    original_assumptions=None,
    changed_assumptions=None,
):
    if original_metrics is None:
        original_metrics = _make_metrics()

    if changed_metrics is None:
        changed_metrics = _make_metrics()

    if original_assumptions is None:
        original_assumptions = _make_assumptions()

    if changed_assumptions is None:
        changed_assumptions = _make_assumptions()

    return SimpleNamespace(
        original_metrics=original_metrics,
        changed_metrics=changed_metrics,
        original_assumptions=original_assumptions,
        changed_assumptions=changed_assumptions,
    )


def _assumption_texts(frame):
    return [
        str(widget.cget("text"))
        for widget in frame.assumptions_frame.winfo_children()
        if "text" in widget.keys()
    ]


def test_results_frame_builds_expected_metric_rows(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    assert set(frame.metric_rows) == {
        "ending_portfolio",
        "depletion_rate",
        "ending_cash_flow",
        "lifetime_funding_gap",
        "lifetime_taxes",
        "ending_pre_tax",
        "ending_after_tax",
        "ending_roth",
        "ending_hsa",
    }

    frame.destroy()


def test_update_results_returns_without_changes_when_view_model_missing(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    frame.update_results(None)

    assert frame.metric_rows["ending_portfolio"]["original"].cget("text") == "-"
    assert frame.metric_rows["ending_portfolio"]["changed"].cget("text") == "-"

    frame.destroy()


def test_update_results_formats_all_metrics(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    original = _make_metrics(
        ending_portfolio=123456,
        depletion_rate=4.25,
        ending_cash_flow=2345,
        lifetime_funding_gap=500,
        lifetime_taxes=12345,
        ending_pre_tax=50000,
        ending_after_tax=30000,
        ending_roth=25000,
        ending_hsa=18456,
    )
    changed = _make_metrics(
        ending_portfolio=234567,
        depletion_rate=1.5,
        ending_cash_flow=3456,
        lifetime_funding_gap=100,
        lifetime_taxes=15000,
        ending_pre_tax=90000,
        ending_after_tax=50000,
        ending_roth=70000,
        ending_hsa=24567,
    )

    frame.update_results(_make_view_model(original_metrics=original, changed_metrics=changed))

    assert frame.metric_rows["ending_portfolio"]["original"].cget("text") == "$123,456"
    assert frame.metric_rows["ending_portfolio"]["changed"].cget("text") == "$234,567"
    assert frame.metric_rows["depletion_rate"]["original"].cget("text") == "4.2%"
    assert frame.metric_rows["depletion_rate"]["changed"].cget("text") == "1.5%"
    assert frame.metric_rows["ending_cash_flow"]["original"].cget("text") == "$2,345"
    assert frame.metric_rows["ending_cash_flow"]["changed"].cget("text") == "$3,456"
    assert frame.metric_rows["lifetime_funding_gap"]["original"].cget("text") == "$500"
    assert frame.metric_rows["lifetime_funding_gap"]["changed"].cget("text") == "$100"
    assert frame.metric_rows["lifetime_taxes"]["original"].cget("text") == "$12,345"
    assert frame.metric_rows["lifetime_taxes"]["changed"].cget("text") == "$15,000"
    assert frame.metric_rows["ending_pre_tax"]["original"].cget("text") == "$50,000"
    assert frame.metric_rows["ending_after_tax"]["changed"].cget("text") == "$50,000"
    assert frame.metric_rows["ending_roth"]["changed"].cget("text") == "$70,000"
    assert frame.metric_rows["ending_hsa"]["changed"].cget("text") == "$24,567"

    frame.destroy()


def test_set_percent_row_displays_dash_when_value_missing(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    frame._set_percent_row("depletion_rate", None, 5.0)

    assert frame.metric_rows["depletion_rate"]["original"].cget("text") == "-"
    assert frame.metric_rows["depletion_rate"]["changed"].cget("text") == "-"

    frame.destroy()


def test_rebuild_assumptions_expense_mode_shows_expected_fields(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    original = _make_assumptions(
        husband_retire_age=65,
        husband_ss_age=67,
        inflation_rate=3.0,
        fund_expense=0.5,
        market_adjustment=100.0,
        dynamic_label="Expense Multiplier",
        dynamic_value=100.0,
    )
    changed = _make_assumptions(
        husband_retire_age=66,
        husband_ss_age=68,
        inflation_rate=4.0,
        fund_expense=0.75,
        market_adjustment=90.0,
        dynamic_label="Expense Multiplier",
        dynamic_value=125.0,
    )

    frame._rebuild_assumptions(
        _make_view_model(original_assumptions=original, changed_assumptions=changed)
    )

    texts = _assumption_texts(frame)

    assert "Husband" in texts
    assert "Retirement Age" in texts
    assert "Social Security Age" in texts
    assert "Inflation Rate" in texts
    assert "Fund Expenses" in texts
    assert "Market Adjustment" in texts
    assert "Expense Multiplier" in texts
    assert "Withdrawal Rate" not in texts
    assert "Stock" in texts
    assert "Bonds" in texts
    assert "Cash" in texts

    frame.destroy()


def test_rebuild_assumptions_withdraw_mode_uses_withdrawal_rate(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    original = _make_assumptions(dynamic_label="Withdrawal Rate", dynamic_value=4.0)
    changed = _make_assumptions(dynamic_label="Withdrawal Rate", dynamic_value=5.5)

    frame._rebuild_assumptions(
        _make_view_model(original_assumptions=original, changed_assumptions=changed)
    )

    texts = _assumption_texts(frame)

    assert "Withdrawal Rate" in texts
    assert "Expense Multiplier" not in texts

    frame.destroy()


def test_rebuild_assumptions_includes_wife_when_present(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    original = _make_assumptions(wife_age=58, wife_retire_age=64, wife_ss_age=66)
    changed = _make_assumptions(wife_age=58, wife_retire_age=65, wife_ss_age=67)

    frame._rebuild_assumptions(
        _make_view_model(original_assumptions=original, changed_assumptions=changed)
    )

    texts = _assumption_texts(frame)

    assert "Wife" in texts

    frame.destroy()


def test_rebuild_assumptions_omits_wife_when_missing(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    original = _make_assumptions(wife_age=None, wife_retire_age=None, wife_ss_age=None)
    changed = _make_assumptions(wife_age=None, wife_retire_age=None, wife_ss_age=None)

    frame._rebuild_assumptions(
        _make_view_model(original_assumptions=original, changed_assumptions=changed)
    )

    texts = _assumption_texts(frame)

    assert "Wife" not in texts

    frame.destroy()


def test_changed_assumption_uses_changed_style(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    original = _make_assumptions(inflation_rate=3.0)
    changed = _make_assumptions(inflation_rate=4.0)

    frame._rebuild_assumptions(
        _make_view_model(original_assumptions=original, changed_assumptions=changed)
    )

    changed_labels = [
        widget
        for widget in frame.assumptions_frame.winfo_children()
        if isinstance(widget, mod.ttk.Label)
        and widget.cget("text") == "4.0%"
    ]

    assert len(changed_labels) == 1
    assert changed_labels[0].cget("style") == "ScenarioChangedResult.TLabel"

    frame.destroy()


def test_unchanged_assumption_uses_normal_style(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    original = _make_assumptions(inflation_rate=3.0)
    changed = _make_assumptions(inflation_rate=3.0)

    frame._rebuild_assumptions(
        _make_view_model(original_assumptions=original, changed_assumptions=changed)
    )

    unchanged_labels = [
        widget
        for widget in frame.assumptions_frame.winfo_children()
        if isinstance(widget, mod.ttk.Label)
        and widget.cget("text") == "3.0%"
    ]

    assert len(unchanged_labels) >= 1
    assert any(label.cget("style") == "TLabel" for label in unchanged_labels)

    frame.destroy()