# test_summary_report.py

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.warpsimlab.reports import summary_report as mod
from src.warpsimlab.reports.report_data import SummaryReportData

import os
from pathlib import Path


def make_report_data(**overrides):
    base = dict(
        report_options={
            "include_simulation_summary": True,
            "include_assumptions_appendix": True,
            "portfolio_visuals": {
                "include_normal_projection": False,
                "include_subcategories_projection": False,
                "include_monte_carlo_analysis": False,
                "include_historical_windows_analysis": False,
            },
            "income_visuals": {
                "include_normal_income": False,
                "include_subcategories_income": False,
            },
            "operating_balance_visuals": {
                "include_cumulative_operating_balance": False,
            },
        },
        report_metadata={
            "Generated Timestamp": "2026-01-01 12:00:00",
            "Projection Period": "2026-2031 (5 Years)",
            "Report Basis": "Raw Dollars (Future Nominal Values)",
            "Report ID": "test-report",
        },
        simulation_snapshot={
            "Years Simulated": 5,
        },
        results_summary={
            "simulation_totals": {
                "Portfolio Start": 100000.0,
                "Portfolio End": 150000.0,
                "Maximum Portfolio": 160000.0,
                "Minimum Portfolio": 90000.0,
                "Total Income": 50000.0,
                "Household Expenses": 30000.0,
                "Net Cash Flow": 20000.0,
                "Fund Expenses": 100.0,
                "Simulated Shortfall Rate": 0.0,
            },
            "portfolio_milestones": {
                "Start of Simulation": {
                    "Year": 2026,
                    "Pre-Tax Assets": 60000.0,
                    "Post-Tax Assets": 40000.0,
                    "Total Portfolio": 100000.0,
                    "Real Estate": 0.0,
                    "Total Assets": 100000.0,
                },
            },
            "income_milestones": {
                "Start Simulation": {
                    "Year": 2026,
                    "Wages": 1000.0,
                    "RMD": 0.0,
                    "Social Security": 0.0,
                    "Pensions & Annuities": 0.0,
                    "Gross Income": 1000.0,
                    "401k or IRA Contribution": 0.0,
                    "Taxes": 100.0,
                    "Tax Bracket": 0.10,
                    "Net Income": 900.0,
                    "Household Expenses": 500.0,
                    "Net Cash Flow": 400.0,
                    "Fund Expenses": 0.0,
                },
            },
        },
        assumptions_summary={
            "Tax Assumptions": {
                "Calculate Income Taxes": True,
                "Calculate Payroll Taxes": False,
            }
        },
        monte_carlo_summary=None,
        historical_windows_summary=None,
        plot_assets={},
        warnings=[],
    )
    base.update(overrides)
    return SummaryReportData(**base)


def test_safe_escapes_html():
    assert mod._safe("<script>x</script>") == "&lt;script&gt;x&lt;/script&gt;"


def test_get_report_option_reads_nested_value_and_defaults():
    options = {
        "portfolio_visuals": {
            "include_normal_projection": True,
        }
    }

    assert (
        mod._get_report_option(
            options,
            ["portfolio_visuals", "include_normal_projection"],
            default=False,
        )
        is True
    )

    assert (
        mod._get_report_option(
            options,
            ["portfolio_visuals", "include_monte_carlo_analysis"],
            default="missing",
        )
        == "missing"
    )


def test_is_percent_key_and_year_key():
    assert mod._is_percent_key("Inflation Rate") is True
    assert mod._is_percent_key("Tax Bracket") is True
    assert mod._is_percent_key("Portfolio Start") is False

    assert mod._is_year_key("Year") is True
    assert mod._is_year_key("Projection End Year") is True
    assert mod._is_year_key("Portfolio End") is False


def test_fmt_value_handles_none_bool_and_strings():
    assert mod._fmt_value(None) == "N/A"
    assert mod._fmt_value(True) == "Yes"
    assert mod._fmt_value(False) == "No"
    assert mod._fmt_value("Raw") == "Raw"


