# test_run_sim_summary.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pytest


@dataclass
class DummySimConfig:
    output_csv: str = "None"  # or "Output"


class DummyPerson:
    pass


class DummyPortfolio:
    pass


class DummyExpenses:
    pass


def _fake_pipeline_result() -> Dict[str, Any]:
    return {
        "summary_results": {"year": [0, 1], "net_income": [100, 110]},
    }


def test_run_sim_summary_calls_pipeline_and_creates_dialog(monkeypatch):
    """
    Verifies:
      - run_pipeline called with force_num_sims=1
      - SummaryDialog instantiated with (summary_results, husband, wife, sim_config, title="Simulation Summary")
      - no CSV write when output_csv != "Output"
      - returns summary_results
    """
    from src.warpsimlab.sim import run_sim_summary as mod

    captured = {
        "pipeline_kwargs": None,
        "dialog_args": None,
        "dialog_kwargs": None,
        "csv_called": False,
    }

    def fake_run_pipeline(*args, **kwargs):
        captured["pipeline_kwargs"] = kwargs
        return _fake_pipeline_result()

    class FakeSummaryDialog:
        def __init__(self, *args, **kwargs):
            captured["dialog_args"] = args
            captured["dialog_kwargs"] = kwargs

    def fake_write_summary_results_csv(*args, **kwargs):
        captured["csv_called"] = True
        return "should_not_be_used.csv"

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "SummaryDialog", FakeSummaryDialog, raising=True)
    monkeypatch.setattr(mod.io, "write_summary_results_csv", fake_write_summary_results_csv, raising=True)

    sim_config = DummySimConfig(output_csv="None")
    husband = DummyPerson()
    wife = DummyPerson()

    result = mod.run_sim_summary(DummyPortfolio(), DummyPortfolio(), husband, wife, DummyExpenses(), sim_config)

    assert captured["pipeline_kwargs"] is not None
    assert captured["pipeline_kwargs"].get("force_num_sims") == 1

    assert captured["dialog_args"] is not None
    # Expected positional args: (summary_results, husband, wife, sim_config)
    assert captured["dialog_args"][0] == _fake_pipeline_result()["summary_results"]
    assert captured["dialog_args"][1] is husband
    assert captured["dialog_args"][2] is wife
    assert captured["dialog_args"][3] is sim_config
    assert captured["dialog_kwargs"] == {"title": "Simulation Summary"}

    assert captured["csv_called"] is False
    assert result == _fake_pipeline_result()["summary_results"]


def test_run_sim_summary_writes_csv_and_prints_path(monkeypatch, capsys):
    """
    Verifies:
      - when output_csv == "Output", io.write_summary_results_csv called with prefix="summary_simulation"
      - prints when writer returns a truthy path
      - returns summary_results
    """
    from src.warpsimlab.sim import run_sim_summary as mod

    captured = {"csv_args": None, "csv_kwargs": None}

    def fake_run_pipeline(*args, **kwargs):
        return _fake_pipeline_result()

    class FakeSummaryDialog:
        def __init__(self, *args, **kwargs):
            pass

    def fake_write_summary_results_csv(*args, **kwargs):
        captured["csv_args"] = args
        captured["csv_kwargs"] = kwargs
        return "summary_results.csv"

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "SummaryDialog", FakeSummaryDialog, raising=True)
    monkeypatch.setattr(mod.io, "write_summary_results_csv", fake_write_summary_results_csv, raising=True)

    sim_config = DummySimConfig(output_csv="Output")
    result = mod.run_sim_summary(DummyPortfolio(), DummyPortfolio(), DummyPerson(), DummyPerson(), DummyExpenses(), sim_config)

    assert captured["csv_args"] is not None
    assert captured["csv_args"][0] == _fake_pipeline_result()["summary_results"]
    assert captured["csv_args"][1] is sim_config
    assert captured["csv_kwargs"]["prefix"] == "summary_simulation"

    out = capsys.readouterr().out
    assert "Simulation results written to:" in out
    assert "summary_results.csv" in out

    assert result == _fake_pipeline_result()["summary_results"]


def test_run_sim_summary_csv_returns_none_no_print(monkeypatch, capsys):
    """
    Verifies:
      - when CSV writer returns None/falsey, no 'written to' message is printed
    """
    from src.warpsimlab.sim import run_sim_summary as mod

    def fake_run_pipeline(*args, **kwargs):
        return _fake_pipeline_result()

    class FakeSummaryDialog:
        def __init__(self, *args, **kwargs):
            pass

    def fake_write_summary_results_csv(*args, **kwargs):
        return None

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "SummaryDialog", FakeSummaryDialog, raising=True)
    monkeypatch.setattr(mod.io, "write_summary_results_csv", fake_write_summary_results_csv, raising=True)

    sim_config = DummySimConfig(output_csv="Output")
    mod.run_sim_summary(DummyPortfolio(), DummyPortfolio(), DummyPerson(), DummyPerson(), DummyExpenses(), sim_config)

    out = capsys.readouterr().out
    assert "Simulation results written to:" not in out