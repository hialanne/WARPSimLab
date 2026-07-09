import pytest

import numpy as np

from src.warpsimlab.sim.simulationObject import Simulation
from src.warpsimlab.dataClasses.person import Person
from src.warpsimlab.dataClasses.portfolio import Portfolio
from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses


@pytest.fixture
def make_case(tmp_path):
    """
    Factory fixture for invariant tests.

    Returns:
        husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config

    Design goals:
    - real simulator objects, not mocks
    - deterministic by default
    - minimal but financially plausible baseline
    - easy per-test overrides
    """

    def _make_case(
        *,
        start_year=2025,
        years_to_simulate=5,
        inflation_rate=0.02,
        num_sims=1,
        plot_mode="nominal",
        subplot_mode="default",
        include_rmd=True,
        calculate_income_taxes=True,
        calculate_payroll_taxes=True,
        calculate_state_taxes=False,
        state_of_residence="CA",
        tax_filing_status="married_filing_jointly",
        second_person_enabled=False,
        include_realestate=False,
        use_fund_expenses=True,
        fund_expense=0.0015,
        always_use_expense_mode=True,
        scenario_expense_multiplier=1.0,
        sim_type="portfolio_sim",
        sim_rebalance="none",
        rebalance_every_year=False,
        annotate_plots=False,
        constant_y_plots=False,
        overlay_tax_impacts=False,
        overlay_fund_expense_impacts=False,
        overlay_household_expenses=False,
        overlay_profit_loss=False,
        overlay_retirement_age=False,
        retirement_withdraw_mode="None",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=0.0,
        eq_mean=0.05,
        bd_mean=0.02,
        cs_mean=0.01,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_mean=0.03,
        re_std=0.0,
        post_tax_equity_dividend_yield=0.015,
        post_tax_bond_interest_yield=0.02,
        post_tax_cash_interest_yield=0.01,
        husband_age=60,
        husband_retire_age=65,
        husband_income=100_000.0,
        husband_ss=24_000.0,
        husband_ss_age=67,
        husband_pension=0.0,
        husband_pension_age=65,
        husband_annuity=0.0,
        husband_annuity_age=65,
        husband_annual_401k_contribution=10_000.0,
        husband_annual_employer_match=5_000.0,
        husband_pension_inflation_adjustment_pct=0.0,
        wife_age=58,
        wife_retire_age=64,
        wife_income=80_000.0,
        wife_ss=18_000.0,
        wife_ss_age=67,
        wife_pension=0.0,
        wife_pension_age=65,
        wife_annuity=0.0,
        wife_annuity_age=65,
        wife_annual_401k_contribution=8_000.0,
        wife_annual_employer_match=4_000.0,
        wife_pension_inflation_adjustment_pct=0.0,
        husband_equity_pre=300_000.0,
        husband_equity_post=150_000.0,
        husband_bond_pre=100_000.0,
        husband_bond_post=50_000.0,
        husband_cash_pre=25_000.0,
        husband_cash_post=25_000.0,
        husband_real_estate=200_000.0,
        wife_equity_pre=200_000.0,
        wife_equity_post=100_000.0,
        wife_bond_pre=75_000.0,
        wife_bond_post=40_000.0,
        wife_cash_pre=20_000.0,
        wife_cash_post=20_000.0,
        wife_real_estate=0.0,
        annual_expense=70_000.0,
    ):
        husband = Person(
            age=husband_age,
            retire_age=husband_retire_age,
            income=husband_income,
            ss=husband_ss,
            ss_age=husband_ss_age,
            pension=husband_pension,
            pension_age=husband_pension_age,
            annuity=husband_annuity,
            annuity_age=husband_annuity_age,
            annual_401k_contribution=husband_annual_401k_contribution,
            annual_employer_match=husband_annual_employer_match,
            pension_inflation_adjustment_pct=husband_pension_inflation_adjustment_pct,
        )

        wife = Person(
            age=wife_age,
            retire_age=wife_retire_age,
            income=wife_income,
            ss=wife_ss,
            ss_age=wife_ss_age,
            pension=wife_pension,
            pension_age=wife_pension_age,
            annuity=wife_annuity,
            annuity_age=wife_annuity_age,
            annual_401k_contribution=wife_annual_401k_contribution,
            annual_employer_match=wife_annual_employer_match,
            pension_inflation_adjustment_pct=wife_pension_inflation_adjustment_pct,
        )

        husband_portfolio = Portfolio(
            equity_pre=husband_equity_pre,
            equity_post=husband_equity_post,
            bond_pre=husband_bond_pre,
            bond_post=husband_bond_post,
            cash_pre=husband_cash_pre,
            cash_post=husband_cash_post,
            real_estate=husband_real_estate,
        )

        wife_portfolio = Portfolio(
            equity_pre=wife_equity_pre,
            equity_post=wife_equity_post,
            bond_pre=wife_bond_pre,
            bond_post=wife_bond_post,
            cash_pre=wife_cash_pre,
            cash_post=wife_cash_post,
            real_estate=wife_real_estate,
        )

        expenses = DynamicExpenses()
        expenses.add_expense(
            start_year=start_year,
            cost=annual_expense,
            end_year=start_year + years_to_simulate,
            comment="baseline household expenses",
        )

        sim_config = Simulation(
            start_year=start_year,
            years_to_simulate=years_to_simulate,
            inflation_rate=inflation_rate,
            num_sims=num_sims,
            fund_expense=fund_expense,
            use_fund_expenses=use_fund_expenses,
            plot_mode=plot_mode,
            subplot_mode=subplot_mode,
            include_rmd=include_rmd,
            calculate_income_taxes=calculate_income_taxes,
            calculate_payroll_taxes=calculate_payroll_taxes,
            tax_filing_status=tax_filing_status,
            calculate_state_taxes=calculate_state_taxes,
            state_of_residence=state_of_residence,
            second_person_enabled=second_person_enabled,
            eq_mean=eq_mean,
            bd_mean=bd_mean,
            cs_mean=cs_mean,
            eq_std=eq_std,
            bd_std=bd_std,
            cs_std=cs_std,
            post_tax_equity_dividend_yield=post_tax_equity_dividend_yield,
            post_tax_bond_interest_yield=post_tax_bond_interest_yield,
            post_tax_cash_interest_yield=post_tax_cash_interest_yield,
            sim_type=sim_type,
            sim_rebalance=sim_rebalance,
            annotate_plots=annotate_plots,
            constant_y_plots=constant_y_plots,
            rebalance_every_year=rebalance_every_year,
            include_realestate=include_realestate,
            re_mean=re_mean,
            re_std=re_std,
            output_csv="None",
            csv_output_dir=str(tmp_path),
            retirement_withdraw_mode=retirement_withdraw_mode,
            retirement_withdraw_pct=retirement_withdraw_pct,
            retirement_withdraw_dollars=retirement_withdraw_dollars,
            always_use_expense_mode=always_use_expense_mode,
            scenario_expense_multiplier=scenario_expense_multiplier,
            overlay_tax_impacts=overlay_tax_impacts,
            overlay_fund_expense_impacts=overlay_fund_expense_impacts,
            overlay_household_expenses=overlay_household_expenses,
            overlay_profit_loss=overlay_profit_loss,
            overlay_retirement_age=overlay_retirement_age,
            show_simulated_shortfall_rate=False,

            use_snapshot_annotations=False,
            user_annotation_strings=[],
            root=None,
        )
        sim_config.return_correlation_matrix = np.eye(4)

        sim_config.eq_std = 0.01
        sim_config.bd_std = 0.01
        sim_config.cs_std = 0.01
        sim_config.re_std = 0.01

        return husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config

    return _make_case