def test_fmt_value_formats_years_percentages_and_tax_bracket():
    assert mod._fmt_value(2026.9, key="Year") == "2026"
    assert mod._fmt_value(7.125, key="Inflation Rate") == "7.12%"
    assert mod._fmt_value(0.24, key="Tax Bracket") == "24%"


def test_fmt_value_formats_currency_and_ints():
    assert mod._fmt_value(1234.0) == "$1,234"
    assert mod._fmt_value(-1234.0) == "-$1,234"
    assert mod._fmt_value(1234) == "1,234"


def test_relative_asset_path_returns_relative_path(tmp_path):
    output_folder = tmp_path / "reports"
    output_folder.mkdir()
    image_path = output_folder / "assets" / "plot.png"
    image_path.parent.mkdir()
    image_path.write_text("fake", encoding="utf-8")

    assert (
        mod._relative_asset_path(str(image_path), str(output_folder))
            == os.path.join("assets", "plot.png")
    )


def test_relative_asset_path_handles_empty_path():
    assert mod._relative_asset_path(None, "/tmp") is None
    assert mod._relative_asset_path("", "/tmp") is None


def test_is_depleted_value_only_flags_depletion_keys():
    assert mod._is_depleted_value("Portfolio End", 0.0) is True
    assert mod._is_depleted_value("Portfolio End Value", -1.0) is True
    assert mod._is_depleted_value("Total Portfolio", "0") is True

    assert mod._is_depleted_value("Taxes Paid", 0.0) is False
    assert mod._is_depleted_value("Portfolio Start", 0.0) is False
    assert mod._is_depleted_value("Portfolio End", "not-a-number") is False


def test_render_kv_table_escapes_text_and_marks_negative_values():
    html = mod._render_kv_table(
        {
            "Name": "<unsafe>",
            "Net Cash Flow": -100.0,
            "Portfolio End": 0.0,
        },
        emphasize_keys={"Net Cash Flow"},
    )

    assert "&lt;unsafe&gt;" in html
    assert "class='emphasis-row'" in html
    assert "class='negative'" in html
    assert "-$100" in html


def test_render_report_header_contains_metadata_and_escapes_values():
    report_data = make_report_data(
        report_metadata={
            "Generated Timestamp": "<bad>",
            "Projection Period": "2026-2031 (5 Years)",
            "Report Basis": "Raw Dollars",
            "Report ID": "abc",
        }
    )

    html = mod.render_report_header(
        report_data,
        title="Executive Summary Report",
        market_wording="simulated market conditions",
    )

    assert "WARPSimLab" in html
    assert "&lt;bad&gt;" in html
    assert "2026-2031" in html
    assert "educational purposes" in html


def test_render_simulation_highlights_includes_shortfall_and_negative_class():
    report_data = make_report_data(
        results_summary={
            "simulation_totals": {
                "Portfolio Start": 100.0,
                "Portfolio End": 0.0,
                "Simulated Shortfall Rate": 12.5,
                "Total Income": 50.0,
                "Household Expenses": 40.0,
            }
        },
        simulation_snapshot={
            "Years Simulated": 3,
        },
    )

    html = mod._render_simulation_highlights(report_data)

    assert "Portfolio End Value" in html
    assert "Simulated Shortfall Rate" in html
    assert "12.50%" in html
    assert "negative" in html


def test_render_portfolio_summary_returns_milestone_cards():
    report_data = make_report_data()

    html = mod._render_portfolio_summary(report_data)

    assert "Portfolio Summary" in html
    assert "Start of Simulation" in html
    assert "Total Portfolio" in html
    assert "$100,000" in html


def test_render_portfolio_projection_placeholder_returns_empty_when_none_selected():
    report_data = make_report_data()

    assert mod._render_portfolio_projection_placeholder(report_data) == ""


