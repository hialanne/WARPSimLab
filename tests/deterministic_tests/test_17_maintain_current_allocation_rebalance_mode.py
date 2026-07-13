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


def make_portfolio(
    *,
    equity_pre=0.0,
    equity_post=0.0,
    bond_pre=0.0,
    bond_post=0.0,
    cash_pre=0.0,
    cash_post=0.0,
):
    return SimpleNamespace(
        equity_pre=equity_pre,
        equity_post=equity_post,
        bond_pre=bond_pre,
        bond_post=bond_post,
        cash_pre=cash_pre,
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
        tax_filing_status="Married Filing Jointly",
        calculate_state_taxes=False,
        state_of_residence="NM",
        second_person_enabled=True,
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
        sim_initial_allocation_mode="maintain-current-allocation",
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
        custom_stock=0.0,
        custom_bonds=0.0,
        custom_cash=1.0,
    )


def run_sim(cfg):
    husband = make_person(age=40, retire_age=100)
    wife = make_person(age=38, retire_age=100)

    # Different asset locations by spouse:
    # husband has only pre-tax equity, wife has only post-tax cash.
    husband_portfolio = make_portfolio(equity_pre=100.0)
    wife_portfolio = make_portfolio(cash_post=100.0)
    expenses = FlatExpenses(0.0)

    results = simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        cfg,
        num_sims=1,
    )
    return results, cfg


def row(results, key):
    return results[key][0]


def assert_discounted(raw_results, real_results, key, inflation_rate):
    discount = np.array([(1.0 + inflation_rate) ** t for t in range(raw_results[key].shape[1])])
    assert row(real_results, key) == pytest.approx(row(raw_results, key) / discount)


def test_maintain_current_allocation_rebalance_mode_nominal():
    results, cfg = run_sim(make_sim(years=1, inflation_rate=0.0, plot_mode="raw"))

    # Household targets are computed once from the combined starting investable assets.
    assert cfg.household_eq_target == pytest.approx(0.50)
    assert cfg.household_bd_target == pytest.approx(0.00)
    assert cfg.household_cs_target == pytest.approx(0.50)

    # Year 0 already reflects the maintain-current-allocation mapping per portfolio.
    assert row(results, "total_assets") == pytest.approx([200.0, 210.0])
    assert row(results, "bonds") == pytest.approx([0.0, 0.0])
    assert row(results, "cash") == pytest.approx([100.0, 105.0])

    # Household cash remains at 50% of total after the yearly rebalance.
    assert row(results, "cash")[1] == pytest.approx(0.50 * row(results, "total_assets")[1])


def test_maintain_current_allocation_rebalance_mode_real_mode_deflates_correctly():
    infl = 0.03
    raw_results, _ = run_sim(make_sim(years=1, inflation_rate=infl, plot_mode="raw"))
    real_results, _ = run_sim(make_sim(years=1, inflation_rate=infl, plot_mode="real"))

    for key in ["total_assets", "cash", "bonds", "pre_tax_assets", "post_tax_assets"]:
        assert_discounted(raw_results, real_results, key, infl)