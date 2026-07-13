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
    age,
    retire_age,
    income=0.0,
):
    return Person(
        age=age,
        retire_age=retire_age,
        income=income,
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
    equity_post=0.0,
):
    return Portfolio(
        equity_pre=0.0,
        equity_post=equity_post,
        bond_pre=0.0,
        bond_post=0.0,
        cash_pre=0.0,
        cash_post=0.0,
        real_estate=0.0,
        equity_roth=0.0,
        bond_roth=0.0,
        cash_roth=0.0,
        hsa_cash=0.0,
        hsa_equity=0.0,
        hsa_bond=0.0,
    )


def make_expenses(
    *,
    annual_amount,
):
    expenses = DynamicExpenses()

    expenses.add_expense(
        start_year=2027,
        cost=annual_amount,
        end_year=None,
    )

    return expenses


def make_config(
    *,
    years_to_simulate,
    second_person_enabled=False,
    always_use_expense_mode=False,
    retirement_withdraw_dollars=0.0,
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
        include_realestate=False,
        re_mean=0.0,
        re_std=0.0,
        output_csv="None",
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=retirement_withdraw_dollars,
        always_use_expense_mode=always_use_expense_mode,
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


def run_simulation(
    monkeypatch,
    *,
    husband,
    husband_portfolio,
    wife=None,
    wife_portfolio=None,
    annual_expense=0.0,
    years_to_simulate=3,
    second_person_enabled=False,
    always_use_expense_mode=False,
    retirement_withdraw_dollars=0.0,
):
    install_zero_market_path(monkeypatch)

    if wife is None:
        wife = make_person(
            age=0,
            retire_age=100,
        )

    if wife_portfolio is None:
        wife_portfolio = make_portfolio()

    return simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        make_expenses(
            annual_amount=annual_expense,
        ),
        make_config(
            years_to_simulate=years_to_simulate,
            second_person_enabled=second_person_enabled,
            always_use_expense_mode=always_use_expense_mode,
            retirement_withdraw_dollars=(
                retirement_withdraw_dollars
            ),
        ),
        num_sims=1,
    )


def test_single_person_uses_expenses_before_retirement(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            age=63,
            retire_age=65,
            income=50_000.0,
        ),
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        annual_expense=30_000.0,
        years_to_simulate=1,
        retirement_withdraw_dollars=10_000.0,
    )

    assert results["expense_amt"][0, 1] == pytest.approx(
        30_000.0
    )
    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(0.0)
    )

    assert (
        results["breakdown_by_class"]["work"][0, 1]
        == pytest.approx(50_000.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        50_000.0
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        120_000.0
    )


def test_single_person_switches_to_withdrawals_at_retirement(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            age=63,
            retire_age=65,
            income=50_000.0,
        ),
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        annual_expense=30_000.0,
        years_to_simulate=3,
        retirement_withdraw_dollars=10_000.0,
    )

    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            30_000.0,
            0.0,
            0.0,
        ]
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0]
        == pytest.approx(
            [
                0.0,
                0.0,
                10_000.0,
                10_000.0,
            ]
        )
    )

    assert (
        results["breakdown_by_class"]["work"][0]
        == pytest.approx(
            [
                0.0,
                50_000.0,
                0.0,
                0.0,
            ]
        )
    )

    assert results["gross_income"][0] == pytest.approx(
        [
            0.0,
            50_000.0,
            10_000.0,
            10_000.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            100_000.0,
            120_000.0,
            110_000.0,
            100_000.0,
        ]
    )


def test_retirement_transition_does_not_apply_expense_and_withdrawal_together(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            age=63,
            retire_age=65,
            income=0.0,
        ),
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        annual_expense=20_000.0,
        years_to_simulate=2,
        retirement_withdraw_dollars=15_000.0,
    )

    assert results["expense_amt"][0, 1] == pytest.approx(
        20_000.0
    )
    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(0.0)
    )

    assert results["expense_amt"][0, 2] == pytest.approx(
        0.0
    )
    assert (
        results["breakdown_by_class"]["withdrawal"][0, 2]
        == pytest.approx(15_000.0)
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            100_000.0,
            80_000.0,
            65_000.0,
        ]
    )


def test_couple_waits_until_both_people_are_retired(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            age=64,
            retire_age=65,
        ),
        wife=make_person(
            age=60,
            retire_age=62,
        ),
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        wife_portfolio=make_portfolio(),
        annual_expense=10_000.0,
        years_to_simulate=2,
        second_person_enabled=True,
        retirement_withdraw_dollars=20_000.0,
    )

    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            10_000.0,
            0.0,
        ]
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0]
        == pytest.approx(
            [
                0.0,
                0.0,
                20_000.0,
            ]
        )
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            100_000.0,
            90_000.0,
            70_000.0,
        ]
    )


def test_couple_switches_when_both_are_retired_in_same_year(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            age=64,
            retire_age=65,
        ),
        wife=make_person(
            age=61,
            retire_age=62,
        ),
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        wife_portfolio=make_portfolio(),
        annual_expense=10_000.0,
        years_to_simulate=1,
        second_person_enabled=True,
        retirement_withdraw_dollars=20_000.0,
    )

    assert results["expense_amt"][0, 1] == pytest.approx(
        0.0
    )
    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(20_000.0)
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        80_000.0
    )


def test_always_use_expense_mode_prevents_retirement_withdrawals(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            age=70,
            retire_age=65,
        ),
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        annual_expense=10_000.0,
        years_to_simulate=2,
        always_use_expense_mode=True,
        retirement_withdraw_dollars=20_000.0,
    )

    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            10_000.0,
            10_000.0,
        ]
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0]
        == pytest.approx(
            [
                0.0,
                0.0,
                0.0,
            ]
        )
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            100_000.0,
            90_000.0,
            80_000.0,
        ]
    )


def test_retirement_withdrawal_off_preserves_assets_after_transition(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            age=63,
            retire_age=65,
        ),
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        annual_expense=10_000.0,
        years_to_simulate=2,
        retirement_withdraw_dollars=0.0,
    )

    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            10_000.0,
            0.0,
        ]
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0]
        == pytest.approx(
            [
                0.0,
                0.0,
                0.0,
            ]
        )
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            100_000.0,
            90_000.0,
            90_000.0,
        ]
    )