def test_render_portfolio_projection_placeholder_uses_plot_asset_path(tmp_path):
    output_folder = tmp_path / "Reports"
    output_folder.mkdir()
    image = output_folder / "assets" / "portfolio.png"
    image.parent.mkdir()
    image.write_text("fake", encoding="utf-8")

    report_data = make_report_data(
        report_options={
            "portfolio_visuals": {
                "include_normal_projection": True,
            }
        },
        plot_assets={
            "portfolio_projection": {
                "path": str(image),
                "title": "Custom Portfolio Plot",
                "alt": "Alt text",
            }
        },
    )

    html = mod._render_portfolio_projection_placeholder(
        report_data,
        output_folder=str(output_folder),
    )

    assert "Portfolio Visuals" in html
    assert "Custom Portfolio Plot" in html
    assert f'src="{os.path.join("assets", "portfolio.png")}"' in html
    assert 'alt="Alt text"' in html


def test_render_portfolio_projection_placeholder_uses_placeholder_when_asset_missing():
    report_data = make_report_data(
        report_options={
            "portfolio_visuals": {
                "include_normal_projection": True,
            }
        },
        plot_assets={},
    )

    html = mod._render_portfolio_projection_placeholder(report_data)

    assert "Portfolio Projection" in html
    assert "Placeholder" in html


def test_render_income_projection_placeholder_uses_assets(tmp_path):
    output_folder = tmp_path / "Reports"
    output_folder.mkdir()
    image = output_folder / "income.png"
    image.write_text("fake", encoding="utf-8")

    report_data = make_report_data(
        report_options={
            "income_visuals": {
                "include_normal_income": True,
                "include_subcategories_income": False,
            }
        },
        plot_assets={
            "income_projection": {
                "path": str(image),
                "title": "Income Chart",
                "alt": "Income alt",
            }
        },
    )

    html = mod._render_income_projection_placeholder(
        report_data,
        output_folder=str(output_folder),
    )

    assert "Income Visuals" in html
    assert "Income Chart" in html
    assert 'src="income.png"' in html


def test_render_income_projection_placeholder_returns_empty_when_none_selected():
    report_data = make_report_data()

    assert mod._render_income_projection_placeholder(report_data) == ""


def test_render_operating_balance_placeholder_can_be_disabled():
    report_data = make_report_data(
        report_options={
            "operating_balance_visuals": {
                "include_cumulative_operating_balance": False,
            }
        }
    )

    assert mod._render_operating_balance_placeholder(report_data) == ""


def test_render_operating_balance_placeholder_uses_placeholder_when_missing_asset():
    report_data = make_report_data(
        report_options={
            "operating_balance_visuals": {
                "include_cumulative_operating_balance": True,
            }
        },
        plot_assets={},
    )

    html = mod._render_operating_balance_placeholder(report_data)

    assert "Operating Balance Visuals" in html    
    assert "Cumulative Operating Balance" in html
    assert "Placeholder" in html


def test_render_income_summary_returns_empty_without_milestones():
    report_data = make_report_data(
        results_summary={
            "income_milestones": {}
        }
    )

    assert mod._render_income_summary(report_data) == ""


def test_render_income_summary_contains_milestone_table_and_tax_bracket():
    report_data = make_report_data()

    html = mod._render_income_summary(report_data)

    assert "Income and Cash Flow Summary" in html
    assert "Start Simulation" in html
    assert "Tax Bracket" in html
    assert "10%" in html


def test_render_simulation_summary_contains_totals():
    report_data = make_report_data()

    html = mod._render_simulation_summary(report_data)

    assert "Simulation Summary" in html
    assert "Portfolio Outcome" in html
    assert "Simulation Totals" in html
    assert "Risk Indicator" in html


def test_render_simple_table_explicit_columns():
    table_data = {
        "columns": ["Name", "Amount"],
        "rows": [
            ["A", 100.0],
            ["B", -50.0],
        ],
    }

    html = mod._render_simple_table(table_data)

    assert "<th>Name</th>" in html
    assert "<td>A</td>" in html
    assert "$100" in html
    assert "-$50" in html
    assert "class='negative'" in html


def test_render_simple_table_empty_explicit_table_uses_message():
    table_data = {
        "type": "table",
        "empty_message": "Nothing here.",
        "rows": [],
    }

    assert mod._render_simple_table(table_data) == "<p>Nothing here.</p>"


