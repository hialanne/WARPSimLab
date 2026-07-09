# tests/test_run_sim_core_manual_expenses.py

import numpy as np
import pytest

from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios

def test_manual_expense_deficit_uses_post_tax_then_pre_tax_exactly(scenario_builders):
    Person = scenario_builders.Person
    Portfolio = scenario_builders.Portfolio
    DynamicExpenses = scenario_builders.DynamicExpenses
    make_config = scenario_builders.make_config

    husband = Person(age=40, retire_age=65, income=20.0)
    wife = Person(age=40, retire_age=65, income=0.0)

    husband_portfolio = Portfolio(equity_pre=30.0, equity_post=50.0)
    wife_portfolio = Portfolio()

    expenses = DynamicExpenses()
    expenses.add_expense(2026, 80.0)

    sim_config = make_config(
        years_to_simulate=1,
        always_use_expense_mode=True,
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

    assert results["gross_income"][0, 1] == pytest.approx(30.0)
    assert results["net_income"][0, 1] == pytest.approx(20.0)
    assert results["net_profit"][0, 1] == pytest.approx(-60.0)

    assert results["post_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["pre_tax_assets"][0, 1] == pytest.approx(20.0)
    assert results["total_assets"][0, 1] == pytest.approx(20.0)

    assert results["emergency_pre_tax_used"][0, 1] == pytest.approx(10.0)
    assert results["final_tax_delta"][0, 1] == pytest.approx(0.0)
    assert results["final_tax_delta_deducted"][0, 1] == pytest.approx(0.0)
    assert results["final_tax_delta_uncovered"][0, 1] == pytest.approx(0.0)


def test_manual_expense_couple_records_per_person_net_income_without_taxes(scenario_builders):
    Person = scenario_builders.Person
    Portfolio = scenario_builders.Portfolio
    DynamicExpenses = scenario_builders.DynamicExpenses
    make_config = scenario_builders.make_config

    husband = Person(age=40, retire_age=65, income=60.0)
    wife = Person(age=40, retire_age=65, income=40.0)

    husband_portfolio = Portfolio()
    wife_portfolio = Portfolio()

    expenses = DynamicExpenses()
    expenses.add_expense(2026, 0.0)

    sim_config = make_config(
        years_to_simulate=1,
        always_use_expense_mode=True,
        second_person_enabled=True,
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

    assert results["net_income"][0, 1] == pytest.approx(100.0)
    assert results["net_income_husband"][0, 1] == pytest.approx(60.0)
    assert results["net_income_wife"][0, 1] == pytest.approx(40.0)
    assert results["post_tax_assets"][0, 1] == pytest.approx(100.0)

def test_manual_expense_results_can_be_real_dollar_deflated(scenario_builders):
    Person = scenario_builders.Person
    Portfolio = scenario_builders.Portfolio
    DynamicExpenses = scenario_builders.DynamicExpenses
    make_config = scenario_builders.make_config

    husband = Person(age=40, retire_age=65, income=50.0)
    wife = Person(age=40, retire_age=65, income=0.0)

    husband_portfolio = Portfolio(equity_pre=100.0)
    wife_portfolio = Portfolio()

    expenses = DynamicExpenses()
    expenses.add_expense(2026, 20.0)

    sim_config = make_config(
        years_to_simulate=1,
        plot_mode="real",
        inflation_rate=0.10,
        always_use_expense_mode=True,
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

    assert results["total_assets"][0, 1] == pytest.approx(133.0 / 1.10)
    assert results["net_income"][0, 1] == pytest.approx(55.0 / 1.10)
    assert results["net_profit"][0, 1] == pytest.approx(33.0 / 1.10)