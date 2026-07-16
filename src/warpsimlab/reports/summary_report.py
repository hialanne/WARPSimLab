# summary_report.py

import os
from datetime import datetime

from src.warpsimlab.reports.report_data import ReportResult, SummaryReportData

from src.warpsimlab.reports.report_common import (
    safe as _safe,
    get_report_output_folder,
    safe_report_id,
    relative_asset_path as _relative_asset_path,
    render_report_header,
    render_footer,
    render_base_css,
)

YEAR_KEYS = {
    "Year",
    "Start Year",
    "Projection End Year",
    "Years Simulated",
    "Years To Simulate",
}

PERCENT_KEY_HINTS = {
    "Rate",
    "Percent",
    "Return",
    "Standard Deviation",
    "Shortfall",
    "Tax Bracket",
}


def _get_report_option(report_options, path, default=False):
    target = report_options

    for key in path:
        if not isinstance(target, dict) or key not in target:
            return default
        target = target[key]

    return target


def _is_percent_key(key):
    key = str(key)
    return any(hint in key for hint in PERCENT_KEY_HINTS)


def _is_year_key(key):
    return str(key) in YEAR_KEYS


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
        if isinstance(value, (int, float)):
            if str(key) == "Tax Bracket" and 0 <= value <= 1:
                return f"{value * 100:.0f}%"
            return f"{value:.2f}%"
        return str(value)

    if isinstance(value, float):
        if value < 0:
            return f"-${abs(value):,.0f}"
        return f"${value:,.0f}"

    if isinstance(value, int):
        return f"{value:,}"

    return str(value)


def _is_depletion_key(key):
    key = str(key)
    return key in {
        "Portfolio End",
        "Portfolio End Value",
        "Total Portfolio",
    }


def _is_depleted_value(key, value):
    if value is None:
        return False

    if not _is_depletion_key(key):
        return False

    try:
        return float(value) <= 0.0
    except (TypeError, ValueError):
        return False


def _render_kv_table(data, emphasize_keys=None):
    emphasize_keys = set(emphasize_keys or [])
    rows = []

    for key, value in data.items():
        is_emphasized = key in emphasize_keys
        row_class = " class='emphasis-row'" if is_emphasized else ""
        value_class = ""
        if isinstance(value, (int, float)) and value < 0:
            value_class = " class='negative'"
        elif _is_depleted_value(key, value):
            value_class = " class='negative'"

        rows.append(
            f"<tr{row_class}>"
            f"<th>{_safe(key)}</th>"
            f"<td{value_class}>{_safe(_fmt_value(value, key=key))}</td>"
            "</tr>"
        )

    return "<table class='kv-table'><tbody>" + "\n".join(rows) + "</tbody></table>"


def _render_simulation_highlights(report_data):
    totals = report_data.results_summary.get("simulation_totals", {})
    snapshot = report_data.simulation_snapshot

    highlights = {
        "Portfolio Start Value": totals.get("Portfolio Start"),
        "Portfolio End Value": totals.get("Portfolio End"),
        "Simulated Shortfall Rate": totals.get("Simulated Shortfall Rate"),
        "Total Income Generated": totals.get("Total Income"),
        "Total Expenses": totals.get("Household Expenses"),
        "Years Simulated": snapshot.get("Years Simulated"),
    }

    cards = []

    for label, value in highlights.items():
        cards.append(
            f"""
            <div class="highlight-card">
                <div class="highlight-label">{_safe(label)}</div>
                <div class="highlight-value{' negative' if _is_depleted_value(label, value) else ''}">
                    {_safe(_fmt_value(value, key=label))}
                </div>
            </div>
            """
        )

    return f"""
<section>
    <h2>Simulation Highlights</h2>
    <div class="highlight-grid">
        {''.join(cards)}
    </div>
</section>
"""

