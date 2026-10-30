import numpy as np
import pytest
from tests.architectural_helpers import make_person as build_person, make_portfolio as build_portfolio, make_simulation

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


def make_person(
    *,
    age=70,
    retire_age=65,
):
    return build_person(age=age, retire_age=retire_age)


def make_portfolio(
    *,
    pre_tax=0.0,
    post_tax=0.0,
    roth=0.0,
    hsa=0.0,
):
    return build_portfolio(equity_pre=pre_tax, equity_post=post_tax, equity_roth=roth, hsa_equity=hsa)


def make_config(
    *,
    withdrawal_amount,
    years_to_simulate=1,
    calculate_income_taxes=False,
):
    return make_simulation(
        years_to_simulate=years_to_simulate,
        results_mode="baseline",
        calculate_income_taxes=calculate_income_taxes,
        sim_initial_allocation_mode="dont-rebalance",
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_dollars=withdrawal_amount,
        always_use_expense_mode=False,
    )


def install_zero_market_path(monkeypatch):
    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        zeros = np.zeros(
            years_to_simulate + 1,
            dtype=float,
        )

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


def run_core(
    monkeypatch,
    *,
    pre_tax=0.0,
    post_tax=0.0,
    roth=0.0,
    hsa=0.0,
    withdrawal_amount,
    years_to_simulate=1,
    calculate_income_taxes=False,
):
    install_zero_market_path(monkeypatch)

    return simulate_yearly_portfolios(
        make_portfolio(
            pre_tax=pre_tax,
            post_tax=post_tax,
            roth=roth,
            hsa=hsa,
        ),
        make_portfolio(),
        make_person(),
        make_person(),
        DynamicExpenses(),
        make_config(
            withdrawal_amount=withdrawal_amount,
            years_to_simulate=years_to_simulate,
            calculate_income_taxes=calculate_income_taxes,
        ),
        num_sims=1,
    )


def test_withdrawal_uses_post_tax_before_other_accounts(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        post_tax=100_000.0,
        pre_tax=100_000.0,
        roth=100_000.0,
        hsa=100_000.0,
        withdrawal_amount=60_000.0,
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(60_000.0)
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        40_000.0
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        100_000.0
    )
    assert results["roth_assets"][0, 1] == pytest.approx(
        100_000.0
    )
    assert results["hsa_assets"][0, 1] == pytest.approx(
        100_000.0
    )

    assert results["roth_withdrawals"][0, 1] == pytest.approx(
        0.0
    )
    assert results["hsa_withdrawals"][0, 1] == pytest.approx(
        0.0
    )


def test_withdrawal_uses_pre_tax_after_post_tax(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        post_tax=20_000.0,
        pre_tax=100_000.0,
        roth=100_000.0,
        hsa=100_000.0,
        withdrawal_amount=60_000.0,
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        60_000.0
    )
    assert results["roth_assets"][0, 1] == pytest.approx(
        100_000.0
    )
    assert results["hsa_assets"][0, 1] == pytest.approx(
        100_000.0
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(60_000.0)
    )


