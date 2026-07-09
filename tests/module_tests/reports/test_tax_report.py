from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.warpsimlab.reports import tax_report as mod
from src.warpsimlab.reports.report_data import TaxReportData


def make_report_data(**overrides):
    base = dict(
        report_options={
            "sections": {
                "include_roth_analysis": True,
                "include_hsa_analysis": True,
                "include_rmd_analysis": True,
            },
            "output": {
                "generate_html": True,
                "generate_csv": True,
            },
        },
        report_metadata={
            "Generated Timestamp": "2026-01-01 12:00:00",
            "Projection Period": "2026-2031 (5 Years)",
            "Report Basis": "Raw Dollars",
            "Report ID": "test-report",
        },
        tax_settings={
            "Calculate Income Taxes": True,
            "Calculate Payroll Taxes": True,
            "Calculate State Taxes": False,
            "Tax Filing Status": "Married Filing Jointly",
            "State of Residence": "None",
        },
        lifetime_tax_summary={
            "Lifetime Total Tax": 10000.0,
            "Lifetime Federal Income Tax": 7000.0,
            "Lifetime State Income Tax": 1000.0,
            "Lifetime Payroll Tax": 2000.0,
            "Average Effective Tax Rate": 0.125,
            "Highest Marginal Tax Bracket": 0.24,
        },
        tax_source_summary={
            "Wages": 50000.0,
            "Social Security": 10000.0,
            "RMD": 5000.0,
            "Withdrawals": 3000.0,
            "Qualified Dividends": 1000.0,
        },
        roth_summary={
            "Starting Roth Assets": 5000.0,
            "Ending Roth Assets": 6000.0,
            "Total Roth Withdrawals": 1000.0,
        },
        hsa_summary={
            "Starting HSA Assets": 2000.0,
            "Ending HSA Assets": 2500.0,
            "Total HSA Withdrawals": 500.0,
        },
        rmd_summary={
            "First RMD Year": 2035,
            "Total RMDs": 5000.0,
        },
        yearly_tax_rows=[
            {
                "Year": 2026,
                "Age": 60,
                "Gross Income": 1000.0,
                "Federal Income Tax": 70.0,
                "State Income Tax": 10.0,
                "Payroll Tax": 20.0,
                "Total Taxes": 100.0,
                "Effective Tax Rate": 0.10,
                "Marginal Tax Bracket": 0.12,
                "RMD": 0.0,
                "Roth Withdrawals": 0.0,
                "HSA Withdrawals": 0.0,
            },
            {
                "Year": 2027,
                "Age": 61,
                "Gross Income": 2000.0,
                "Federal Income Tax": 140.0,
                "State Income Tax": 20.0,
                "Payroll Tax": 40.0,
                "Total Taxes": 200.0,
                "Effective Tax Rate": 0.10,
                "Marginal Tax Bracket": 0.12,
                "RMD": 100.0,
                "Roth Withdrawals": 1000.0,
                "HSA Withdrawals": 500.0,
            },
        ],
        warnings=[],
    )

    base.update(overrides)
    return TaxReportData(**base)


def test_get_report_option_reads_nested_value_and_default():
    options = {
        "sections": {
            "include_roth_analysis": True,
        }
    }

    assert (
        mod._get_report_option(
            options,
            ["sections", "include_roth_analysis"],
            default=False,
        )
        is True
    )

    assert (
        mod._get_report_option(
            options,
            ["sections", "include_hsa_analysis"],
            default="missing",
        )
        == "missing"
    )


def test_is_percent_key_detects_rate_percent_and_bracket():
    assert mod._is_percent_key("Average Effective Tax Rate") is True
    assert mod._is_percent_key("Percent of Income") is True
    assert mod._is_percent_key("Highest Marginal Tax Bracket") is True
    assert mod._is_percent_key("Lifetime Total Tax") is False


