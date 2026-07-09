# tests/gui/test_gui_portfolio.py

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk

import pytest


@dataclass
class DummyPortfolio:
    equity_pre: float = 0.0
    equity_post: float = 0.0
    equity_roth: float = 0.0

    bond_pre: float = 0.0
    bond_post: float = 0.0
    bond_roth: float = 0.0

    cash_pre: float = 0.0
    cash_post: float = 0.0
    cash_roth: float = 0.0

    hsa_cash: float = 0.0
    hsa_equity: float = 0.0
    hsa_bond: float = 0.0

    real_estate: float = 0.0


@pytest.fixture
def tk_root():
    """
    Use a withdrawn root for reliability on CI/headless-ish setups.
    Do not assert winfo_ismapped(); use winfo_manager() instead.
    """
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk not available: {e}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def mod_no_tooltip(monkeypatch):
    """
    gui_portfolio imports Tooltip. Patch it to a no-op so tests don't
    depend on tooltip behavior or Tk timing details.
    """
    from src.warpsimlab.gui import gui_portfolio as mod

    class DummyTooltip:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(mod, "Tooltip", DummyTooltip, raising=True)
    return mod


def _all_texts(widget: tk.Misc) -> list[str]:
    """
    Collect visible 'text' strings from common text-bearing widgets.
    (ttk.Checkbutton is critical because 'Derived Statistics' lives there.)
    Only inspects direct children, matching how gui_portfolio lays out its UI.
    """
    out: list[str] = []
    for w in widget.winfo_children():
        if isinstance(w, (ttk.Label, ttk.Checkbutton, ttk.Button, ttk.Radiobutton)):
            try:
                out.append(w.cget("text"))
            except tk.TclError:
                pass
    return out


def _count_entries(widget: tk.Misc) -> int:
    return sum(isinstance(w, ttk.Entry) for w in widget.winfo_children())


def _is_gridded(widget: tk.Misc) -> bool:
    """
    Works even when the root window is withdrawn.
    If managed by grid => "grid"; if removed => "".
    """
    return widget.winfo_manager() == "grid"


def test_basic_mode_builds_only_savings_row(mod_no_tooltip, tk_root):
    mod = mod_no_tooltip

    h = DummyPortfolio(cash_post=1234)
    w = DummyPortfolio(cash_post=999)

    frame = mod.PortfolioEditFrame(tk_root, husband_portfolio=h, wife_portfolio=w, mode="Basic")
    frame.pack()

    texts = _all_texts(frame)
    assert "Savings" in texts

    # In Basic mode, only husband + wife savings entries
    assert _count_entries(frame) == 6

    # Derived toggle is not added in Basic mode (build_fields returns early)
    assert "Derived Statistics" not in texts


def test_bind_var_sets_portfolio_value_and_ignores_invalid(mod_no_tooltip, tk_root, monkeypatch):
    mod = mod_no_tooltip

    h = DummyPortfolio()
    frame = mod.PortfolioEditFrame(tk_root, husband_portfolio=h, wife_portfolio=None, mode="Advanced")
    frame.pack()

    scheduled = {"idle_calls": 0, "cancel_calls": 0}

    def fake_after_idle(fn):
        scheduled["idle_calls"] += 1
        fn()  # run immediately for determinism
        return "ID1"

    def fake_after_cancel(_id):
        scheduled["cancel_calls"] += 1

    monkeypatch.setattr(frame, "after_idle", fake_after_idle, raising=True)
    monkeypatch.setattr(frame, "after_cancel", fake_after_cancel, raising=True)

    called = {"totals": 0}

    monkeypatch.setattr(
        frame,
        "_update_totals",
        lambda: called.__setitem__("totals", called["totals"] + 1),
        raising=True,
    )

    # Valid numeric with commas should parse and set portfolio value
    assert frame._validate_portfolio_field_on_focusout("1,234.5", "husband", "equity_pre") is True

    assert h.equity_pre == pytest.approx(1234.5)
    assert frame.h_vars["equity_pre"].get() == "1,234"

    # Valid path schedules:
    #   1. reformat the edited StringVar
    #   2. update totals
    assert scheduled["idle_calls"] >= 2
    assert called["totals"] >= 1

    prev = h.equity_pre
    prev_idle_calls = scheduled["idle_calls"]

    # Invalid input should be ignored: no portfolio value change.
    assert frame._validate_portfolio_field_on_focusout(
        "not a number",
        "husband",
        "equity_pre",
    ) is True

    assert h.equity_pre == prev
    assert frame.h_vars["equity_pre"].get() == "1,234"

    # Invalid path also schedules:
    #   1. restore formatted current value
    #   2. update totals
    assert scheduled["idle_calls"] >= prev_idle_calls + 2


