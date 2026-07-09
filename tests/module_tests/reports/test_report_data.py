from __future__ import annotations

from src.warpsimlab.reports.report_data import (
    ReportResult,
    RiskReportData,
    SummaryReportData,
    TaxReportData,
    YearByYearReportData,
)


def test_summary_report_data_preserves_required_fields_and_defaults():
    data = SummaryReportData(
        report_options={"include_simulation_summary": True},
        report_metadata={"Report ID": "summary-1"},
        simulation_snapshot={"Years Simulated": 5},
        results_summary={"simulation_totals": {"Portfolio End": 100000.0}},
        assumptions_summary={"Tax Assumptions": {"Calculate Taxes": True}},
    )

    assert data.report_options == {"include_simulation_summary": True}
    assert data.report_metadata == {"Report ID": "summary-1"}
    assert data.simulation_snapshot == {"Years Simulated": 5}
    assert data.results_summary == {
        "simulation_totals": {
            "Portfolio End": 100000.0,
        }
    }
    assert data.assumptions_summary == {
        "Tax Assumptions": {
            "Calculate Taxes": True,
        }
    }

    assert data.monte_carlo_summary is None
    assert data.historical_windows_summary is None
    assert data.plot_assets == {}
    assert data.warnings == []


def test_summary_report_data_accepts_optional_sections():
    data = SummaryReportData(
        report_options={},
        report_metadata={},
        simulation_snapshot={},
        results_summary={},
        assumptions_summary={},
        monte_carlo_summary={"runs": 100},
        historical_windows_summary={"windows": 25},
        plot_assets={"portfolio_projection": {"path": "plot.png"}},
        warnings=["warning"],
    )

    assert data.monte_carlo_summary == {"runs": 100}
    assert data.historical_windows_summary == {"windows": 25}
    assert data.plot_assets == {"portfolio_projection": {"path": "plot.png"}}
    assert data.warnings == ["warning"]


def test_summary_report_data_default_mutable_fields_are_independent():
    first = SummaryReportData(
        report_options={},
        report_metadata={},
        simulation_snapshot={},
        results_summary={},
        assumptions_summary={},
    )
    second = SummaryReportData(
        report_options={},
        report_metadata={},
        simulation_snapshot={},
        results_summary={},
        assumptions_summary={},
    )

    first.plot_assets["plot"] = {"path": "a.png"}
    first.warnings.append("first warning")

    assert second.plot_assets == {}
    assert second.warnings == []


def test_year_by_year_report_data_preserves_fields_and_defaults():
    data = YearByYearReportData(
        report_options={"table_detail": "Detailed"},
        report_metadata={"Report ID": "yearly-1"},
        year_rows=[
            {
                "Year": 2026,
                "Total Portfolio": 100000.0,
            }
        ],
    )

    assert data.report_options == {"table_detail": "Detailed"}
    assert data.report_metadata == {"Report ID": "yearly-1"}
    assert data.year_rows == [
        {
            "Year": 2026,
            "Total Portfolio": 100000.0,
        }
    ]
    assert data.warnings == []


def test_year_by_year_report_data_default_warnings_are_independent():
    first = YearByYearReportData(
        report_options={},
        report_metadata={},
        year_rows=[],
    )
    second = YearByYearReportData(
        report_options={},
        report_metadata={},
        year_rows=[],
    )

    first.warnings.append("first warning")

    assert second.warnings == []


def test_risk_report_data_preserves_required_fields_and_defaults():
    data = RiskReportData(
        report_options={"output": {"generate_html": True}},
        report_metadata={"Report ID": "risk-1"},
        simulation_snapshot={"Years Simulated": 5},
        analysis_summary={
            "Analysis Method": "Monte Carlo Analysis",
            "Scenario Count": 100,
        },
    )

    assert data.report_options == {"output": {"generate_html": True}}
    assert data.report_metadata == {"Report ID": "risk-1"}
    assert data.simulation_snapshot == {"Years Simulated": 5}
    assert data.analysis_summary == {
        "Analysis Method": "Monte Carlo Analysis",
        "Scenario Count": 100,
    }

    assert data.historical_insights == {}
    assert data.monte_carlo_insights == {}
    assert data.risk_observations == []
    assert data.percentile_table == []
    assert data.failure_statistics == {}
    assert data.plot_assets == {}
    assert data.warnings == []


