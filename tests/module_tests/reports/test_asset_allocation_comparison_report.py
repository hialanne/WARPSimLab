from __future__ import annotations

from types import SimpleNamespace

from src.warpsimlab.reports import asset_allocation_comparison_report as mod


def make_case(
    equity_percentage,
    *,
    bonds=30.0,
    cash=10.0,
    current=False,
    ending_portfolio=100000.0,
    depletion_percent=10.0,
    highlight_only=False,
):
    return {
        "equity_percentage": float(equity_percentage),
        "bond_percentage": float(bonds),
        "cash_percentage": float(cash),
        "is_current_allocation": current,
        "highlight_only": highlight_only,
        "deterministic_ending_portfolio": ending_portfolio,
        "depletion": {
            "windows_reaching_zero_percent": depletion_percent,
        },
        "ending_portfolio": {
            "10th_percentile": 10000.0,
            "25th_percentile": 25000.0,
            "median": 50000.0,
            "75th_percentile": 75000.0,
            "90th_percentile": 90000.0,
        },
    }


def make_report_data(cases):
    return SimpleNamespace(
        comparison_cases=cases,
        historical_plot_assets={},
        warnings=[],
    )


def test_format_helpers():
    assert mod._fmt_currency(None) == "N/A"
    assert mod._fmt_currency(1234.0) == "$1,234"
    assert mod._fmt_currency(-1234.0) == "-$1,234"

    assert mod._fmt_percent(12.34) == "12.3%"

    assert mod._fmt_allocation_percent(60.0) == "60%"
    assert mod._fmt_allocation_percent(62.5) == "62.5%"


def test_find_current_case():
    current = make_case(
        60.0,
        current=True,
    )

    report_data = make_report_data(
        [
            make_case(40.0),
            current,
            make_case(80.0),
        ]
    )

    assert mod._find_current_case(report_data) is current


def test_find_equity_case():
    report_data = make_report_data(
        [
            make_case(40.0),
            make_case(60.0),
            make_case(80.0),
        ]
    )

    assert mod._find_equity_case(
        report_data,
        60.0,
    )["equity_percentage"] == 60.0

    assert mod._find_equity_case(
        report_data,
        99.0,
    ) is None


def test_table_cases_excludes_highlight_only_cases():
    report_data = make_report_data(
        [
            make_case(40.0),
            make_case(
                60.0,
                highlight_only=True,
            ),
            make_case(80.0),
        ]
    )

    result = mod._table_cases(report_data)

    assert len(result) == 2
    assert [case["equity_percentage"] for case in result] == [
        40.0,
        80.0,
    ]


def test_allocation_label_marks_current_case():
    assert (
        mod._allocation_label(
            make_case(
                60.0,
                current=True,
            )
        )
        == "60% - Current"
    )

    assert mod._allocation_label(
        make_case(40.0)
    ) == "40%"


def test_render_highlights_marks_zero_ending_portfolio():
    report_data = make_report_data(
        [
            make_case(40.0),
            make_case(
                60.0,
                current=True,
                ending_portfolio=0.0,
            ),
            make_case(80.0),
        ]
    )

    html = mod._render_current_allocation_highlights(
        report_data
    )

    assert "Allocation Highlights" in html
    assert "60% - Current" in html
    assert "ending-portfolio-zero" in html
    assert "$0" in html


def test_render_portfolio_results_marks_current_and_zero():
    report_data = make_report_data(
        [
            make_case(40.0),
            make_case(
                60.0,
                current=True,
                ending_portfolio=0.0,
            ),
            make_case(80.0),
        ]
    )

    html = mod._render_portfolio_durability(
        report_data
    )

    assert "Portfolio Results by Allocation" in html
    assert "60% - Current" in html
    assert "baseline-row" in html
    assert "ending-portfolio-zero" in html
    assert "$0" in html


def test_render_portfolio_outcomes_has_market_condition_headers():
    report_data = make_report_data(
        [
            make_case(60.0, current=True),
        ]
    )

    html = mod._render_portfolio_outcomes(
        report_data
    )

    assert "Portfolio Risk by Allocation" in html
    assert "Less Favorable Market" in html
    assert "Median" in html
    assert "More Favorable Market" in html
    assert "10th Percentile" in html
    assert "25th Percentile" in html
    assert "75th Percentile" in html
    assert "90th Percentile" in html


def test_render_portfolio_outcomes_marks_zero_percentiles():
    case = make_case(
        60.0,
        current=True,
    )

    case["ending_portfolio"] = {
        "10th_percentile": 0.0,
        "25th_percentile": 0.0,
        "median": 50000.0,
        "75th_percentile": 75000.0,
        "90th_percentile": 90000.0,
    }

    html = mod._render_portfolio_outcomes(
        make_report_data([case])
    )

    assert html.count("ending-portfolio-zero") == 2


def test_historical_visualization_requires_all_three_plots():
    report_data = SimpleNamespace(
        historical_plot_assets={
            "current": {
                "path": "current.png",
                "equity_percentage": 60.0,
            },
            "minus_20": {
                "path": "minus.png",
                "equity_percentage": 40.0,
            },
        }
    )

    assert (
        mod._render_historical_window_risk_visualization(
            report_data,
            ".",
        )
        == ""
    )


def test_method_note_describes_allocation_rules():
    html = mod._render_method_note(
        SimpleNamespace()
    )

    assert "Only the modeled Stock/Bond/Cash" in html
    assert "current household bond-to-cash ratio" in html
    assert "pre-tax, post-tax, Roth, and HSA" in html
    assert "Real estate is not included" in html