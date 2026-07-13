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
    age=40,
    retire_age=65,
    income=0.0,
    annual_401k_contribution=0.0,
    annual_employer_match=0.0,
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
        annual_401k_contribution=annual_401k_contribution,
        annual_employer_match=annual_employer_match,
        pension_inflation_adjustment_pct=0.0,
    )


def make_portfolio(
    *,
    equity_pre=0.0,
    bond_pre=0.0,
    cash_pre=0.0,
):
    return Portfolio(
        equity_pre=equity_pre,
        equity_post=0.0,
        bond_pre=bond_pre,
        bond_post=0.0,
        cash_pre=cash_pre,
        cash_post=0.0,
        real_estate=0.0,
        equity_roth=0.0,
        bond_roth=0.0,
        cash_roth=0.0,
        hsa_cash=0.0,
        hsa_equity=0.0,
        hsa_bond=0.0,
    )


def make_config(
    *,
    years_to_simulate=1,
    inflation_rate=0.0,
    second_person_enabled=False,
    calculate_payroll_taxes=False,
):
    return Simulation(
        start_year=2026,
        years_to_simulate=years_to_simulate,
        inflation_rate=inflation_rate,
        num_sims=1,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode="raw",
        subplot_mode="baseline",
        include_rmd=False,
        calculate_income_taxes=False,
        calculate_payroll_taxes=calculate_payroll_taxes,
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
        retirement_withdraw_mode="Off",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=0.0,
        always_use_expense_mode=True,
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
    husband,
    husband_portfolio=None,
    wife=None,
    wife_portfolio=None,
    years_to_simulate=1,
    inflation_rate=0.0,
    second_person_enabled=False,
    calculate_payroll_taxes=False,
):
    install_zero_market_path(monkeypatch)

    if husband_portfolio is None:
        husband_portfolio = make_portfolio()

    if wife is None:
        wife = make_person()

    if wife_portfolio is None:
        wife_portfolio = make_portfolio()

    return simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        DynamicExpenses(),
        make_config(
            years_to_simulate=years_to_simulate,
            inflation_rate=inflation_rate,
            second_person_enabled=second_person_enabled,
            calculate_payroll_taxes=calculate_payroll_taxes,
        ),
        num_sims=1,
    )


def test_employee_contribution_reduces_work_income(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            income=100_000.0,
            annual_401k_contribution=10_000.0,
        ),
    )

    assert (
        results["breakdown_by_class"]["work"][0, 1]
        == pytest.approx(90_000.0)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        100_000.0
    )
    assert results["net_income"][0, 1] == pytest.approx(
        90_000.0
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        90_000.0
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        10_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        100_000.0
    )

    assert results["ira_401k"][0, 1] == pytest.approx(
        10_000.0
    )

    assert (
        results["post_tax_assets"][0, 1]
        == pytest.approx(results["net_income"][0, 1])
    )

def test_employee_and_employer_contributions_enter_pre_tax_assets(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            income=100_000.0,
            annual_401k_contribution=10_000.0,
            annual_employer_match=5_000.0,
        ),
    )

    expected_employee = 10_000.0
    expected_employer = 5_000.0
    expected_pre_tax = expected_employee + expected_employer
    expected_post_tax = 100_000.0 - expected_employee

    assert results["ira_401k"][0, 1] == pytest.approx(
        expected_pre_tax
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        expected_pre_tax
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        expected_post_tax
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        100_000.0
    )
    assert results["net_income"][0, 1] == pytest.approx(
        90_000.0
    )

    assert results["total_assets"][0, 1] == pytest.approx(
        105_000.0
    )


def test_employer_match_is_not_deducted_from_income(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            income=100_000.0,
            annual_401k_contribution=10_000.0,
            annual_employer_match=5_000.0,
        ),
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        100_000.0
    )

    assert results["gross_income"][0, 1] != pytest.approx(
        95_000.0
    )

    assert results["ira_401k"][0, 1] == pytest.approx(
        15_000.0
    )


def test_employee_contribution_is_capped_by_work_income(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            income=5_000.0,
            annual_401k_contribution=10_000.0,
            annual_employer_match=2_000.0,
        ),
    )

    expected_employee = 5_000.0
    expected_employer = 2_000.0

    assert (
        results["breakdown_by_class"]["work"][0, 1]
        == pytest.approx(0.0)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        5_000.0
    )
    assert results["net_income"][0, 1] == pytest.approx(
        0.0
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )

    assert results["ira_401k"][0, 1] == pytest.approx(
        expected_employee + expected_employer
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        expected_employee + expected_employer
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        7_000.0
    )