def _render_portfolio_summary(report_data):
    milestones = report_data.results_summary.get("portfolio_milestones", {})

    cards = []
    for title, values in milestones.items():
        year = values.get("Year", "N/A")
        cards.append(
            f"""
            <div class="milestone-card">
                <h3>{_safe(title)}</h3>
                <div class="subhead">Portfolio Value in {_safe(_fmt_value(year, key="Year"))}</div>
                {_render_kv_table(
                    {
                        "Pre-Tax Assets": values.get("Pre-Tax Assets"),
                        "Post-Tax Assets": values.get("Post-Tax Assets"),
                        "Roth Assets": values.get("Roth Assets"),
                        "HSA Assets": values.get("HSA Assets"),
                        "Total Portfolio": values.get("Total Portfolio"),
                        "Real Estate": values.get("Real Estate"),
                        "Total Assets": values.get("Total Assets"),
                    },
                    emphasize_keys={"Total Portfolio", "Total Assets"},
                )}
            </div>
            """
        )

    return f"""
<section>
    <h2>Portfolio Summary</h2>
    <p class="section-intro">
        This section summarizes the portfolio at three major points in the simulation:
        the start, retirement, and the end of the projection period.
    </p>
    <div class="card-grid three-col">
        {''.join(cards)}
    </div>
</section>
"""


def _render_portfolio_projection_placeholder(report_data, output_folder=None):
    portfolio_visuals = report_data.report_options.get("portfolio_visuals", {})
    plot_assets = report_data.plot_assets or {}

    include_monte_carlo = portfolio_visuals.get("include_monte_carlo_analysis", False)
    include_historical_windows = portfolio_visuals.get(
        "include_historical_windows_analysis",
        False,
    )

    method_note = ""
    if include_monte_carlo:
        method_note = """
        <p class="section-intro">
            Monte Carlo results use randomized market sampling and may vary between simulation runs.
            Historical Windows results use fixed historical return sequences and will produce repeatable
            results when run with the same assumptions and historical data.
        </p>
        """

    cards = []

    if portfolio_visuals.get("include_normal_projection", False):
        asset = plot_assets.get("portfolio_projection")

        if asset and asset.get("path"):
            image_src = _relative_asset_path(asset.get("path"), output_folder)
            cards.append(f"""
            <div class="plot-card">
                <h3>{_safe(asset.get("title", "Portfolio Projection"))}</h3>
                <p>
                    This chart shows the simulated portfolio path under the selected assumptions.
                </p>
                <img src="{_safe(image_src)}" alt="{_safe(asset.get("alt", "Portfolio projection"))}">
            </div>
            """)
        else:
            cards.append("""
            <div class="placeholder-card">
                <h3>Portfolio Projection</h3>
                <p>Placeholder. The selected portfolio plot was not available for this report.</p>
            </div>
            """)

    if portfolio_visuals.get("include_subcategories_projection", False):
        asset = plot_assets.get("subcategories_projection")

        if asset and asset.get("path"):
            image_src = _relative_asset_path(asset.get("path"), output_folder)
            cards.append(f"""
            <div class="plot-card">
                <h3>{_safe(asset.get("title", "Portfolio Subcategories"))}</h3>
                <p>
                    This chart shows the simulated portfolio projection broken down by asset category.
                </p>
                <img src="{_safe(image_src)}" alt="{_safe(asset.get("alt", "Portfolio subcategories projection"))}">
            </div>
            """)
        else:
            cards.append("""
            <div class="placeholder-card">
                <h3>Portfolio Subcategories</h3>
                <p>Placeholder. The selected portfolio subcategories plot was not available for this report.</p>
            </div>
            """)

    if portfolio_visuals.get("include_monte_carlo_analysis", False):
        asset = plot_assets.get("monte_carlo_analysis")

        if asset and asset.get("path"):
            image_src = _relative_asset_path(asset.get("path"), output_folder)
            cards.append(f"""
            <div class="plot-card">
                <h3>{_safe(asset.get("title", "Monte Carlo Analysis"))}</h3>
                <p>
                    This chart shows the simulated range of portfolio outcomes across modeled market paths.
                </p>
                <img src="{_safe(image_src)}" alt="{_safe(asset.get("alt", "Monte Carlo analysis"))}">
            </div>
            """)
        else:
            cards.append("""
            <div class="placeholder-card">
                <h3>Monte Carlo Analysis</h3>
                <p>Placeholder. The selected Monte Carlo plot was not available for this report.</p>
            </div>
            """)

    if portfolio_visuals.get("include_historical_windows_analysis", False):
        asset = plot_assets.get("historical_windows_analysis")

        if asset and asset.get("path"):
            image_src = _relative_asset_path(asset.get("path"), output_folder)
            cards.append(f"""
            <div class="plot-card">
                <h3>{_safe(asset.get("title", "Historical Windows Analysis"))}</h3>
                <p>
                    This chart shows portfolio outcomes using rolling historical return windows.
                </p>
                <img src="{_safe(image_src)}" alt="{_safe(asset.get("alt", "Historical Windows analysis"))}">
            </div>
            """)
        else:
            cards.append("""
            <div class="placeholder-card">
                <h3>Historical Windows Analysis</h3>
                <p>Placeholder. The selected Historical Windows plot was not available for this report.</p>
            </div>
            """)

    if not cards:
        return ""

    if len(cards) >= 3:
        if '<div class="plot-card">' in cards[2]:
            cards[2] = cards[2].replace(
                '<div class="plot-card">',
                '<div class="plot-card portfolio-break-before">',
                1,
            )
        elif '<div class="placeholder-card">' in cards[2]:
            cards[2] = cards[2].replace(
                '<div class="placeholder-card">',
                '<div class="placeholder-card portfolio-break-before">',
                1,
            )

    return f"""
<section>
    <h2>Portfolio Visuals</h2>
    <p class="section-intro">
        This section presents selected portfolio visuals generated from the simulation results.
    </p>
    {method_note}
    <div class="plot-stack">
        {''.join(cards)}
    </div>
</section>
"""

