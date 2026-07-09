# test_run_sim_operating_balance.py

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict

import numpy as np
import pytest


@dataclass
class DummySimConfig:
    years_to_simulate: int = 5
    output_csv: str = "None"  # or "Output"


class DummyPerson:
    pass


class DummyPortfolio:
    pass


class DummyExpenses:
    pass


def _fake_portfolio_plot_data(median_series):
    # Matches access pattern in module:
    # portfolio_plot_data.percentiles["median"]
    return SimpleNamespace(percentiles={"median": list(median_series)})


def _fake_pipeline_result(net_profit, years, median_series) -> Dict[str, Any]:
    return {
        "years": years,
        "years_list": list(range(0, years + 1)),
        "net_profit": list(net_profit),
        "portfolio_plot_data": _fake_portfolio_plot_data(median_series),
    }


def test_run_sim_operating_balance_calls_pipeline_and_plot_and_computes_cumsum(monkeypatch):
    """
    Verifies:
      - run_pipeline called with force_num_sims=1
      - operating_balance[0] == 0 and operating_balance[1:] == cumsum(net_profit[1:])
      - portfolio_value taken from portfolio_plot_data.percentiles["median"]
      - no CSV attempt when output_csv != "Output"
    """
    from src.warpsimlab.sim import run_sim_operating_balance as mod

    captured = {"pipeline_kwargs": None, "plot_kwargs": None, "csv_called": False}

    net_profit = np.array([0, 10, -2, 5, 0, 7], dtype=float)  # years=5 -> len=6
    years = 5
    median_series = [100, 110, 120, 130, 140, 150]

    def fake_run_pipeline(*args, **kwargs):
        captured["pipeline_kwargs"] = kwargs
        return _fake_pipeline_result(net_profit, years, median_series)

    def fake_plot_operating_balance(**kwargs):
        captured["plot_kwargs"] = kwargs

    def fake_write_operating_balance_results_csv(*args, **kwargs):
        captured["csv_called"] = True
        return "should_not_be_used.csv"

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "plot_operating_balance", fake_plot_operating_balance, raising=True)
    monkeypatch.setattr(mod.io, "write_operating_balance_results_csv", fake_write_operating_balance_results_csv, raising=True)

    sim_config = DummySimConfig(output_csv="None")
    husband = DummyPerson()
    wife = DummyPerson()

    mod.run_sim_operating_balance(DummyPortfolio(), DummyPortfolio(), husband, wife, DummyExpenses(), sim_config)

    assert captured["pipeline_kwargs"] is not None
    assert captured["pipeline_kwargs"].get("force_num_sims") == 1

    assert captured["plot_kwargs"] is not None

    # Inputs passed through
    assert captured["plot_kwargs"]["years_to_simulate"] == years
    np.testing.assert_allclose(captured["plot_kwargs"]["net_profit"], net_profit)

    # Operating balance definition in module:
    # operating_balance[0]=0; operating_balance[1:]=cumsum(net_profit[1:])
    expected_ob = np.zeros_like(net_profit, dtype=float)
    expected_ob[1:] = np.cumsum(net_profit[1:])
    np.testing.assert_allclose(captured["plot_kwargs"]["operating_balance"], expected_ob)

    # Portfolio value is median series as float array
    np.testing.assert_allclose(
        captured["plot_kwargs"]["portfolio_value"],
        np.array(median_series, dtype=float),
    )

    assert captured["plot_kwargs"]["husband"] is husband
    assert captured["plot_kwargs"]["wife"] is wife
    assert captured["plot_kwargs"]["sim_config"] is sim_config

    assert captured["csv_called"] is False


