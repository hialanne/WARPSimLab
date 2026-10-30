import numpy as np
import pytest
from tests.architectural_helpers import make_person, make_portfolio, make_simulation

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


def make_config(
    *,
    years_to_simulate=5,
    inflation_rate=0.0,
    scenario_expense_multiplier=1.0,
):
    return make_simulation(
        years_to_simulate=years_to_simulate,
        inflation_rate=inflation_rate,
        results_mode="baseline",
        sim_initial_allocation_mode="dont-rebalance",
        retirement_withdraw_dollars=0.0,
        scenario_expense_multiplier=scenario_expense_multiplier,
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


def make_expenses(*expense_rows):
    expenses = DynamicExpenses()

    for row in expense_rows:
        expenses.add_expense(
            start_year=row["start_year"],
            end_year=row.get("end_year"),
            cost=row["cost"],
            comment=row.get("comment", ""),
        )

    return expenses


def run_core(
    monkeypatch,
    *,
    expenses,
    years_to_simulate=5,
    inflation_rate=0.0,
    scenario_expense_multiplier=1.0,
    starting_assets=500_000.0,
    annual_income=0.0,
):
    install_zero_market_path(monkeypatch)

    return simulate_yearly_portfolios(
        make_portfolio(
            equity_post=starting_assets,
        ),
        make_portfolio(),
        make_person(
            income=annual_income,
        ),
        make_person(),
        expenses,
        make_config(
            years_to_simulate=years_to_simulate,
            inflation_rate=inflation_rate,
            scenario_expense_multiplier=(
                scenario_expense_multiplier
            ),
        ),
        num_sims=1,
    )


def test_expense_starts_in_correct_calendar_year(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        expenses=make_expenses(
            {
                "start_year": 2028,
                "cost": 10_000.0,
            },
        ),
        years_to_simulate=4,
    )

    # Simulation year 1 is calendar year 2027.
    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            0.0,
            10_000.0,
            10_000.0,
            10_000.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            500_000.0,
            500_000.0,
            490_000.0,
            480_000.0,
            470_000.0,
        ]
    )


def test_expense_end_year_is_inclusive(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        expenses=make_expenses(
            {
                "start_year": 2027,
                "end_year": 2029,
                "cost": 12_000.0,
            },
        ),
        years_to_simulate=5,
    )

    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            12_000.0,
            12_000.0,
            12_000.0,
            0.0,
            0.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            500_000.0,
            488_000.0,
            476_000.0,
            464_000.0,
            464_000.0,
            464_000.0,
        ]
    )


def test_one_year_expense_occurs_once(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        expenses=make_expenses(
            {
                "start_year": 2028,
                "end_year": 2028,
                "cost": 25_000.0,
            },
        ),
        years_to_simulate=4,
    )

    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            0.0,
            25_000.0,
            0.0,
            0.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            500_000.0,
            500_000.0,
            475_000.0,
            475_000.0,
            475_000.0,
        ]
    )


def test_overlapping_expenses_are_added_together(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        expenses=make_expenses(
            {
                "start_year": 2027,
                "cost": 10_000.0,
            },
            {
                "start_year": 2028,
                "end_year": 2029,
                "cost": 20_000.0,
            },
            {
                "start_year": 2029,
                "end_year": 2029,
                "cost": 5_000.0,
            },
        ),
        years_to_simulate=4,
    )

    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            10_000.0,
            30_000.0,
            35_000.0,
            10_000.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            500_000.0,
            490_000.0,
            460_000.0,
            425_000.0,
            415_000.0,
        ]
    )


def test_expenses_are_inflated_from_simulation_start(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        expenses=make_expenses(
            {
                "start_year": 2027,
                "cost": 10_000.0,
            },
        ),
        years_to_simulate=3,
        inflation_rate=0.10,
    )

    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            11_000.0,
            12_100.0,
            13_310.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            500_000.0,
            489_000.0,
            476_900.0,
            463_590.0,
        ]
    )


def test_scenario_multiplier_is_applied_before_inflation(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        expenses=make_expenses(
            {
                "start_year": 2027,
                "cost": 10_000.0,
            },
        ),
        years_to_simulate=2,
        inflation_rate=0.10,
        scenario_expense_multiplier=1.50,
    )

    # Year 1:
    # 10,000 x 1.50 x 1.10 = 16,500
    #
    # Year 2:
    # 10,000 x 1.50 x 1.10^2 = 18,150
    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            16_500.0,
            18_150.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            500_000.0,
            483_500.0,
            465_350.0,
        ]
    )


def test_income_funds_expenses_before_portfolio_assets(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        expenses=make_expenses(
            {
                "start_year": 2027,
                "cost": 30_000.0,
            },
        ),
        years_to_simulate=2,
        starting_assets=100_000.0,
        annual_income=20_000.0,
    )

    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            30_000.0,
            30_000.0,
        ]
    )

    assert results["gross_income"][0] == pytest.approx(
        [
            0.0,
            20_000.0,
            20_000.0,
        ]
    )

    assert results["uncovered_expense"][0] == pytest.approx(
        [
            0.0,
            0.0,
            0.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            100_000.0,
            90_000.0,
            80_000.0,
        ]
    )


def test_unfunded_expense_is_reported_as_uncovered(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        expenses=make_expenses(
            {
                "start_year": 2027,
                "cost": 50_000.0,
            },
        ),
        years_to_simulate=2,
        starting_assets=30_000.0,
    )

    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            50_000.0,
            50_000.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            30_000.0,
            0.0,
            0.0,
        ]
    )

    assert results["uncovered_expense"][0] == pytest.approx(
        [
            0.0,
            20_000.0,
            50_000.0,
        ]
    )


def test_zero_scenario_multiplier_eliminates_expenses(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        expenses=make_expenses(
            {
                "start_year": 2027,
                "cost": 50_000.0,
            },
        ),
        years_to_simulate=2,
        scenario_expense_multiplier=0.0,
    )

    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            0.0,
            0.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            500_000.0,
            500_000.0,
            500_000.0,
        ]
    )

    assert results["uncovered_expense"][0] == pytest.approx(
        [
            0.0,
            0.0,
            0.0,
        ]
    )