# risk_report.py

import csv
import os
from datetime import datetime

from src.warpsimlab.reports.report_data import ReportResult

from src.warpsimlab.reports.report_common import (
    safe as _safe,
    safe_report_id as _safe_report_id,
    get_report_output_folder as _get_output_folder,
    relative_asset_path as _relative_asset_path,
    render_report_header,
    render_footer,
    render_base_css,
    open_html_report_in_browser,
)

YEAR_KEYS = {
    "Year",
    "Start Year",
    "End Year",
    "Retirement Start Year",
    "Historical Window Start Year",
    "Historical Window End Year",
    "Earliest Simulation Start Year",
    "Latest Simulation Start Year",
    "Earliest Portfolio Depletion Year",
    "Median Portfolio Depletion Year",
    "Latest Portfolio Depletion Year",
    "Best Historical Retirement Start Year",
    "Worst Historical Retirement Start Year",}

PERCENT_KEY_HINTS = {
    "Rate",
    "Percent",
    "Probability",
    "Shortfall",
}

COUNT_KEY_HINTS = {
    "Count",
    "Scenarios",
    "Windows",
    "Simulations",
}


def _is_percent_key(key):
    key = str(key)
    return any(hint in key for hint in PERCENT_KEY_HINTS)


def _is_year_key(key):
    return str(key) in YEAR_KEYS


def _is_count_key(key):
    key = str(key)
    return any(hint in key for hint in COUNT_KEY_HINTS)


def _fmt_value(value, key=None):
    if value is None:
        return "N/A"

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(value, str):
        return value

    if key is not None and _is_year_key(key):
        try:
            return str(int(value))
        except (TypeError, ValueError):
            return str(value)

    if key is not None and _is_percent_key(key):
        key_text = str(key)

        if "Percentile" not in key_text:
            try:
                return f"{float(value):.2f}%"
            except (TypeError, ValueError):
                return str(value)

    if key is not None and _is_count_key(key):
        try:
            return f"{int(value):,}"
        except (TypeError, ValueError):
            return str(value)

    if isinstance(value, int):
        return f"{value:,}"

    if isinstance(value, float):
        if value < 0:
            return f"-${abs(value):,.0f}"
        return f"${value:,.0f}"

    return str(value)


def _get_report_option(report_options, path, default=False):
    target = report_options

    for key in path:
        if not isinstance(target, dict) or key not in target:
            return default
        target = target[key]

    return target


def _render_kv_table(data, emphasize_keys=None):
    emphasize_keys = set(emphasize_keys or [])
    rows = []

    for key, value in data.items():
        row_class = " class='emphasis-row'" if key in emphasize_keys else ""
        value_class = ""

        try:
            if isinstance(value, (int, float)) and value < 0:
                value_class = " class='negative'"
        except TypeError:
            pass

        rows.append(
            f"<tr{row_class}>"
            f"<th>{_safe(key)}</th>"
            f"<td{value_class}>{_safe(_fmt_value(value, key=key))}</td>"
            "</tr>"
        )

    return "<table class='kv-table'><tbody>" + "\n".join(rows) + "</tbody></table>"


def _render_simple_table(rows, empty_message="No entries."):
    if not rows:
        return f"<p>{_safe(empty_message)}</p>"

    headers = []
    for row in rows:
        if isinstance(row, dict):
            for key in row.keys():
                if key not in headers:
                    headers.append(key)

    if not headers:
        items = "".join(f"<li>{_safe(_fmt_value(row))}</li>" for row in rows)
        return f"<ul>{items}</ul>"

    header_html = "".join(f"<th>{_safe(header)}</th>" for header in headers)

    body_rows = []
    for row in rows:
        cells = []
        for header in headers:
            value = row.get(header)
            css_class = ""

            if isinstance(value, (int, float)) and value < 0:
                css_class = " class='negative'"

            cells.append(
                f"<td{css_class}>{_safe(_fmt_value(value, key=header))}</td>"
            )

        body_rows.append("<tr>" + "".join(cells) + "</tr>")

    return f"""
<table class="wide-table">
    <thead>
        <tr>{header_html}</tr>
    </thead>
    <tbody>
        {''.join(body_rows)}
    </tbody>
</table>
"""