def test_fmt_value_handles_none_bool_string_percent_currency_and_int():
    assert mod._fmt_value(None) == "N/A"
    assert mod._fmt_value(True) == "Yes"
    assert mod._fmt_value(False) == "No"
    assert mod._fmt_value("Raw Dollars") == "Raw Dollars"

    assert mod._fmt_value(0.125, key="Average Effective Tax Rate") == "12.50%"
    assert mod._fmt_value(12.5, key="Average Effective Tax Rate") == "12.50%"
    assert mod._fmt_value(0.24, key="Highest Marginal Tax Bracket") == "24.00%"

    assert mod._fmt_value(1234.0) == "$1,234"
    assert mod._fmt_value(-1234.0) == "-$1,234"
    assert mod._fmt_value(1234) == "1,234"


def test_render_kv_table_escapes_text_marks_negative_and_emphasizes():
    html = mod._render_kv_table(
        {
            "Unsafe": "<bad>",
            "Lifetime Total Tax": 10000.0,
            "Adjustment": -50.0,
        },
        emphasize_keys={"Lifetime Total Tax"},
    )

    assert "&lt;bad&gt;" in html
    assert "class='emphasis-row'" in html
    assert "class='negative'" in html
    assert "-$50" in html


def test_render_highlights_contains_core_tax_cards():
    report_data = make_report_data()

    html = mod._render_highlights(report_data)

    assert "Tax Highlights" in html
    assert "Lifetime Total Tax" in html
    assert "$10,000" in html
    assert "Average Effective Tax Rate" in html
    assert "12.50%" in html
    assert "Highest Marginal Tax Bracket" in html
    assert "24.00%" in html


def test_render_tax_overview_contains_tax_advice_warning():
    html = mod._render_tax_overview(make_report_data())

    assert "Tax Overview" in html
    assert "not a tax return" in html
    assert "professional tax advice" in html


def test_render_tax_model_limitations_mentions_roth_hsa_and_state_taxes():
    html = mod._render_tax_model_limitations(make_report_data())

    assert "Tax Model Limitations" in html
    assert "Roth accounts" in html
    assert "HSA accounts" in html
    assert "State income taxes" in html


def test_render_tax_settings_escapes_values():
    report_data = make_report_data(
        tax_settings={
            "Tax Filing Status": "<bad>",
            "Calculate Income Taxes": True,
        }
    )

    html = mod._render_tax_settings(report_data)

    assert "Tax Settings Used" in html
    assert "&lt;bad&gt;" in html
    assert "Yes" in html


def test_render_lifetime_tax_summary_emphasizes_key_rows():
    report_data = make_report_data()

    html = mod._render_lifetime_tax_summary(report_data)

    assert "Lifetime Tax Summary" in html
    assert "Lifetime Total Tax" in html
    assert "Average Effective Tax Rate" in html
    assert "Highest Marginal Tax Bracket" in html
    assert "class='emphasis-row'" in html


def test_render_tax_source_summary_contains_sources():
    report_data = make_report_data()

    html = mod._render_tax_source_summary(report_data)

    assert "Tax Source Breakdown" in html
    assert "Wages" in html
    assert "Social Security" in html
    assert "Qualified Dividends" in html


def test_render_roth_hsa_and_rmd_sections():
    report_data = make_report_data()

    roth_html = mod._render_roth_analysis(report_data)
    hsa_html = mod._render_hsa_analysis(report_data)
    rmd_html = mod._render_rmd_analysis(report_data)

    assert "Roth Analysis" in roth_html
    assert "Total Roth Withdrawals" in roth_html

    assert "HSA Analysis" in hsa_html
    assert "Total HSA Withdrawals" in hsa_html

    assert "Required Minimum Distribution Analysis" in rmd_html
    assert "First RMD Year" in rmd_html


def test_render_yearly_tax_table_returns_empty_without_rows():
    report_data = make_report_data(yearly_tax_rows=[])

    assert mod._render_yearly_tax_table(report_data) == ""