def test_run_sim_operating_balance_len_one_net_profit_skips_cumsum(monkeypatch):
    """
    Covers the branch: if len(net_profit) <= 1, operating_balance stays zeros_like.
    """
    from src.warpsimlab.sim import run_sim_operating_balance as mod

    captured = {"plot_kwargs": None}

    net_profit = np.array([42.0], dtype=float)  # len == 1
    years = 0
    median_series = [999]

    def fake_run_pipeline(*args, **kwargs):
        return _fake_pipeline_result(net_profit, years, median_series)

    def fake_plot_operating_balance(**kwargs):
        captured["plot_kwargs"] = kwargs

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "plot_operating_balance", fake_plot_operating_balance, raising=True)

    sim_config = DummySimConfig(output_csv="None")
    mod.run_sim_operating_balance(DummyPortfolio(), DummyPortfolio(), DummyPerson(), DummyPerson(), DummyExpenses(), sim_config)

    assert captured["plot_kwargs"] is not None
    expected_ob = np.zeros_like(net_profit, dtype=float)
    np.testing.assert_allclose(captured["plot_kwargs"]["operating_balance"], expected_ob)


def test_run_sim_operating_balance_writes_csv_and_prints_path(monkeypatch, capsys):
    """
    Verifies:
      - when output_csv == "Output", attempts to call io.write_operating_balance_results_csv
      - prints when writer returns a truthy path
    """
    from src.warpsimlab.sim import run_sim_operating_balance as mod

    captured = {"csv_args": None, "csv_kwargs": None}

    net_profit = np.array([0, 1, 2], dtype=float)
    years = 2
    median_series = [10, 11, 12]

    def fake_run_pipeline(*args, **kwargs):
        return _fake_pipeline_result(net_profit, years, median_series)

    def fake_plot_operating_balance(**kwargs):
        return None

    def fake_write_operating_balance_results_csv(*args, **kwargs):
        captured["csv_args"] = args
        captured["csv_kwargs"] = kwargs
        return "operating_balance_results.csv"

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "plot_operating_balance", fake_plot_operating_balance, raising=True)
    monkeypatch.setattr(mod.io, "write_operating_balance_results_csv", fake_write_operating_balance_results_csv, raising=True)

    sim_config = DummySimConfig(output_csv="Output")
    mod.run_sim_operating_balance(DummyPortfolio(), DummyPortfolio(), DummyPerson(), DummyPerson(), DummyExpenses(), sim_config)

    # Positional args in module:
    # years_list, net_profit, operating_balance, sim_config, prefix=...
    assert captured["csv_args"] is not None
    p = _fake_pipeline_result(net_profit, years, median_series)

    assert list(captured["csv_args"][0]) == list(p["years_list"])
    np.testing.assert_allclose(captured["csv_args"][1], net_profit)

    expected_ob = np.zeros_like(net_profit, dtype=float)
    expected_ob[1:] = np.cumsum(net_profit[1:])
    np.testing.assert_allclose(captured["csv_args"][2], expected_ob)

    assert captured["csv_args"][3] is sim_config
    assert captured["csv_kwargs"]["prefix"] == "operating_balance_simulation"

    out = capsys.readouterr().out
    assert "Operating balance simulation results written to:" in out
    assert "operating_balance_results.csv" in out


def test_run_sim_operating_balance_output_csv_writer_missing_is_silent(monkeypatch, capsys):
    """
    Covers the AttributeError handler around io.write_operating_balance_results_csv.
    If the writer is absent, the module should silently skip.
    """
    from src.warpsimlab.sim import run_sim_operating_balance as mod

    net_profit = np.array([0, 1], dtype=float)
    years = 1
    median_series = [10, 11]

    def fake_run_pipeline(*args, **kwargs):
        return _fake_pipeline_result(net_profit, years, median_series)

    def fake_plot_operating_balance(**kwargs):
        return None

    # Remove attribute so access raises AttributeError inside the try:
    monkeypatch.delattr(mod.io, "write_operating_balance_results_csv", raising=False)

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "plot_operating_balance", fake_plot_operating_balance, raising=True)

    sim_config = DummySimConfig(output_csv="Output")
    mod.run_sim_operating_balance(DummyPortfolio(), DummyPortfolio(), DummyPerson(), DummyPerson(), DummyExpenses(), sim_config)

    out = capsys.readouterr().out
    assert "Operating balance simulation results written to:" not in out