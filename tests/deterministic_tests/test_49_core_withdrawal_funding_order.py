import numpy as np
import pytest

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.dataClasses.person import Person
from src.warpsimlab.dataClasses.portfolio import Portfolio
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios
from src.warpsimlab.sim.simulationObject import Simulation


def make_person(
    *,
    age=70,
    retire_age=65,
):
    return Person(
        age=age,
        retire_age=retire_age,
        income=0.0,
        ss=0.0,
        ss_age=99,
        pension=0.0,
        pension_age=99,
        annuity=0.0,
        annuity_age=99,
        annual_401k_contribution=0.0,
        annual_employer_match=0.0,
        pension_inflation_adjustment_pct=0.0,
    )


def make_portfolio(
    *,
    pre_tax=0.0,
    post_tax=0.0,
    roth=0.0,
    hsa=0.0,
):
    return Portfolio(
        equity_pre=pre_tax,
        equity_post=post_tax,
        bond_pre=0.0,
        bond_post=0.0,
        cash_pre=0.0,
        cash_post=0.0,
        real_estate=0.0,
        equity_roth=roth,
        bond_roth=0.0,
        cash_roth=0.0,
        hsa_cash=0.0,
        hsa_equity=hsa,
        hsa_bond=0.0,
    )


def make_config(
    *,
    withdrawal_amount,
    years_to_simulate=1,
    calculate_income_taxes=False,
):
    return Simulation(
        start_year=2026,
        years_to_simulate=years_to_simulate,
        inflation_rate=0.0,
        num_sims=1,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode="raw",
        subplot_mode="baseline",
        include_rmd=False,
        calculate_income_taxes=calculate_income_taxes,
        calculate_payroll_taxes=False,
        tax_filing_status="Single",
        calculate_state_taxes=False,
        state_of_residence="TX",
        second_person_enabled=False,
        eq_mean=0.0,
        bd_mean=0.0,
        cs_mean=0.0,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        sim_type="portfolio_sim",
        sim_initial_allocation_mode="dont-rebalance",
        rebalance_every_year=False,
        include_realestate=False,
        re_mean=0.0,
        re_std=0.0,
        output_csv="None",
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=withdrawal_amount,
        always_use_expense_mode=False,
        sequence_risk_enabled=False,
        scenario_expense_multiplier=1.0,
        overlay_tax_impacts=False,
        overlay_fund_expense_impacts=False,
        overlay_household_expenses=False,
        overlay_profit_loss=False,
        overlay_retirement_age=False,
        show_simulated_shortfall_rate=False,
        use_snapshot_annotations=False,
        user_annotation_strings=[],
        root=None,
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


def test_only_pre_tax_portion_creates_income_tax(
    monkeypatch,
):
    post_tax_results = run_core(
        monkeypatch,
        post_tax=100_000.0,
        withdrawal_amount=60_000.0,
        calculate_income_taxes=True,
    )

    pre_tax_results = run_core(
        monkeypatch,
        pre_tax=100_000.0,
        withdrawal_amount=60_000.0,
        calculate_income_taxes=True,
    )

    roth_results = run_core(
        monkeypatch,
        roth=100_000.0,
        withdrawal_amount=60_000.0,
        calculate_income_taxes=True,
    )

    hsa_results = run_core(
        monkeypatch,
        hsa=100_000.0,
        withdrawal_amount=60_000.0,
        calculate_income_taxes=True,
    )

    for results in [
        post_tax_results,
        pre_tax_results,
        roth_results,
        hsa_results,
    ]:
        assert results["gross_income"][0, 1] == pytest.approx(
            60_000.0
        )

    assert post_tax_results["taxes"][0, 1] == pytest.approx(
        0.0
    )

    assert pre_tax_results["taxes"][0, 1] > 0.0

    assert roth_results["taxes"][0, 1] == pytest.approx(
        0.0
    )

    assert hsa_results["taxes"][0, 1] == pytest.approx(
        0.0
    )


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