def _render_income_projection_placeholder(report_data, output_folder=None):
    income_visuals = report_data.report_options.get("income_visuals", {})
    plot_assets = report_data.plot_assets or {}

    cards = []

    if income_visuals.get("include_normal_income", False):
        asset = plot_assets.get("income_projection")

        if asset and asset.get("path"):
            image_src = _relative_asset_path(asset.get("path"), output_folder)
            cards.append(f"""
            <div class="plot-card">
                <h3>{_safe(asset.get("title", "Income Projection"))}</h3>
                <p>
                    This chart shows simulated Income and Cash Flow values under the selected assumptions.
                </p>
                <img src="{_safe(image_src)}" alt="{_safe(asset.get("alt", "Income projection"))}">
            </div>
            """)
        else:
            cards.append("""
            <div class="placeholder-card">
                <h3>Income Projection</h3>
                <p>Placeholder. The selected income plot was not available for this report.</p>
            </div>
            """)

    if income_visuals.get("include_subcategories_income", False):
        asset = plot_assets.get("income_subcategories")

        if asset and asset.get("path"):
            image_src = _relative_asset_path(asset.get("path"), output_folder)
            cards.append(f"""
            <div class="plot-card">
                <h3>{_safe(asset.get("title", "Income Source Breakdown"))}</h3>
                <p>
                    This chart shows simulated income broken down by income source across the projection period.
                </p>
                <img src="{_safe(image_src)}" alt="{_safe(asset.get("alt", "Income source breakdown"))}">
            </div>
            """)
        else:
            cards.append("""
            <div class="placeholder-card">
                <h3>Income Source Breakdown</h3>
                <p>Placeholder. The selected income source breakdown plot was not available for this report.</p>
            </div>
            """)

    if not cards:
        return ""

    return f"""
<section>
    <h2>Income Visuals</h2>
    <p class="section-intro">
        This section presents selected income visuals generated from the simulation results.
    </p>
    <div class="plot-stack">
        {''.join(cards)}
    </div>
</section>
"""


