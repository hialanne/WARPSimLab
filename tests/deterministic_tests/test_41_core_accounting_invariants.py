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
    retire_age=65,
    income=0.0,
    ss=0.0,
    ss_age=99,
    pension=0.0,
    pension_age=99,
    annuity=0.0,
    annuity_age=99,
    annual_401k_contribution=0.0,
    annual_employer_match=0.0,
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
        annual_401k_contribution=annual_401k_contribution,
        annual_employer_match=annual_employer_match,
        pension_inflation_adjustment_pct=0.0,
    )


def make_portfolio(
    *,
    equity_pre=0.0,
    bond_pre=0.0,
    cash_pre=0.0,
    equity_post=0.0,
    bond_post=0.0,
    cash_post=0.0,
    equity_roth=0.0,
    bond_roth=0.0,
    cash_roth=0.0,
    hsa_equity=0.0,
    hsa_bond=0.0,
    hsa_cash=0.0,
    real_estate=0.0,
):
    return Portfolio(
        equity_pre=equity_pre,
        equity_post=equity_post,
        bond_pre=bond_pre,
        bond_post=bond_post,
        cash_pre=cash_pre,
        cash_post=cash_post,
        real_estate=real_estate,
        equity_roth=equity_roth,
        bond_roth=bond_roth,
        cash_roth=cash_roth,
        hsa_cash=hsa_cash,
        hsa_equity=hsa_equity,
        hsa_bond=hsa_bond,
    )


def make_config(
    *,
    years_to_simulate=3,
    num_sims=1,
    second_person_enabled=False,
    include_realestate=False,
    calculate_income_taxes=False,
    calculate_payroll_taxes=False,
    calculate_state_taxes=False,
    always_use_expense_mode=True,
    retirement_withdraw_mode="Off",
    retirement_withdraw_dollars=0.0,
    use_fund_expenses=False,
    fund_expense=0.0,
):
    return Simulation(
        start_year=2026,
        years_to_simulate=years_to_simulate,
        inflation_rate=0.0,
        num_sims=num_sims,
        fund_expense=fund_expense,
        use_fund_expenses=use_fund_expenses,
        plot_mode="raw",
        subplot_mode="baseline",
        include_rmd=False,
        calculate_income_taxes=calculate_income_taxes,
        calculate_payroll_taxes=calculate_payroll_taxes,
        tax_filing_status="Single",
        calculate_state_taxes=calculate_state_taxes,
        state_of_residence="CO",
        second_person_enabled=second_person_enabled,
        eq_mean=0.0,
        bd_mean=0.0,
        cs_mean=0.0,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        post_tax_equity_dividend_yield=0.02,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        sim_type="portfolio_sim",
        sim_initial_allocation_mode="dont-rebalance",
        rebalance_every_year=False,
        include_realestate=include_realestate,
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
    equity_return=0.0,
    bond_return=0.0,
    cash_return=0.0,
    real_estate_return=0.0,
):
    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        equity = np.zeros(years_to_simulate + 1, dtype=float)
        bonds = np.zeros(years_to_simulate + 1, dtype=float)
        cash = np.zeros(years_to_simulate + 1, dtype=float)
        real_estate = np.zeros(
            years_to_simulate + 1,
            dtype=float,
        )

        equity[1:] = equity_return
        bonds[1:] = bond_return
        cash[1:] = cash_return
        real_estate[1:] = real_estate_return

        return {
            "eq": equity,
            "bd": bonds,
            "cs": cash,
            "re": real_estate,
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )


def make_expenses(
    *,
    annual_amount=0.0,
):
    expenses = DynamicExpenses()

    if annual_amount > 0.0:
        expenses.add_expense(
            start_year=2027,
            cost=annual_amount,
            end_year=None,
        )

    return expenses


