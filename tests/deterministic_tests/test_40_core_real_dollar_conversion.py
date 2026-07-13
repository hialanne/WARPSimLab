import numpy as np
import pytest

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.dataClasses.person import Person
from src.warpsimlab.dataClasses.portfolio import Portfolio
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.engines import withdrawalEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios
from src.warpsimlab.sim.simulationObject import Simulation


INFLATION_RATE = 0.10


@pytest.fixture(autouse=True)
def install_test_rmd_table(monkeypatch):
    monkeypatch.setattr(
        withdrawalEngine,
        "RMD_START_AGE",
        73,
        raising=False,
    )
    monkeypatch.setattr(
        withdrawalEngine,
        "UNIFORM_LIFETIME_TABLE",
        {
            73: 25.0,
            74: 24.0,
        },
        raising=False,
    )


def make_person(
    *,
    age=40,
    retire_age=65,
    income=0.0,
    annual_401k_contribution=0.0,
    annual_employer_match=0.0,
):
    return Person(
        age=age,
        retire_age=retire_age,
        income=income,
        ss=0.0,
        ss_age=99,
        pension=0.0,
        pension_age=99,
        annuity=0.0,
        annuity_age=99,
        annual_401k_contribution=annual_401k_contribution,
        annual_employer_match=annual_employer_match,
        pension_inflation_adjustment_pct=0.0,
    )


def make_portfolio(
    *,
    equity_pre=0.0,
    equity_post=0.0,
    equity_roth=0.0,
    hsa_equity=0.0,
):
    return Portfolio(
        equity_pre=equity_pre,
        equity_post=equity_post,
        bond_pre=0.0,
        bond_post=0.0,
        cash_pre=0.0,
        cash_post=0.0,
        real_estate=0.0,
        equity_roth=equity_roth,
        bond_roth=0.0,
        cash_roth=0.0,
        hsa_cash=0.0,
        hsa_equity=hsa_equity,
        hsa_bond=0.0,
    )


def make_config(
    *,
    plot_mode,
    years_to_simulate=2,
    always_use_expense_mode=True,
    include_rmd=False,
    retirement_withdraw_mode="Off",
    retirement_withdraw_dollars=0.0,
    use_fund_expenses=False,
    fund_expense=0.0,
    dividend_yield=0.0,
):
    return Simulation(
        start_year=2026,
        years_to_simulate=years_to_simulate,
        inflation_rate=INFLATION_RATE,
        num_sims=1,
        fund_expense=fund_expense,
        use_fund_expenses=use_fund_expenses,
        plot_mode=plot_mode,
        subplot_mode="baseline",
        include_rmd=include_rmd,
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
        retirement_withdraw_mode=retirement_withdraw_mode,
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=retirement_withdraw_dollars,
        always_use_expense_mode=always_use_expense_mode,
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
    years_to_simulate,
    equity_return=0.0,
):
    def fake_generate_market_path(
        sim_config,
        requested_years,
        sim_index=None,
    ):
        assert requested_years == years_to_simulate

        equity = np.zeros(requested_years + 1, dtype=float)
        equity[1:] = equity_return

        zeros = np.zeros(requested_years + 1, dtype=float)

        return {
            "eq": equity,
            "bd": zeros.copy(),
            "cs": zeros.copy(),
            "re": zeros.copy(),
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )


def make_expenses(
    *,
    amount,
    start_year=2027,
):
    expenses = DynamicExpenses()
    expenses.add_expense(
        start_year=start_year,
        cost=amount,
        end_year=None,
    )
    return expenses


def discount_factors(years_to_simulate):
    return np.array(
        [
            (1.0 + INFLATION_RATE) ** year
            for year in range(years_to_simulate + 1)
        ],
        dtype=float,
    )


def assert_result_is_deflated(
    raw_results,
    real_results,
    key,
    factors,
):
    assert real_results[key][0] == pytest.approx(
        raw_results[key][0] / factors
    )


def assert_breakdown_is_deflated(
    raw_results,
    real_results,
    key,
    factors,
):
    assert real_results["breakdown_by_class"][key][0] == (
        pytest.approx(
            raw_results["breakdown_by_class"][key][0]
            / factors
        )
    )


def run_expense_mode(
    monkeypatch,
    *,
    plot_mode,
):
    years_to_simulate = 2

    install_market_path(
        monkeypatch,
        years_to_simulate=years_to_simulate,
        equity_return=0.08,
    )

    return simulate_yearly_portfolios(
        make_portfolio(
            equity_post=100_000.0,
        ),
        make_portfolio(),
        make_person(
            income=80_000.0,
            annual_401k_contribution=8_000.0,
            annual_employer_match=4_000.0,
        ),
        make_person(),
        make_expenses(
            amount=30_000.0,
        ),
        make_config(
            plot_mode=plot_mode,
            years_to_simulate=years_to_simulate,
            always_use_expense_mode=True,
            use_fund_expenses=True,
            fund_expense=0.01,
            dividend_yield=0.02,
        ),
        num_sims=1,
    )


