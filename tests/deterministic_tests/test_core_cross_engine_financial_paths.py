import numpy as np
import pytest

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.dataClasses.person import Person
from src.warpsimlab.dataClasses.portfolio import Portfolio
from src.warpsimlab.dataClasses.portfolioState import PortfolioState
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.engines import portfolioEngine
from src.warpsimlab.sim.engines import rothEngine
from src.warpsimlab.sim.engines import taxEngine
from src.warpsimlab.sim.engines import withdrawalEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios
from src.warpsimlab.sim.simulationObject import Simulation


def make_person(*, age=40, retire_age=65, income=0.0):
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
        annual_401k_contribution=0.0,
        annual_employer_match=0.0,
        pension_inflation_adjustment_pct=0.0,
    )


def make_portfolio(
    *,
    pre_tax=0.0,
    post_tax=0.0,
    roth=0.0,
    hsa_equity=0.0,
    hsa_bond=0.0,
    hsa_cash=0.0,
):
    return Portfolio(
        equity_pre=pre_tax,
        equity_post=post_tax,
        bond_pre=0.0,
        bond_post=0.0,
        cash_pre=0.0,
        cash_post=0.0,
        real_estate=0.0,
        equity_roth=roth,
        bond_roth=0.0,
        cash_roth=0.0,
        hsa_equity=hsa_equity,
        hsa_bond=hsa_bond,
        hsa_cash=hsa_cash,
    )


def make_roth_flow(*, flow_type, amount, owner="husband"):
    return {
        "enabled": True,
        "type": flow_type,
        "owner": owner,
        "amount": float(amount),
        "start_age": 0,
        "end_age": 120,
        "inflation_adjustment_pct": 0.0,
    }


def make_expenses(amount):
    expenses = DynamicExpenses()
    if amount > 0.0:
        expenses.add_expense(
            start_year=2027,
            end_year=2027,
            cost=float(amount),
        )
    return expenses


def make_config(
    *,
    second_person_enabled=False,
    include_rmd=False,
    calculate_income_taxes=False,
    calculate_payroll_taxes=False,
    calculate_state_taxes=False,
    tax_filing_status="Single",
    state_of_residence="TX",
    dividend_yield=0.0,
    fund_expense=0.0,
    use_fund_expenses=False,
    rebalance_every_year=False,
    initial_allocation_mode="dont-rebalance",
    roth_flows=None,
):
    return Simulation(
        start_year=2026,
        years_to_simulate=1,
        inflation_rate=0.0,
        num_sims=1,
        fund_expense=fund_expense,
        use_fund_expenses=use_fund_expenses,
        plot_mode="raw",
        subplot_mode="baseline",
        include_rmd=include_rmd,
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
        sim_initial_allocation_mode=initial_allocation_mode,
        custom_stock=0.50,
        custom_bonds=0.30,
        custom_cash=0.20,
        rebalance_every_year=rebalance_every_year,
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
        roth_flows=[] if roth_flows is None else roth_flows,
        root=None,
    )


def install_market_path(monkeypatch, *, equity_return=0.0, bond_return=0.0, cash_return=0.0):
    def fake_generate_market_path(sim_config, years_to_simulate, sim_index=None):
        assert years_to_simulate == 1
        return {
            "eq": np.array([0.0, equity_return], dtype=float),
            "bd": np.array([0.0, bond_return], dtype=float),
            "cs": np.array([0.0, cash_return], dtype=float),
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
    husband=None,
    wife=None,
    husband_portfolio=None,
    wife_portfolio=None,
    expenses=0.0,
    config=None,
    equity_return=0.0,
    bond_return=0.0,
    cash_return=0.0,
):
    install_market_path(
        monkeypatch,
        equity_return=equity_return,
        bond_return=bond_return,
        cash_return=cash_return,
    )

    return simulate_yearly_portfolios(
        make_portfolio() if husband_portfolio is None else husband_portfolio,
        make_portfolio() if wife_portfolio is None else wife_portfolio,
        make_person() if husband is None else husband,
        make_person() if wife is None else wife,
        make_expenses(expenses),
        make_config() if config is None else config,
        num_sims=1,
    )


