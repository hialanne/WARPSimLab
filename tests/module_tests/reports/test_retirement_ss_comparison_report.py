from __future__ import annotations

from types import SimpleNamespace

from src.warpsimlab.reports import retirement_ss_comparison_report as mod


def make_case(
    retirement_age,
    ss_age,
    *,
    current=False,
    current_retirement=False,
    current_ss=False,
    ending_portfolio=100000.0,
    depletion_percent=10.0,
    husband_ss=24000.0,
    wife_ss=12000.0,
):
    return {
        "requested_retirement_age": int(retirement_age),
        "requested_social_security_age": int(ss_age),
        "is_current_timing": current,
        "is_current_retirement_timing": current_retirement,
        "is_current_social_security_timing": current_ss,
        "deterministic_portfolio_at_retirement": 200000.0,
        "deterministic_ending_portfolio": ending_portfolio,
        "deterministic_total_social_security": 500000.0,
        "deterministic_monthly_retirement_income": 5000.0,
        "deterministic_final_monthly_retirement_income": 6000.0,
        "deterministic_lifetime_cash_flow_shortfall": 100000.0,
        "depletion": {
            "reaching_zero_percent": depletion_percent,
        },
        "husband": {
            "social_security_amount": husband_ss,
        },
        "wife": {
            "social_security_amount": wife_ss,
        },
    }


def make_report_data(cases):
    return SimpleNamespace(
        baseline={
            "household_retirement_age": 67,
            "household_social_security_age": 67,
            "husband": {
                "current_age": 60,
                "retirement_age": 67,
                "social_security_age": 67,
                "social_security_amount": 24000.0,
            },
            "wife": {
                "current_age": 58,
                "retirement_age": 65,
                "social_security_age": 65,
                "social_security_amount": 12000.0,
            },
        },
        retirement_ages=[65, 67, 69],
        social_security_ages=[65, 67, 69],
        comparison_cases=cases,
        report_options={
            "output": {
                "open_report_in_browser": False,
            },
        },
        warnings=[],
    )


def test_format_helpers():
    assert mod._fmt_currency(None) == "N/A"
    assert mod._fmt_currency(1234.0) == "$1,234"
    assert mod._fmt_currency(-1234.0) == "-$1,234"

    assert mod._fmt_percent(None) == "N/A"
    assert mod._fmt_percent(12.34) == "12.3%"

    assert mod._fmt_age(None) == "N/A"
    assert mod._fmt_age(67.9) == "67"


def test_find_case_uses_both_retirement_and_ss_age():
    report_data = make_report_data(
        [
            make_case(65, 67),
            make_case(67, 67),
            make_case(67, 69),
        ]
    )

    result = mod._find_case(
        report_data,
        67,
        69,
    )

    assert result["requested_retirement_age"] == 67
    assert result["requested_social_security_age"] == 69

    assert mod._find_case(
        report_data,
        69,
        65,
    ) is None


def test_timing_label_marks_current():
    assert mod._timing_label(67, True) == "67 - Current"
    assert mod._timing_label(65, False) == "65"


def test_current_row_class():
    assert (
        mod._current_row_class(
            {"is_current_timing": True}
        )
        == " class='current-row'"
    )

    assert (
        mod._current_row_class(
            {"is_current_timing": False}
        )
        == ""
    )


def test_render_current_timing_contains_household_definitions():
    report_data = make_report_data([])

    html = mod._render_current_timing(
        report_data
    )

    assert "Household Retirement Age" in html
    assert "Household Social Security Age" in html

    assert (
        "Household Retirement Age is the age when the household has no"
        in html
    )

    assert (
        "Household Social Security Age is the age"
        in html
    )

    assert (
        "when the last household member begins receiving Social Security."
        in html
    )

    assert "Husband" in html
    assert "Wife" in html