def run_retirement_mode(
    monkeypatch,
    *,
    plot_mode,
):
    years_to_simulate = 1

    install_market_path(
        monkeypatch,
        years_to_simulate=years_to_simulate,
    )

    return simulate_yearly_portfolios(
        make_portfolio(
            equity_pre=20_000.0,
            equity_post=10_000.0,
            equity_roth=30_000.0,
            hsa_equity=40_000.0,
        ),
        make_portfolio(),
        make_person(
            age=72,
            retire_age=65,
        ),
        make_person(),
        DynamicExpenses(),
        make_config(
            plot_mode=plot_mode,
            years_to_simulate=years_to_simulate,
            always_use_expense_mode=False,
            include_rmd=True,
            retirement_withdraw_mode="Fixed Dollar Amount",
            retirement_withdraw_dollars=100_000.0,
        ),
        num_sims=1,
    )


def test_expense_mode_monetary_results_are_deflated(
    monkeypatch,
):
    raw_results = run_expense_mode(
        monkeypatch,
        plot_mode="raw",
    )
    real_results = run_expense_mode(
        monkeypatch,
        plot_mode="real",
    )

    factors = discount_factors(2)

    result_keys = [
        "total_assets",
        "pre_tax_assets",
        "post_tax_assets",
        "roth_assets",
        "hsa_assets",
        "cash",
        "bonds",
        "real_estate",
        "gross_income",
        "net_income",
        "net_profit",
        "expense_amt",
        "uncovered_expense",
        "ira_401k",
        "taxes",
        "fund_expenses",
        "qualified_dividends",
        "bond_interest",
        "cash_interest",
        "net_income_husband",
        "net_income_wife",
        "emergency_pre_tax_used",
        "federal_ordinary_tax",
        "federal_qualified_dividend_tax",
        "state_income_tax",
        "payroll_tax",
        "social_security_payroll_tax",
        "medicare_tax",
        "additional_medicare_tax",
    ]

    for key in result_keys:
        assert_result_is_deflated(
            raw_results,
            real_results,
            key,
            factors,
        )


def test_expense_mode_income_breakdown_is_deflated(
    monkeypatch,
):
    raw_results = run_expense_mode(
        monkeypatch,
        plot_mode="raw",
    )
    real_results = run_expense_mode(
        monkeypatch,
        plot_mode="real",
    )

    factors = discount_factors(2)

    breakdown_keys = [
        "work",
        "ss",
        "pension",
        "annuity",
        "rmd",
        "withdrawal",
        "special_income",
        "qualified_dividends",
        "bond_interest",
        "cash_interest",
    ]

    for key in breakdown_keys:
        assert_breakdown_is_deflated(
            raw_results,
            real_results,
            key,
            factors,
        )


def test_retirement_mode_monetary_results_are_deflated(
    monkeypatch,
):
    raw_results = run_retirement_mode(
        monkeypatch,
        plot_mode="raw",
    )
    real_results = run_retirement_mode(
        monkeypatch,
        plot_mode="real",
    )

    factors = discount_factors(1)

    result_keys = [
        "total_assets",
        "pre_tax_assets",
        "post_tax_assets",
        "roth_assets",
        "hsa_assets",
        "gross_income",
        "net_income",
        "roth_withdrawals",
        "hsa_withdrawals",
        "net_income_husband",
        "net_income_wife",
    ]

    for key in result_keys:
        assert_result_is_deflated(
            raw_results,
            real_results,
            key,
            factors,
        )


def test_retirement_withdrawal_breakdown_is_deflated(
    monkeypatch,
):
    raw_results = run_retirement_mode(
        monkeypatch,
        plot_mode="raw",
    )
    real_results = run_retirement_mode(
        monkeypatch,
        plot_mode="real",
    )

    factors = discount_factors(1)

    assert_breakdown_is_deflated(
        raw_results,
        real_results,
        "rmd",
        factors,
    )
    assert_breakdown_is_deflated(
        raw_results,
        real_results,
        "withdrawal",
        factors,
    )


def test_real_mode_does_not_modify_nominal_raw_run(
    monkeypatch,
):
    first_raw = run_expense_mode(
        monkeypatch,
        plot_mode="raw",
    )
    run_expense_mode(
        monkeypatch,
        plot_mode="real",
    )
    second_raw = run_expense_mode(
        monkeypatch,
        plot_mode="raw",
    )

    keys = [
        "total_assets",
        "pre_tax_assets",
        "post_tax_assets",
        "gross_income",
        "net_income",
        "expense_amt",
        "ira_401k",
        "fund_expenses",
        "qualified_dividends",
    ]

    for key in keys:
        assert second_raw[key] == pytest.approx(
            first_raw[key]
        )