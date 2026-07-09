import numpy as np
import pytest
from types import SimpleNamespace

from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


class FlatExpenses:
    def __init__(self, annual_amount: float):
        self.annual_amount = annual_amount

    def get_total_expense_for_year(self, year: int) -> float:
        return self.annual_amount


def make_person(
    *,
    age,
    retire_age,
    income=0.0,
    annual_401k_contribution=0.0,
    annual_employer_match=0.0,
):
    return SimpleNamespace(
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


def make_portfolio(*, equity_pre=0.0, bond_pre=0.0, cash_pre=0.0):
    return SimpleNamespace(
        equity_pre=equity_pre,
        equity_post=0.0,
        bond_pre=bond_pre,
        bond_post=0.0,
        cash_pre=cash_pre,
        cash_post=0.0,
        real_estate=0.0,
    )


def make_sim(*, years, inflation_rate=0.0, plot_mode="raw"):
    return SimpleNamespace(
        start_year=2026,
        years_to_simulate=years,
        inflation_rate=inflation_rate,
        num_sims=1,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode=plot_mode,
        subplot_mode="fixed",
        monte_carlo_mode="pathBasedAnnualSampling",
        monte_carlo_plot_style="fill",
        use_correlated_returns=True,
        include_rmd=False,
        calculate_income_taxes=False,
        calculate_payroll_taxes=False,
        tax_filing_status="Single",
        calculate_state_taxes=False,
        state_of_residence="NM",
        second_person_enabled=False,
        eq_mean=0.0,
        bd_mean=0.0,
        cs_mean=0.0,
        re_mean=0.0,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_std=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        sim_type="portfolio_sim",
        sim_rebalance="dont-rebalance",
        rebalance_every_year=False,
        include_realestate=False,
        retirement_withdraw_mode="Off",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=0.0,
        always_use_expense_mode=True,
        scenario_expense_multiplier=1.0,
        household_eq_target=None,
        household_bd_target=None,
        household_cs_target=None,
        custom_stock=0.0,
        custom_bonds=0.0,
        custom_cash=1.0,
    )


def run_sim(cfg, husband, expenses, husband_portfolio):
    wife = make_person(age=0, retire_age=0)
    wife_portfolio = make_portfolio()
    return simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        cfg,
        num_sims=1,
    )


def row(results, key):
    return results[key][0]


def assert_discounted(raw_results, real_results, key, inflation_rate):
    discount = np.array([(1.0 + inflation_rate) ** t for t in range(raw_results[key].shape[1])])
    assert row(real_results, key) == pytest.approx(row(raw_results, key) / discount)


def test_401k_contribution_scenario_while_working_nominal():
    husband = make_person(
        age=40,
        retire_age=100,
        income=100_000.0,
        annual_401k_contribution=10_000.0,
        annual_employer_match=5_000.0,
    )
    husband_portfolio = make_portfolio(equity_pre=60_000.0, bond_pre=40_000.0, cash_pre=0.0)
    expenses = FlatExpenses(90_000.0)
    cfg = make_sim(years=1, inflation_rate=0.0, plot_mode="raw")

    results = run_sim(cfg, husband, expenses, husband_portfolio)

    assert row(results, "year").tolist() == [2026.0, 2027.0]

    # Employee contribution reduces work income.
    assert row(results, "gross_income") == pytest.approx([0.0, 105_000.0])
    assert row(results, "net_income") == pytest.approx([0.0, 90_000.0])
    assert row(results, "ira_401k") == pytest.approx([0.0, 15_000.0])
    assert row(results, "expense_amt") == pytest.approx([0.0, 90_000.0])
    assert row(results, "net_profit") == pytest.approx([0.0, 0.0])

    # Work-class income reflects only the employee reduction, not employer match.
    assert results["breakdown_by_class"]["work"][0] == pytest.approx([0.0, 90_000.0])

    # Pre-tax assets rise by employee + employer contribution.
    assert row(results, "pre_tax_assets") == pytest.approx([100_000.0, 115_000.0])
    assert row(results, "post_tax_assets") == pytest.approx([0.0, 0.0])
    assert row(results, "total_assets") == pytest.approx([100_000.0, 115_000.0])


def test_401k_contribution_scenario_while_working_real_mode_deflates_correctly():
    husband = make_person(
        age=40,
        retire_age=100,
        income=100_000.0,
        annual_401k_contribution=10_000.0,
        annual_employer_match=5_000.0,
    )
    husband_portfolio = make_portfolio(equity_pre=60_000.0, bond_pre=40_000.0, cash_pre=0.0)
    expenses = FlatExpenses(90_000.0)
    infl = 0.03

    raw_cfg = make_sim(years=1, inflation_rate=infl, plot_mode="raw")
    real_cfg = make_sim(years=1, inflation_rate=infl, plot_mode="real")

    raw_results = run_sim(raw_cfg, husband, expenses, husband_portfolio)
    real_results = run_sim(real_cfg, husband, expenses, husband_portfolio)

    for key in ["gross_income", "net_income", "ira_401k", "expense_amt", "pre_tax_assets", "total_assets"]:
        assert_discounted(raw_results, real_results, key, infl)