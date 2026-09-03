import copy
import cProfile
import pstats
from datetime import datetime

import numpy as np

from .simulation import run_pipeline
from src.warpsimlab.reports.report_data import RetirementSSComparisonReportData
from src.warpsimlab.reports.retirement_ss_comparison_report import generate_retirement_ss_comparison_report


PROFILE_RETIREMENT_SS_REPORT = False


SS_FACTORS = {
    62: 0.70,
    63: 0.75,
    64: 0.80,
    65: 0.867,
    66: 0.933,
    67: 1.00,
    68: 1.08,
    69: 1.16,
    70: 1.24,
}


def _distribution(values):
    values = np.asarray(values, dtype=float)

    if values.size == 0:
        return {
            "minimum": 0.0,
            "p10": 0.0,
            "p25": 0.0,
            "median": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "maximum": 0.0,
        }

    return {
        "minimum": float(np.min(values)),
        "p10": float(np.percentile(values, 10)),
        "p25": float(np.percentile(values, 25)),
        "median": float(np.median(values)),
        "p75": float(np.percentile(values, 75)),
        "p90": float(np.percentile(values, 90)),
        "maximum": float(np.max(values)),
    }


def _build_depletion_statistics(total_assets, years):
    total_assets = np.asarray(total_assets, dtype=float)
    years = np.asarray(years)

    reaches_zero = np.any(total_assets <= 0.0, axis=1)
    zero_indices = []

    for path in total_assets[reaches_zero]:
        zero_locations = np.flatnonzero(path <= 0.0)

        if zero_locations.size > 0:
            zero_indices.append(int(zero_locations[0]))

    reaching_zero_count = int(np.sum(reaches_zero))
    historical_window_count = int(total_assets.shape[0])

    if historical_window_count > 0:
        reaching_zero_percent = reaching_zero_count / historical_window_count * 100.0
    else:
        reaching_zero_percent = 0.0

    if zero_indices:
        zero_years = np.asarray([years[index] for index in zero_indices], dtype=float)
        earliest_zero_year = float(np.min(zero_years))
        median_zero_year = float(np.median(zero_years))
        latest_zero_year = float(np.max(zero_years))
    else:
        earliest_zero_year = None
        median_zero_year = None
        latest_zero_year = None

    return {
        "historical_window_count": historical_window_count,
        "reaching_zero_count": reaching_zero_count,
        "reaching_zero_percent": float(reaching_zero_percent),
        "earliest_reaching_zero_year": earliest_zero_year,
        "median_reaching_zero_year": median_zero_year,
        "latest_reaching_zero_year": latest_zero_year,
    }


def _years_until_event(person, age_attribute):
    return int(getattr(person, age_attribute)) - int(person.age)


def _household_event_age(husband, wife, second_person_enabled, age_attribute):
    husband_event_age = int(getattr(husband, age_attribute))

    if not second_person_enabled or wife is None:
        return husband_event_age

    wife_event_age = int(getattr(wife, age_attribute))
    husband_years = _years_until_event(husband, age_attribute)
    wife_years = _years_until_event(wife, age_attribute)

    if husband_years > wife_years:
        return husband_event_age

    if wife_years > husband_years:
        return wife_event_age

    return max(husband_event_age, wife_event_age)


def _clamp_social_security_age(age):
    return max(62, min(70, int(age)))


def _adjust_social_security(person, baseline_person, year_shift):
    if year_shift == 0:
        return

    baseline_ss_age = int(baseline_person.ss_age)
    requested_ss_age = baseline_ss_age + int(year_shift)
    actual_ss_age = _clamp_social_security_age(requested_ss_age)
    baseline_factor_age = _clamp_social_security_age(baseline_ss_age)

    baseline_factor = SS_FACTORS[baseline_factor_age]
    new_factor = SS_FACTORS[actual_ss_age]
    baseline_ss = float(baseline_person.ss)

    if baseline_factor > 0.0:
        baseline_pia = baseline_ss / baseline_factor
    else:
        baseline_pia = baseline_ss

    person.ss_age = actual_ss_age
    person.ss = round(baseline_pia * new_factor, 2)


