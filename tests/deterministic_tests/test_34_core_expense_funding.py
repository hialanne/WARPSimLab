import numpy as np
import pytest
from tests.architectural_helpers import make_person, make_portfolio, make_simulation

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


def make_config(
    *,
    inflation_rate=0.0,
    scenario_expense_multiplier=1.0,
    second_person_enabled=False,
    include_realestate=False,
):
    return make_simulation(
        inflation_rate=inflation_rate,
        results_mode="baseline",
        second_person_enabled=second_person_enabled,
        sim_initial_allocation_mode="dont-rebalance",
        include_realestate=include_realestate,
        retirement_withdraw_dollars=0.0,
        scenario_expense_multiplier=scenario_expense_multiplier,
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


def make_expenses(amount):
    expenses = DynamicExpenses()
    expenses.add_expense(
        start_year=2026,
        cost=amount,
        end_year=None,
    )
    return expenses


def run_one_year(
    monkeypatch,
    *,
    husband_portfolio,
    expense_amount,
    husband_income=0.0,
    wife_portfolio=None,
    wife_income=0.0,
    inflation_rate=0.0,
    scenario_expense_multiplier=1.0,
    second_person_enabled=False,
    include_realestate=False,
):
    install_zero_market_path(monkeypatch)

    if wife_portfolio is None:
        wife_portfolio = make_portfolio()

    return simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        make_person(income=husband_income),
        make_person(income=wife_income),
        make_expenses(expense_amount),
        make_config(
            inflation_rate=inflation_rate,
            scenario_expense_multiplier=scenario_expense_multiplier,
            second_person_enabled=second_person_enabled,
            include_realestate=include_realestate,
        ),
        num_sims=1,
    )


def test_income_covers_expense_and_surplus_is_deposited(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(),
        husband_income=50_000.0,
        expense_amount=30_000.0,
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        50_000.0
    )
    assert results["net_income"][0, 1] == pytest.approx(
        50_000.0
    )
    assert results["expense_amt"][0, 1] == pytest.approx(
        30_000.0
    )
    assert results["net_profit"][0, 1] == pytest.approx(
        20_000.0
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        20_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        20_000.0
    )
    assert results["emergency_pre_tax_used"][0, 1] == (
        pytest.approx(0.0)
    )


def test_expense_equal_to_income_leaves_assets_unchanged(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=25_000.0,
        ),
        husband_income=50_000.0,
        expense_amount=50_000.0,
    )

    assert results["net_profit"][0, 1] == pytest.approx(0.0)
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        25_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        25_000.0
    )


def test_expense_deficit_uses_post_tax_first(monkeypatch):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
            equity_pre=100_000.0,
            equity_roth=100_000.0,
            hsa_equity=100_000.0,
        ),
        expense_amount=60_000.0,
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

    assert results["emergency_pre_tax_used"][0, 1] == (
        pytest.approx(0.0)
    )


def test_expense_deficit_uses_pre_tax_after_post_tax(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=30_000.0,
            equity_pre=100_000.0,
            equity_roth=100_000.0,
            hsa_equity=100_000.0,
        ),
        expense_amount=80_000.0,
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        50_000.0
    )
    assert results["roth_assets"][0, 1] == pytest.approx(
        100_000.0
    )
    assert results["hsa_assets"][0, 1] == pytest.approx(
        100_000.0
    )

    assert results["emergency_pre_tax_used"][0, 1] == (
        pytest.approx(50_000.0)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        50_000.0
    )


def test_expense_deficit_uses_roth_after_pre_tax(monkeypatch):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=20_000.0,
            equity_pre=30_000.0,
            equity_roth=100_000.0,
            hsa_equity=100_000.0,
        ),
        expense_amount=80_000.0,
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["pre_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["roth_assets"][0, 1] == pytest.approx(
        70_000.0
    )
    assert results["hsa_assets"][0, 1] == pytest.approx(
        100_000.0
    )

    assert results["emergency_pre_tax_used"][0, 1] == (
        pytest.approx(30_000.0)
    )