def _render_cashflow_projection_placeholder(report_data, output_folder=None):
    cashflow_visuals = report_data.report_options.get("cashflow_visuals", {})
    plot_assets = report_data.plot_assets or {}

    cards = []

    if cashflow_visuals.get("include_normal_cashflow", False):
        asset = plot_assets.get("cashflow_projection")

        if asset and asset.get("path"):
            image_src = _relative_asset_path(asset.get("path"), output_folder)
            cards.append(f"""
            <div class="plot-card">
                <h3>{_safe(asset.get("title", "Cash Flow Projection"))}</h3>
                <p>
                    This chart shows simulated household Cash Flow under the selected assumptions.
                </p>
                <img src="{_safe(image_src)}" alt="{_safe(asset.get("alt", "Cash Flow projection"))}">
            </div>
            """)
        else:
            cards.append("""
            <div class="placeholder-card">
                <h3>Cash Flow Projection</h3>
                <p>Placeholder. The selected Cash Flow plot was not available for this report.</p>
            </div>
            """)

    if cashflow_visuals.get("include_subcategories_cashflow", False):
        asset = plot_assets.get("cashflow_subcategories")

        if asset and asset.get("path"):
            image_src = _relative_asset_path(asset.get("path"), output_folder)
            cards.append(f"""
            <div class="plot-card">
                <h3>{_safe(asset.get("title", "Cash Flow Breakdown"))}</h3>
                <p>
                    This chart shows simulated Cash Flow broken down by source across the projection period.
                </p>
                <img src="{_safe(image_src)}" alt="{_safe(asset.get("alt", "Cash Flow breakdown"))}">
            </div>
            """)
        else:
            cards.append("""
            <div class="placeholder-card">
                <h3>Cash Flow Breakdown</h3>
                <p>Placeholder. The selected Cash Flow breakdown plot was not available for this report.</p>
            </div>
            """)

    if not cards:
        return ""

    return f"""
<section>
    <h2>Cash Flow Visuals</h2>
    <p class="section-intro">
        This section presents selected Cash Flow visuals generated from the simulation results.
    </p>
    <div class="plot-stack">
        {''.join(cards)}
    </div>
</section>
"""

def _render_operating_balance_placeholder(report_data, output_folder=None):
    operating_balance_visuals = report_data.report_options.get("operating_balance_visuals", {})
    include_operating_balance = operating_balance_visuals.get(
        "include_cumulative_operating_balance",
        True,
    )

    if not include_operating_balance:
        return ""

    plot_assets = report_data.plot_assets or {}
    asset = plot_assets.get("cumulative_operating_balance")

    if asset and asset.get("path"):
        image_src = _relative_asset_path(asset.get("path"), output_folder)

        card_html = f"""
        <div class="plot-card">
            <h3>{_safe(asset.get("title", "Cumulative Operating Balance"))}</h3>
            <p>
                This chart shows the cumulative simulated operating balance across the projection period.
                Positive values indicate cumulative simulated Cash Flow surplus.
                Negative values indicate cumulative simulated Cash Flow deficit.
            </p>
            <img src="{_safe(image_src)}" alt="{_safe(asset.get("alt", "Cumulative operating balance"))}">
        </div>
        """
    else:
        card_html = """
        <div class="placeholder-card">
            <h3>Cumulative Operating Balance</h3>
            <p>Placeholder. The selected cumulative operating balance plot was not available for this report.</p>
        </div>
        """

    return f"""
<section>
    <h2>Operating Balance Visuals</h2>
    <p class="section-intro">
        This section shows cumulative simulated operating surplus or deficit over time.
    </p>
    <div class="plot-stack">
        {card_html}
    </div>
</section>
"""