def test_risk_report_data_accepts_optional_sections():
    data = RiskReportData(
        report_options={},
        report_metadata={},
        simulation_snapshot={},
        analysis_summary={},
        historical_insights={"Best Retirement Years": []},
        monte_carlo_insights={"Commentary": []},
        risk_observations=["observation"],
        percentile_table=[{"Year": 2026, "Median": 100000.0}],
        failure_statistics={"Simulated Shortfall Rate": 5.0},
        plot_assets={"portfolio_range_projection": {"path": "risk.png"}},
        warnings=["warning"],
    )

    assert data.historical_insights == {"Best Retirement Years": []}
    assert data.monte_carlo_insights == {"Commentary": []}
    assert data.risk_observations == ["observation"]
    assert data.percentile_table == [{"Year": 2026, "Median": 100000.0}]
    assert data.failure_statistics == {"Simulated Shortfall Rate": 5.0}
    assert data.plot_assets == {"portfolio_range_projection": {"path": "risk.png"}}
    assert data.warnings == ["warning"]


def test_risk_report_data_default_mutable_fields_are_independent():
    first = RiskReportData(
        report_options={},
        report_metadata={},
        simulation_snapshot={},
        analysis_summary={},
    )
    second = RiskReportData(
        report_options={},
        report_metadata={},
        simulation_snapshot={},
        analysis_summary={},
    )

    first.historical_insights["x"] = 1
    first.monte_carlo_insights["y"] = 2
    first.risk_observations.append("observation")
    first.percentile_table.append({"Year": 2026})
    first.failure_statistics["rate"] = 1.0
    first.plot_assets["plot"] = {"path": "plot.png"}
    first.warnings.append("warning")

    assert second.historical_insights == {}
    assert second.monte_carlo_insights == {}
    assert second.risk_observations == []
    assert second.percentile_table == []
    assert second.failure_statistics == {}
    assert second.plot_assets == {}
    assert second.warnings == []


def test_tax_report_data_preserves_required_fields_and_defaults():
    data = TaxReportData(
        report_options={"output": {"generate_html": True}},
        report_metadata={"Report ID": "tax-1"},
        tax_settings={"Calculate Income Taxes": True},
        lifetime_tax_summary={"Lifetime Total Tax": 10000.0},
        tax_source_summary={"Wages": 50000.0},
        roth_summary={"Total Roth Withdrawals": 1000.0},
        hsa_summary={"Total HSA Withdrawals": 500.0},
        rmd_summary={"Total RMDs": 2000.0},
        yearly_tax_rows=[
            {
                "Year": 2026,
                "Total Taxes": 100.0,
            }
        ],
    )

    assert data.report_options == {"output": {"generate_html": True}}
    assert data.report_metadata == {"Report ID": "tax-1"}
    assert data.tax_settings == {"Calculate Income Taxes": True}
    assert data.lifetime_tax_summary == {"Lifetime Total Tax": 10000.0}
    assert data.tax_source_summary == {"Wages": 50000.0}
    assert data.roth_summary == {"Total Roth Withdrawals": 1000.0}
    assert data.hsa_summary == {"Total HSA Withdrawals": 500.0}
    assert data.rmd_summary == {"Total RMDs": 2000.0}
    assert data.yearly_tax_rows == [
        {
            "Year": 2026,
            "Total Taxes": 100.0,
        }
    ]
    assert data.warnings == []


def test_tax_report_data_default_warnings_are_independent():
    first = TaxReportData(
        report_options={},
        report_metadata={},
        tax_settings={},
        lifetime_tax_summary={},
        tax_source_summary={},
        roth_summary={},
        hsa_summary={},
        rmd_summary={},
        yearly_tax_rows=[],
    )
    second = TaxReportData(
        report_options={},
        report_metadata={},
        tax_settings={},
        lifetime_tax_summary={},
        tax_source_summary={},
        roth_summary={},
        hsa_summary={},
        rmd_summary={},
        yearly_tax_rows=[],
    )

    first.warnings.append("first warning")

    assert second.warnings == []


def test_report_result_defaults_to_no_paths_warnings_or_errors():
    result = ReportResult(success=True)

    assert result.success is True
    assert result.report_path is None
    assert result.output_folder is None
    assert result.warnings == []
    assert result.errors == []


def test_report_result_preserves_failure_details():
    result = ReportResult(
        success=False,
        report_path=None,
        output_folder="/tmp/reports",
        warnings=["warning"],
        errors=["cannot write"],
    )

    assert result.success is False
    assert result.report_path is None
    assert result.output_folder == "/tmp/reports"
    assert result.warnings == ["warning"]
    assert result.errors == ["cannot write"]


def test_report_result_default_mutable_fields_are_independent():
    first = ReportResult(success=True)
    second = ReportResult(success=True)

    first.warnings.append("warning")
    first.errors.append("error")

    assert second.warnings == []
    assert second.errors == []