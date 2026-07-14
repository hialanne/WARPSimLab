from __future__ import annotations

import pytest

from src.warpsimlab.dataClasses.portfolioState import PortfolioState
from src.warpsimlab.sim.engines import portfolioEngine


def make_portfolio(
    *,
    eq_pre=0.0,
    bd_pre=0.0,
    cs_pre=0.0,
    eq_post=0.0,
    bd_post=0.0,
    cs_post=0.0,
    eq_roth=0.0,
    bd_roth=0.0,
    cs_roth=0.0,
):
    return PortfolioState(
        eq_pre=eq_pre,
        bd_pre=bd_pre,
        cs_pre=cs_pre,
        eq_post=eq_post,
        bd_post=bd_post,
        cs_post=cs_post,
        eq_roth=eq_roth,
        bd_roth=bd_roth,
        cs_roth=cs_roth,
        hsa_eq=0.0,
        hsa_bd=0.0,
        hsa_cs=0.0,
        re_post=0.0,
    )


@pytest.mark.parametrize("amount", [0.0, -1.0, -1000.0])
def test_apply_roth_contribution_ignores_non_positive_amounts(amount):
    port = make_portfolio(
        eq_roth=100.0,
        bd_roth=200.0,
        cs_roth=300.0,
    )

    before_total = port.total_value_roth

    result = portfolioEngine.apply_roth_contribution(
        port,
        amount,
    )

    assert result == 0.0
    assert port.eq_roth == pytest.approx(100.0)
    assert port.bd_roth == pytest.approx(200.0)
    assert port.cs_roth == pytest.approx(300.0)
    assert port.total_value_roth == pytest.approx(before_total)


def test_apply_roth_contribution_adds_new_money_to_roth_cash_only():
    port = make_portfolio(
        eq_roth=1000.0,
        bd_roth=2000.0,
        cs_roth=3000.0,
    )

    before_total = port.total_value
    before_roth_total = port.total_value_roth

    result = portfolioEngine.apply_roth_contribution(
        port,
        4000.0,
    )

    assert result == pytest.approx(4000.0)
    assert port.eq_roth == pytest.approx(1000.0)
    assert port.bd_roth == pytest.approx(2000.0)
    assert port.cs_roth == pytest.approx(7000.0)
    assert port.total_value_roth == pytest.approx(
        before_roth_total + 4000.0
    )
    assert port.total_value == pytest.approx(
        before_total + 4000.0
    )


@pytest.mark.parametrize("amount", [0.0, -1.0, -1000.0])
def test_convert_pre_tax_to_roth_ignores_non_positive_amounts(amount):
    port = make_portfolio(
        eq_pre=6000.0,
        bd_pre=3000.0,
        cs_pre=1000.0,
    )

    before_total = port.total_value

    result = portfolioEngine.convert_pre_tax_to_roth(
        port,
        amount,
    )

    assert result == 0.0
    assert port.eq_pre == pytest.approx(6000.0)
    assert port.bd_pre == pytest.approx(3000.0)
    assert port.cs_pre == pytest.approx(1000.0)
    assert port.total_value_roth == pytest.approx(0.0)
    assert port.total_value == pytest.approx(before_total)


def test_convert_pre_tax_to_roth_returns_zero_when_pre_tax_bucket_empty():
    port = make_portfolio(
        eq_roth=1000.0,
        bd_roth=500.0,
        cs_roth=250.0,
    )

    before_total = port.total_value

    result = portfolioEngine.convert_pre_tax_to_roth(
        port,
        5000.0,
    )

    assert result == 0.0
    assert port.total_value_pre == pytest.approx(0.0)
    assert port.total_value_roth == pytest.approx(1750.0)
    assert port.total_value == pytest.approx(before_total)


