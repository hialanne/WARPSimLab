# run_sim_tax_report.py

from datetime import datetime

from .simulation import run_pipeline
from .engines import medicareEngine

def _as_float(value, default=0.0):
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_array(results, key):
    value = results.get(key)
    return [] if value is None else list(value)


def _sum(results, key):
    return float(sum(_as_float(v) for v in _safe_array(results, key)))


def _max(results, key):
    values = [_as_float(v) for v in _safe_array(results, key)]
    return float(max(values)) if values else 0.0


def _min(results, key):
    values = [_as_float(v) for v in _safe_array(results, key)]
    return float(min(values)) if values else 0.0

def _optional_float(value):
    if value is None:
        return None

    value = float(value)

    if value != value:
        return None

    return value


def _irmaa_tier_label(level, medicare_active, lookback_available):
    if not medicare_active:
        return "Not on Medicare"

    if not lookback_available or level is None:
        return "Unavailable"

    if level == 0:
        return "No IRMAA"

    return f"Tier {level}"


def _build_irmaa_yearly_rows(core, husband, wife, sim_config):
    years = list(core["year"][0])
    rows = []
    terminal_year = int(core["terminal_year"][0])
    second_person_enabled = getattr(sim_config, "second_person_enabled", False) and wife is not None

    for i, year in enumerate(years):
        if i == 0:
            continue

        if terminal_year >= 0 and int(year) == terminal_year:
            continue

        husband_alive = bool(core["husband_alive"][0, i])
        wife_alive = bool(core["wife_alive"][0, i])
        husband_age = getattr(husband, "age", 0) + i
        husband_medicare = husband_alive and husband_age >= getattr(husband, "medicare_start_age", 65)

        wife_medicare = False
        if second_person_enabled:
            wife_age = getattr(wife, "age", 0) + i
            wife_medicare = wife_alive and wife_age >= getattr(wife, "medicare_start_age", 65)

        medicare_active = husband_medicare or wife_medicare
        lookback_available = bool(core["irmaa_lookback_available"][0, i])
        level = int(core["irmaa_level"][0, i])

        if level < 0:
            level = None

        filing_status = "Married Filing Jointly"
        if bool(core["irmaa_filing_status_single"][0, i]):
            filing_status = "Single"

        lookback_magi = None
        if lookback_available:
            lookback_magi = _optional_float(core["irmaa_lookback_magi"][0, i])

        lower_threshold = None
        upper_threshold = None

        if medicare_active and lookback_available:
            lower_threshold = _optional_float(core["irmaa_lower_threshold"][0, i])
            upper_threshold = _optional_float(core["irmaa_upper_threshold"][0, i])

        rows.append({
            "IRMAA Year": int(year),
            "MAGI Year": int(year) - 2,
            "Medicare Active": medicare_active,
            "IRMAA MAGI Basis": lookback_magi,
            "Filing Status": filing_status,
            "IRMAA Tier": _irmaa_tier_label(level, medicare_active, lookback_available),
            "Lower Threshold": lower_threshold,
            "Upper Threshold": upper_threshold,
            "Annual IRMAA": _as_float(core["irmaa"][0, i]),
            "Medicare Cost": _as_float(core["medicare_cost"][0, i]),
        })

    return rows


def _build_irmaa_milestones(rows):
    first_medicare = None
    first_irmaa = None

    for row in rows:
        if first_medicare is None and row["Medicare Active"]:
            first_medicare = row

        if first_irmaa is None and row["Annual IRMAA"] > 0.0:
            first_irmaa = row

    milestones = {}

    if first_medicare is None:
        milestones["First Medicare Year"] = {
            "Status": "No Medicare enrollment during the modeled period.",
        }
    else:
        milestones["First Medicare Year"] = {
            "Year": first_medicare["IRMAA Year"],
            "MAGI Year": first_medicare["MAGI Year"],
            "IRMAA MAGI Basis": first_medicare["IRMAA MAGI Basis"],
            "Filing Status": first_medicare["Filing Status"],
            "IRMAA Tier": first_medicare["IRMAA Tier"],
            "Lower Threshold": first_medicare["Lower Threshold"],
            "Upper Threshold": first_medicare["Upper Threshold"],
            "Medicare Cost": first_medicare["Medicare Cost"],
            "Annual IRMAA": first_medicare["Annual IRMAA"],
        }

    if first_irmaa is None:
        milestones["First IRMAA Year"] = {
            "Status": "No IRMAA surcharge projected during the modeled period.",
        }
    else:
        milestones["First IRMAA Year"] = {
            "Year": first_irmaa["IRMAA Year"],
            "MAGI Year": first_irmaa["MAGI Year"],
            "IRMAA MAGI Basis": first_irmaa["IRMAA MAGI Basis"],
            "Filing Status": first_irmaa["Filing Status"],
            "IRMAA Tier": first_irmaa["IRMAA Tier"],
            "Lower Threshold": first_irmaa["Lower Threshold"],
            "Upper Threshold": first_irmaa["Upper Threshold"],
            "Annual IRMAA": first_irmaa["Annual IRMAA"],
        }

    return milestones


