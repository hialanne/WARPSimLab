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
    pension_inflation_adjustment_pct=0.0,
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
        pension_inflation_adjustment_pct=(
            pension_inflation_adjustment_pct
        ),
    )


def make_portfolio():
    return Portfolio(
        equity_pre=0.0,
        equity_post=0.0,
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
    years_to_simulate=1,
    inflation_rate=0.0,
    second_person_enabled=False,
    special_income_streams=None,
):
    return Simulation(
        start_year=2026,
        years_to_simulate=years_to_simulate,
        inflation_rate=inflation_rate,
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
        second_person_enabled=second_person_enabled,
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
        special_income_streams=special_income_streams,
        root=None,
    )


def install_zero_market_path(monkeypatch):
    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        zeros = np.zeros(years_to_simulate + 1, dtype=float)

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


def run_simulation(
    monkeypatch,
    husband,
    *,
    wife=None,
    years_to_simulate=1,
    inflation_rate=0.0,
    second_person_enabled=False,
    special_income_streams=None,
):
    install_zero_market_path(monkeypatch)

    if wife is None:
        wife = make_person()

    return simulate_yearly_portfolios(
        make_portfolio(),
        make_portfolio(),
        husband,
        wife,
        DynamicExpenses(),
        make_config(
            years_to_simulate=years_to_simulate,
            inflation_rate=inflation_rate,
            second_person_enabled=second_person_enabled,
            special_income_streams=special_income_streams,
        ),
        num_sims=1,
    )


