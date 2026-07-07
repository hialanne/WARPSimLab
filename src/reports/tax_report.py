# tax_report.py

import os
import csv

from src.reports.report_data import ReportResult, TaxReportData

from src.reports.report_plot_helpers import (
    save_tax_by_year_report_plot,
    save_effective_tax_rate_report_plot,
    save_taxable_income_source_report_plot,
)

from src.reports.report_common import (
    safe as _safe,
    get_report_output_folder,
    safe_report_id,
    render_report_header,
    render_footer,
    render_base_css,
)


PERCENT_KEY_HINTS = {
    "Rate",
    "Percent",
    "Bracket",
}


def _get_report_option(report_options, path, default=False):
    target = report_options

    for key in path:
        if not isinstance(target, dict) or key not in target:
            return default
        target = target[key]

    return target


def _is_percent_key(key):
    return any(hint in str(key) for hint in PERCENT_KEY_HINTS)


def _fmt_value(value, key=None):
    if value is None:
        return "N/A"

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(value, str):
        return value

    if key is not None and _is_percent_key(key):
        if isinstance(value, (int, float)):
            if 0 <= value <= 1:
                return f"{value * 100:.2f}%"
            return f"{value:.2f}%"
        return str(value)

    if isinstance(value, float):
        if value < 0:
            return f"-${abs(value):,.0f}"
        return f"${value:,.0f}"

    if isinstance(value, int):
        return f"{value:,}"

    return str(value)


def _render_kv_table(data, emphasize_keys=None):
    emphasize_keys = set(emphasize_keys or [])
    rows = []

    for key, value in data.items():
        row_class = " class='emphasis-row'" if key in emphasize_keys else ""
        value_class = " class='negative'" if isinstance(value, (int, float)) and value < 0 else ""

        rows.append(
            f"<tr{row_class}>"
            f"<th>{_safe(key)}</th>"
            f"<td{value_class}>{_safe(_fmt_value(value, key=key))}</td>"
            "</tr>"
        )

    return "<table class='kv-table'><tbody>" + "\n".join(rows) + "</tbody></table>"


def _render_highlights(report_data):
    summary = report_data.lifetime_tax_summary

    highlights = {
        "Lifetime Total Tax": summary.get("Lifetime Total Tax"),
        "Lifetime Federal Income Tax": summary.get("Lifetime Federal Income Tax"),
        "Lifetime State Income Tax": summary.get("Lifetime State Income Tax"),
        "Lifetime Payroll Tax": summary.get("Lifetime Payroll Tax"),
        "Average Effective Tax Rate": summary.get("Average Effective Tax Rate"),
        "Highest Marginal Tax Bracket": summary.get("Highest Marginal Tax Bracket"),
    }

    cards = []

    for label, value in highlights.items():
        cards.append(
            f"""
            <div class="highlight-card">
                <div class="highlight-label">{_safe(label)}</div>
                <div class="highlight-value">{_safe(_fmt_value(value, key=label))}</div>
            </div>
            """
        )

    return f"""
<section>
    <h2>Tax Highlights</h2>
    <div class="highlight-grid">
        {''.join(cards)}
    </div>
</section>
"""


def _render_tax_overview(report_data):
    return """
<section>
    <h2>Tax Overview</h2>
    <p class="section-intro">
        This report summarizes the taxes estimated by WARPSimLab over the simulation period.
        It is intended to explain how federal income taxes, state income taxes, payroll taxes,
        Roth assets, HSA assets, and required minimum distributions affect the simulated plan.
    </p>
    <p class="section-intro">
        This report is not a tax return, does not replace tax software, and should not be
        interpreted as professional tax advice.
    </p>
</section>
"""


def _render_tax_model_limitations(report_data):
    return """
<section>
    <h2>Tax Model Limitations</h2>
    <p class="section-intro">
        WARPSimLab uses simplified, planning-grade tax calculations. The goal is to
        explain broad retirement tax behavior, not to reproduce a tax return.
    </p>
    <ul>
        <li>Social Security benefits are currently treated as ordinary taxable income rather than using the detailed federal provisional-income rules.</li>
        <li>Qualified dividends and long-term capital gains are modeled with simplified tax handling and may not match an actual tax return.</li>
        <li>Emergency pre-tax withdrawals use a one-pass approximation. A fully precise calculation would require an iterative withdrawal/tax solve.</li>
        <li>Roth accounts are modeled as tax-free retirement buckets. The simulator does not currently optimize Roth withdrawal timing or Roth conversions.</li>
        <li>HSA accounts are modeled as simplified tax-free buckets. The simulator does not currently distinguish qualified medical withdrawals from other uses.</li>
        <li>State income taxes are planning-grade approximations and may omit deductions, credits, local taxes, and state-specific retirement income rules.</li>
    </ul>
</section>
"""


