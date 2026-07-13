import numpy as np
import pytest

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.dataClasses.person import Person
from src.warpsimlab.dataClasses.portfolio import Portfolio
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios
from src.warpsimlab.sim.simulationObject import Simulation


def make_person():
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
    bond_pre=0.0,
    cash_pre=0.0,
):
    return Portfolio(
        equity_pre=equity_pre,
        equity_post=0.0,
        bond_pre=bond_pre,
        bond_post=0.0,
        cash_pre=cash_pre,
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
    years_to_simulate=2,
    subplot_mode="monte_carlo",
    monte_carlo_mode="pathBasedAnnualSampling",
):
    config = Simulation(
        start_year=2026,
        years_to_simulate=years_to_simulate,
        inflation_rate=0.0,
        num_sims=1,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode="raw",
        subplot_mode=subplot_mode,
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

    config.monte_carlo_mode = monte_carlo_mode
    config.use_correlated_returns = False
    config.disable_sequence_risk_for_historical = True

    return config


def make_path(
    *,
    equity_returns,
    bond_returns=None,
    cash_returns=None,
):
    equity_returns = list(equity_returns)
    years_to_simulate = len(equity_returns)

    if bond_returns is None:
        bond_returns = [0.0] * years_to_simulate

    if cash_returns is None:
        cash_returns = [0.0] * years_to_simulate

    return {
        "eq": np.array(
            [0.0] + list(equity_returns),
            dtype=float,
        ),
        "bd": np.array(
            [0.0] + list(bond_returns),
            dtype=float,
        ),
        "cs": np.array(
            [0.0] + list(cash_returns),
            dtype=float,
        ),
        "re": np.zeros(
            years_to_simulate + 1,
            dtype=float,
        ),
    }


def install_identity_sequence_risk(monkeypatch):
    def fake_apply_sequence_risk_overlay(
        *,
        market_path,
        sim_config,
        years_to_simulate,
        withdrawal_start_year,
    ):
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


def run_core(
    *,
    config,
    num_sims,
):
    return simulate_yearly_portfolios(
        make_portfolio(
            equity_pre=100_000.0,
        ),
        make_portfolio(),
        make_person(),
        make_person(),
        DynamicExpenses(),
        config,
        num_sims=num_sims,
    )


def test_core_requests_one_market_path_per_simulation(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=2,
    )

    requested_indices = []

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
        requested_indices.append(sim_index)

        return make_path(
            equity_returns=[0.0, 0.0],
        )

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )

    install_identity_sequence_risk(monkeypatch)

    results = run_core(
        config=config,
        num_sims=3,
    )

    assert requested_indices == [
        0,
        1,
        2,
    ]

    assert results["total_assets"].shape == (
        3,
        3,
    )


def test_different_market_paths_produce_different_simulation_rows(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=2,
    )

    monkeypatch.setattr(
        monteCarloEngine,
        "prepare_market_path_sampling",
        lambda sim_config: None,
    )

    paths = {
        0: make_path(
            equity_returns=[
                0.10,
                0.10,
            ],
        ),
        1: make_path(
            equity_returns=[
                0.00,
                0.00,
            ],
        ),
        2: make_path(
            equity_returns=[
                -0.10,
                -0.10,
            ],
        ),
    }

    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        return paths[sim_index]

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )

    install_identity_sequence_risk(monkeypatch)

    results = run_core(
        config=config,
        num_sims=3,
    )

    assert results["total_assets"][0] == pytest.approx(
        [
            100_000.0,
            110_000.0,
            121_000.0,
        ]
    )

    assert results["total_assets"][1] == pytest.approx(
        [
            100_000.0,
            100_000.0,
            100_000.0,
        ]
    )

    assert results["total_assets"][2] == pytest.approx(
        [
            100_000.0,
            90_000.0,
            81_000.0,
        ]
    )


def test_market_path_year_zero_value_is_not_applied(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=2,
    )

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
        return {
            "eq": np.array(
                [
                    9.99,
                    0.10,
                    0.20,
                ],
                dtype=float,
            ),
            "bd": np.zeros(3, dtype=float),
            "cs": np.zeros(3, dtype=float),
            "re": np.zeros(3, dtype=float),
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )

    install_identity_sequence_risk(monkeypatch)

    results = run_core(
        config=config,
        num_sims=1,
    )

    assert results["total_assets"][0] == pytest.approx(
        [
            100_000.0,
            110_000.0,
            132_000.0,
        ]
    )


def test_market_path_uses_correct_asset_return_indices(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=2,
    )

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
        return make_path(
            equity_returns=[
                0.10,
                -0.20,
            ],
            bond_returns=[
                0.05,
                0.10,
            ],
            cash_returns=[
                0.02,
                0.03,
            ],
        )

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )

    install_identity_sequence_risk(monkeypatch)

    results = simulate_yearly_portfolios(
        make_portfolio(
            equity_pre=50_000.0,
            bond_pre=30_000.0,
            cash_pre=20_000.0,
        ),
        make_portfolio(),
        make_person(),
        make_person(),
        DynamicExpenses(),
        config,
        num_sims=1,
    )

    expected_year_1 = (
        50_000.0 * 1.10
        + 30_000.0 * 1.05
        + 20_000.0 * 1.02
    )

    expected_year_2 = (
        50_000.0 * 1.10 * 0.80
        + 30_000.0 * 1.05 * 1.10
        + 20_000.0 * 1.02 * 1.03
    )

    assert results["total_assets"][0, 1] == pytest.approx(
        expected_year_1
    )
    assert results["total_assets"][0, 2] == pytest.approx(
        expected_year_2
    )


