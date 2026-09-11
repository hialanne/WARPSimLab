# test_gui_scenarioResults.py

from types import SimpleNamespace

import pytest
import tkinter as tk

from src.warpsimlab.gui.scenario import gui_scenarioResults as mod


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk unavailable in this environment: {e}")
    root.withdraw()
    yield root
    root.destroy()


def _make_summary(total_assets=100000, depletion_rate=5.0, net_cash_flow=1000, funding_gap=0, taxes=10000,
                  pre_tax=40000, post_tax=30000, roth=20000, hsa=10000):
    return {
        "total_assets": [total_assets],
        "simulated_shortfall_rate": depletion_rate,
        "net_cash_flow": [net_cash_flow],
        "funding_gap": [funding_gap],
        "taxes": [taxes],
        "pre_tax_assets": [pre_tax],
        "post_tax_assets": [post_tax],
        "roth_assets": [roth],
        "hsa_assets": [hsa],
    }


def _make_result(summary=None, retire_age=67, ss_age=67, wife=None, inflation=0.03, fund_expense=0.005,
                 market_adjustment=100.0, expense_mode=True, expense_multiplier=1.0, withdraw_pct=4.0,
                 stock=0.60, bonds=0.30, cash=0.10):
    return {
        "p": {"summary_results": summary or _make_summary()},
        "sim_config": SimpleNamespace(
            inflation_rate=inflation,
            fund_expense=fund_expense,
            always_use_expense_mode=expense_mode,
            scenario_expense_multiplier=expense_multiplier,
            retirement_withdraw_pct=withdraw_pct,
            custom_stock=stock,
            custom_bonds=bonds,
            custom_cash=cash,
        ),
        "retirement_snapshots": SimpleNamespace(historical_data_multiplier=market_adjustment),
        "husband": SimpleNamespace(age=60, retire_age=retire_age, ss_age=ss_age),
        "wife": wife,
    }


def test_results_frame_builds_expected_metric_rows(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    assert set(frame.metric_rows) == {
        "ending_portfolio", "depletion_rate", "ending_cash_flow", "lifetime_funding_gap", "lifetime_taxes",
        "ending_pre_tax", "ending_after_tax", "ending_roth", "ending_hsa",
    }

    frame.destroy()


def test_update_results_formats_all_summary_metrics(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    baseline = _make_result(summary=_make_summary(
        total_assets=123456, depletion_rate=4.25, net_cash_flow=2345, funding_gap=500, taxes=12345,
        pre_tax=50000, post_tax=30000, roth=25000, hsa=18456,
    ))
    scenario = _make_result(summary=_make_summary(
        total_assets=234567, depletion_rate=1.5, net_cash_flow=3456, funding_gap=100, taxes=15000,
        pre_tax=90000, post_tax=50000, roth=70000, hsa=24567,
    ))

    frame.update_results(baseline, scenario)

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


def test_update_results_returns_without_changes_when_results_missing(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    frame.update_results(None, _make_result())

    assert frame.metric_rows["ending_portfolio"]["original"].cget("text") == "-"
    assert frame.metric_rows["ending_portfolio"]["changed"].cget("text") == "-"

    frame.update_results(_make_result(), None)

    assert frame.metric_rows["ending_portfolio"]["original"].cget("text") == "-"
    assert frame.metric_rows["ending_portfolio"]["changed"].cget("text") == "-"

    frame.destroy()


def test_set_percent_row_displays_dash_when_value_missing(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    frame._set_percent_row("depletion_rate", None, 5.0)

    assert frame.metric_rows["depletion_rate"]["original"].cget("text") == "-"
    assert frame.metric_rows["depletion_rate"]["changed"].cget("text") == "-"

    frame.destroy()


def test_rebuild_assumptions_expense_mode_shows_husband_and_financial_assumptions(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    baseline = _make_result(retire_age=65, ss_age=67, inflation=0.03, fund_expense=0.005,
                            market_adjustment=100.0, expense_mode=True, expense_multiplier=1.0)
    scenario = _make_result(retire_age=66, ss_age=68, inflation=0.04, fund_expense=0.0075,
                            market_adjustment=90.0, expense_mode=True, expense_multiplier=1.25)

    frame._rebuild_assumptions(baseline, scenario)

    texts = [str(widget.cget("text")) for widget in frame.assumptions_frame.winfo_children() if "text" in widget.keys()]

    assert "Husband" in texts
    assert "Retirement Age" in texts
    assert "Social Security Age" in texts
    assert "Inflation Rate" in texts
    assert "Fund Expenses" in texts
    assert "Market Adjustment" in texts
    assert "Expense Multiplier" in texts
    assert "Withdrawal Rate" not in texts

    frame.destroy()


def test_rebuild_assumptions_withdraw_mode_uses_withdrawal_rate(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    baseline = _make_result(expense_mode=False, withdraw_pct=4.0)
    scenario = _make_result(expense_mode=False, withdraw_pct=5.0)

    frame._rebuild_assumptions(baseline, scenario)

    texts = [str(widget.cget("text")) for widget in frame.assumptions_frame.winfo_children() if "text" in widget.keys()]

    assert "Withdrawal Rate" in texts
    assert "Expense Multiplier" not in texts

    frame.destroy()


def test_rebuild_assumptions_includes_wife_only_when_both_results_have_wife(tk_root):
    frame = mod.ScenarioResultsFrame(tk_root)

    baseline_wife = SimpleNamespace(age=58, retire_age=64, ss_age=66)
    scenario_wife = SimpleNamespace(age=58, retire_age=65, ss_age=67)
    baseline = _make_result(wife=baseline_wife)
    scenario = _make_result(wife=scenario_wife)

    frame._rebuild_assumptions(baseline, scenario)

    texts = [str(widget.cget("text")) for widget in frame.assumptions_frame.winfo_children() if "text" in widget.keys()]
    assert "Wife" in texts

    baseline["wife"] = None
    frame._rebuild_assumptions(baseline, scenario)

    texts = [str(widget.cget("text")) for widget in frame.assumptions_frame.winfo_children() if "text" in widget.keys()]
    assert "Wife" not in texts

    frame.destroy()