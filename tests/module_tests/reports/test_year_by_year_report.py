from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.warpsimlab.reports import year_by_year_report as mod
from src.warpsimlab.reports.report_data import YearByYearReportData


def make_report_data(**overrides):
    base = dict(
        report_options={
            "table_detail": "Compact",
            "insert_5_year_breaks": True,
            "generate_html": True,
            "generate_csv": True,
        },
        report_metadata={
            "Generated Timestamp": "2026-01-01 12:00:00",
            "Projection Period": "2026-2031 (5 Years)",
            "Report Basis": "Raw Dollars",
            "Report ID": "test-report",
        },
        year_rows=[
            {
                "Year": 2026,
                "Age": 60,
                "Age 1": 60,
                "Age 2": 58,
                "Wages": 1000.0,
                "Social Security": 0.0,
                "Pensions & Annuities": 0.0,
                "RMD": 0.0,
                "Portfolio Withdrawals": 0.0,
                "Gross Income": 1000.0,
                "Taxes": 100.0,
                "Household Expenses": 500.0,
                "Net Cash Flow": 400.0,
                "Fund Expenses": 10.0,
                "Pre-Tax Assets": 60000.0,
                "Post-Tax Assets": 40000.0,
                "Roth Assets": 5000.0,
                "HSA Assets": 2000.0,
                "Real Estate": 0.0,
                "Total Portfolio": 107000.0,
                "Total Assets / Net Worth": 107000.0,
            },
            {
                "Year": 2027,
                "Age": 61,
                "Age 1": 61,
                "Age 2": 59,
                "Wages": 1100.0,
                "Social Security": 0.0,
                "Pensions & Annuities": 0.0,
                "RMD": 0.0,
                "Portfolio Withdrawals": 100.0,
                "Gross Income": 1200.0,
                "Taxes": 120.0,
                "Household Expenses": 600.0,
                "Net Cash Flow": 480.0,
                "Fund Expenses": 12.0,
                "Pre-Tax Assets": 61000.0,
                "Post-Tax Assets": 41000.0,
                "Roth Assets": 5200.0,
                "HSA Assets": 2100.0,
                "Real Estate": 0.0,
                "Total Portfolio": 109300.0,
                "Total Assets / Net Worth": 109300.0,
            },
        ],
        warnings=[],
    )
    base.update(overrides)
    return YearByYearReportData(**base)


def test_fmt_value_handles_none_bool_year_age_currency_and_strings():
    assert mod._fmt_value(None) == ""
    assert mod._fmt_value(True) == "Yes"
    assert mod._fmt_value(False) == "No"

    assert mod._fmt_value(2026.9, key="Year") == "2026"
    assert mod._fmt_value(60.8, key="Age") == "60"
    assert mod._fmt_value(61.2, key="Age 1") == "61"
    assert mod._fmt_value(59.9, key="Age 2") == "59"

    assert mod._fmt_value(1234) == "1,234"
    assert mod._fmt_value(1234.0) == "$1,234"
    assert mod._fmt_value(-1234.0) == "-$1,234"

    assert mod._fmt_value("<unsafe>") == "<unsafe>"


def test_selected_columns_uses_compact_columns_and_only_available_fields():
    report_data = make_report_data(
        report_options={
            "table_detail": "Compact",
        },
        year_rows=[
            {
                "Year": 2026,
                "Age": 60,
                "Gross Income": 1000.0,
                "Taxes": 100.0,
                "Unknown Extra": 999.0,
            }
        ],
    )

    columns = mod._selected_columns(report_data)

    assert columns == [
        "Year",
        "Age",
        "Gross Income",
        "Taxes",
    ]


def test_selected_columns_uses_detailed_columns_and_includes_roth_hsa():
    report_data = make_report_data(
        report_options={
            "table_detail": "Detailed",
        }
    )

    columns = mod._selected_columns(report_data)

    assert "Wages" in columns
    assert "Roth Assets" in columns
    assert "HSA Assets" in columns
    assert "Total Assets / Net Worth" in columns


