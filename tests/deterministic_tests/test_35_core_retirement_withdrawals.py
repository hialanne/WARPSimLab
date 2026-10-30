import numpy as np
import pytest
from tests.architectural_helpers import make_person as build_person, make_portfolio, make_simulation

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


def make_person(
    *,
    age=70,
    retire_age=65,
):
    return build_person(age=age, retire_age=retire_age)


def make_config(
    *,
    years_to_simulate=1,
    inflation_rate=0.0,
    inflation_mode="nominal",
    second_person_enabled=False,
    include_realestate=False,
    retirement_withdraw_mode="Fixed Dollar Amount",
    retirement_withdraw_pct=4.0,
    retirement_withdraw_dollars=0.0,
):
    return make_simulation(
        years_to_simulate=years_to_simulate,
        inflation_rate=inflation_rate,
        inflation_mode=inflation_mode,
        results_mode="baseline",
        second_person_enabled=second_person_enabled,
        sim_initial_allocation_mode="dont-rebalance",
        include_realestate=include_realestate,
        retirement_withdraw_mode=retirement_withdraw_mode,
        retirement_withdraw_pct=retirement_withdraw_pct,
        retirement_withdraw_dollars=retirement_withdraw_dollars,
        always_use_expense_mode=False,
    )


def install_zero_market_path(monkeypatch):
    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        zeros = np.zeros(years_to_simulate + 1, dtype=float)

        return {
            "eq": zeros.copy(),
            "bd": zeros.copy(),
            "cs": zeros.copy(),
            "re": zeros.copy(),
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )


def run_simulation(
    monkeypatch,
    *,
    husband_portfolio,
    husband=None,
    wife_portfolio=None,
    wife=None,
    years_to_simulate=1,
    inflation_rate=0.0,
    inflation_mode="nominal",
    second_person_enabled=False,
    include_realestate=False,
    retirement_withdraw_mode="Fixed Dollar Amount",
    retirement_withdraw_pct=4.0,
    retirement_withdraw_dollars=0.0,
):
    install_zero_market_path(monkeypatch)

    if husband is None:
        husband = make_person()

    if wife is None:
        wife = make_person()

    if wife_portfolio is None:
        wife_portfolio = make_portfolio()

    config = make_config(
        years_to_simulate=years_to_simulate,
        inflation_rate=inflation_rate,
        inflation_mode=inflation_mode,
        second_person_enabled=second_person_enabled,
        include_realestate=include_realestate,
        retirement_withdraw_mode=retirement_withdraw_mode,
        retirement_withdraw_pct=retirement_withdraw_pct,
        retirement_withdraw_dollars=retirement_withdraw_dollars,
    )

    return simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        DynamicExpenses(),
        config,
        num_sims=1,
    )


def test_fixed_dollar_withdrawal_reduces_post_tax_assets(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        retirement_withdraw_dollars=10_000.0,
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(10_000.0)
    )

    assert results["post_tax_assets"][0, 0] == pytest.approx(
        100_000.0
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        90_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        90_000.0
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        10_000.0
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        results["breakdown_by_class"]["withdrawal"][0, 1]
    )

    assert results["roth_withdrawals"][0, 1] == pytest.approx(
        0.0
    )
    assert results["hsa_withdrawals"][0, 1] == pytest.approx(
        0.0
    )


def test_fixed_dollar_withdrawal_repeats_each_year(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        years_to_simulate=3,
        retirement_withdraw_dollars=10_000.0,
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0]
        == pytest.approx(
            [
                0.0,
                10_000.0,
                10_000.0,
                10_000.0,
            ]
        )
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            100_000.0,
            90_000.0,
            80_000.0,
            70_000.0,
        ]
    )

    assert results["gross_income"][0] == pytest.approx(
        [
            0.0,
            10_000.0,
            10_000.0,
            10_000.0,
        ]
    )


def test_withdrawal_uses_post_tax_before_pre_tax(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=50_000.0,
            equity_pre=100_000.0,
        ),
        retirement_withdraw_dollars=80_000.0,
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(80_000.0)
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        70_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        70_000.0
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        80_000.0
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        results["breakdown_by_class"]["withdrawal"][0, 1]
    )