def _build_case_persons(husband, wife, second_person_enabled, retirement_shift, social_security_shift):
    case_husband = copy.deepcopy(husband)
    case_wife = None

    if second_person_enabled and wife is not None:
        case_wife = copy.deepcopy(wife)

    case_husband.retire_age = int(husband.retire_age) + int(retirement_shift)
    _adjust_social_security(case_husband, husband, social_security_shift)

    if case_wife is not None:
        case_wife.retire_age = int(wife.retire_age) + int(retirement_shift)
        _adjust_social_security(case_wife, wife, social_security_shift)

    return case_husband, case_wife


def _deterministic_portfolio_at_retirement(total_assets, case_husband, case_wife, second_person_enabled):
    total_assets = np.asarray(total_assets, dtype=float)

    if total_assets.ndim != 2:
        raise ValueError("Expected a 2D deterministic portfolio array, " f"got shape {total_assets.shape}")

    retirement_index = int(case_husband.retire_age) - int(case_husband.age)

    if second_person_enabled and case_wife is not None:
        wife_retirement_index = int(case_wife.retire_age) - int(case_wife.age)
        retirement_index = max(retirement_index, wife_retirement_index)

    retirement_index = min(max(retirement_index, 0), total_assets.shape[1] - 1)

    return float(total_assets[0, retirement_index])


def _deterministic_monthly_retirement_income(core, case_husband, case_wife, second_person_enabled):
    social_security = np.asarray(core["breakdown_by_class"]["ss"], dtype=float)
    pension = np.asarray(core["breakdown_by_class"]["pension"], dtype=float)
    annuity = np.asarray(core["breakdown_by_class"]["annuity"], dtype=float)

    retirement_income = social_security + pension + annuity
    reference_person = case_husband

    if second_person_enabled and case_wife is not None:
        husband_retirement_years = _years_until_event(case_husband, "retire_age")
        wife_retirement_years = _years_until_event(case_wife, "retire_age")

        if wife_retirement_years > husband_retirement_years:
            reference_person = case_wife

    years_until_age_70 = 70 - int(reference_person.age)
    year_index = years_until_age_70 + 1

    if year_index < 1 or year_index >= retirement_income.shape[1]:
        return None

    return float(retirement_income[0, year_index] / 12.0)


def _deterministic_final_monthly_retirement_income(core):
    social_security = np.asarray(core["breakdown_by_class"]["ss"], dtype=float)
    pension = np.asarray(core["breakdown_by_class"]["pension"], dtype=float)
    annuity = np.asarray(core["breakdown_by_class"]["annuity"], dtype=float)

    retirement_income = social_security + pension + annuity

    return float(retirement_income[0, -1] / 12.0)


def _deterministic_lifetime_total(values):
    values = np.asarray(values, dtype=float)

    if values.ndim != 2:
        raise ValueError("Expected a 2D deterministic array, " f"got shape {values.shape}")

    return float(np.sum(values[0]))


