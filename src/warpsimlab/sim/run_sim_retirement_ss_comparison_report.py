import copy

import numpy as np

import copy
from datetime import datetime

import numpy as np

from .simulation import run_pipeline

from src.warpsimlab.reports.report_data import (
    RetirementSSComparisonReportData,
)

from src.warpsimlab.reports.retirement_ss_comparison_report import (
    generate_retirement_ss_comparison_report,
)


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

    reaches_zero = np.any(
        total_assets <= 0.0,
        axis=1,
    )

    zero_indices = []

    for path in total_assets[reaches_zero]:
        zero_locations = np.flatnonzero(
            path <= 0.0
        )

        if zero_locations.size > 0:
            zero_indices.append(
                int(zero_locations[0])
            )

    reaching_zero_count = int(
        np.sum(reaches_zero)
    )

    historical_window_count = int(
        total_assets.shape[0]
    )

    if historical_window_count > 0:
        reaching_zero_percent = (
            reaching_zero_count
            / historical_window_count
            * 100.0
        )
    else:
        reaching_zero_percent = 0.0

    if zero_indices:
        zero_years = np.asarray(
            [
                years[index]
                for index in zero_indices
            ],
            dtype=float,
        )

        earliest_zero_year = float(
            np.min(zero_years)
        )

        median_zero_year = float(
            np.median(zero_years)
        )

        latest_zero_year = float(
            np.max(zero_years)
        )
    else:
        earliest_zero_year = None
        median_zero_year = None
        latest_zero_year = None

    return {
        "historical_window_count": (
            historical_window_count
        ),
        "reaching_zero_count": (
            reaching_zero_count
        ),
        "reaching_zero_percent": float(
            reaching_zero_percent
        ),
        "earliest_reaching_zero_year": (
            earliest_zero_year
        ),
        "median_reaching_zero_year": (
            median_zero_year
        ),
        "latest_reaching_zero_year": (
            latest_zero_year
        ),
    }


def _years_until_event(
    person,
    age_attribute,
):
    return (
        int(getattr(person, age_attribute))
        - int(person.age)
    )


def _household_event_age(
    husband,
    wife,
    second_person_enabled,
    age_attribute,
):
    husband_event_age = int(
        getattr(
            husband,
            age_attribute,
        )
    )

    if (
        not second_person_enabled
        or wife is None
    ):
        return husband_event_age

    wife_event_age = int(
        getattr(
            wife,
            age_attribute,
        )
    )

    husband_years = _years_until_event(
        husband,
        age_attribute,
    )

    wife_years = _years_until_event(
        wife,
        age_attribute,
    )

    if husband_years > wife_years:
        return husband_event_age

    if wife_years > husband_years:
        return wife_event_age

    return max(
        husband_event_age,
        wife_event_age,
    )


def _clamp_social_security_age(age):
    return max(
        62,
        min(
            70,
            int(age),
        ),
    )


def _adjust_social_security(
    person,
    baseline_person,
    year_shift,
):
    if year_shift == 0:
        return

    baseline_ss_age = int(
        baseline_person.ss_age
    )

    requested_ss_age = (
        baseline_ss_age
        + int(year_shift)
    )

    actual_ss_age = (
        _clamp_social_security_age(
            requested_ss_age
        )
    )

    baseline_factor_age = (
        _clamp_social_security_age(
            baseline_ss_age
        )
    )

    baseline_factor = SS_FACTORS[
        baseline_factor_age
    ]

    new_factor = SS_FACTORS[
        actual_ss_age
    ]

    baseline_ss = float(
        baseline_person.ss
    )

    if baseline_factor > 0.0:
        baseline_pia = (
            baseline_ss
            / baseline_factor
        )
    else:
        baseline_pia = baseline_ss

    person.ss_age = actual_ss_age
    person.ss = round(
        baseline_pia
        * new_factor,
        2,
    )


def _build_case_persons(
    husband,
    wife,
    second_person_enabled,
    retirement_shift,
    social_security_shift,
):
    case_husband = copy.deepcopy(
        husband
    )

    case_wife = None

    if (
        second_person_enabled
        and wife is not None
    ):
        case_wife = copy.deepcopy(
            wife
        )

    case_husband.retire_age = (
        int(husband.retire_age)
        + int(retirement_shift)
    )

    _adjust_social_security(
        case_husband,
        husband,
        social_security_shift,
    )

    if case_wife is not None:
        case_wife.retire_age = (
            int(wife.retire_age)
            + int(retirement_shift)
        )

        _adjust_social_security(
            case_wife,
            wife,
            social_security_shift,
        )

    return (
        case_husband,
        case_wife,
    )


def _lifetime_distribution(
    values,
):
    values = np.asarray(
        values,
        dtype=float,
    )

    if values.ndim != 2:
        raise ValueError(
            "Expected a 2D Historical Windows "
            f"array, got shape {values.shape}"
        )

    lifetime_values = np.sum(
        values,
        axis=1,
    )

    return _distribution(
        lifetime_values
    )