def test_calculate_summary_statistics_empty_rows_returns_empty_dict():
    report_data = make_report_data(year_rows=[])

    assert mod._calculate_summary_statistics(report_data) == {}


def test_calculate_summary_statistics_uses_totals_maximum_and_last_row():
    report_data = make_report_data()

    stats = mod._calculate_summary_statistics(report_data)

    assert stats["Years Simulated"] == 1
    assert stats["Total Lifetime Income"] == pytest.approx(2200.0)
    assert stats["Total Taxes Paid"] == pytest.approx(220.0)
    assert stats["Total Household Expenses"] == pytest.approx(1100.0)
    assert stats["Total Portfolio Withdrawals"] == pytest.approx(100.0)
    assert stats["Largest Annual Portfolio Withdrawal"] == pytest.approx(100.0)
    assert stats["Ending Portfolio"] == pytest.approx(109300.0)
    assert stats["Ending Net Worth"] == pytest.approx(109300.0)


def test_render_summary_statistics_returns_empty_without_rows():
    report_data = make_report_data(year_rows=[])

    assert mod._render_summary_statistics(report_data) == ""


def test_render_summary_statistics_contains_formatted_values():
    report_data = make_report_data()

    html = mod._render_summary_statistics(report_data)

    assert "Summary Statistics" in html
    assert "Years Simulated" in html
    assert "1" in html
    assert "Total Lifetime Income" in html
    assert "$2,200" in html
    assert "Ending Portfolio" in html
    assert "$109,300" in html


def test_render_year_table_escapes_headers_values_and_marks_negative_values():
    report_data = make_report_data(
        year_rows=[
            {
                "Year": 2026,
                "Age": 60,
                "Gross Income": "<bad>",
                "Taxes": -100.0,
                "Household Expenses": 500.0,
                "Portfolio Withdrawals": 0.0,
                "Net Cash Flow": -400.0,
                "Total Portfolio": 100000.0,
                "Total Assets / Net Worth": 100000.0,
            }
        ]
    )

    html = mod._render_year_table(report_data)

    assert "Year-by-Year Details" in html
    assert "&lt;bad&gt;" in html
    assert "-$100" in html
    assert "-$400" in html
    assert "class='negative'" in html


def test_render_year_table_inserts_five_year_break_when_enabled():
    rows = []
    for i in range(6):
        rows.append(
            {
                "Year": 2026 + i,
                "Gross Income": 100.0,
            }
        )

    report_data = make_report_data(
        report_options={
            "table_detail": "Compact",
            "insert_5_year_breaks": True,
        },
        year_rows=rows,
    )

    html = mod._render_year_table(report_data)

    assert "class='five-year-break'" in html


def test_render_year_table_omits_five_year_break_when_disabled():
    rows = []
    for i in range(6):
        rows.append(
            {
                "Year": 2026 + i,
                "Gross Income": 100.0,
            }
        )

    report_data = make_report_data(
        report_options={
            "table_detail": "Compact",
            "insert_5_year_breaks": False,
        },
        year_rows=rows,
    )

    html = mod._render_year_table(report_data)

    assert "class='five-year-break'" not in html


def test_render_warnings_returns_empty_without_warnings():
    report_data = make_report_data(warnings=[])

    assert mod._render_warnings(report_data) == ""


def test_render_warnings_escapes_warning_text():
    report_data = make_report_data(warnings=["<bad warning>"])

    html = mod._render_warnings(report_data)

    assert "Warnings" in html
    assert "&lt;bad warning&gt;" in html


def test_build_html_document_contains_header_sections_and_footer():
    report_data = make_report_data(
        report_metadata={
            "Generated Timestamp": "2026-01-01",
            "Projection Period": "2026-2031",
            "Report Basis": "Raw Dollars",
            "Report ID": "abc",
            "Report Title": "<Unsafe Title>",
        }
    )

    html = mod._build_html_document(report_data)

    assert "<title>&lt;Unsafe Title&gt;</title>" in html
    assert "Year-by-Year Details Report" in html
    assert "Summary Statistics" in html
    assert "Year-by-Year Details" in html
    assert "WARPSimLab" in html