def _format_irmaa_range(thresholds, level):
    if level == 0:
        return f"Up to ${thresholds[0]:,.0f}"

    if level == 5:
        return f"Over ${thresholds[4]:,.0f}"

    return f"Over ${thresholds[level - 1]:,.0f} to ${thresholds[level]:,.0f}"


def _build_irmaa_reference_rows():
    single = medicareEngine.IRMAA_THRESHOLDS_2026["Single"]
    married = medicareEngine.IRMAA_THRESHOLDS_2026["Other"]
    rows = []
    previous_annual_irmaa = 0.0

    for level in range(6):
        tier = "No IRMAA"
        if level > 0:
            tier = f"Tier {level}"

        part_b_monthly = (
            medicareEngine.PART_B_STANDARD_MONTHLY_2026
            * medicareEngine.PART_B_IRMAA_MULTIPLIERS[level]
        )
        part_d_monthly = medicareEngine.PART_D_IRMAA_MONTHLY_2026[level]
        annual_irmaa = 12.0 * (part_b_monthly + part_d_monthly)
        increase_from_prior = annual_irmaa - previous_annual_irmaa

        rows.append({
            "Tier": tier,
            "Single MAGI Range": _format_irmaa_range(single, level),
            "Married Filing Jointly MAGI Range": _format_irmaa_range(married, level),
            "Annual IRMAA / Person": annual_irmaa,
            "Annual IRMAA / Two People": annual_irmaa * 2.0,
            "Increase / Person": increase_from_prior,
        })

        previous_annual_irmaa = annual_irmaa

    return rows


def _build_yearly_tax_rows(results, husband, wife, sim_config):
    years = _safe_array(results, "year")
    rows = []
    second_person_enabled = getattr(sim_config, "second_person_enabled", False) and wife is not None
    terminal_year = int(results.get("terminal_year", -1))

    for i, year in enumerate(years):
        if i == 0:
            continue

        if terminal_year >= 0 and int(year) == terminal_year:
            continue

        gross_income = _as_float(results.get("gross_income", [])[i])
        total_taxes = _as_float(results.get("taxes", [])[i])
        effective_tax_rate = total_taxes / gross_income if gross_income > 0.0 else 0.0
        husband_age = getattr(husband, "age", 0) + i

        federal_income_tax = (
            _as_float(results.get("federal_ordinary_tax", [])[i])
            + _as_float(results.get("federal_qualified_dividend_tax", [])[i])
        )

        filing_status = "Single"
        if not bool(results.get("filing_status_single", [])[i]):
            filing_status = "Married Filing Jointly"

        lookback_magi = None
        if bool(results.get("irmaa_lookback_available", [])[i]):
            lookback_magi = _as_float(results.get("irmaa_lookback_magi", [])[i])

        row = {"Year": int(year)}

        if second_person_enabled:
            row["Husband Age"] = husband_age
            row["Wife Age"] = getattr(wife, "age", 0) + i
        else:
            row["Age"] = husband_age

        bracket_lower = _as_float(results.get("federal_bracket_lower_threshold", [])[i])
        bracket_upper = _as_float(results.get("federal_bracket_upper_threshold", [])[i])

        if bracket_lower < 0.0:
            bracket_lower = None

        if bracket_upper < 0.0:
            bracket_upper = None

        row.update({
            "Filing Status": filing_status,
            "Gross Income": gross_income,
            "MAGI": _as_float(results.get("magi", [])[i]),
            "IRMAA Lookback MAGI": lookback_magi,
            "Federal Income Tax": federal_income_tax,
            "Federal Ordinary Tax": _as_float(results.get("federal_ordinary_tax", [])[i]),
            "Federal Qualified Dividend Tax": _as_float(results.get("federal_qualified_dividend_tax", [])[i]),
            "State Income Tax": _as_float(results.get("state_income_tax", [])[i]),
            "Payroll Tax": _as_float(results.get("payroll_tax", [])[i]),
            "Social Security Payroll Tax": _as_float(results.get("social_security_payroll_tax", [])[i]),
            "Medicare Payroll Tax": _as_float(results.get("medicare_tax", [])[i]),
            "Additional Medicare Payroll Tax": _as_float(results.get("additional_medicare_tax", [])[i]),
            "Total Taxes": total_taxes,
            "Effective Tax Rate": effective_tax_rate,
            "Marginal Tax Bracket": _as_float(results.get("tax_bracket", [])[i]),
            "Taxable Ordinary Income": _as_float(results.get("taxable_ordinary_income", [])[i]),
            "Lower Bracket Limit": bracket_lower,
            "Upper Bracket Limit": bracket_upper,
            "Medicare Cost": _as_float(results.get("medicare_cost", [])[i]),
            "IRMAA": _as_float(results.get("irmaa", [])[i]),
            "Traditional Withdrawals": _as_float(results.get("pre_tax_withdrawals", [])[i]),
            "Emergency Tax-Deferred Withdrawal": _as_float(results.get("emergency_pre_tax_used", [])[i]),
            "Roth Conversions": _as_float(results.get("roth_conversions", [])[i]),
            "Roth Withdrawals": _as_float(results.get("roth_withdrawals", [])[i]),
            "Qualified HSA Withdrawals": _as_float(results.get("hsa_qualified_withdrawals", [])[i]),
            "Taxable HSA Withdrawals": _as_float(results.get("hsa_taxable_withdrawals", [])[i]),
            "Qualified Equity Distributions": _as_float(results.get("qualified_equity_distributions", [])[i]),
        })

        if second_person_enabled:
            row["Husband RMD"] = _as_float(results.get("rmd_husband", [])[i])
            row["Wife RMD"] = _as_float(results.get("rmd_wife", [])[i])
            row["Total RMD"] = _as_float(results.get("rmd", [])[i])
        else:
            row["RMD"] = _as_float(results.get("rmd", [])[i])

        rows.append(row)

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

    annual_taxes = [_as_float(value) for value in _safe_array(results, "taxes")[1:]]
    average_effective_rate = lifetime_total / lifetime_gross_income if lifetime_gross_income > 0.0 else 0.0

    return {
        "Lifetime Federal Ordinary Tax": lifetime_federal_ordinary,
        "Lifetime Tax on Dividends and Capital Gains": lifetime_federal_qd,
        "Lifetime Federal Income Tax": lifetime_federal,
        "Lifetime State Income Tax": lifetime_state,
        "Lifetime Payroll Tax": lifetime_payroll,
        "Lifetime Social Security Payroll Tax": lifetime_social_security_payroll,
        "Lifetime Medicare Payroll Tax": lifetime_medicare,
        "Lifetime Additional Medicare Payroll Tax": lifetime_additional_medicare,
        "Lifetime Total Tax": lifetime_total,
        "Lifetime Gross Income": lifetime_gross_income,
        "Average Effective Tax Rate": average_effective_rate,
        "Highest Annual Tax Bill": max(annual_taxes) if annual_taxes else 0.0,
        "Lowest Annual Tax Bill": min(annual_taxes) if annual_taxes else 0.0,
        "Highest Marginal Tax Bracket": _max(results, "tax_bracket"),
    }


