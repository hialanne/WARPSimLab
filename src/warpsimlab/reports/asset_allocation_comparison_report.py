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
    relative_asset_path,
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


def _find_equity_case(
    report_data,
    equity_percentage,
):
    target = float(equity_percentage)

    for case in report_data.comparison_cases:
        if abs(
            float(
                case.get(
                    "equity_percentage",
                    0.0,
                )
            )
            - target
        ) < 1e-6:
            return case

    return None


def _table_cases(report_data):
    return [
        case
        for case in report_data.comparison_cases
        if not case.get(
            "highlight_only",
            False,
        )
    ]


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

    current_equity = float(
        current_case.get(
            "equity_percentage",
            0.0,
        )
    )

    highlight_equity_percentages = (
        max(
            0.0,
            current_equity - 20.0,
        ),
        current_equity,
        min(
            100.0,
            current_equity + 20.0,
        ),
    )

    rows = []

    for equity_percentage in highlight_equity_percentages:
        if abs(
            equity_percentage - current_equity
        ) < 1e-6:
            case = current_case
        else:
            case = _find_equity_case(
                report_data,
                equity_percentage,
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

        if float(ending_portfolio or 0.0) <= 0.0:
            ending_class = "ending-portfolio-zero"
        else:
            ending_class = ""

        equity_text = _fmt_allocation_percent(
            case.get(
                "equity_percentage"
            )
        )

        if case.get(
            "is_current_allocation",
            False,
        ):
            equity_text += " - Current"

        bonds_text = _fmt_allocation_percent(
            case.get(
                "bond_percentage"
            )
        )

        cash_text = _fmt_allocation_percent(
            case.get(
                "cash_percentage"
            )
        )

        rows.append(
            f"""
            <div class="highlight-grid">

                <div class="highlight-card">
                    <div class="highlight-label">
                        {_safe(equity_text)} Equity
                    </div>
                    <div class="highlight-value allocation-components">
                        {_safe(bonds_text)} Bonds /
                        {_safe(cash_text)} Cash
                    </div>
                </div>

                <div class="highlight-card">
                    <div class="highlight-label">
                        Ending Portfolio
                    </div>
                    <div class="highlight-value {ending_class}">
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

    return f"""
<section>
    <h2>Allocation Highlights</h2>

    {''.join(rows)}

</section>
"""


def _render_portfolio_durability(
    report_data,
):
    rows = []

    for case in _table_cases(report_data):
        depletion = case.get(
            "depletion",
            {},
        )

        ending_portfolio = case.get(
            "deterministic_ending_portfolio"
        )

        if float(ending_portfolio or 0.0) <= 0.0:
            ending_class = "ending-portfolio-zero"
        else:
            ending_class = ""

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
                <td>{_safe(_fmt_percent(
                    depletion.get(
                        "windows_reaching_zero_percent"
                    )
                ))}</td>

                <td class="{ending_class}">
                    {_safe(_fmt_currency(ending_portfolio))}
                </td>
            </tr>
            """
        )

    return f"""
<section>
    <h2>Portfolio Results by Allocation</h2>

    <p class="section-intro">
        This table compares portfolio depletion and ending portfolio
        values across the modeled asset allocations. The Current row
        represents the household's current modeled allocation.
    </p>

    <table class="wide-table comparison-table allocation-results-table">
        <thead>
            <tr>
                <th>Equity Allocation</th>
                <th>Bonds</th>
                <th>Cash</th>
                <th>Scenarios That Depleted Portfolio</th>
                <th>Ending Portfolio</th>
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

    def outcome_cell(value):
        cell_class = "ending-portfolio-zero" if float(value or 0.0) <= 0.0 else ""
        return f'<td class="{cell_class}">{_safe(_fmt_currency(value))}</td>'

    for case in _table_cases(report_data):
        outcomes = case.get(
            "ending_portfolio",
            {},
        )

        rows.append(
            f"""
            <tr{_current_row_class(case)}>
                <td>{_safe(_allocation_label(case))}</td>
                {outcome_cell(outcomes.get("10th_percentile"))}
                {outcome_cell(outcomes.get("25th_percentile"))}
                {outcome_cell(outcomes.get("median"))}
                {outcome_cell(outcomes.get("75th_percentile"))}
                {outcome_cell(outcomes.get("90th_percentile"))}
            </tr>
            """
        )

    return f"""
<section>
    <h2>Portfolio Risk by Allocation</h2>

    <p class="section-intro">
        These results show how different asset allocations affect the range of
        possible ending portfolio values. Lower-percentile results represent
        less favorable market conditions, while higher-percentile results
        represent more favorable conditions. The table shows how portfolio
        outcomes change across a range of market conditions.
    </p>

    <div class="table-scroll">
        <table class="wide-table comparison-table outcome-table">
            <thead>
                <tr>
                    <th rowspan="2">Equity Allocation</th>
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
                {''.join(rows)}
            </tbody>
        </table>
    </div>
</section>
"""


def _render_historical_window_risk_visualization(
    report_data,
    output_folder,
):
    plot_assets = report_data.historical_plot_assets

    current = plot_assets.get("current")
    minus_20 = plot_assets.get("minus_20")
    plus_20 = plot_assets.get("plus_20")

    if (
        current is None
        or minus_20 is None
        or plus_20 is None
    ):
        return ""

    def image_src(asset):
        path = relative_asset_path(
            asset["path"],
            output_folder,
        )

        return path.replace(
            os.sep,
            "/",
        )

    current_src = image_src(current)
    minus_20_src = image_src(minus_20)
    plus_20_src = image_src(plus_20)

    current_equity = _fmt_allocation_percent(
        current["equity_percentage"]
    )

    minus_20_equity = _fmt_allocation_percent(
        minus_20["equity_percentage"]
    )

    plus_20_equity = _fmt_allocation_percent(
        plus_20["equity_percentage"]
    )

    return f"""
<section class="historical-allocation-risk">
    <h2>Historical-Window Risk Visualization</h2>

    <p class="section-intro">
        These charts compare how the modeled portfolio would have behaved
        across the same rolling historical market windows under three asset
        allocations centered on the household's current allocation.
    </p>

    <div class="allocation-risk-primary">
        <div class="allocation-risk-heading">
            Current Allocation - {_safe(current_equity)} Equity
        </div>

        <img
            src="{_safe(current_src)}"
            alt="Historical-window portfolio outcomes for the current asset allocation"
        >
    </div>

    <div class="allocation-risk-comparisons">

        <div class="allocation-risk-secondary">
            <div class="allocation-risk-heading">
                Current -20 Points Equity -
                {_safe(minus_20_equity)} Equity
            </div>

            <img
                src="{_safe(minus_20_src)}"
                alt="Historical-window portfolio outcomes for current allocation minus 20 percentage points equity"
            >
        </div>

        <div class="allocation-risk-secondary">
            <div class="allocation-risk-heading">
                Current +20 Points Equity -
                {_safe(plus_20_equity)} Equity
            </div>

            <img
                src="{_safe(plus_20_src)}"
                alt="Historical-window portfolio outcomes for current allocation plus 20 percentage points equity"
            >
        </div>

    </div>
</section>
"""


def _render_method_note(report_data):
    return """
<section>
    <h2>Comparison Method</h2>

    <p class="section-intro">
        Each allocation case uses the same household assumptions and
        deterministic market-return assumptions. Portfolio risk is
        evaluated using rolling historical return windows.
        Only the modeled Stock/Bond/Cash allocation is changed.
    </p>

    <p class="section-intro">
        To reduce report generation time, comparison allocations use
        every second valid historical starting year. The household's
        current allocation uses all available Historical Windows.
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

    .allocation-components {{
        font-size: 16px;
    }}

    .outcome-table {{
        font-size: 12px;
    }}

    .outcome-table th,
    .outcome-table td {{
        white-space: nowrap;
    }}

    .allocation-results-table {{
        table-layout: fixed;
    }}

    .allocation-results-table thead th {{
        height: 54px;
        white-space: normal;
        line-height: 1.25;
        vertical-align: middle;
    }}

    .table-scroll {{
        overflow-x: auto;
    }}

    .historical-allocation-risk {{
        margin-top: 34px;
    }}

    .allocation-risk-primary,
    .allocation-risk-secondary {{
        border: 1px solid #ccc;
        background: #fafafa;
        border-radius: 6px;
        padding: 14px;
    }}

    .allocation-risk-primary {{
        margin-top: 14px;
    }}

    .allocation-risk-primary img {{
        display: block;
        width: 88%;
        height: auto;
        margin: 10px auto 0 auto;
    }}

    .allocation-risk-comparisons {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
        margin-top: 16px;
    }}

    .allocation-risk-secondary img {{
        display: block;
        width: 100%;
        height: auto;
        margin: 10px auto 0 auto;
    }}

    .allocation-risk-heading {{
        font-size: 16px;
        font-weight: bold;
        color: #333;
        text-align: center;
    }}

    .ending-portfolio-zero {{
        color: #b00020;
    }}

    .market-left {{
        text-align: left !important;
    }}

    @media print {{
        .allocation-risk-primary,
        .allocation-risk-secondary {{
            page-break-inside: avoid;
            break-inside: avoid;
        }}

        .allocation-risk-comparisons {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }}
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
            market_wording="historical market conditions",
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

        {_render_historical_window_risk_visualization(
            report_data,
            output_folder,
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