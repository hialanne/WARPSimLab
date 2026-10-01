# incomeEngine.py

from . import diagnosticEngine

def _build_income_inflation_factors(sim_config):
    years = sim_config.years_to_simulate + 1
    factors = [1.0] * years

    historical_mode_active = (
        sim_config.results_mode == "risk_analysis"
        and sim_config.sim_type == "portfolio_sim"
        and getattr(sim_config, "risk_analysis_mode", "monte_carlo") == "historical_windows"
        and getattr(sim_config, "_active_historical_sim_index", None) is not None
        and getattr(sim_config, "_hist_inflation", None) is not None
    )

    if historical_mode_active:
        start_idx = int(
            sim_config._hist_window_start_indices[sim_config._active_historical_sim_index]
        )
        for y in range(1, years):
            annual_inflation = float(sim_config._hist_inflation[start_idx + (y - 1)]) + sim_config.inflation_delta
            factors[y] = factors[y - 1] * (1.0 + annual_inflation)
        return factors

    base_mult = 1.0 + sim_config.inflation_rate + sim_config.inflation_delta
    for y in range(1, years):
        factors[y] = factors[y - 1] * base_mult

    return factors


def _build_pension_factors(sim_config, inflation_adjustment_pct):
    years = sim_config.years_to_simulate + 1
    factors = [1.0] * years

    historical_mode_active = (
        sim_config.results_mode == "risk_analysis"
        and sim_config.sim_type == "portfolio_sim"
        and getattr(sim_config, "risk_analysis_mode", "monte_carlo") == "historical_windows"
        and getattr(sim_config, "_active_historical_sim_index", None) is not None
        and getattr(sim_config, "_hist_inflation", None) is not None
    )

    if historical_mode_active:
        start_idx = int(
            sim_config._hist_window_start_indices[sim_config._active_historical_sim_index]
        )
        for y in range(1, years):
            annual_inflation = float(sim_config._hist_inflation[start_idx + (y - 1)]) + sim_config.inflation_delta
            pension_step = 1.0 + (
                annual_inflation * inflation_adjustment_pct / 100.0
            )
            factors[y] = factors[y - 1] * pension_step
        return factors

    pension_mult = 1.0 + (
        (sim_config.inflation_rate + sim_config.inflation_delta) * inflation_adjustment_pct / 100.0
    )
    for y in range(1, years):
        factors[y] = factors[y - 1] * pension_mult

    return factors


def _build_special_income_factor(sim_config, adjustment_mode, adjustment_pct, start_year, year):
    start_factor = sim_config._income_inflation_factors[start_year]

    if year <= start_year or adjustment_mode == "none":
        return start_factor

    years_since_start = year - start_year

    if adjustment_mode == "fixed":
        return start_factor * (1.0 + adjustment_pct / 100.0) ** years_since_start

    if adjustment_mode != "inflation":
        raise ValueError(f"Unsupported special income adjustment mode: {adjustment_mode!r}")

    historical_mode_active = (
        sim_config.results_mode == "risk_analysis"
        and sim_config.sim_type == "portfolio_sim"
        and getattr(sim_config, "risk_analysis_mode", "monte_carlo") == "historical_windows"
        and getattr(sim_config, "_active_historical_sim_index", None) is not None
        and getattr(sim_config, "_hist_inflation", None) is not None
    )

    if historical_mode_active:
        hist_start_idx = int(sim_config._hist_window_start_indices[sim_config._active_historical_sim_index])
        factor = start_factor

        for y in range(start_year + 1, year + 1):
            annual_inflation = float(sim_config._hist_inflation[hist_start_idx + (y - 1)]) + sim_config.inflation_delta
            factor *= 1.0 + annual_inflation * adjustment_pct / 100.0

        return factor

    annual_step = (sim_config.inflation_rate + sim_config.inflation_delta) * adjustment_pct / 100.0
    return start_factor * (1.0 + annual_step) ** years_since_start


