# medicareEngine.py

from . import diagnosticEngine

IRMAA_THRESHOLDS_2026 = {
    "Single": (109000.0, 137000.0, 171000.0, 205000.0, 500000.0),
    "Other": (218000.0, 274000.0, 342000.0, 410000.0, 750000.0),
}

PART_B_STANDARD_MONTHLY_2026 = 202.90
PART_B_IRMAA_MULTIPLIERS = (0.0, 0.4, 1.0, 1.6, 2.2, 2.4)
PART_D_IRMAA_MONTHLY_2026 = (0.0, 14.50, 37.50, 60.40, 83.30, 91.00)

IRMAA_BASE_YEAR = 2026
IRMAA_TOP_THRESHOLD_FROZEN_THROUGH_YEAR = 2027

def initialize_medicare_engine_for_simulation(sim_config):
    """
    Initialize Medicare inflation factors for the active simulation path.

    Medicare annual costs are year-0-dollar inputs and follow the same
    inflation path as ordinary household expenses.

    Published Medicare and IRMAA constants are anchored to calendar year 2026.
    """
    if not hasattr(sim_config, "_expense_inflation_factors"):
        diagnosticEngine.raise_internal_error(
            "Expense engine not initialized before Medicare engine.",
            sim_config,
        )

    sim_config._medicare_inflation_factors = list(sim_config._expense_inflation_factors)

    base_multiplier = 1.0 + sim_config.inflation_rate + sim_config.inflation_delta
    years_from_base = sim_config.start_year - IRMAA_BASE_YEAR
    sim_config._medicare_2026_anchor_factor = base_multiplier ** years_from_base


def calculate_medicare_cost(person, current_age, year, sim_config):
    """
    Calculate one person's baseline Medicare cost for a simulation year.

    Medicare is modeled at annual resolution. Once current_age reaches
    medicare_start_age, the full inflation-adjusted annual cost applies.
    """
    if current_age < person.medicare_start_age:
        return 0.0

    annual_cost = max(0.0, float(person.medicare_annual_cost))
    return annual_cost * sim_config._medicare_inflation_factors[year]


def calculate_household_medicare_cost(
    husband, wife, curr_h_age, curr_w_age, year, second_person_enabled, husband_alive, wife_alive, sim_config
):
    medicare_husband = 0.0
    medicare_wife = 0.0

    if husband_alive:
        medicare_husband = calculate_medicare_cost(husband, curr_h_age, year, sim_config)

    if second_person_enabled and wife_alive:
        medicare_wife = calculate_medicare_cost(wife, curr_w_age, year, sim_config)

    return {
        "husband": medicare_husband,
        "wife": medicare_wife,
        "total": medicare_husband + medicare_wife,
    }


def _get_2026_constant_factor(year, sim_config):
    return sim_config._medicare_2026_anchor_factor * sim_config._medicare_inflation_factors[year]


def _get_top_threshold_factor(year, sim_config):
    calendar_year = sim_config.start_year + year

    if calendar_year <= IRMAA_TOP_THRESHOLD_FROZEN_THROUGH_YEAR:
        return 1.0

    start_year = sim_config.start_year

    if start_year >= IRMAA_TOP_THRESHOLD_FROZEN_THROUGH_YEAR:
        base_multiplier = 1.0 + sim_config.inflation_rate + sim_config.inflation_delta
        years_from_freeze = start_year - IRMAA_TOP_THRESHOLD_FROZEN_THROUGH_YEAR
        start_factor = base_multiplier ** years_from_freeze
        return start_factor * sim_config._medicare_inflation_factors[year]

    freeze_index = IRMAA_TOP_THRESHOLD_FROZEN_THROUGH_YEAR - start_year
    frozen_factor = sim_config._medicare_inflation_factors[freeze_index]

    if frozen_factor <= 0.0:
        diagnosticEngine.raise_internal_error(
            "Invalid Medicare inflation factor at IRMAA threshold freeze year.",
            sim_config,
            context={
                "year": year,
                "start_year": start_year,
                "freeze_index": freeze_index,
                "frozen_factor": frozen_factor,
            },
        )

    return sim_config._medicare_inflation_factors[year] / frozen_factor