def _render_income_summary(report_data):
    milestones = report_data.results_summary.get("income_milestones", {})

    if not milestones:
        return ""

    categories = [
        "Wages",
        "RMD",
        "Social Security",
        "Pensions and Annuities",
        "Gross Income",
        "401k or IRA Contribution",
        "Taxes",
        "Tax Bracket",
        "Net Income",
        "Household Expenses",
        "Net Cash Flow",
        "Fund Expenses",
    ]

    emphasize_categories = {
        "Gross Income",
        "Net Income",
        "Net Cash Flow",
    }

    headers = ["Cash Flow Category"]
    for milestone_name, values in milestones.items():
        headers.append(
            f"{_safe(milestone_name)}<br>"
            f"<span class='year'>({_safe(_fmt_value(values.get('Year', 'N/A'), key='Year'))})</span>"
        )

    rows = []
    for category in categories:
        row_class = " class='emphasis-row'" if category in emphasize_categories else ""
        cells = [f"<th>{_safe(category)}</th>"]

        for values in milestones.values():
            value = values.get(category)
            css_class = "negative" if isinstance(value, (int, float)) and value < 0 else ""
            cells.append(
                f"<td class='{css_class}'>{_safe(_fmt_value(value, key=category))}</td>"
            )

        rows.append(f"<tr{row_class}>" + "".join(cells) + "</tr>")

    return f"""
<section>
    <h2>Income and Cash Flow Summary</h2>
    <p class="section-intro">
        This section shows how major income and Cash Flow categories change at key points
        in the simulation. It is a milestone summary, not a year-by-year table.
    </p>
    <table class="wide-table">
        <thead>
            <tr>{"".join(f"<th>{h}</th>" for h in headers)}</tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
</section>
"""


def _render_simulation_summary(report_data):
    totals = report_data.results_summary.get("simulation_totals", {})

    groups = [
        (
            "Portfolio Outcome",
            {
                "Portfolio Start": totals.get("Portfolio Start"),
                "Portfolio End": totals.get("Portfolio End"),
                "Maximum Portfolio": totals.get("Maximum Portfolio"),
                "Minimum Portfolio": totals.get("Minimum Portfolio"),
            },
            set(),
        ),
        (
            "Simulation Totals",
            {
                "Taxes Paid": totals.get("Taxes Paid"),
                "Household Expenses": totals.get("Household Expenses"),
                "Net Cash Flow": totals.get("Net Cash Flow"),
                "Fund Expenses": totals.get("Fund Expenses"),
            },
            {"Net Cash Flow"},
        ),
        (
            "Risk Indicator",
            {
                "Simulated Shortfall Rate": totals.get("Simulated Shortfall Rate"),
            },
            {"Simulated Shortfall Rate"},
        ),
    ]

    cards = []
    for title, data, emphasize_keys in groups:
        cards.append(
            f"""
            <div class="summary-card">
                <h3>{_safe(title)}</h3>
                {_render_kv_table(data, emphasize_keys=emphasize_keys)}
            </div>
            """
        )

    return f"""
<section>
    <h2>Simulation Summary</h2>
    <p class="section-intro">
        These totals summarize the overall simulated outcome across the projection period.
    </p>
    <div class="card-grid three-col">
        {''.join(cards)}
    </div>
</section>
"""


