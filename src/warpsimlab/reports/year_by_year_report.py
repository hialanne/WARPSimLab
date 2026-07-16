# year_by_year_report.py
import csv
import os

from src.warpsimlab.reports.report_data import ReportResult, YearByYearReportData
from src.warpsimlab.reports.report_common import (
    safe as _safe,
    get_report_output_folder as _get_output_folder,
    safe_report_id as _safe_report_id,
    render_report_header,
    render_footer,
    render_base_css,
)

COMPACT_COLUMNS = [
    "Year",
    "Age",
    "Age 1",
    "Age 2",
    "Gross Income",
    "Taxes",
    "Household Expenses",
    "Portfolio Withdrawals",
    "Net Cash Flow",
    "Total Portfolio",
    "Total Assets / Net Worth",
]

DETAILED_COLUMNS = [
    "Year",
    "Age",
    "Age 1",
    "Age 2",
    "Wages",
    "Social Security",
    "Pensions and Annuities",
    "RMD",
    "Portfolio Withdrawals",
    "Gross Income",
    "Taxes",
    "Household Expenses",
    "Net Cash Flow",
    "Fund Expenses",
    "Pre-Tax Assets",
    "Post-Tax Assets",
    "Roth Assets",
    "HSA Assets",
    "Real Estate",
    "Total Portfolio",
    "Total Assets / Net Worth",
]

YEAR_KEYS = {"Year"}
AGE_KEYS = {"Age", "Age 1", "Age 2"}


def _fmt_value(value, key=None):
    if value is None:
        return ""

    if key in YEAR_KEYS or key in AGE_KEYS:
        try:
            return str(int(value))
        except (TypeError, ValueError):
            return str(value)

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(value, int):
        return f"{value:,}"

    if isinstance(value, float):
        if value < 0:
            return f"-${abs(value):,.0f}"
        return f"${value:,.0f}"

    return str(value)


def _selected_columns(report_data):
    detail = report_data.report_options.get("table_detail", "Compact")

    if detail == "Detailed":
        candidates = DETAILED_COLUMNS
    else:
        candidates = COMPACT_COLUMNS

    available = set()
    for row in report_data.year_rows:
        available.update(row.keys())

    return [column for column in candidates if column in available]


def _calculate_summary_statistics(report_data):
    rows = report_data.year_rows

    if not rows:
        return {}

    def total(column):
        return sum(
            float(row.get(column, 0.0) or 0.0)
            for row in rows
        )

    def maximum(column):
        return max(
            float(row.get(column, 0.0) or 0.0)
            for row in rows
        )

    last = rows[-1]

    return {
        "Years Simulated": len(rows) - 1,
        "Total Lifetime Income": total("Gross Income"),
        "Total Taxes Paid": total("Taxes"),
        "Total Household Expenses": total("Household Expenses"),
        "Total Portfolio Withdrawals": total("Portfolio Withdrawals"),
        "Largest Annual Portfolio Withdrawal": maximum("Portfolio Withdrawals"),
        "Ending Portfolio": last.get("Total Portfolio", 0.0),
        "Ending Net Worth": last.get("Total Assets / Net Worth", 0.0),
    }


def _render_summary_statistics(report_data):
    stats = _calculate_summary_statistics(report_data)

    if not stats:
        return ""

    items = list(stats.items())

    left_items = items[:4]
    right_items = items[4:]

    def build_side(side_items):
        rows = []

        for label, value in side_items:

            if isinstance(value, (int, float)):
                if label == "Years Simulated":
                    formatted = f"{int(value)}"
                else:
                    formatted = _fmt_value(value)
            else:
                formatted = str(value)

            rows.append(f"""
<tr>
    <td class="summary-label">{_safe(label)}</td>
    <td class="summary-value">{_safe(formatted)}</td>
</tr>
""")

        return f"""
<table class="summary-table">
<tbody>
{''.join(rows)}
</tbody>
</table>
"""

    return f"""
<section>

<h2>Summary Statistics</h2>

<div class="summary-grid">

{build_side(left_items)}

{build_side(right_items)}

</div>

</section>
"""


