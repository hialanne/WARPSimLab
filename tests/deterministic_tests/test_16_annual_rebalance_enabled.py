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


def make_portfolio(*, equity_post=0.0, bond_post=0.0, cash_post=0.0):
    return SimpleNamespace(
        equity_pre=0.0,
        equity_post=equity_post,
        bond_pre=0.0,
        bond_post=bond_post,
        cash_pre=0.0,
        cash_post=cash_post,
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
        eq_mean=0.10,
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
        sim_rebalance="custom",
        rebalance_every_year=True,
        include_realestate=False,
        retirement_withdraw_mode="Off",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=0.0,
        always_use_expense_mode=True,
        scenario_expense_multiplier=1.0,
        household_eq_target=None,
        household_bd_target=None,
        household_cs_target=None,
        custom_stock=0.50,
        custom_bonds=0.30,
        custom_cash=0.20,
    )


def run_sim(cfg):
    husband = make_person(age=40, retire_age=100)
    wife = make_person(age=0, retire_age=0)
    husband_portfolio = make_portfolio(
        equity_post=60.0,
        bond_post=30.0,
        cash_post=10.0,
    )
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


def test_annual_rebalance_enabled_nominal():
    cfg = make_sim(years=2, inflation_rate=0.0, plot_mode="raw")
    results = run_sim(cfg)

    # create_sim_portfolio with custom rebalance sets year-0 holdings to 50/30/20.
    # Then each year equity grows 10%, followed by annual rebalance back to 50/30/20.
    assert row(results, "total_assets") == pytest.approx([100.0, 105.0, 110.25])
    assert row(results, "bonds") == pytest.approx([30.0, 31.5, 33.075])
    assert row(results, "cash") == pytest.approx([20.0, 21.0, 22.05])

    # Stability of target weights at each reported year.
    assert row(results, "bonds")[1:] == pytest.approx(0.30 * row(results, "total_assets")[1:])
    assert row(results, "cash")[1:] == pytest.approx(0.20 * row(results, "total_assets")[1:])


def test_annual_rebalance_enabled_real_mode_deflates_correctly():
    infl = 0.03
    raw_cfg = make_sim(years=2, inflation_rate=infl, plot_mode="raw")
    real_cfg = make_sim(years=2, inflation_rate=infl, plot_mode="real")

    raw_results = run_sim(raw_cfg)
    real_results = run_sim(real_cfg)

    for key in ["total_assets", "bonds", "cash", "post_tax_assets"]:
        assert_discounted(raw_results, real_results, key, infl)