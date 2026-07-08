# run_sim_year_by_year_report.py

from datetime import datetime

from .simulation import run_pipeline
from src.warpsimlab.reports.report_data import YearByYearReportData
from src.warpsimlab.reports.year_by_year_report import generate_year_by_year_report


def _as_float(value, default=0.0):
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _array_value(results, key, index, default=0.0):
    values = results.get(key)

    if values is None:
        return default

    try:
        return _as_float(values[index], default=default)
    except (IndexError, TypeError, ValueError):
        return default


def _build_projection_period_label(sim_config):
    start_year = getattr(sim_config, "start_year", None)
    years = getattr(sim_config, "years_to_simulate", None)

    if start_year is None or years is None:
        return "N/A"

    try:
        start_year = int(start_year)
        years = int(years)
        end_year = start_year + years
        return f"{start_year}-{end_year} ({years} Years)"
    except (TypeError, ValueError):
        return "N/A"


def _build_report_basis_label(sim_config):
    plot_mode = getattr(sim_config, "plot_mode", None)

    if plot_mode == "real":
        return "Real Dollars (Inflation Adjusted)"

    if plot_mode == "raw":
        return "Raw Dollars (Future Nominal Values)"

    return "N/A"


def _build_age_value(person, index):
    if person is None:
        return None

    try:
        return int(getattr(person, "age", 0)) + int(index)
    except (TypeError, ValueError):
        return None


def _build_year_row(results, index, husband, wife, sim_config):
    pre_tax_assets = _array_value(results, "pre_tax_assets", index)
    post_tax_assets = _array_value(results, "post_tax_assets", index)
    roth_assets = _array_value(results, "roth_assets", index)
    hsa_assets = _array_value(results, "hsa_assets", index)
    real_estate = _array_value(results, "real_estate", index)

    total_portfolio = (
        pre_tax_assets
        + post_tax_assets
        + roth_assets
        + hsa_assets
    )

    pensions_and_annuities = (
        _array_value(results, "pensions", index)
        + _array_value(results, "annuities", index)
    )

    row = {
        "Year": _array_value(results, "year", index),
        "Age": _build_age_value(husband, index),
        "Wages": _array_value(results, "wages", index),
        "Social Security": _array_value(results, "social_security", index),
        "Pensions & Annuities": pensions_and_annuities,
        "RMD": _array_value(results, "rmd", index),
        "Withdrawals": _array_value(results, "withdrawal", index),
        "Gross Income": _array_value(results, "gross_income", index),
        "Taxes": _array_value(results, "taxes", index),
        "Household Expenses": _array_value(results, "expenses", index),
        "Net Cash Flow": _array_value(results, "net_cash_flow", index),
        "Fund Expenses": _array_value(results, "fund_expenses", index),
        "Pre-Tax Assets": pre_tax_assets,
        "Post-Tax Assets": post_tax_assets,
        "Roth Assets": roth_assets,
        "HSA Assets": hsa_assets,
        "Real Estate": real_estate,
        "Total Portfolio": total_portfolio,
        "Total Assets / Net Worth": total_portfolio + real_estate,
    }

    if getattr(sim_config, "second_person_enabled", False) and wife is not None:
        row["Age 1"] = row.pop("Age")
        row["Age 2"] = _build_age_value(wife, index)

    return row


def _build_year_rows(results, husband, wife, sim_config):
    years = results.get("year", [])
    rows = []

    for index in range(len(years)):
        rows.append(
            _build_year_row(
                results,
                index,
                husband,
                wife,
                sim_config,
            )
        )

    return rows


def build_year_by_year_report_data_from_pipeline(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
):
    original_include_realestate = getattr(sim_config, "include_realestate", False)

    try:
        sim_config.include_realestate = True

        p = run_pipeline(
            husband_portfolio,
            wife_portfolio,
            husband,
            wife,
            expenses,
            sim_config,
            force_num_sims=1,
        )
    finally:
        sim_config.include_realestate = original_include_realestate

    results = p["summary_results"]
    report_options = dict(getattr(sim_config, "report_options", {}) or {})

    generated_timestamp = datetime.now()
    visible_report_id = generated_timestamp.strftime("%Y-%m-%d %H:%M:%S")

    return YearByYearReportData(
        report_options=report_options,
        report_metadata={
            "Report Title": "WARPSimLab Year-by-Year Details Report",
            "Generated Timestamp": visible_report_id,
            "Report ID": visible_report_id,
            "Report Type": "year_by_year_report",
            "Projection Period": _build_projection_period_label(sim_config),
            "Report Basis": _build_report_basis_label(sim_config),
        },
        year_rows=_build_year_rows(
            results,
            husband,
            wife,
            sim_config,
        ),
        warnings=[],
    )


def run_sim_year_by_year_report(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
):
    report_data = build_year_by_year_report_data_from_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
    )

    return generate_year_by_year_report(report_data)