def test_expense_shortfall_reduces_ira_and_workplace_roth_contributions_proportionally(
    monkeypatch,
):
    config = make_config(
        roth_flows=[
            make_roth_flow(
                flow_type="roth_ira_contribution",
                amount=4_000.0,
            ),
            make_roth_flow(
                flow_type="roth_workplace_contribution",
                amount=4_000.0,
            ),
        ]
    )

    results = run_one_year(
        monkeypatch,
        husband=make_person(income=10_000.0),
        expenses=5_000.0,
        config=config,
    )

    assert results["roth_ira_contributions"][0, 1] == pytest.approx(2_500.0)
    assert results["roth_workplace_contributions"][0, 1] == pytest.approx(2_500.0)
    assert results["roth_total_flows"][0, 1] == pytest.approx(5_000.0)
    assert results["roth_assets"][0, 1] == pytest.approx(5_000.0)
    assert results["uncovered_expense"][0, 1] == pytest.approx(0.0)
    assert results["net_profit"][0, 1] == pytest.approx(0.0)


def test_couple_roth_shortfall_preserves_owner_and_flow_type_allocation():
    config = make_config(
        second_person_enabled=True,
        roth_flows=[
            make_roth_flow(
                flow_type="roth_ira_contribution",
                amount=4_000.0,
                owner="husband",
            ),
            make_roth_flow(
                flow_type="roth_ira_contribution",
                amount=2_000.0,
                owner="wife",
            ),
            make_roth_flow(
                flow_type="roth_workplace_contribution",
                amount=2_000.0,
                owner="husband",
            ),
            make_roth_flow(
                flow_type="roth_workplace_contribution",
                amount=2_000.0,
                owner="wife",
            ),
        ],
    )
    requested = rothEngine.prepare_requested_roth_flows(
        curr_husband_age=41,
        curr_wife_age=41,
        year=1,
        payroll_wages_husband=20_000.0,
        payroll_wages_wife=20_000.0,
        second_person_enabled=True,
        sim_config=config,
    )
    resolved = rothEngine.resolve_contribution_shortfall(
        requested_flows=requested,
        uncovered_amount=4_000.0,
    )
    husband_portfolio = portfolioEngine.create_sim_portfolio(
        make_portfolio(),
        config,
    )
    wife_portfolio = portfolioEngine.create_sim_portfolio(
        make_portfolio(),
        config,
    )

    deposited = rothEngine.deposit_funded_roth_contributions(
        husband_portfolio=husband_portfolio,
        wife_portfolio=wife_portfolio,
        funded_contributions=resolved["funded_contributions"],
        second_person_enabled=True,
    )

    funded = resolved["funded_contributions"]
    assert funded["roth_ira_contribution"] == pytest.approx(
        {"husband": 2_400.0, "wife": 1_200.0, "total": 3_600.0}
    )
    assert funded["roth_workplace_contribution"] == pytest.approx(
        {"husband": 1_200.0, "wife": 1_200.0, "total": 2_400.0}
    )
    assert deposited == pytest.approx(
        {"husband": 3_600.0, "wife": 2_400.0, "total": 6_000.0}
    )
    assert husband_portfolio.total_value_roth == pytest.approx(3_600.0)
    assert wife_portfolio.total_value_roth == pytest.approx(2_400.0)


