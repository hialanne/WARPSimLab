import numpy as np
import pytest

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.dataClasses.person import Person
from src.warpsimlab.dataClasses.portfolio import Portfolio
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios
from src.warpsimlab.sim.simulationObject import Simulation


STARTING_BALANCE = 100_000.0

EQUITY_TOTAL_RETURN = 0.08
EQUITY_DIVIDEND_YIELD = 0.02
EQUITY_PRICE_RETURN = (
    EQUITY_TOTAL_RETURN - EQUITY_DIVIDEND_YIELD
)

POSITIVE_BOND_RETURN = 0.08
NEGATIVE_BOND_RETURN = -0.10

POSITIVE_CASH_RETURN = 0.05
NEGATIVE_CASH_RETURN = -0.03


def make_person():
    """
    Create a person with no income and no active retirement income sources.
    """
    return Person(
        age=40,
        retire_age=100,
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
    equity_roth=0.0,
    hsa_equity=0.0,
    bond_pre=0.0,
    bond_post=0.0,
    bond_roth=0.0,
    hsa_bond=0.0,
    cash_pre=0.0,
    cash_post=0.0,
    cash_roth=0.0,
    hsa_cash=0.0,
):
    """
    Create a portfolio containing only the asset buckets under test.
    """
    return Portfolio(
        equity_pre=equity_pre,
        equity_post=equity_post,
        bond_pre=bond_pre,
        bond_post=bond_post,
        cash_pre=cash_pre,
        cash_post=cash_post,
        real_estate=0.0,
        equity_roth=equity_roth,
        bond_roth=bond_roth,
        cash_roth=cash_roth,
        hsa_cash=hsa_cash,
        hsa_equity=hsa_equity,
        hsa_bond=hsa_bond,
    )


def make_config(
    *,
    dividend_yield=0.0,
):
    """
    Create a one-year deterministic core configuration.

    Unrelated behavior is disabled so each test isolates asset accounting.
    """
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
    bond_return=0.0,
    cash_return=0.0,
    real_estate_return=0.0,
):
    """
    Replace random market-path generation with one known annual return.
    """
    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        assert years_to_simulate == 1

        return {
            "eq": np.array([0.0, equity_return], dtype=float),
            "bd": np.array([0.0, bond_return], dtype=float),
            "cs": np.array([0.0, cash_return], dtype=float),
            "re": np.array([0.0, real_estate_return], dtype=float),
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )


def run_one_year(
    monkeypatch,
    husband_portfolio,
    *,
    equity_return=0.0,
    bond_return=0.0,
    cash_return=0.0,
    real_estate_return=0.0,
    dividend_yield=0.0,
):
    """
    Run one deterministic year through the real core simulation pipeline.
    """
    install_market_path(
        monkeypatch,
        equity_return=equity_return,
        bond_return=bond_return,
        cash_return=cash_return,
        real_estate_return=real_estate_return,
    )

    husband = make_person()
    wife = make_person()
    wife_portfolio = make_portfolio()
    expenses = DynamicExpenses()

    sim_config = make_config(
        dividend_yield=dividend_yield,
    )

    return simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        num_sims=1,
    )


def test_zero_return_preserves_all_four_equity_buckets(monkeypatch):
    husband_portfolio = make_portfolio(
        equity_pre=10_000.0,
        equity_post=20_000.0,
        equity_roth=30_000.0,
        hsa_equity=40_000.0,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        equity_return=0.0,
        dividend_yield=0.0,
    )

    assert results["pre_tax_assets"][0, 0] == pytest.approx(10_000.0)
    assert results["post_tax_assets"][0, 0] == pytest.approx(20_000.0)
    assert results["roth_assets"][0, 0] == pytest.approx(30_000.0)
    assert results["hsa_assets"][0, 0] == pytest.approx(40_000.0)

    assert results["pre_tax_assets"][0, 1] == pytest.approx(10_000.0)
    assert results["post_tax_assets"][0, 1] == pytest.approx(20_000.0)
    assert results["roth_assets"][0, 1] == pytest.approx(30_000.0)
    assert results["hsa_assets"][0, 1] == pytest.approx(40_000.0)

    assert results["total_assets"][0, 0] == pytest.approx(100_000.0)
    assert results["total_assets"][0, 1] == pytest.approx(100_000.0)

    assert results["gross_income"][0, 1] == pytest.approx(0.0)
    assert results["qualified_dividends"][0, 1] == pytest.approx(0.0)