def test_advanced_mode_builds_roth_hsa_and_total_rows(mod_no_tooltip, tk_root):
    mod = mod_no_tooltip

    h = DummyPortfolio(
        equity_pre=100,
        equity_post=200,
        equity_roth=300,
        bond_pre=400,
        bond_post=500,
        bond_roth=600,
        cash_pre=700,
        cash_post=800,
        cash_roth=900,
        hsa_cash=1000,
    )

    frame = mod.PortfolioEditFrame(
        tk_root,
        husband_portfolio=h,
        wife_portfolio=None,
        mode="Advanced",
    )
    frame.pack()

    texts = _all_texts(frame)

    assert "Stocks Pre-Tax" in texts
    assert "Stocks After-Tax" in texts
    assert "Stocks Roth" in texts
    assert "Bonds Pre-Tax" in texts
    assert "Bonds After-Tax" in texts
    assert "Bonds Roth" in texts
    assert "Cash Pre-Tax" in texts
    assert "Cash After-Tax" in texts
    assert "Cash Roth" in texts
    assert "HSA" in texts
    assert "TOTAL" in texts

    assert frame.h_vars["equity_roth"].get() == "300"
    assert frame.h_vars["bond_roth"].get() == "600"
    assert frame.h_vars["cash_roth"].get() == "900"
    assert frame.h_vars["hsa"].get() == "1,000"

    assert frame.column_total_vars["husband"].get().replace(",", "") == "5500"
    assert frame.column_total_vars["wife"].get() == "--"
    assert frame.column_total_vars["total"].get().replace(",", "") == "5500"


def test_update_totals_populates_row_and_column_totals_for_couple(mod_no_tooltip, tk_root):
    mod = mod_no_tooltip

    h = DummyPortfolio(equity_pre=100, cash_post=50, equity_roth=25)
    w = DummyPortfolio(equity_pre=200, cash_post=75, hsa_cash=10)

    frame = mod.PortfolioEditFrame(
        tk_root,
        husband_portfolio=h,
        wife_portfolio=w,
        mode="Advanced",
    )
    frame.pack()

    frame.h_vars["equity_pre"].set("100")
    frame.w_vars["equity_pre"].set("200")
    frame.h_vars["cash_post"].set("50")
    frame.w_vars["cash_post"].set("75")
    frame.h_vars["equity_roth"].set("25")
    frame.w_vars["hsa"].set("10")

    frame._update_totals()

    assert frame.row_total_vars["equity_pre"].get() == "300"
    assert frame.row_total_vars["cash_post"].get() == "125"
    assert frame.row_total_vars["equity_roth"].get() == "25"
    assert frame.row_total_vars["hsa"].get() == "10"

    assert frame.column_total_vars["husband"].get() == "175"
    assert frame.column_total_vars["wife"].get() == "285"
    assert frame.column_total_vars["total"].get() == "460"


def test_hsa_total_combines_cash_equity_and_bond(mod_no_tooltip, tk_root):
    mod = mod_no_tooltip

    h = DummyPortfolio(hsa_cash=10, hsa_equity=20, hsa_bond=30)

    frame = mod.PortfolioEditFrame(
        tk_root,
        husband_portfolio=h,
        wife_portfolio=None,
        mode="Advanced",
    )
    frame.pack()

    assert frame._get_hsa_total(h) == pytest.approx(60.0)
    assert frame.h_vars["hsa"].get() == "60"


def test_hsa_total_combines_cash_equity_and_bond(mod_no_tooltip, tk_root):
    mod = mod_no_tooltip

    h = DummyPortfolio(hsa_cash=10, hsa_equity=20, hsa_bond=30)

    frame = mod.PortfolioEditFrame(
        tk_root,
        husband_portfolio=h,
        wife_portfolio=None,
        mode="Advanced",
    )
    frame.pack()

    assert frame._get_hsa_total(h) == pytest.approx(60.0)
    assert frame.h_vars["hsa"].get() == "60"


def test_validate_hsa_stores_hsa_as_cash_only(mod_no_tooltip, tk_root, monkeypatch):
    mod = mod_no_tooltip

    h = DummyPortfolio(hsa_cash=10, hsa_equity=20, hsa_bond=30)

    frame = mod.PortfolioEditFrame(
        tk_root,
        husband_portfolio=h,
        wife_portfolio=None,
        mode="Advanced",
    )
    frame.pack()

    monkeypatch.setattr(frame, "after_idle", lambda fn: fn(), raising=True)

    assert frame._validate_portfolio_field_on_focusout("1,234", "husband", "hsa") is True

    assert h.hsa_cash == pytest.approx(1234.0)
    assert h.hsa_equity == pytest.approx(0.0)
    assert h.hsa_bond == pytest.approx(0.0)
    assert frame.h_vars["hsa"].get() == "1,234"