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
        annual_401k_contribution=0.0,
        annual_employer_match=0.0,
        pension_inflation_adjustment_pct=0.0,
    )


def make_portfolio(
    *,
    pre_tax=0.0,
    post_tax=0.0,
    roth=0.0,
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
        hsa_cash=0.0,
        hsa_equity=0.0,
        hsa_bond=0.0,
    )


def make_roth_flow(
    *,
    flow_type,
    amount,
    owner="husband",
    start_age=0,
    end_age=120,
    inflation_adjustment_pct=0.0,
):
    return {
        "enabled": True,
        "type": flow_type,
        "owner": owner,
        "amount": amount,
        "start_age": start_age,
        "end_age": end_age,
        "inflation_adjustment_pct": inflation_adjustment_pct,
    }


def make_config(
    *,
    years_to_simulate=1,
    calculate_income_taxes=False,
    roth_flows=None,
):
    config = Simulation(
        start_year=2026,
        years_to_simulate=years_to_simulate,
        inflation_rate=0.0,
        num_sims=1,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode="raw",
        subplot_mode="baseline",
        include_rmd=False,
        calculate_income_taxes=calculate_income_taxes,
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

    config.roth_flows = [] if roth_flows is None else roth_flows

    return config


def install_zero_market_path(monkeypatch):
    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        zeros = np.zeros(
            years_to_simulate + 1,
            dtype=float,
        )

        return {
            "eq": zeros.copy(),
            "bd": zeros.copy(),
            "cs": zeros.copy(),
            "re": zeros.copy(),
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )


def run_core(
    monkeypatch,
    *,
    husband=None,
    husband_portfolio=None,
    years_to_simulate=1,
    calculate_income_taxes=False,
    roth_flows=None,
):
    install_zero_market_path(monkeypatch)

    if husband is None:
        husband = make_person()

    if husband_portfolio is None:
        husband_portfolio = make_portfolio()

    return simulate_yearly_portfolios(
        husband_portfolio,
        make_portfolio(),
        husband,
        make_person(
            age=0,
            retire_age=100,
        ),
        DynamicExpenses(),
        make_config(
            years_to_simulate=years_to_simulate,
            calculate_income_taxes=calculate_income_taxes,
            roth_flows=roth_flows,
        ),
        num_sims=1,
    )


def test_ira_and_workplace_contributions_accumulate_in_roth_assets(
    monkeypatch,
):
    roth_flows = [
        make_roth_flow(
            flow_type="roth_ira_contribution",
            amount=6_000.0,
        ),
        make_roth_flow(
            flow_type="roth_workplace_contribution",
            amount=10_000.0,
        ),
    ]

    results = run_core(
        monkeypatch,
        husband=make_person(
            age=40,
            retire_age=65,
            income=50_000.0,
        ),
        years_to_simulate=2,
        roth_flows=roth_flows,
    )

    assert results["gross_income"][0] == pytest.approx(
        [
            0.0,
            50_000.0,
            50_000.0,
        ]
    )

    assert results["roth_ira_contributions"][0] == pytest.approx(
        [
            0.0,
            6_000.0,
            6_000.0,
        ]
    )

    assert results["roth_workplace_contributions"][0] == pytest.approx(
        [
            0.0,
            10_000.0,
            10_000.0,
        ]
    )

    assert results["roth_total_flows"][0] == pytest.approx(
        [
            0.0,
            16_000.0,
            16_000.0,
        ]
    )

    assert results["roth_assets"][0] == pytest.approx(
        [
            0.0,
            16_000.0,
            32_000.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            0.0,
            34_000.0,
            68_000.0,
        ]
    )

    assert results["total_assets"][0] == pytest.approx(
        [
            0.0,
            50_000.0,
            100_000.0,
        ]
    )


def test_workplace_roth_contribution_is_capped_by_current_wages(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=40,
            retire_age=65,
            income=8_000.0,
        ),
        roth_flows=[
            make_roth_flow(
                flow_type="roth_workplace_contribution",
                amount=20_000.0,
            ),
        ],
    )

    assert results["roth_workplace_contributions"][0, 1] == (
        pytest.approx(8_000.0)
    )

    assert results["roth_assets"][0, 1] == pytest.approx(
        8_000.0
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )

    assert results["total_assets"][0, 1] == pytest.approx(
        8_000.0
    )