def run_simulation(
    monkeypatch,
    *,
    husband_portfolio,
    husband=None,
    wife_portfolio=None,
    wife=None,
    expenses=None,
    years_to_simulate=3,
    num_sims=1,
    second_person_enabled=False,
    include_realestate=False,
    calculate_income_taxes=False,
    calculate_payroll_taxes=False,
    calculate_state_taxes=False,
    always_use_expense_mode=True,
    retirement_withdraw_mode="Off",
    retirement_withdraw_dollars=0.0,
    use_fund_expenses=False,
    fund_expense=0.0,
    equity_return=0.0,
    bond_return=0.0,
    cash_return=0.0,
    real_estate_return=0.0,
):
    install_market_path(
        monkeypatch,
        equity_return=equity_return,
        bond_return=bond_return,
        cash_return=cash_return,
        real_estate_return=real_estate_return,
    )

    if husband is None:
        husband = make_person()

    if wife is None:
        wife = make_person()

    if wife_portfolio is None:
        wife_portfolio = make_portfolio()

    if expenses is None:
        expenses = make_expenses()

    config = make_config(
        years_to_simulate=years_to_simulate,
        num_sims=num_sims,
        second_person_enabled=second_person_enabled,
        include_realestate=include_realestate,
        calculate_income_taxes=calculate_income_taxes,
        calculate_payroll_taxes=calculate_payroll_taxes,
        calculate_state_taxes=calculate_state_taxes,
        always_use_expense_mode=always_use_expense_mode,
        retirement_withdraw_mode=retirement_withdraw_mode,
        retirement_withdraw_dollars=retirement_withdraw_dollars,
        use_fund_expenses=use_fund_expenses,
        fund_expense=fund_expense,
    )

    return simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        config,
        num_sims=num_sims,
    )


def assert_all_nonnegative(values):
    assert np.all(values >= -1e-8)


def test_total_assets_reconcile_to_account_buckets_and_real_estate(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=50_000.0,
            bond_pre=20_000.0,
            cash_pre=10_000.0,
            equity_post=40_000.0,
            bond_post=15_000.0,
            cash_post=5_000.0,
            equity_roth=30_000.0,
            bond_roth=10_000.0,
            cash_roth=5_000.0,
            hsa_equity=20_000.0,
            hsa_bond=8_000.0,
            hsa_cash=2_000.0,
            real_estate=100_000.0,
        ),
        include_realestate=True,
        equity_return=0.08,
        bond_return=0.03,
        cash_return=0.01,
        real_estate_return=0.04,
        use_fund_expenses=True,
        fund_expense=0.005,
    )

    reconciled_total = (
        results["pre_tax_assets"]
        + results["post_tax_assets"]
        + results["roth_assets"]
        + results["hsa_assets"]
        + results["real_estate"]
    )

    assert results["total_assets"] == pytest.approx(
        reconciled_total
    )


def test_equity_bond_and_cash_totals_reconcile_to_financial_assets(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=50_000.0,
            bond_pre=20_000.0,
            cash_pre=10_000.0,
            equity_post=40_000.0,
            bond_post=15_000.0,
            cash_post=5_000.0,
            equity_roth=30_000.0,
            bond_roth=10_000.0,
            cash_roth=5_000.0,
            hsa_equity=20_000.0,
            hsa_bond=8_000.0,
            hsa_cash=2_000.0,
        ),
        equity_return=0.08,
        bond_return=-0.03,
        cash_return=0.01,
    )

    financial_assets = (
        results["pre_tax_assets"]
        + results["post_tax_assets"]
        + results["roth_assets"]
        + results["hsa_assets"]
    )

    equity_assets = (
        financial_assets
        - results["bonds"]
        - results["cash"]
    )

    assert_all_nonnegative(equity_assets)
    assert_all_nonnegative(results["bonds"])
    assert_all_nonnegative(results["cash"])

    assert (
        equity_assets
        + results["bonds"]
        + results["cash"]
        == pytest.approx(financial_assets)
    )


def test_all_asset_and_shortfall_results_remain_nonnegative(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=10_000.0,
            equity_post=10_000.0,
            equity_roth=10_000.0,
            hsa_equity=10_000.0,
            real_estate=10_000.0,
        ),
        expenses=make_expenses(
            annual_amount=100_000.0,
        ),
        include_realestate=True,
        equity_return=-0.50,
        real_estate_return=-0.25,
    )

    nonnegative_keys = [
        "total_assets",
        "pre_tax_assets",
        "post_tax_assets",
        "roth_assets",
        "hsa_assets",
        "cash",
        "bonds",
        "real_estate",
        "taxes",
        "expense_amt",
        "uncovered_expense",
        "emergency_pre_tax_used",
        "roth_withdrawals",
        "hsa_withdrawals",
        "fund_expenses",
        "qualified_dividends",
        "bond_interest",
        "cash_interest",
    ]

    for key in nonnegative_keys:
        assert_all_nonnegative(results[key])