def _render_tax_settings(report_data):
    return f"""
<section>
    <h2>Tax Settings Used</h2>
    <p class="section-intro">
        These are the tax calculation settings used when the simulation was run.
    </p>
    <div class="card-grid two-col">
        <div class="summary-card">
            {_render_kv_table(report_data.tax_settings)}
        </div>
    </div>
</section>
"""


def _render_lifetime_tax_summary(report_data):
    return f"""
<section>
    <h2>Lifetime Tax Summary</h2>
    <p class="section-intro">
        This section summarizes estimated taxes across the full simulation period.
    </p>
    <div class="card-grid two-col">
        <div class="summary-card">
            {_render_kv_table(
                report_data.lifetime_tax_summary,
                emphasize_keys={
                    "Lifetime Total Tax",
                    "Average Effective Tax Rate",
                    "Highest Marginal Tax Bracket",
                },
            )}
        </div>
    </div>
</section>
"""


def _render_tax_source_summary(report_data):
    return f"""
<section>
    <h2>Tax Source Breakdown</h2>
    <p class="section-intro">
        These values summarize the income sources that contributed to taxable income
        and tax exposure during the simulation.
    </p>
    <div class="card-grid two-col">
        <div class="summary-card">
            {_render_kv_table(report_data.tax_source_summary)}
        </div>
    </div>
</section>
"""


def _render_roth_analysis(report_data):
    return f"""
<section>
    <h2>Roth Analysis</h2>
    <p class="section-intro">
        WARPSimLab currently treats Roth accounts as tax-free retirement buckets.
        Roth withdrawals occur only after post-tax and pre-tax assets are depleted
        under the current withdrawal order.
    </p>
    <div class="card-grid two-col">
        <div class="summary-card">
            {_render_kv_table(report_data.roth_summary)}
        </div>
    </div>
</section>
"""


def _render_hsa_analysis(report_data):
    return f"""
<section>
    <h2>HSA Analysis</h2>
    <p class="section-intro">
        WARPSimLab currently treats HSA accounts as simplified tax-free buckets.
        HSA withdrawals occur only after post-tax, pre-tax, and Roth assets are depleted.
    </p>
    <div class="card-grid two-col">
        <div class="summary-card">
            {_render_kv_table(report_data.hsa_summary)}
        </div>
    </div>
</section>
"""


def _render_rmd_analysis(report_data):
    return f"""
<section>
    <h2>Required Minimum Distribution Analysis</h2>
    <p class="section-intro">
        Required Minimum Distributions can increase taxable income later in retirement.
        This section summarizes when RMDs appear and their total simulated impact.
    </p>
    <div class="card-grid two-col">
        <div class="summary-card">
            {_render_kv_table(report_data.rmd_summary)}
        </div>
    </div>
</section>
"""


def _render_yearly_tax_table(report_data):
    rows = report_data.yearly_tax_rows or []

    if not rows:
        return ""

    columns = [
        "Year",
        "Age",
        "Gross Income",
        "Federal Income Tax",
        "State Income Tax",
        "Payroll Tax",
        "Total Taxes",
        "Effective Tax Rate",
        "Marginal Tax Bracket",
        "RMD",
        "Roth Withdrawals",
        "HSA Withdrawals",
    ]

    header_html = "".join(f"<th>{_safe(column)}</th>" for column in columns)

    body_rows = []

    for row in rows:
        cells = []
        for column in columns:
            value = row.get(column)
            css_class = " class='negative'" if isinstance(value, (int, float)) and value < 0 else ""
            cells.append(
                f"<td{css_class}>{_safe(_fmt_value(value, key=column))}</td>"
            )

        body_rows.append("<tr>" + "".join(cells) + "</tr>")

    return f"""
<section>
    <h2>Year-by-Year Tax Details</h2>
    <p class="section-intro">
        This detailed table provides the annual tax values used to generate the
        summaries and charts presented earlier in the report.
    </p>
    <table class="wide-table">
        <thead>
            <tr>{header_html}</tr>
        </thead>
        <tbody>
            {''.join(body_rows)}
        </tbody>
    </table>
</section>
"""