def calculate_modeled_agi(income, traditional_withdrawal, taxable_hsa_withdrawal, roth_conversion):
    """
    Calculate planning-grade federal AGI from income components already modeled
    by WARPSimLab.

    This intentionally follows the simulator's existing federal tax treatment.
    The standard deduction is not part of AGI and is not applied here.
    """
    by_class = income["by_class"]

    modeled_agi = (
        by_class.get("work", 0.0) +
        by_class.get("pension", 0.0) +
        by_class.get("annuity", 0.0) +
        by_class.get("ss", 0.0) +
        by_class.get("rmd", 0.0) +
        by_class.get("bond_interest", 0.0) +
        by_class.get("cash_interest", 0.0) +
        by_class.get("qualified_equity_distributions", 0.0) +
        income.get("taxable_special_income", 0.0) +
        traditional_withdrawal +
        taxable_hsa_withdrawal +
        roth_conversion
    )

    return max(0.0, modeled_agi)


def calculate_irmaa_magi(income, traditional_withdrawal, taxable_hsa_withdrawal, roth_conversion):
    modeled_agi = calculate_modeled_agi(
        income, traditional_withdrawal, taxable_hsa_withdrawal, roth_conversion
    )

    tax_exempt_interest = max(0.0, float(income.get("tax_exempt_interest", 0.0)))
    return modeled_agi + tax_exempt_interest

def get_irmaa_lookback_magi(year, sim_index, results, sim_config):
    """
    Return the MAGI used for the current year's two-year IRMAA lookback.
    """
    if year == 1:
        value = sim_config.historical_magi.get("two_years_prior")
    elif year == 2:
        value = sim_config.historical_magi.get("one_year_prior")
    else:
        value = results["magi"][sim_index, year - 2]

    if value is None:
        return float("nan"), False

    value = float(value)
    if value != value:
        return float("nan"), False

    return max(0.0, value), True


def get_irmaa_lookback_filing_status_single(year, sim_index, results, sim_config):
    if year <= 2:
        return sim_config.tax_filing_status == "Single"

    return bool(results["filing_status_single"][sim_index, year - 2])


def _round_irmaa_threshold(value):
    return round(value / 1000.0) * 1000.0


def _get_irmaa_thresholds(year, filing_status_single, sim_config):
    filing_key = "Other"
    if filing_status_single:
        filing_key = "Single"

    threshold_factor = _get_2026_constant_factor(year, sim_config)
    base_thresholds = IRMAA_THRESHOLDS_2026[filing_key]
    thresholds = []

    for index, base_threshold in enumerate(base_thresholds):
        factor = threshold_factor

        if index == 4:
            factor = _get_top_threshold_factor(year, sim_config)

        thresholds.append(_round_irmaa_threshold(base_threshold * factor))

    return thresholds


def get_irmaa_level(magi, year, filing_status_single, sim_config):
    thresholds = _get_irmaa_thresholds(year, filing_status_single, sim_config)

    for level, upper_limit in enumerate(thresholds):
        if magi <= upper_limit:
            return level

    return 5


def calculate_person_irmaa(person, current_age, level, year, sim_config):
    if current_age < person.medicare_start_age:
        return 0.0

    inflation_factor = _get_2026_constant_factor(year, sim_config)
    part_b_standard = PART_B_STANDARD_MONTHLY_2026 * inflation_factor
    part_b_irmaa = part_b_standard * PART_B_IRMAA_MULTIPLIERS[level]
    part_d_irmaa = PART_D_IRMAA_MONTHLY_2026[level] * inflation_factor

    return 12.0 * (part_b_irmaa + part_d_irmaa)


def calculate_household_irmaa(
    husband, wife, curr_h_age, curr_w_age, year, second_person_enabled, husband_alive, wife_alive,
    lookback_magi, lookback_available, lookback_filing_status_single, sim_config
):
    irmaa_husband = 0.0
    irmaa_wife = 0.0

    if not sim_config.irmaa_enabled or not lookback_available:
        return {
            "husband": irmaa_husband,
            "wife": irmaa_wife,
            "total": 0.0,
            "lookback_magi": lookback_magi,
            "lookback_available": lookback_available,
        }

    level = get_irmaa_level(lookback_magi, year, lookback_filing_status_single, sim_config)

    if husband_alive:
        irmaa_husband = calculate_person_irmaa(husband, curr_h_age, level, year, sim_config)

    if second_person_enabled and wife_alive:
        irmaa_wife = calculate_person_irmaa(wife, curr_w_age, level, year, sim_config)

    return {
        "husband": irmaa_husband,
        "wife": irmaa_wife,
        "total": irmaa_husband + irmaa_wife,
        "lookback_magi": lookback_magi,
        "lookback_available": lookback_available,
    }

