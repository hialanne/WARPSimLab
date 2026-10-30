# test_portfolioState.py

from __future__ import annotations

import pytest

from src.warpsimlab.dataClasses.portfolioState import PortfolioState


def make_state():
    return PortfolioState(
        eq_pre=100,
        bd_pre=50,
        cs_pre=25,
        eq_post=200,
        bd_post=75,
        cs_post=50,
        re_post=500
    )


def test_total_value():
    s = make_state()

    expected = 100 + 50 + 25 + 200 + 75 + 50
    assert s.total_value == expected


def test_total_value_including_real_estate():
    s = make_state()

    expected = (100 + 50 + 25 + 200 + 75 + 50) + 500
    assert s.total_value_including_real_estate == expected


def test_total_value_pre():
    s = make_state()

    expected = 100 + 50 + 25
    assert s.total_value_pre == expected


def test_total_value_post():
    s = make_state()

    expected = 200 + 75 + 50
    assert s.total_value_post == expected


def test_total_value_cash():
    s = make_state()

    assert s.total_value_cash == 25 + 50


def test_total_value_bonds():
    s = make_state()

    assert s.total_value_bonds == 50 + 75


def test_ratios_initially_zero():
    s = make_state()

    assert s.eq_ratio_pre == 0
    assert s.bd_ratio_pre == 0
    assert s.cs_ratio_pre == 0
    assert s.eq_ratio_post == 0
    assert s.bd_ratio_post == 0
    assert s.cs_ratio_post == 0


def test_roth_and_hsa_buckets_participate_in_account_and_asset_totals():
    s = PortfolioState(1, 2, 3, 4, 5, 6, 1000,
                       eq_roth=10, bd_roth=20, cs_roth=30,
                       hsa_eq=100, hsa_bd=200, hsa_cs=300)
    assert s.total_value_roth == 60
    assert s.total_value_hsa == 600
    assert s.total_value == 681
    assert s.total_value_including_real_estate == 1681
    assert s.total_value_equity == 115
    assert s.total_value_bonds == 227
    assert s.total_value_cash == 339
    s.hsa_cs = 0
    assert s.total_value == 381
    assert s.total_value_cash == 39