def _render_percentile_table_rows(rows):
    body_rows = []

    for row in rows:
        body_rows.append(
            f"""
            <tr>
                <td>
                    {_safe(_fmt_value(row.get("Year"), key="Year"))}
                </td>
                <td>
                    {_safe(_fmt_value(row.get("10th Percentile"), key="10th Percentile"))}
                </td>
                <td>
                    {_safe(_fmt_value(row.get("25th Percentile"), key="25th Percentile"))}
                </td>
                <td>
                    {_safe(_fmt_value(row.get("Median"), key="Median"))}
                </td>
                <td>
                    {_safe(_fmt_value(row.get("75th Percentile"), key="75th Percentile"))}
                </td>
                <td>
                    {_safe(_fmt_value(row.get("90th Percentile"), key="90th Percentile"))}
                </td>
            </tr>
            """
        )

    return f"""
<table class="wide-table">
    <thead>
        <tr>
            <th rowspan="2">Year</th>
            <th colspan="2" class="market-left">Less Favorable Market</th>
            <th>Median</th>
            <th colspan="2">More Favorable Market</th>
        </tr>
        <tr>
            <th>10th Percentile</th>
            <th>25th Percentile</th>
            <th></th>
            <th>75th Percentile</th>
            <th>90th Percentile</th>
        </tr>
    </thead>
    <tbody>
        {''.join(body_rows)}
    </tbody>
</table>
"""

def _render_executive_summary(report_data):
    if not _get_report_option(
        report_data.report_options,
        ["general", "include_executive_summary"],
        True,
    ):
        return ""

    summary = report_data.analysis_summary or {}

    method = str(
        summary.get("Analysis Method", "")
    ).lower()

    if "historical" in method:
        keys = [
            "Historical Window Count",
            "Years Simulated",
            "Simulated Shortfall Rate",
            "Earliest Simulation Start Year",
            "Latest Simulation Start Year",
            "Median Ending Portfolio",
            "Worst Historical Retirement Start Year",
            "Best Historical Retirement Start Year",
            "Best Ending Portfolio",
        ]
    elif "monte" in method:
        keys = [
            "Scenario Count",
            "Years Simulated",
            "Simulated Shortfall Rate",
            "10th Percentile Ending Portfolio",
            "Median Ending Portfolio",
            "90th Percentile Ending Portfolio",
        ]
    else:
        keys = [
            "Scenario Count",
            "Years Simulated",
            "Simulated Shortfall Rate",
            "Worst Ending Portfolio",
            "Median Ending Portfolio",
            "Best Ending Portfolio",
        ]

    cards = []
    for key in keys:
        if key not in summary:
            continue

        value = summary.get(key)
        negative_class = ""

        if key in {
            "Worst Ending Portfolio",
            "Median Ending Portfolio",
            "Best Ending Portfolio",
        }:
            try:
                if float(value) <= 0.0:
                    negative_class = " negative-risk"
            except (TypeError, ValueError):
                pass

        cards.append(
            f"""
            <div class="highlight-card{negative_class}">
                <div class="highlight-label">{_safe(key)}</div>
                <div class="highlight-value">{_safe(_fmt_value(value, key=key))}</div>
            </div>
            """
        )

    return f"""
<section>
    <h2>Executive Summary</h2>
    <p class="section-intro">
        This section summarizes the main risk results from the selected analysis method.
    </p>
    <div class="highlight-grid">
        {''.join(cards)}
    </div>
</section>
"""


def _render_method_explanation(report_data):
    if not _get_report_option(
        report_data.report_options,
        ["general", "include_method_explanation"],
        True,
    ):
        return ""

    method = str(
        report_data.analysis_summary.get("Analysis Method", "")
    ).lower()

    if "historical" in method:
        explanation = """
        <p>
            Historical Window Analysis evaluates portfolio outcomes using rolling
            periods of actual historical market and inflation data. Each path
            represents one historical economic sequence applied over the modeled
            period.
        </p>
        <p>
            This method is useful for understanding how different historical
            market environments would have affected your financial plan.
        </p>
        """
    elif "monte" in method:
        explanation = """
        <p>
            Monte Carlo Analysis evaluates your financial plan across many
            simulated market paths. Investment returns are generated from your
            selected market assumptions rather than replaying one specific
            historical period.
        </p>
        <p>
            This method helps illustrate how your financial plan may perform
            across a broad range of possible future market conditions, including
            return sequences that have not occurred in the historical record.
        </p>
        """
    else:
        raise ValueError(f"Unknown risk analysis method: {method}")

    return f"""
<section>
    <h2>Method Explanation</h2>
    <div class="explanation-card">
        {explanation}
    </div>
</section>
"""


