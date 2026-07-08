# incomeEngine.py


def _build_income_inflation_factors(sim_config):
    years = sim_config.years_to_simulate + 1
    factors = [1.0] * years

    historical_mode_active = (
        sim_config.subplot_mode == "monte_carlo"
        and sim_config.sim_type == "portfolio_sim"
        and getattr(sim_config, "monte_carlo_mode", "pathBasedAnnualSampling") == "rollingHistoricalWindows"
        and getattr(sim_config, "_active_historical_sim_index", None) is not None
        and getattr(sim_config, "_hist_inflation", None) is not None
    )

    if historical_mode_active:
        start_idx = int(
            sim_config._hist_window_start_indices[sim_config._active_historical_sim_index]
        )
        for y in range(1, years):
            annual_inflation = float(sim_config._hist_inflation[start_idx + (y - 1)])
            factors[y] = factors[y - 1] * (1.0 + annual_inflation)
        return factors

    base_mult = 1.0 + sim_config.inflation_rate
    for y in range(1, years):
        factors[y] = factors[y - 1] * base_mult

    return factors


def _build_pension_factors(sim_config, inflation_adjustment_pct):
    years = sim_config.years_to_simulate + 1
    factors = [1.0] * years

    historical_mode_active = (
        sim_config.subplot_mode == "monte_carlo"
        and sim_config.sim_type == "portfolio_sim"
        and getattr(sim_config, "monte_carlo_mode", "pathBasedAnnualSampling") == "rollingHistoricalWindows"
        and getattr(sim_config, "_active_historical_sim_index", None) is not None
        and getattr(sim_config, "_hist_inflation", None) is not None
    )

    if historical_mode_active:
        start_idx = int(
            sim_config._hist_window_start_indices[sim_config._active_historical_sim_index]
        )
        for y in range(1, years):
            annual_inflation = float(sim_config._hist_inflation[start_idx + (y - 1)])
            pension_step = 1.0 + (
                annual_inflation * inflation_adjustment_pct / 100.0
            )
            factors[y] = factors[y - 1] * pension_step
        return factors

    pension_mult = 1.0 + (
        sim_config.inflation_rate * inflation_adjustment_pct / 100.0
    )
    for y in range(1, years):
        factors[y] = factors[y - 1] * pension_mult

    return factors