def install_historical_preparation(
    monkeypatch,
    *,
    number_of_windows,
):
    def fake_prepare_market_path_sampling(sim_config):
        sim_config._hist_num_windows = number_of_windows

        sim_config._hist_years = np.array(
            [
                2000,
                2001,
                2002,
                2003,
                2004,
            ],
            dtype=int,
        )

        sim_config._hist_window_start_indices = np.arange(
            number_of_windows,
            dtype=int,
        )

        sim_config._hist_inflation = np.zeros(
            len(sim_config._hist_years),
            dtype=float,
        )

        sim_config._hist_eq_returns = np.array(
            [
                0.10,
                0.20,
                -0.10,
                0.05,
                0.00,
            ],
            dtype=float,
        )

        sim_config._hist_bd_returns = np.zeros(
            len(sim_config._hist_years),
            dtype=float,
        )

        sim_config._hist_cs_returns = np.zeros(
            len(sim_config._hist_years),
            dtype=float,
        )

        sim_config._hist_re_returns = np.zeros(
            len(sim_config._hist_years),
            dtype=float,
        )

    monkeypatch.setattr(
        monteCarloEngine,
        "prepare_market_path_sampling",
        fake_prepare_market_path_sampling,
    )


def install_historical_paths(monkeypatch):
    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        assert sim_index == sim_config._active_historical_sim_index

        start_index = int(
            sim_config._hist_window_start_indices[sim_index]
        )

        end_index = start_index + years_to_simulate

        equity_returns = sim_config._hist_eq_returns[
            start_index:end_index
        ]

        return make_path(
            equity_returns=equity_returns,
        )

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )


def test_historical_mode_overrides_requested_simulation_count(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=2,
        monte_carlo_mode="rollingHistoricalWindows",
    )

    install_historical_preparation(
        monkeypatch,
        number_of_windows=3,
    )
    install_historical_paths(monkeypatch)

    results = run_core(
        config=config,
        num_sims=99,
    )

    assert results["total_assets"].shape == (
        3,
        3,
    )

    assert results["total_assets"][0] == pytest.approx(
        [
            100_000.0,
            110_000.0,
            132_000.0,
        ]
    )

    assert results["total_assets"][1] == pytest.approx(
        [
            100_000.0,
            120_000.0,
            108_000.0,
        ]
    )

    assert results["total_assets"][2] == pytest.approx(
        [
            100_000.0,
            90_000.0,
            94_500.0,
        ]
    )


def test_historical_window_year_metadata_is_stored(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=2,
        monte_carlo_mode="rollingHistoricalWindows",
    )

    install_historical_preparation(
        monkeypatch,
        number_of_windows=3,
    )
    install_historical_paths(monkeypatch)

    results = run_core(
        config=config,
        num_sims=1,
    )

    assert results["historical_window_start_year"] == (
        pytest.approx(
            [
                2000,
                2001,
                2002,
            ]
        )
    )

    assert results["historical_window_end_year"] == (
        pytest.approx(
            [
                2001,
                2002,
                2003,
            ]
        )
    )


def test_nonhistorical_mode_uses_default_historical_metadata(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=2,
        monte_carlo_mode="pathBasedAnnualSampling",
    )

    monkeypatch.setattr(
        monteCarloEngine,
        "prepare_market_path_sampling",
        lambda sim_config: None,
    )

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        lambda sim_config, years_to_simulate, sim_index=None: (
            make_path(
                equity_returns=[
                    0.0,
                    0.0,
                ],
            )
        ),
    )

    install_identity_sequence_risk(monkeypatch)

    results = run_core(
        config=config,
        num_sims=2,
    )

    assert results["historical_window_start_year"] == (
        pytest.approx(
            [
                -1,
                -1,
            ]
        )
    )

    assert results["historical_window_end_year"] == (
        pytest.approx(
            [
                -1,
                -1,
            ]
        )
    )


def test_historical_mode_rejects_zero_windows(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=2,
        monte_carlo_mode="rollingHistoricalWindows",
    )

    install_historical_preparation(
        monkeypatch,
        number_of_windows=0,
    )

    with pytest.raises(
        RuntimeError,
        match="prepared zero windows",
    ):
        run_core(
            config=config,
            num_sims=10,
        )


def test_historical_mode_can_disable_sequence_risk_overlay(
    monkeypatch,
):
    config = make_config(
        years_to_simulate=2,
        monte_carlo_mode="rollingHistoricalWindows",
    )

    config.sequence_risk_enabled = True
    config.disable_sequence_risk_for_historical = True

    install_historical_preparation(
        monkeypatch,
        number_of_windows=2,
    )
    install_historical_paths(monkeypatch)

    def unexpected_sequence_risk_call(*args, **kwargs):
        raise AssertionError(
            "Sequence-risk overlay should not run in historical mode"
        )

    monkeypatch.setattr(
        monteCarloEngine,
        "apply_sequence_risk_overlay",
        unexpected_sequence_risk_call,
    )

    results = run_core(
        config=config,
        num_sims=20,
    )

    assert results["sequence_risk_active"] == pytest.approx(
        [
            False,
            False,
        ]
    )

    assert results["sequence_risk_start_year"] == pytest.approx(
        [
            -1,
            -1,
        ]
    )

    assert results["sequence_risk_end_year"] == pytest.approx(
        [
            -1,
            -1,
        ]
    )