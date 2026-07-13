import pytest
from types import SimpleNamespace

from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


class FlatExpenses:
    def __init__(self, annual_amount: float):
        self.annual_amount = annual_amount

    def get_total_expense_for_year(self, year: int) -> float:
        return self.annual_amount


def make_person(*, age, retire_age, income=0.0):
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
        annual_401k_contribution=0.0,
        annual_employer_match=0.0,
        pension_inflation_adjustment_pct=0.0,
    )


def make_portfolio(*, equity_post=0.0):
    return SimpleNamespace(
        equity_pre=0.0,
        equity_post=equity_post,
        bond_pre=0.0,
        bond_post=0.0,
        cash_pre=0.0,
        cash_post=0.0,
        real_estate=0.0,
    )


def make_sim(years):
    return SimpleNamespace(
        start_year=2026,
        years_to_simulate=years,
        inflation_rate=0.0,
        num_sims=1,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode="raw",
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
        sim_initial_allocation_mode="dont-rebalance",
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


def run_sim(years):
    cfg = make_sim(years)
    husband = make_person(age=40, retire_age=100, income=100_000.0)
    wife = make_person(age=0, retire_age=0)
    husband_portfolio = make_portfolio(equity_post=50_000.0)
    wife_portfolio = make_portfolio()
    expenses = FlatExpenses(40_000.0)

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


def row_class(results, key):
    return results["breakdown_by_class"][key][0]


def test_two_year_vs_multi_year_consistency():
    one_year = run_sim(1)
    two_year = run_sim(2)
    three_year = run_sim(3)

    top_level_keys = [
        "year",
        "gross_income",
        "net_income",
        "net_profit",
        "expense_amt",
        "taxes",
        "total_assets",
        "pre_tax_assets",
        "post_tax_assets",
        "cash",
        "bonds",
        "real_estate",
        "net_income_husband",
        "net_income_wife",
        "bond_interest",
        "cash_interest",
        "qualified_dividends",
        "ira_401k",
        "fund_expenses",
        "emergency_pre_tax_used",
    ]

    for key in top_level_keys:
        assert row(two_year, key)[:2] == pytest.approx(row(one_year, key))
        assert row(three_year, key)[:2] == pytest.approx(row(one_year, key))
        assert row(three_year, key)[:3] == pytest.approx(row(two_year, key))

    class_keys = [
        "work",
        "pension",
        "annuity",
        "ss",
        "rmd",
        "withdrawal",
        "bond_interest",
        "cash_interest",
        "qualified_dividends",
    ]

    for key in class_keys:
        assert row_class(two_year, key)[:2] == pytest.approx(row_class(one_year, key))
        assert row_class(three_year, key)[:2] == pytest.approx(row_class(one_year, key))
        assert row_class(three_year, key)[:3] == pytest.approx(row_class(two_year, key))