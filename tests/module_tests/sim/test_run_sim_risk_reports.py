from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from src.warpsimlab.sim import run_sim_risk_reports as mod


def test_failure_statistics_counts_first_depletion_even_after_recovery():
    assets = np.array([[100, 110, 120], [100, 0, 10], [100, 20, -1], [0, 10, 20]])
    stats = mod._build_failure_statistics(assets, [2025, 2026, 2027])
    assert stats == {"Scenario Count": 4, "Portfolio Survived Count": 1,
        "Portfolio Depleted Count": 3, "Portfolio Survival Rate": 25,
        "Simulated Shortfall Rate": 75, "Earliest Portfolio Depletion Year": 2025,
        "Median Portfolio Depletion Year": 2026, "Latest Portfolio Depletion Year": 2027}
    assert mod._first_failure_year(np.array([1, 0]), []) == 1
    assert mod._build_failure_statistics([[1, 2]], [2025, 2026])["Median Portfolio Depletion Year"] is None
    assert mod._rate(0, 0) == 0


def test_percentiles_use_each_year_across_paths():
    rows = mod._build_percentile_table([[0, 100], [100, 200]], [2025, 2026])
    assert rows == [
        {"Year": 2025, "10th Percentile": 10, "25th Percentile": 25, "Median": 50, "75th Percentile": 75, "90th Percentile": 90},
        {"Year": 2026, "10th Percentile": 110, "25th Percentile": 125, "Median": 150, "75th Percentile": 175, "90th Percentile": 190}]


def test_historical_ranking_breaks_depleted_ties_by_first_failure():
    assets = [[100, 0, 0], [100, 50, 0], [100, 100, 300], [100, 100, 200]]
    core = {"historical_window_start_year": [1929, 1930, 1980, -1],
            "historical_window_end_year": [1931, 1932, 1982, -1]}
    insights = mod._build_historical_insights(core, assets, {"Simulated Shortfall Rate": 50})
    assert insights["Best Indices"] == [2, 1, 0]
    assert insights["Worst Indices"] == [0, 1, 2]
    assert insights["Worst Retirement Years"][0]["Retirement Start Year"] == 1929
    assert insights["Commentary"]
    assert mod._build_historical_insights({}, assets, {}) == {}


@pytest.mark.parametrize("runner,mode", [(mod.run_sim_monte_carlo_risk_report, "monte_carlo"), (mod.run_sim_historical_window_risk_report, "historical_windows")])
@pytest.mark.parametrize("failure_stage", [None, "pipeline", "report"])
def test_risk_runner_temporary_modes_restored(monkeypatch, scenario_builders, runner, mode, failure_stage):
    from src.warpsimlab.sim import simulation
    config = scenario_builders.make_config(include_realestate=True, calculate_simulated_shortfall_rate=True,
                                          show_simulated_shortfall_rate=True, sim_type="income_sim")
    before = vars(config).copy()
    def pipeline(*args, **kwargs):
        assert config.results_mode == "risk_analysis"
        assert config.sim_type == "portfolio_sim"
        assert config.risk_analysis_mode == mode
        assert config.include_realestate is False
        assert config.calculate_simulated_shortfall_rate is False
        assert config.show_simulated_shortfall_rate is False
        assert kwargs == {"force_num_sims": None}
        if failure_stage == "pipeline":
            raise RuntimeError("pipeline failed")
        return {"pipeline": True}
    def generate(result, actual_config, husband, wife, **kwargs):
        assert result == {"pipeline": True}
        assert actual_config is config
        assert kwargs["risk_analysis_mode"] == mode
        if failure_stage == "report":
            raise RuntimeError("report failed")
        return "risk.html"
    monkeypatch.setattr(simulation, "run_pipeline", pipeline)
    monkeypatch.setattr(mod, "_build_and_generate_risk_report", generate)
    if failure_stage:
        with pytest.raises(RuntimeError, match=failure_stage):
            runner(None, None, None, None, None, config)
    else:
        assert runner(None, None, None, None, None, config) == "risk.html"
    assert vars(config) == before


def test_report_assembly_selects_options_and_effective_horizon(monkeypatch, scenario_builders):
    config = scenario_builders.make_config(years_to_simulate=30,
        report_options={"monte_carlo_risk": {"include_csv": True}})
    pipeline = {"core": {"total_assets": np.array([[100, 200], [100, 0]]), "year": np.array([[2025, 2026], [2025, 2026]])}}
    monkeypatch.setattr(mod, "_build_risk_plot_assets", Mock(return_value={}))
    generate = Mock(return_value="risk.html")
    monkeypatch.setattr(mod, "generate_risk_report", generate)
    assert mod._build_and_generate_risk_report(pipeline, config, None, None, risk_analysis_mode="monte_carlo") == "risk.html"
    report = generate.call_args.args[0]
    assert report.report_options == {"include_csv": True}
    assert report.analysis_summary["Years Simulated"] == 1
    assert report.analysis_summary["Median Ending Portfolio"] == 100
    assert report.failure_statistics["Simulated Shortfall Rate"] == 50
    assert report.simulation_snapshot["Configured Years"] == 30


def test_plot_failures_become_warnings_and_use_safe_asset_path(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "_get_report_output_folder", lambda: str(tmp_path))
    portfolio = Mock(side_effect=OSError("plot unavailable"))
    historical = Mock(side_effect=ValueError("missing history"))
    monkeypatch.setattr(mod, "save_portfolio_projection_report_plot", portfolio)
    monkeypatch.setattr(mod, "save_historical_window_highlight_report_plot", historical)
    warnings = []
    result = mod._build_risk_plot_assets({"years_list": [2025], "portfolio_plot_data": {}, "core": {"total_assets": [[1]]}},
        {"Report ID": "report:/id"}, SimpleNamespace(risk_analysis_mode="historical_windows"), None, None, warnings, {"Best Indices": [0]})
    assert result == {}
    assert len(warnings) == 2
    assert "plot unavailable" in warnings[0] and "missing history" in warnings[1]
    assert portfolio.call_args.kwargs["output_folder"] == str(tmp_path / "risk_report_report__id_assets")
