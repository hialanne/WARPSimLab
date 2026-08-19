# spending_comparison_report.py

import os

from src.warpsimlab.reports.report_data import (
    ReportResult,
    SpendingComparisonReportData,
)

from src.warpsimlab.reports.report_common import (
    safe as _safe,
    get_report_output_folder,
    safe_report_id,
    render_report_header,
    render_footer,
    render_base_css,
    open_html_report_in_browser,
)


def _fmt_currency(value):
    if value is None:
        return "N/A"

    value = float(value)

    if value < 0:
        return f"-${abs(value):,.0f}"

    return f"${value:,.0f}"


def _fmt_percent(value):
    if value is None:
        return "N/A"

    return f"{float(value):.1f}%"


def _fmt_spending_percent(value):
    if value is None:
        return "N/A"

    value = float(value)

    if value.is_integer():
        return f"{int(value)}%"

    return f"{value:g}%"


def _find_baseline_case(report_data):
    baseline_percentage = float(
        report_data.baseline_percentage
    )

    for case in report_data.comparison_cases:
        if float(case.get("spending_percentage", 0.0)) == baseline_percentage:
            return case

    return None


def _find_spending_case(report_data, spending_percentage):
    target = float(spending_percentage)

    for case in report_data.comparison_cases:
        if float(case.get("spending_percentage", 0.0)) == target:
            return case

    return None


def _render_highlights(report_data):
    highlight_percentages = (
        80.0,
        100.0,
        120.0,
    )

    rows = []

    for spending_percentage in highlight_percentages:
        case = _find_spending_case(
            report_data,
            spending_percentage,
        )

        if case is None:
            continue

        depletion = case.get(
            "depletion",
            {},
        )

        ending_portfolio = case.get(
            "deterministic_ending_portfolio"
        )

        first_year_expenses = case.get(
            "deterministic_first_year_expenses"
        )

        spending_label = _fmt_spending_percent(
            case.get("spending_percentage")
        )

        if case.get("is_current_spending", False):
            spending_label += " - Current Spending"

        rows.append(
            f"""
            <div class="highlight-grid spending-highlight-row">

                <div class="highlight-card">
                    <div class="highlight-label">
                        {_safe(spending_label)}
                    </div>
                    <div class="highlight-value">
                        {_safe(_fmt_currency(
                            first_year_expenses
                        ))}
                    </div>
                    <div class="highlight-note">
                        First-Year Spending
                    </div>
                </div>

                <div class="highlight-card">
                    <div class="highlight-label">
                        Ending Portfolio
                    </div>
                    <div class="highlight-value">
                        {_safe(_fmt_currency(
                            ending_portfolio
                        ))}
                    </div>
                </div>

                <div class="highlight-card">
                    <div class="highlight-label">
                        Scenarios That Depleted Portfolio
                    </div>
                    <div class="highlight-value">
                        {_safe(_fmt_percent(
                            depletion.get(
                                "windows_reaching_zero_percent"
                            )
                        ))}
                    </div>
                </div>

            </div>
            """
        )

    if not rows:
        return ""

    return f"""
<section>
    <h2>Spending Highlights</h2>

    {''.join(rows)}

</section>
"""


def _baseline_row_class(case, baseline_percentage):
    if (
        float(case.get("spending_percentage", 0.0))
        == float(baseline_percentage)
    ):
        return " class='baseline-row'"

    return ""