def _render_tax_insights(report_data):
    summary = report_data.lifetime_tax_summary
    sources = report_data.tax_source_summary
    rmd = report_data.rmd_summary
    rows = report_data.yearly_tax_rows

    observations = []

    lifetime_total = float(summary.get("Lifetime Total Tax") or 0.0)
    federal = float(summary.get("Lifetime Federal Income Tax") or 0.0)
    state = float(summary.get("Lifetime State Income Tax") or 0.0)
    payroll = float(summary.get("Lifetime Payroll Tax") or 0.0)

    #
    # Overall tax burden
    #

    if lifetime_total > 0:
        observations.append(
            f"Federal income taxes account for {100.0 * federal / lifetime_total:.1f}% of lifetime taxes."
        )

        observations.append(
            f"State income taxes account for {100.0 * state / lifetime_total:.1f}% of lifetime taxes."
        )

        observations.append(
            f"Payroll taxes account for {100.0 * payroll / lifetime_total:.1f}% of lifetime taxes."
        )

    highest_rate = summary.get("Average Effective Tax Rate")

    if highest_rate is not None:
        observations.append(
            f"Average effective tax rate over the simulation is {highest_rate * 100.0:.2f}%."
        )

    #
    # Payroll taxes
    #

    if payroll > 0.0:
        observations.append(
            "Payroll taxes decline and eventually disappear once earned employment income ends."
        )

    #
    # Required Minimum Distributions
    #

    first_rmd = rmd.get("First RMD Year")

    if first_rmd:
        observations.append(
            f"Required Minimum Distributions begin in {first_rmd}."
        )

        observations.append(
            "Once RMDs begin, they increase taxable retirement income."
        )

    #
    # Annual characteristics
    #

    if rows:
        highest = max(rows, key=lambda r: r["Total Taxes"])

        observations.append(
            f"The largest annual tax bill occurs in {highest['Year']} "
            f"(${highest['Total Taxes']:,.0f})."
        )

    #
    # Tax-free retirement assets
    #

    if float(report_data.roth_summary.get("Total Roth Withdrawals") or 0.0) > 0.0:
        observations.append(
            "Roth withdrawals provide tax-free retirement income under the current simulation model."
        )

    if float(report_data.hsa_summary.get("Total HSA Withdrawals") or 0.0) > 0.0:
        observations.append(
            "HSA withdrawals provide an additional tax-free retirement funding source under the current simulation model."
        )

    html = "\n".join(
        f"<li>{_safe(item)}</li>"
        for item in observations
    )

    return f"""
<section>
    <h2>Tax Insights</h2>
    <p class="section-intro">
        This section summarizes the most important tax characteristics of the
        simulation and explains why they occurred. These observations are
        generated directly from the simulation results.
    </p>

    <ul>
        {html}
    </ul>

</section>
"""


def _render_warnings(report_data):
    if not report_data.warnings:
        return ""

    items = "\n".join(f"<li>{_safe(w)}</li>" for w in report_data.warnings)

    return f"""
<section>
    <h2>Warnings</h2>
    <ul class="warnings">
        {items}
    </ul>
</section>
"""


def _build_tax_plot_assets(report_data, output_folder, safe_id):
    rows = report_data.yearly_tax_rows or []

    if not rows:
        return {}

    return {
        "tax_by_year": {
            "path": save_tax_by_year_report_plot(
                output_folder,
                "tax_by_year.png",
                rows,
            ),
            "title": "Taxes by Year",
            "alt": "Taxes by year",
        },
        "effective_tax_rate": {
            "path": save_effective_tax_rate_report_plot(
                output_folder,
                "effective_tax_rate.png",
                rows,
            ),
            "title": "Effective Tax Rate by Year",
            "alt": "Effective tax rate by year",
        },
        "retirement_withdrawal_sources": {
            "path": save_taxable_income_source_report_plot(
                output_folder,
                "retirement_withdrawal_sources.png",
                rows,
            ),
            "title": "Retirement Withdrawal Sources by Year",
            "alt": "Retirement withdrawal sources by year",
        },
    }