def test_employer_match_is_zero_when_employee_has_no_wages(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            income=0.0,
            annual_401k_contribution=10_000.0,
            annual_employer_match=5_000.0,
        ),
    )

    assert results["gross_income"][0, 1] == pytest.approx(0.0)
    assert results["net_income"][0, 1] == pytest.approx(0.0)
    assert results["ira_401k"][0, 1] == pytest.approx(0.0)
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        0.0
    )


def test_contributions_stop_at_retirement_age(monkeypatch):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            age=63,
            retire_age=65,
            income=100_000.0,
            annual_401k_contribution=10_000.0,
            annual_employer_match=5_000.0,
        ),
        years_to_simulate=2,
    )

    assert results["ira_401k"][0] == pytest.approx(
        [
            0.0,
            15_000.0,
            0.0,
        ]
    )

    assert (
        results["breakdown_by_class"]["work"][0]
        == pytest.approx(
            [
                0.0,
                90_000.0,
                0.0,
            ]
        )
    )

    assert results["gross_income"][0] == pytest.approx(
        [
            0.0,
            100_000.0,
            0.0,
        ]
    )

    assert results["pre_tax_assets"][0] == pytest.approx(
        [
            0.0,
            15_000.0,
            15_000.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            0.0,
            90_000.0,
            90_000.0,
        ]
    )


def test_income_and_contributions_inflate_together(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            age=40,
            retire_age=65,
            income=100_000.0,
            annual_401k_contribution=10_000.0,
            annual_employer_match=5_000.0,
        ),
        inflation_rate=0.10,
    )

    expected_income = 100_000.0 * 1.10
    expected_employee = 10_000.0 * 1.10
    expected_employer = 5_000.0 * 1.10

    expected_reported_work = (
        expected_income - expected_employee
    )
    expected_pre_tax = (
        expected_employee + expected_employer
    )

    assert expected_income == pytest.approx(110_000.0)
    assert expected_employee == pytest.approx(11_000.0)
    assert expected_employer == pytest.approx(5_500.0)

    assert (
        results["breakdown_by_class"]["work"][0, 1]
        == pytest.approx(expected_reported_work)
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        expected_income
    )
    assert results["net_income"][0, 1] == pytest.approx(
        expected_reported_work
    )
    assert results["ira_401k"][0, 1] == pytest.approx(
        expected_pre_tax
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        16_500.0
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        99_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        115_500.0
    )


def test_contribution_preserves_existing_pre_tax_allocation(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            income=100_000.0,
            annual_401k_contribution=10_000.0,
            annual_employer_match=5_000.0,
        ),
        husband_portfolio=make_portfolio(
            equity_pre=60_000.0,
            bond_pre=30_000.0,
            cash_pre=10_000.0,
        ),
    )

    expected_total_pre_tax = 115_000.0
    expected_bonds = 30_000.0 + 15_000.0 * 0.30
    expected_cash = 10_000.0 + 15_000.0 * 0.10
    expected_equity = 60_000.0 + 15_000.0 * 0.60

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        expected_total_pre_tax
    )
    assert results["bonds"][0, 1] == pytest.approx(
        expected_bonds
    )
    assert results["cash"][0, 1] == pytest.approx(
        expected_cash
    )

    actual_equity = (
        results["pre_tax_assets"][0, 1]
        - results["bonds"][0, 1]
        - results["cash"][0, 1]
    )

    assert actual_equity == pytest.approx(expected_equity)


def test_couple_contributions_and_income_reconcile(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            income=60_000.0,
            annual_401k_contribution=6_000.0,
            annual_employer_match=3_000.0,
        ),
        wife=make_person(
            income=40_000.0,
            annual_401k_contribution=4_000.0,
            annual_employer_match=2_000.0,
        ),
        second_person_enabled=True,
    )

    expected_husband_available_income = 54_000.0
    expected_wife_available_income = 36_000.0
    expected_household_gross_income = 100_000.0
    expected_employee_contributions = 10_000.0
    expected_total_contributions = 15_000.0

    assert results["net_income_husband"][0, 1] == (
        pytest.approx(expected_husband_available_income)
    )
    assert results["net_income_wife"][0, 1] == (
        pytest.approx(expected_wife_available_income)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        expected_household_gross_income
    )
    assert results["net_income"][0, 1] == pytest.approx(
        90_000.0
    )

    assert (
        results["net_income_husband"][0, 1]
        + results["net_income_wife"][0, 1]
        == pytest.approx(results["net_income"][0, 1])
    )

    assert results["ira_401k"][0, 1] == pytest.approx(
        expected_total_contributions
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        expected_total_contributions
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        90_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        105_000.0
    )