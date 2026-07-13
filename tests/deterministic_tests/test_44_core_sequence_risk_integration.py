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
    age=63,
    retire_age=65,
):
    return Person(
        age=age,
        retire_age=retire_age,
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
):
    return Portfolio(
        equity_pre=equity_pre,
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
    years_to_simulate=4,
    sequence_risk_enabled=True,
    always_use_expense_mode=False,
):
    config = Simulation(
        start_year=2026,
        years_to_simulate=years_to_simulate,
        inflation_rate=0.0,
        num_sims=1,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode="raw",
        subplot_mode="monte_carlo",
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
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=0.0,
        always_use_expense_mode=always_use_expense_mode,
        sequence_risk_enabled=sequence_risk_enabled,
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

    config.monte_carlo_mode = "pathBasedAnnualSampling"
    config.use_correlated_returns = False
    config.disable_sequence_risk_for_historical = True

    return config


def make_market_path(
    equity_returns,
):
    years_to_simulate = len(equity_returns)

    return {
        "eq": np.array(
            [0.0] + list(equity_returns),
            dtype=float,
        ),
        "bd": np.zeros(
            years_to_simulate + 1,
            dtype=float,
        ),
        "cs": np.zeros(
            years_to_simulate + 1,
            dtype=float,
        ),
        "re": np.zeros(
            years_to_simulate + 1,
            dtype=float,
        ),
    }


def install_market_path(
    monkeypatch,
    *,
    equity_returns,
):
    path = make_market_path(equity_returns)

    monkeypatch.setattr(
        monteCarloEngine,
        "prepare_market_path_sampling",
        lambda sim_config: None,
    )

    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        assert years_to_simulate == len(equity_returns)
        return {
            key: values.copy()
            for key, values in path.items()
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )


def run_core(
    *,
    config,
    husband=None,
    num_sims=1,
):
    if husband is None:
        husband = make_person()

    return simulate_yearly_portfolios(
        make_portfolio(
            equity_pre=100_000.0,
        ),
        make_portfolio(),
        husband,
        make_person(
            age=0,
            retire_age=100,
        ),
        DynamicExpenses(),
        config,
        num_sims=num_sims,
    )


def test_sequence_risk_overlay_receives_withdrawal_start_year(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=4,
        sequence_risk_enabled=True,
        always_use_expense_mode=False,
    )

    install_market_path(
        monkeypatch,
        equity_returns=[
            0.0,
            0.0,
            0.0,
            0.0,
        ],
    )

    received = {}

    def fake_apply_sequence_risk_overlay(
        *,
        market_path,
        sim_config,
        years_to_simulate,
        withdrawal_start_year,
    ):
        received["years_to_simulate"] = years_to_simulate
        received["withdrawal_start_year"] = (
            withdrawal_start_year
        )

        return market_path, {
            "enabled": True,
            "applied": True,
            "start_year": 2,
            "end_year": 3,
            "length_years": 2,
            "timing": "At Retirement",
            "depth": "Moderate",
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "apply_sequence_risk_overlay",
        fake_apply_sequence_risk_overlay,
    )

    run_core(
        config=config,
        husband=make_person(
            age=63,
            retire_age=65,
        ),
    )

    assert received["years_to_simulate"] == 4

    # The person is age 63 initially and reaches retirement
    # age 65 in simulation year 2.
    assert received["withdrawal_start_year"] == 2


def test_sequence_risk_overlay_modified_path_is_used_by_core(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=3,
        sequence_risk_enabled=True,
    )

    install_market_path(
        monkeypatch,
        equity_returns=[
            0.10,
            0.10,
            0.10,
        ],
    )

    def fake_apply_sequence_risk_overlay(
        *,
        market_path,
        sim_config,
        years_to_simulate,
        withdrawal_start_year,
    ):
        stressed_path = {
            key: values.copy()
            for key, values in market_path.items()
        }

        stressed_path["eq"] = np.array(
            [
                0.0,
                -0.20,
                -0.10,
                0.10,
            ],
            dtype=float,
        )

        return stressed_path, {
            "enabled": True,
            "applied": True,
            "start_year": 1,
            "end_year": 2,
            "length_years": 2,
            "timing": "Before Retirement",
            "depth": "Severe",
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "apply_sequence_risk_overlay",
        fake_apply_sequence_risk_overlay,
    )

    results = run_core(
        config=config,
    )

    assert results["total_assets"][0] == pytest.approx(
        [
            100_000.0,
            80_000.0,
            72_000.0,
            79_200.0,
        ]
    )


def test_sequence_risk_metadata_is_recorded(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=3,
        sequence_risk_enabled=True,
    )

    install_market_path(
        monkeypatch,
        equity_returns=[
            0.0,
            0.0,
            0.0,
        ],
    )

    def fake_apply_sequence_risk_overlay(
        *,
        market_path,
        sim_config,
        years_to_simulate,
        withdrawal_start_year,
    ):
        return market_path, {
            "enabled": True,
            "applied": True,
            "start_year": 1,
            "end_year": 2,
            "length_years": 2,
            "timing": "At Retirement",
            "depth": "Severe",
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "apply_sequence_risk_overlay",
        fake_apply_sequence_risk_overlay,
    )

    results = run_core(
        config=config,
    )

    assert results["sequence_risk_active"] == pytest.approx(
        [
            True,
        ]
    )
    assert results["sequence_risk_start_year"] == pytest.approx(
        [
            1,
        ]
    )
    assert results["sequence_risk_end_year"] == pytest.approx(
        [
            2,
        ]
    )


def test_sequence_risk_metadata_is_stored_per_simulation(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=2,
        sequence_risk_enabled=True,
    )

    install_market_path(
        monkeypatch,
        equity_returns=[
            0.0,
            0.0,
        ],
    )

    calls = []

    def fake_apply_sequence_risk_overlay(
        *,
        market_path,
        sim_config,
        years_to_simulate,
        withdrawal_start_year,
    ):
        sim_index = len(calls)
        calls.append(sim_index)

        return market_path, {
            "enabled": True,
            "applied": sim_index != 1,
            "start_year": (
                sim_index + 1
                if sim_index != 1
                else None
            ),
            "end_year": (
                sim_index + 1
                if sim_index != 1
                else None
            ),
            "length_years": (
                1
                if sim_index != 1
                else 0
            ),
            "timing": (
                "Early"
                if sim_index == 0
                else "None"
                if sim_index == 1
                else "Late"
            ),
            "depth": (
                "Moderate"
                if sim_index != 2
                else "Severe"
            ),
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "apply_sequence_risk_overlay",
        fake_apply_sequence_risk_overlay,
    )

    results = run_core(
        config=config,
        num_sims=3,
    )

    assert calls == [
        0,
        1,
        2,
    ]

    assert results["sequence_risk_active"] == pytest.approx(
        [
            True,
            False,
            True,
        ]
    )

    assert results["sequence_risk_start_year"] == pytest.approx(
        [
            1,
            -1,
            3,
        ]
    )

    assert results["sequence_risk_end_year"] == pytest.approx(
        [
            1,
            -1,
            3,
        ]
    )


def test_disabled_sequence_risk_does_not_change_market_path(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=2,
        sequence_risk_enabled=False,
    )

    install_market_path(
        monkeypatch,
        equity_returns=[
            0.10,
            0.10,
        ],
    )

    calls = []

    def fake_apply_sequence_risk_overlay(
        *,
        market_path,
        sim_config,
        years_to_simulate,
        withdrawal_start_year,
    ):
        calls.append(
            {
                "enabled": sim_config.sequence_risk_enabled,
                "years_to_simulate": years_to_simulate,
                "withdrawal_start_year": withdrawal_start_year,
            }
        )

        return market_path, {
            "enabled": False,
            "applied": False,
            "start_year": None,
            "end_year": None,
            "length_years": 0,
            "timing": "None",
            "depth": "Moderate",
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "apply_sequence_risk_overlay",
        fake_apply_sequence_risk_overlay,
    )

    results = run_core(
        config=config,
    )

    assert len(calls) == 1
    assert calls[0]["enabled"] is False
    assert calls[0]["years_to_simulate"] == 2

    assert results["total_assets"][0] == pytest.approx(
        [
            100_000.0,
            110_000.0,
            121_000.0,
        ]
    )

    assert results["sequence_risk_active"] == pytest.approx(
        [
            False,
        ]
    )
    assert results["sequence_risk_start_year"] == pytest.approx(
        [
            -1,
        ]
    )
    assert results["sequence_risk_end_year"] == pytest.approx(
        [
            -1,
        ]
    )

def test_always_expense_mode_has_no_withdrawal_start_year(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=3,
        sequence_risk_enabled=True,
        always_use_expense_mode=True,
    )

    install_market_path(
        monkeypatch,
        equity_returns=[
            0.0,
            0.0,
            0.0,
        ],
    )

    received = {}

    def fake_apply_sequence_risk_overlay(
        *,
        market_path,
        sim_config,
        years_to_simulate,
        withdrawal_start_year,
    ):
        received["withdrawal_start_year"] = (
            withdrawal_start_year
        )

        return market_path, {
            "enabled": True,
            "applied": False,
            "start_year": None,
            "end_year": None,
            "length_years": 0,
            "timing": "None",
            "depth": "Moderate",
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "apply_sequence_risk_overlay",
        fake_apply_sequence_risk_overlay,
    )

    run_core(
        config=config,
    )

    assert received["withdrawal_start_year"] is None