def test_pre_tax_equity_receives_total_return(monkeypatch):
    husband_portfolio = make_portfolio(
        equity_pre=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        equity_return=EQUITY_TOTAL_RETURN,
        dividend_yield=EQUITY_DIVIDEND_YIELD,
    )

    assert results["pre_tax_assets"][0, 0] == pytest.approx(
        STARTING_BALANCE
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        STARTING_BALANCE * (1.0 + EQUITY_TOTAL_RETURN)
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["roth_assets"][0, 1] == pytest.approx(0.0)
    assert results["hsa_assets"][0, 1] == pytest.approx(0.0)

    assert results["qualified_dividends"][0, 1] == pytest.approx(0.0)
    assert results["gross_income"][0, 1] == pytest.approx(0.0)


def test_roth_equity_receives_total_return(monkeypatch):
    husband_portfolio = make_portfolio(
        equity_roth=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        equity_return=EQUITY_TOTAL_RETURN,
        dividend_yield=EQUITY_DIVIDEND_YIELD,
    )

    assert results["roth_assets"][0, 0] == pytest.approx(
        STARTING_BALANCE
    )
    assert results["roth_assets"][0, 1] == pytest.approx(
        STARTING_BALANCE * (1.0 + EQUITY_TOTAL_RETURN)
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["post_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["hsa_assets"][0, 1] == pytest.approx(0.0)

    assert results["qualified_dividends"][0, 1] == pytest.approx(0.0)
    assert results["gross_income"][0, 1] == pytest.approx(0.0)


def test_hsa_equity_receives_total_return(monkeypatch):
    husband_portfolio = make_portfolio(
        hsa_equity=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        equity_return=EQUITY_TOTAL_RETURN,
        dividend_yield=EQUITY_DIVIDEND_YIELD,
    )

    assert results["hsa_assets"][0, 0] == pytest.approx(
        STARTING_BALANCE
    )
    assert results["hsa_assets"][0, 1] == pytest.approx(
        STARTING_BALANCE * (1.0 + EQUITY_TOTAL_RETURN)
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["post_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["roth_assets"][0, 1] == pytest.approx(0.0)

    assert results["qualified_dividends"][0, 1] == pytest.approx(0.0)
    assert results["gross_income"][0, 1] == pytest.approx(0.0)


def test_taxable_equity_reports_qualified_dividend_income(monkeypatch):
    husband_portfolio = make_portfolio(
        equity_post=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        equity_return=EQUITY_TOTAL_RETURN,
        dividend_yield=EQUITY_DIVIDEND_YIELD,
    )

    expected_dividends = (
        STARTING_BALANCE * EQUITY_DIVIDEND_YIELD
    )

    assert results["qualified_dividends"][0, 1] == pytest.approx(
        expected_dividends
    )
    assert (
        results["breakdown_by_class"]["qualified_dividends"][0, 1]
        == pytest.approx(expected_dividends)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        expected_dividends
    )
    assert results["net_income"][0, 1] == pytest.approx(
        expected_dividends
    )

    assert results["bond_interest"][0, 1] == pytest.approx(0.0)
    assert results["cash_interest"][0, 1] == pytest.approx(0.0)


def test_taxable_equity_uses_price_return_after_cash_deposit(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        equity_post=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        equity_return=EQUITY_TOTAL_RETURN,
        dividend_yield=EQUITY_DIVIDEND_YIELD,
    )

    expected_dividends = (
        STARTING_BALANCE * EQUITY_DIVIDEND_YIELD
    )

    expected_balance_before_return = (
        STARTING_BALANCE + expected_dividends
    )

    expected_ending_balance = (
        expected_balance_before_return
        * (1.0 + EQUITY_PRICE_RETURN)
    )

    assert results["post_tax_assets"][0, 0] == pytest.approx(
        STARTING_BALANCE
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        expected_ending_balance
    )

    assert expected_ending_balance == pytest.approx(108_120.0)


def test_taxable_equity_current_order_adds_120_of_same_year_growth(
    monkeypatch,
):
    """
    Document the current ordering effect.

    The $2,000 dividend is deposited into taxable equity before the 6%
    equity price return is applied. That deposit therefore earns $120
    during the same simulated year.
    """
    husband_portfolio = make_portfolio(
        equity_post=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        equity_return=EQUITY_TOTAL_RETURN,
        dividend_yield=EQUITY_DIVIDEND_YIELD,
    )

    ending_balance = results["post_tax_assets"][0, 1]
    reported_dividends = results["qualified_dividends"][0, 1]

    original_equity_price_gain = (
        STARTING_BALANCE * EQUITY_PRICE_RETURN
    )
    same_year_growth_on_dividend = (
        reported_dividends * EQUITY_PRICE_RETURN
    )

    expected_total_gain = (
        reported_dividends
        + original_equity_price_gain
        + same_year_growth_on_dividend
    )

    assert ending_balance - STARTING_BALANCE == pytest.approx(
        expected_total_gain
    )

    assert original_equity_price_gain == pytest.approx(6_000.0)
    assert reported_dividends == pytest.approx(2_000.0)
    assert same_year_growth_on_dividend == pytest.approx(120.0)
    assert expected_total_gain == pytest.approx(8_120.0)


def test_pre_tax_bond_receives_positive_total_return(monkeypatch):
    husband_portfolio = make_portfolio(
        bond_pre=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        bond_return=POSITIVE_BOND_RETURN,
    )

    expected_balance = (
        STARTING_BALANCE * (1.0 + POSITIVE_BOND_RETURN)
    )

    assert results["pre_tax_assets"][0, 0] == pytest.approx(
        STARTING_BALANCE
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        expected_balance
    )
    assert results["bonds"][0, 1] == pytest.approx(
        expected_balance
    )

    assert results["bond_interest"][0, 1] == pytest.approx(0.0)
    assert results["gross_income"][0, 1] == pytest.approx(0.0)


def test_roth_bond_receives_positive_total_return(monkeypatch):
    husband_portfolio = make_portfolio(
        bond_roth=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        bond_return=POSITIVE_BOND_RETURN,
    )

    expected_balance = (
        STARTING_BALANCE * (1.0 + POSITIVE_BOND_RETURN)
    )

    assert results["roth_assets"][0, 0] == pytest.approx(
        STARTING_BALANCE
    )
    assert results["roth_assets"][0, 1] == pytest.approx(
        expected_balance
    )
    assert results["bonds"][0, 1] == pytest.approx(
        expected_balance
    )

    assert results["bond_interest"][0, 1] == pytest.approx(0.0)
    assert results["gross_income"][0, 1] == pytest.approx(0.0)


def test_hsa_bond_receives_positive_total_return(monkeypatch):
    husband_portfolio = make_portfolio(
        hsa_bond=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        bond_return=POSITIVE_BOND_RETURN,
    )

    expected_balance = (
        STARTING_BALANCE * (1.0 + POSITIVE_BOND_RETURN)
    )

    assert results["hsa_assets"][0, 0] == pytest.approx(
        STARTING_BALANCE
    )
    assert results["hsa_assets"][0, 1] == pytest.approx(
        expected_balance
    )
    assert results["bonds"][0, 1] == pytest.approx(
        expected_balance
    )

    assert results["bond_interest"][0, 1] == pytest.approx(0.0)
    assert results["gross_income"][0, 1] == pytest.approx(0.0)


def test_taxable_positive_bond_return_becomes_income(monkeypatch):
    husband_portfolio = make_portfolio(
        bond_post=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        bond_return=POSITIVE_BOND_RETURN,
    )

    expected_interest = (
        STARTING_BALANCE * POSITIVE_BOND_RETURN
    )

    assert results["bond_interest"][0, 1] == pytest.approx(
        expected_interest
    )
    assert (
        results["breakdown_by_class"]["bond_interest"][0, 1]
        == pytest.approx(expected_interest)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        expected_interest
    )
    assert results["net_income"][0, 1] == pytest.approx(
        expected_interest
    )

    assert results["cash_interest"][0, 1] == pytest.approx(0.0)
    assert results["qualified_dividends"][0, 1] == pytest.approx(0.0)


def test_taxable_positive_bond_return_is_not_applied_to_bond_balance(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        bond_post=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        bond_return=POSITIVE_BOND_RETURN,
    )

    expected_interest = (
        STARTING_BALANCE * POSITIVE_BOND_RETURN
    )

    assert results["bonds"][0, 0] == pytest.approx(
        STARTING_BALANCE
    )
    assert results["bonds"][0, 1] == pytest.approx(
        STARTING_BALANCE
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        STARTING_BALANCE + expected_interest
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        STARTING_BALANCE + expected_interest
    )


def test_taxable_positive_bond_income_is_deposited_into_equity(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        bond_post=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        bond_return=POSITIVE_BOND_RETURN,
    )

    expected_interest = (
        STARTING_BALANCE * POSITIVE_BOND_RETURN
    )

    assert results["bonds"][0, 1] == pytest.approx(
        STARTING_BALANCE
    )
    assert (
        results["post_tax_assets"][0, 1]
        - results["bonds"][0, 1]
        == pytest.approx(expected_interest)
    )


def test_taxable_negative_bond_return_reduces_balance(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        bond_post=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        bond_return=NEGATIVE_BOND_RETURN,
    )

    expected_ending_balance = (
        STARTING_BALANCE * (1.0 + NEGATIVE_BOND_RETURN)
    )

    assert results["bonds"][0, 1] == pytest.approx(
        expected_ending_balance
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        expected_ending_balance
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        expected_ending_balance
    )


def test_taxable_negative_bond_return_does_not_create_negative_income(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        bond_post=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        bond_return=NEGATIVE_BOND_RETURN,
    )

    assert results["bond_interest"][0, 1] == pytest.approx(0.0)
    assert (
        results["breakdown_by_class"]["bond_interest"][0, 1]
        == pytest.approx(0.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(0.0)
    assert results["net_income"][0, 1] == pytest.approx(0.0)


def test_pre_tax_cash_receives_positive_total_return(monkeypatch):
    husband_portfolio = make_portfolio(
        cash_pre=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        cash_return=POSITIVE_CASH_RETURN,
    )

    expected_balance = (
        STARTING_BALANCE * (1.0 + POSITIVE_CASH_RETURN)
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        expected_balance
    )
    assert results["cash"][0, 1] == pytest.approx(
        expected_balance
    )

    assert results["cash_interest"][0, 1] == pytest.approx(0.0)
    assert results["gross_income"][0, 1] == pytest.approx(0.0)


def test_roth_cash_receives_positive_total_return(monkeypatch):
    husband_portfolio = make_portfolio(
        cash_roth=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        cash_return=POSITIVE_CASH_RETURN,
    )

    expected_balance = (
        STARTING_BALANCE * (1.0 + POSITIVE_CASH_RETURN)
    )

    assert results["roth_assets"][0, 1] == pytest.approx(
        expected_balance
    )
    assert results["cash"][0, 1] == pytest.approx(
        expected_balance
    )

    assert results["cash_interest"][0, 1] == pytest.approx(0.0)
    assert results["gross_income"][0, 1] == pytest.approx(0.0)


def test_hsa_cash_receives_positive_total_return(monkeypatch):
    husband_portfolio = make_portfolio(
        hsa_cash=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        cash_return=POSITIVE_CASH_RETURN,
    )

    expected_balance = (
        STARTING_BALANCE * (1.0 + POSITIVE_CASH_RETURN)
    )

    assert results["hsa_assets"][0, 1] == pytest.approx(
        expected_balance
    )
    assert results["cash"][0, 1] == pytest.approx(
        expected_balance
    )

    assert results["cash_interest"][0, 1] == pytest.approx(0.0)
    assert results["gross_income"][0, 1] == pytest.approx(0.0)


def test_taxable_positive_cash_return_becomes_income(monkeypatch):
    husband_portfolio = make_portfolio(
        cash_post=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        cash_return=POSITIVE_CASH_RETURN,
    )

    expected_interest = (
        STARTING_BALANCE * POSITIVE_CASH_RETURN
    )

    assert results["cash_interest"][0, 1] == pytest.approx(
        expected_interest
    )
    assert (
        results["breakdown_by_class"]["cash_interest"][0, 1]
        == pytest.approx(expected_interest)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        expected_interest
    )
    assert results["net_income"][0, 1] == pytest.approx(
        expected_interest
    )

    assert results["bond_interest"][0, 1] == pytest.approx(0.0)
    assert results["qualified_dividends"][0, 1] == pytest.approx(0.0)


def test_taxable_positive_cash_return_is_not_applied_to_cash_balance(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        cash_post=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        cash_return=POSITIVE_CASH_RETURN,
    )

    expected_interest = (
        STARTING_BALANCE * POSITIVE_CASH_RETURN
    )

    assert results["cash"][0, 0] == pytest.approx(
        STARTING_BALANCE
    )
    assert results["cash"][0, 1] == pytest.approx(
        STARTING_BALANCE
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        STARTING_BALANCE + expected_interest
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        STARTING_BALANCE + expected_interest
    )


def test_taxable_positive_cash_income_is_deposited_into_equity(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        cash_post=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        cash_return=POSITIVE_CASH_RETURN,
    )

    expected_interest = (
        STARTING_BALANCE * POSITIVE_CASH_RETURN
    )

    assert results["cash"][0, 1] == pytest.approx(
        STARTING_BALANCE
    )
    assert (
        results["post_tax_assets"][0, 1]
        - results["cash"][0, 1]
        == pytest.approx(expected_interest)
    )


def test_taxable_negative_cash_return_reduces_balance(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        cash_post=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        cash_return=NEGATIVE_CASH_RETURN,
    )

    expected_ending_balance = (
        STARTING_BALANCE * (1.0 + NEGATIVE_CASH_RETURN)
    )

    assert results["cash"][0, 1] == pytest.approx(
        expected_ending_balance
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        expected_ending_balance
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        expected_ending_balance
    )


def test_taxable_negative_cash_return_does_not_create_negative_income(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        cash_post=STARTING_BALANCE,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        cash_return=NEGATIVE_CASH_RETURN,
    )

    assert results["cash_interest"][0, 1] == pytest.approx(0.0)
    assert (
        results["breakdown_by_class"]["cash_interest"][0, 1]
        == pytest.approx(0.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(0.0)
    assert results["net_income"][0, 1] == pytest.approx(0.0)