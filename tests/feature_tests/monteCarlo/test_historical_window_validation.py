from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.sim.engines import monteCarloEngine


def make_historical_config(*, years_to_simulate=2, historical_window_mode="rolling_overlapping_all"):
    return SimpleNamespace(
        subplot_mode="monte_carlo",
        sim_type="portfolio_sim",
        monte_carlo_mode="rollingHistoricalWindows",
        use_correlated_returns=False,
        eq_mean=0.0,
        bd_mean=0.0,
        cs_mean=0.0,
        re_mean=0.0,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_std=0.0,
        years_to_simulate=years_to_simulate,
        historical_window_mode=historical_window_mode,
        historical_asset_returns_file="returns.csv",
        historical_inflation_file="inflation.csv",
    )


def install_historical_loaders(
    monkeypatch,
    *,
    return_years=(2000, 2001, 2002, 2003),
    inflation_years=None,
):
    return_years = np.asarray(return_years, dtype=int)
    if inflation_years is None:
        inflation_years = return_years
    inflation_years = np.asarray(inflation_years, dtype=int)

    historical_returns = {
        "years": return_years,
        "eq": np.arange(len(return_years), dtype=float) / 100.0,
        "bd": np.arange(len(return_years), dtype=float) / 200.0,
        "cs": np.arange(len(return_years), dtype=float) / 400.0,
        "re": np.arange(len(return_years), dtype=float) / 150.0,
    }
    historical_inflation = {
        "years": inflation_years,
        "inflation": np.arange(len(inflation_years), dtype=float) / 300.0,
    }

    monkeypatch.setattr(
        monteCarloEngine,
        "load_historical_asset_returns_csv",
        lambda filename: historical_returns,
    )
    monkeypatch.setattr(
        monteCarloEngine,
        "load_historical_inflation_csv",
        lambda filename: historical_inflation,
    )


def test_historical_returns_and_inflation_years_must_match_exactly(monkeypatch):
    config = make_historical_config()
    install_historical_loaders(
        monkeypatch,
        return_years=(2000, 2001, 2002),
        inflation_years=(2001, 2002, 2003),
    )

    with pytest.raises(ValueError) as exc_info:
        monteCarloEngine.prepare_market_path_sampling(config)

    assert str(exc_info.value) == (
        "Historical asset return years and historical inflation years must match exactly. "
        "Returns years: 2000..2002 (3 rows), "
        "Inflation years: 2001..2003 (3 rows)"
    )


def test_historical_horizon_must_be_positive(monkeypatch):
    config = make_historical_config(years_to_simulate=0)
    install_historical_loaders(monkeypatch)

    with pytest.raises(ValueError) as exc_info:
        monteCarloEngine.prepare_market_path_sampling(config)

    assert str(exc_info.value) == (
        "years_to_simulate must be > 0 for rolling historical windows"
    )


def test_historical_horizon_cannot_exceed_available_rows(monkeypatch):
    config = make_historical_config(years_to_simulate=4)
    install_historical_loaders(
        monkeypatch,
        return_years=(2000, 2001, 2002),
    )

    with pytest.raises(ValueError) as exc_info:
        monteCarloEngine.prepare_market_path_sampling(config)

    assert str(exc_info.value) == (
        "Historical data file has only 3 rows, but years_to_simulate is 4. "
        "Need at least as many historical years as the simulation horizon."
    )


def test_unsupported_historical_window_mode_is_rejected(monkeypatch):
    config = make_historical_config(historical_window_mode="non_overlapping")
    install_historical_loaders(monkeypatch)

    with pytest.raises(ValueError) as exc_info:
        monteCarloEngine.prepare_market_path_sampling(config)

    assert str(exc_info.value) == (
        "Unsupported historical_window_mode: non_overlapping"
    )


def test_overlapping_historical_window_count_and_start_indices_are_exact(monkeypatch):
    config = make_historical_config(years_to_simulate=3)
    install_historical_loaders(
        monkeypatch,
        return_years=(2000, 2001, 2002, 2003, 2004),
    )

    monteCarloEngine.prepare_market_path_sampling(config)

    assert config._hist_num_windows == 3
    np.testing.assert_array_equal(
        config._hist_window_start_indices,
        np.array([0, 1, 2], dtype=int),
    )
    np.testing.assert_array_equal(
        config._hist_years,
        np.array([2000, 2001, 2002, 2003, 2004], dtype=int),
    )


def test_historical_market_path_requires_sim_index():
    config = SimpleNamespace(
        _hist_window_start_indices=np.array([0], dtype=int),
        _hist_num_windows=1,
    )

    with pytest.raises(ValueError) as exc_info:
        monteCarloEngine._build_historical_market_path(
            config,
            years_to_simulate=2,
            sim_index=None,
        )

    assert str(exc_info.value) == (
        "sim_index is required for rollingHistoricalWindows mode"
    )


def test_historical_market_path_rejects_out_of_range_index():
    config = SimpleNamespace(
        _hist_window_start_indices=np.array([0, 1], dtype=int),
        _hist_num_windows=2,
    )

    with pytest.raises(IndexError) as negative_exc:
        monteCarloEngine._build_historical_market_path(
            config,
            years_to_simulate=2,
            sim_index=-1,
        )

    assert str(negative_exc.value) == (
        "Historical sim_index -1 is out of range for 2 available rolling windows."
    )

    with pytest.raises(IndexError) as upper_exc:
        monteCarloEngine._build_historical_market_path(
            config,
            years_to_simulate=2,
            sim_index=2,
        )

    assert str(upper_exc.value) == (
        "Historical sim_index 2 is out of range for 2 available rolling windows."
    )


def test_historical_inflation_path_rejects_unprepared_cache():
    config = SimpleNamespace(
        _hist_window_start_indices=None,
        _hist_num_windows=0,
    )

    with pytest.raises(RuntimeError) as exc_info:
        monteCarloEngine.build_historical_inflation_rate_path(
            config,
            years_to_simulate=2,
            sim_index=0,
        )

    assert str(exc_info.value) == (
        "Historical rolling-window data not prepared. "
        "Call prepare_market_path_sampling(sim_config) before simulation."
    )
