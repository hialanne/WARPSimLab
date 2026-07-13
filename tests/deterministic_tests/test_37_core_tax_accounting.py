import numpy as np
import pytest

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.dataClasses.person import Person
from src.warpsimlab.dataClasses.portfolio import Portfolio
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios
from src.warpsimlab.sim.simulationObject import Simulation


def make_person(
    *,
    age=40,
    retire_age=100,
    income=0.0,
    ss=0.0,
    ss_age=99,
    pension=0.0,
    pension_age=99,
    annuity=0.0,
    annuity_age=99,
):
    return Person(
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


def make_portfolio(
    *,
    equity_post=0.0,
):
    return Portfolio(
        equity_pre=0.0,
        equity_post=equity_post,
        bond_pre=0.0,
        bond_post=0.0,
        cash_pre=0.0,
        cash_post=0.0,
        real_estate=0.0,
        equity_roth=0.0,
        bond_roth=0.0,
        cash_roth=0.0,
        hsa_cash=0.0,
        hsa_equity=0.0,
        hsa_bond=0.0,
    )


def make_config(
    *,
    calculate_income_taxes=True,
    calculate_payroll_taxes=False,
    calculate_state_taxes=False,
    state_of_residence="TX",
    tax_filing_status="Single",
    second_person_enabled=False,
    dividend_yield=0.0,
):
    return Simulation(
        start_year=2026,
        years_to_simulate=1,
        inflation_rate=0.0,
        num_sims=1,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode="raw",
        subplot_mode="baseline",
        include_rmd=False,
        calculate_income_taxes=calculate_income_taxes,
        calculate_payroll_taxes=calculate_payroll_taxes,
        tax_filing_status=tax_filing_status,
        calculate_state_taxes=calculate_state_taxes,
        state_of_residence=state_of_residence,
        second_person_enabled=second_person_enabled,
        eq_mean=0.0,
        bd_mean=0.0,
        cs_mean=0.0,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        post_tax_equity_dividend_yield=dividend_yield,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        sim_type="portfolio_sim",
        sim_initial_allocation_mode="dont-rebalance",
        rebalance_every_year=False,
        include_realestate=False,
        re_mean=0.0,
        re_std=0.0,
        output_csv="None",
        retirement_withdraw_mode="Off",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=0.0,
        always_use_expense_mode=True,
        sequence_risk_enabled=False,
        scenario_expense_multiplier=1.0,
        overlay_tax_impacts=False,
        overlay_fund_expense_impacts=False,
        overlay_household_expenses=False,
        overlay_profit_loss=False,
        overlay_retirement_age=False,
        show_simulated_shortfall_rate=False,
        use_snapshot_annotations=False,
        user_annotation_strings=[],
        root=None,
    )


def install_market_path(
    monkeypatch,
    *,
    equity_return=0.0,
):
    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        assert years_to_simulate == 1

        return {
            "eq": np.array([0.0, equity_return], dtype=float),
            "bd": np.zeros(2, dtype=float),
            "cs": np.zeros(2, dtype=float),
            "re": np.zeros(2, dtype=float),
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )


def run_one_year(
    monkeypatch,
    *,
    husband,
    husband_portfolio=None,
    wife=None,
    wife_portfolio=None,
    calculate_income_taxes=True,
    calculate_payroll_taxes=False,
    calculate_state_taxes=False,
    state_of_residence="TX",
    tax_filing_status="Single",
    second_person_enabled=False,
    dividend_yield=0.0,
    equity_return=0.0,
):
    install_market_path(
        monkeypatch,
        equity_return=equity_return,
    )

    if husband_portfolio is None:
        husband_portfolio = make_portfolio()

    if wife is None:
        wife = make_person()

    if wife_portfolio is None:
        wife_portfolio = make_portfolio()

    return simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        DynamicExpenses(),
        make_config(
            calculate_income_taxes=calculate_income_taxes,
            calculate_payroll_taxes=calculate_payroll_taxes,
            calculate_state_taxes=calculate_state_taxes,
            state_of_residence=state_of_residence,
            tax_filing_status=tax_filing_status,
            second_person_enabled=second_person_enabled,
            dividend_yield=dividend_yield,
        ),
        num_sims=1,
    )


