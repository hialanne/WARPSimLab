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
    equity_pre=0.0,
    equity_post=0.0,
    equity_roth=0.0,
    hsa_equity=0.0,
    real_estate=0.0,
):
    return Portfolio(
        equity_pre=equity_pre,
        equity_post=equity_post,
        bond_pre=0.0,
        bond_post=0.0,
        cash_pre=0.0,
        cash_post=0.0,
        real_estate=real_estate,
        equity_roth=equity_roth,
        bond_roth=0.0,
        cash_roth=0.0,
        hsa_cash=0.0,
        hsa_equity=hsa_equity,
        hsa_bond=0.0,
    )


def make_config(
    *,
    years_to_simulate=1,
    inflation_rate=0.0,
    plot_mode="raw",
    second_person_enabled=False,
    include_realestate=False,
    retirement_withdraw_mode="Fixed Dollar Amount",
    retirement_withdraw_pct=4.0,
    retirement_withdraw_dollars=0.0,
):
    return Simulation(
        start_year=2026,
        years_to_simulate=years_to_simulate,
        inflation_rate=inflation_rate,
        num_sims=1,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode=plot_mode,
        subplot_mode="baseline",
        include_rmd=False,
        calculate_income_taxes=False,
        calculate_payroll_taxes=False,
        tax_filing_status="Single",
        calculate_state_taxes=False,
        state_of_residence="TX",
        second_person_enabled=second_person_enabled,
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
        include_realestate=include_realestate,
        re_mean=0.0,
        re_std=0.0,
        output_csv="None",
        retirement_withdraw_mode=retirement_withdraw_mode,
        retirement_withdraw_pct=retirement_withdraw_pct,
        retirement_withdraw_dollars=retirement_withdraw_dollars,
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
    plot_mode="raw",
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
        plot_mode=plot_mode,
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
        plot_mode="raw",
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
        plot_mode="real",
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