def _render_year_table(report_data):
    columns = _selected_columns(report_data)
    insert_breaks = report_data.report_options.get("insert_5_year_breaks", True)

    header_html = "".join(f"<th>{_safe(column)}</th>" for column in columns)

    body_rows = []

    for index, row in enumerate(report_data.year_rows):
        row_class = ""

        if insert_breaks and index > 0 and index % 5 == 0:
            row_class = " class='five-year-break'"

        cells = []

        for column in columns:
            value = row.get(column)
            css_class = ""

            if isinstance(value, (int, float)) and value < 0:
                css_class = " class='negative'"

            cells.append(
                f"<td{css_class}>{_safe(_fmt_value(value, key=column))}</td>"
            )

        body_rows.append(
            f"<tr{row_class}>"
            + "".join(cells)
            + "</tr>"
        )

    return f"""
<section>
    <h2>Year-by-Year Details</h2>
    <p class="section-intro">
        This table shows one deterministic simulation path using the selected assumptions.
        Monte Carlo and Historical Window detail rows are intentionally excluded from this report.
    </p>
    <div class="table-scroll">
        <table class="wide-table year-table">
            <thead>
                <tr>{header_html}</tr>
            </thead>
            <tbody>
                {''.join(body_rows)}
            </tbody>
        </table>
    </div>
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


def _render_css():
    return f"""
<style>

{render_base_css()}

.table-scroll {{
    overflow-x: auto;
}}

.year-table {{
    font-size: 12px;
}}

.year-table th,
.year-table td {{
    text-align: right;
    white-space: nowrap;
}}

.year-table th:first-child,
.year-table td:first-child {{
    text-align: left;
}}

.year-table tbody tr:nth-child(even) {{
    background: #f8f8f8;
}}

.five-year-break td {{
    border-top: 3px solid #2e7d32;
}}

.summary-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 40px;
    margin-top: 10px;
    margin-bottom: 20px;
}}

.summary-table {{
    border-collapse: collapse;
    width: 100%;
}}

.summary-table td {{
    border: 1px solid #ddd;
    padding: 8px;
}}

.summary-label {{
    font-weight: bold;
    width: 65%;
}}

.summary-value {{
    text-align: right;
    white-space: nowrap;
}}

@media print {{

    .table-scroll {{
        overflow-x: visible;
    }}

    .year-table {{
        font-size: 10px;
    }}

}}

</style>
"""


def _build_html_document(report_data):
    title = report_data.report_metadata.get(
        "Report Title",
        "Year-by-Year Details Report",
    )

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{_safe(title)}</title>
{_render_css()}
</head>
<body>
<main class="report-page">

{render_report_header(
    report_data,
    title="Year-by-Year Details Report",
    market_wording="simulated market conditions",
)}

{_render_summary_statistics(report_data)}
{_render_year_table(report_data)}
{_render_warnings(report_data)}

{render_footer()}

</main>
</body>
</html>
"""


def _write_csv(report_data, output_folder, safe_report_id):
    columns = _selected_columns(report_data)
    csv_path = os.path.join(
        output_folder,
        f"year_by_year_details_{safe_report_id}.csv",
    )

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=columns,
            extrasaction="ignore",
        )

        writer.writeheader()

        for row in report_data.year_rows:
            writer.writerow({
                column: row.get(column, "")
                for column in columns
            })

    return csv_path


def _write_html(report_data, output_folder, safe_report_id):
    html_path = os.path.join(
        output_folder,
        f"year_by_year_details_{safe_report_id}.html",
    )

    html_text = _build_html_document(report_data)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_text)

    return html_path


def generate_year_by_year_report(
    report_data: YearByYearReportData,
) -> ReportResult:
    output_folder = _get_output_folder()
    os.makedirs(output_folder, exist_ok=True)

    report_id = report_data.report_metadata.get(
        "Report ID",
        "year_by_year_report",
    )
    safe_report_id = _safe_report_id(report_id)

    generate_html = report_data.report_options.get("generate_html", True)
    generate_csv = report_data.report_options.get("generate_csv", True)

    if not generate_html and not generate_csv:
        return ReportResult(
            success=False,
            output_folder=output_folder,
            warnings=report_data.warnings,
            errors=["No Year-by-Year report output format was selected."],
        )

    html_path = None
    csv_path = None

    try:
        if generate_html:
            html_path = _write_html(
                report_data,
                output_folder,
                safe_report_id,
            )

        if generate_csv:
            csv_path = _write_csv(
                report_data,
                output_folder,
                safe_report_id,
            )

        return ReportResult(
            success=True,
            report_path=html_path or csv_path,
            output_folder=output_folder,
            warnings=report_data.warnings,
            errors=[],
        )

    except Exception as exc:
        return ReportResult(
            success=False,
            report_path=html_path or csv_path,
            output_folder=output_folder,
            warnings=report_data.warnings,
            errors=[str(exc)],
        )