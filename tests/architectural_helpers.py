"""Shared real-object construction and comparisons for financial regression tests."""

import copy

import numpy as np

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.dataClasses.person import Person
from src.warpsimlab.dataClasses.portfolio import Portfolio
from src.warpsimlab.sim.simulationObject import Simulation


def make_simulation(**overrides):
    """Real one-year configuration with no returns, taxes, fees or withdrawals.

    Scenario-specific financial assumptions belong at the call site. Defaults
    contain no private engine state; production preparation owns that state.
    Each call constructs fresh mutable defaults through Simulation itself.
    """
    values = dict(
        start_year=2026, years_to_simulate=1, inflation_rate=0.0, num_sims=1,
        fund_expense=0.0, use_fund_expenses=False, inflation_mode="nominal",
        results_mode="fill", include_rmd=False, calculate_income_taxes=False,
        calculate_payroll_taxes=False, tax_filing_status="Single",
        calculate_state_taxes=False, state_of_residence="TX", second_person_enabled=False,
        eq_mean=0.0, bd_mean=0.0, cs_mean=0.0, re_mean=0.0,
        eq_std=0.0, bd_std=0.0, cs_std=0.0, re_std=0.0,
        post_tax_equity_dividend_yield=0.0, post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0, sim_type="portfolio_sim",
        always_use_expense_mode=True, output_csv="None", show_simulated_shortfall_rate=False,
        overlay_profit_loss=False,
    )
    values.update(overrides)
    return Simulation(**values)


def make_person(**overrides):
    """Real person with no income or contributions; activation ages remain explicit."""
    values = dict(age=40, retire_age=100, income=0.0, ss=0.0, ss_age=99,
                  pension=0.0, pension_age=99, annuity=0.0, annuity_age=99)
    values.update(overrides)
    return Person(**values)


def make_portfolio(**overrides):
    """Real empty portfolio; specify only the funded buckets in each scenario."""
    values = dict(equity_pre=0.0, equity_post=0.0, bond_pre=0.0, bond_post=0.0,
                  cash_pre=0.0, cash_post=0.0, real_estate=0.0)
    values.update(overrides)
    return Portfolio(**values)


def run_invariant_case(make_case, **overrides):
    """Execute an existing invariant fixture case and return its core and config."""
    from src.warpsimlab.sim.simulation import run_pipeline

    inputs = make_case(**overrides)
    return run_pipeline(*inputs)["core"], inputs[-1]