def test_workplace_roth_cap_is_applied_per_spouse_before_household_funding(monkeypatch):
    config = make_config(
        second_person_enabled=True,
        roth_flows=[
            make_roth_flow(
                flow_type="roth_workplace_contribution",
                amount=10_000.0,
                owner="husband",
            ),
            make_roth_flow(
                flow_type="roth_workplace_contribution",
                amount=10_000.0,
                owner="wife",
            ),
        ],
    )

    results = run_one_year(
        monkeypatch,
        husband=make_person(income=3_000.0),
        wife=make_person(income=20_000.0),
        config=config,
    )

    assert results["gross_income"][0, 1] == pytest.approx(23_000.0)
    assert results["roth_workplace_contributions"][0, 1] == pytest.approx(13_000.0)
    assert results["roth_assets"][0, 1] == pytest.approx(13_000.0)
    assert results["post_tax_assets"][0, 1] == pytest.approx(10_000.0)
    assert results["total_assets"][0, 1] == pytest.approx(23_000.0)


def test_rmd_and_roth_conversion_are_both_included_once_in_ordinary_income(
    monkeypatch,
):
    config = make_config(
        include_rmd=True,
        calculate_income_taxes=True,
        roth_flows=[
            make_roth_flow(
                flow_type="roth_conversion",
                amount=10_000.0,
            )
        ],
    )
    ordinary_income_calls = []

    def capture_tax_split(*, ordinary_income, qualified_dividends, year_cache, sim_config):
        ordinary_income_calls.append(ordinary_income)
        return 0.0, 0.0, 0.0, 0.0, 0.0

    monkeypatch.setattr(
        taxEngine,
        "calculate_total_income_tax_split",
        capture_tax_split,
    )

    results = run_one_year(
        monkeypatch,
        husband=make_person(age=72, retire_age=65),
        husband_portfolio=make_portfolio(pre_tax=100_000.0),
        config=config,
    )
    expected_rmd = withdrawalEngine.calculate_rmd(100_000.0, 73)
    expected_ordinary_income = expected_rmd + 10_000.0

    assert ordinary_income_calls == pytest.approx([expected_ordinary_income])
    assert results["breakdown_by_class"]["rmd"][0, 1] == pytest.approx(expected_rmd)
    assert results["roth_conversions"][0, 1] == pytest.approx(10_000.0)
    assert results["gross_income"][0, 1] == pytest.approx(expected_rmd)
    assert ordinary_income_calls[0] == pytest.approx(
        results["gross_income"][0, 1]
        + results["roth_conversions"][0, 1]
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        100_000.0 - expected_rmd - 10_000.0
    )
    assert results["roth_assets"][0, 1] == pytest.approx(10_000.0)


def test_ordinary_income_qualified_dividends_and_state_tax_reconcile_exactly(
    monkeypatch,
):
    config = make_config(
        calculate_income_taxes=True,
        calculate_state_taxes=True,
        state_of_residence="CO",
        dividend_yield=0.10,
    )

    results = run_one_year(
        monkeypatch,
        husband=make_person(income=60_000.0),
        husband_portfolio=make_portfolio(post_tax=100_000.0),
        config=config,
        equity_return=0.10,
    )

    expected_state_tax = 70_000.0 * 0.044
    component_total = (
        results["federal_ordinary_tax"][0, 1]
        + results["federal_qualified_dividend_tax"][0, 1]
        + results["state_income_tax"][0, 1]
    )

    assert results["gross_income"][0, 1] == pytest.approx(70_000.0)
    assert results["qualified_dividends"][0, 1] == pytest.approx(10_000.0)
    assert results["state_income_tax"][0, 1] == pytest.approx(expected_state_tax)
    assert results["taxes"][0, 1] == pytest.approx(component_total)
    assert results["net_income"][0, 1] == pytest.approx(
        results["gross_income"][0, 1] - component_total
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        100_000.0 + results["net_income"][0, 1]
    )