def test_render_yearly_tax_table_contains_columns_and_formats_percentages():
    report_data = make_report_data()

    html = mod._render_yearly_tax_table(report_data)

    assert "Year-by-Year Tax Details" in html
    assert "Federal Income Tax" in html
    assert "State Income Tax" in html
    assert "Payroll Tax" in html
    assert "Effective Tax Rate" in html
    assert "Marginal Tax Bracket" in html
    assert "Roth Withdrawals" in html
    assert "HSA Withdrawals" in html
    assert "10.00%" in html
    assert "12.00%" in html


def test_render_yearly_tax_table_escapes_text_and_marks_negative_values():
    report_data = make_report_data(
        yearly_tax_rows=[
            {
                "Year": 2026,
                "Age": 60,
                "Gross Income": "<bad>",
                "Federal Income Tax": -70.0,
                "State Income Tax": 0.0,
                "Payroll Tax": 0.0,
                "Total Taxes": -70.0,
                "Effective Tax Rate": 0.0,
                "Marginal Tax Bracket": 0.0,
                "RMD": 0.0,
                "Roth Withdrawals": 0.0,
                "HSA Withdrawals": 0.0,
            }
        ]
    )

    html = mod._render_yearly_tax_table(report_data)

    assert "&lt;bad&gt;" in html
    assert "-$70" in html
    assert "class='negative'" in html


def test_render_tax_insights_generates_expected_observations():
    report_data = make_report_data()

    html = mod._render_tax_insights(report_data)

    assert "Tax Insights" in html
    assert "Federal income taxes account for 70.0% of lifetime taxes." in html
    assert "State income taxes account for 10.0% of lifetime taxes." in html
    assert "Payroll taxes account for 20.0% of lifetime taxes." in html
    assert "Average effective tax rate over the simulation is 12.50%." in html
    assert "Required Minimum Distributions begin in 2035." in html
    assert "The largest annual tax bill occurs in 2027" in html
    assert "Roth withdrawals provide tax-free retirement income" in html
    assert "HSA withdrawals provide an additional tax-free retirement funding source" in html


def test_render_tax_insights_handles_zero_tax_and_empty_rows():
    report_data = make_report_data(
        lifetime_tax_summary={
            "Lifetime Total Tax": 0.0,
            "Lifetime Federal Income Tax": 0.0,
            "Lifetime State Income Tax": 0.0,
            "Lifetime Payroll Tax": 0.0,
            "Average Effective Tax Rate": None,
            "Highest Marginal Tax Bracket": None,
        },
        rmd_summary={},
        roth_summary={"Total Roth Withdrawals": 0.0},
        hsa_summary={"Total HSA Withdrawals": 0.0},
        yearly_tax_rows=[],
    )

    html = mod._render_tax_insights(report_data)

    assert "Tax Insights" in html
    assert "Federal income taxes account" not in html
    assert "The largest annual tax bill" not in html


def test_render_warnings_returns_empty_without_warnings():
    report_data = make_report_data(warnings=[])

    assert mod._render_warnings(report_data) == ""


def test_render_warnings_escapes_warning_text():
    report_data = make_report_data(warnings=["<bad warning>"])

    html = mod._render_warnings(report_data)

    assert "Warnings" in html
    assert "&lt;bad warning&gt;" in html


def test_build_tax_plot_assets_returns_empty_without_rows(tmp_path):
    report_data = make_report_data(yearly_tax_rows=[])

    assert mod._build_tax_plot_assets(report_data, str(tmp_path), "abc") == {}