def _render_sustainability_interpretation(report_data):
    method = str(
        report_data.analysis_summary.get("Analysis Method", "")
    ).lower()

    stats = report_data.failure_statistics or {}
    shortfall_rate = stats.get("Simulated Shortfall Rate")

    try:
        shortfall_rate = float(shortfall_rate)
    except (TypeError, ValueError):
        return ""

    if "historical" in method:
        heading = "Historical Outcome Summary"
        message = (
            f"{shortfall_rate:.1f}% of the evaluated historical windows depleted "
            "the portfolio before the end of the projection period."
        )
    elif "monte" in method:
        heading = "Monte Carlo Outcome Summary"
        message = (
            f"{shortfall_rate:.1f}% of the analyzed Monte Carlo paths depleted "
            "the portfolio before the end of the projection period."
        )
    else:
        return ""

    return f"""
    <div class="summary-card interpretation-card">
        <h3>{_safe(heading)}</h3>
        <p>{_safe(message)}</p>
    </div>
"""

def _render_failure_statistics(report_data):
    if not _get_report_option(
        report_data.report_options,
        ["analysis", "include_portfolio_sustainability"],
        True,
    ):
        return ""

    stats = report_data.failure_statistics or {}

    if not stats:
        return ""

    method = str(
        report_data.analysis_summary.get("Analysis Method", "")
    ).lower()

    if "historical" in method:
        intro = """
        <p class="section-intro">
            This section summarizes how often the modeled portfolio was depleted
            before the end of the projection period across the historical windows.
        </p>
        """
    elif "monte" in method:
        intro = """
        <p class="section-intro">
            This section summarizes how often the modeled portfolio was depleted
            before the end of the projection period across the Monte Carlo paths.
        </p>
        """
    else:
        raise ValueError(f"Unknown risk analysis method: {method}")
    return f"""
<section>
    <h2>Portfolio Sustainability Analysis</h2>
    {intro}
    <div class="summary-card">
        {_render_kv_table(
            stats,
            emphasize_keys={
                "Simulated Shortfall Rate",
                "Earliest Portfolio Depletion Year",
                "Median Portfolio Depletion Year",
                "Latest Portfolio Depletion Year",
            },
        )}
    </div>
</section>
"""


def _render_percentile_table(report_data):
    if not _get_report_option(
        report_data.report_options,
        ["analysis", "include_percentile_table"],
        True,
    ):
        return ""

    rows = report_data.percentile_table or []

    if not rows:
        return ""

    method = str(
        report_data.analysis_summary.get("Analysis Method", "")
    ).lower()

    if "historical" in method:
        explanation = """
        <p class="section-intro">
            This table summarizes how portfolio values varied across all historical
            windows during each year of the projection. Each row represents one
            projection year, while the percentile columns show the distribution of
            portfolio values across the historical windows at that point in time.
        </p>

        <p>
            For example, the 10th percentile is the portfolio value below which
            approximately 10% of historical windows fell at that point in the
            projection. The median represents the middle historical-window outcome,
            while the 90th percentile represents a stronger historical-window
            outcome.
        </p>
        """
    else:
        explanation = """
        <p class="section-intro">
            This table summarizes how portfolio values varied across all simulated
            scenarios during each year of the projection. Each row represents one
            projection year, while the percentile columns show the distribution of
            portfolio values across the simulations at that point in time.
        </p>

        <p>
            For example, the 10th percentile is the portfolio value below which
            approximately 10% of simulations fell at that point in the projection.
            The median represents the middle simulated outcome, while the 90th
            percentile represents a stronger simulated outcome.
        </p>
        """

    return f"""
<section>
    <h2>Percentile Portfolio Table</h2>
    {explanation}
    <div class="table-scroll">
        {_render_percentile_table_rows(rows)}
    </div>
</section>
"""


