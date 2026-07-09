from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DummySimConfig:
    num_sims: int = 100
    annotate_plots: bool = False
    sim_rebalance: str = "None"
    output_csv: str = "None"


class DummyPerson:
    pass


class DummyPortfolio:
    pass


class DummyExpenses:
    pass


def _fake_pipeline_result():
    return {
        "portfolio_plot_data": "SIM_DATA",
        "years_list": [2025, 2026, 2027],
    }


def test_run_sim_portfolio_calls_pipeline_and_plot(monkeypatch):
    from src.warpsimlab.sim import run_sim_portfolio as mod

    captured = {"pipeline_kwargs": None, "plot_args": None}

    def fake_run_pipeline(*args, **kwargs):
        captured["pipeline_kwargs"] = kwargs
        return _fake_pipeline_result()

    def fake_plot(years_list, simulation_data, **kwargs):
        captured["plot_args"] = (years_list, simulation_data, kwargs)

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "plot_portfolio_projection", fake_plot, raising=True)

    sim_config = DummySimConfig()
    husband = DummyPerson()
    wife = DummyPerson()

    mod.run_sim_portfolio(
        DummyPortfolio(),
        DummyPortfolio(),
        husband,
        wife,
        DummyExpenses(),
        sim_config,
    )

    assert captured["pipeline_kwargs"] is not None
    assert captured["pipeline_kwargs"]["force_num_sims"] is None

    years_list, simulation_data, kwargs = captured["plot_args"]
    assert years_list == _fake_pipeline_result()["years_list"]
    assert simulation_data == _fake_pipeline_result()["portfolio_plot_data"]

    assert kwargs["sim_config"] is sim_config
    assert kwargs["annotate_plots"] == sim_config.annotate_plots
    assert kwargs["sim_rebalance_string"] == sim_config.sim_rebalance
    assert kwargs["husband"] is husband
    assert kwargs["wife"] is wife


def test_run_sim_portfolio_caps_num_sims_at_40000(monkeypatch):
    from src.warpsimlab.sim import run_sim_portfolio as mod

    captured = {"sim_config_seen": None, "force_num_sims": None, "plot_args": None}

    def fake_run_pipeline(*args, **kwargs):
        captured["sim_config_seen"] = args[5]
        captured["force_num_sims"] = kwargs.get("force_num_sims")
        return _fake_pipeline_result()

    def fake_plot(*args, **kwargs):
        captured["plot_args"] = (args, kwargs)

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "plot_portfolio_projection", fake_plot, raising=True)

    sim_config = DummySimConfig(num_sims=50000)

    mod.run_sim_portfolio(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
    )

    assert sim_config.num_sims == 50000
    assert captured["sim_config_seen"] is sim_config
    assert captured["force_num_sims"] is None
    assert captured["plot_args"] is not None


def test_run_sim_portfolio_does_not_show_limit_message_when_under_cap(monkeypatch):
    from src.warpsimlab.sim import run_sim_portfolio as mod

    captured = {"message": None}

    def fake_run_pipeline(*args, **kwargs):
        return _fake_pipeline_result()

    def fake_plot(*args, **kwargs):
        return None

    def fake_showinfo(title, msg):
        captured["message"] = (title, msg)

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "plot_portfolio_projection", fake_plot, raising=True)
    monkeypatch.setattr(mod.messagebox, "showinfo", fake_showinfo, raising=True)

    sim_config = DummySimConfig(num_sims=20000)

    mod.run_sim_portfolio(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
    )

    assert sim_config.num_sims == 20000
    assert captured["message"] is None


def test_run_sim_portfolio_writes_csv_and_prints_path(monkeypatch, capsys):
    from src.warpsimlab.sim import run_sim_portfolio as mod

    captured = {"csv_args": None}

    def fake_run_pipeline(*args, **kwargs):
        return _fake_pipeline_result()

    def fake_plot(*args, **kwargs):
        return None

    def fake_write_csv(*args, **kwargs):
        captured["csv_args"] = (args, kwargs)
        return "portfolio_results.csv"

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "plot_portfolio_projection", fake_plot, raising=True)
    monkeypatch.setattr(mod.io, "write_portfolio_results_csv", fake_write_csv, raising=True)

    sim_config = DummySimConfig(output_csv="Output")

    mod.run_sim_portfolio(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
    )

    args, kwargs = captured["csv_args"]

    assert args[0] == _fake_pipeline_result()["years_list"]
    assert args[1] == _fake_pipeline_result()["portfolio_plot_data"]
    assert args[2] is sim_config
    assert kwargs["prefix"] == "portfolio_simulation"

    out = capsys.readouterr().out
    assert "Portfolio simulation results written to:" in out
    assert "portfolio_results.csv" in out


def test_run_sim_portfolio_csv_returns_none_no_print(monkeypatch, capsys):
    from src.warpsimlab.sim import run_sim_portfolio as mod

    def fake_run_pipeline(*args, **kwargs):
        return _fake_pipeline_result()

    def fake_plot(*args, **kwargs):
        return None

    def fake_write_csv(*args, **kwargs):
        return None

    monkeypatch.setattr(mod, "run_pipeline", fake_run_pipeline, raising=True)
    monkeypatch.setattr(mod, "plot_portfolio_projection", fake_plot, raising=True)
    monkeypatch.setattr(mod.io, "write_portfolio_results_csv", fake_write_csv, raising=True)

    sim_config = DummySimConfig(output_csv="Output")

    mod.run_sim_portfolio(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
    )

    out = capsys.readouterr().out
    assert "Portfolio simulation results written to:" not in out
