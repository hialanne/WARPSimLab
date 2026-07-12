# run_sim_tax_report.py

from datetime import datetime

from .simulation import run_pipeline


def _as_float(value, default=0.0):
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_array(results, key):
    value = results.get(key)

    if value is None:
        return []

    return list(value)


def _sum(results, key):
    return float(sum(_as_float(v) for v in _safe_array(results, key)))


def _max(results, key):
    values = [_as_float(v) for v in _safe_array(results, key)]

    if not values:
        return 0.0

    return float(max(values))


def _min(results, key):
    values = [_as_float(v) for v in _safe_array(results, key)]

    if not values:
        return 0.0

    return float(min(values))


def _build_yearly_tax_rows(results, husband, wife, sim_config):
    years = _safe_array(results, "year")

    rows = []

    for i, year in enumerate(years):
        if i == 0:
            continue

        gross_income = _as_float(results.get("gross_income", [])[i])
        total_taxes = _as_float(results.get("taxes", [])[i])

        effective_tax_rate = 0.0
        if gross_income > 0.0:
            effective_tax_rate = total_taxes / gross_income

        husband_age = getattr(husband, "age", 0) + i

        if getattr(sim_config, "second_person_enabled", False) and wife is not None:
            wife_age = getattr(wife, "age", 0) + i
            age_label = f"{husband_age} / {wife_age}"
        else:
            age_label = husband_age

        federal_income_tax = (
            _as_float(results.get("federal_ordinary_tax", [])[i])
            + _as_float(results.get("federal_qualified_dividend_tax", [])[i])
        )

        rows.append({
            "Year": int(year),
            "Age": age_label,
            "Gross Income": gross_income,
            "Federal Income Tax": federal_income_tax,
            "Federal Ordinary Tax": _as_float(results.get("federal_ordinary_tax", [])[i]),
            "Federal Qualified Dividend Tax": _as_float(results.get("federal_qualified_dividend_tax", [])[i]),
            "State Income Tax": _as_float(results.get("state_income_tax", [])[i]),
            "Payroll Tax": _as_float(results.get("payroll_tax", [])[i]),
            "Social Security Payroll Tax": _as_float(results.get("social_security_payroll_tax", [])[i]),
            "Medicare Tax": _as_float(results.get("medicare_tax", [])[i]),
            "Additional Medicare Tax": _as_float(results.get("additional_medicare_tax", [])[i]),
            "Total Taxes": total_taxes,
            "Effective Tax Rate": effective_tax_rate,
            "Marginal Tax Bracket": _as_float(results.get("tax_bracket", [])[i]),
            "RMD": _as_float(results.get("rmd", [])[i]),
            "Traditional Withdrawals": _as_float(results.get("withdrawal", [])[i]),
            "Roth Withdrawals": _as_float(results.get("roth_withdrawals", [])[i]),
            "HSA Withdrawals": _as_float(results.get("hsa_withdrawals", [])[i]),
        })

    return rows


def _build_lifetime_tax_summary(results):
    lifetime_federal_ordinary = _sum(results, "federal_ordinary_tax")
    lifetime_federal_qd = _sum(results, "federal_qualified_dividend_tax")
    lifetime_federal = lifetime_federal_ordinary + lifetime_federal_qd

    lifetime_state = _sum(results, "state_income_tax")
    lifetime_payroll = _sum(results, "payroll_tax")
    lifetime_social_security_payroll = _sum(results, "social_security_payroll_tax")
    lifetime_medicare = _sum(results, "medicare_tax")
    lifetime_additional_medicare = _sum(results, "additional_medicare_tax")
    lifetime_total = _sum(results, "taxes")
    lifetime_gross_income = _sum(results, "gross_income")

    average_effective_rate = 0.0
    if lifetime_gross_income > 0.0:
        average_effective_rate = lifetime_total / lifetime_gross_income

    return {
        "Lifetime Federal Ordinary Tax": lifetime_federal_ordinary,
        "Lifetime Federal Qualified Dividend Tax": lifetime_federal_qd,
        "Lifetime Federal Income Tax": lifetime_federal,
        "Lifetime State Income Tax": lifetime_state,
        "Lifetime Payroll Tax": lifetime_payroll,
        "Lifetime Social Security Payroll Tax": lifetime_social_security_payroll,
        "Lifetime Medicare Tax": lifetime_medicare,
        "Lifetime Additional Medicare Tax": lifetime_additional_medicare,
        "Lifetime Total Tax": lifetime_total,
        "Lifetime Gross Income": lifetime_gross_income,
        "Average Effective Tax Rate": average_effective_rate,
        "Highest Annual Tax Bill": _max(results, "taxes"),
        "Lowest Annual Tax Bill": _min(results, "taxes"),
        "Highest Marginal Tax Bracket": _max(results, "tax_bracket"),
    }