def _calculate_special_income_for_year(
    curr_husband_age,
    curr_wife_age,
    year,
    husband_alive,
    wife_alive,
    sim_config,
):
    """
    Calculate special income streams for the current simulation year.

    Special income:
      - is age-based by owner
      - stops when the owner is deceased
      - uses an amount entered in today's dollars
      - is inflated to nominal dollars through the year the stream begins
      - after starting, may follow inflation, a fixed annual increase, or no further increase
      - may be taxable or non-taxable
      - is not payroll wage income
    """
    taxable_special_income = 0.0
    non_taxable_special_income = 0.0
    husband_special_income = 0.0
    wife_special_income = 0.0

    special_income_streams = getattr(sim_config, "special_income_streams", [])

    for stream in special_income_streams:
        if not stream.get("enabled", True):
            continue

        owner = stream.get("owner", "husband")

        if owner == "wife":
            if not sim_config.second_person_enabled or not wife_alive:
                continue
            owner_age = curr_wife_age
        else:
            if not husband_alive:
                continue
            owner_age = curr_husband_age

        start_age = int(stream.get("start_age", 0))
        end_age = int(stream.get("end_age", 120))

        if owner_age < start_age or owner_age > end_age:
            continue

        amount = float(stream.get("amount", 0.0))
        if amount <= 0.0:
            continue

        adjustment_mode = stream.get("adjustment_mode", "inflation")
        adjustment_pct = float(stream.get("adjustment_pct", stream.get("inflation_adjustment_pct", 100.0)))

        start_year = max(0, year - (owner_age - start_age))
        special_income_factor = _build_special_income_factor(
            sim_config, adjustment_mode, adjustment_pct, start_year, year
        )

        adjusted_amount = amount * special_income_factor

        if stream.get("taxable", True):
            taxable_special_income += adjusted_amount
        else:
            non_taxable_special_income += adjusted_amount

        if owner == "wife":
            wife_special_income += adjusted_amount
        else:
            husband_special_income += adjusted_amount

    return {
        "taxable": taxable_special_income,
        "non_taxable": non_taxable_special_income,
        "husband": husband_special_income,
        "wife": wife_special_income,
        "total": taxable_special_income + non_taxable_special_income,
    }


def _ensure_income_engine_initialized(husband, wife, sim_config):
    if not hasattr(sim_config, "_income_inflation_factors"):
        initialize_income_engine_for_simulation(husband, wife, sim_config)

    if not hasattr(husband, "_ss_start_age"):
        husband._ss_start_age = husband.ss_age if husband.ss_age <= 70 else 70

    if sim_config.second_person_enabled and wife is not None and not hasattr(wife, "_ss_start_age"):
        wife._ss_start_age = wife.ss_age if wife.ss_age <= 70 else 70


def initialize_income_engine_for_simulation(husband, wife, sim_config):
    sim_config._income_inflation_factors = _build_income_inflation_factors(sim_config)

    sim_config._husband_pension_factors = _build_pension_factors(
        sim_config,
        husband.pension_inflation_adjustment_pct,
    )

    if sim_config.second_person_enabled:
        sim_config._wife_pension_factors = _build_pension_factors(
            sim_config,
            wife.pension_inflation_adjustment_pct,
        )
    else:
        sim_config._wife_pension_factors = None

    husband._ss_start_age = husband.ss_age if husband.ss_age <= 70 else 70

    if sim_config.second_person_enabled:
        wife._ss_start_age = wife.ss_age if wife.ss_age <= 70 else 70


def _calculate_social_security_for_year(
    husband,
    wife,
    curr_husband_age,
    curr_wife_age,
    year,
    husband_alive,
    wife_alive,
    sim_config,
):
    income_factor = sim_config._income_inflation_factors[year]

    husband_ss = 0.0
    wife_ss = 0.0

    if not sim_config.second_person_enabled:
        if husband_alive and curr_husband_age >= husband._ss_start_age:
            husband_ss = husband.ss * income_factor
        return husband_ss, wife_ss

    if husband_alive and wife_alive:
        if curr_husband_age >= husband._ss_start_age:
            husband_ss = husband.ss * income_factor

        if curr_wife_age >= wife._ss_start_age:
            wife_ss = wife.ss * income_factor

        return husband_ss, wife_ss

    survivor_benefit = max(husband.ss, wife.ss) * income_factor

    if husband_alive and curr_husband_age >= husband._ss_start_age:
        husband_ss = survivor_benefit

    if wife_alive and curr_wife_age >= wife._ss_start_age:
        wife_ss = survivor_benefit

    return husband_ss, wife_ss


