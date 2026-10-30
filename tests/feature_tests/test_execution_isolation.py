"""Full-run reproducibility and standalone-versus-batch financial isolation."""

import copy

import numpy as np
import pytest

from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.simulation import run_pipeline
from tests.architectural_helpers import (
    assert_tree_equal, core_row, make_execution_case, user_config_tree,
)


@pytest.mark.parametrize("correlated", [False, True])
@pytest.mark.parametrize("expense_mode", [False, True])
def test_complete_seeded_runs_reproduce_after_reuse_and_intervening_seed(
    monkeypatch, correlated, expense_mode,
):
    # There is currently no per-config seed API: control the existing module
    # constant before real preparation, not config._mc_rng after preparation.
    monkeypatch.setattr(monteCarloEngine, "MONTE_CARLO_SEED", 4201)
    options = dict(results_mode="risk_analysis", use_correlated_returns=correlated,
                   always_use_expense_mode=expense_mode)
    case = make_execution_case(**options)
    before = user_config_tree(case["sim_config"])
    first = run_pipeline(**case)
    saved = copy.deepcopy(first["core"])
    repeat = run_pipeline(**case)
    fresh = run_pipeline(**make_execution_case(**options))
    assert_tree_equal(repeat["core"], saved)
    assert_tree_equal(fresh["core"], saved)
    assert_tree_equal(repeat["summary_results"], first["summary_results"])
    assert_tree_equal(fresh["portfolio_plot_data"].percentiles, first["portfolio_plot_data"].percentiles)
    monkeypatch.setattr(monteCarloEngine, "MONTE_CARLO_SEED", 4202)
    different = run_pipeline(**case)
    assert not np.array_equal(different["core"]["total_assets"], saved["total_assets"])
    monkeypatch.setattr(monteCarloEngine, "MONTE_CARLO_SEED", 4201)
    assert_tree_equal(run_pipeline(**case)["core"], saved)
    assert_tree_equal(first["core"], saved, "earlier results after later runs")
    assert_tree_equal(user_config_tree(case["sim_config"]), before)
    # Reproducible does not mean accidentally repeating the same path.
    assert not np.array_equal(saved["total_assets"][0], saved["total_assets"][1])


@pytest.mark.parametrize("expense_mode", [False, True])
@pytest.mark.parametrize("correlated", [False, True])
def test_captured_market_paths_match_independent_real_financial_execution(
    monkeypatch, expense_mode, correlated,
):
    paths = []
    original_generate = monteCarloEngine.generate_market_path

    def capture(config, years_to_simulate, sim_index=None):
        path = original_generate(config, years_to_simulate, sim_index=sim_index)
        paths.append(copy.deepcopy(path))
        return path

    monkeypatch.setattr(monteCarloEngine, "generate_market_path", capture)
    case = make_execution_case(
        results_mode="risk_analysis", always_use_expense_mode=expense_mode,
        use_correlated_returns=correlated,
    )
    combined = run_pipeline(**case)["core"]
    assert len(paths) == 3
    assert not np.array_equal(paths[0]["eq"], paths[1]["eq"])
    saved_paths = copy.deepcopy(paths)
    # Replay only the market input at the existing seam. Preparation and every
    # financial engine remain real. This asserts no RNG path-order guarantee.
    # Reuse the batch's config in reverse path order to exercise stale caches.
    for index in [2, 1, 0]:
        def replay(config, years_to_simulate, sim_index=None):
            return copy.deepcopy(paths[index])

        monkeypatch.setattr(monteCarloEngine, "generate_market_path", replay)
        isolated = run_pipeline(**case, force_num_sims=1)["core"]
        assert_tree_equal(isolated, core_row(combined, index), f"path {index}")
    assert_tree_equal(paths, saved_paths, "captured paths remain unchanged")
    assert np.any(combined["magi"] > 0)
    assert np.any(combined["irmaa"] > 0)
    assert np.any(combined["survivor_state"])
    assert np.any(combined["hsa_total_contributions"] > 0)
    if not expense_mode:
        assert np.any(combined["breakdown_by_class"]["withdrawal"] > 0)


@pytest.fixture
def historical_inputs(monkeypatch):
    years = np.arange(2000, 2010)
    returns = dict(
        years=years, eq=np.array([-0.35, 0.15, 0.20, -0.05, 0.08, 0.04, -0.10, 0.10, 0.07, -0.08]),
        bd=np.array([0.06, -0.02, 0.03, 0.04, -0.01, 0.02, 0.05, 0.01, -0.03, 0.04]),
        cs=np.linspace(0.01, 0.03, 10), re=np.linspace(-0.10, 0.10, 10),
    )
    inflation = dict(years=years.copy(), inflation=np.array([0.02, 0.08, -0.01, 0.03, 0.04,
                                                          0.01, 0.06, 0.02, 0.03, 0.0]))
    loads = dict(returns=0, inflation=0)

    def load_returns(filename):
        loads["returns"] += 1
        return returns

    def load_inflation(filename):
        loads["inflation"] += 1
        return inflation

    monkeypatch.setattr(monteCarloEngine, "load_historical_asset_returns_csv", load_returns)
    monkeypatch.setattr(monteCarloEngine, "load_historical_inflation_csv", load_inflation)
    return returns, inflation, loads


@pytest.mark.parametrize("expense_mode", [False, True])
@pytest.mark.parametrize("inflation_mode", ["nominal", "real"])
def test_historical_windows_match_isolated_selection_and_survive_config_reuse(
    historical_inputs, expense_mode, inflation_mode,
):
    returns, inflation, loads = historical_inputs
    source_before = copy.deepcopy((returns, inflation))
    options = dict(results_mode="risk_analysis", risk_analysis_mode="historical_windows",
                   always_use_expense_mode=expense_mode, inflation_mode=inflation_mode)
    case = make_execution_case(**options)
    config = case["sim_config"]
    before = user_config_tree(config)
    combined = run_pipeline(**case)["core"]
    assert loads == dict(returns=1, inflation=1)  # Load per run, not per path.
    assert combined["historical_window_start_year"].tolist() == [2000, 2001, 2002]
    assert not np.array_equal(combined["total_assets"][0], combined["total_assets"][1])
    assert not np.array_equal(combined["magi"][0], combined["magi"][1])
    # Selection is an existing supported interface; no private window-index patch.
    for index in [2, 0, 1]:
        year = 2000 + index
        selected_case = make_execution_case(
            **options, historical_window_start_year=year, historical_window_stop_year=year,
        )
        isolated = run_pipeline(**selected_case)["core"]
        repeated = run_pipeline(**selected_case)["core"]
        assert_tree_equal(isolated, core_row(combined, index), f"window {year}")
        assert_tree_equal(repeated, isolated, f"reused selected window {year}")
    assert_tree_equal(run_pipeline(**case)["core"], combined, "combined rerun after standalone runs")
    assert_tree_equal(user_config_tree(config), before, "historical user configuration")
    assert_tree_equal((returns, inflation), source_before, "loader-owned source data")


def test_reused_historical_config_can_narrow_window_selection(historical_inputs):
    options = dict(results_mode="risk_analysis", risk_analysis_mode="historical_windows")
    case = make_execution_case(**options)
    combined = run_pipeline(**case)["core"]
    selected = run_pipeline(**make_execution_case(
        **options, historical_window_start_year=2002, historical_window_stop_year=2002,
    ))["core"]
    assert_tree_equal(selected, core_row(combined, 2))
    case["sim_config"].historical_window_start_year = 2002
    case["sim_config"].historical_window_stop_year = 2002
    assert_tree_equal(run_pipeline(**case)["core"], selected)
