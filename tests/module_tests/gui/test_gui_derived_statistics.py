from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk

import pytest

from src.warpsimlab.gui.gui_derivedStatistics import DerivedStatisticsFrame


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
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk not available: {e}")

    root.withdraw()
    yield root
    root.destroy()


def _label_texts(widget: tk.Misc) -> list[str]:
    out = []
    for child in widget.winfo_children():
        if isinstance(child, ttk.Label):
            try:
                out.append(child.cget("text"))
            except tk.TclError:
                pass
    return out


def _entry_count(widget: tk.Misc) -> int:
    return sum(isinstance(child, ttk.Entry) for child in widget.winfo_children())


def test_builds_expected_readonly_rows(tk_root):
    h = DummyPortfolio()

    frame = DerivedStatisticsFrame(
        tk_root,
        husband_portfolio=h,
        wife_portfolio=None,
        mode="Advanced",
    )
    frame.pack()

    texts = _label_texts(frame)

    assert "Balance Sheet Summary" in texts
    assert "Investable Assets" in texts
    assert "Real Estate" in texts
    assert "Total Wealth" in texts

    assert "Tax Bucket Percentages" in texts
    assert "Pre-Tax" in texts
    assert "After-Tax" in texts
    assert "Roth" in texts
    assert "HSA" in texts

    assert "Asset Class Percentages" in texts
    assert "Stocks" in texts
    assert "Bonds" in texts
    assert "Cash" in texts

    expected_keys = {
        "investable_assets",
        "real_estate",
        "total_wealth",
        "pct_pre",
        "pct_post",
        "pct_roth",
        "pct_hsa",
        "pct_equity",
        "pct_bonds",
        "pct_cash",
    }

    assert set(frame.vars) == expected_keys
    assert _entry_count(frame) == len(expected_keys)


def test_format_money_rounds_and_adds_commas(tk_root):
    frame = DerivedStatisticsFrame(
        tk_root,
        husband_portfolio=DummyPortfolio(),
    )

    assert frame._format_money(123456.78) == "123,457"
    assert frame._format_money(0) == "0"


def test_format_pct_uses_one_decimal_and_width(tk_root):
    frame = DerivedStatisticsFrame(
        tk_root,
        husband_portfolio=DummyPortfolio(),
    )

    assert frame._format_pct(50) == " 50.0%"
    assert frame._format_pct(5.25) == "  5.2%"


def test_portfolio_value_returns_zero_for_missing_portfolio_or_missing_attribute(tk_root):
    frame = DerivedStatisticsFrame(
        tk_root,
        husband_portfolio=DummyPortfolio(),
    )

    assert frame._portfolio_value(None, "equity_pre") == pytest.approx(0.0)
    assert frame._portfolio_value(DummyPortfolio(equity_pre=123.0), "equity_pre") == pytest.approx(123.0)
    assert frame._portfolio_value(DummyPortfolio(), "does_not_exist") == pytest.approx(0.0)


def test_hsa_total_sums_cash_equity_and_bond(tk_root):
    portfolio = DummyPortfolio(
        hsa_cash=10.0,
        hsa_equity=20.0,
        hsa_bond=30.0,
    )

    frame = DerivedStatisticsFrame(
        tk_root,
        husband_portfolio=portfolio,
    )

    assert frame._hsa_total(portfolio) == pytest.approx(60.0)
    assert frame._hsa_total(None) == pytest.approx(0.0)


def test_combined_sums_husband_and_wife_values(tk_root):
    h = DummyPortfolio(equity_pre=10.0)
    w = DummyPortfolio(equity_pre=20.0)

    frame = DerivedStatisticsFrame(
        tk_root,
        husband_portfolio=h,
        wife_portfolio=w,
    )

    assert frame._combined("equity_pre") == pytest.approx(30.0)


def test_combined_treats_missing_wife_as_zero(tk_root):
    h = DummyPortfolio(equity_pre=10.0)

    frame = DerivedStatisticsFrame(
        tk_root,
        husband_portfolio=h,
        wife_portfolio=None,
    )

    assert frame._combined("equity_pre") == pytest.approx(10.0)


def test_combined_hsa_sums_husband_and_wife_hsa(tk_root):
    h = DummyPortfolio(hsa_cash=10.0, hsa_equity=20.0, hsa_bond=30.0)
    w = DummyPortfolio(hsa_cash=1.0, hsa_equity=2.0, hsa_bond=3.0)

    frame = DerivedStatisticsFrame(
        tk_root,
        husband_portfolio=h,
        wife_portfolio=w,
    )

    assert frame._combined_hsa() == pytest.approx(66.0)


def test_safe_pct_returns_double_dash_for_zero_or_negative_denominator(tk_root):
    frame = DerivedStatisticsFrame(
        tk_root,
        husband_portfolio=DummyPortfolio(),
    )

    assert frame._safe_pct(10.0, 0.0) == "--"
    assert frame._safe_pct(10.0, -1.0) == "--"


def test_safe_pct_formats_valid_percentage(tk_root):
    frame = DerivedStatisticsFrame(
        tk_root,
        husband_portfolio=DummyPortfolio(),
    )

    assert frame._safe_pct(25.0, 100.0) == " 25.0%"