def _render_year_list(rows, empty_message="No year data available."):
    if not rows:
        return f"<p>{_safe(empty_message)}</p>"

    items = []

    for row in rows:
        year = row.get("Retirement Start Year")
        result = row.get("Result")
        ending_portfolio = row.get("Ending Portfolio")

        details = []
        if result:
            details.append(str(result))
        if ending_portfolio is not None:
            details.append(_fmt_value(ending_portfolio, key="Ending Portfolio"))

        if details:
            items.append(
                f"<li><strong>{_safe(_fmt_value(year, key='Retirement Start Year'))}</strong> - "
                f"{_safe(', '.join(details))}</li>"
            )
        else:
            items.append(
                f"<li><strong>{_safe(_fmt_value(year, key='Retirement Start Year'))}</strong></li>"
            )
            
    return "<ul class='year-list'>" + "\n".join(items) + "</ul>"


def _render_historical_insights(report_data):
    method = str(
        report_data.analysis_summary.get("Analysis Method", "")
    ).lower()

    if "historical" not in method:
        return ""

    if not _get_report_option(
        report_data.report_options,
        ["analysis", "include_historical_window_insights"],
        True,
    ):
        return ""

    insights = report_data.historical_insights or {}

    if not isinstance(insights, dict):
        return ""

    plot = (report_data.plot_assets or {}).get("historical_window_highlights")
    plot_html = ""

    if plot:
        image_path = _relative_asset_path(
            str(plot.get("path", "")),
            _get_output_folder(),
        )

        if image_path:
            alt = plot.get(
                "alt",
                "Historical portfolio paths with strongest and weakest retirement start years highlighted",
            )

            plot_html = f"""
            <div class="plot-card historical-window-plot">
                <img src="{_safe(image_path)}" alt="{_safe(alt)}">
            </div>
            """

    best_rows = insights.get("Best Retirement Years", [])
    worst_rows = insights.get("Worst Retirement Years", [])
    commentary = insights.get("Commentary", [])

    commentary_html = ""
    if commentary:
        commentary_html = "\n".join(
            f"<p>{_safe(item)}</p>"
            for item in commentary
        )

    best_worst_html = ""

    if best_rows or worst_rows:
        best_worst_html = f"""
        <div class="card-grid two-col historical-year-lists historical-year-break">
            <div class="summary-card">
                <h3>Best Historical Retirement Start Years</h3>
                <p>
                    These retirement start years produced the strongest long-term
                    portfolio outcomes.
                </p>
                {_render_year_list(
                    best_rows,
                    empty_message="No best-year data available.",
                )}
            </div>

            <div class="summary-card">
                <h3>Worst Historical Retirement Start Years</h3>
                <p>
                    These retirement start years produced the weakest portfolio
                    outcomes, with earlier portfolio depletion ranked as more severe.
                </p>
                {_render_year_list(
                    worst_rows,
                    empty_message="No worst-year data available.",
                )}
            </div>
        </div>
        """

    return f"""
<section>
    <h2>Historical Window Insights</h2>

    <p class="section-intro">
        This section highlights the strongest and weakest historical retirement
        start years and shows how portfolio outcomes varied across historical windows.
    </p>

    {plot_html}

    <p class="section-intro">
        The chart shows all historical portfolio paths in light gray. The five
        strongest historical retirement starts are redrawn in blue, while the five
        weakest are redrawn in red. The labels at the right edge identify the
        historical retirement start year for each highlighted path.
    </p>

    <div class="summary-card">
        <h3>Sequence-of-Returns Risk</h3>
        <p>
            Historical Window Analysis includes sequence-of-returns effects because
            each historical window preserves the chronological order of market
            returns. Losses that occur early in retirement can reduce the portfolio
            while withdrawals continue, leaving a smaller portfolio to participate
            in later market recoveries.
        </p>
    </div>

    {best_worst_html}

    <div class="summary-card interpretation-card">
        <h3>Historical Outcome Summary</h3>
        {commentary_html}
    </div>
</section>
"""