def test_render_simple_table_dict_rows_collects_headers():
    rows = [
        {"Description": "Rent", "Annual Amount": 1000.0},
        {"Description": "Car", "End Year": 2030},
    ]

    html = mod._render_simple_table(rows)

    assert "<th>Description</th>" in html
    assert "<th>Annual Amount</th>" in html
    assert "<th>End Year</th>" in html
    assert "Rent" in html
    assert "$1,000" in html
    assert "2,030" in html

def test_render_simple_table_plain_list_returns_ul():
    html = mod._render_simple_table(["A", "B"])

    assert "<ul>" in html
    assert "<li>A</li>" in html
    assert "<li>B</li>" in html


def test_render_assumption_node_handles_none_scalar_list_and_nested_dict():
    assert mod._render_assumption_node(None) == "<p>N/A</p>"
    assert mod._render_assumption_node("Text") == "<p>Text</p>"

    list_html = mod._render_assumption_node(["A"])
    assert "<li>A</li>" in list_html

    nested_html = mod._render_assumption_node(
        {
            "Scalar": True,
            "Nested": {
                "Value": 10.0,
            },
            "Rows": [
                {"Name": "A"},
            ],
        }
    )

    assert "Scalar" in nested_html
    assert "Yes" in nested_html
    assert "Nested" in nested_html
    assert "$10" in nested_html
    assert "Rows" in nested_html


def test_render_assumptions_appendix_contains_sections():
    report_data = make_report_data(
        assumptions_summary={
            "Tax Assumptions": {
                "Calculate Payroll Taxes": False,
            }
        }
    )

    html = mod._render_assumptions_appendix(report_data)

    assert "Assumptions Appendix" in html
    assert "Tax Assumptions" in html
    assert "Calculate Payroll Taxes" in html
    assert "No" in html


def test_render_warnings_filters_fixture_messages():
    report_data = make_report_data(
        warnings=[
            "fixture setup warning",
            "build_fake_summary_report_data warning",
            "Real user-facing warning",
        ]
    )

    html = mod._render_warnings(report_data)

    assert "Real user-facing warning" in html
    assert "fixture setup warning" not in html
    assert "build_fake_summary_report_data" not in html


def test_render_warnings_returns_empty_when_all_filtered():
    report_data = make_report_data(
        warnings=[
            "fixture setup warning",
            "build_fake_summary_report_data warning",
        ]
    )

    assert mod._render_warnings(report_data) == ""


def test_generate_summary_report_writes_html_to_expected_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(mod.os.path, "expanduser", lambda _: str(tmp_path))

    report_data = make_report_data(
        report_metadata={
            "Generated Timestamp": "2026-01-01 12:00:00",
            "Projection Period": "2026-2031 (5 Years)",
            "Report Basis": "Raw Dollars",
            "Report ID": "report id/with spaces",
        }
    )

    result = mod.generate_summary_report(report_data)

    assert result.success is True
    assert result.errors == []
    assert result.report_path is not None
    assert result.output_folder.endswith(os.path.join("Desktop", "WARPSimLab", "Reports"))

    report_path = mod.os.path.normpath(result.report_path)
    assert report_path.endswith(
        mod.os.path.normpath(
            "Desktop/WARPSimLab/Reports/executive_summary_report_id_with_spaces.html"
        )
    )

    html_text = Path(result.report_path).read_text(encoding="utf-8")
    assert "WARPSimLab Executive Summary Report" in html_text
    assert "Simulation Highlights" in html_text
    assert "Portfolio Summary" in html_text
    assert "Assumptions Appendix" in html_text


def test_generate_summary_report_returns_error_when_write_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(mod.os.path, "expanduser", lambda _: str(tmp_path))

    def raise_on_open(*args, **kwargs):
        raise OSError("cannot write")

    monkeypatch.setattr("builtins.open", raise_on_open)

    report_data = make_report_data()
    result = mod.generate_summary_report(report_data)

    assert result.success is False
    assert result.report_path is None
    assert result.errors == ["cannot write"]