def _render_simple_table(table_data, empty_message="No entries."):
    if isinstance(table_data, dict):
        columns = table_data.get("columns")
        rows = table_data.get("rows", [])
        empty_message = table_data.get("empty_message", empty_message)

        if not rows:
            return f"<p>{_safe(empty_message)}</p>"

        # New explicit table format:
        # {"columns": [...], "rows": [[...], [...]]}
        if columns:
            header_html = "".join(f"<th>{_safe(column)}</th>" for column in columns)

            body_rows = []
            for row in rows:
                cells = []
                for value in row:
                    css_class = " class='negative'" if isinstance(value, (int, float)) and value < 0 else ""
                    cells.append(f"<td{css_class}>{_safe(_fmt_value(value))}</td>")
                body_rows.append("<tr>" + "".join(cells) + "</tr>")

            return f"""
            <table class="wide-table assumptions-table">
                <thead>
                    <tr>{header_html}</tr>
                </thead>
                <tbody>
                    {''.join(body_rows)}
                </tbody>
            </table>
            """

        # Backward-compatible dict-row table format:
        # {"rows": [{"Description": "...", ...}]}
        table_data = rows

    rows = table_data

    if not rows:
        return f"<p>{_safe(empty_message)}</p>"

    dict_rows = [row for row in rows if isinstance(row, dict)]

    if not dict_rows:
        items = "".join(f"<li>{_safe(_fmt_value(row))}</li>" for row in rows)
        return f"<ul>{items}</ul>"

    headers = []
    for row in dict_rows:
        for key in row.keys():
            if key not in headers:
                headers.append(key)

    header_html = "".join(f"<th>{_safe(header)}</th>" for header in headers)

    body_rows = []
    for row in dict_rows:
        cells = []
        for header in headers:
            value = row.get(header)
            css_class = " class='negative'" if isinstance(value, (int, float)) and value < 0 else ""
            cells.append(
                f"<td{css_class}>{_safe(_fmt_value(value, key=header))}</td>"
            )
        body_rows.append("<tr>" + "".join(cells) + "</tr>")

    return f"""
    <table class="wide-table assumptions-table">
        <thead>
            <tr>{header_html}</tr>
        </thead>
        <tbody>
            {''.join(body_rows)}
        </tbody>
    </table>
    """


def _render_assumption_node(node):
    if node is None:
        return "<p>N/A</p>"

    if isinstance(node, dict):
        node_type = node.get("type")

        if node_type == "table":
            return _render_simple_table(
                node,
                empty_message=node.get("empty_message", "No entries."),
            )

        scalar_items = {}
        nested_blocks = []

        for key, value in node.items():
            if isinstance(value, dict):
                nested_blocks.append(
                    f"""
                    <div class="appendix-subblock">
                        <h4>{_safe(key)}</h4>
                        {_render_assumption_node(value)}
                    </div>
                    """
                )
            elif isinstance(value, list):
                nested_blocks.append(
                    f"""
                    <div class="appendix-subblock">
                        <h4>{_safe(key)}</h4>
                        {_render_simple_table(value)}
                    </div>
                    """
                )
            else:
                scalar_items[key] = value

        rendered = ""
        if scalar_items:
            rendered += _render_kv_table(scalar_items)

        rendered += "".join(nested_blocks)

        return rendered or "<p>N/A</p>"

    if isinstance(node, list):
        return _render_simple_table(node)

    return f"<p>{_safe(_fmt_value(node))}</p>"


def _render_assumptions_appendix(report_data):
    assumptions = report_data.assumptions_summary or {}

    blocks = []
    for section_title, section_data in assumptions.items():
        blocks.append(
            f"""
            <div class="appendix-block">
                <h3>{_safe(section_title)}</h3>
                {_render_assumption_node(section_data)}
            </div>
            """
        )

    return f"""
<section class="appendix">
    <h2>Assumptions Appendix</h2>
    <p class="section-intro">
        This appendix documents the user-provided assumptions and report settings used for the simulation.
    </p>
    {''.join(blocks)}
</section>
"""


def _render_warnings(report_data):
    user_facing_warnings = []

    for warning in report_data.warnings:
        text = str(warning)
        if "fixture" in text.lower():
            continue
        if "build_fake_summary_report_data" in text:
            continue
        user_facing_warnings.append(text)

    if not user_facing_warnings:
        return ""

    items = "\n".join(f"<li>{_safe(w)}</li>" for w in user_facing_warnings)

    return f"""
<section>
    <h2>Warnings</h2>
    <ul class="warnings">
        {items}
    </ul>
</section>
"""