def _render_tax_plots(plot_assets, output_folder):
    if not plot_assets:
        return ""

    cards = []

    for key in [
        "tax_by_year",
        "effective_tax_rate",
        "retirement_withdrawal_sources",
    ]:
        asset = plot_assets.get(key)

        if not asset or not asset.get("path"):
            continue

        image_src = os.path.relpath(asset["path"], start=output_folder)

        cards.append(f"""
        <div class="plot-card">
            <h3>{_safe(asset.get("title", "Tax Plot"))}</h3>
            <img src="{_safe(image_src)}" alt="{_safe(asset.get("alt", "Tax plot"))}">
        </div>
        """)

    if not cards:
        return ""

    return f"""
<section>
    <h2>Tax Visuals</h2>
    <p class="section-intro">
        These charts show how estimated taxes and withdrawal sources change over time.
    </p>
    <div class="plot-stack">
        {''.join(cards)}
    </div>
</section>
"""


def _write_yearly_tax_csv(report_data, output_folder, safe_id):
    filename = os.path.join(
        output_folder,
        f"tax_year_by_year_{safe_id}.csv",
    )

    rows = report_data.yearly_tax_rows

    if not rows:
        return

    columns = list(rows[0].keys())

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=columns,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def _write_summary_csv(report_data, output_folder, safe_id):
    filename = os.path.join(
        output_folder,
        f"tax_lifetime_summary_{safe_id}.csv",
    )

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(["Statistic", "Value"])

        for key, value in report_data.lifetime_tax_summary.items():
            writer.writerow([key, value])


def _write_tax_source_csv(report_data, output_folder, safe_id):
    filename = os.path.join(
        output_folder,
        f"tax_source_breakdown_{safe_id}.csv",
    )

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(["Income Source", "Amount"])

        for key, value in report_data.tax_source_summary.items():
            writer.writerow([key, value])


def generate_tax_report(report_data) -> ReportResult:
    if isinstance(report_data, dict):
        report_data = TaxReportData(**report_data)

    output_folder = get_report_output_folder()
    os.makedirs(output_folder, exist_ok=True)

    report_id = report_data.report_metadata.get("Report ID", "tax_report")
    safe_id = safe_report_id(report_id)

    report_path = os.path.join(
        output_folder,
        f"tax_report_{safe_id}.html",
    )

    asset_folder = os.path.join(
        output_folder,
        f"tax_report_{safe_id}_assets",
    )

    plot_assets = _build_tax_plot_assets(
        report_data,
        asset_folder,
        safe_id,
    )

    report_options = report_data.report_options or {}

    sections = report_options.get("sections", {})
    output = report_options.get("output", {})

    if not output.get("generate_html", True):
        return ReportResult(
            success=True,
            report_path=None,
            output_folder=output_folder,
            warnings=list(report_data.warnings),
            errors=[],
        )

    roth_html = ""
    if sections.get("include_roth_analysis", True):
        roth_html = _render_roth_analysis(report_data)

    hsa_html = ""
    if sections.get("include_hsa_analysis", True):
        hsa_html = _render_hsa_analysis(report_data)

    rmd_html = ""
    if sections.get("include_rmd_analysis", True):
        rmd_html = _render_rmd_analysis(report_data)

    insights_html = _render_tax_insights(report_data)
    
    html_text = f"""<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>WARPSimLab Tax Report</title>

    <style>
    {render_base_css()}

    .summary-card .kv-table th {{
        width: auto;
        white-space: nowrap;
        padding-right: 16px;
    }}

    .summary-card .kv-table td {{
        width: 1%;
        white-space: nowrap;
        text-align: right;
    }}

    .wide-table {{
        font-size: 13px;
    }}

    .wide-table td:not(:first-child),
    .wide-table th:not(:first-child) {{
        text-align: right;
    }}
    </style>
</head>
<body>
    <main class="report-page">

        {render_report_header(
            report_data,
            title="Tax Report",
            market_wording="user-provided tax settings and simulated market conditions",
        )}

        {_render_highlights(report_data)}

        {_render_tax_overview(report_data)}

        {_render_tax_model_limitations(report_data)}

        {_render_tax_settings(report_data)}

        {_render_lifetime_tax_summary(report_data)}

        {insights_html}

        {_render_tax_plots(plot_assets, output_folder)}

        {_render_tax_source_summary(report_data)}

        {rmd_html}

        {roth_html}

        {hsa_html}

        {_render_yearly_tax_table(report_data)}

        {_render_warnings(report_data)}

        {render_footer()}

    </main>
</body>
</html>
"""

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_text)

        if output.get("generate_csv", True):
            _write_yearly_tax_csv(
                report_data,
                output_folder,
                safe_id,
            )

            _write_summary_csv(
                report_data,
                output_folder,
                safe_id,
            )

            _write_tax_source_csv(
                report_data,
                output_folder,
                safe_id,
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