def test_write_csv_writes_selected_columns_and_rows(tmp_path):
    report_data = make_report_data(
        report_options={
            "table_detail": "Compact",
        }
    )

    csv_path = mod._write_csv(
        report_data,
        output_folder=str(tmp_path),
        safe_report_id="abc",
    )

    assert Path(csv_path).name == "year_by_year_details_abc.csv"

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert "Year" in rows[0]
    assert "Gross Income" in rows[0]
    assert "Wages" not in rows[0]
    assert rows[0]["Year"] == "2026"
    assert rows[0]["Gross Income"] == "1000.0"


def test_write_html_writes_html_document(tmp_path):
    report_data = make_report_data()

    html_path = mod._write_html(
        report_data,
        output_folder=str(tmp_path),
        safe_report_id="abc",
    )

    text = Path(html_path).read_text(encoding="utf-8")

    assert Path(html_path).name == "year_by_year_details_abc.html"
    assert "Year-by-Year Details Report" in text
    assert "Summary Statistics" in text


def test_generate_year_by_year_report_returns_error_when_no_outputs_selected(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_get_output_folder", lambda: str(tmp_path))

    report_data = make_report_data(
        report_options={
            "generate_html": False,
            "generate_csv": False,
        }
    )

    result = mod.generate_year_by_year_report(report_data)

    assert result.success is False
    assert result.output_folder == str(tmp_path)
    assert result.report_path is None
    assert result.errors == ["No Year-by-Year report output format was selected."]


def test_generate_year_by_year_report_writes_html_and_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_get_output_folder", lambda: str(tmp_path))
    monkeypatch.setattr(mod, "_safe_report_id", lambda report_id: "safe-id")

    report_data = make_report_data(
        report_options={
            "generate_html": True,
            "generate_csv": True,
        },
        report_metadata={
            "Generated Timestamp": "2026-01-01",
            "Projection Period": "2026-2031",
            "Report Basis": "Raw Dollars",
            "Report ID": "unsafe/id",
        },
    )

    result = mod.generate_year_by_year_report(report_data)

    assert result.success is True
    assert result.errors == []
    assert result.output_folder == str(tmp_path)
    assert result.report_path == str(tmp_path / "year_by_year_details_safe-id.html")

    assert (tmp_path / "year_by_year_details_safe-id.html").exists()
    assert (tmp_path / "year_by_year_details_safe-id.csv").exists()


def test_generate_year_by_year_report_writes_csv_only_when_html_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_get_output_folder", lambda: str(tmp_path))
    monkeypatch.setattr(mod, "_safe_report_id", lambda report_id: "safe-id")

    report_data = make_report_data(
        report_options={
            "generate_html": False,
            "generate_csv": True,
        }
    )

    result = mod.generate_year_by_year_report(report_data)

    assert result.success is True
    assert result.report_path == str(tmp_path / "year_by_year_details_safe-id.csv")

    assert not (tmp_path / "year_by_year_details_safe-id.html").exists()
    assert (tmp_path / "year_by_year_details_safe-id.csv").exists()


def test_generate_year_by_year_report_returns_error_when_write_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_get_output_folder", lambda: str(tmp_path))
    monkeypatch.setattr(mod, "_safe_report_id", lambda report_id: "safe-id")

    def raise_on_write(*args, **kwargs):
        raise OSError("cannot write")

    monkeypatch.setattr(mod, "_write_html", raise_on_write)

    report_data = make_report_data(
        report_options={
            "generate_html": True,
            "generate_csv": True,
        }
    )

    result = mod.generate_year_by_year_report(report_data)

    assert result.success is False
    assert result.report_path is None
    assert result.output_folder == str(tmp_path)
    assert result.errors == ["cannot write"]