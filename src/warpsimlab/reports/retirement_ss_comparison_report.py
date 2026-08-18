# retirement_ss_comparison_report.py

import os

from src.warpsimlab.reports.report_data import (
    ReportResult,
    RetirementSSComparisonReportData,
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

    if value < 0.0:
        return f"-${abs(value):,.0f}"

    return f"${value:,.0f}"


def _fmt_percent(value):
    if value is None:
        return "N/A"

    return f"{float(value):.1f}%"


def _fmt_age(value):
    if value is None:
        return "N/A"

    return str(int(value))


def _find_case(
    report_data,
    retirement_age,
    social_security_age,
):
    for case in report_data.comparison_cases:
        if (
            int(case["requested_retirement_age"])
            == int(retirement_age)
            and
            int(case["requested_social_security_age"])
            == int(social_security_age)
        ):
            return case

    return None


def _current_case(report_data):
    for case in report_data.comparison_cases:
        if case.get("is_current_timing", False):
            return case

    return None


def _current_row_class(case):
    if case.get("is_current_timing", False):
        return " class='current-row'"

    return ""


def _timing_label(age, is_current):
    label = str(int(age))

    if is_current:
        label += " - Current"

    return label


def _render_current_timing(report_data):
    baseline = report_data.baseline

    husband = baseline["husband"]
    wife = baseline.get("wife")

    rows = [
        f"""
        <tr>
            <th>Household Retirement Age</th>
            <td>{_safe(_fmt_age(baseline["household_retirement_age"]))}</td>
        </tr>
        """,
        f"""
        <tr>
            <th>Household Social Security Age</th>
            <td>{_safe(_fmt_age(baseline["household_social_security_age"]))}</td>
        </tr>
        """,
    ]

    person_rows = [
        f"""
        <tr>
            <th>Husband</th>
            <td>{_safe(_fmt_age(husband["current_age"]))}</td>
            <td>{_safe(_fmt_age(husband["retirement_age"]))}</td>
            <td>{_safe(_fmt_age(husband["social_security_age"]))}</td>
            <td>{_safe(_fmt_currency(husband["social_security_amount"]))}</td>
        </tr>
        """
    ]

    if wife is not None:
        person_rows.append(
            f"""
            <tr>
                <th>Wife</th>
                <td>{_safe(_fmt_age(wife["current_age"]))}</td>
                <td>{_safe(_fmt_age(wife["retirement_age"]))}</td>
                <td>{_safe(_fmt_age(wife["social_security_age"]))}</td>
                <td>{_safe(_fmt_currency(wife["social_security_amount"]))}</td>
            </tr>
            """
        )

    return f"""
<section>
    <h2>Current Timing</h2>

    <p class="section-intro">
        The current household timing is the baseline used for comparison
        throughout this report.
    </p>

    <div class="card-grid two-col">
        <div class="summary-card current-card">
            <h3>Household Timing</h3>
            <table class="kv-table">
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>

        <div class="summary-card">
            <h3>Individual Timing</h3>
            <table class="wide-table timing-table">
                <thead>
                    <tr>
                        <th>Person</th>
                        <th>Current Age</th>
                        <th>Retirement Age</th>
                        <th>Social Security Age</th>
                        <th>Annual Social Security</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(person_rows)}
                </tbody>
            </table>
        </div>
    </div>
</section>
"""


def _render_methodology(report_data):
    has_wife = (
        report_data.baseline.get("wife")
        is not None
    )

    couple_text = ""

    if has_wife:
        couple_text = """
        <p>
            For couples, retirement ages are shifted together by the same
            number of years. Household Retirement Age is defined as the age
            of the person whose retirement causes the household to have no
            remaining wage earners.
        </p>

        <p>
            Social Security claiming ages are also shifted by the same
            number of years for both spouses, preserving the household's
            existing timing relationship as closely as possible.
        </p>
        """

    return f"""
<section>
    <h2>How Timing Alternatives Are Modeled</h2>

    <div class="explanation-card">
        <p>
            Retirement timing and Social Security claiming timing are
            modeled as independent variables. A household may retire before,
            at the same time as, or after Social Security benefits begin.
        </p>

        {couple_text}

        <p>
            Social Security claiming ages are limited to the modeled range
            of ages 62 through 70. If a shifted age would fall below 62,
            benefits begin at 62. If a shifted age would exceed 70, benefits
            begin at 70. The Social Security benefit amount is adjusted using
            the resulting claiming age.
        </p>

        <p>
            Each timing combination is evaluated using the same Historical
            Windows methodology and the household's other modeled assumptions
            are left unchanged.
        </p>
    </div>
</section>
"""


def _render_retirement_comparison(report_data):
    baseline_ss_age = int(
        report_data.baseline[
            "household_social_security_age"
        ]
    )

    rows = []

    for retirement_age in report_data.retirement_ages:
        case = _find_case(
            report_data,
            retirement_age,
            baseline_ss_age,
        )

        if case is None:
            continue

        label = _timing_label(
            retirement_age,
            case.get(
                "is_current_retirement_timing",
                False,
            ),
        )

        rows.append(
            f"""
            <tr{_current_row_class(case)}>
                <td>{_safe(label)}</td>
                <td>{_safe(_fmt_age(case["husband"]["retirement_age"]))}</td>
                <td>{_safe(
                    _fmt_age(
                        case["wife"]["retirement_age"]
                    )
                    if case["wife"] is not None
                    else "N/A"
                )}</td>
                <td>{_safe(_fmt_currency(
                    case["lifetime_wages"]["median"]
                ))}</td>
                <td>{_safe(_fmt_currency(
                    case[
                        "lifetime_cash_flow_shortfall"
                    ]["median"]
                ))}</td>
                <td>{_safe(_fmt_currency(
                    case["lifetime_taxes"]["median"]
                ))}</td>
                <td>{_safe(_fmt_percent(
                    case["depletion"][
                        "reaching_zero_percent"
                    ]
                ))}</td>
                <td>{_safe(_fmt_currency(
                    case["ending_portfolio"]["median"]
                ))}</td>
            </tr>
            """
        )

    return f"""
<section>
    <h2>Retirement Timing Comparison</h2>

    <p class="section-intro">
        This comparison changes retirement timing while holding Social
        Security timing at the household's current setting of age
        {_safe(baseline_ss_age)}.
    </p>

    <table class="wide-table comparison-table">
        <thead>
            <tr>
                <th>Household Retirement Age</th>
                <th>Husband Retirement Age</th>
                <th>Wife Retirement Age</th>
                <th>Median Lifetime Wages</th>
                <th>Median Portfolio Cash Needed</th>
                <th>Median Lifetime Taxes</th>
                <th>Historical Windows Reaching Zero</th>
                <th>Median Ending Portfolio</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
</section>
"""


def _render_social_security_comparison(
    report_data,
):
    baseline_retirement_age = int(
        report_data.baseline[
            "household_retirement_age"
        ]
    )

    rows = []

    for ss_age in report_data.social_security_ages:
        case = _find_case(
            report_data,
            baseline_retirement_age,
            ss_age,
        )

        if case is None:
            continue

        label = _timing_label(
            ss_age,
            case.get(
                "is_current_social_security_timing",
                False,
            ),
        )

        rows.append(
            f"""
            <tr{_current_row_class(case)}>
                <td>{_safe(label)}</td>
                <td>{_safe(_fmt_age(
                    case["husband"][
                        "social_security_age"
                    ]
                ))}</td>
                <td>{_safe(
                    _fmt_age(
                        case["wife"][
                            "social_security_age"
                        ]
                    )
                    if case["wife"] is not None
                    else "N/A"
                )}</td>
                <td>{_safe(_fmt_currency(
                    case["husband"][
                        "social_security_amount"
                    ]
                ))}</td>
                <td>{_safe(
                    _fmt_currency(
                        case["wife"][
                            "social_security_amount"
                        ]
                    )
                    if case["wife"] is not None
                    else "N/A"
                )}</td>
                <td>{_safe(_fmt_currency(
                    case[
                        "lifetime_social_security"
                    ]["median"]
                ))}</td>
                <td>{_safe(_fmt_currency(
                    case[
                        "lifetime_cash_flow_shortfall"
                    ]["median"]
                ))}</td>
                <td>{_safe(_fmt_percent(
                    case["depletion"][
                        "reaching_zero_percent"
                    ]
                ))}</td>
                <td>{_safe(_fmt_currency(
                    case["ending_portfolio"]["median"]
                ))}</td>
            </tr>
            """
        )

    return f"""
<section>
    <h2>Social Security Timing Comparison</h2>

    <p class="section-intro">
        This comparison changes Social Security claiming timing while
        holding retirement timing at the household's current setting of
        age {_safe(baseline_retirement_age)}.
    </p>

    <table class="wide-table comparison-table">
        <thead>
            <tr>
                <th>Household Social Security Age</th>
                <th>Husband Actual SS Age</th>
                <th>Wife Actual SS Age</th>
                <th>Husband Annual SS</th>
                <th>Wife Annual SS</th>
                <th>Median Lifetime SS</th>
                <th>Median Portfolio Cash Needed</th>
                <th>Historical Windows Reaching Zero</th>
                <th>Median Ending Portfolio</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
</section>
"""


def _render_interaction_matrix(report_data):
    header_cells = [
        "<th>Retirement Age</th>"
    ]

    for ss_age in report_data.social_security_ages:
        header_cells.append(
            f"<th>SS {int(ss_age)}</th>"
        )

    rows = []

    baseline_retirement_age = int(
        report_data.baseline[
            "household_retirement_age"
        ]
    )

    baseline_ss_age = int(
        report_data.baseline[
            "household_social_security_age"
        ]
    )

    for retirement_age in report_data.retirement_ages:
        cells = [
            f"<th>{int(retirement_age)}</th>"
        ]

        for ss_age in report_data.social_security_ages:
            case = _find_case(
                report_data,
                retirement_age,
                ss_age,
            )

            if case is None:
                cells.append("<td>N/A</td>")
                continue

            value = _fmt_percent(
                case["depletion"][
                    "reaching_zero_percent"
                ]
            )

            current_class = ""

            if (
                int(retirement_age)
                == baseline_retirement_age
                and int(ss_age)
                == baseline_ss_age
            ):
                current_class = (
                    " class='current-cell'"
                )

            cells.append(
                f"<td{current_class}>"
                f"{_safe(value)}"
                "</td>"
            )

        rows.append(
            "<tr>"
            + "".join(cells)
            + "</tr>"
        )

    return f"""
<section>
    <h2>Retirement and Social Security Interaction</h2>

    <p class="section-intro">
        Each cell shows the percentage of Historical Windows in which the
        modeled portfolio reaches zero for that retirement and Social
        Security timing combination. The current household timing is
        highlighted.
    </p>

    <table class="wide-table matrix-table">
        <thead>
            <tr>
                {''.join(header_cells)}
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
</section>
"""


def _render_portfolio_outcomes(report_data):
    current_case = _current_case(
        report_data
    )

    if current_case is None:
        return ""

    ending = current_case[
        "ending_portfolio"
    ]

    minimum = current_case[
        "minimum_portfolio"
    ]

    return f"""
<section>
    <h2>Current Timing Historical Portfolio Outcomes</h2>

    <p class="section-intro">
        These values provide additional context for the current timing
        configuration. They summarize the range of outcomes across the
        Historical Windows used by this report.
    </p>

    <div class="card-grid two-col">
        <div class="summary-card">
            <h3>Ending Portfolio</h3>

            <table class="kv-table">
                <tbody>
                    <tr>
                        <th>10th Percentile</th>
                        <td>{_safe(_fmt_currency(ending["p10"]))}</td>
                    </tr>
                    <tr>
                        <th>Median</th>
                        <td>{_safe(_fmt_currency(ending["median"]))}</td>
                    </tr>
                    <tr>
                        <th>90th Percentile</th>
                        <td>{_safe(_fmt_currency(ending["p90"]))}</td>
                    </tr>
                    <tr>
                        <th>Minimum</th>
                        <td>{_safe(_fmt_currency(ending["minimum"]))}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="summary-card">
            <h3>Minimum Portfolio During Projection</h3>

            <table class="kv-table">
                <tbody>
                    <tr>
                        <th>10th Percentile</th>
                        <td>{_safe(_fmt_currency(minimum["p10"]))}</td>
                    </tr>
                    <tr>
                        <th>Median</th>
                        <td>{_safe(_fmt_currency(minimum["median"]))}</td>
                    </tr>
                    <tr>
                        <th>Historical Windows Reaching Zero</th>
                        <td>{_safe(_fmt_percent(
                            current_case["depletion"][
                                "reaching_zero_percent"
                            ]
                        ))}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</section>
"""


def generate_retirement_ss_comparison_report(
    report_data: RetirementSSComparisonReportData,
):
    output_folder = (
        get_report_output_folder()
    )

    os.makedirs(
        output_folder,
        exist_ok=True,
    )

    report_id = (
        report_data.report_metadata.get(
            "Report ID",
            "retirement_ss_comparison",
        )
    )

    filename = (
        "retirement_ss_timing_comparison_"
        f"{safe_report_id(report_id)}.html"
    )

    report_path = os.path.join(
        output_folder,
        filename,
    )

    extra_css = """
    .current-card {
        border: 2px solid #2e7d32;
    }

    .current-row td {
        background: #e8f5e9;
        font-weight: bold;
    }

    .current-cell {
        background: #e8f5e9;
        font-weight: bold;
        border: 2px solid #2e7d32 !important;
    }

    .comparison-table th,
    .comparison-table td,
    .matrix-table th,
    .matrix-table td,
    .timing-table th,
    .timing-table td {
        text-align: right;
    }

    .comparison-table th:first-child,
    .comparison-table td:first-child,
    .matrix-table th:first-child,
    .matrix-table td:first-child,
    .timing-table th:first-child,
    .timing-table td:first-child {
        text-align: left;
    }

    .matrix-table td {
        text-align: center;
    }

    @media print {
        .comparison-table,
        .matrix-table {
            font-size: 11px;
        }
    }
    """

    html_text = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>WARPSimLab Retirement &amp; Social Security Timing Comparison Report</title>

    <style>
        {render_base_css()}
        {extra_css}
    </style>
</head>

<body>
    <main class="report-page">

        {render_report_header(
            report_data,
            title=(
                "Retirement & Social Security "
                "Timing Comparison Report"
            ),
            market_wording=(
                "historical market return sequences"
            ),
        )}

        {_render_current_timing(
            report_data
        )}

        {_render_methodology(
            report_data
        )}

        {_render_retirement_comparison(
            report_data
        )}

        {_render_social_security_comparison(
            report_data
        )}

        {_render_interaction_matrix(
            report_data
        )}

        {_render_portfolio_outcomes(
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
        ) as file:
            file.write(
                html_text
            )

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
            errors=[
                str(exc)
            ],
        )