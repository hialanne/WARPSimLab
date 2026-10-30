import numpy as np
import pytest
from tests.architectural_helpers import make_person as build_person, make_portfolio, make_simulation

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


def make_person(
    *,
    age=40,
    retire_age=65,
    income=0.0,
    annual_401k_contribution=0.0,
    annual_employer_match=0.0,
):
    return build_person(
        age=age,
        retire_age=retire_age,
        income=income,
        annual_401k_contribution=annual_401k_contribution,
        annual_employer_match=annual_employer_match,
    )


def make_config(
    *,
    years_to_simulate=1,
    inflation_rate=0.0,
    second_person_enabled=False,
    calculate_payroll_taxes=False,
):
    return make_simulation(
        years_to_simulate=years_to_simulate,
        inflation_rate=inflation_rate,
        results_mode="baseline",
        calculate_payroll_taxes=calculate_payroll_taxes,
        second_person_enabled=second_person_enabled,
        sim_initial_allocation_mode="dont-rebalance",
        retirement_withdraw_dollars=0.0,
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

    assert results["pre_tax_assets"][0, 1] == pytest.approx(expected_total_pre_tax)
    assert results["pre_tax_equity"][0, 1] == pytest.approx(expected_equity)
    assert results["pre_tax_bonds"][0, 1] == pytest.approx(expected_bonds)
    assert results["pre_tax_cash"][0, 1] == pytest.approx(expected_cash)


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