def test_federal_ordinary_income_tax_is_calculated_and_deducted(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband=make_person(
            income=50_000.0,
        ),
        calculate_income_taxes=True,
        calculate_payroll_taxes=False,
    )

    standard_deduction = 16_100.0
    taxable_income = 50_000.0 - standard_deduction

    expected_federal_tax = (
        12_400.0 * 0.10
        + (taxable_income - 12_400.0) * 0.12
    )

    expected_net_income = 50_000.0 - expected_federal_tax

    assert taxable_income == pytest.approx(33_900.0)
    assert expected_federal_tax == pytest.approx(3_820.0)
    assert expected_net_income == pytest.approx(46_180.0)

    assert results["gross_income"][0, 1] == pytest.approx(
        50_000.0
    )
    assert results["federal_ordinary_tax"][0, 1] == (
        pytest.approx(expected_federal_tax)
    )
    assert results["federal_qualified_dividend_tax"][0, 1] == (
        pytest.approx(0.0)
    )
    assert results["state_income_tax"][0, 1] == pytest.approx(
        0.0
    )
    assert results["payroll_tax"][0, 1] == pytest.approx(0.0)
    assert results["taxes"][0, 1] == pytest.approx(
        expected_federal_tax
    )

    assert results["net_income"][0, 1] == pytest.approx(
        expected_net_income
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        expected_net_income
    )


def test_income_below_standard_deduction_has_no_federal_tax(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband=make_person(
            income=16_000.0,
        ),
        calculate_income_taxes=True,
        calculate_payroll_taxes=False,
    )

    assert results["federal_ordinary_tax"][0, 1] == (
        pytest.approx(0.0)
    )
    assert results["taxes"][0, 1] == pytest.approx(0.0)
    assert results["net_income"][0, 1] == pytest.approx(
        16_000.0
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        16_000.0
    )


def test_qualified_dividend_tax_is_calculated_separately(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband=make_person(),
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        calculate_income_taxes=True,
        calculate_payroll_taxes=False,
        dividend_yield=0.50,
        equity_return=0.50,
    )

    expected_dividends = 50_000.0

    zero_percent_band = 48_350.0
    dividends_taxed_at_fifteen = (
        expected_dividends - zero_percent_band
    )
    expected_dividend_tax = (
        dividends_taxed_at_fifteen * 0.15
    )

    expected_net_income = (
        expected_dividends - expected_dividend_tax
    )

    assert expected_dividend_tax == pytest.approx(247.50)

    assert results["qualified_dividends"][0, 1] == pytest.approx(
        expected_dividends
    )
    assert results["federal_ordinary_tax"][0, 1] == (
        pytest.approx(0.0)
    )
    assert results["federal_qualified_dividend_tax"][0, 1] == (
        pytest.approx(expected_dividend_tax)
    )
    assert results["taxes"][0, 1] == pytest.approx(
        expected_dividend_tax
    )
    assert results["net_income"][0, 1] == pytest.approx(
        expected_net_income
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        100_000.0 + expected_net_income
    )


def test_flat_state_tax_is_calculated_on_income(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband=make_person(
            income=100_000.0,
        ),
        calculate_income_taxes=False,
        calculate_payroll_taxes=False,
        calculate_state_taxes=True,
        state_of_residence="CO",
    )

    expected_state_tax = 100_000.0 * 0.044
    expected_net_income = 100_000.0 - expected_state_tax

    assert expected_state_tax == pytest.approx(4_400.0)

    assert results["federal_ordinary_tax"][0, 1] == (
        pytest.approx(0.0)
    )
    assert results["federal_qualified_dividend_tax"][0, 1] == (
        pytest.approx(0.0)
    )
    assert results["state_income_tax"][0, 1] == pytest.approx(
        expected_state_tax
    )
    assert results["taxes"][0, 1] == pytest.approx(
        expected_state_tax
    )
    assert results["net_income"][0, 1] == pytest.approx(
        expected_net_income
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        expected_net_income
    )


def test_payroll_tax_components_are_calculated_from_work_income(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband=make_person(
            income=50_000.0,
        ),
        calculate_income_taxes=False,
        calculate_payroll_taxes=True,
    )

    expected_social_security_tax = 50_000.0 * 0.062
    expected_medicare_tax = 50_000.0 * 0.0145
    expected_additional_medicare_tax = 0.0

    expected_payroll_tax = (
        expected_social_security_tax
        + expected_medicare_tax
        + expected_additional_medicare_tax
    )

    expected_net_income = 50_000.0 - expected_payroll_tax

    assert expected_social_security_tax == pytest.approx(
        3_100.0
    )
    assert expected_medicare_tax == pytest.approx(725.0)
    assert expected_payroll_tax == pytest.approx(3_825.0)

    assert results["social_security_payroll_tax"][0, 1] == (
        pytest.approx(expected_social_security_tax)
    )
    assert results["medicare_tax"][0, 1] == pytest.approx(
        expected_medicare_tax
    )
    assert results["additional_medicare_tax"][0, 1] == (
        pytest.approx(expected_additional_medicare_tax)
    )
    assert results["payroll_tax"][0, 1] == pytest.approx(
        expected_payroll_tax
    )
    assert results["taxes"][0, 1] == pytest.approx(
        expected_payroll_tax
    )
    assert results["net_income"][0, 1] == pytest.approx(
        expected_net_income
    )