def test_convert_pre_tax_to_roth_preserves_asset_mix():
    port = make_portfolio(
        eq_pre=6000.0,
        bd_pre=3000.0,
        cs_pre=1000.0,
    )

    result = portfolioEngine.convert_pre_tax_to_roth(
        port,
        4000.0,
    )

    assert result == pytest.approx(4000.0)

    assert port.eq_pre == pytest.approx(3600.0)
    assert port.bd_pre == pytest.approx(1800.0)
    assert port.cs_pre == pytest.approx(600.0)

    assert port.eq_roth == pytest.approx(2400.0)
    assert port.bd_roth == pytest.approx(1200.0)
    assert port.cs_roth == pytest.approx(400.0)

    assert port.eq_roth / port.total_value_roth == pytest.approx(0.60)
    assert port.bd_roth / port.total_value_roth == pytest.approx(0.30)
    assert port.cs_roth / port.total_value_roth == pytest.approx(0.10)


def test_convert_pre_tax_to_roth_adds_to_existing_roth_balances():
    port = make_portfolio(
        eq_pre=6000.0,
        bd_pre=3000.0,
        cs_pre=1000.0,
        eq_roth=100.0,
        bd_roth=200.0,
        cs_roth=300.0,
    )

    result = portfolioEngine.convert_pre_tax_to_roth(
        port,
        4000.0,
    )

    assert result == pytest.approx(4000.0)
    assert port.eq_roth == pytest.approx(2500.0)
    assert port.bd_roth == pytest.approx(1400.0)
    assert port.cs_roth == pytest.approx(700.0)


def test_convert_pre_tax_to_roth_caps_at_available_pre_tax_assets():
    port = make_portfolio(
        eq_pre=6000.0,
        bd_pre=3000.0,
        cs_pre=1000.0,
    )

    result = portfolioEngine.convert_pre_tax_to_roth(
        port,
        15000.0,
    )

    assert result == pytest.approx(10000.0)
    assert port.total_value_pre == pytest.approx(0.0)
    assert port.eq_pre == pytest.approx(0.0)
    assert port.bd_pre == pytest.approx(0.0)
    assert port.cs_pre == pytest.approx(0.0)

    assert port.eq_roth == pytest.approx(6000.0)
    assert port.bd_roth == pytest.approx(3000.0)
    assert port.cs_roth == pytest.approx(1000.0)


@pytest.mark.parametrize(
    "requested",
    [
        1.0,
        2500.0,
        10000.0,
        15000.0,
    ],
)
def test_convert_pre_tax_to_roth_preserves_total_portfolio_value(requested):
    port = make_portfolio(
        eq_pre=6000.0,
        bd_pre=3000.0,
        cs_pre=1000.0,
        eq_post=5000.0,
        bd_post=2000.0,
        cs_post=1000.0,
        eq_roth=100.0,
        bd_roth=200.0,
        cs_roth=300.0,
    )

    before_total = port.total_value

    portfolioEngine.convert_pre_tax_to_roth(
        port,
        requested,
    )

    assert port.total_value == pytest.approx(before_total)


def test_convert_pre_tax_to_roth_does_not_change_post_tax_assets():
    port = make_portfolio(
        eq_pre=6000.0,
        bd_pre=3000.0,
        cs_pre=1000.0,
        eq_post=5000.0,
        bd_post=2000.0,
        cs_post=1000.0,
    )

    portfolioEngine.convert_pre_tax_to_roth(
        port,
        4000.0,
    )

    assert port.eq_post == pytest.approx(5000.0)
    assert port.bd_post == pytest.approx(2000.0)
    assert port.cs_post == pytest.approx(1000.0)


def test_convert_pre_tax_to_roth_leaves_no_negative_components_after_full_conversion():
    port = make_portfolio(
        eq_pre=0.1,
        bd_pre=0.2,
        cs_pre=0.3,
    )

    result = portfolioEngine.convert_pre_tax_to_roth(
        port,
        1000.0,
    )

    assert result == pytest.approx(0.6)
    assert port.eq_pre >= 0.0
    assert port.bd_pre >= 0.0
    assert port.cs_pre >= 0.0
    assert port.eq_roth >= 0.0
    assert port.bd_roth >= 0.0
    assert port.cs_roth >= 0.0