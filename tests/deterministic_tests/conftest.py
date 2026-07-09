# tests/conftest.py

from types import SimpleNamespace

import pytest


class PersonStub:
    def __init__(
        self,
        *,
        age,
        retire_age,
        income=0.0,
        ss=0.0,
        ss_age=70,
        pension=0.0,
        pension_age=100,
        annuity=0.0,
        annuity_age=100,
        annual_401k_contribution=0.0,
        annual_employer_match=0.0,
        pension_inflation_adjustment_pct=0.0,
    ):
        self.age = age
        self.retire_age = retire_age
        self.income = income
        self.ss = ss
        self.ss_age = ss_age
        self.pension = pension
        self.pension_age = pension_age
        self.annuity = annuity
        self.annuity_age = annuity_age
        self.annual_401k_contribution = annual_401k_contribution
        self.annual_employer_match = annual_employer_match
        self.pension_inflation_adjustment_pct = pension_inflation_adjustment_pct


class PortfolioStub:
    def __init__(
        self,
        *,
        equity_pre=0.0,
        equity_post=0.0,
        bond_pre=0.0,
        bond_post=0.0,
        cash_pre=0.0,
        cash_post=0.0,
        real_estate=0.0,
    ):
        self.equity_pre = equity_pre
        self.equity_post = equity_post
        self.bond_pre = bond_pre
        self.bond_post = bond_post
        self.cash_pre = cash_pre
        self.cash_post = cash_post
        self.real_estate = real_estate


class DynamicExpensesStub:
    def __init__(self):
        self.expenses = []

    def add_expense(self, start_year, cost, end_year=None, comment=""):
        self.expenses.append(
            {
                "start_year": start_year,
                "end_year": end_year,
                "cost": cost,
                "comment": comment,
            }
        )

    def get_total_expense_for_year(self, year):
        total = 0.0
        for exp in self.expenses:
            start = exp["start_year"]
            end = exp["end_year"]
            if year >= start and (end is None or year <= end):
                total += exp["cost"]
        return total


def make_config(**overrides):
    base = dict(
        start_year=2025,
        years_to_simulate=1,
        inflation_rate=0.0,
        num_sims=1,
        monte_carlo_mode="pathBasedAnnualSampling",
        monte_carlo_plot_style="fill",
        use_correlated_returns=True,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode="nominal",
        subplot_mode="baseline",
        include_rmd=False,
        calculate_income_taxes=False,
        calculate_payroll_taxes=False,
        tax_filing_status="Single",
        calculate_state_taxes=False,
        state_of_residence="TX",
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
        sim_rebalance="none",
        custom_stock=0.0,
        custom_bonds=0.0,
        custom_cash=1.0,
        annotate_plots=False,
        constant_y_plots=False,
        rebalance_every_year=False,
        include_realestate=False,
        re_mean=0.0,
        re_std=0.0,
        output_csv="None",
        csv_output_dir=None,
        retirement_withdraw_mode="Off",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=0.0,
        always_use_expense_mode=True,
        scenario_expense_multiplier=1.0,
        overlay_tax_impacts=False,
        overlay_fund_expense_impacts=False,
        overlay_household_expenses=False,
        overlay_profit_loss=True,
        overlay_retirement_age=False,
        show_simulated_shortfall_rate=False,
        use_snapshot_annotations=False,
        user_annotation_strings=[],
        root=None,
        househould_eq_target=None,
        househould_bd_target=None,
        househould_cs_target=None,
        household_eq_target=None,
        household_bd_target=None,
        household_cs_target=None,
        _ret_withdraw_base_dollars=None,
        _ret_withdraw_base_year=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.fixture
def scenario_builders():
    return SimpleNamespace(
        Person=PersonStub,
        Portfolio=PortfolioStub,
        DynamicExpenses=DynamicExpensesStub,
        make_config=make_config,
    )