import numpy as np
import pytest
from tests.architectural_helpers import make_person, make_portfolio, make_simulation

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


def make_config(
    *,
    years_to_simulate=2,
    results_mode="risk_analysis",
    risk_analysis_mode="monte_carlo",
):
    config = make_simulation(
        years_to_simulate=years_to_simulate,
        results_mode=results_mode,
        sim_initial_allocation_mode="dont-rebalance",
        retirement_withdraw_dollars=0.0,
    )

    config.risk_analysis_mode = risk_analysis_mode
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
        risk_analysis_mode="historical_windows",
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
        risk_analysis_mode="historical_windows",
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
        risk_analysis_mode="monte_carlo",
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
        risk_analysis_mode="historical_windows",
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


def test_historical_mode_applies_sequence_risk_overlay(monkeypatch):
    config = make_config(
        years_to_simulate=2,
        risk_analysis_mode="historical_windows",
    )

    config.sequence_risk_enabled = True

    install_historical_preparation(
        monkeypatch,
        number_of_windows=2,
    )
    install_historical_paths(monkeypatch)

    calls = []

    def fake_sequence_risk_overlay(*, market_path, sim_config, years_to_simulate, withdrawal_start_year):
        calls.append(np.array(market_path["eq"], copy=True))
        adjusted = {key: np.array(value, copy=True) for key, value in market_path.items()}
        adjusted["eq"][1] = -0.50
        return adjusted, {
            "enabled": True,
            "applied": True,
            "start_year": 1,
            "end_year": 1,
            "length_years": 1,
            "timing": "Early downturn",
            "depth": "Moderate",
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "apply_sequence_risk_overlay",
        fake_sequence_risk_overlay,
    )

    results = run_core(
        config=config,
        num_sims=20,
    )

    assert len(calls) == 2
    assert results["sequence_risk_active"] == pytest.approx([True, True])
    assert results["sequence_risk_start_year"] == pytest.approx([1, 1])
    assert results["sequence_risk_end_year"] == pytest.approx([1, 1])
    assert results["total_assets"][:, 1] == pytest.approx([50_000.0, 50_000.0])