def test_withdrawal_uses_roth_after_post_and_pre_tax(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        post_tax=20_000.0,
        pre_tax=30_000.0,
        roth=100_000.0,
        hsa=100_000.0,
        withdrawal_amount=60_000.0,
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["roth_assets"][0, 1] == pytest.approx(
        90_000.0
    )
    assert results["hsa_assets"][0, 1] == pytest.approx(
        100_000.0
    )

    assert results["roth_withdrawals"][0, 1] == pytest.approx(
        10_000.0
    )
    assert results["hsa_withdrawals"][0, 1] == pytest.approx(
        0.0
    )


def test_withdrawal_uses_hsa_after_roth(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        post_tax=20_000.0,
        pre_tax=30_000.0,
        roth=40_000.0,
        hsa=100_000.0,
        withdrawal_amount=120_000.0,
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
        40_000.0
    )
    assert results["hsa_withdrawals"][0, 1] == pytest.approx(
        30_000.0
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(120_000.0)
    )


def test_withdrawal_is_limited_to_available_assets(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        post_tax=10_000.0,
        pre_tax=20_000.0,
        roth=30_000.0,
        hsa=40_000.0,
        withdrawal_amount=150_000.0,
    )

    assert results["total_assets"][0, 1] == pytest.approx(
        0.0
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

    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(100_000.0)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        100_000.0
    )

    assert results["roth_withdrawals"][0, 1] == pytest.approx(
        30_000.0
    )
    assert results["hsa_withdrawals"][0, 1] == pytest.approx(
        40_000.0
    )


def test_gross_income_reports_total_withdrawal_regardless_of_source(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        post_tax=20_000.0,
        pre_tax=30_000.0,
        roth=40_000.0,
        hsa=50_000.0,
        withdrawal_amount=100_000.0,
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(100_000.0)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        100_000.0
    )

    assert results["roth_withdrawals"][0, 1] == pytest.approx(
        40_000.0
    )
    assert results["hsa_withdrawals"][0, 1] == pytest.approx(
        10_000.0
    )


def test_pre_tax_and_general_hsa_withdrawals_create_income_tax(monkeypatch):
    post_tax_results = run_core(
        monkeypatch, post_tax=100_000.0, withdrawal_amount=60_000.0, calculate_income_taxes=True
    )
    pre_tax_results = run_core(
        monkeypatch, pre_tax=100_000.0, withdrawal_amount=60_000.0, calculate_income_taxes=True
    )
    roth_results = run_core(
        monkeypatch, roth=100_000.0, withdrawal_amount=60_000.0, calculate_income_taxes=True
    )
    hsa_results = run_core(
        monkeypatch, hsa=100_000.0, withdrawal_amount=60_000.0, calculate_income_taxes=True
    )

    for results in [post_tax_results, pre_tax_results, roth_results, hsa_results]:
        assert results["gross_income"][0, 1] == pytest.approx(60_000.0)

    assert post_tax_results["taxes"][0, 1] == pytest.approx(0.0)
    assert pre_tax_results["taxes"][0, 1] > 0.0
    assert roth_results["taxes"][0, 1] == pytest.approx(0.0)
    assert hsa_results["taxes"][0, 1] > 0.0
    assert hsa_results["hsa_taxable_withdrawals"][0, 1] == pytest.approx(60_000.0)
    assert hsa_results["hsa_qualified_withdrawals"][0, 1] == pytest.approx(0.0)

def test_mixed_withdrawal_tax_is_based_on_pre_tax_portion(
    monkeypatch,
):
    mixed_results = run_core(
        monkeypatch,
        post_tax=20_000.0,
        pre_tax=40_000.0,
        roth=100_000.0,
        withdrawal_amount=100_000.0,
        calculate_income_taxes=True,
    )

    pre_tax_only_results = run_core(
        monkeypatch,
        pre_tax=40_000.0,
        withdrawal_amount=40_000.0,
        calculate_income_taxes=True,
    )

    assert mixed_results["gross_income"][0, 1] == pytest.approx(
        100_000.0
    )

    assert (
        mixed_results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(100_000.0)
    )

    assert mixed_results["roth_withdrawals"][0, 1] == (
        pytest.approx(40_000.0)
    )

    assert mixed_results["taxes"][0, 1] == pytest.approx(
        pre_tax_only_results["taxes"][0, 1]
    )


def test_funding_order_continues_correctly_across_years(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        post_tax=20_000.0,
        pre_tax=30_000.0,
        roth=40_000.0,
        hsa=50_000.0,
        withdrawal_amount=60_000.0,
        years_to_simulate=3,
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0]
        == pytest.approx(
            [
                0.0,
                60_000.0,
                60_000.0,
                20_000.0,
            ]
        )
    )

    assert results["roth_withdrawals"][0] == pytest.approx(
        [
            0.0,
            10_000.0,
            30_000.0,
            0.0,
        ]
    )

    assert results["hsa_withdrawals"][0] == pytest.approx(
        [
            0.0,
            0.0,
            30_000.0,
            20_000.0,
        ]
    )

    assert results["total_assets"][0] == pytest.approx(
        [
            140_000.0,
            80_000.0,
            20_000.0,
            0.0,
        ]
    )