def _build_tax_source_summary(results):
    return {
        "Work Income": _sum(results, "wages"),
        "Social Security": _sum(results, "social_security"),
        "Pensions": _sum(results, "pensions"),
        "Annuities": _sum(results, "annuities"),
        "Traditional Withdrawals": _sum(results, "pre_tax_withdrawals"),
        "Emergency Tax-Deferred Withdrawals": _sum(results, "emergency_pre_tax_used"),
        "RMDs": _sum(results, "rmd"),
        "Roth Conversions": _sum(results, "roth_conversions"),
        "Taxable HSA Withdrawals": _sum(results, "hsa_taxable_withdrawals"),
        "Bond Interest": _sum(results, "bond_interest"),
        "Cash Interest": _sum(results, "cash_interest"),
        "Qualified Equity Distributions": _sum(results, "qualified_equity_distributions"),
    }


def _build_roth_summary(results):
    roth_assets = _safe_array(results, "roth_assets")

    return {
        "Starting Roth Balance": _as_float(roth_assets[0]) if roth_assets else 0.0,
        "Ending Roth Balance": _as_float(roth_assets[-1]) if roth_assets else 0.0,
        "Total Roth Conversions": _sum(results, "roth_conversions"),
        "Total Roth Withdrawals": _sum(results, "roth_withdrawals"),
    }


def _build_hsa_summary(results):
    hsa_assets = _safe_array(results, "hsa_assets")

    return {
        "Starting HSA Balance": _as_float(hsa_assets[0]) if hsa_assets else 0.0,
        "Ending HSA Balance": _as_float(hsa_assets[-1]) if hsa_assets else 0.0,
        "Employee HSA Contributions": _sum(results, "hsa_employee_contributions"),
        "Employer HSA Contributions": _sum(results, "hsa_employer_contributions"),
        "Qualified HSA Withdrawals": _sum(results, "hsa_qualified_withdrawals"),
        "Taxable HSA Withdrawals": _sum(results, "hsa_taxable_withdrawals"),
        "Total HSA Withdrawals": _sum(results, "hsa_withdrawals"),
    }