def generate_summary_report(report_data: SummaryReportData) -> ReportResult:
    output_folder = get_report_output_folder()
    os.makedirs(output_folder, exist_ok=True)

    report_id = report_data.report_metadata.get("Report ID", "summary_report")
    safe_id = safe_report_id(report_id)

    report_path = os.path.join(
        output_folder,
        f"executive_summary_{safe_id}.html",
    )

    portfolio_plot_html = _render_portfolio_projection_placeholder(
        report_data,
        output_folder=output_folder,
    )

    income_plot_html = _render_income_projection_placeholder(
        report_data,
        output_folder=output_folder,
    )

    cashflow_plot_html = _render_cashflow_projection_placeholder(
        report_data,
        output_folder=output_folder,
    )

    operating_balance_html = _render_operating_balance_placeholder(
        report_data,
        output_folder=output_folder,
    )

    assumptions_html = ""
    if report_data.report_options.get("include_assumptions_appendix", True):
        assumptions_html = _render_assumptions_appendix(report_data)

    simulation_summary_html = ""
    if report_data.report_options.get("include_simulation_summary", True):
        simulation_summary_html = _render_simulation_summary(report_data)

    html_text = f"""<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>WARPSimLab Executive Summary Report</title>

    <style>

    {render_base_css()}

    .milestone-card,
    .appendix-block {{
        border: 1px solid #ccc;
        background: #fafafa;
        padding: 14px;
        border-radius: 6px;
    }}

    .subhead {{
        color: #555;
        font-size: 16px;
        margin-bottom: 10px;
    }}

    .summary-card .kv-table {{
        table-layout: auto;
    }}

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

    .year {{
        font-weight: normal;
        color: #555;
        font-size: 12px;
    }}

    .placeholder-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(160px, 1fr));
        gap: 14px;
        margin-top: 14px;
    }}

    .placeholder-grid.two-col {{
        grid-template-columns: repeat(2, minmax(220px, 1fr));
    }}

    .placeholder-card {{
        border-style: dashed;
        color: #555;
        background: #fcfcfc;
    }}

    .placeholder-card h3 {{
        color: #333;
    }}

    .appendix {{
        margin-top: 42px;
    }}

    .appendix-block {{
        margin-bottom: 14px;
    }}

    .appendix-subblock {{
        margin-top: 12px;
    }}

    .appendix-subblock h4 {{
        margin: 8px 0 6px 0;
        font-size: 15px;
    }}

    .simulation-summary-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(220px, 1fr));
        gap: 16px;
        margin-top: 14px;
    }}

    .assumptions-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-size: 14px;
    }}

    .assumptions-table th,
    .assumptions-table td {{
        border: 1px solid #ccc;
        padding: 6px 8px;
        text-align: left;
        vertical-align: top;
    }}

    .assumptions-table thead th {{
        background: #f0f0f0;
    }}

    .assumptions-table td:not(:first-child),
    .assumptions-table th:not(:first-child) {{
        text-align: right;
    }}

    @media print {{

        .simulation-summary-grid {{
            grid-template-columns: repeat(2, 1fr);
        }}

        .simulation-summary-grid .summary-card {{
            page-break-inside: avoid;
            break-inside: avoid;
        }}

        .simulation-summary-grid .kv-table th {{
            width: 55%;
            white-space: nowrap;
        }}

        .simulation-summary-grid .kv-table td {{
            width: 45%;
            white-space: nowrap;
        }}

        .placeholder-grid {{
            grid-template-columns: repeat(2, 1fr);
        }}

        .portfolio-break-before {{
            page-break-before: always;
            break-before: page;
        }}

    }}

    </style>
</head>
<body>
    <main class="report-page">

        {render_report_header(
            report_data,
            title="Executive Summary Report",
            market_wording="simulated market conditions",
        )}

        {_render_simulation_highlights(report_data)}

        {_render_portfolio_summary(report_data)}

        {portfolio_plot_html}

        {_render_income_summary(report_data)}

        {income_plot_html}

        {cashflow_plot_html}

        {operating_balance_html}

        {simulation_summary_html}

        {assumptions_html}

        {_render_warnings(report_data)}

        {render_footer()}

    </main>
</body>
</html>
"""

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_text)

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