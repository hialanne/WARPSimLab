# asset_allocation_comparison_report.py

import os

from src.warpsimlab.reports.report_data import (
    AssetAllocationComparisonReportData,
    ReportResult,
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


def _fmt_allocation_percent(value):
    if value is None:
        return "N/A"

    value = float(value)

    if value.is_integer():
        return f"{int(value)}%"

    return f"{value:.1f}%"


def _find_current_case(report_data):
    for case in report_data.comparison_cases:
        if case.get(
            "is_current_allocation",
            False,
        ):
            return case

    return None


def _current_row_class(case):
    if case.get(
        "is_current_allocation",
        False,
    ):
        return " class='baseline-row'"

    return ""


def _allocation_label(case):
    equity = _fmt_allocation_percent(
        case.get("equity_percentage")
    )

    if case.get(
        "is_current_allocation",
        False,
    ):
        return f"{equity} - Current"

    return equity


def _render_current_allocation_highlights(
    report_data,
):
    current_case = _find_current_case(
        report_data
    )

    if current_case is None:
        return ""

    current_allocation = (
        report_data.current_allocation
    )

    depletion = current_case.get(
        "depletion",
        {},
    )

    ending_portfolio = current_case.get(
        "ending_portfolio",
        {},
    )

    return f"""
<section>
    <h2>Current Allocation Highlights</h2>

    <p class="section-intro">
        The Current Allocation case represents the household
        investment allocation in the current WARPSimLab scenario.
        Other equity allocations are compared with this baseline.
    </p>

    <div class="highlight-grid">

        <div class="highlight-card">
            <div class="highlight-label">
                Current Equity Allocation
            </div>
            <div class="highlight-value">
                {_safe(_fmt_allocation_percent(
                    current_allocation.get(
                        "equity_percentage"
                    )
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
                    ending_portfolio.get(
                        "median"
                    )
                ))}
            </div>
        </div>

    </div>

    <div class="current-allocation-detail">
        <strong>Current modeled allocation:</strong>
        Equity
        {_safe(_fmt_allocation_percent(
            current_allocation.get(
                "equity_percentage"
            )
        ))},
        Bonds
        {_safe(_fmt_allocation_percent(
            current_allocation.get(
                "bond_percentage"
            )
        ))},
        Cash
        {_safe(_fmt_allocation_percent(
            current_allocation.get(
                "cash_percentage"
            )
        ))}.
    </div>

</section>
"""


def _render_portfolio_durability(
    report_data,
):
    rows = []

    for case in report_data.comparison_cases:
        depletion = case.get(
            "depletion",
            {},
        )

        rows.append(
            f"""
            <tr{_current_row_class(case)}>
                <td>{_safe(_allocation_label(case))}</td>
                <td>{_safe(_fmt_allocation_percent(
                    case.get("bond_percentage")
                ))}</td>
                <td>{_safe(_fmt_allocation_percent(
                    case.get("cash_percentage")
                ))}</td>
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
        This table compares how often the modeled portfolio reached
        zero across the historical windows evaluated for each
        allocation. The Current row represents the household's
        current modeled allocation.
    </p>

    <table class="wide-table comparison-table">
        <thead>
            <tr>
                <th>Equity Allocation</th>
                <th>Bonds</th>
                <th>Cash</th>
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


def _render_portfolio_outcomes(
    report_data,
):
    rows = []

    for case in report_data.comparison_cases:
        outcomes = case.get(
            "ending_portfolio",
            {},
        )

        rows.append(
            f"""
            <tr{_current_row_class(case)}>
                <td>{_safe(_allocation_label(case))}</td>
                <td>{_safe(_fmt_currency(
                    outcomes.get("minimum")
                ))}</td>
                <td>{_safe(_fmt_currency(
                    outcomes.get(
                        "10th_percentile"
                    )
                ))}</td>
                <td>{_safe(_fmt_currency(
                    outcomes.get(
                        "25th_percentile"
                    )
                ))}</td>
                <td>{_safe(_fmt_currency(
                    outcomes.get("median")
                ))}</td>
                <td>{_safe(_fmt_currency(
                    outcomes.get(
                        "75th_percentile"
                    )
                ))}</td>
                <td>{_safe(_fmt_currency(
                    outcomes.get(
                        "90th_percentile"
                    )
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
        Ending portfolio values show the distribution of modeled
        outcomes across the same historical windows for each
        allocation.
    </p>

    <div class="table-scroll">
        <table class="wide-table comparison-table outcome-table">
            <thead>
                <tr>
                    <th>Equity Allocation</th>
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


def _render_tradeoff_effects(
    report_data,
):
    rows = []

    for case in report_data.comparison_cases:
        minimum_portfolio = case.get(
            "minimum_portfolio",
            {},
        )

        ending_portfolio = case.get(
            "ending_portfolio",
            {},
        )

        depletion = case.get(
            "depletion",
            {},
        )

        rows.append(
            f"""
            <tr{_current_row_class(case)}>
                <td>{_safe(_allocation_label(case))}</td>
                <td>{_safe(_fmt_percent(
                    depletion.get(
                        "windows_reaching_zero_percent"
                    )
                ))}</td>
                <td>{_safe(_fmt_currency(
                    minimum_portfolio.get(
                        "10th_percentile"
                    )
                ))}</td>
                <td>{_safe(_fmt_currency(
                    ending_portfolio.get(
                        "10th_percentile"
                    )
                ))}</td>
                <td>{_safe(_fmt_currency(
                    ending_portfolio.get(
                        "median"
                    )
                ))}</td>
                <td>{_safe(_fmt_currency(
                    ending_portfolio.get(
                        "90th_percentile"
                    )
                ))}</td>
            </tr>
            """
        )

    return f"""
<section>
    <h2>Risk and Outcome Tradeoffs</h2>

    <p class="section-intro">
        This section places lower-end, median, and upper-end modeled
        outcomes together. It is intended to show how allocation
        changes can affect different parts of the historical outcome
        distribution rather than identify a preferred allocation.
    </p>

    <table class="wide-table comparison-table">
        <thead>
            <tr>
                <th>Equity Allocation</th>
                <th>Reaching Zero</th>
                <th>10th Percentile Minimum Portfolio</th>
                <th>10th Percentile Ending Portfolio</th>
                <th>Median Ending Portfolio</th>
                <th>90th Percentile Ending Portfolio</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
</section>
"""


def _render_method_note(
    report_data,
):
    return """
<section>
    <h2>Comparison Method</h2>

    <p class="section-intro">
        Each allocation case uses the same historical return windows
        and the same household assumptions. Only the modeled
        Stock/Bond/Cash allocation is changed.
    </p>

    <p class="section-intro">
        For comparison equity levels, the remaining non-equity
        allocation is divided between bonds and cash using the
        current household bond-to-cash ratio.
    </p>

    <p class="section-intro">
        Investable assets include pre-tax, post-tax, Roth, and HSA
        assets. Real estate is not included in the allocation being
        compared.
    </p>
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


def generate_asset_allocation_comparison_report(
    report_data: AssetAllocationComparisonReportData,
) -> ReportResult:
    output_folder = get_report_output_folder()

    os.makedirs(
        output_folder,
        exist_ok=True,
    )

    report_id = (
        report_data.report_metadata.get(
            "Report ID",
            "asset_allocation_comparison",
        )
    )

    safe_id = safe_report_id(
        report_id
    )

    report_path = os.path.join(
        output_folder,
        (
            "asset_allocation_comparison_"
            f"{safe_id}.html"
        ),
    )

    html_text = f"""<!doctype html>
<html>
<head>
    <meta charset="utf-8">

    <title>
        WARPSimLab Asset Allocation Comparison Report
    </title>

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

    .current-allocation-detail {{
        margin-top: 12px;
        padding: 10px 12px;
        border: 1px solid #ccc;
        background: #fafafa;
        border-radius: 6px;
    }}

    </style>
</head>

<body>
    <main class="report-page">

        {render_report_header(
            report_data,
            title=(
                "Asset Allocation Comparison Report"
            ),
            market_wording=(
                "historical market conditions"
            ),
        )}

        {_render_current_allocation_highlights(
            report_data
        )}

        {_render_portfolio_durability(
            report_data
        )}

        {_render_portfolio_outcomes(
            report_data
        )}

        {_render_tradeoff_effects(
            report_data
        )}

        {_render_method_note(
            report_data
        )}

        {_render_warnings(
            report_data
        )}

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

        output_options = (
            report_data.report_options.get(
                "output",
                {},
            )
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
            warnings=list(
                report_data.warnings
            ),
            errors=[],
        )

    except Exception as exc:
        return ReportResult(
            success=False,
            report_path=None,
            output_folder=output_folder,
            warnings=list(
                report_data.warnings
            ),
            errors=[str(exc)],
        )