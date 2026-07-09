# tests/test_run_sim_core_retirement_withdrawals.py

import pytest

from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


def test_simulation_switches_from_manual_expenses_to_withdrawals_at_retirement(scenario_builders):
    Person = scenario_builders.Person
    Portfolio = scenario_builders.Portfolio
    DynamicExpenses = scenario_builders.DynamicExpenses
    make_config = scenario_builders.make_config

    husband = Person(age=63, retire_age=65, income=30.0)
    wife = Person(age=40, retire_age=65, income=0.0)

    husband_portfolio = Portfolio(equity_post=100.0)
    wife_portfolio = Portfolio()

    expenses = DynamicExpenses()
    expenses.add_expense(2026, 10.0)
    expenses.add_expense(2027, 10.0)

    sim_config = make_config(
        years_to_simulate=2,
        always_use_expense_mode=False,
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_dollars=20.0,
        second_person_enabled=False,
        calculate_income_taxes=False,
        sim_type="portfolio_sim",
    )

    results = simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        num_sims=1,
    )

    # Year 1: still pre-retirement, so manual expenses are used
    assert results["expense_amt"][0, 1] == pytest.approx(10.0)
    assert results["breakdown_by_class"]["work"][0, 1] == pytest.approx(30.0)
    assert results["breakdown_by_class"]["withdrawal"][0, 1] == pytest.approx(0.0)

    # Year 2: retired, so withdrawal mode is used
    assert results["expense_amt"][0, 2] == pytest.approx(0.0)
    assert results["breakdown_by_class"]["work"][0, 2] == pytest.approx(0.0)
    assert results["breakdown_by_class"]["withdrawal"][0, 2] == pytest.approx(20.0)

    assert results["total_assets"][0, 0] == pytest.approx(100.0)
    assert results["total_assets"][0, 1] == pytest.approx(120.0)
    assert results["total_assets"][0, 2] == pytest.approx(100.0)


def test_fixed_dollar_withdrawal_uses_post_tax_then_pre_tax(scenario_builders):
    Person = scenario_builders.Person
    Portfolio = scenario_builders.Portfolio
    DynamicExpenses = scenario_builders.DynamicExpenses
    make_config = scenario_builders.make_config

    husband = Person(age=65, retire_age=65, income=0.0)
    wife = Person(age=40, retire_age=65, income=0.0)

    husband_portfolio = Portfolio(equity_pre=60.0, equity_post=40.0)
    wife_portfolio = Portfolio()

    expenses = DynamicExpenses()

    sim_config = make_config(
        years_to_simulate=1,
        always_use_expense_mode=False,
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_dollars=50.0,
        second_person_enabled=False,
        calculate_income_taxes=False,
        sim_type="portfolio_sim",
    )

    results = simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        num_sims=1,
    )

    assert results["breakdown_by_class"]["withdrawal"][0, 1] == pytest.approx(50.0)
    assert results["post_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["pre_tax_assets"][0, 1] == pytest.approx(50.0)
    assert results["total_assets"][0, 1] == pytest.approx(50.0)


def test_rmd_off_mode_still_withdraws_required_minimum_distribution(scenario_builders):
    Person = scenario_builders.Person
    Portfolio = scenario_builders.Portfolio
    DynamicExpenses = scenario_builders.DynamicExpenses
    make_config = scenario_builders.make_config

    husband = Person(age=72, retire_age=65, income=0.0)
    wife = Person(age=40, retire_age=65, income=0.0)

    husband_portfolio = Portfolio(equity_pre=100.0)
    wife_portfolio = Portfolio()

    expenses = DynamicExpenses()

    sim_config = make_config(
        years_to_simulate=1,
        always_use_expense_mode=False,
        include_rmd=True,
        retirement_withdraw_mode="Off",
        second_person_enabled=False,
        calculate_income_taxes=False,
        sim_type="portfolio_sim",
    )

    results = simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        num_sims=1,
    )

    expected_rmd = 100.0 / 26.5
    expected_remaining_pre_tax = 100.0 - expected_rmd

    assert results["breakdown_by_class"]["rmd"][0, 1] == pytest.approx(expected_rmd)
    assert results["pre_tax_assets"][0, 1] == pytest.approx(expected_remaining_pre_tax)
    assert results["total_assets"][0, 1] == pytest.approx(expected_remaining_pre_tax)