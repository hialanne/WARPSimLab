from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.dataClasses.portfolioState import PortfolioState
from src.warpsimlab.sim.engines import withdrawalEngine


def make_person(*, age=60, retire_age=60):
    return SimpleNamespace(age=age, retire_age=retire_age)


def make_portfolio_state(
    *,
    pre_tax=0.0,
    post_tax=0.0,
    roth=0.0,
    hsa=0.0,
    real_estate=0.0,
):
    return PortfolioState(
        eq_pre=float(pre_tax),
        bd_pre=0.0,
        cs_pre=0.0,
        eq_post=float(post_tax),
        bd_post=0.0,
        cs_post=0.0,
        re_post=float(real_estate),
        eq_roth=float(roth),
        bd_roth=0.0,
        cs_roth=0.0,
        hsa_eq=float(hsa),
        hsa_bd=0.0,
        hsa_cs=0.0,
    )


def make_config(
    *,
    withdrawal_amount,
    second_person_enabled=False,
    withdrawal_mode="Fixed Dollar Amount",
    inflation_rate=0.0,
):
    return SimpleNamespace(
        include_rmd=False,
        second_person_enabled=second_person_enabled,
        retirement_withdraw_mode=withdrawal_mode,
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=float(withdrawal_amount),
        inflation_rate=float(inflation_rate),
        subplot_mode="baseline",
        sim_type="portfolio_sim",
        monte_carlo_mode="pathBasedAnnualSampling",
        _ret_withdraw_base_dollars=None,
    )


def calculate_withdrawal(
    husband_portfolio,
    wife_portfolio,
    config,
    *,
    year=0,
    additional_cash_needed=0.0,
):
    return withdrawalEngine.calculate_retirement_withdrawal(
        husband_portfolio,
        wife_portfolio,
        make_person(),
        make_person(),
        year,
        config,
        additional_cash_needed=additional_cash_needed,
    )


def test_couple_withdrawal_uses_larger_spouse_post_tax_balance_first():
    husband_portfolio = make_portfolio_state(post_tax=100_000.0)
    wife_portfolio = make_portfolio_state(post_tax=60_000.0)
    config = make_config(
        withdrawal_amount=80_000.0,
        second_person_enabled=True,
    )

    result = calculate_withdrawal(
        husband_portfolio,
        wife_portfolio,
        config,
    )

    assert result["total"] == pytest.approx(80_000.0)
    assert result["post_tax"] == pytest.approx(80_000.0)
    assert result["by_person"] == pytest.approx(
        {"husband": 80_000.0, "wife": 0.0}
    )
    assert husband_portfolio.total_value_post == pytest.approx(20_000.0)
    assert wife_portfolio.total_value_post == pytest.approx(60_000.0)


def test_couple_withdrawal_reorders_by_balance_for_each_account_type():
    husband_portfolio = make_portfolio_state(
        post_tax=100_000.0,
        pre_tax=10_000.0,
    )
    wife_portfolio = make_portfolio_state(
        post_tax=20_000.0,
        pre_tax=100_000.0,
    )
    config = make_config(
        withdrawal_amount=150_000.0,
        second_person_enabled=True,
    )

    result = calculate_withdrawal(
        husband_portfolio,
        wife_portfolio,
        config,
    )

    assert result["post_tax"] == pytest.approx(120_000.0)
    assert result["pre_tax"] == pytest.approx(30_000.0)
    assert result["by_person"] == pytest.approx(
        {"husband": 100_000.0, "wife": 50_000.0}
    )
    assert husband_portfolio.total_value_post == pytest.approx(0.0)
    assert wife_portfolio.total_value_post == pytest.approx(0.0)
    assert husband_portfolio.total_value_pre == pytest.approx(10_000.0)
    assert wife_portfolio.total_value_pre == pytest.approx(70_000.0)


def test_single_person_withdrawal_uses_real_estate_after_hsa():
    husband_portfolio = make_portfolio_state(
        post_tax=10_000.0,
        pre_tax=20_000.0,
        roth=30_000.0,
        hsa=40_000.0,
        real_estate=50_000.0,
    )
    wife_portfolio = make_portfolio_state()
    config = make_config(withdrawal_amount=125_000.0)

    result = calculate_withdrawal(
        husband_portfolio,
        wife_portfolio,
        config,
    )

    assert result["post_tax"] == pytest.approx(10_000.0)
    assert result["pre_tax"] == pytest.approx(20_000.0)
    assert result["roth"] == pytest.approx(30_000.0)
    assert result["hsa"] == pytest.approx(40_000.0)
    assert result["real_estate"] == pytest.approx(25_000.0)
    assert result["uncovered"] == pytest.approx(0.0)
    assert husband_portfolio.total_value_hsa == pytest.approx(0.0)
    assert husband_portfolio.re_post == pytest.approx(25_000.0)