def test_additional_medicare_tax_applies_above_single_threshold(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband=make_person(
            income=250_000.0,
        ),
        calculate_income_taxes=False,
        calculate_payroll_taxes=True,
        tax_filing_status="Single",
    )

    expected_social_security_tax = 184_500.0 * 0.062
    expected_medicare_tax = 250_000.0 * 0.0145
    expected_additional_medicare_tax = (
        250_000.0 - 200_000.0
    ) * 0.009

    expected_payroll_tax = (
        expected_social_security_tax
        + expected_medicare_tax
        + expected_additional_medicare_tax
    )

    assert results["social_security_payroll_tax"][0, 1] == (
        pytest.approx(expected_social_security_tax)
    )
    assert results["medicare_tax"][0, 1] == pytest.approx(
        expected_medicare_tax
    )
    assert results["additional_medicare_tax"][0, 1] == (
        pytest.approx(expected_additional_medicare_tax)
    )
    assert results["payroll_tax"][0, 1] == pytest.approx(
        expected_payroll_tax
    )


def test_payroll_tax_excludes_pension_income(monkeypatch):
    results = run_one_year(
        monkeypatch,
        husband=make_person(
            age=69,
            retire_age=65,
            pension=100_000.0,
            pension_age=70,
        ),
        calculate_income_taxes=False,
        calculate_payroll_taxes=True,
    )

    assert (
        results["breakdown_by_class"]["pension"][0, 1]
        == pytest.approx(100_000.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        100_000.0
    )

    assert results["social_security_payroll_tax"][0, 1] == (
        pytest.approx(0.0)
    )
    assert results["medicare_tax"][0, 1] == pytest.approx(0.0)
    assert results["additional_medicare_tax"][0, 1] == (
        pytest.approx(0.0)
    )
    assert results["payroll_tax"][0, 1] == pytest.approx(0.0)
    assert results["taxes"][0, 1] == pytest.approx(0.0)
    assert results["net_income"][0, 1] == pytest.approx(
        100_000.0
    )


def test_total_tax_equals_sum_of_all_tax_components(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband=make_person(
            income=100_000.0,
        ),
        calculate_income_taxes=True,
        calculate_payroll_taxes=True,
        calculate_state_taxes=True,
        state_of_residence="CO",
    )

    component_total = (
        results["federal_ordinary_tax"][0, 1]
        + results["federal_qualified_dividend_tax"][0, 1]
        + results["state_income_tax"][0, 1]
        + results["payroll_tax"][0, 1]
    )

    assert results["taxes"][0, 1] == pytest.approx(
        component_total
    )

    assert results["payroll_tax"][0, 1] == pytest.approx(
        results["social_security_payroll_tax"][0, 1]
        + results["medicare_tax"][0, 1]
        + results["additional_medicare_tax"][0, 1]
    )

    assert results["net_income"][0, 1] == pytest.approx(
        results["gross_income"][0, 1]
        - results["taxes"][0, 1]
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        results["net_income"][0, 1]
    )


def test_couple_net_income_is_allocated_after_household_tax(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband=make_person(
            income=60_000.0,
        ),
        wife=make_person(
            income=40_000.0,
        ),
        calculate_income_taxes=True,
        calculate_payroll_taxes=False,
        tax_filing_status="Married Filing Jointly",
        second_person_enabled=True,
    )

    household_tax = results["taxes"][0, 1]
    husband_share = 60_000.0 / 100_000.0
    wife_share = 40_000.0 / 100_000.0

    expected_husband_net = (
        60_000.0 - household_tax * husband_share
    )
    expected_wife_net = (
        40_000.0 - household_tax * wife_share
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        100_000.0
    )
    assert results["net_income_husband"][0, 1] == (
        pytest.approx(expected_husband_net)
    )
    assert results["net_income_wife"][0, 1] == (
        pytest.approx(expected_wife_net)
    )

    assert (
        results["net_income_husband"][0, 1]
        + results["net_income_wife"][0, 1]
        == pytest.approx(results["net_income"][0, 1])
    )