def _render_monte_carlo_insights(report_data):
    method = str(
        report_data.analysis_summary.get("Analysis Method", "")
    ).lower()

    if "monte" not in method:
        return ""

    if not _get_report_option(
        report_data.report_options,
        ["analysis", "include_monte_carlo_insights"],
        True,
    ):
        return ""

    snapshot = report_data.simulation_snapshot or {}

    settings = {
        "Sampling Method": snapshot.get("Sampling Method"),
        "Correlated Returns": snapshot.get("Correlated Returns"),
        "Sequence Risk": snapshot.get("Sequence Risk"),
        "Random Seed": snapshot.get("Random Seed"),
    }

    if snapshot.get("Sequence Risk"):
        settings["Sequence Risk Timing"] = snapshot.get(
            "Sequence Risk Timing"
        )
        settings["Sequence Risk Length"] = snapshot.get(
            "Sequence Risk Length"
        )
        settings["Sequence Risk Depth"] = snapshot.get(
            "Sequence Risk Depth"
        )

    return f"""
<section>
    <h2>Monte Carlo Insights</h2>

    <div class="summary-card">
        <h3>Monte Carlo Run Settings</h3>
        {_render_kv_table(settings)}
    </div>

    <div class="summary-card interpretation-card">
        <h3>Sequence-of-Returns Risk</h3>

        <p>
            Monte Carlo paths naturally include sequence-of-returns effects because
            each path contains an ordered series of annual investment returns. Losses
            that occur early in retirement can reduce the portfolio while withdrawals
            continue, leaving a smaller portfolio to participate in later market
            recoveries.
        </p>

        <p>
            WARPSimLab's optional Sequence Risk feature adds a deliberate downturn
            pattern to the generated market path. When enabled, the configured
            downturn replaces sampled equity, bond, and real-estate returns for the
            affected years while leaving cash returns unchanged.
        </p>
    </div>

    {_render_sustainability_interpretation(report_data)}

</section>
"""


def _render_plot_assets(report_data):
    assets = report_data.plot_assets or {}

    plot = assets.get("portfolio_range_projection")
    if not plot:
        return ""

    image_path = _relative_asset_path(
        str(plot.get("path", "")),
        _get_output_folder(),
    )
    if not image_path:
        return ""

    if not _get_report_option(
        report_data.report_options,
        ["analysis", "include_portfolio_projection"],
        True,
    ):
        return ""

    method = str(
        report_data.analysis_summary.get("Analysis Method", "")
    ).lower()

    if "historical" in method:
        title = "Portfolio Projection Across Historical Market Periods"
        intro = (
            "This chart summarizes portfolio outcomes produced by applying "
            "actual historical market returns and inflation to your financial "
            "plan. Each scenario begins in a different "
            "historical year, allowing the report to compare how the modeled portfolio "
            "would have behaved under real market conditions experienced in the past."
        )
    elif "monte" in method:
        title = "Portfolio Projection Across Simulated Market Scenarios"
        intro = (
            "This chart summarizes portfolio outcomes generated from simulated market "
            "paths. Each scenario represents one possible sequence of investment returns "
            "using the configured inflation assumption, illustrating a range of potential "
            "outcomes rather than replaying actual market history."
        )
    else:
        raise ValueError(f"Unknown risk analysis method: {method}")
    alt = plot.get("alt", title)

    return f"""
<section>
    <h2>{_safe(title)}</h2>
    <p class="section-intro">
        {_safe(intro)}
    </p>
    <div class="plot-card">
        <img src="{_safe(image_path)}" alt="{_safe(alt)}">
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

.wide-table th:not(:first-child),
.wide-table td:not(:first-child) {{
    text-align: right;
}}

.observations {{
    border: 1px solid #ccc;
    background: #fafafa;
    padding: 14px 14px 14px 34px;
}}

.observations li {{
    margin-bottom: 6px;
}}

.historical-window-plot img {{
    width: 88%;
    max-width: 900px;
}}

.year-list {{
    margin-top: 10px;
    padding-left: 22px;
}}

.year-list li {{
    margin-bottom: 5px;
}}

.interpretation-card {{
    margin-top: 16px;
}}

.historical-year-lists {{
    margin-top: 16px;
}}

.historical-year-break {{
    page-break-before: always;
    break-before: page;
}}

.market-left {{
    text-align: left !important;
}}

</style>
"""

def _build_html_document(report_data):
    title = report_data.report_metadata.get(
        "Report Title",
        "Risk Analysis Report",
    )
    document_title = f"WARPSimLab {title}"

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{_safe(document_title)}</title>
{_render_css()}
</head>
<body>
<main class="report-page">