def _minimum_portfolio_distribution(
    total_assets,
):
    total_assets = np.asarray(
        total_assets,
        dtype=float,
    )

    minimum_values = np.min(
        total_assets,
        axis=1,
    )

    return _distribution(
        minimum_values
    )


def _ending_portfolio_distribution(
    total_assets,
):
    total_assets = np.asarray(
        total_assets,
        dtype=float,
    )

    ending_values = total_assets[
        :,
        -1,
    ]

    return _distribution(
        ending_values
    )


def _build_case_result(
    pipeline_result,
    case_husband,
    case_wife,
    second_person_enabled,
    requested_retirement_age,
    requested_ss_age,
    baseline_retirement_age,
    baseline_ss_age,
):
    core = pipeline_result["core"]

    actual_retirement_age = (
        _household_event_age(
            case_husband,
            case_wife,
            second_person_enabled,
            "retire_age",
        )
    )

    actual_ss_age = (
        _household_event_age(
            case_husband,
            case_wife,
            second_person_enabled,
            "ss_age",
        )
    )

    husband_timing = {
        "current_age": int(
            case_husband.age
        ),
        "retirement_age": int(
            case_husband.retire_age
        ),
        "social_security_age": int(
            case_husband.ss_age
        ),
        "social_security_amount": float(
            case_husband.ss
        ),
    }

    wife_timing = None

    if (
        second_person_enabled
        and case_wife is not None
    ):
        wife_timing = {
            "current_age": int(
                case_wife.age
            ),
            "retirement_age": int(
                case_wife.retire_age
            ),
            "social_security_age": int(
                case_wife.ss_age
            ),
            "social_security_amount": float(
                case_wife.ss
            ),
        }

    return {
        "requested_retirement_age": int(
            requested_retirement_age
        ),
        "requested_social_security_age": int(
            requested_ss_age
        ),
        "actual_household_retirement_age": int(
            actual_retirement_age
        ),
        "actual_household_social_security_age": int(
            actual_ss_age
        ),
        "is_current_retirement_timing": (
            int(requested_retirement_age)
            == int(baseline_retirement_age)
        ),
        "is_current_social_security_timing": (
            int(requested_ss_age)
            == int(baseline_ss_age)
        ),
        "is_current_timing": (
            int(requested_retirement_age)
            == int(baseline_retirement_age)
            and int(requested_ss_age)
            == int(baseline_ss_age)
        ),
        "husband": husband_timing,
        "wife": wife_timing,
        "depletion": (
            _build_depletion_statistics(
                core["total_assets"],
                pipeline_result["years_list"],
            )
        ),
        "ending_portfolio": (
            _ending_portfolio_distribution(
                core["total_assets"]
            )
        ),
        "minimum_portfolio": (
            _minimum_portfolio_distribution(
                core["total_assets"]
            )
        ),
        "lifetime_wages": (
            _lifetime_distribution(
                core[
                    "breakdown_by_class"
                ]["work"]
            )
        ),
        "lifetime_social_security": (
            _lifetime_distribution(
                core[
                    "breakdown_by_class"
                ]["ss"]
            )
        ),
        "lifetime_traditional_retirement_contributions": (
            _lifetime_distribution(
                core["ira_401k"]
            )
        ),
        "lifetime_employee_401k_contributions": (
            _lifetime_distribution(
                core[
                    "employee_401k_contributions"
                ]
            )
        ),
        "lifetime_roth_ira_contributions": (
            _lifetime_distribution(
                core[
                    "roth_ira_contributions"
                ]
            )
        ),
        "lifetime_roth_workplace_contributions": (
            _lifetime_distribution(
                core[
                    "roth_workplace_contributions"
                ]
            )
        ),
        "lifetime_taxes": (
            _lifetime_distribution(
                core["taxes"]
            )
        ),
        "lifetime_expenses": (
            _lifetime_distribution(
                core["expense_amt"]
            )
        ),
        "lifetime_cash_flow_shortfall": (
            _lifetime_distribution(
                core[
                    "cash_flow_shortfall"
                ]
            )
        ),
        "lifetime_uncovered_expense": (
            _lifetime_distribution(
                core[
                    "uncovered_expense"
                ]
            )
        ),
        "lifetime_withdrawal_income": (
            _lifetime_distribution(
                core[
                    "breakdown_by_class"
                ]["withdrawal"]
            )
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
    report_options = (
        getattr(
            sim_config,
            "report_options",
            {},
        )
        or {}
    )

    retirement_ages = sorted(
        {
            int(value)
            for value in report_options.get(
                "retirement_ages",
                [],
            )
        }
    )

    social_security_ages = sorted(
        {
            int(value)
            for value in report_options.get(
                "social_security_ages",
                [],
            )
        }
    )

    second_person_enabled = bool(
        getattr(
            sim_config,
            "second_person_enabled",
            False,
        )
        and wife is not None
    )

    baseline_retirement_age = (
        _household_event_age(
            husband,
            wife,
            second_person_enabled,
            "retire_age",
        )
    )

    baseline_ss_age = (
        _household_event_age(
            husband,
            wife,
            second_person_enabled,
            "ss_age",
        )
    )

    retirement_ages = sorted(
        set(
            retirement_ages
            + [
                int(
                    baseline_retirement_age
                )
            ]
        )
    )

    social_security_ages = sorted(
        set(
            social_security_ages
            + [
                int(
                    baseline_ss_age
                )
            ]
        )
    )

    baseline = {
        "household_retirement_age": int(
            baseline_retirement_age
        ),
        "household_social_security_age": int(
            baseline_ss_age
        ),
        "husband": {
            "current_age": int(
                husband.age
            ),
            "retirement_age": int(
                husband.retire_age
            ),
            "social_security_age": int(
                husband.ss_age
            ),
            "social_security_amount": float(
                husband.ss
            ),
        },
        "wife": None,
    }

    if second_person_enabled:
        baseline["wife"] = {
            "current_age": int(
                wife.age
            ),
            "retirement_age": int(
                wife.retire_age
            ),
            "social_security_age": int(
                wife.ss_age
            ),
            "social_security_amount": float(
                wife.ss
            ),
        }

    original_subplot_mode = (
        sim_config.subplot_mode
    )

    original_sim_type = (
        sim_config.sim_type
    )

    original_monte_carlo_mode = (
        sim_config.monte_carlo_mode
    )

    original_include_realestate = (
        sim_config.include_realestate
    )

    original_show_shortfall_rate = (
        sim_config.show_simulated_shortfall_rate
    )

    original_overlay_tax_impacts = (
        sim_config.overlay_tax_impacts
    )

    original_overlay_fund_expense_impacts = (
        sim_config.overlay_fund_expense_impacts
    )

    cases = []

    try:
        sim_config.subplot_mode = (
            "monte_carlo"
        )

        sim_config.sim_type = (
            "portfolio_sim"
        )

        sim_config.monte_carlo_mode = (
            "rollingHistoricalWindows"
        )

        sim_config.include_realestate = False

        sim_config.show_simulated_shortfall_rate = (
            False
        )

        sim_config.overlay_tax_impacts = False

        sim_config.overlay_fund_expense_impacts = (
            False
        )

        for retirement_age in retirement_ages:
            retirement_shift = (
                int(retirement_age)
                - int(
                    baseline_retirement_age
                )
            )

            for ss_age in social_security_ages:
                social_security_shift = (
                    int(ss_age)
                    - int(
                        baseline_ss_age
                    )
                )

                (
                    case_husband,
                    case_wife,
                ) = _build_case_persons(
                    husband,
                    wife,
                    second_person_enabled,
                    retirement_shift,
                    social_security_shift,
                )

                pipeline_result = run_pipeline(
                    husband_portfolio,
                    wife_portfolio,
                    case_husband,
                    case_wife,
                    expenses,
                    sim_config,
                    force_num_sims=None,
                )

                cases.append(
                    _build_case_result(
                        pipeline_result,
                        case_husband,
                        case_wife,
                        second_person_enabled,
                        retirement_age,
                        ss_age,
                        baseline_retirement_age,
                        baseline_ss_age,
                    )
                )

    finally:
        sim_config.subplot_mode = (
            original_subplot_mode
        )

        sim_config.sim_type = (
            original_sim_type
        )

        sim_config.monte_carlo_mode = (
            original_monte_carlo_mode
        )

        sim_config.include_realestate = (
            original_include_realestate
        )

        sim_config.show_simulated_shortfall_rate = (
            original_show_shortfall_rate
        )

        sim_config.overlay_tax_impacts = (
            original_overlay_tax_impacts
        )

        sim_config.overlay_fund_expense_impacts = (
            original_overlay_fund_expense_impacts
        )

    generated_timestamp = datetime.now()

    visible_report_id = (
        generated_timestamp.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    report_data = (
        RetirementSSComparisonReportData(
            report_options=report_options,
            report_metadata={
                "Report Title": (
                    "WARPSimLab Retirement & "
                    "Social Security Timing "
                    "Comparison Report"
                ),
                "Generated Timestamp": (
                    visible_report_id
                ),
                "Report ID": (
                    visible_report_id
                ),
                "Report Type": (
                    "retirement_ss_comparison_report"
                ),
                "Output Format": "HTML",
                "Projection Period": (
                    f"{int(sim_config.years_to_simulate)} years"
                ),
                "Report Basis": (
                    "Historical Windows"
                ),
            },
            baseline=baseline,
            retirement_ages=(
                retirement_ages
            ),
            social_security_ages=(
                social_security_ages
            ),
            comparison_cases=cases,
            warnings=[],
        )
    )

    return generate_retirement_ss_comparison_report(
        report_data
    )