def _render_portfolio_durability(report_data):
    rows = []

    baseline = _find_baseline_case(report_data)

    baseline_first_year_spending = None

    if baseline is not None:
        baseline_first_year_spending = baseline.get(
            "deterministic_first_year_expenses"
        )

    for case in report_data.comparison_cases:
        depletion = case.get(
            "depletion",
            {},
        )

        row_class = _baseline_row_class(
            case,
            report_data.baseline_percentage,
        )

        spending_text = _fmt_spending_percent(
            case.get("spending_percentage")
        )

        if case.get("is_current_spending", False):
            spending_text += " - Current Spending"

        first_year_spending = case.get(
            "deterministic_first_year_expenses"
        )

        spending_delta = None

        if (
            first_year_spending is not None
            and baseline_first_year_spending is not None
        ):
            spending_delta = (
                float(first_year_spending)
                - float(baseline_first_year_spending)
            )

        rows.append(
            f"""
            <tr{row_class}>
                <td>{_safe(spending_text)}</td>
                <td>{_safe(_fmt_currency(
                    first_year_spending
                ))}</td>
                <td>{_safe(_fmt_currency(
                    spending_delta
                ))}</td>
                <td>{_safe(_fmt_percent(
                    depletion.get(
                        "windows_reaching_zero_percent"
                    )
                ))}</td>
            </tr>
            """
        )

    return f"""
<section>
    <h2>Spending and Portfolio Health</h2>

    <p class="section-intro">
        This table compares modeled first-year spending and how often
        historical scenarios depleted the portfolio at each spending level.
        The 100% row represents current modeled household spending.
    </p>

    <table class="wide-table comparison-table">
        <thead>
            <tr>
                <th>Spending Level</th>
                <th>First-Year Spending</th>
                <th>Delta from Baseline</th>
                <th>Scenarios That Depleted Portfolio</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
</section>
"""


def _render_portfolio_outcomes(report_data):
    rows = []

    for case in report_data.comparison_cases:
        outcomes = case.get(
            "ending_portfolio",
            {},
        )

        row_class = _baseline_row_class(
            case,
            report_data.baseline_percentage,
        )

        spending_text = _fmt_spending_percent(
            case.get("spending_percentage")
        )

        if case.get("is_current_spending", False):
            spending_text += " - Current"

        rows.append(
            f"""
            <tr{row_class}>
                <td>{_safe(spending_text)}</td>
                <td>{_safe(_fmt_currency(
                    outcomes.get("minimum")
                ))}</td>
                <td>{_safe(_fmt_currency(
                    outcomes.get("10th_percentile")
                ))}</td>
                <td>{_safe(_fmt_currency(
                    outcomes.get("25th_percentile")
                ))}</td>
                <td>{_safe(_fmt_currency(
                    outcomes.get("median")
                ))}</td>
                <td>{_safe(_fmt_currency(
                    outcomes.get("75th_percentile")
                ))}</td>
                <td>{_safe(_fmt_currency(
                    outcomes.get("90th_percentile")
                ))}</td>
                <td>{_safe(_fmt_currency(
                    outcomes.get("maximum")
                ))}</td>
            </tr>
            """
        )

    return f"""
<section>
    <h2>Portfolio Risk by Spending Level</h2>

    <p class="section-intro">
        These results show how different spending levels affect the range of
        possible ending portfolio values. Lower-percentile results represent
        less favorable market conditions, while higher-percentile results
        represent more favorable conditions. The table
        shows how spending levels depend on market performance
        and how much financial cushion remains for down markets.
    </p>

    <div class="table-scroll">
        <table class="wide-table comparison-table outcome-table">
            <thead>
                <tr>
                    <th>Spending</th>
                    <th>Lowest</th>
                    <th>10th Percentile</th>
                    <th>25th Percentile</th>
                    <th>Median</th>
                    <th>75th Percentile</th>
                    <th>90th Percentile</th>
                    <th>Highest</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </div>
</section>
"""


def _has_uncovered_expenses(report_data):
    for case in report_data.comparison_cases:
        uncovered = case.get(
            "deterministic_lifetime_uncovered_expense",
            0.0,
        )

        if float(uncovered or 0.0) > 0.0:
            return True

    return False