def test_work_income_is_reported_and_deposited(monkeypatch):
    husband = make_person(
        age=40,
        retire_age=65,
        income=50_000.0,
    )

    results = run_simulation(
        monkeypatch,
        husband,
    )

    assert results["breakdown_by_class"]["work"][0, 1] == (
        pytest.approx(50_000.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        50_000.0
    )
    assert results["net_income"][0, 1] == pytest.approx(
        50_000.0
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        50_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        50_000.0
    )


def test_work_income_stops_at_retirement_age(monkeypatch):
    husband = make_person(
        age=64,
        retire_age=65,
        income=50_000.0,
    )

    results = run_simulation(
        monkeypatch,
        husband,
    )

    assert results["breakdown_by_class"]["work"][0, 1] == (
        pytest.approx(0.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(0.0)
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )


def test_work_income_is_inflated(monkeypatch):
    husband = make_person(
        age=40,
        retire_age=65,
        income=50_000.0,
    )

    results = run_simulation(
        monkeypatch,
        husband,
        years_to_simulate=2,
        inflation_rate=0.10,
    )

    assert results["breakdown_by_class"]["work"][0] == (
        pytest.approx(
            [
                0.0,
                55_000.0,
                60_500.0,
            ]
        )
    )

    assert results["gross_income"][0] == pytest.approx(
        [
            0.0,
            55_000.0,
            60_500.0,
        ]
    )


def test_social_security_starts_at_selected_age(monkeypatch):
    husband = make_person(
        age=64,
        retire_age=65,
        ss=24_000.0,
        ss_age=66,
    )

    results = run_simulation(
        monkeypatch,
        husband,
        years_to_simulate=2,
    )

    assert results["breakdown_by_class"]["ss"][0] == (
        pytest.approx(
            [
                0.0,
                0.0,
                24_000.0,
            ]
        )
    )


def test_social_security_start_age_is_capped_at_70(monkeypatch):
    husband = make_person(
        age=69,
        retire_age=65,
        ss=24_000.0,
        ss_age=75,
    )

    results = run_simulation(
        monkeypatch,
        husband,
    )

    assert results["breakdown_by_class"]["ss"][0, 1] == (
        pytest.approx(24_000.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        24_000.0
    )


def test_social_security_is_inflated(monkeypatch):
    husband = make_person(
        age=64,
        retire_age=65,
        ss=20_000.0,
        ss_age=65,
    )

    results = run_simulation(
        monkeypatch,
        husband,
        years_to_simulate=2,
        inflation_rate=0.10,
    )

    assert results["breakdown_by_class"]["ss"][0] == (
        pytest.approx(
            [
                0.0,
                22_000.0,
                24_200.0,
            ]
        )
    )


def test_pension_starts_at_selected_age(monkeypatch):
    husband = make_person(
        age=64,
        retire_age=65,
        pension=30_000.0,
        pension_age=66,
    )

    results = run_simulation(
        monkeypatch,
        husband,
        years_to_simulate=2,
    )

    assert results["breakdown_by_class"]["pension"][0] == (
        pytest.approx(
            [
                0.0,
                0.0,
                30_000.0,
            ]
        )
    )


def test_pension_uses_configured_fraction_of_inflation(
    monkeypatch,
):
    husband = make_person(
        age=64,
        retire_age=65,
        pension=30_000.0,
        pension_age=65,
        pension_inflation_adjustment_pct=50.0,
    )

    results = run_simulation(
        monkeypatch,
        husband,
        years_to_simulate=2,
        inflation_rate=0.10,
    )

    assert results["breakdown_by_class"]["pension"][0] == (
        pytest.approx(
            [
                0.0,
                31_500.0,
                33_075.0,
            ]
        )
    )


def test_annuity_starts_at_selected_age_and_remains_fixed(
    monkeypatch,
):
    husband = make_person(
        age=64,
        retire_age=65,
        annuity=12_000.0,
        annuity_age=65,
    )

    results = run_simulation(
        monkeypatch,
        husband,
        years_to_simulate=2,
        inflation_rate=0.10,
    )

    assert results["breakdown_by_class"]["annuity"][0] == (
        pytest.approx(
            [
                0.0,
                12_000.0,
                12_000.0,
            ]
        )
    )


def test_income_classes_sum_to_household_income(monkeypatch):
    husband = make_person(
        age=69,
        retire_age=75,
        income=40_000.0,
        ss=20_000.0,
        ss_age=70,
        pension=15_000.0,
        pension_age=70,
        annuity=5_000.0,
        annuity_age=70,
    )

    results = run_simulation(
        monkeypatch,
        husband,
    )

    expected_total = (
        40_000.0
        + 20_000.0
        + 15_000.0
        + 5_000.0
    )

    assert results["breakdown_by_class"]["work"][0, 1] == (
        pytest.approx(40_000.0)
    )
    assert results["breakdown_by_class"]["ss"][0, 1] == (
        pytest.approx(20_000.0)
    )
    assert results["breakdown_by_class"]["pension"][0, 1] == (
        pytest.approx(15_000.0)
    )
    assert results["breakdown_by_class"]["annuity"][0, 1] == (
        pytest.approx(5_000.0)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        expected_total
    )
    assert results["net_income"][0, 1] == pytest.approx(
        expected_total
    )


def test_taxable_special_income_is_reported_and_deposited(
    monkeypatch,
):
    husband = make_person(
        age=49,
        retire_age=100,
    )

    streams = [
        {
            "enabled": True,
            "owner": "husband",
            "start_age": 50,
            "end_age": 55,
            "amount": 10_000.0,
            "taxable": True,
            "inflation_adjustment_pct": 0.0,
        }
    ]

    results = run_simulation(
        monkeypatch,
        husband,
        special_income_streams=streams,
    )

    assert (
        results["breakdown_by_class"]["special_income"][0, 1]
        == pytest.approx(10_000.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        10_000.0
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        10_000.0
    )


def test_special_income_respects_age_range(monkeypatch):
    husband = make_person(
        age=48,
        retire_age=100,
    )

    streams = [
        {
            "enabled": True,
            "owner": "husband",
            "start_age": 50,
            "end_age": 50,
            "amount": 10_000.0,
            "taxable": True,
            "inflation_adjustment_pct": 0.0,
        }
    ]

    results = run_simulation(
        monkeypatch,
        husband,
        years_to_simulate=3,
        special_income_streams=streams,
    )

    assert (
        results["breakdown_by_class"]["special_income"][0]
        == pytest.approx(
            [
                0.0,
                0.0,
                10_000.0,
                0.0,
            ]
        )
    )


def test_non_taxable_special_income_is_still_household_cash(
    monkeypatch,
):
    husband = make_person(
        age=49,
        retire_age=100,
    )

    streams = [
        {
            "enabled": True,
            "owner": "husband",
            "start_age": 50,
            "end_age": 55,
            "amount": 10_000.0,
            "taxable": False,
            "inflation_adjustment_pct": 0.0,
        }
    ]

    results = run_simulation(
        monkeypatch,
        husband,
        special_income_streams=streams,
    )

    assert (
        results["breakdown_by_class"]["special_income"][0, 1]
        == pytest.approx(10_000.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        10_000.0
    )
    assert results["net_income"][0, 1] == pytest.approx(
        10_000.0
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        10_000.0
    )


def test_disabled_special_income_is_ignored(monkeypatch):
    husband = make_person(
        age=49,
        retire_age=100,
    )

    streams = [
        {
            "enabled": False,
            "owner": "husband",
            "start_age": 50,
            "end_age": 55,
            "amount": 10_000.0,
            "taxable": True,
            "inflation_adjustment_pct": 0.0,
        }
    ]

    results = run_simulation(
        monkeypatch,
        husband,
        special_income_streams=streams,
    )

    assert (
        results["breakdown_by_class"]["special_income"][0, 1]
        == pytest.approx(0.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(0.0)


def test_couple_income_is_assigned_to_correct_person(monkeypatch):
    husband = make_person(
        age=40,
        retire_age=65,
        income=60_000.0,
    )
    wife = make_person(
        age=40,
        retire_age=65,
        income=40_000.0,
    )

    results = run_simulation(
        monkeypatch,
        husband,
        wife=wife,
        second_person_enabled=True,
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        100_000.0
    )
    assert results["net_income"][0, 1] == pytest.approx(
        100_000.0
    )

    assert results["net_income_husband"][0, 1] == (
        pytest.approx(60_000.0)
    )
    assert results["net_income_wife"][0, 1] == (
        pytest.approx(40_000.0)
    )

    assert (
        results["net_income_husband"][0, 1]
        + results["net_income_wife"][0, 1]
        == pytest.approx(results["net_income"][0, 1])
    )


def test_wife_special_income_is_assigned_to_wife(monkeypatch):
    husband = make_person(
        age=49,
        retire_age=100,
    )
    wife = make_person(
        age=49,
        retire_age=100,
    )

    streams = [
        {
            "enabled": True,
            "owner": "wife",
            "start_age": 50,
            "end_age": 55,
            "amount": 12_000.0,
            "taxable": True,
            "inflation_adjustment_pct": 0.0,
        }
    ]

    results = run_simulation(
        monkeypatch,
        husband,
        wife=wife,
        second_person_enabled=True,
        special_income_streams=streams,
    )

    assert results["net_income_husband"][0, 1] == (
        pytest.approx(0.0)
    )
    assert results["net_income_wife"][0, 1] == (
        pytest.approx(12_000.0)
    )
    assert results["net_income"][0, 1] == pytest.approx(
        12_000.0
    )


def test_wife_special_income_is_ignored_when_disabled(
    monkeypatch,
):
    husband = make_person(
        age=49,
        retire_age=100,
    )
    wife = make_person(
        age=49,
        retire_age=100,
    )

    streams = [
        {
            "enabled": True,
            "owner": "wife",
            "start_age": 50,
            "end_age": 55,
            "amount": 12_000.0,
            "taxable": True,
            "inflation_adjustment_pct": 0.0,
        }
    ]

    results = run_simulation(
        monkeypatch,
        husband,
        wife=wife,
        second_person_enabled=False,
        special_income_streams=streams,
    )

    assert (
        results["breakdown_by_class"]["special_income"][0, 1]
        == pytest.approx(0.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(0.0)