def test_build_tax_plot_assets_calls_plot_helpers(tmp_path, monkeypatch):
    report_data = make_report_data()

    calls = []

    def fake_plot(output_folder, filename, rows):
        calls.append((output_folder, filename, rows))
        return str(tmp_path / filename)

    monkeypatch.setattr(mod, "save_tax_by_year_report_plot", fake_plot)
    monkeypatch.setattr(mod, "save_effective_tax_rate_report_plot", fake_plot)
    monkeypatch.setattr(mod, "save_taxable_income_source_report_plot", fake_plot)

    assets = mod._build_tax_plot_assets(report_data, str(tmp_path), "abc")

    assert set(assets.keys()) == {
        "tax_by_year",
        "effective_tax_rate",
        "retirement_withdrawal_sources",
    }

    assert len(calls) == 3
    assert calls[0][1] == "tax_by_year.png"
    assert calls[1][1] == "effective_tax_rate.png"
    assert calls[2][1] == "retirement_withdrawal_sources.png"


def test_render_tax_plots_returns_empty_without_assets(tmp_path):
    assert mod._render_tax_plots({}, str(tmp_path)) == ""


def test_render_tax_plots_uses_relative_asset_paths(tmp_path):
    asset_folder = tmp_path / "assets"
    asset_folder.mkdir()
    image = asset_folder / "tax_by_year.png"
    image.write_text("fake", encoding="utf-8")

    html = mod._render_tax_plots(
        {
            "tax_by_year": {
                "path": str(image),
                "title": "Taxes by Year",
                "alt": "Taxes by year alt",
            }
        },
        output_folder=str(tmp_path),
    )

    assert "Tax Visuals" in html
    assert "Taxes by Year" in html
    assert 'src="assets' in html
    assert 'alt="Taxes by year alt"' in html


def test_write_yearly_tax_csv_returns_none_without_rows(tmp_path):
    report_data = make_report_data(yearly_tax_rows=[])

    result = mod._write_yearly_tax_csv(report_data, str(tmp_path), "abc")

    assert result is None
    assert not (tmp_path / "tax_year_by_year_abc.csv").exists()


def test_write_yearly_tax_csv_writes_rows(tmp_path):
    report_data = make_report_data()

    mod._write_yearly_tax_csv(report_data, str(tmp_path), "abc")

    csv_path = tmp_path / "tax_year_by_year_abc.csv"
    assert csv_path.exists()

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert rows[0]["Year"] == "2026"
    assert rows[0]["Total Taxes"] == "100.0"


def test_write_summary_csv_writes_lifetime_summary(tmp_path):
    report_data = make_report_data()

    mod._write_summary_csv(report_data, str(tmp_path), "abc")

    csv_path = tmp_path / "tax_lifetime_summary_abc.csv"
    assert csv_path.exists()

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    assert rows[0] == ["Statistic", "Value"]
    assert ["Lifetime Total Tax", "10000.0"] in rows


def test_write_tax_source_csv_writes_source_summary(tmp_path):
    report_data = make_report_data()

    mod._write_tax_source_csv(report_data, str(tmp_path), "abc")

    csv_path = tmp_path / "tax_source_breakdown_abc.csv"
    assert csv_path.exists()

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    assert rows[0] == ["Income Source", "Amount"]
    assert ["Wages", "50000.0"] in rows


def test_generate_tax_report_returns_success_without_html_when_html_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "get_report_output_folder", lambda: str(tmp_path))
    monkeypatch.setattr(mod, "safe_report_id", lambda report_id: "safe-id")

    report_data = make_report_data(
        report_options={
            "output": {
                "generate_html": False,
                "generate_csv": True,
            },
            "sections": {},
        },
        yearly_tax_rows=[],
    )

    result = mod.generate_tax_report(report_data)

    assert result.success is True
    assert result.report_path is None
    assert result.output_folder == str(tmp_path)
    assert result.errors == []