def _build_case_result(
    deterministic_pipeline_result,
    historical_pipeline_result,
    case_husband,
    case_wife,
    second_person_enabled,
    requested_retirement_age,
    requested_ss_age,
    baseline_retirement_age,
    baseline_ss_age,
):
    deterministic_core = deterministic_pipeline_result["core"]
    historical_core = historical_pipeline_result["core"]

    actual_retirement_age = _household_event_age(case_husband, case_wife, second_person_enabled, "retire_age")
    actual_ss_age = _household_event_age(case_husband, case_wife, second_person_enabled, "ss_age")

    husband_timing = {
        "current_age": int(case_husband.age),
        "retirement_age": int(case_husband.retire_age),
        "social_security_age": int(case_husband.ss_age),
        "social_security_amount": float(case_husband.ss),
    }

    wife_timing = None

    if second_person_enabled and case_wife is not None:
        wife_timing = {
            "current_age": int(case_wife.age),
            "retirement_age": int(case_wife.retire_age),
            "social_security_age": int(case_wife.ss_age),
            "social_security_amount": float(case_wife.ss),
        }

    deterministic_total_assets = np.asarray(deterministic_core["total_assets"], dtype=float)
    deterministic_ending_portfolio = float(deterministic_total_assets[0, -1])

    return {
        "requested_retirement_age": int(requested_retirement_age),
        "requested_social_security_age": int(requested_ss_age),
        "actual_household_retirement_age": int(actual_retirement_age),
        "actual_household_social_security_age": int(actual_ss_age),

        "is_current_retirement_timing": int(requested_retirement_age) == int(baseline_retirement_age),
        "is_current_social_security_timing": int(requested_ss_age) == int(baseline_ss_age),
        "is_current_timing": (
            int(requested_retirement_age) == int(baseline_retirement_age)
            and int(requested_ss_age) == int(baseline_ss_age)
        ),

        "husband": husband_timing,
        "wife": wife_timing,

        # -----------------------------------------------------
        # Deterministic financial quantities
        # -----------------------------------------------------

        "deterministic_ending_portfolio": deterministic_ending_portfolio,
        "deterministic_portfolio_at_retirement": _deterministic_portfolio_at_retirement(
            deterministic_core["total_assets"], case_husband, case_wife, second_person_enabled
        ),
        "deterministic_total_social_security": _deterministic_lifetime_total(
            deterministic_core["breakdown_by_class"]["ss"]
        ),
        "deterministic_monthly_retirement_income": _deterministic_monthly_retirement_income(
            deterministic_core, case_husband, case_wife, second_person_enabled
        ),
        "deterministic_final_monthly_retirement_income": _deterministic_final_monthly_retirement_income(
            deterministic_core
        ),
        "deterministic_lifetime_cash_flow_shortfall": _deterministic_lifetime_total(
            deterministic_core["cash_flow_shortfall"]
        ),

        # -----------------------------------------------------
        # Historical Window risk quantity
        # -----------------------------------------------------

        "depletion": _build_depletion_statistics(
            historical_core["total_assets"], historical_pipeline_result["years_list"]
        ),
    }


