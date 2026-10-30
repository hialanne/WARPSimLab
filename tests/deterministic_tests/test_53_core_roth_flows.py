import numpy as np
import pytest
from tests.architectural_helpers import make_person as build_person, make_portfolio as build_portfolio, make_simulation

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


def make_person(
    *,
    age=40,
    retire_age=65,
    income=0.0,
):
    return build_person(age=age, retire_age=retire_age, income=income)


def make_portfolio(
    *,
    pre_tax=0.0,
    post_tax=0.0,
    roth=0.0,
):
    return build_portfolio(equity_pre=pre_tax, equity_post=post_tax, equity_roth=roth)


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
    config = make_simulation(
        years_to_simulate=years_to_simulate,
        results_mode="baseline",
        calculate_income_taxes=calculate_income_taxes,
        sim_initial_allocation_mode="dont-rebalance",
        retirement_withdraw_dollars=0.0,
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