def test_tax_components_reconcile_to_total_tax(monkeypatch):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(),
        husband=make_person(
            income=100_000.0,
        ),
        calculate_income_taxes=True,
        calculate_payroll_taxes=True,
        calculate_state_taxes=True,
    )

    expected_total_tax = (
        results["federal_ordinary_tax"]
        + results["federal_qualified_dividend_tax"]
        + results["state_income_tax"]
        + results["payroll_tax"]
    )

    expected_payroll_tax = (
        results["social_security_payroll_tax"]
        + results["medicare_tax"]
        + results["additional_medicare_tax"]
    )

    assert results["taxes"] == pytest.approx(
        expected_total_tax
    )
    assert results["payroll_tax"] == pytest.approx(
        expected_payroll_tax
    )


def test_income_components_reconcile_without_contributions_or_withdrawals(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
            bond_post=50_000.0,
            cash_post=20_000.0,
        ),
        husband=make_person(
            age=69,
            retire_age=75,
            income=40_000.0,
            ss=20_000.0,
            ss_age=70,
            pension=15_000.0,
            pension_age=70,
            annuity=5_000.0,
            annuity_age=70,
        ),
        equity_return=0.08,
        bond_return=0.04,
        cash_return=0.02,
    )

    breakdown = results["breakdown_by_class"]

    reconstructed_income = (
        breakdown["work"]
        + breakdown["ss"]
        + breakdown["pension"]
        + breakdown["annuity"]
        + breakdown["rmd"]
        + breakdown["withdrawal"]
        + breakdown["special_income"]
        + breakdown["qualified_dividends"]
        + breakdown["bond_interest"]
        + breakdown["cash_interest"]
    )

    assert results["gross_income"] == pytest.approx(
        reconstructed_income
    )


def test_withdrawal_only_gross_income_matches_actual_withdrawal(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=20_000.0,
            equity_pre=30_000.0,
            equity_roth=40_000.0,
            hsa_equity=50_000.0,
        ),
        husband=make_person(
            age=70,
            retire_age=65,
        ),
        years_to_simulate=2,
        always_use_expense_mode=False,
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_dollars=60_000.0,
    )

    actual_withdrawal = (
        results["breakdown_by_class"]["withdrawal"]
    )

    expected_gross_income = (
        actual_withdrawal
        + results["breakdown_by_class"]["qualified_dividends"]
    )

    assert results["gross_income"] == pytest.approx(
        expected_gross_income
    )

    assert results["roth_withdrawals"][0, 1] == pytest.approx(
        10_000.0
    )

    assert results["roth_withdrawals"][0] == pytest.approx(
        [
            0.0,
            10_000.0,
            30_000.0,
        ]
    )

    assert results["hsa_withdrawals"][0] == pytest.approx(
        [
            0.0,
            0.0,
            30_000.0,
        ]
    )

    assert (
        results["breakdown_by_class"]["qualified_dividends"][0, 1]
        == pytest.approx(400.0)
    )

def test_couple_person_net_income_reconciles_to_household_net_income(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(),
        wife_portfolio=make_portfolio(),
        husband=make_person(
            income=60_000.0,
        ),
        wife=make_person(
            income=40_000.0,
        ),
        second_person_enabled=True,
        calculate_income_taxes=True,
        calculate_payroll_taxes=True,
    )

    person_total = (
        results["net_income_husband"]
        + results["net_income_wife"]
    )

    assert person_total == pytest.approx(
        results["net_income"]
    )


def test_result_arrays_have_expected_shape(monkeypatch):
    years_to_simulate = 4
    num_sims = 3

    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        years_to_simulate=years_to_simulate,
        num_sims=num_sims,
        equity_return=0.05,
    )

    expected_shape = (
        num_sims,
        years_to_simulate + 1,
    )

    array_keys = [
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
        "roth_withdrawals",
        "hsa_withdrawals",
    ]

    for key in array_keys:
        assert results[key].shape == expected_shape

    for values in results["breakdown_by_class"].values():
        assert values.shape == expected_shape


def test_identical_deterministic_simulations_produce_identical_rows(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=50_000.0,
            bond_pre=30_000.0,
            cash_pre=20_000.0,
        ),
        years_to_simulate=3,
        num_sims=3,
        equity_return=0.08,
        bond_return=0.03,
        cash_return=0.01,
    )

    keys = [
        "total_assets",
        "pre_tax_assets",
        "post_tax_assets",
        "cash",
        "bonds",
        "gross_income",
        "net_income",
    ]

    for key in keys:
        assert results[key][1] == pytest.approx(
            results[key][0]
        )
        assert results[key][2] == pytest.approx(
            results[key][0]
        )