def _render_financial_effects(report_data):
    include_uncovered = _has_uncovered_expenses(
        report_data
    )

    rows = []

    for case in report_data.comparison_cases:
        row_class = _baseline_row_class(
            case,
            report_data.baseline_percentage,
        )

        spending_text = _fmt_spending_percent(
            case.get("spending_percentage")
        )

        if case.get("is_current_spending", False):
            spending_text += " - Current"

        expenses = case.get(
            "deterministic_lifetime_expenses"
        )

        taxes = case.get(
            "deterministic_lifetime_taxes"
        )

        cash_flow_shortfall = case.get(
            "deterministic_lifetime_cash_flow_shortfall"
        )

        uncovered = case.get(
            "deterministic_lifetime_uncovered_expense"
        )

        uncovered_cell = ""

        if include_uncovered:
            uncovered_cell = (
                "<td>"
                + _safe(
                    _fmt_currency(
                        uncovered
                    )
                )
                + "</td>"
            )

        rows.append(
            f"""
            <tr{row_class}>
                <td>{_safe(spending_text)}</td>
                <td>{_safe(_fmt_currency(
                    expenses
                ))}</td>
                <td>{_safe(_fmt_currency(
                    taxes
                ))}</td>
                <td>{_safe(_fmt_currency(
                    cash_flow_shortfall
                ))}</td>
                {uncovered_cell}
            </tr>
            """
        )

    uncovered_header = ""

    if include_uncovered:
        uncovered_header = (
            "<th>Uncovered Expenses</th>"
        )

    return f"""
<section>
    <h2>Lifetime Financial Effects</h2>

    <p class="section-intro">
        These values show the cumulative lifetime financial effects of each
        spending level. They compare total household expenses, taxes, the amount
        of portfolio assets needed to cover negative Cash Flow (withdrawals from
        the portfolio), and expenses that could not be covered after the portfolio
        was empty.
    </p>

    <table class="wide-table comparison-table lifetime-effects-table">
        <thead>
            <tr>
                <th>Spending Level</th>
                <th>Household Expenses</th>
                <th>Taxes</th>
                <th>Cash Flow Shortfall</th>
                {uncovered_header}
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
</section>
"""


def _render_warnings(report_data):
    if not report_data.warnings:
        return ""

    items = "\n".join(
        f"<li>{_safe(warning)}</li>"
        for warning in report_data.warnings
    )

    return f"""
<section>
    <h2>Warnings</h2>
    <ul class="warnings">
        {items}
    </ul>
</section>
"""


def generate_spending_comparison_report(
    report_data: SpendingComparisonReportData,
) -> ReportResult:
    output_folder = get_report_output_folder()
    os.makedirs(output_folder, exist_ok=True)

    report_id = report_data.report_metadata.get(
        "Report ID",
        "spending_comparison",
    )

    safe_id = safe_report_id(report_id)

    report_path = os.path.join(
        output_folder,
        f"spending_comparison_{safe_id}.html",
    )

    html_text = f"""<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>WARPSimLab Spending Comparison Report</title>

    <style>

    {render_base_css()}

    .comparison-table th:not(:first-child),
    .comparison-table td:not(:first-child) {{
        text-align: right;
    }}

    .baseline-row td {{
        font-weight: bold;
        background: #eef6ee;
    }}

    .highlight-note {{
        margin-top: 4px;
        color: #666;
        font-size: 13px;
    }}

    .baseline-row td:first-child {{
        border-left: 4px solid #2e7d32;
    }}

    .outcome-table {{
        font-size: 12px;
    }}

    .outcome-table th,
    .outcome-table td {{
        white-space: nowrap;
    }}

    .lifetime-effects-table {{
        table-layout: fixed;
    }}

    .lifetime-effects-table thead th {{
        height: 54px;
        white-space: normal;
        line-height: 1.25;
        vertical-align: middle;
    }}

    .table-scroll {{
        overflow-x: auto;
    }}

    </style>
</head>

<body>
    <main class="report-page">

        {render_report_header(
            report_data,
            title="Spending Comparison Report",
            market_wording="historical market conditions",
        )}

        {_render_highlights(report_data)}

        {_render_portfolio_durability(report_data)}

        {_render_portfolio_outcomes(report_data)}

        {_render_financial_effects(report_data)}

        {_render_warnings(report_data)}

        {render_footer()}

    </main>
</body>
</html>
"""

    try:
        with open(
            report_path,
            "w",
            encoding="utf-8",
        ) as f:
            f.write(html_text)

        output_options = report_data.report_options.get(
            "output",
            {},
        )

        if output_options.get(
            "open_report_in_browser",
            False,
        ):
            open_html_report_in_browser(
                report_path
            )

        return ReportResult(
            success=True,
            report_path=report_path,
            output_folder=output_folder,
            warnings=list(report_data.warnings),
            errors=[],
        )

    except Exception as exc:
        return ReportResult(
            success=False,
            report_path=None,
            output_folder=output_folder,
            warnings=list(report_data.warnings),
            errors=[str(exc)],
        )