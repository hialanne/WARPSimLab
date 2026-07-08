# report_data.py

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SummaryReportData:
    report_options: dict[str, Any]
    report_metadata: dict[str, Any]
    simulation_snapshot: dict[str, Any]
    results_summary: dict[str, Any]
    assumptions_summary: dict[str, Any]
    monte_carlo_summary: Optional[dict[str, Any]] = None
    historical_windows_summary: Optional[dict[str, Any]] = None
    plot_assets: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class YearByYearReportData:
    report_options: dict[str, Any]
    report_metadata: dict[str, Any]
    year_rows: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)

@dataclass
class RiskReportData:
    report_options: dict[str, Any]
    report_metadata: dict[str, Any]
    simulation_snapshot: dict[str, Any]

    # Executive Summary / Risk Summary values.
    # These should contain only scalar display values.
    analysis_summary: dict[str, Any]

    # Historical / Monte Carlo specific sections.
    historical_insights: dict[str, Any] = field(default_factory=dict)
    monte_carlo_insights: dict[str, Any] = field(default_factory=dict)

    # Educational observations shown later in the report.
    risk_observations: list[str] = field(default_factory=list)

    percentile_table: list[dict[str, Any]] = field(default_factory=list)
    failure_statistics: dict[str, Any] = field(default_factory=dict)

    plot_assets: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class TaxReportData:
    report_options: dict[str, Any]
    report_metadata: dict[str, Any]
    tax_settings: dict[str, Any]
    lifetime_tax_summary: dict[str, Any]
    tax_source_summary: dict[str, Any]
    roth_summary: dict[str, Any]
    hsa_summary: dict[str, Any]
    rmd_summary: dict[str, Any]
    yearly_tax_rows: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)


@dataclass
class ReportResult:
    success: bool
    report_path: Optional[str] = None
    output_folder: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)