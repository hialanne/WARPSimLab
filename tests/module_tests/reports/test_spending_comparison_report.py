from __future__ import annotations

from types import SimpleNamespace

from src.warpsimlab.reports import spending_comparison_report as mod


def make_case(
    spending_percentage,
    *,
    current=False,
    ending_portfolio=100000.0,
    depletion_percent=10.0,
    first_year_expenses=40000.0,
    lifetime_expenses=1000000.0,
    lifetime_taxes=100000.0,
    cash_flow_shortfall=200000.0,
    uncovered_expense=0.0,
):
    return {
        "spending_percentage": float(spending_percentage),
        "is_current_spending": current,
        "deterministic_ending_portfolio": ending_portfolio,
        "deterministic_first_year_expenses": first_year_expenses,
        "deterministic_lifetime_expenses": lifetime_expenses,
        "deterministic_lifetime_taxes": lifetime_taxes,
        "deterministic_lifetime_cash_flow_shortfall": cash_flow_shortfall,
        "deterministic_lifetime_uncovered_expense": uncovered_expense,
        "depletion": {
            "windows_reaching_zero_percent": depletion_percent,
        },
        "ending_portfolio": {
            "minimum": 0.0,
            "10th_percentile": 10000.0,
            "25th_percentile": 25000.0,
            "median": 50000.0,
            "75th_percentile": 75000.0,
            "90th_percentile": 90000.0,
            "maximum": 100000.0,
        },
    }


def make_report_data(cases):
    return SimpleNamespace(
        baseline_percentage=100.0,
        comparison_cases=cases,
        warnings=[],
    )


def test_format_helpers():
    assert mod._fmt_currency(None) == "N/A"
    assert mod._fmt_currency(1234.0) == "$1,234"
    assert mod._fmt_currency(-1234.0) == "-$1,234"

    assert mod._fmt_percent(None) == "N/A"
    assert mod._fmt_percent(12.34) == "12.3%"

    assert mod._fmt_spending_percent(80.0) == "80%"
    assert mod._fmt_spending_percent(87.5) == "87.5%"


def test_find_spending_case_and_baseline():
    report_data = make_report_data(
        [
            make_case(80.0),
            make_case(100.0, current=True),
            make_case(120.0),
        ]
    )

    assert mod._find_baseline_case(report_data)["spending_percentage"] == 100.0
    assert mod._find_spending_case(report_data, 80.0)["spending_percentage"] == 80.0
    assert mod._find_spending_case(report_data, 999.0) is None


def test_render_highlights_marks_current_spending_and_zero_portfolio():
    report_data = make_report_data(
        [
            make_case(80.0),
            make_case(
                100.0,
                current=True,
                ending_portfolio=0.0,
            ),
            make_case(120.0),
        ]
    )

    html = mod._render_highlights(report_data)

    assert "80%" in html
    assert "100% - Current Spending" in html
    assert "120%" in html
    assert "ending-portfolio-zero" in html
    assert "$0" in html


def test_render_portfolio_durability_marks_baseline_row():
    report_data = make_report_data(
        [
            make_case(80.0),
            make_case(100.0, current=True),
            make_case(120.0),
        ]
    )

    html = mod._render_portfolio_durability(report_data)

    assert "Spending and Portfolio Health" in html
    assert "Lower depletion percentages are better." in html
    assert "baseline-row" in html
    assert "100% - Current Spending" in html


def test_render_portfolio_outcomes_has_market_condition_headers():
    report_data = make_report_data(
        [
            make_case(100.0, current=True),
        ]
    )

    html = mod._render_portfolio_outcomes(report_data)

    assert "Portfolio Risk by Spending Level" in html
    assert "Less Favorable Market" in html
    assert "Median" in html
    assert "More Favorable Market" in html
    assert "10th Percentile" in html
    assert "90th Percentile" in html


def test_render_portfolio_outcomes_marks_zero_values_red():
    case = make_case(100.0, current=True)

    case["ending_portfolio"] = {
        "minimum": 0.0,
        "10th_percentile": 0.0,
        "25th_percentile": 10000.0,
        "median": 50000.0,
        "75th_percentile": 75000.0,
        "90th_percentile": 90000.0,
        "maximum": 100000.0,
    }

    html = mod._render_portfolio_outcomes(
        make_report_data([case])
    )

    assert html.count("ending-portfolio-zero") == 2


def test_has_uncovered_expenses_detects_positive_value():
    report_data = make_report_data(
        [
            make_case(80.0, uncovered_expense=0.0),
            make_case(100.0, uncovered_expense=1.0),
        ]
    )

    assert mod._has_uncovered_expenses(report_data) is True


def test_has_uncovered_expenses_false_when_all_zero():
    report_data = make_report_data(
        [
            make_case(80.0, uncovered_expense=0.0),
            make_case(100.0, uncovered_expense=0.0),
        ]
    )

    assert mod._has_uncovered_expenses(report_data) is False


def test_financial_effects_only_shows_uncovered_column_when_needed():
    no_uncovered = make_report_data(
        [
            make_case(100.0, current=True),
        ]
    )

    html = mod._render_financial_effects(no_uncovered)

    assert "Uncovered Expenses" not in html

    with_uncovered = make_report_data(
        [
            make_case(
                100.0,
                current=True,
                uncovered_expense=5000.0,
            ),
        ]
    )

    html = mod._render_financial_effects(with_uncovered)

    assert "Uncovered Expenses" in html
    assert "uncovered-expense" in html
    assert "$5,000" in html


def test_render_warnings_escapes_html():
    report_data = SimpleNamespace(
        warnings=["Bad <value>"],
    )

    html = mod._render_warnings(report_data)

    assert "Warnings" in html
    assert "Bad &lt;value&gt;" in html