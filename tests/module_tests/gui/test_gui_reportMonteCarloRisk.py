from __future__ import annotations

from src.warpsimlab.gui.gui_reportMonteCarloRisk import (
    MonteCarloRiskReportFrame,
)


def test_class_constants_identify_monte_carlo_risk_report():
    assert MonteCarloRiskReportFrame.REPORT_NAME == "Monte Carlo Risk Report"
    assert MonteCarloRiskReportFrame.RUN_SIM_TYPE == "monte_carlo_risk_report"


def test_description_and_method_note_are_monte_carlo_specific():
    assert "Monte Carlo Risk Report" in MonteCarloRiskReportFrame.DESCRIPTION
    assert "report contents only" in MonteCarloRiskReportFrame.DESCRIPTION

    assert "number of simulations" in MonteCarloRiskReportFrame.METHOD_NOTE
    assert "correlation" in MonteCarloRiskReportFrame.METHOD_NOTE
    assert "sampling mode" in MonteCarloRiskReportFrame.METHOD_NOTE
    assert "Simulation" in MonteCarloRiskReportFrame.METHOD_NOTE


def test_default_options_include_expected_general_sections():
    options = MonteCarloRiskReportFrame.DEFAULT_OPTIONS

    assert options["general"] == {
        "include_executive_summary": True,
        "include_method_explanation": True,
    }


def test_default_options_include_expected_analysis_sections():
    options = MonteCarloRiskReportFrame.DEFAULT_OPTIONS

    assert options["analysis"] == {
        "include_portfolio_projection": True,
        "include_portfolio_sustainability": True,
        "include_monte_carlo_insights": True,
        "include_percentile_table": True,
    }


def test_default_options_include_expected_output_sections():
    options = MonteCarloRiskReportFrame.DEFAULT_OPTIONS

    assert options["output"] == {
        "generate_html": True,
        "generate_csv": False,
    }


def test_build_method_specific_analysis_options_adds_monte_carlo_insights(monkeypatch):
    frame = object.__new__(MonteCarloRiskReportFrame)

    calls = []

    def fake_add_check_path_to_frame(parent, label, path, row):
        calls.append(
            {
                "parent": parent,
                "label": label,
                "path": path,
                "row": row,
            }
        )
        return row + 1

    monkeypatch.setattr(
        frame,
        "_add_check_path_to_frame",
        fake_add_check_path_to_frame,
        raising=False,
    )

    parent = object()

    result_row = frame._build_method_specific_analysis_options(parent, 7)

    assert result_row == 8
    assert calls == [
        {
            "parent": parent,
            "label": "Include Monte Carlo Insights",
            "path": ["analysis", "include_monte_carlo_insights"],
            "row": 7,
        }
    ]