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


def make_portfolio(*, equity_pre=0.0, equity_post=0.0, bond_post=0.0, cash_post=0.0):
    return SimpleNamespace(
        equity_pre=equity_pre,
        equity_post=equity_post,
        bond_pre=0.0,
        bond_post=bond_post,
        cash_pre=0.0,
        cash_post=cash_post,
        real_estate=0.0,
    )


def make_sim(years):
    return SimpleNamespace(
        start_year=2026,
        years_to_simulate=years,
        monte_carlo_mode="pathBasedAnnualSampling",
        monte_carlo_plot_style="fill",
        use_correlated_returns=True,
        inflation_rate=0.0,
        num_sims=1,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode="raw",
        subplot_mode="fixed",
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


def run_single(years):
    cfg = make_sim(years)

    husband = make_person(
        age=40,
        retire_age=100,
        income=80_000.0,
        ss=0.0,
        ss_age=99,
        pension=0.0,
        pension_age=99,
        annuity=0.0,
        annuity_age=99,
    )
    wife = make_person(
        age=35,
        retire_age=60,
        income=999_999.0,
        ss=123_456.0,
        ss_age=35,
        pension=88_888.0,
        pension_age=35,
        annuity=77_777.0,
        annuity_age=35,
    )

    husband_portfolio = make_portfolio(
        equity_pre=10_000.0,
        equity_post=20_000.0,
        bond_post=5_000.0,
        cash_post=2_000.0,
    )
    wife_portfolio = make_portfolio(
        equity_pre=999_999.0,
        equity_post=999_999.0,
        bond_post=999_999.0,
        cash_post=999_999.0,
    )

    expenses = FlatExpenses(30_000.0)

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


def test_single_vs_couple_disabled_second_person_equivalence():
    results = run_single(2)

    # With second_person_enabled=False, the core creates an empty wife portfolio
    # and the wife income path is ignored. Only husband values should appear.
    assert row(results, "gross_income") == pytest.approx([0.0, 80_000.0, 80_000.0])
    assert row(results, "net_income") == pytest.approx([0.0, 80_000.0, 80_000.0])
    assert row(results, "net_income_husband") == pytest.approx([0.0, 80_000.0, 80_000.0])
    assert row(results, "net_income_wife") == pytest.approx([0.0, 0.0, 0.0])

    assert row(results, "pre_tax_assets") == pytest.approx([10_000.0, 10_000.0, 10_000.0])
    assert row(results, "post_tax_assets") == pytest.approx([27_000.0, 77_000.0, 127_000.0])
    assert row(results, "total_assets") == pytest.approx([37_000.0, 87_000.0, 137_000.0])

    assert row_class(results, "work") == pytest.approx([0.0, 80_000.0, 80_000.0])
    assert row_class(results, "ss") == pytest.approx([0.0, 0.0, 0.0])
    assert row_class(results, "pension") == pytest.approx([0.0, 0.0, 0.0])
    assert row_class(results, "annuity") == pytest.approx([0.0, 0.0, 0.0])
    assert row_class(results, "withdrawal") == pytest.approx([0.0, 0.0, 0.0])