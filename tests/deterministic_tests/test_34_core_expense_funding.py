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
    income=0.0,
):
    return Person(
        age=40,
        retire_age=100,
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
    inflation_rate=0.0,
    scenario_expense_multiplier=1.0,
    second_person_enabled=False,
    include_realestate=False,
):
    return Simulation(
        start_year=2026,
        years_to_simulate=1,
        inflation_rate=inflation_rate,
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
        include_realestate=include_realestate,
        re_mean=0.0,
        re_std=0.0,
        output_csv="None",
        retirement_withdraw_mode="Off",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=0.0,
        always_use_expense_mode=True,
        sequence_risk_enabled=False,
        scenario_expense_multiplier=scenario_expense_multiplier,
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