def test_generate_tax_report_writes_html_and_csvs(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "get_report_output_folder", lambda: str(tmp_path))
    monkeypatch.setattr(mod, "safe_report_id", lambda report_id: "safe-id")
    monkeypatch.setattr(mod, "_build_tax_plot_assets", lambda report_data, output_folder, safe_id: {})

    report_data = make_report_data(
        report_options={
            "output": {
                "generate_html": True,
                "generate_csv": True,
            },
            "sections": {
                "include_roth_analysis": True,
                "include_hsa_analysis": True,
                "include_rmd_analysis": True,
            },
        }
    )

    result = mod.generate_tax_report(report_data)

    assert result.success is True
    assert result.errors == []
    assert result.report_path == str(tmp_path / "tax_report_safe-id.html")
    assert result.output_folder == str(tmp_path)

    assert (tmp_path / "tax_report_safe-id.html").exists()
    assert (tmp_path / "tax_year_by_year_safe-id.csv").exists()
    assert (tmp_path / "tax_lifetime_summary_safe-id.csv").exists()
    assert (tmp_path / "tax_source_breakdown_safe-id.csv").exists()

    html = (tmp_path / "tax_report_safe-id.html").read_text(encoding="utf-8")
    assert "WARPSimLab Tax Report" in html
    assert "Tax Highlights" in html
    assert "Tax Overview" in html
    assert "Tax Model Limitations" in html
    assert "Roth Analysis" in html
    assert "HSA Analysis" in html
    assert "Required Minimum Distribution Analysis" in html
    assert "Year-by-Year Tax Details" in html


def test_generate_tax_report_can_disable_optional_analysis_sections(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "get_report_output_folder", lambda: str(tmp_path))
    monkeypatch.setattr(mod, "safe_report_id", lambda report_id: "safe-id")
    monkeypatch.setattr(mod, "_build_tax_plot_assets", lambda report_data, output_folder, safe_id: {})

    report_data = make_report_data(
        report_options={
            "output": {
                "generate_html": True,
                "generate_csv": False,
            },
            "sections": {
                "include_roth_analysis": False,
                "include_hsa_analysis": False,
                "include_rmd_analysis": False,
            },
        }
    )

    result = mod.generate_tax_report(report_data)

    assert result.success is True

    html = (tmp_path / "tax_report_safe-id.html").read_text(encoding="utf-8")

    assert "Roth Analysis" not in html
    assert "HSA Analysis" not in html
    assert "Required Minimum Distribution Analysis" not in html

    assert not (tmp_path / "tax_year_by_year_safe-id.csv").exists()
    assert not (tmp_path / "tax_lifetime_summary_safe-id.csv").exists()
    assert not (tmp_path / "tax_source_breakdown_safe-id.csv").exists()


def test_generate_tax_report_accepts_dict_input(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "get_report_output_folder", lambda: str(tmp_path))
    monkeypatch.setattr(mod, "safe_report_id", lambda report_id: "safe-id")
    monkeypatch.setattr(mod, "_build_tax_plot_assets", lambda report_data, output_folder, safe_id: {})

    report_data = make_report_data(
        report_options={
            "output": {
                "generate_html": True,
                "generate_csv": False,
            },
            "sections": {},
        }
    )

    result = mod.generate_tax_report(report_data.__dict__)

    assert result.success is True
    assert result.report_path == str(tmp_path / "tax_report_safe-id.html")
    assert (tmp_path / "tax_report_safe-id.html").exists()


def test_generate_tax_report_returns_error_when_write_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "get_report_output_folder", lambda: str(tmp_path))
    monkeypatch.setattr(mod, "safe_report_id", lambda report_id: "safe-id")
    monkeypatch.setattr(mod, "_build_tax_plot_assets", lambda report_data, output_folder, safe_id: {})

    def raise_on_open(*args, **kwargs):
        raise OSError("cannot write")

    monkeypatch.setattr("builtins.open", raise_on_open)

    report_data = make_report_data(
        report_options={
            "output": {
                "generate_html": True,
                "generate_csv": True,
            },
            "sections": {},
        }
    )

    result = mod.generate_tax_report(report_data)

    assert result.success is False
    assert result.report_path is None
    assert result.output_folder == str(tmp_path)
    assert result.errors == ["cannot write"]