def test_couple_real_estate_withdrawal_uses_larger_owner_first():
    husband_portfolio = make_portfolio_state(real_estate=40_000.0)
    wife_portfolio = make_portfolio_state(real_estate=100_000.0)
    config = make_config(
        withdrawal_amount=70_000.0,
        second_person_enabled=True,
    )

    result = calculate_withdrawal(
        husband_portfolio,
        wife_portfolio,
        config,
    )

    assert result["real_estate"] == pytest.approx(70_000.0)
    assert result["by_person"] == pytest.approx(
        {"husband": 0.0, "wife": 70_000.0}
    )
    assert husband_portfolio.re_post == pytest.approx(40_000.0)
    assert wife_portfolio.re_post == pytest.approx(30_000.0)


def test_insufficient_real_estate_reports_only_actual_withdrawal():
    husband_portfolio = make_portfolio_state(
        post_tax=10_000.0,
        pre_tax=20_000.0,
        roth=30_000.0,
        hsa=40_000.0,
        real_estate=50_000.0,
    )
    wife_portfolio = make_portfolio_state()
    config = make_config(withdrawal_amount=200_000.0)

    result = calculate_withdrawal(
        husband_portfolio,
        wife_portfolio,
        config,
    )

    assert result["total"] == pytest.approx(150_000.0)
    assert result["real_estate"] == pytest.approx(50_000.0)
    assert result["uncovered"] == pytest.approx(50_000.0)
    assert husband_portfolio.total_value_including_real_estate == pytest.approx(0.0)


def test_inflation_adjusted_withdrawal_uses_historical_inflation_path():
    husband_portfolio = make_portfolio_state(post_tax=1_000.0)
    wife_portfolio = make_portfolio_state()
    config = make_config(
        withdrawal_amount=100.0,
        withdrawal_mode="Fixed Dollar Amount + Inflation",
        inflation_rate=0.99,
    )
    config.subplot_mode = "monte_carlo"
    config.monte_carlo_mode = "rollingHistoricalWindows"
    config._active_historical_sim_index = 1
    config._hist_window_start_indices = np.array([0, 2], dtype=int)
    config._hist_inflation = np.array([0.01, 0.02, 0.10, -0.20])

    result = calculate_withdrawal(
        husband_portfolio,
        wife_portfolio,
        config,
        year=2,
    )

    assert result["total"] == pytest.approx(88.0)
    assert husband_portfolio.total_value_post == pytest.approx(912.0)


def test_additional_cash_needed_does_not_change_cached_base_withdrawal():
    husband_portfolio = make_portfolio_state(post_tax=1_000.0)
    wife_portfolio = make_portfolio_state()
    config = make_config(withdrawal_amount=100.0)

    first_result = calculate_withdrawal(
        husband_portfolio,
        wife_portfolio,
        config,
        year=0,
        additional_cash_needed=50.0,
    )
    second_result = calculate_withdrawal(
        husband_portfolio,
        wife_portfolio,
        config,
        year=1,
    )

    assert first_result["total"] == pytest.approx(150.0)
    assert config._ret_withdraw_base_dollars == pytest.approx(100.0)
    assert second_result["total"] == pytest.approx(100.0)
    assert husband_portfolio.total_value_post == pytest.approx(750.0)


def test_couple_withdrawal_person_totals_reconcile_to_account_type_totals():
    husband_portfolio = make_portfolio_state(
        post_tax=30_000.0,
        pre_tax=20_000.0,
        roth=10_000.0,
        hsa=5_000.0,
        real_estate=15_000.0,
    )
    wife_portfolio = make_portfolio_state(
        post_tax=20_000.0,
        pre_tax=30_000.0,
        roth=15_000.0,
        hsa=10_000.0,
        real_estate=25_000.0,
    )
    config = make_config(
        withdrawal_amount=160_000.0,
        second_person_enabled=True,
    )

    result = calculate_withdrawal(
        husband_portfolio,
        wife_portfolio,
        config,
    )

    person_total = sum(result["by_person"].values())
    account_type_total = sum(
        result[key]
        for key in ("post_tax", "pre_tax", "roth", "hsa", "real_estate")
    )

    assert person_total == pytest.approx(160_000.0)
    assert account_type_total == pytest.approx(160_000.0)
    assert person_total == pytest.approx(account_type_total)
    assert person_total == pytest.approx(result["total"])
    assert result["uncovered"] == pytest.approx(0.0)