def test_render_retirement_comparison_marks_current_and_zero():
    report_data = make_report_data(
        [
            make_case(65, 67),
            make_case(
                67,
                67,
                current=True,
                current_retirement=True,
                ending_portfolio=0.0,
            ),
            make_case(69, 67),
        ]
    )

    html = mod._render_retirement_comparison(
        report_data
    )

    assert "Retirement Timing Comparison" in html
    assert "67 - Current" in html
    assert "current-row" in html
    assert "ending-portfolio-zero" in html
    assert "$0" in html

    assert "Scenarios" in html
    assert "That Depleted Portfolio shows the percentage" in html
    assert "lower is better" in html


def test_render_social_security_comparison_uses_monthly_values():
    report_data = make_report_data(
        [
            make_case(
                67,
                67,
                current=True,
                current_ss=True,
                husband_ss=24000.0,
                wife_ss=12000.0,
            ),
        ]
    )

    html = mod._render_social_security_comparison(
        report_data
    )

    assert "Social Security Timing Comparison" in html
    assert "67 - Current" in html

    # Annual values are divided by 12 for this table.
    assert "$2,000" in html
    assert "$1,000" in html

    assert "Total Social Security Received" in html
    assert "Lifetime Cash Flow Shortfall" in html

    assert (
        "the amount received during the simulation"
        in html
    )


def test_render_social_security_comparison_handles_single_person():
    case = make_case(
        67,
        67,
        current=True,
        current_ss=True,
    )

    case["wife"] = None

    report_data = make_report_data([case])

    html = mod._render_social_security_comparison(
        report_data
    )

    assert "Husband Monthly SS" in html
    assert "Wife Monthly SS" in html
    assert "N/A" in html


def test_interaction_matrix_contains_all_ss_headers():
    cases = []

    for retirement_age in [65, 67, 69]:
        for ss_age in [65, 67, 69]:
            cases.append(
                make_case(
                    retirement_age,
                    ss_age,
                    current=(
                        retirement_age == 67
                        and ss_age == 67
                    ),
                )
            )

    report_data = make_report_data(cases)

    html = mod._render_interaction_matrix(
        report_data
    )

    assert "Retirement and Social Security Interaction" in html
    assert "SS 65" in html
    assert "SS 67" in html
    assert "SS 69" in html


def test_interaction_matrix_marks_current_cell():
    report_data = make_report_data(
        [
            make_case(67, 67),
        ]
    )

    report_data.retirement_ages = [67]
    report_data.social_security_ages = [67]

    html = mod._render_interaction_matrix(
        report_data
    )

    assert "class='current-cell'" in html


def test_interaction_matrix_marks_zero_portfolio():
    report_data = make_report_data(
        [
            make_case(
                67,
                67,
                ending_portfolio=0.0,
            ),
        ]
    )

    report_data.retirement_ages = [67]
    report_data.social_security_ages = [67]

    html = mod._render_interaction_matrix(
        report_data
    )

    assert "matrix-portfolio-zero" in html
    assert "$0" in html


def test_interaction_matrix_marks_positive_portfolio():
    report_data = make_report_data(
        [
            make_case(
                67,
                67,
                ending_portfolio=100000.0,
            ),
        ]
    )

    report_data.retirement_ages = [67]
    report_data.social_security_ages = [67]

    html = mod._render_interaction_matrix(
        report_data
    )

    assert "matrix-portfolio-positive" in html
    assert "$100,000" in html


def test_interaction_matrix_missing_case_renders_na():
    report_data = make_report_data([])

    report_data.retirement_ages = [67]
    report_data.social_security_ages = [67]

    html = mod._render_interaction_matrix(
        report_data
    )

    assert "<td>N/A</td>" in html


def test_methodology_contains_historical_window_sampling_explanation():
    report_data = make_report_data([])

    html = mod._render_methodology(
        report_data
    )

    assert "ages 62 through 70" in html
    assert "every fourth valid historical starting year" in html

    assert "current" in html
    assert "retirement and Social Security ages use all available historical" in html