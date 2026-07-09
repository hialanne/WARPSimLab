# test_run_sim_income.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np

import pytest


@dataclass
class DummySimConfig:
    years_to_simulate: int = 5
    output_csv: str = "None"  # or "Output"
    sim_type: str = "income_sim"


class DummyPerson:
    pass


class DummyPortfolio:
    pass


class DummyExpenses:
    pass


def _fake_pipeline_result() -> Dict[str, Any]:
    return {
        "years": 5,
        "years_list": np.array([0, 1, 2, 3, 4, 5]),
        "net_profit": np.array([0, 10, 20, 30, 40, 50]),
        "net_income": np.array([0, 100, 110, 120, 130, 140]),
        "breakdown_by_class": {
            "work": np.array([0, 1, 2, 3, 4, 5]),
            "pension": np.array([0, 10, 10, 10, 10, 10]),
            "annuity": np.array([0, 0, 0, 0, 0, 0]),
            "ss": np.array([0, 20, 20, 20, 20, 20]),
            "special_income": np.array([0, 0, 0, 0, 0, 0]),

            "rmd": np.array([0, 0, 0, 0, 0, 0]),
            "withdrawal": np.array([0, 0, 0, 0, 0, 0]),
            "bond_interest": np.array([0, 0, 0, 0, 0, 0]),
            "cash_interest": np.array([0, 0, 0, 0, 0, 0]),
            "qualified_dividends": np.array([0, 0, 0, 0, 0, 0]),
        },
        "taxes": np.array([0, 5, 5, 5, 5, 5]),
        "expense_amt": np.array([0, 50, 50, 50, 50, 50]),
    }

def test_run_sim_income_calls_pipeline_and_plot(monkeypatch):
    """
    Verifies:
      - run_pipeline called with force_num_sims=1
      - plot_yearly_income called with mapped pipeline outputs
      - no CSV written when output_csv != "Output"
    """
    # Import inside test so monkeypatch applies to module namespace reliably
    from src.warpsimlab.sim import run_sim_income as mod

    captured = {"pipeline_kwargs": None, "plot_kwargs": None, "csv_called": False}

    def fake_run_pipeline(*args, **kwargs):
        captured["pipeline_kwargs"] = kwargs
        return _fake_pipeline_result()

    def fake_plot_yearly_income(years, **kwargs):
        captured["plot_kwargs"] = {"years": years, **kwargs}

    def fake_write_income_results_csv(*args, **kwargs):
        captured["csv_called"] = True
        return "should_not_be_used.csv"

    # Patch dependencies in the module under test
    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "plot_yearly_income", fake_plot_yearly_income, raising=True)
    # io is imported as: from .plots import io
    monkeypatch.setattr(mod.io, "write_income_results_csv", fake_write_income_results_csv, raising=True)

    sim_config = DummySimConfig(output_csv="None")
    husband = DummyPerson()
    wife = DummyPerson()

    mod.run_sim_income(DummyPortfolio(), DummyPortfolio(), husband, wife, DummyExpenses(), sim_config)

    assert captured["pipeline_kwargs"] is not None
    assert captured["pipeline_kwargs"].get("force_num_sims") == 1

    assert captured["plot_kwargs"] is not None
    # Years should be p["years"] (an int in this module)
    assert captured["plot_kwargs"]["years"] == 5
    np.testing.assert_allclose(
        captured["plot_kwargs"]["net_profit"],
        _fake_pipeline_result()["net_profit"],
    )

    p = _fake_pipeline_result()
    expected_plot_total = (
        p["breakdown_by_class"]["work"]
        + p["breakdown_by_class"]["pension"]
        + p["breakdown_by_class"]["annuity"]
        + p["breakdown_by_class"]["ss"]
        + p["breakdown_by_class"]["special_income"]
    )

    np.testing.assert_allclose(captured["plot_kwargs"]["net_income"], expected_plot_total)

    p = _fake_pipeline_result()
    actual_breakdown = captured["plot_kwargs"]["breakdown"]

    assert set(actual_breakdown.keys()) == {
        "work",
        "pension",
        "annuity",
        "ss",
        "special_income",
    }

    for key in actual_breakdown:
        np.testing.assert_allclose(
            actual_breakdown[key],
            p["breakdown_by_class"][key],
        )

    np.testing.assert_allclose(
        captured["plot_kwargs"]["taxes"],
        _fake_pipeline_result()["taxes"],
    )

    np.testing.assert_allclose(
        captured["plot_kwargs"]["expenses"],
        _fake_pipeline_result()["expense_amt"],
    )

    assert captured["plot_kwargs"]["husband"] is husband
    assert captured["plot_kwargs"]["wife"] is wife
    assert captured["plot_kwargs"]["sim_config"] is sim_config

    assert captured["csv_called"] is False


