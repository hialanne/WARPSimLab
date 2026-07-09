from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.warpsimlab.reports import risk_report as mod


def make_report_data(**overrides):
    base = dict(
        report_options={
            "general": {
                "include_executive_summary": True,
                "include_method_explanation": True,
            },
            "analysis": {
                "include_portfolio_sustainability": True,
                "include_percentile_table": True,
                "include_historical_window_insights": True,
                "include_monte_carlo_insights": True,
                "include_risk_observations": True,
                "include_portfolio_projection": True,
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
            "Report Title": "WARPSimLab Risk Analysis Report",
        },
        analysis_summary={
            "Analysis Method": "Monte Carlo Analysis",
            "Scenario Count": 100,
            "Years Simulated": 5,
            "Simulated Shortfall Rate": 10.0,
            "Worst Ending Portfolio": 0.0,
            "Median Ending Portfolio": 100000.0,
            "Best Ending Portfolio": 250000.0,
            "Risk Observations": [
                "Some scenarios depleted the portfolio.",
                "<unsafe observation>",
            ],
        },
        failure_statistics={
            "Simulated Shortfall Rate": 10.0,
            "Scenario Count": 100,
            "Earliest Portfolio Depletion Year": 2030,
            "Median Portfolio Depletion Year": 2032,
            "Latest Portfolio Depletion Year": 2035,
        },
        percentile_table=[
            {
                "Year": 2026,
                "10th Percentile": 90000.0,
                "Median": 100000.0,
                "90th Percentile": 120000.0,
            },
            {
                "Year": 2027,
                "10th Percentile": 80000.0,
                "Median": 105000.0,
                "90th Percentile": 130000.0,
            },
        ],
        historical_insights={
            "Best Retirement Years": [
                {
                    "Retirement Start Year": 1982,
                    "Result": "Best",
                    "Ending Portfolio": 250000.0,
                }
            ],
            "Worst Retirement Years": [
                {
                    "Retirement Start Year": 1966,
                    "Result": "Worst",
                    "Ending Portfolio": 0.0,
                }
            ],
            "Commentary": [
                "Historical commentary.",
                "<unsafe commentary>",
            ],
        },
        plot_assets={},
        warnings=[],
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def make_historical_report_data(**overrides):
    data = make_report_data(
        analysis_summary={
            "Analysis Method": "Historical Window Analysis",
            "Scenario Count": 25,
            "Years Simulated": 5,
            "Simulated Shortfall Rate": 0.0,
            "Worst Ending Portfolio": 50000.0,
            "Median Ending Portfolio": 100000.0,
            "Best Ending Portfolio": 250000.0,
            "Risk Observations": ["Historical observations."],
        },
        failure_statistics={
            "Simulated Shortfall Rate": 0.0,
            "Window Count": 25,
            "Earliest Portfolio Depletion Year": None,
            "Median Portfolio Depletion Year": None,
            "Latest Portfolio Depletion Year": None,
        },
    )

    for key, value in overrides.items():
        setattr(data, key, value)

    return data


def test_is_percent_year_and_count_keys():
    assert mod._is_percent_key("Simulated Shortfall Rate") is True
    assert mod._is_percent_key("Probability of Depletion") is True
    assert mod._is_percent_key("Worst Ending Portfolio") is False

    assert mod._is_year_key("Year") is True
    assert mod._is_year_key("Historical Window Start Year") is True
    assert mod._is_year_key("Ending Portfolio") is False

    assert mod._is_count_key("Scenario Count") is True
    assert mod._is_count_key("Historical Windows") is True
    assert mod._is_count_key("Years Simulated") is False


def test_fmt_value_handles_none_bool_string_year_percent_count_currency_and_int():
    assert mod._fmt_value(None) == "N/A"
    assert mod._fmt_value(True) == "Yes"
    assert mod._fmt_value(False) == "No"
    assert mod._fmt_value("Raw") == "Raw"

    assert mod._fmt_value(2026.9, key="Year") == "2026"
    assert mod._fmt_value(12.345, key="Simulated Shortfall Rate") == "12.35%"
    assert mod._fmt_value(1000, key="Scenario Count") == "1,000"

    assert mod._fmt_value(1234) == "1,234"
    assert mod._fmt_value(1234.0) == "$1,234"
    assert mod._fmt_value(-1234.0) == "-$1,234"


def test_fmt_value_does_not_format_percentile_as_percent():
    assert mod._fmt_value(90000.0, key="10th Percentile") == "$90,000"


def test_get_report_option_reads_nested_value_and_default():
    options = {
        "analysis": {
            "include_percentile_table": True,
        }
    }

    assert (
        mod._get_report_option(
            options,
            ["analysis", "include_percentile_table"],
            default=False,
        )
        is True
    )

    assert (
        mod._get_report_option(
            options,
            ["analysis", "missing"],
            default="missing",
        )
        == "missing"
    )


def test_render_kv_table_escapes_emphasizes_and_marks_negative():
    html = mod._render_kv_table(
        {
            "Unsafe": "<bad>",
            "Simulated Shortfall Rate": 12.5,
            "Adjustment": -100.0,
        },
        emphasize_keys={"Simulated Shortfall Rate"},
    )

    assert "&lt;bad&gt;" in html
    assert "class='emphasis-row'" in html
    assert "class='negative'" in html
    assert "-$100" in html


def test_render_simple_table_empty_returns_message():
    html = mod._render_simple_table([], empty_message="Nothing here.")

    assert html == "<p>Nothing here.</p>"


def test_render_simple_table_plain_list_returns_ul_and_escapes():
    html = mod._render_simple_table(["A", "<bad>"])

    assert "<ul>" in html
    assert "<li>A</li>" in html
    assert "&lt;bad&gt;" in html


def test_render_simple_table_dict_rows_collects_headers_and_marks_negative():
    html = mod._render_simple_table(
        [
            {"Year": 2026, "Ending Portfolio": 100000.0},
            {"Year": 2027, "Shortfall": -10.0},
        ]
    )

    assert "<th>Year</th>" in html
    assert "<th>Ending Portfolio</th>" in html
    assert "<th>Shortfall</th>" in html
    assert "$100,000" in html
    assert "class='negative'" in html


def test_render_executive_summary_can_be_disabled():
    report_data = make_report_data(
        report_options={
            "general": {
                "include_executive_summary": False,
            }
        }
    )

    assert mod._render_executive_summary(report_data) == ""


def test_render_executive_summary_contains_cards_and_negative_risk_class():
    report_data = make_report_data()

    html = mod._render_executive_summary(report_data)

    assert "Executive Summary" in html
    assert "Scenario Count" in html
    assert "100" in html
    assert "Simulated Shortfall Rate" in html
    assert "10.00%" in html
    assert "Worst Ending Portfolio" in html
    assert "negative-risk" in html


def test_render_method_explanation_historical_and_monte_carlo():
    historical_html = mod._render_method_explanation(make_historical_report_data())
    monte_html = mod._render_method_explanation(make_report_data())

    assert "Method Explanation" in historical_html
    assert "Historical Window Analysis" in historical_html
    assert "actual historical market" in historical_html

    assert "Method Explanation" in monte_html
    assert "Monte Carlo Analysis" in monte_html
    assert "simulated market paths" in monte_html


def test_render_method_explanation_can_be_disabled():
    report_data = make_report_data(
        report_options={
            "general": {
                "include_method_explanation": False,
            }
        }
    )

    assert mod._render_method_explanation(report_data) == ""


def test_render_method_explanation_raises_for_unknown_method():
    report_data = make_report_data(
        analysis_summary={
            "Analysis Method": "Unknown Method",
        }
    )

    with pytest.raises(ValueError, match="Unknown risk analysis method"):
        mod._render_method_explanation(report_data)


@pytest.mark.parametrize(
    "shortfall_rate, expected_text",
    [
        (0.0, "Every analyzed scenario remained funded"),
        (2.0, "Only a small fraction of scenarios depleted"),
        (10.0, "Most scenarios remained funded"),
        (30.0, "A meaningful share of scenarios depleted"),
        (60.0, "Most analyzed scenarios depleted"),
    ],
)
def test_render_sustainability_interpretation_thresholds(shortfall_rate, expected_text):
    report_data = make_report_data(
        failure_statistics={
            "Simulated Shortfall Rate": shortfall_rate,
        }
    )

    html = mod._render_sustainability_interpretation(report_data)

    assert expected_text in html
    assert "What Monte Carlo Suggests" in html


def test_render_sustainability_interpretation_historical_heading():
    report_data = make_historical_report_data(
        failure_statistics={
            "Simulated Shortfall Rate": 0.0,
        }
    )

    html = mod._render_sustainability_interpretation(report_data)

    assert "What History Suggests" in html


def test_render_sustainability_interpretation_returns_empty_for_invalid_rate():
    report_data = make_report_data(
        failure_statistics={
            "Simulated Shortfall Rate": "bad",
        }
    )

    assert mod._render_sustainability_interpretation(report_data) == ""


def test_render_failure_statistics_can_be_disabled_or_empty():
    disabled = make_report_data(
        report_options={
            "analysis": {
                "include_portfolio_sustainability": False,
            }
        }
    )
    empty = make_report_data(failure_statistics={})

    assert mod._render_failure_statistics(disabled) == ""
    assert mod._render_failure_statistics(empty) == ""


def test_render_failure_statistics_historical_and_monte_text():
    historical_html = mod._render_failure_statistics(make_historical_report_data())
    monte_html = mod._render_failure_statistics(make_report_data())

    assert "Portfolio Sustainability Analysis" in historical_html
    assert "Historical Window Analysis evaluates your financial plan" in historical_html

    assert "Portfolio Sustainability Analysis" in monte_html
    assert "Monte Carlo Analysis evaluates your financial plan" in monte_html


def test_render_failure_statistics_raises_for_unknown_method():
    report_data = make_report_data(
        analysis_summary={
            "Analysis Method": "Unknown Method",
        }
    )

    with pytest.raises(ValueError, match="Unknown risk analysis method"):
        mod._render_failure_statistics(report_data)


def test_render_percentile_table_can_be_disabled_or_empty():
    disabled = make_report_data(
        report_options={
            "analysis": {
                "include_percentile_table": False,
            }
        }
    )
    empty = make_report_data(percentile_table=[])

    assert mod._render_percentile_table(disabled) == ""
    assert mod._render_percentile_table(empty) == ""


def test_render_percentile_table_contains_rows_and_explanation():
    report_data = make_report_data()

    html = mod._render_percentile_table(report_data)

    assert "Percentile Portfolio Table" in html
    assert "10th Percentile" in html
    assert "Median" in html
    assert "$90,000" in html
    assert "approximately 10% of scenarios" in html


def test_render_year_list_empty_and_populated():
    empty_html = mod._render_year_list([], empty_message="No years.")
    populated_html = mod._render_year_list(
        [
            {
                "Retirement Start Year": 1966,
                "Result": "Worst",
                "Ending Portfolio": 0.0,
            }
        ]
    )

    assert empty_html == "<p>No years.</p>"

    assert "1966" in populated_html
    assert "Worst" in populated_html
    assert "$0" in populated_html


def test_render_historical_insights_only_for_historical_method():
    assert mod._render_historical_insights(make_report_data()) == ""

    html = mod._render_historical_insights(make_historical_report_data())

    assert "Historical Window Insights" in html
    assert "Best Historical Retirement Start Years" in html
    assert "Worst Historical Retirement Start Years" in html
    assert "Sequence-of-Returns Risk" in html
    assert "Historical commentary." in html
    assert "&lt;unsafe commentary&gt;" in html


def test_render_historical_insights_can_be_disabled():
    report_data = make_historical_report_data(
        report_options={
            "analysis": {
                "include_historical_window_insights": False,
            }
        }
    )

    assert mod._render_historical_insights(report_data) == ""


def test_render_historical_insights_returns_empty_for_non_dict_insights():
    report_data = make_historical_report_data()
    report_data.historical_insights = "not-a-dict"

    assert mod._render_historical_insights(report_data) == ""


def test_render_historical_insights_includes_plot_when_present(tmp_path, monkeypatch):
    image = tmp_path / "historical.png"
    image.write_text("fake", encoding="utf-8")

    monkeypatch.setattr(mod, "_get_output_folder", lambda: str(tmp_path))

    report_data = make_historical_report_data(
        plot_assets={
            "historical_window_highlights": {
                "path": str(image),
                "alt": "Historical alt text",
            }
        }
    )

    html = mod._render_historical_insights(report_data)

    assert "historical-window-plot" in html
    assert 'alt="Historical alt text"' in html


def test_render_monte_carlo_insights_only_for_monte_method():
    assert mod._render_monte_carlo_insights(make_historical_report_data()) == ""

    html = mod._render_monte_carlo_insights(make_report_data())

    assert "Monte Carlo Insights" in html
    assert "Sequence-of-Returns Risk" in html
    assert "What Monte Carlo Suggests" in html


def test_render_monte_carlo_insights_can_be_disabled():
    report_data = make_report_data(
        report_options={
            "analysis": {
                "include_monte_carlo_insights": False,
            }
        }
    )

    assert mod._render_monte_carlo_insights(report_data) == ""


def test_render_risk_observations_can_be_disabled_or_empty():
    disabled = make_report_data(
        report_options={
            "analysis": {
                "include_risk_observations": False,
            }
        }
    )
    empty = make_report_data(
        analysis_summary={
            "Analysis Method": "Monte Carlo Analysis",
            "Risk Observations": [],
        }
    )

    assert mod._render_risk_observations(disabled) == ""
    assert mod._render_risk_observations(empty) == ""


def test_render_risk_observations_escapes_items():
    html = mod._render_risk_observations(make_report_data())

    assert "Risk Observations" in html
    assert "Some scenarios depleted the portfolio." in html
    assert "&lt;unsafe observation&gt;" in html


def test_render_plot_assets_returns_empty_without_asset_or_when_disabled(tmp_path):
    no_asset = make_report_data(plot_assets={})
    disabled = make_report_data(
        report_options={
            "analysis": {
                "include_portfolio_projection": False,
            }
        },
        plot_assets={
            "portfolio_range_projection": {
                "path": str(tmp_path / "plot.png"),
            }
        },
    )

    assert mod._render_plot_assets(no_asset) == ""
    assert mod._render_plot_assets(disabled) == ""


def test_render_plot_assets_historical_and_monte_carlo_text(tmp_path, monkeypatch):
    image = tmp_path / "plot.png"
    image.write_text("fake", encoding="utf-8")
    monkeypatch.setattr(mod, "_get_output_folder", lambda: str(tmp_path))

    historical = make_historical_report_data(
        plot_assets={
            "portfolio_range_projection": {
                "path": str(image),
                "alt": "Historical projection",
            }
        }
    )
    monte = make_report_data(
        plot_assets={
            "portfolio_range_projection": {
                "path": str(image),
                "alt": "Monte projection",
            }
        }
    )

    historical_html = mod._render_plot_assets(historical)
    monte_html = mod._render_plot_assets(monte)

    assert "Portfolio Projection Across Historical Market Periods" in historical_html
    assert 'alt="Historical projection"' in historical_html

    assert "Portfolio Projection Across Simulated Market Scenarios" in monte_html
    assert 'alt="Monte projection"' in monte_html


def test_render_plot_assets_raises_for_unknown_method(tmp_path, monkeypatch):
    image = tmp_path / "plot.png"
    image.write_text("fake", encoding="utf-8")
    monkeypatch.setattr(mod, "_get_output_folder", lambda: str(tmp_path))

    report_data = make_report_data(
        analysis_summary={
            "Analysis Method": "Unknown Method",
        },
        plot_assets={
            "portfolio_range_projection": {
                "path": str(image),
            }
        },
    )

    with pytest.raises(ValueError, match="Unknown risk analysis method"):
        mod._render_plot_assets(report_data)


def test_render_warnings_returns_empty_without_warnings():
    assert mod._render_warnings(make_report_data(warnings=[])) == ""


def test_render_warnings_escapes_text():
    html = mod._render_warnings(make_report_data(warnings=["<bad warning>"]))

    assert "Warnings" in html
    assert "&lt;bad warning&gt;" in html


def test_build_html_document_contains_core_sections():
    report_data = make_report_data()

    html = mod._build_html_document(report_data)

    assert "<title>WARPSimLab Risk Analysis Report</title>" in html
    assert "Executive Summary" in html
    assert "Method Explanation" in html
    assert "Portfolio Sustainability Analysis" in html
    assert "Monte Carlo Insights" in html
    assert "Percentile Portfolio Table" in html
    assert "Risk Observations" in html
    assert "WARPSimLab" in html


def test_build_html_document_escapes_title():
    report_data = make_report_data(
        report_metadata={
            "Report Title": "<Unsafe Risk Report>",
        }
    )

    html = mod._build_html_document(report_data)

    assert "<title>&lt;Unsafe Risk Report&gt;</title>" in html


def test_write_html_uses_method_specific_prefix(tmp_path):
    monte = make_report_data()
    historical = make_historical_report_data()

    monte_path = mod._write_html(monte, str(tmp_path), "abc")
    historical_path = mod._write_html(historical, str(tmp_path), "abc")

    assert Path(monte_path).name == "monte_carlo_risk_abc.html"
    assert Path(historical_path).name == "historical_window_risk_abc.html"

    assert Path(monte_path).exists()
    assert Path(historical_path).exists()


def test_write_percentile_csv_returns_none_without_rows(tmp_path):
    report_data = make_report_data(percentile_table=[])

    assert mod._write_percentile_csv(report_data, str(tmp_path), "abc") is None


def test_write_percentile_csv_writes_union_of_headers(tmp_path):
    report_data = make_report_data(
        percentile_table=[
            {"Year": 2026, "Median": 100000.0},
            {"Year": 2027, "10th Percentile": 90000.0},
        ]
    )

    path = mod._write_percentile_csv(report_data, str(tmp_path), "abc")

    assert Path(path).name == "risk_percentiles_abc.csv"

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert rows[0]["Year"] == "2026"
    assert "Median" in rows[0]
    assert "10th Percentile" in rows[0]


def test_write_failure_csv_returns_none_without_stats(tmp_path):
    report_data = make_report_data(failure_statistics={})

    assert mod._write_failure_csv(report_data, str(tmp_path), "abc") is None


def test_write_failure_csv_writes_metric_value_rows(tmp_path):
    report_data = make_report_data()

    path = mod._write_failure_csv(report_data, str(tmp_path), "abc")

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    assert rows[0] == ["Metric", "Value"]
    assert ["Simulated Shortfall Rate", "10.0"] in rows


def test_write_summary_csv_skips_dict_and_list_values(tmp_path):
    report_data = make_report_data(
        analysis_summary={
            "Analysis Method": "Monte Carlo Analysis",
            "Scenario Count": 100,
            "Risk Observations": ["skip me"],
            "Nested": {"skip": True},
        }
    )

    path = mod._write_summary_csv(report_data, str(tmp_path), "abc")

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    assert rows[0] == ["Metric", "Value"]
    assert ["Analysis Method", "Monte Carlo Analysis"] in rows
    assert ["Scenario Count", "100"] in rows
    assert not any(row[0] == "Risk Observations" for row in rows[1:])
    assert not any(row[0] == "Nested" for row in rows[1:])


def test_write_summary_csv_returns_none_without_summary(tmp_path):
    report_data = make_report_data(analysis_summary={})

    assert mod._write_summary_csv(report_data, str(tmp_path), "abc") is None


def test_write_csv_outputs_returns_existing_paths(tmp_path):
    report_data = make_report_data()

    paths = mod._write_csv_outputs(report_data, str(tmp_path), "abc")

    assert len(paths) == 3
    assert (tmp_path / "risk_summary_abc.csv").exists()
    assert (tmp_path / "risk_failure_statistics_abc.csv").exists()
    assert (tmp_path / "risk_percentiles_abc.csv").exists()


def test_generate_risk_report_returns_error_when_no_outputs_selected(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_get_output_folder", lambda: str(tmp_path))

    report_data = make_report_data(
        report_options={
            "output": {
                "generate_html": False,
                "generate_csv": False,
            }
        }
    )

    result = mod.generate_risk_report(report_data)

    assert result.success is False
    assert result.report_path is None
    assert result.output_folder == str(tmp_path)
    assert result.errors == ["No Risk Report output format was selected."]


def test_generate_risk_report_writes_html_and_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_get_output_folder", lambda: str(tmp_path))
    monkeypatch.setattr(mod, "_safe_report_id", lambda report_id: "safe-id")

    report_data = make_report_data()

    result = mod.generate_risk_report(report_data)

    assert result.success is True
    assert result.errors == []
    assert result.output_folder == str(tmp_path)
    assert result.report_path == str(tmp_path / "monte_carlo_risk_safe-id.html")

    assert (tmp_path / "monte_carlo_risk_safe-id.html").exists()
    assert (tmp_path / "risk_summary_safe-id.csv").exists()
    assert (tmp_path / "risk_failure_statistics_safe-id.csv").exists()
    assert (tmp_path / "risk_percentiles_safe-id.csv").exists()


def test_generate_risk_report_writes_csv_only_when_html_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_get_output_folder", lambda: str(tmp_path))
    monkeypatch.setattr(mod, "_safe_report_id", lambda report_id: "safe-id")

    report_data = make_report_data(
        report_options={
            "output": {
                "generate_html": False,
                "generate_csv": True,
            }
        }
    )

    result = mod.generate_risk_report(report_data)

    assert result.success is True
    assert result.errors == []
    assert result.report_path == str(tmp_path / "risk_summary_safe-id.csv")

    assert not (tmp_path / "monte_carlo_risk_safe-id.html").exists()
    assert (tmp_path / "risk_summary_safe-id.csv").exists()


def test_generate_risk_report_returns_error_when_write_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_get_output_folder", lambda: str(tmp_path))
    monkeypatch.setattr(mod, "_safe_report_id", lambda report_id: "safe-id")

    def raise_on_write(*args, **kwargs):
        raise OSError("cannot write")

    monkeypatch.setattr(mod, "_write_html", raise_on_write)

    report_data = make_report_data()

    result = mod.generate_risk_report(report_data)

    assert result.success is False
    assert result.report_path is None
    assert result.output_folder == str(tmp_path)
    assert result.errors == ["cannot write"]