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
        if isinstance(child, (ttk.Label, ttk.LabelFrame)):
            try:
                out.append(child.cget("text"))
            except tk.TclError:
                pass

        out.extend(_label_texts(child))

    return out


def _entry_count(widget: tk.Misc) -> int:
    return sum(isinstance(child, ttk.Entry) for child in widget.winfo_children()) + sum(
        _entry_count(child) for child in widget.winfo_children()
    )


def test_builds_expected_readonly_rows(tk_root):
    frame = DerivedStatisticsFrame(tk_root, husband_portfolio=DummyPortfolio(), wife_portfolio=None, mode="Advanced")
    frame.pack()

    texts = _label_texts(frame)

    assert "Balance Sheet Summary" in texts
    assert "Investable Assets" in texts
    assert "Real Estate" in texts
    assert "Total Wealth" in texts

    assert "Overall Asset Allocation" in texts
    assert "Stocks" in texts
    assert "Bonds" in texts
    assert "Cash" in texts

    assert "Portfolio by Tax Bucket" in texts
    assert "Pre-Tax" in texts
    assert "After-Tax" in texts
    assert "Roth" in texts
    assert "HSA" in texts
    assert "Total" in texts

    expected_keys = {
        "summary_investable_husband", "summary_investable_wife", "summary_investable_household",
        "summary_investable_pct", "summary_real_estate_husband", "summary_real_estate_wife",
        "summary_real_estate_household", "summary_real_estate_pct", "summary_wealth_husband",
        "summary_wealth_wife", "summary_wealth_household", "summary_wealth_pct",
        "overall_stocks_dollars", "overall_stocks_pct", "overall_bonds_dollars", "overall_bonds_pct",
        "overall_cash_dollars", "overall_cash_pct", "overall_total_dollars", "overall_total_pct",
    }

    for bucket in ("pre", "post", "roth", "hsa", "total"):
        expected_keys.update({
            f"bucket_{bucket}_dollars",
            f"bucket_{bucket}_portfolio_pct",
            f"bucket_{bucket}_stocks_pct",
            f"bucket_{bucket}_bonds_pct",
            f"bucket_{bucket}_cash_pct",
        })

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
        equity_pre=100.0, equity_post=200.0, equity_roth=300.0,
        bond_pre=400.0, bond_post=500.0, bond_roth=600.0,
        cash_pre=700.0, cash_post=800.0, cash_roth=900.0,
        hsa_cash=1000.0, hsa_equity=1100.0, hsa_bond=1200.0, real_estate=1300.0,
    )

    frame = DerivedStatisticsFrame(tk_root, husband_portfolio=h, wife_portfolio=None)

    assert frame.vars["summary_investable_husband"].get() == "7,800"
    assert frame.vars["summary_investable_wife"].get() == "--"
    assert frame.vars["summary_investable_household"].get() == "7,800"
    assert frame.vars["summary_investable_pct"].get() == " 85.7%"

    assert frame.vars["summary_real_estate_husband"].get() == "1,300"
    assert frame.vars["summary_real_estate_household"].get() == "1,300"
    assert frame.vars["summary_real_estate_pct"].get() == " 14.3%"

    assert frame.vars["summary_wealth_husband"].get() == "9,100"
    assert frame.vars["summary_wealth_household"].get() == "9,100"
    assert frame.vars["summary_wealth_pct"].get() == "100.0%"

    assert frame.vars["overall_stocks_dollars"].get() == "1,700"
    assert frame.vars["overall_stocks_pct"].get() == " 21.8%"
    assert frame.vars["overall_bonds_dollars"].get() == "2,700"
    assert frame.vars["overall_bonds_pct"].get() == " 34.6%"
    assert frame.vars["overall_cash_dollars"].get() == "3,400"
    assert frame.vars["overall_cash_pct"].get() == " 43.6%"
    assert frame.vars["overall_total_dollars"].get() == "7,800"
    assert frame.vars["overall_total_pct"].get() == "100.0%"

    assert frame.vars["bucket_pre_dollars"].get() == "1,200"
    assert frame.vars["bucket_pre_portfolio_pct"].get() == " 15.4%"
    assert frame.vars["bucket_pre_stocks_pct"].get() == "  8.3%"
    assert frame.vars["bucket_pre_bonds_pct"].get() == " 33.3%"
    assert frame.vars["bucket_pre_cash_pct"].get() == " 58.3%"

    assert frame.vars["bucket_post_dollars"].get() == "1,500"
    assert frame.vars["bucket_post_portfolio_pct"].get() == " 19.2%"
    assert frame.vars["bucket_roth_dollars"].get() == "1,800"
    assert frame.vars["bucket_roth_portfolio_pct"].get() == " 23.1%"
    assert frame.vars["bucket_hsa_dollars"].get() == "3,300"
    assert frame.vars["bucket_hsa_portfolio_pct"].get() == " 42.3%"

    assert frame.vars["bucket_total_dollars"].get() == "7,800"
    assert frame.vars["bucket_total_portfolio_pct"].get() == "100.0%"
    assert frame.vars["bucket_total_stocks_pct"].get() == " 21.8%"
    assert frame.vars["bucket_total_bonds_pct"].get() == " 34.6%"
    assert frame.vars["bucket_total_cash_pct"].get() == " 43.6%"