def test_run_sim_income_writes_csv_and_prints_path(monkeypatch, capsys):
    """
    Verifies:
      - when sim_config.output_csv == "Output", io.write_income_results_csv is called
      - if it returns a path, the module prints the path
    """
    from src.warpsimlab.sim import run_sim_income as mod

    captured = {"csv_args": None, "csv_kwargs": None}

    def fake_run_pipeline(*args, **kwargs):
        return _fake_pipeline_result()

    def fake_plot_yearly_income(*args, **kwargs):
        # plotting side effects not under test here
        return None

    def fake_write_income_results_csv(*args, **kwargs):
        captured["csv_args"] = args
        captured["csv_kwargs"] = kwargs
        return "income_simulation_results.csv"

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "plot_yearly_income", fake_plot_yearly_income, raising=True)
    monkeypatch.setattr(mod.io, "write_income_results_csv", fake_write_income_results_csv, raising=True)

    sim_config = DummySimConfig(output_csv="Output")
    husband = DummyPerson()
    wife = DummyPerson()

    mod.run_sim_income(DummyPortfolio(), DummyPortfolio(), husband, wife, DummyExpenses(), sim_config)

    assert captured["csv_args"] is not None
    # Positional args map to: years_list, net_income, net_profit, taxes, breakdown_by_class, sim_config
    p = _fake_pipeline_result()
    assert list(captured["csv_args"][0]) == list(p["years_list"])
    assert list(captured["csv_args"][1]) == list(p["net_income"])
    assert list(captured["csv_args"][2]) == list(p["net_profit"])
    assert list(captured["csv_args"][3]) == list(p["taxes"])
    actual_breakdown = captured["csv_args"][4]
    expected_breakdown = p["breakdown_by_class"]

    assert set(actual_breakdown.keys()) == set(expected_breakdown.keys())

    for key in expected_breakdown:
        np.testing.assert_allclose(actual_breakdown[key], expected_breakdown[key])

    assert captured["csv_args"][5] is sim_config

    assert captured["csv_kwargs"]["prefix"] == "income_simulation"

    out = capsys.readouterr().out
    assert "Income simulation results written to:" in out
    assert "income_simulation_results.csv" in out


def test_run_sim_income_csv_returns_none_no_print(monkeypatch, capsys):
    """
    Verifies:
      - when CSV writer returns None/falsey, no 'written to' message is printed
    """
    from src.warpsimlab.sim import run_sim_income as mod

    def fake_run_pipeline(*args, **kwargs):
        return _fake_pipeline_result()

    def fake_plot_yearly_income(*args, **kwargs):
        return None

    def fake_write_income_results_csv(*args, **kwargs):
        return None

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "plot_yearly_income", fake_plot_yearly_income, raising=True)
    monkeypatch.setattr(mod.io, "write_income_results_csv", fake_write_income_results_csv, raising=True)

    sim_config = DummySimConfig(output_csv="Output")
    mod.run_sim_income(DummyPortfolio(), DummyPortfolio(), DummyPerson(), DummyPerson(), DummyExpenses(), sim_config)

    out = capsys.readouterr().out
    assert "Income simulation results written to:" not in out