def calculate_income_breakdown(
    husband,
    wife,
    curr_husband_age,
    curr_wife_age,
    rmd_h,
    rmd_w,
    year,
    husband_alive,
    wife_alive,
    sim_config,
):
    """
    Returns structured income data:
      - total household income
      - income by class
      - income by person
    """
    _ensure_income_engine_initialized(husband, wife, sim_config)

    second_person_enabled = sim_config.second_person_enabled

    if not second_person_enabled:
        rmd_w = 0.0
        wife_alive = False

    income_factor = sim_config._income_inflation_factors[year]
    h_pension_factor = sim_config._husband_pension_factors[year]

    work = 0.0
    pension = 0.0
    annuity = 0.0
    ss = 0.0
    rmd = rmd_h + rmd_w

    withdrawal = 0.0
    bond_interest = 0.0
    cash_interest = 0.0
    qualified_equity_distributions = 0.0

    husband_income = rmd_h
    wife_income = rmd_w

    husband_work = 0.0
    wife_work = 0.0

    if husband_alive:
        if curr_husband_age < husband.retire_age:
            husband_work = husband.income * income_factor
            work += husband_work
            husband_income += husband_work

        if curr_husband_age >= husband.pension_age:
            amt = husband.pension * h_pension_factor
            pension += amt
            husband_income += amt

        if curr_husband_age >= husband.annuity_age:
            annuity += husband.annuity
            husband_income += husband.annuity

    if second_person_enabled and wife_alive:
        w_pension_factor = sim_config._wife_pension_factors[year]

        if curr_wife_age < wife.retire_age:
            wife_work = wife.income * income_factor
            work += wife_work
            wife_income += wife_work

        if curr_wife_age >= wife.pension_age:
            amt = wife.pension * w_pension_factor
            pension += amt
            wife_income += amt

        if curr_wife_age >= wife.annuity_age:
            annuity += wife.annuity
            wife_income += wife.annuity

    husband_ss, wife_ss = _calculate_social_security_for_year(
        husband,
        wife,
        curr_husband_age,
        curr_wife_age,
        year,
        husband_alive,
        wife_alive,
        sim_config,
    )

    ss = husband_ss + wife_ss
    husband_income += husband_ss
    wife_income += wife_ss

    special_income = _calculate_special_income_for_year(
        curr_husband_age,
        curr_wife_age,
        year,
        husband_alive,
        wife_alive,
        sim_config,
    )

    special_income_amt = special_income["total"]
    non_taxable_income = special_income["non_taxable"]

    husband_income += special_income["husband"]
    wife_income += special_income["wife"]

    total = work + pension + annuity + ss + rmd + special_income_amt

    return {
        "total": total,
        "taxable_special_income": special_income["taxable"],
        "non_taxable_special_income": special_income["non_taxable"],
        "by_class": {
            "work": work,
            "pension": pension,
            "annuity": annuity,
            "ss": ss,
            "rmd": rmd,
            "withdrawal": withdrawal,
            "tax_funding_withdrawal": 0.0,
            "bond_interest": bond_interest,
            "cash_interest": cash_interest,
            "qualified_equity_distributions": qualified_equity_distributions,
            "special_income": special_income_amt,
        },
        "non_taxable_income": non_taxable_income,
        "by_person": {
            "husband": husband_income,
            "wife": wife_income,
        },
        "work_by_person": {
            "husband": husband_work,
            "wife": wife_work,
        },
    }


def calculate_social_security(husband, wife, year, sim_config):
    """
    Calculate husband's and wife's Social Security with inflation adjustment.
    """
    _ensure_income_engine_initialized(husband, wife, sim_config)

    second_person_enabled = sim_config.second_person_enabled

    # Husband SS
    curr_husband_age = husband.age + year
    husband_ss_infl = 0.0
    if curr_husband_age >= husband._ss_start_age:
        husband_ss_infl = husband.ss * sim_config._income_inflation_factors[year]

    # Wife SS
    wife_ss_infl = 0.0
    if second_person_enabled:
        curr_wife_age = wife.age + year
        if curr_wife_age >= wife._ss_start_age:
            wife_ss_infl = wife.ss * sim_config._income_inflation_factors[year]

    return husband_ss_infl, wife_ss_infl


def calculate_pre_tax_401k_contributions(person, current_age, year, alive, sim_config):
    """
    Returns
    -------
    tuple
        (employee_contribution, employer_contribution)
    """

    if not hasattr(sim_config, "_income_inflation_factors"):
        diagnosticEngine.raise_internal_error("Income engine not initialized before 401(k) contribution calculation.", sim_config,
                                              context={"year": year, "current_age": current_age})

    if not alive:
        return 0.0, 0.0

    if current_age >= person.retire_age:
        return 0.0, 0.0

    infl_factor = sim_config._income_inflation_factors[year]

    current_work_income = person.income * infl_factor
    if current_work_income < 0.0:
        current_work_income = 0.0

    requested_employee = person.annual_401k_contribution * infl_factor
    if requested_employee < 0.0:
        requested_employee = 0.0

    requested_employer = person.annual_employer_match * infl_factor
    if requested_employer < 0.0:
        requested_employer = 0.0

    if requested_employee <= current_work_income:
        employee_contribution = requested_employee
    else:
        employee_contribution = current_work_income

    employer_contribution = requested_employer if employee_contribution > 0.0 else 0.0

    return employee_contribution, employer_contribution


def apply_employee_401k_to_income(gross_income, employee_contribution, person_key):
    """
    Mutates gross_income to reflect employee 401(k) contribution.
    Employer match is NOT handled here.
    """
    if employee_contribution <= 0:
        return

    gross_income["total"] -= employee_contribution
    gross_income["by_person"][person_key] -= employee_contribution
    gross_income["by_class"]["work"] -= employee_contribution