def test_update_statistics_single_person_full_balances(tk_root):
    h = DummyPortfolio(
        equity_pre=100.0,
        equity_post=200.0,
        equity_roth=300.0,
        bond_pre=400.0,
        bond_post=500.0,
        bond_roth=600.0,
        cash_pre=700.0,
        cash_post=800.0,
        cash_roth=900.0,
        hsa_cash=1000.0,
        hsa_equity=1100.0,
        hsa_bond=1200.0,
        real_estate=1300.0,
    )

    frame = DerivedStatisticsFrame(
        tk_root,
        husband_portfolio=h,
        wife_portfolio=None,
    )

    # Asset-class totals:
    # equity = 100 + 200 + 300 + 1100 = 1700
    # bonds  = 400 + 500 + 600 + 1200 = 2700
    # cash   = 700 + 800 + 900 + 1000 = 3400
    # investable = 7800
    assert frame.vars["investable_assets"].get() == "7,800"
    assert frame.vars["real_estate"].get() == "1,300"
    assert frame.vars["total_wealth"].get() == "9,100"

    # Tax buckets:
    # pre  = 100 + 400 + 700 = 1200 = 15.3846%
    # post = 200 + 500 + 800 = 1500 = 19.2308%
    # roth = 300 + 600 + 900 = 1800 = 23.0769%
    # hsa  = 1000 + 1100 + 1200 = 3300 = 42.3077%
    assert frame.vars["pct_pre"].get() == " 15.4%"
    assert frame.vars["pct_post"].get() == " 19.2%"
    assert frame.vars["pct_roth"].get() == " 23.1%"
    assert frame.vars["pct_hsa"].get() == " 42.3%"

    # Asset-class percentages:
    # equity = 1700 / 7800 = 21.7949%
    # bonds  = 2700 / 7800 = 34.6154%
    # cash   = 3400 / 7800 = 43.5897%
    assert frame.vars["pct_equity"].get() == " 21.8%"
    assert frame.vars["pct_bonds"].get() == " 34.6%"
    assert frame.vars["pct_cash"].get() == " 43.6%"


def test_update_statistics_combines_husband_and_wife(tk_root):
    h = DummyPortfolio(
        equity_pre=100.0,
        cash_post=200.0,
        hsa_cash=300.0,
        real_estate=400.0,
    )
    w = DummyPortfolio(
        equity_pre=10.0,
        cash_post=20.0,
        hsa_cash=30.0,
        real_estate=40.0,
    )

    frame = DerivedStatisticsFrame(
        tk_root,
        husband_portfolio=h,
        wife_portfolio=w,
    )

    # investable = equity_pre 110 + cash_post 220 + hsa_cash 330 = 660
    # real estate = 440
    assert frame.vars["investable_assets"].get() == "660"
    assert frame.vars["real_estate"].get() == "440"
    assert frame.vars["total_wealth"].get() == "1,100"

    # pre = 110 / 660 = 16.6667%
    # post = 220 / 660 = 33.3333%
    # hsa = 330 / 660 = 50.0%
    assert frame.vars["pct_pre"].get() == " 16.7%"
    assert frame.vars["pct_post"].get() == " 33.3%"
    assert frame.vars["pct_roth"].get() == "  0.0%"
    assert frame.vars["pct_hsa"].get() == " 50.0%"

    assert frame.vars["pct_equity"].get() == " 16.7%"
    assert frame.vars["pct_bonds"].get() == "  0.0%"
    assert frame.vars["pct_cash"].get() == " 83.3%"


def test_update_statistics_zero_investable_assets_sets_percentages_to_double_dash(tk_root):
    h = DummyPortfolio(real_estate=1000.0)

    frame = DerivedStatisticsFrame(
        tk_root,
        husband_portfolio=h,
        wife_portfolio=None,
    )

    assert frame.vars["investable_assets"].get() == "0"
    assert frame.vars["real_estate"].get() == "1,000"
    assert frame.vars["total_wealth"].get() == "1,000"

    assert frame.vars["pct_pre"].get() == "--"
    assert frame.vars["pct_post"].get() == "--"
    assert frame.vars["pct_roth"].get() == "--"
    assert frame.vars["pct_hsa"].get() == "--"
    assert frame.vars["pct_equity"].get() == "--"
    assert frame.vars["pct_bonds"].get() == "--"
    assert frame.vars["pct_cash"].get() == "--"


def test_update_statistics_can_be_recomputed_after_portfolio_changes(tk_root):
    h = DummyPortfolio(equity_pre=100.0)

    frame = DerivedStatisticsFrame(
        tk_root,
        husband_portfolio=h,
        wife_portfolio=None,
    )

    assert frame.vars["investable_assets"].get() == "100"
    assert frame.vars["pct_equity"].get() == "100.0%"

    h.cash_post = 300.0
    frame._update_statistics()

    assert frame.vars["investable_assets"].get() == "400"
    assert frame.vars["pct_equity"].get() == " 25.0%"
    assert frame.vars["pct_cash"].get() == " 75.0%"