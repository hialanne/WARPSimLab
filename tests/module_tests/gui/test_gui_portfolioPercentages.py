# tests/module_tests/gui/test_gui_portfolioPercentages.py

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk

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


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk not available: {e}")

    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def mod():
    from src.warpsimlab.gui import gui_portfolioPercentages as module
    return module


def _set_valid_percentages(frame, person_key, *, total="100,000"):
    frame.total_vars[person_key].set(total)

    for bucket, value in {"pre": "40", "post": "30", "roth": "20", "hsa": "10"}.items():
        frame.tax_vars[(person_key, bucket)].set(value)

    for bucket in frame.TAX_BUCKETS:
        frame.asset_vars[(person_key, bucket, "stocks")].set("60")
        frame.asset_vars[(person_key, bucket, "bonds")].set("30")
        frame.asset_vars[(person_key, bucket, "cash")].set("10")


def test_load_from_portfolio_derives_total_and_percentages(mod, tk_root):
    portfolio = DummyPortfolio(
        equity_pre=30000, bond_pre=10000,
        equity_post=15000, bond_post=10000, cash_post=5000,
        equity_roth=15000, cash_roth=5000,
        hsa_equity=5000, hsa_cash=5000,
    )

    frame = mod.PortfolioPercentagesEditFrame(tk_root, husband_portfolio=portfolio)
    frame.pack()

    assert frame.total_vars["husband"].get() == "100,000"

    assert frame.tax_vars[("husband", "pre")].get() == "40.0"
    assert frame.tax_vars[("husband", "post")].get() == "30.0"
    assert frame.tax_vars[("husband", "roth")].get() == "20.0"
    assert frame.tax_vars[("husband", "hsa")].get() == "10.0"

    assert frame.asset_vars[("husband", "pre", "stocks")].get() == "75.0"
    assert frame.asset_vars[("husband", "pre", "bonds")].get() == "25.0"
    assert frame.asset_vars[("husband", "pre", "cash")].get() == "0.0"

    assert frame.tax_total_vars["husband"].get() == "100.0%"
    assert frame.asset_total_vars[("husband", "pre")].get() == "100.0%"


def test_zero_portfolio_uses_zero_tax_allocation_and_stock_default_within_buckets(mod, tk_root):
    portfolio = DummyPortfolio()

    frame = mod.PortfolioPercentagesEditFrame(tk_root, husband_portfolio=portfolio)
    frame.pack()

    assert frame.total_vars["husband"].get() == "0"

    for bucket in frame.TAX_BUCKETS:
        assert frame.tax_vars[("husband", bucket)].get() == "0.0"
        assert frame.asset_vars[("husband", bucket, "stocks")].get() == "100.0"
        assert frame.asset_vars[("husband", bucket, "bonds")].get() == "0.0"
        assert frame.asset_vars[("husband", bucket, "cash")].get() == "0.0"

    assert frame.tax_total_vars["husband"].get() == "0.0%"


def test_apply_percentages_converts_percentages_to_dollar_portfolio(mod, tk_root):
    portfolio = DummyPortfolio()
    frame = mod.PortfolioPercentagesEditFrame(tk_root, husband_portfolio=portfolio)
    frame.pack()

    _set_valid_percentages(frame, "husband")
    frame._apply_percentages()

    assert portfolio.equity_pre == pytest.approx(24000)
    assert portfolio.bond_pre == pytest.approx(12000)
    assert portfolio.cash_pre == pytest.approx(4000)

    assert portfolio.equity_post == pytest.approx(18000)
    assert portfolio.bond_post == pytest.approx(9000)
    assert portfolio.cash_post == pytest.approx(3000)

    assert portfolio.equity_roth == pytest.approx(12000)
    assert portfolio.bond_roth == pytest.approx(6000)
    assert portfolio.cash_roth == pytest.approx(2000)

    assert portfolio.hsa_equity == pytest.approx(6000)
    assert portfolio.hsa_bond == pytest.approx(3000)
    assert portfolio.hsa_cash == pytest.approx(1000)

    assert frame.status_var.get() == "Portfolio updated."


def test_invalid_tax_total_does_not_modify_portfolio(mod, tk_root, monkeypatch):
    portfolio = DummyPortfolio(equity_pre=1234, cash_post=5678)
    frame = mod.PortfolioPercentagesEditFrame(tk_root, husband_portfolio=portfolio)
    frame.pack()

    shown_errors = []
    monkeypatch.setattr(mod.messagebox, "showerror", lambda *args, **kwargs: shown_errors.append((args, kwargs)))

    _set_valid_percentages(frame, "husband")
    frame.tax_vars[("husband", "pre")].set("30")

    frame._apply_percentages()

    assert portfolio.equity_pre == pytest.approx(1234)
    assert portfolio.cash_post == pytest.approx(5678)
    assert frame.status_var.get() == ""
    assert len(shown_errors) == 1
    assert shown_errors[0][0][0] == "Invalid Portfolio Percentages"
    assert "tax bucket percentages must total 100%" in shown_errors[0][0][1]


def test_invalid_asset_total_does_not_modify_portfolio(mod, tk_root, monkeypatch):
    portfolio = DummyPortfolio(equity_pre=1234, cash_post=5678)
    frame = mod.PortfolioPercentagesEditFrame(tk_root, husband_portfolio=portfolio)
    frame.pack()

    shown_errors = []
    monkeypatch.setattr(mod.messagebox, "showerror", lambda *args, **kwargs: shown_errors.append((args, kwargs)))

    _set_valid_percentages(frame, "husband")
    frame.asset_vars[("husband", "post", "stocks")].set("50")

    frame._apply_percentages()

    assert portfolio.equity_pre == pytest.approx(1234)
    assert portfolio.cash_post == pytest.approx(5678)
    assert frame.status_var.get() == ""
    assert len(shown_errors) == 1
    assert "After-Tax Stocks/Bonds/Cash percentages must total 100%" in shown_errors[0][0][1]


def test_couple_apply_is_transactional_when_wife_is_invalid(mod, tk_root, monkeypatch):
    husband = DummyPortfolio(equity_pre=1111)
    wife = DummyPortfolio(equity_pre=2222)

    frame = mod.PortfolioPercentagesEditFrame(
        tk_root, husband_portfolio=husband, wife_portfolio=wife
    )
    frame.pack()

    shown_errors = []
    monkeypatch.setattr(mod.messagebox, "showerror", lambda *args, **kwargs: shown_errors.append((args, kwargs)))

    _set_valid_percentages(frame, "husband", total="100,000")
    _set_valid_percentages(frame, "wife", total="50,000")
    frame.tax_vars[("wife", "hsa")].set("0")

    frame._apply_percentages()

    assert husband.equity_pre == pytest.approx(1111)
    assert wife.equity_pre == pytest.approx(2222)
    assert frame.status_var.get() == ""
    assert len(shown_errors) == 1
    assert "Wife tax bucket percentages must total 100%" in shown_errors[0][0][1]


def test_display_totals_show_invalid_percentage_as_dashes(mod, tk_root):
    portfolio = DummyPortfolio(equity_pre=100)
    frame = mod.PortfolioPercentagesEditFrame(tk_root, husband_portfolio=portfolio)
    frame.pack()

    frame.tax_vars[("husband", "pre")].set("not-a-number")
    frame.asset_vars[("husband", "roth", "stocks")].set("not-a-number")
    frame._update_display_totals()

    assert frame.tax_total_vars["husband"].get() == "--"
    assert frame.asset_total_vars[("husband", "roth")].get() == "--"