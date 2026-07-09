from __future__ import annotations

from src.warpsimlab.gui.gui_reportHistoricalWindowRisk import (
    HistoricalWindowRiskReportFrame,
)


def test_class_constants_identify_historical_window_risk_report():
    assert HistoricalWindowRiskReportFrame.REPORT_NAME == "Historical Window Risk Report"
    assert HistoricalWindowRiskReportFrame.RUN_SIM_TYPE == "historical_window_risk_report"


def test_description_and_method_note_are_historical_window_specific():
    assert "Historical Window Risk Report" in HistoricalWindowRiskReportFrame.DESCRIPTION
    assert "report contents only" in HistoricalWindowRiskReportFrame.DESCRIPTION

    assert "historical data files" in HistoricalWindowRiskReportFrame.METHOD_NOTE
    assert "window mode" in HistoricalWindowRiskReportFrame.METHOD_NOTE
    assert "Simulation" in HistoricalWindowRiskReportFrame.METHOD_NOTE


def test_default_options_include_expected_general_sections():
    options = HistoricalWindowRiskReportFrame.DEFAULT_OPTIONS

    assert options["general"] == {
        "include_executive_summary": True,
        "include_method_explanation": True,
    }


def test_default_options_include_expected_analysis_sections():
    options = HistoricalWindowRiskReportFrame.DEFAULT_OPTIONS

    assert options["analysis"] == {
        "include_portfolio_projection": True,
        "include_portfolio_sustainability": True,
        "include_historical_window_insights": True,
        "include_percentile_table": True,
    }


def test_default_options_include_expected_output_sections():
    options = HistoricalWindowRiskReportFrame.DEFAULT_OPTIONS

    assert options["output"] == {
        "generate_html": True,
        "generate_csv": False,
    }


def test_build_method_specific_analysis_options_adds_historical_window_insights(monkeypatch):
    frame = object.__new__(HistoricalWindowRiskReportFrame)

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
            "label": "Include Historical Window Insights",
            "path": ["analysis", "include_historical_window_insights"],
            "row": 7,
        }
    ]