def make_execution_case(**config_overrides):
    """Exercise working/retired/survivor years, tax history and multiple buckets."""
    husband = make_person(
        age=68, retire_age=70, income=120_000, ss=28_000, ss_age=70,
        pension=12_000, pension_age=70, annuity=2_000, annuity_age=70,
        annual_401k_contribution=9_000, annual_employer_match=2_000,
        annual_hsa_contribution=3_000, annual_hsa_employer_contribution=1_000,
        modeled_death_age=72, medicare_annual_cost=3_000,
    )
    wife = make_person(
        age=66, retire_age=68, income=75_000, ss=20_000, ss_age=68,
        pension=8_000, pension_age=68, annuity=1_000, annuity_age=68,
        annual_401k_contribution=5_000, annual_employer_match=1_000,
        annual_hsa_contribution=2_000, annual_hsa_employer_contribution=500,
        modeled_death_age=74, medicare_annual_cost=2_500,
    )
    def portfolio(scale):
        return make_portfolio(
            equity_pre=200_000 * scale, equity_post=120_000 * scale,
            bond_pre=80_000 * scale, bond_post=40_000 * scale,
            cash_pre=20_000 * scale, cash_post=40_000 * scale,
            equity_roth=30_000 * scale, bond_roth=10_000 * scale,
            cash_roth=5_000 * scale, hsa_equity=5_000 * scale,
            hsa_bond=3_000 * scale, hsa_cash=2_000 * scale,
            real_estate=100_000 * scale,
        )
    h_port, w_port = portfolio(1.0), portfolio(0.6)
    expenses = DynamicExpenses()
    expenses.add_expense(2027, 40_000, comment="ordinary household spending")
    expenses.add_expense(2027, 5_000, comment="qualified spending", is_hsa_eligible=True)
    values = dict(
        start_year=2026, years_to_simulate=8, inflation_rate=0.025, num_sims=3,
        fund_expense=0.002, use_fund_expenses=True, inflation_mode="nominal",
        results_mode="fill", include_rmd=True, calculate_income_taxes=True,
        calculate_payroll_taxes=True, tax_filing_status="Married filing jointly",
        calculate_state_taxes=True, state_of_residence="CO", second_person_enabled=True,
        eq_mean=0.07, bd_mean=0.03, cs_mean=0.01, re_mean=0.04,
        eq_std=0.14, bd_std=0.04, cs_std=0.005, re_std=0.08,
        husband_portfolio=h_port, wife_portfolio=w_port,
        post_tax_equity_dividend_yield=0.015, post_tax_bond_interest_yield=0.02,
        post_tax_cash_interest_yield=0.01, sim_type="portfolio_sim",
        sim_initial_allocation_mode="maintain-current-allocation",
        include_realestate=True, rebalance_every_year=True,
        always_use_expense_mode=False, retirement_withdraw_mode="Percentage + Inflation",
        retirement_withdraw_pct=5.0, irmaa_enabled=True,
        historical_magi=dict(two_years_prior=300_000, one_year_prior=150_000),
        show_simulated_shortfall_rate=False, output_csv="None", overlay_profit_loss=True,
        special_income_streams=[dict(
            name="Temporary consulting", owner="wife", amount=7_000,
            start_age=67, end_age=69, taxable=True, enabled=True,
            adjustment_mode="inflation", adjustment_pct=50.0,
        )],
        roth_flows=[dict(
            name="Early conversion", owner="husband", type="roth_conversion",
            amount=35_000, start_age=69, end_age=70, enabled=True,
            inflation_adjustment_pct=0.0,
        )],
        user_annotation_strings=[[dict(text="user note", color=None)]],
        scenario_explorer_annotations=[[dict(text="scenario note", color="blue")]],
        report_options={"columns": ["taxes", "magi"], "options": {"detail": True}},
    )
    values.update(config_overrides)
    return dict(husband_portfolio=h_port, wife_portfolio=w_port, husband=husband,
                wife=wife, expenses=expenses, sim_config=make_simulation(**values))


def public_input_tree(value):
    """Snapshot public input data, including nested objects, without runtime caches."""
    if isinstance(value, dict):
        return {key: public_input_tree(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(public_input_tree(item) for item in value)
    if hasattr(value, "__dict__"):
        return {key: public_input_tree(item) for key, item in vars(value).items()
                if not key.startswith("_")}
    return copy.deepcopy(value)


def user_config_tree(config):
    """Current compatibility boundary, not future whole-object immutability.

    Maintain-current allocation writes these public derived targets; private
    sampling, withdrawal and engine caches are also existing runtime state.
    Do not assert that those caches must remain stored on Simulation forever.
    """
    derived_targets = {"household_eq_target", "household_bd_target", "household_cs_target"}
    return {key: public_input_tree(value) for key, value in vars(config).items()
            if not key.startswith("_") and key not in derived_targets}


def assert_tree_equal(actual, expected, location="result"):
    """Compare every key/array, including NaNs, nested breakdowns and metadata."""
    if isinstance(expected, np.ndarray):
        np.testing.assert_array_equal(actual, expected, err_msg=location, strict=True)
    elif isinstance(expected, dict):
        assert actual.keys() == expected.keys(), location
        for key in expected:
            assert_tree_equal(actual[key], expected[key], f"{location}.{key}")
    elif isinstance(expected, (list, tuple)):
        assert type(actual) is type(expected), location
        assert len(actual) == len(expected), location
        for index, item in enumerate(expected):
            assert_tree_equal(actual[index], item, f"{location}[{index}]")
    else:
        assert actual == expected, location


def core_row(core, index):
    """Keep the simulation dimension so an extracted row matches a one-path run."""
    return {key: core_row(value, index) if isinstance(value, dict)
            else value[index:index + 1] if isinstance(value, np.ndarray) else value
            for key, value in core.items()}
