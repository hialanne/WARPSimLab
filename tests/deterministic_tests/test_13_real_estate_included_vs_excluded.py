import numpy as np
import pytest
from types import SimpleNamespace

from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


class FlatExpenses:
    def __init__(self, annual_amount: float):
        self.annual_amount = annual_amount

    def get_total_expense_for_year(self, year: int) -> float:
        return self.annual_amount


def make_person(*, age, retire_age):
    return SimpleNamespace(
        age=age,
        retire_age=retire_age,
        income=0.0,
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


def make_portfolio(*, equity_post=0.0, real_estate=0.0):
    return SimpleNamespace(
        equity_pre=0.0,
        equity_post=equity_post,
        bond_pre=0.0,
        bond_post=0.0,
        cash_pre=0.0,
        cash_post=0.0,
        real_estate=real_estate,
    )


def make_sim(*, years, include_realestate, inflation_rate=0.0, plot_mode="raw"):
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
        sim_initial_allocation_mode="dont-rebalance",
        rebalance_every_year=False,
        include_realestate=include_realestate,
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


def run_sim(cfg, husband_portfolio):
    husband = make_person(age=40, retire_age=100)
    wife = make_person(age=0, retire_age=0)
    wife_portfolio = make_portfolio()
    expenses = FlatExpenses(0.0)
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


def test_real_estate_included_vs_excluded_nominal():
    husband_portfolio = make_portfolio(equity_post=100_000.0, real_estate=50_000.0)

    excluded_cfg = make_sim(years=1, include_realestate=False, inflation_rate=0.0, plot_mode="raw")
    included_cfg = make_sim(years=1, include_realestate=True, inflation_rate=0.0, plot_mode="raw")

    excluded = run_sim(excluded_cfg, husband_portfolio)
    included = run_sim(included_cfg, husband_portfolio)

    assert row(excluded, "real_estate") == pytest.approx([0.0, 0.0])
    assert row(included, "real_estate") == pytest.approx([50_000.0, 50_000.0])

    assert row(excluded, "post_tax_assets") == pytest.approx([100_000.0, 100_000.0])
    assert row(included, "post_tax_assets") == pytest.approx([100_000.0, 100_000.0])

    assert row(excluded, "total_assets") == pytest.approx([100_000.0, 100_000.0])
    assert row(included, "total_assets") == pytest.approx([150_000.0, 150_000.0])


def test_real_estate_included_vs_excluded_real_mode_deflates_correctly():
    husband_portfolio = make_portfolio(equity_post=100_000.0, real_estate=50_000.0)
    infl = 0.03

    raw_cfg = make_sim(years=1, include_realestate=True, inflation_rate=infl, plot_mode="raw")
    real_cfg = make_sim(years=1, include_realestate=True, inflation_rate=infl, plot_mode="real")

    raw_results = run_sim(raw_cfg, husband_portfolio)
    real_results = run_sim(real_cfg, husband_portfolio)

    for key in ["real_estate", "post_tax_assets", "total_assets"]:
        assert_discounted(raw_results, real_results, key, infl)