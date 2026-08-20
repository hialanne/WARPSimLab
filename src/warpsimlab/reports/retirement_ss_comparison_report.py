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
    <h2>Retirement and Social Security Timing</h2>

    <div class="current-timing-summary">
        <div>
            <strong>Household Retirement Age</strong>
            <span>{_safe(_fmt_age(baseline["household_retirement_age"]))}</span>
        </div>
        <div>
            <strong>Household Social Security Age</strong>
            <span>{_safe(_fmt_age(baseline["household_social_security_age"]))}</span>
        </div>
    </div>

    <table class="wide-table timing-table compact-timing-table">
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
    <p class="section-intro timing-definition">
        Household Retirement Age is the age when the household has no
        remaining wage earners. Household Social Security Age is the
        comparison age used to shift Social Security claiming ages for
        the household.
    </p>
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
    <h2>Comparison Method</h2>

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
            Each timing combination uses the same household assumptions and
            deterministic market-return assumptions. Historical return
            sequences are evaluated separately for portfolio depletion risk.
            Only retirement timing and Social Security claiming timing are
            changed.
        </p>
        <p>
            To reduce report generation time, comparison scenarios use every
            fourth valid historical starting year. The household's current
            retirement and Social Security timing uses all available historical
            windows.
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
                <td>{_safe(_fmt_currency(
                    case[
                        "deterministic_portfolio_at_retirement"
                    ]
                ))}</td>
                <td>{_safe(_fmt_percent(
                    case["depletion"][
                        "reaching_zero_percent"
                    ]
                ))}</td>
                <td>{_safe(_fmt_currency(
                    case[
                        "deterministic_ending_portfolio"
                    ]
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
                <th>Portfolio at Retirement</th>
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

        husband_monthly_ss = (
            float(
                case["husband"][
                    "social_security_amount"
                ]
            )
            / 12.0
        )

        wife_monthly_ss = None

        if case["wife"] is not None:
            wife_monthly_ss = (
                float(
                    case["wife"][
                        "social_security_amount"
                    ]
                )
                / 12.0
            )

        rows.append(
            f"""
            <tr{_current_row_class(case)}>
                <td>{_safe(label)}</td>
                <td>{_safe(_fmt_currency(
                    husband_monthly_ss
                ))}</td>
                <td>{_safe(
                    _fmt_currency(
                        wife_monthly_ss
                    )
                    if wife_monthly_ss is not None
                    else "N/A"
                )}</td>
                <td>{_safe(_fmt_currency(
                    case[
                        "deterministic_total_social_security"
                    ]
                ))}</td>
                <td>{_safe(_fmt_currency(
                    case[
                        "deterministic_monthly_retirement_income"
                    ]
                ))}</td>
                <td>{_safe(_fmt_currency(
                    case[
                        "deterministic_final_monthly_retirement_income"
                    ]
                ))}</td>
                <td>{_safe(_fmt_currency(
                    case[
                        "deterministic_lifetime_cash_flow_shortfall"
                    ]
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
        age {_safe(baseline_retirement_age)}. Monthly Social Security
        amounts reflect the modeled benefit at each claiming age. Total
        Social Security is the amount received during the simulation
        period, not over the household's lifetime.
    </p>

    <table class="wide-table comparison-table">
        <thead>
            <tr>
                <th>Household Social Security Age</th>
                <th>Husband Monthly SS</th>
                <th>Wife Monthly SS</th>
                <th>Total Social Security During Simulation</th>
                <th>Monthly Retirement Income at Age 70</th>
                <th>Monthly Retirement Income in Final Simulation Year</th>
                <th>Portfolio Support Needed</th>
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

            monthly_income = _fmt_currency(
                case[
                    "deterministic_monthly_retirement_income"
                ]
            )

            ending_value = case[
                "deterministic_ending_portfolio"
            ]

            ending_text = _fmt_currency(
                ending_value
            )

            ending_class = (
                "matrix-portfolio-zero"
                if float(ending_value) <= 0.0
                else "matrix-portfolio-positive"
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
                f"<div class='matrix-depletion'>"
                f"{_safe(value)}"
                "</div>"
                f"<div class='matrix-income'>"
                f"{_safe(monthly_income)}/mo"
                "</div>"
                f"<div class='{ending_class}'>"
                f"{_safe(ending_text)}"
                "</div>"
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
        Each cell shows three results for that retirement and Social
        Security combination. Monthly Retirement Income at Age 70 includes
        Social Security, pensions, and annuities being received at that age,
        and excludes wages, portfolio withdrawals, and investment income.
        Pension and annuity start dates remain unchanged. For couples,
        age 70 refers to the same person whose retirement defines Household
        Retirement Age. The current household timing is outlined.
    </p>

    <div class="matrix-legend">
        <span class="matrix-depletion">
            Scenarios That Depleted Portfolio
        </span>
        <span class="matrix-income">
            Monthly Retirement Income at Age 70
        </span>
        <span class="matrix-portfolio-positive">
            Ending Portfolio
        </span>
        <span class="matrix-portfolio-zero">
            $0 Ending Portfolio
        </span>
    </div>

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

    .current-timing-summary {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 14px;
        margin-top: 14px;
        margin-bottom: 14px;
    }

    .current-timing-summary > div {
        border: 1px solid #ccc;
        border-top: 4px solid #2e7d32;
        background: #fafafa;
        border-radius: 6px;
        padding: 12px 14px;
    }

    .current-timing-summary strong,
    .current-timing-summary span {
        display: block;
    }

    .current-timing-summary span {
        margin-top: 6px;
        font-size: 20px;
        font-weight: bold;
    }

    .compact-timing-table {
        margin-top: 0;
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

    .matrix-depletion {
        color: #222;
        font-weight: bold;
    }

    .matrix-income {
        color: #1565c0;
        margin-top: 3px;
    }

    .matrix-portfolio-positive {
        color: #2e7d32;
        margin-top: 3px;
    }

    .matrix-portfolio-zero {
        color: #b00020;
        margin-top: 3px;
    }

    .timing-definition {
        margin-top: 12px;
    }

    .matrix-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 8px 22px;
        margin: 10px 0 14px 0;
        font-size: 13px;
    }

    .matrix-legend span {
        font-weight: bold;
        margin-top: 0;
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
    <title>WARPSimLab Retirement &amp; Social Security Comparison Report</title>

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
                "Retirement & Social Security Comparison Report"
            ),
            market_wording=(
                "modeled and historical market conditions"
            ),
        )}

        {_render_current_timing(
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

        {_render_methodology(
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