# test_portfolio.py

from __future__ import annotations

from src.warpsimlab.dataClasses.portfolio import Portfolio


def test_portfolio_assigns_fields():
    p = Portfolio(
        equity_pre=100.0,
        equity_post=200.0,
        bond_pre=10.0,
        bond_post=20.0,
        cash_pre=1.0,
        cash_post=2.0,
        real_estate=999.0,
    )

    assert p.equity_pre == 100.0
    assert p.equity_post == 200.0
    assert p.bond_pre == 10.0
    assert p.bond_post == 20.0
    assert p.cash_pre == 1.0
    assert p.cash_post == 2.0
    assert p.real_estate == 999.0


def test_portfolio_accepts_ints_and_preserves_values():
    p = Portfolio(
        equity_pre=1,
        equity_post=2,
        bond_pre=3,
        bond_post=4,
        cash_pre=5,
        cash_post=6,
        real_estate=7,
    )

    assert p.equity_pre == 1
    assert p.equity_post == 2
    assert p.bond_pre == 3
    assert p.bond_post == 4
    assert p.cash_pre == 5
    assert p.cash_post == 6
    assert p.real_estate == 7