def test_couple_payroll_taxes_apply_wage_thresholds_per_person(monkeypatch):
    config = make_config(
        second_person_enabled=True,
        calculate_payroll_taxes=True,
        tax_filing_status="Married Filing Jointly",
    )

    results = run_one_year(
        monkeypatch,
        husband=make_person(income=200_000.0),
        wife=make_person(income=100_000.0),
        config=config,
    )

    expected_social_security = (184_500.0 + 100_000.0) * 0.062
    expected_medicare = 300_000.0 * 0.0145
    expected_additional_medicare = 50_000.0 * 0.009
    expected_payroll = (
        expected_social_security
        + expected_medicare
        + expected_additional_medicare
    )

    assert results["social_security_payroll_tax"][0, 1] == pytest.approx(
        expected_social_security
    )
    assert results["medicare_tax"][0, 1] == pytest.approx(expected_medicare)
    assert results["additional_medicare_tax"][0, 1] == pytest.approx(
        expected_additional_medicare
    )
    assert results["payroll_tax"][0, 1] == pytest.approx(expected_payroll)
    assert results["taxes"][0, 1] == pytest.approx(expected_payroll)
    assert (
        results["net_income_husband"][0, 1]
        + results["net_income_wife"][0, 1]
        == pytest.approx(results["net_income"][0, 1])
    )


def test_emergency_pre_tax_tax_delta_reconciles_income_tax_and_remaining_assets(
    monkeypatch,
):
    config = make_config(calculate_income_taxes=True)
    husband = make_person(income=40_000.0)
    portfolio = make_portfolio(pre_tax=100_000.0, post_tax=20_000.0)

    taxEngine.initialize_tax_engine_for_simulation(config)
    year_cache = taxEngine.prepare_tax_year_cache(1, config)
    _, _, _, baseline_tax, _ = taxEngine.calculate_total_income_tax_split(
        40_000.0,
        0.0,
        year_cache,
        config,
    )
    expected_emergency = 100_000.0 - 40_000.0 + baseline_tax - 20_000.0
    _, _, _, final_tax, _ = taxEngine.calculate_total_income_tax_split(
        40_000.0 + expected_emergency,
        0.0,
        year_cache,
        config,
    )
    expected_delta = final_tax - baseline_tax

    results = run_one_year(
        monkeypatch,
        husband=husband,
        husband_portfolio=portfolio,
        expenses=100_000.0,
        config=config,
    )

    assert results["emergency_pre_tax_used"][0, 1] == pytest.approx(expected_emergency)
    assert results["final_tax_delta"][0, 1] == pytest.approx(expected_delta)
    assert results["final_tax_delta_deducted"][0, 1] == pytest.approx(0.0)
    assert results["final_tax_delta_uncovered"][0, 1] == pytest.approx(expected_delta)
    assert results["taxes"][0, 1] == pytest.approx(final_tax)
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        100_000.0 - expected_emergency
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(0.0)
    assert results["final_tax_delta"][0, 1] == pytest.approx(
        results["final_tax_delta_deducted"][0, 1]
        + results["final_tax_delta_uncovered"][0, 1]
    )


def test_hsa_returns_fund_expenses_and_rebalance_preserve_bucket_accounting():
    portfolio = PortfolioState(
        eq_pre=0.0,
        bd_pre=0.0,
        cs_pre=0.0,
        eq_post=0.0,
        bd_post=0.0,
        cs_post=0.0,
        re_post=0.0,
        hsa_eq=100.0,
        hsa_bd=100.0,
        hsa_cs=100.0,
    )
    config = make_config(initial_allocation_mode="custom")

    fund_expenses = portfolioEngine.apply_returns_and_fund_expenses(
        portfolio,
        eq_total_return=0.10,
        eq_taxable_price_return=0.10,
        bd_return=0.05,
        cs_return=0.0,
        re_return=0.0,
        fund_expense=0.01,
    )
    value_after_returns_and_expenses = portfolio.total_value_hsa
    portfolioEngine.rebalance(portfolio, config)

    assert fund_expenses == pytest.approx(3.15)
    assert value_after_returns_and_expenses == pytest.approx(311.85)
    assert portfolio.hsa_eq == pytest.approx(155.925)
    assert portfolio.hsa_bd == pytest.approx(93.555)
    assert portfolio.hsa_cs == pytest.approx(62.37)
    assert portfolio.total_value_hsa == pytest.approx(value_after_returns_and_expenses)
    assert portfolio.total_value == pytest.approx(311.85)
