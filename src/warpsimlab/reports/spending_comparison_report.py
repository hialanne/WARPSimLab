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


def _render_highlights(report_data):
    baseline = _find_baseline_case(report_data)

    if baseline is None:
        return ""

    depletion = baseline.get("depletion", {})
    ending_portfolio = baseline.get(
        "ending_portfolio",
        {},
    )

    return f"""
<section>
    <h2>Current Spending Highlights</h2>

    <p class="section-intro">
        The 100% case represents the household spending entered in the
        current WARPSimLab scenario. Other spending levels are compared
        with this baseline.
    </p>

    <div class="highlight-grid">

        <div class="highlight-card">
            <div class="highlight-label">
                Current Spending
            </div>
            <div class="highlight-value">
                {_safe(_fmt_spending_percent(
                    baseline.get("spending_percentage")
                ))}
            </div>
        </div>

        <div class="highlight-card">
            <div class="highlight-label">
                Historical Windows Reaching Zero
            </div>
            <div class="highlight-value">
                {_safe(_fmt_percent(
                    depletion.get(
                        "windows_reaching_zero_percent"
                    )
                ))}
            </div>
        </div>

        <div class="highlight-card">
            <div class="highlight-label">
                Median Ending Portfolio
            </div>
            <div class="highlight-value">
                {_safe(_fmt_currency(
                    ending_portfolio.get("median")
                ))}
            </div>
        </div>

    </div>
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

    for case in report_data.comparison_cases:
        depletion = case.get("depletion", {})

        row_class = _baseline_row_class(
            case,
            report_data.baseline_percentage,
        )

        spending_text = _fmt_spending_percent(
            case.get("spending_percentage")
        )

        if case.get("is_current_spending", False):
            spending_text += " - Current Spending"

        rows.append(
            f"""
            <tr{row_class}>
                <td>{_safe(spending_text)}</td>
                <td>{_safe(depletion.get(
                    "historical_window_count",
                    "N/A",
                ))}</td>
                <td>{_safe(depletion.get(
                    "windows_reaching_zero_count",
                    "N/A",
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
    <h2>Portfolio Durability</h2>

    <p class="section-intro">
        This table compares how often the modeled portfolio reached zero
        across the historical windows evaluated at each spending level.
        The 100% row represents current modeled household spending.
    </p>

    <table class="wide-table comparison-table">
        <thead>
            <tr>
                <th>Spending Level</th>
                <th>Historical Windows</th>
                <th>Windows Reaching Zero</th>
                <th>Reaching Zero</th>
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
    <h2>Portfolio Outcomes</h2>

    <p class="section-intro">
        Ending portfolio values show the distribution of modeled outcomes
        across the same set of historical windows for each spending level.
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
        distribution = case.get(
            "lifetime_uncovered_expense",
            {},
        )

        if float(distribution.get("maximum", 0.0)) > 0.0:
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
            "lifetime_expenses",
            {},
        )

        taxes = case.get(
            "lifetime_taxes",
            {},
        )

        cash_flow_shortfall = case.get(
            "lifetime_cash_flow_shortfall",
            {},
        )

        uncovered = case.get(
            "lifetime_uncovered_expense",
            {},
        )

        uncovered_cell = ""

        if include_uncovered:
            uncovered_cell = (
                "<td>"
                + _safe(
                    _fmt_currency(
                        uncovered.get("median")
                    )
                )
                + "</td>"
            )

        rows.append(
            f"""
            <tr{row_class}>
                <td>{_safe(spending_text)}</td>
                <td>{_safe(_fmt_currency(
                    expenses.get("median")
                ))}</td>
                <td>{_safe(_fmt_currency(
                    taxes.get("median")
                ))}</td>
                <td>{_safe(_fmt_currency(
                    cash_flow_shortfall.get("median")
                ))}</td>
                {uncovered_cell}
            </tr>
            """
        )

    uncovered_header = ""

    if include_uncovered:
        uncovered_header = (
            "<th>Median Uncovered Expenses</th>"
        )

    return f"""
<section>
    <h2>Financial Effects</h2>

    <p class="section-intro">
        These values show median cumulative financial amounts across the
        historical windows evaluated for each spending level. Cash Flow
        Shortfall represents modeled amounts drawn from portfolio assets
        to cover negative household Cash Flow.
    </p>

    <table class="wide-table comparison-table">
        <thead>
            <tr>
                <th>Spending Level</th>
                <th>Median Household Expenses</th>
                <th>Median Taxes</th>
                <th>Median Cash Flow Shortfall</th>
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