def test_update_statistics_combines_husband_and_wife(tk_root):
    h = DummyPortfolio(equity_pre=100.0, cash_post=200.0, hsa_cash=300.0, real_estate=400.0)
    w = DummyPortfolio(equity_pre=10.0, cash_post=20.0, hsa_cash=30.0, real_estate=40.0)

    frame = DerivedStatisticsFrame(tk_root, husband_portfolio=h, wife_portfolio=w)

    assert frame.vars["summary_investable_husband"].get() == "600"
    assert frame.vars["summary_investable_wife"].get() == "60"
    assert frame.vars["summary_investable_household"].get() == "660"

    assert frame.vars["summary_real_estate_husband"].get() == "400"
    assert frame.vars["summary_real_estate_wife"].get() == "40"
    assert frame.vars["summary_real_estate_household"].get() == "440"

    assert frame.vars["summary_wealth_husband"].get() == "1,000"
    assert frame.vars["summary_wealth_wife"].get() == "100"
    assert frame.vars["summary_wealth_household"].get() == "1,100"

    assert frame.vars["overall_stocks_dollars"].get() == "110"
    assert frame.vars["overall_stocks_pct"].get() == " 16.7%"
    assert frame.vars["overall_bonds_dollars"].get() == "0"
    assert frame.vars["overall_bonds_pct"].get() == "  0.0%"
    assert frame.vars["overall_cash_dollars"].get() == "550"
    assert frame.vars["overall_cash_pct"].get() == " 83.3%"

    assert frame.vars["bucket_pre_dollars"].get() == "110"
    assert frame.vars["bucket_pre_portfolio_pct"].get() == " 16.7%"
    assert frame.vars["bucket_pre_stocks_pct"].get() == "100.0%"

    assert frame.vars["bucket_post_dollars"].get() == "220"
    assert frame.vars["bucket_post_portfolio_pct"].get() == " 33.3%"
    assert frame.vars["bucket_post_cash_pct"].get() == "100.0%"

    assert frame.vars["bucket_roth_dollars"].get() == "0"
    assert frame.vars["bucket_roth_portfolio_pct"].get() == "  0.0%"
    assert frame.vars["bucket_roth_stocks_pct"].get() == "--"
    assert frame.vars["bucket_roth_bonds_pct"].get() == "--"
    assert frame.vars["bucket_roth_cash_pct"].get() == "--"

    assert frame.vars["bucket_hsa_dollars"].get() == "330"
    assert frame.vars["bucket_hsa_portfolio_pct"].get() == " 50.0%"
    assert frame.vars["bucket_hsa_cash_pct"].get() == "100.0%"

    assert frame.vars["bucket_total_dollars"].get() == "660"
    assert frame.vars["bucket_total_portfolio_pct"].get() == "100.0%"
    assert frame.vars["bucket_total_stocks_pct"].get() == " 16.7%"
    assert frame.vars["bucket_total_bonds_pct"].get() == "  0.0%"
    assert frame.vars["bucket_total_cash_pct"].get() == " 83.3%"


def test_update_statistics_zero_investable_assets_sets_percentages_to_double_dash(tk_root):
    frame = DerivedStatisticsFrame(tk_root, husband_portfolio=DummyPortfolio(real_estate=1000.0), wife_portfolio=None)

    assert frame.vars["summary_investable_husband"].get() == "0"
    assert frame.vars["summary_investable_household"].get() == "0"
    assert frame.vars["summary_investable_pct"].get() == "  0.0%"

    assert frame.vars["summary_real_estate_household"].get() == "1,000"
    assert frame.vars["summary_real_estate_pct"].get() == "100.0%"
    assert frame.vars["summary_wealth_household"].get() == "1,000"
    assert frame.vars["summary_wealth_pct"].get() == "100.0%"

    for key in ("stocks", "bonds", "cash", "total"):
        assert frame.vars[f"overall_{key}_pct"].get() == "--"

    for bucket in ("pre", "post", "roth", "hsa", "total"):
        assert frame.vars[f"bucket_{bucket}_dollars"].get() == "0"
        assert frame.vars[f"bucket_{bucket}_portfolio_pct"].get() == "--"
        assert frame.vars[f"bucket_{bucket}_stocks_pct"].get() == "--"
        assert frame.vars[f"bucket_{bucket}_bonds_pct"].get() == "--"
        assert frame.vars[f"bucket_{bucket}_cash_pct"].get() == "--"


def test_update_statistics_can_be_recomputed_after_portfolio_changes(tk_root):
    h = DummyPortfolio(equity_pre=100.0)
    frame = DerivedStatisticsFrame(tk_root, husband_portfolio=h, wife_portfolio=None)

    assert frame.vars["summary_investable_household"].get() == "100"
    assert frame.vars["overall_stocks_pct"].get() == "100.0%"
    assert frame.vars["bucket_pre_portfolio_pct"].get() == "100.0%"

    h.cash_post = 300.0
    frame._update_statistics()

    assert frame.vars["summary_investable_household"].get() == "400"
    assert frame.vars["overall_stocks_pct"].get() == " 25.0%"
    assert frame.vars["overall_cash_pct"].get() == " 75.0%"
    assert frame.vars["bucket_pre_portfolio_pct"].get() == " 25.0%"
    assert frame.vars["bucket_post_portfolio_pct"].get() == " 75.0%"