"""HSA wage limits and qualified-spending conservation, independent of tax limits."""

from types import SimpleNamespace

import pytest

from src.warpsimlab.dataClasses.portfolioState import PortfolioState
from src.warpsimlab.sim.engines import hsaEngine


def hsa_portfolio(**buckets):
    return PortfolioState(0, 0, 0, 0, 0, 0, 0, **buckets)


@pytest.mark.parametrize("wages,k401,employee,employer", [
    (10_000, 2_000, 5_000, 1_000),
    (10_000, 8_000, 2_000, 1_000),
    (10_000, 10_000, 0, 1_000),
    (10_000, 12_000, 0, 1_000),
    (0, 0, 0, 0), (-100, 0, 0, 0),
])
def test_employee_contribution_is_capped_after_401k_but_employer_is_not_deducted(
    wages, k401, employee, employer,
):
    person = SimpleNamespace(retire_age=65, annual_hsa_contribution=5_000,
                             annual_hsa_employer_contribution=1_000)
    result = hsaEngine.calculate_hsa_contributions(
        person, 64, 1, wages, k401, True,
        SimpleNamespace(_income_inflation_factors=[1.0, 1.0]),
    )
    assert result == dict(employee=employee, employer=employer, total=employee + employer)


@pytest.mark.parametrize("age,alive", [(65, True), (66, True), (64, False)])
def test_retired_or_deceased_person_makes_no_hsa_contributions(age, alive):
    person = SimpleNamespace(retire_age=65, annual_hsa_contribution=5_000,
                             annual_hsa_employer_contribution=1_000)
    assert hsaEngine.calculate_hsa_contributions(
        person, age, 1, 10_000, 0, alive, SimpleNamespace()
    ) == dict(employee=0.0, employer=0.0, total=0.0)


@pytest.mark.parametrize("requested,paid,uncovered", [
    (-10, 0, 0), (0, 0, 0), (40, 40, 0), (100, 100, 0), (140, 100, 40),
])
def test_qualified_spending_preserves_spouse_and_asset_proportions(requested, paid, uncovered):
    husband = hsa_portfolio(hsa_eq=30, hsa_bd=18, hsa_cs=12)
    wife = hsa_portfolio(hsa_eq=20, hsa_bd=12, hsa_cs=8)
    result = hsaEngine.pay_qualified_hsa_expenses(husband, wife, requested, True)
    assert result == pytest.approx(dict(paid=paid, uncovered=uncovered))
    fraction = 1.0 - paid / 100
    assert [husband.hsa_eq, husband.hsa_bd, husband.hsa_cs] == pytest.approx(
        [30 * fraction, 18 * fraction, 12 * fraction]
    )
    assert [wife.hsa_eq, wife.hsa_bd, wife.hsa_cs] == pytest.approx(
        [20 * fraction, 12 * fraction, 8 * fraction]
    )


def test_disabled_spouse_hsa_cannot_pay_qualified_expenses():
    husband = hsa_portfolio(hsa_cs=20)
    wife = hsa_portfolio(hsa_cs=100)
    result = hsaEngine.pay_qualified_hsa_expenses(husband, wife, 50, False)
    assert result == dict(paid=20, uncovered=30)
    assert husband.total_value_hsa == 0
    assert wife.total_value_hsa == 100


def test_employee_and_employer_requests_follow_income_inflation_before_wage_cap():
    person = SimpleNamespace(retire_age=65, annual_hsa_contribution=3_000,
                             annual_hsa_employer_contribution=1_000)
    result = hsaEngine.calculate_hsa_contributions(
        person, 40, 2, 10_000, 6_000, True,
        SimpleNamespace(_income_inflation_factors=[1.0, 1.2, 1.5]),
    )
    # Requested employee 4,500 is capped at 4,000; employer 1,500 is additional.
    assert result == dict(employee=4_000, employer=1_500, total=5_500)
