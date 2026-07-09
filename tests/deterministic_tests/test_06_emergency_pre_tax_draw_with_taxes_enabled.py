import numpy as np
import pytest
from types import SimpleNamespace

from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios

# pytest.skip("Skipping test_06_emergency_pre_tax_draw_with_taxes_enabled tests for now", allow_module_level=True)


try:
    from src.warpsimlab.sim.engines import taxEngine
except ImportError:
    from src.warpsimlab.sim.engine import taxEngine


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


def make_portfolio(*, equity_pre=0.0, equity_post=0.0):
    return SimpleNamespace(
        equity_pre=equity_pre,
        equity_post=equity_post,
        bond_pre=0.0,
        bond_post=0.0,
        cash_pre=0.0,
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
        calculate_income_taxes=True,
        calculate_payroll_taxes=False,
        tax_filing_status="Married Filing Jointly",
        calculate_state_taxes=True,
        state_of_residence="NM",
        second_person_enabled=True,
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
        sim_rebalance="dont-rebalance",
        rebalance_every_year=False,
        include_realestate=False,
        re_mean=0.0,
        re_std=0.0,
        retirement_withdraw_mode="Off",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=0.0,
        always_use_expense_mode=True,
        scenario_expense_multiplier=1.0,
        household_eq_target=None,
        household_bd_target=None,
        household_cs_target=None,
    )


def run_sim(cfg, husband, wife, expenses, husband_portfolio, wife_portfolio):
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


def test_emergency_pre_tax_draw_with_taxes_enabled_nominal():
    husband = make_person(age=45, retire_age=100, income=20_000.0)
    wife = make_person(age=43, retire_age=100, income=20_000.0)
    expenses = FlatExpenses(100_000.0)
    husband_portfolio = make_portfolio(equity_pre=100_000.0, equity_post=20_000.0)
    wife_portfolio = make_portfolio()
    cfg = make_sim(years=1, inflation_rate=0.0, plot_mode="raw")

    taxEngine.initialize_tax_engine_for_simulation(cfg)
    year_cache = taxEngine.prepare_tax_year_cache(0, cfg)

    results = run_sim(cfg, husband, wife, expenses, husband_portfolio, wife_portfolio)

    _, _, _, baseline_tax, _ = taxEngine.calculate_total_income_tax_split(
        40_000.0,
        0.0,
        year_cache,
        cfg,
    )

    expected_emergency_pre_tax_used = 100_000.0 - 40_000.0 + baseline_tax - 20_000.0

    _, _, _, final_total_tax, _ = taxEngine.calculate_total_income_tax_split(
        40_000.0 + expected_emergency_pre_tax_used,
        0.0,
        year_cache,
        cfg,
    )

    expected_delta = final_total_tax - baseline_tax

    assert expected_emergency_pre_tax_used > 0.0
    assert expected_delta > 0.0

    assert row(results, "emergency_pre_tax_used") == pytest.approx(
        [0.0, expected_emergency_pre_tax_used]
    )
    assert row(results, "final_tax_delta") == pytest.approx([0.0, expected_delta])


def test_emergency_pre_tax_draw_with_taxes_enabled_real_mode_deflates_correctly():
    husband = make_person(age=45, retire_age=100, income=20_000.0)
    wife = make_person(age=43, retire_age=100, income=20_000.0)
    expenses = FlatExpenses(100_000.0)
    husband_portfolio = make_portfolio(equity_pre=100_000.0, equity_post=20_000.0)
    wife_portfolio = make_portfolio()
    infl = 0.03

    raw_cfg = make_sim(years=1, inflation_rate=infl, plot_mode="raw")
    real_cfg = make_sim(years=1, inflation_rate=infl, plot_mode="real")

    raw_results = run_sim(raw_cfg, husband, wife, expenses, husband_portfolio, wife_portfolio)
    real_results = run_sim(real_cfg, husband, wife, expenses, husband_portfolio, wife_portfolio)

    for key in [
        "taxes",
        "emergency_pre_tax_used",
        "final_tax_delta",
        "final_tax_delta_deducted",
        "final_tax_delta_uncovered",
        "pre_tax_assets",
        "post_tax_assets",
    ]:
        assert_discounted(raw_results, real_results, key, infl)