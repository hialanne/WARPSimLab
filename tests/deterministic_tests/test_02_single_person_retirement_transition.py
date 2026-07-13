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
    ss=0.0,
    ss_age=99,
    pension=0.0,
    pension_age=99,
    annuity=0.0,
    annuity_age=99,
):
    return SimpleNamespace(
        age=age,
        retire_age=retire_age,
        income=income,
        ss=ss,
        ss_age=ss_age,
        pension=pension,
        pension_age=pension_age,
        annuity=annuity,
        annuity_age=annuity_age,
        annual_401k_contribution=0.0,
        annual_employer_match=0.0,
        pension_inflation_adjustment_pct=0.0,
    )


def make_portfolio(*, equity_pre=0.0, equity_post=0.0, bond_pre=0.0, bond_post=0.0, cash_pre=0.0, cash_post=0.0):
    return SimpleNamespace(
        equity_pre=equity_pre,
        equity_post=equity_post,
        bond_pre=bond_pre,
        bond_post=bond_post,
        cash_pre=cash_pre,
        cash_post=cash_post,
        real_estate=0.0,
    )


def make_sim(*, years, inflation_rate=0.0, plot_mode="raw", **overrides):
    cfg = SimpleNamespace(
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
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=30_000.0,
        always_use_expense_mode=False,
        scenario_expense_multiplier=1.0,
        household_eq_target=None,
        household_bd_target=None,
        household_cs_target=None,
    )
    cfg.__dict__.update(overrides)
    return cfg


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


def row_class(results, key):
    return results["breakdown_by_class"][key][0]


def assert_discounted(raw_results, real_results, key, inflation_rate):
    discount = np.array([(1.0 + inflation_rate) ** t for t in range(raw_results[key].shape[1])])
    assert row(real_results, key) == pytest.approx(row(raw_results, key) / discount)


def assert_discounted_class(raw_results, real_results, key, inflation_rate):
    discount = np.array([(1.0 + inflation_rate) ** t for t in range(raw_results["breakdown_by_class"][key].shape[1])])
    assert row_class(real_results, key) == pytest.approx(row_class(raw_results, key) / discount)


def test_single_person_retirement_transition_switches_in_exact_year():
    husband = make_person(age=63, retire_age=65, income=100_000.0)
    expenses = FlatExpenses(40_000.0)
    husband_portfolio = make_portfolio(equity_post=100_000.0)
    cfg = make_sim(years=3, inflation_rate=0.0, plot_mode="raw")

    results = run_sim(cfg, husband, expenses, husband_portfolio)

    # Year 1: still working, still using manual expenses.
    assert row(results, "year").tolist() == [2026.0, 2027.0, 2028.0, 2029.0]
    assert row(results, "expense_amt")[1] == pytest.approx(40_000.0)
    assert row_class(results, "work")[1] == pytest.approx(100_000.0)
    assert row_class(results, "withdrawal")[1] == pytest.approx(0.0)

    # Year 2: first retirement year, switches out of manual-expense mode.
    assert row(results, "expense_amt")[2] == pytest.approx(0.0)
    assert row_class(results, "work")[2] == pytest.approx(0.0)
    assert row_class(results, "withdrawal")[2] == pytest.approx(30_000.0)

    # Year 3 stays in retirement withdrawal mode.
    assert row(results, "expense_amt")[3] == pytest.approx(0.0)
    assert row_class(results, "work")[3] == pytest.approx(0.0)
    assert row_class(results, "withdrawal")[3] == pytest.approx(30_000.0)

    assert row(results, "total_assets") == pytest.approx([100_000.0, 160_000.0, 130_000.0, 100_000.0])


def test_single_person_retirement_transition_real_mode_deflates_correctly():
    husband = make_person(age=63, retire_age=65, income=100_000.0)
    expenses = FlatExpenses(40_000.0)
    husband_portfolio = make_portfolio(equity_post=100_000.0)
    infl = 0.03

    raw_cfg = make_sim(years=3, inflation_rate=infl, plot_mode="raw")
    real_cfg = make_sim(years=3, inflation_rate=infl, plot_mode="real")

    raw_results = run_sim(raw_cfg, husband, expenses, husband_portfolio)
    real_results = run_sim(real_cfg, husband, expenses, husband_portfolio)

    for key in ["expense_amt", "total_assets"]:
        assert_discounted(raw_results, real_results, key, infl)

    for key in ["work", "withdrawal"]:
        assert_discounted_class(raw_results, real_results, key, infl)