def _build_tax_source_summary(results):
    return {
        "Work Income": _sum(results, "wages"),
        "Social Security": _sum(results, "social_security"),
        "Pensions": _sum(results, "pensions"),
        "Annuities": _sum(results, "annuities"),
        "Traditional Withdrawals": _sum(results, "withdrawal"),
        "RMDs": _sum(results, "rmd"),
        "Bond Interest": _sum(results, "bond_interest"),
        "Cash Interest": _sum(results, "cash_interest"),
        "Qualified Dividends": _sum(results, "qualified_dividends"),
    }


def _build_roth_summary(results):
    roth_assets = _safe_array(results, "roth_assets")

    return {
        "Starting Roth Balance": _as_float(roth_assets[0]) if roth_assets else 0.0,
        "Ending Roth Balance": _as_float(roth_assets[-1]) if roth_assets else 0.0,
        "Total Roth Withdrawals": _sum(results, "roth_withdrawals"),
    }


def _build_hsa_summary(results):
    hsa_assets = _safe_array(results, "hsa_assets")

    return {
        "Starting HSA Balance": _as_float(hsa_assets[0]) if hsa_assets else 0.0,
        "Ending HSA Balance": _as_float(hsa_assets[-1]) if hsa_assets else 0.0,
        "Total HSA Withdrawals": _sum(results, "hsa_withdrawals"),
    }


def _build_rmd_summary(results):
    rmd_values = [_as_float(v) for v in _safe_array(results, "rmd")]
    years = _safe_array(results, "year")

    first_rmd_year = None

    for i, rmd in enumerate(rmd_values):
        if rmd > 0.0:
            first_rmd_year = int(years[i])
            break

    return {
        "First RMD Year": first_rmd_year,
        "Largest RMD": max(rmd_values) if rmd_values else 0.0,
        "Lifetime RMD Withdrawals": sum(rmd_values),
    }


def build_tax_report_data_from_pipeline(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
):
    p = run_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        force_num_sims=1,
    )

    results = p["summary_results"]
    report_options = dict(getattr(sim_config, "report_options", {}) or {})

    generated_timestamp = datetime.now()
    visible_report_id = generated_timestamp.strftime("%Y-%m-%d %H:%M:%S")

    return {
        "report_options": report_options,
        "report_metadata": {
            "Report Title": "WARPSimLab Tax Report",
            "Generated Timestamp": visible_report_id,
            "Report ID": visible_report_id,
            "Report Type": "tax_report",
            "Projection Period": (
                f"{getattr(sim_config, 'start_year', '')}-"
                f"{getattr(sim_config, 'start_year', 0) + getattr(sim_config, 'years_to_simulate', 0)}"
            ),
            "Report Basis": (
                "Real Dollars (Inflation Adjusted)"
                if getattr(sim_config, "plot_mode", None) == "real"
                else "Raw Dollars (Future Nominal Values)"
            ),
        },
        "tax_settings": {
            "Calculate Income Taxes": getattr(sim_config, "calculate_income_taxes", None),
            "Calculate Payroll Taxes": getattr(sim_config, "calculate_payroll_taxes", None),
            "Calculate State Taxes": getattr(sim_config, "calculate_state_taxes", None),
            "Tax Filing Status": getattr(sim_config, "tax_filing_status", None),
            "State of Residence": getattr(sim_config, "state_of_residence", None),
            "Include RMDs": getattr(sim_config, "include_rmd", None),
        },
        "lifetime_tax_summary": _build_lifetime_tax_summary(results),
        "tax_source_summary": _build_tax_source_summary(results),
        "roth_summary": _build_roth_summary(results),
        "hsa_summary": _build_hsa_summary(results),
        "rmd_summary": _build_rmd_summary(results),
        "yearly_tax_rows": _build_yearly_tax_rows(
            results,
            husband,
            wife,
            sim_config,
        ),
        "warnings": [],
    }


def run_sim_tax_report(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
):
    from src.warpsimlab.reports.tax_report import generate_tax_report

    report_data = build_tax_report_data_from_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
    )

    return generate_tax_report(report_data)