def test_withdrawal_uses_roth_after_pre_tax(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=20_000.0,
            equity_pre=30_000.0,
            equity_roth=100_000.0,
        ),
        retirement_withdraw_dollars=80_000.0,
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["roth_assets"][0, 1] == pytest.approx(
        70_000.0
    )

    assert results["roth_withdrawals"][0, 1] == pytest.approx(
        30_000.0
    )
    assert results["hsa_withdrawals"][0, 1] == pytest.approx(
        0.0
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(80_000.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        80_000.0
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        results["breakdown_by_class"]["withdrawal"][0, 1]
    )


def test_withdrawal_uses_hsa_after_roth(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=10_000.0,
            equity_pre=20_000.0,
            equity_roth=30_000.0,
            hsa_equity=100_000.0,
        ),
        retirement_withdraw_dollars=90_000.0,
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["roth_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["hsa_assets"][0, 1] == pytest.approx(
        70_000.0
    )

    assert results["roth_withdrawals"][0, 1] == pytest.approx(
        30_000.0
    )
    assert results["hsa_withdrawals"][0, 1] == pytest.approx(
        30_000.0
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(90_000.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        90_000.0
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        results["breakdown_by_class"]["withdrawal"][0, 1]
    )


def test_withdrawal_uses_real_estate_after_financial_assets(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=10_000.0,
            equity_pre=20_000.0,
            equity_roth=30_000.0,
            hsa_equity=40_000.0,
            real_estate=100_000.0,
        ),
        include_realestate=True,
        retirement_withdraw_dollars=125_000.0,
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["roth_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["hsa_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["real_estate"][0, 1] == pytest.approx(
        75_000.0
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(125_000.0)
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        75_000.0
    )

    assert results["roth_withdrawals"][0, 1] == pytest.approx(
        30_000.0
    )
    assert results["hsa_withdrawals"][0, 1] == pytest.approx(
        40_000.0
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        125_000.0
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        results["breakdown_by_class"]["withdrawal"][0, 1]
    )


def test_withdrawal_is_limited_to_available_assets(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=10_000.0,
            equity_pre=20_000.0,
            equity_roth=30_000.0,
            hsa_equity=40_000.0,
            real_estate=50_000.0,
        ),
        include_realestate=True,
        retirement_withdraw_dollars=200_000.0,
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(150_000.0)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        150_000.0
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        results["breakdown_by_class"]["withdrawal"][0, 1]
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["roth_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["hsa_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["real_estate"][0, 1] == pytest.approx(
        0.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        0.0
    )


def test_percentage_withdrawal_uses_initial_financial_assets(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
            equity_pre=100_000.0,
        ),
        retirement_withdraw_mode="Percentage",
        retirement_withdraw_pct=4.0,
    )

    expected_withdrawal = 200_000.0 * 0.04

    assert expected_withdrawal == pytest.approx(8_000.0)

    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(expected_withdrawal)
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        expected_withdrawal
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        92_000.0
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        100_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        192_000.0
    )


def test_fixed_dollar_plus_inflation_increases_withdrawal(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        years_to_simulate=2,
        inflation_rate=0.10,
        retirement_withdraw_mode="Fixed Dollar Amount + Inflation",
        retirement_withdraw_dollars=10_000.0,
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0]
        == pytest.approx(
            [
                0.0,
                11_000.0,
                12_100.0,
            ]
        )
    )

    assert results["gross_income"][0] == pytest.approx(
        [
            0.0,
            11_000.0,
            12_100.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            100_000.0,
            89_000.0,
            76_900.0,
        ]
    )


def test_real_mode_deflates_withdrawals_and_assets(
    monkeypatch,
):
    inflation_rate = 0.10

    raw_results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        years_to_simulate=2,
        inflation_rate=inflation_rate,
        inflation_mode="nominal",
        retirement_withdraw_mode="Fixed Dollar Amount + Inflation",
        retirement_withdraw_dollars=10_000.0,
    )

    real_results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        years_to_simulate=2,
        inflation_rate=inflation_rate,
        inflation_mode="real",
        retirement_withdraw_mode="Fixed Dollar Amount + Inflation",
        retirement_withdraw_dollars=10_000.0,
    )

    discount_factors = np.array(
        [
            1.0,
            1.10,
            1.21,
        ]
    )

    assert real_results["post_tax_assets"][0] == pytest.approx(
        raw_results["post_tax_assets"][0] / discount_factors
    )
    assert real_results["total_assets"][0] == pytest.approx(
        raw_results["total_assets"][0] / discount_factors
    )
    assert real_results["gross_income"][0] == pytest.approx(
        raw_results["gross_income"][0] / discount_factors
    )
    assert (
        real_results["breakdown_by_class"]["withdrawal"][0]
        == pytest.approx(
            raw_results["breakdown_by_class"]["withdrawal"][0]
            / discount_factors
        )
    )
    assert real_results["roth_withdrawals"][0] == pytest.approx(
        raw_results["roth_withdrawals"][0] / discount_factors
    )
    assert real_results["hsa_withdrawals"][0] == pytest.approx(
        raw_results["hsa_withdrawals"][0] / discount_factors
    )


def test_couple_withdrawal_uses_household_post_tax_before_pre_tax(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        wife_portfolio=make_portfolio(
            equity_pre=100_000.0,
        ),
        husband=make_person(),
        wife=make_person(),
        second_person_enabled=True,
        retirement_withdraw_dollars=150_000.0,
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(150_000.0)
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        50_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        50_000.0
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        150_000.0
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        results["breakdown_by_class"]["withdrawal"][0, 1]
    )