def test_expense_deficit_uses_hsa_after_roth(monkeypatch):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=10_000.0,
            equity_pre=20_000.0,
            equity_roth=30_000.0,
            hsa_equity=100_000.0,
        ),
        expense_amount=90_000.0,
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["pre_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["roth_assets"][0, 1] == pytest.approx(0.0)
    assert results["hsa_assets"][0, 1] == pytest.approx(
        70_000.0
    )

    assert results["emergency_pre_tax_used"][0, 1] == (
        pytest.approx(20_000.0)
    )


def test_expense_deficit_uses_real_estate_last(monkeypatch):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=10_000.0,
            equity_pre=20_000.0,
            equity_roth=30_000.0,
            hsa_equity=40_000.0,
            real_estate=100_000.0,
        ),
        expense_amount=125_000.0,
        include_realestate=True,
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["pre_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["roth_assets"][0, 1] == pytest.approx(0.0)
    assert results["hsa_assets"][0, 1] == pytest.approx(0.0)

    assert results["real_estate"][0, 1] == pytest.approx(
        75_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        75_000.0
    )

    assert results["emergency_pre_tax_used"][0, 1] == (
        pytest.approx(20_000.0)
    )
    assert results["uncovered_expense"][0, 1] == pytest.approx(
        0.0
    )


def test_expense_beyond_all_assets_depletes_every_bucket(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=10_000.0,
            equity_pre=20_000.0,
            equity_roth=30_000.0,
            hsa_equity=40_000.0,
            real_estate=50_000.0,
        ),
        expense_amount=200_000.0,
        include_realestate=True,
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["pre_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["roth_assets"][0, 1] == pytest.approx(0.0)
    assert results["hsa_assets"][0, 1] == pytest.approx(0.0)
    assert results["real_estate"][0, 1] == pytest.approx(0.0)
    assert results["total_assets"][0, 1] == pytest.approx(0.0)

    assert results["expense_amt"][0, 1] == pytest.approx(
        200_000.0
    )
    assert results["net_profit"][0, 1] == pytest.approx(
        -200_000.0
    )
    assert results["uncovered_expense"][0, 1] == pytest.approx(
        50_000.0
    )


def test_expense_amount_is_inflated(monkeypatch):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        expense_amount=20_000.0,
        inflation_rate=0.10,
    )

    assert results["expense_amt"][0, 1] == pytest.approx(
        22_000.0
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        78_000.0
    )


def test_scenario_expense_multiplier_is_applied_before_inflation(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        expense_amount=20_000.0,
        inflation_rate=0.10,
        scenario_expense_multiplier=1.50,
    )

    expected_expense = 20_000.0 * 1.50 * 1.10

    assert expected_expense == pytest.approx(33_000.0)
    assert results["expense_amt"][0, 1] == pytest.approx(
        expected_expense
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        67_000.0
    )


def test_couple_post_tax_deficit_is_shared_proportionally(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=75_000.0,
        ),
        wife_portfolio=make_portfolio(
            equity_post=25_000.0,
        ),
        expense_amount=40_000.0,
        second_person_enabled=True,
    )

    assert results["post_tax_assets"][0, 0] == pytest.approx(
        100_000.0
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        60_000.0
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["emergency_pre_tax_used"][0, 1] == (
        pytest.approx(0.0)
    )


def test_couple_real_estate_uses_larger_balance_first(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            real_estate=80_000.0,
        ),
        wife_portfolio=make_portfolio(
            real_estate=20_000.0,
        ),
        expense_amount=50_000.0,
        second_person_enabled=True,
        include_realestate=True,
    )

    assert results["real_estate"][0, 0] == pytest.approx(
        100_000.0
    )
    assert results["real_estate"][0, 1] == pytest.approx(
        50_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        50_000.0
    )