def _build_rmd_summary(results, second_person_enabled):
    years = _safe_array(results, "year")
    total_rmd = [_as_float(v) for v in _safe_array(results, "rmd")]

    def first_rmd_year(values):
        for i, value in enumerate(values):
            if value > 0.0:
                return int(years[i])

        return None

    if second_person_enabled:
        husband_rmd = [_as_float(v) for v in _safe_array(results, "rmd_husband")]
        wife_rmd = [_as_float(v) for v in _safe_array(results, "rmd_wife")]

        return {
            "Husband First RMD Year": first_rmd_year(husband_rmd),
            "Wife First RMD Year": first_rmd_year(wife_rmd),
            "Largest Total RMD": max(total_rmd) if total_rmd else 0.0,
            "Husband Lifetime RMD": sum(husband_rmd),
            "Wife Lifetime RMD": sum(wife_rmd),
            "Lifetime Total RMD": sum(total_rmd),
        }

    return {
        "First RMD Year": first_rmd_year(total_rmd),
        "Largest RMD": max(total_rmd) if total_rmd else 0.0,
        "Lifetime RMD Withdrawals": sum(total_rmd),
    }


def _build_medicare_summary(results):
    lifetime_medicare_cost = _sum(results, "medicare_cost")
    lifetime_irmaa = _sum(results, "irmaa")

    return {
        "Lifetime Medicare Cost": lifetime_medicare_cost,
        "Lifetime IRMAA": lifetime_irmaa,
        "Lifetime Medicare and IRMAA Outlays": lifetime_medicare_cost + lifetime_irmaa,
    }


def build_tax_report_data_from_pipeline(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
):
    original_calculate_shortfall_rate = sim_config.calculate_simulated_shortfall_rate

    try:
        sim_config.calculate_simulated_shortfall_rate = False

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
        sim_config.calculate_simulated_shortfall_rate = original_calculate_shortfall_rate

    results = p["summary_results"]
    irmaa_yearly_rows = _build_irmaa_yearly_rows(p["core"], husband, wife, sim_config)
    report_options = dict(getattr(sim_config, "report_options", {}) or {})

    generated_timestamp = datetime.now()
    visible_report_id = generated_timestamp.strftime("%Y-%m-%d %H:%M:%S")
    second_person_enabled = getattr(sim_config, "second_person_enabled", False) and wife is not None

    years = _safe_array(results, "year")

    years = _safe_array(results, "year")
    terminal_year = int(results.get("terminal_year", -1))

    if years:
        projection_period = f"{int(years[0])}-{int(years[-1])} ({len(years) - 1} Years)"
        if terminal_year >= 0 and int(years[-1]) == terminal_year:
            projection_period += f"; {terminal_year} is the terminal death year"
    else:
        projection_period = "N/A"

    return {
        "report_options": report_options,
        "report_metadata": {
            "Report Title": "WARPSimLab Tax and Medicare Report",
            "Generated Timestamp": visible_report_id,
            "Report ID": visible_report_id,
            "Report Type": "tax_report",
            "Projection Period": projection_period,
            "Report Basis": (
                "Real Dollars (Inflation Adjusted)"
                if getattr(sim_config, "inflation_mode", None) == "real"
                else "Raw Dollars (Future Nominal Values)"
            ),
        },
        "tax_settings": {
            "Calculate Income Taxes": getattr(sim_config, "calculate_income_taxes", None),
            "Calculate Payroll Taxes": getattr(sim_config, "calculate_payroll_taxes", None),
            "Calculate State Taxes": getattr(sim_config, "calculate_state_taxes", None),
            "Initial Tax Filing Status": getattr(sim_config, "tax_filing_status", None),
            "State of Residence": getattr(sim_config, "state_of_residence", None),
            "Include RMDs": getattr(sim_config, "include_rmd", None),
            "IRMAA Enabled": getattr(sim_config, "irmaa_enabled", False),
        },
        "lifetime_tax_summary": _build_lifetime_tax_summary(results),
        "tax_source_summary": _build_tax_source_summary(results),
        "roth_summary": _build_roth_summary(results),
        "hsa_summary": _build_hsa_summary(results),
        "rmd_summary": _build_rmd_summary(results, second_person_enabled),
        "medicare_summary": _build_medicare_summary(results),
        "yearly_tax_rows": _build_yearly_tax_rows(results, husband, wife, sim_config),
        "irmaa_milestones": _build_irmaa_milestones(irmaa_yearly_rows),
        "irmaa_yearly_rows": irmaa_yearly_rows,
        "irmaa_reference_rows": _build_irmaa_reference_rows(),
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