def run_sim_retirement_ss_comparison_report(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
):
    report_options = getattr(sim_config, "report_options", {}) or {}

    retirement_ages = sorted({int(value) for value in report_options.get("retirement_ages", [])})
    social_security_ages = sorted({int(value) for value in report_options.get("social_security_ages", [])})

    second_person_enabled = bool(getattr(sim_config, "second_person_enabled", False) and wife is not None)

    baseline_retirement_age = _household_event_age(husband, wife, second_person_enabled, "retire_age")
    baseline_ss_age = _household_event_age(husband, wife, second_person_enabled, "ss_age")

    retirement_ages = sorted(set(retirement_ages + [int(baseline_retirement_age)]))
    social_security_ages = sorted(set(social_security_ages + [int(baseline_ss_age)]))

    baseline = {
        "household_retirement_age": int(baseline_retirement_age),
        "household_social_security_age": int(baseline_ss_age),
        "husband": {
            "current_age": int(husband.age),
            "retirement_age": int(husband.retire_age),
            "social_security_age": int(husband.ss_age),
            "social_security_amount": float(husband.ss),
        },
        "wife": None,
    }

    if second_person_enabled:
        baseline["wife"] = {
            "current_age": int(wife.age),
            "retirement_age": int(wife.retire_age),
            "social_security_age": int(wife.ss_age),
            "social_security_amount": float(wife.ss),
        }

    original_subplot_mode = sim_config.subplot_mode
    original_sim_type = sim_config.sim_type
    original_monte_carlo_mode = sim_config.monte_carlo_mode
    original_include_realestate = sim_config.include_realestate
    original_show_shortfall_rate = sim_config.show_simulated_shortfall_rate
    original_calculate_shortfall_rate = sim_config.calculate_simulated_shortfall_rate
    original_overlay_tax_impacts = sim_config.overlay_tax_impacts
    original_overlay_fund_expense_impacts = sim_config.overlay_fund_expense_impacts
    original_historical_window_stride = sim_config.historical_window_stride

    cases = []

    try:
        # This report compares the investment portfolio.
        # Keep real estate excluded, matching the existing
        # Retirement / Social Security comparison semantics.
        sim_config.include_realestate = False

        # Historical Window depletion is calculated directly.
        sim_config.show_simulated_shortfall_rate = False
        sim_config.calculate_simulated_shortfall_rate = False

        # Prevent unrelated overlay runs for every timing case.
        sim_config.overlay_tax_impacts = False
        sim_config.overlay_fund_expense_impacts = False

        if PROFILE_RETIREMENT_SS_REPORT:
            profiler = cProfile.Profile()
            profiler.enable()

        for retirement_age in retirement_ages:
            retirement_shift = int(retirement_age) - int(baseline_retirement_age)

            for ss_age in social_security_ages:
                social_security_shift = int(ss_age) - int(baseline_ss_age)

                # ---------------------------------------------
                # Deterministic case
                # ---------------------------------------------

                deterministic_husband, deterministic_wife = _build_case_persons(
                    husband, wife, second_person_enabled, retirement_shift, social_security_shift
                )

                sim_config.subplot_mode = "fill"
                sim_config.sim_type = "portfolio_sim"

                deterministic_pipeline_result = run_pipeline(
                    husband_portfolio,
                    wife_portfolio,
                    deterministic_husband,
                    deterministic_wife,
                    expenses,
                    sim_config,
                    force_num_sims=1,
                )

                # ---------------------------------------------
                # Historical Window case
                # ---------------------------------------------

                historical_husband, historical_wife = _build_case_persons(
                    husband, wife, second_person_enabled, retirement_shift, social_security_shift
                )

                sim_config.subplot_mode = "monte_carlo"
                sim_config.sim_type = "portfolio_sim"
                sim_config.monte_carlo_mode = "rollingHistoricalWindows"

                # We are going to create a 6x6 matrix of percents portfolio goes to zero.
                # This is very computational heavy. Lets use stride 4 except on our
                # baseline, where we will use stride 1.
                if int(retirement_age) == int(baseline_retirement_age) and int(ss_age) == int(baseline_ss_age):
                    sim_config.historical_window_stride = 1
                else:
                    # sim_config.historical_window_stride = 2
                    sim_config.historical_window_stride = 4

                historical_pipeline_result = run_pipeline(
                    husband_portfolio,
                    wife_portfolio,
                    historical_husband,
                    historical_wife,
                    expenses,
                    sim_config,
                    force_num_sims=None,
                )

                cases.append(
                    _build_case_result(
                        deterministic_pipeline_result,
                        historical_pipeline_result,
                        deterministic_husband,
                        deterministic_wife,
                        second_person_enabled,
                        retirement_age,
                        ss_age,
                        baseline_retirement_age,
                        baseline_ss_age,
                    )
                )

        if PROFILE_RETIREMENT_SS_REPORT:
            profiler.disable()

            stats = pstats.Stats(profiler)
            stats.strip_dirs()
            stats.sort_stats("cumulative")
            stats.print_stats(40)

    finally:
        sim_config.subplot_mode = original_subplot_mode
        sim_config.sim_type = original_sim_type
        sim_config.monte_carlo_mode = original_monte_carlo_mode
        sim_config.include_realestate = original_include_realestate
        sim_config.show_simulated_shortfall_rate = original_show_shortfall_rate
        sim_config.calculate_simulated_shortfall_rate = original_calculate_shortfall_rate
        sim_config.overlay_tax_impacts = original_overlay_tax_impacts
        sim_config.overlay_fund_expense_impacts = original_overlay_fund_expense_impacts
        sim_config.historical_window_stride = original_historical_window_stride

    generated_timestamp = datetime.now()
    visible_report_id = generated_timestamp.strftime("%Y-%m-%d %H:%M:%S")

    report_data = RetirementSSComparisonReportData(
        report_options=report_options,
        report_metadata={
            "Report Title": "WARPSimLab Retirement & Social Security Timing Comparison Report",
            "Generated Timestamp": visible_report_id,
            "Report ID": visible_report_id,
            "Report Type": "retirement_ss_comparison_report",
            "Output Format": "HTML",
            "Projection Period": (
                f"{int(sim_config.start_year)}-{int(sim_config.start_year) + int(sim_config.years_to_simulate)} "
                f"({int(sim_config.years_to_simulate)} Years)"
            ),
            "Report Basis": (
                "Real Dollars (Inflation Adjusted)"
                if getattr(sim_config, "plot_mode", None) == "real"
                else "Raw Dollars (Future Nominal Values)"
            ),
        },
        baseline=baseline,
        retirement_ages=retirement_ages,
        social_security_ages=social_security_ages,
        comparison_cases=cases,
        warnings=[],
    )

    return generate_retirement_ss_comparison_report(report_data)