{render_report_header(
    report_data,
    title=title,
    market_wording="simulated or historical market conditions",
)}

{_render_executive_summary(report_data)}
{_render_method_explanation(report_data)}
{_render_plot_assets(report_data)}
{_render_failure_statistics(report_data)}
{_render_historical_insights(report_data)}
{_render_monte_carlo_insights(report_data)}
{_render_percentile_table(report_data)}
{_render_warnings(report_data)}

{render_footer()}

</main>
</body>
</html>
"""


def _write_html(report_data, output_folder, safe_report_id):
    method = str(
        report_data.analysis_summary.get("Analysis Method", "risk")
    ).lower()

    if "historical" in method:
        prefix = "historical_window_risk"
    elif "monte" in method:
        prefix = "monte_carlo_risk"

    html_path = os.path.join(
        output_folder,
        f"{prefix}_{safe_report_id}.html",
    )

    html_text = _build_html_document(report_data)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_text)

    return html_path


def _write_percentile_csv(report_data, output_folder, safe_report_id):
    rows = report_data.percentile_table or []

    if not rows:
        return None

    csv_path = os.path.join(
        output_folder,
        f"risk_percentiles_{safe_report_id}.csv",
    )

    headers = []
    for row in rows:
        for key in row.keys():
            if key not in headers:
                headers.append(key)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=headers,
            extrasaction="ignore",
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(row)

    return csv_path


def _write_failure_csv(report_data, output_folder, safe_report_id):
    stats = report_data.failure_statistics or {}

    if not stats:
        return None

    csv_path = os.path.join(
        output_folder,
        f"risk_failure_statistics_{safe_report_id}.csv",
    )

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])

        for key, value in stats.items():
            writer.writerow([key, value])

    return csv_path


def _write_summary_csv(report_data, output_folder, safe_report_id):
    summary = report_data.analysis_summary or {}

    if not summary:
        return None

    csv_path = os.path.join(
        output_folder,
        f"risk_summary_{safe_report_id}.csv",
    )

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])

        for key, value in summary.items():
            if isinstance(value, (dict, list)):
                continue
            writer.writerow([key, value])

    return csv_path


def _write_csv_outputs(report_data, output_folder, safe_report_id):
    paths = []

    for path in [
        _write_summary_csv(report_data, output_folder, safe_report_id),
        _write_failure_csv(report_data, output_folder, safe_report_id),
        _write_percentile_csv(report_data, output_folder, safe_report_id),
    ]:
        if path:
            paths.append(path)

    return paths


def generate_risk_report(report_data) -> ReportResult:
    output_folder = _get_output_folder()
    os.makedirs(output_folder, exist_ok=True)

    report_id = report_data.report_metadata.get(
        "Report ID",
        "risk_report",
    )
    safe_report_id = _safe_report_id(report_id)

    generate_html = _get_report_option(
        report_data.report_options,
        ["output", "generate_html"],
        True,
    )
    generate_csv = _get_report_option(
        report_data.report_options,
        ["output", "generate_csv"],
        True,
    )

    if not generate_html and not generate_csv:
        return ReportResult(
            success=False,
            output_folder=output_folder,
            warnings=list(report_data.warnings),
            errors=["No Risk Report output format was selected."],
        )

    html_path = None
    csv_paths = []

    try:
        if generate_html:
            html_path = _write_html(
                report_data,
                output_folder,
                safe_report_id,
            )

        if generate_csv:
            csv_paths = _write_csv_outputs(
                report_data,
                output_folder,
                safe_report_id,
            )

        open_report_in_browser = _get_report_option(
            report_data.report_options,
            ["output", "open_report_in_browser"],
            False,
        )

        if html_path and open_report_in_browser:
            open_html_report_in_browser(html_path)

        return ReportResult(
            success=True,
            report_path=html_path or (csv_paths[0] if csv_paths else None),
            output_folder=output_folder,
            warnings=list(report_data.warnings),
            errors=[],
        )

    except Exception as exc:
        return ReportResult(
            success=False,
            report_path=html_path,
            output_folder=output_folder,
            warnings=list(report_data.warnings),
            errors=[str(exc)],
        )