def test_roth_conversion_moves_assets_without_changing_total_value(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband_portfolio=make_portfolio(
            pre_tax=100_000.0,
        ),
        roth_flows=[
            make_roth_flow(
                flow_type="roth_conversion",
                amount=20_000.0,
            ),
        ],
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        80_000.0
    )

    assert results["roth_assets"][0, 1] == pytest.approx(
        20_000.0
    )

    assert results["roth_conversions"][0, 1] == pytest.approx(
        20_000.0
    )

    assert results["roth_total_flows"][0, 1] == pytest.approx(
        20_000.0
    )

    assert (
        results["breakdown_by_class"]["roth_conversion"][0, 1]
        == pytest.approx(20_000.0)
    )

    assert results["total_assets"][0, 1] == pytest.approx(
        100_000.0
    )


def test_roth_conversion_is_capped_by_available_pre_tax_assets(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband_portfolio=make_portfolio(
            pre_tax=12_000.0,
        ),
        roth_flows=[
            make_roth_flow(
                flow_type="roth_conversion",
                amount=20_000.0,
            ),
        ],
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        0.0
    )

    assert results["roth_assets"][0, 1] == pytest.approx(
        12_000.0
    )

    assert results["roth_conversions"][0, 1] == pytest.approx(
        12_000.0
    )

    assert results["roth_total_flows"][0, 1] == pytest.approx(
        12_000.0
    )

    assert results["total_assets"][0, 1] == pytest.approx(
        12_000.0
    )


def test_roth_conversion_generates_income_tax(
    monkeypatch,
):
    no_conversion = run_core(
        monkeypatch,
        husband_portfolio=make_portfolio(
            pre_tax=100_000.0,
            post_tax=50_000.0,
        ),
        calculate_income_taxes=True,
    )

    with_conversion = run_core(
        monkeypatch,
        husband_portfolio=make_portfolio(
            pre_tax=100_000.0,
            post_tax=50_000.0,
        ),
        calculate_income_taxes=True,
        roth_flows=[
            make_roth_flow(
                flow_type="roth_conversion",
                amount=20_000.0,
            ),
        ],
    )

    assert no_conversion["taxes"][0, 1] == pytest.approx(
        0.0
    )

    assert with_conversion["taxes"][0, 1] > 0.0

    assert with_conversion["federal_ordinary_tax"][0, 1] > (
        no_conversion["federal_ordinary_tax"][0, 1]
    )

    assert (
        with_conversion["breakdown_by_class"]["roth_conversion"][
            0, 1
        ]
        == pytest.approx(20_000.0)
    )

    assert with_conversion["pre_tax_assets"][0, 1] == pytest.approx(
        80_000.0
    )

    assert with_conversion["roth_assets"][0, 1] == pytest.approx(
        20_000.0
    )

    assert with_conversion["total_assets"][0, 1] == pytest.approx(
        150_000.0 - with_conversion["taxes"][0, 1]
    )


def test_roth_flow_age_window_is_applied_by_the_full_core(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=39,
            retire_age=65,
            income=20_000.0,
        ),
        years_to_simulate=3,
        roth_flows=[
            make_roth_flow(
                flow_type="roth_ira_contribution",
                amount=5_000.0,
                start_age=41,
                end_age=42,
            ),
        ],
    )

    # Simulation ages are 40, 41, and 42.
    assert results["roth_ira_contributions"][0] == pytest.approx(
        [
            0.0,
            0.0,
            5_000.0,
            5_000.0,
        ]
    )

    assert results["roth_assets"][0] == pytest.approx(
        [
            0.0,
            0.0,
            5_000.0,
            10_000.0,
        ]
    )
