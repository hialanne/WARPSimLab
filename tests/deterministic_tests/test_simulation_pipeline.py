# tests/test_simulation_pipeline.py

import numpy as np
import pytest

from src.warpsimlab.sim.simulation import run_pipeline


def test_run_pipeline_single_person_manual_expenses_exact_basics(scenario_builders):
    Person = scenario_builders.Person
    Portfolio = scenario_builders.Portfolio
    DynamicExpenses = scenario_builders.DynamicExpenses
    make_config = scenario_builders.make_config

    husband = Person(age=40, retire_age=65, income=50.0)
    wife = Person(age=40, retire_age=65, income=0.0)

    husband_portfolio = Portfolio(equity_pre=100.0)
    wife_portfolio = Portfolio()

    expenses = DynamicExpenses()
    expenses.add_expense(2026, 20.0, 2026)
    expenses.add_expense(2027, 20.0, 2027)

    sim_config = make_config(
        years_to_simulate=2,
        sim_type="portfolio_sim",
        always_use_expense_mode=True,
        second_person_enabled=False,
        calculate_income_taxes=False,
    )

    result = run_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        force_num_sims=1,
    )

    assert np.array_equal(result["years_list"], np.array([0, 1, 2]))
    assert np.allclose(result["portfolio_plot_data"].percentiles["median"], [100.0, 130.0, 160.0])

    assert np.allclose(result["net_income"], [0.0, 50.0, 50.0])
    assert np.allclose(result["net_profit"], [0.0, 30.0, 30.0])
    assert np.allclose(result["expense_amt"], [0.0, 20.0, 20.0])

    breakdown = result["breakdown_by_class"]
    assert np.allclose(breakdown["work"], [0.0, 50.0, 50.0])
    assert np.allclose(breakdown["withdrawal"], [0.0, 0.0, 0.0])

    summary = result["summary_results"]
    assert np.allclose(summary["total_assets"], [100.0, 130.0, 160.0])
    assert np.allclose(summary["gross_income"], [0.0, 50.0, 50.0])
    assert np.allclose(summary["net_cash_flow"], [0.0, 30.0, 30.0])

def test_run_pipeline_real_mode_deflates_outputs(scenario_builders):
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
    )

    result = run_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        force_num_sims=1,
    )

    expected_year1_nominal = 133.0
    expected_year1_real = expected_year1_nominal / 1.10

    assert result["portfolio_plot_data"].percentiles["median"][0] == pytest.approx(100.0)
    assert result["portfolio_plot_data"].percentiles["median"][1] == pytest.approx(expected_year1_real)
    assert result["summary_results"]["total_assets"][1] == pytest.approx(expected_year1_real)
    assert result["net_profit"][1] == pytest.approx(33.0 / 1.10)


def test_run_pipeline_attaches_overlay_series(scenario_builders):
    Person = scenario_builders.Person
    Portfolio = scenario_builders.Portfolio
    DynamicExpenses = scenario_builders.DynamicExpenses
    make_config = scenario_builders.make_config

    husband = Person(age=40, retire_age=65, income=60000.0)
    wife = Person(age=40, retire_age=65, income=0.0)

    husband_portfolio = Portfolio(equity_pre=100.0)
    wife_portfolio = Portfolio()

    expenses = DynamicExpenses()

    sim_config = make_config(
        years_to_simulate=1,
        sim_type="portfolio_sim",
        always_use_expense_mode=True,
        second_person_enabled=False,
        calculate_income_taxes=True,
        tax_filing_status="Single",
        use_fund_expenses=True,
        fund_expense=0.10,
        overlay_tax_impacts=True,
        overlay_fund_expense_impacts=True,
    )

    result = run_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        force_num_sims=1,
    )

    plot_data = result["portfolio_plot_data"]
    baseline = plot_data.percentiles["median"]
    no_taxes = plot_data.median_without_taxes
    no_fees = plot_data.median_without_fund_expenses
    no_both = plot_data.median_without_taxes_or_fund_expenses

    assert no_taxes is not None
    assert no_fees is not None
    assert no_both is not None

    assert len(baseline) == 2
    assert len(no_taxes) == 2
    assert len(no_fees) == 2
    assert len(no_both) == 2

    assert no_taxes[1] > baseline[1]
    assert no_fees[1] > baseline[1]
    assert no_both[1] >= no_taxes[1]
    assert no_both[1] >= no_fees[1]