def _calculate_special_income_for_year(curr_husband_age, curr_wife_age, year, sim_config):
    """
    Calculate special income streams for the current simulation year.

    Special income:
      - is age-based by owner
      - may be taxable or non-taxable
      - may be inflation-adjusted by a percentage of inflation
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

        if owner == "wife" and not sim_config.second_person_enabled:
            continue

        owner_age = curr_wife_age if owner == "wife" else curr_husband_age

        start_age = int(stream.get("start_age", 0))
        end_age = int(stream.get("end_age", 120))

        if owner_age < start_age or owner_age > end_age:
            continue

        amount = float(stream.get("amount", 0.0))
        if amount <= 0.0:
            continue

        inflation_adjustment_pct = float(
            stream.get("inflation_adjustment_pct", 100.0)
        )

        special_income_factor = _build_pension_factors(
            sim_config,
            inflation_adjustment_pct,
        )[year]

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


def calculate_income(husband, wife, curr_husband_age, curr_wife_age,
                     rmd_h, rmd_w, year, sim_config):
    """
    Calculate total income for husband and (optionally) wife in a given year.
    Includes work income, pension, annuity, Social Security, and RMDs.
    """
    _ensure_income_engine_initialized(husband, wife, sim_config)

    second_person_enabled = sim_config.second_person_enabled

    # Husband's income
    income_factor = sim_config._income_inflation_factors[year]
    pension_factor = sim_config._husband_pension_factors[year]

    husband_income = rmd_h

    if curr_husband_age < husband.retire_age:
        husband_income += husband.income * income_factor

    if curr_husband_age >= husband._ss_start_age:
        husband_income += husband.ss * income_factor

    if curr_husband_age >= husband.pension_age:
        husband_income += husband.pension * pension_factor

    if curr_husband_age >= husband.annuity_age:
        husband_income += husband.annuity

    # Wife's income (if applicable)
    wife_income = 0.0
    if second_person_enabled:
        income_factor = sim_config._income_inflation_factors[year]
        pension_factor = sim_config._wife_pension_factors[year]

        wife_income = rmd_w

        if curr_wife_age < wife.retire_age:
            wife_income += wife.income * income_factor

        if curr_wife_age >= wife._ss_start_age:
            wife_income += wife.ss * income_factor

        if curr_wife_age >= wife.pension_age:
            wife_income += wife.pension * pension_factor

        if curr_wife_age >= wife.annuity_age:
            wife_income += wife.annuity

    special_income = _calculate_special_income_for_year(
        curr_husband_age,
        curr_wife_age,
        year,
        sim_config,
    )

    return husband_income + wife_income + special_income["total"]


def calculate_income_breakdown(husband, wife,
                               curr_husband_age, curr_wife_age,
                               rmd_h, rmd_w,
                               year, sim_config):
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

    income_factor = sim_config._income_inflation_factors[year]
    h_pension_factor = sim_config._husband_pension_factors[year]

    h_retire_age = husband.retire_age
    h_income = husband.income
    h_ss_start_age = husband._ss_start_age

    h_ss = husband.ss
    h_pension_age = husband.pension_age
    h_pension = husband.pension
    h_annuity_age = husband.annuity_age
    h_annuity = husband.annuity

    work = 0.0
    pension = 0.0
    annuity = 0.0
    ss = 0.0
    rmd = rmd_h + rmd_w

    withdrawal = 0.0
    bond_interest = 0.0
    cash_interest = 0.0
    qualified_dividends = 0.0
    special_income_amt = 0.0
    non_taxable_income = 0.0

    husband_income = rmd_h
    wife_income = rmd_w

    # Husband
    if curr_husband_age < h_retire_age:
        amt = h_income * income_factor
        work += amt
        husband_income += amt

    if curr_husband_age >= h_ss_start_age:
        amt = h_ss * income_factor
        ss += amt
        husband_income += amt

    if curr_husband_age >= h_pension_age:
        amt = h_pension * h_pension_factor
        pension += amt
        husband_income += amt

    if curr_husband_age >= h_annuity_age:
        amt = h_annuity
        annuity += amt
        husband_income += amt

    # Wife
    if second_person_enabled:
        w_pension_factor = sim_config._wife_pension_factors[year]

        w_retire_age = wife.retire_age
        w_income = wife.income
        w_ss_start_age = wife._ss_start_age

        w_ss = wife.ss
        w_pension_age = wife.pension_age
        w_pension = wife.pension
        w_annuity_age = wife.annuity_age
        w_annuity = wife.annuity

        if curr_wife_age < w_retire_age:
            amt = w_income * income_factor
            work += amt
            wife_income += amt

        if curr_wife_age >= w_ss_start_age:
            amt = w_ss * income_factor
            ss += amt
            wife_income += amt

        if curr_wife_age >= w_pension_age:
            amt = w_pension * w_pension_factor
            pension += amt
            wife_income += amt

        if curr_wife_age >= w_annuity_age:
            amt = w_annuity
            annuity += amt
            wife_income += amt

    special_income = _calculate_special_income_for_year(
        curr_husband_age,
        curr_wife_age,
        year,
        sim_config,
    )

    special_income_amt = special_income["total"]
    non_taxable_income = special_income["non_taxable"]

    husband_income += special_income["husband"]
    wife_income += special_income["wife"]

    total = work + pension + annuity + ss + rmd + special_income_amt

    return {
        "total": total,
        "by_class": {
            "work": work,
            "pension": pension,
            "annuity": annuity,
            "ss": ss,
            "rmd": rmd,
            "withdrawal": withdrawal,
            "bond_interest": bond_interest,
            "cash_interest": cash_interest,
            "qualified_dividends": qualified_dividends,
            "special_income": special_income_amt,
        },
        
        "non_taxable_income": non_taxable_income,

        "by_person": {
            "husband": husband_income,
            "wife": wife_income,
        },

        "work_by_person": {
            "husband": (
                h_income * income_factor
                if curr_husband_age < h_retire_age
                else 0.0
            ),
            "wife": (
                w_income * income_factor
                if second_person_enabled and curr_wife_age < w_retire_age
                else 0.0
            ),
        }
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


def calculate_pre_tax_401k_contributions(person, current_age, year, sim_config):
    """
    Returns
    -------
    tuple
        (employee_contribution, employer_contribution)
    """
    if not hasattr(sim_config, "_income_inflation_factors"):
        raise RuntimeError(
            "Income engine not initialized before 401(k) contribution calculation."
        )

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