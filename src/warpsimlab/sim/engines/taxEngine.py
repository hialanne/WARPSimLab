# taxEngine.py



# --------------------------------------
# Payroll tax rules - employee side only
# --------------------------------------

SOCIAL_SECURITY_EMPLOYEE_RATE = 0.062
SOCIAL_SECURITY_WAGE_BASE_2026 = 184_500.0

MEDICARE_EMPLOYEE_RATE = 0.0145
ADDITIONAL_MEDICARE_RATE = 0.009

ADDITIONAL_MEDICARE_SINGLE_THRESHOLD = 200_000.0
ADDITIONAL_MEDICARE_MFJ_THRESHOLD = 250_000.0


def calculate_employee_payroll_tax_split(
    husband_wages,
    wife_wages,
    year_cache,
    sim_config
):
    """
    Calculate employee-side payroll taxes.

    Payroll taxes are applied only to gross work wages:
      - Social Security: 6.2% up to the wage base, per person
      - Medicare: 1.45% on all wages, per person
      - Additional Medicare: 0.9% above filing-status threshold

    This intentionally excludes Social Security benefits, pensions,
    annuities, RMDs, retirement withdrawals, interest, dividends,
    and capital gains.

    Returns
    -------
    tuple
        (social_security_tax, medicare_tax, additional_medicare_tax, total_payroll_tax)
    """

    if not getattr(sim_config, "calculate_payroll_taxes", True):
        return 0.0, 0.0, 0.0, 0.0

    husband_wages = max(0.0, float(husband_wages))
    wife_wages = max(0.0, float(wife_wages))

    wage_base = year_cache["social_security_wage_base"]

    husband_social_security_tax = (
        min(husband_wages, wage_base) * SOCIAL_SECURITY_EMPLOYEE_RATE
    )
    wife_social_security_tax = (
        min(wife_wages, wage_base) * SOCIAL_SECURITY_EMPLOYEE_RATE
    )

    social_security_tax = husband_social_security_tax + wife_social_security_tax

    medicare_tax = (
        husband_wages + wife_wages
    ) * MEDICARE_EMPLOYEE_RATE

    if sim_config.tax_filing_status == "Single":
        additional_medicare_threshold = ADDITIONAL_MEDICARE_SINGLE_THRESHOLD
    else:
        additional_medicare_threshold = ADDITIONAL_MEDICARE_MFJ_THRESHOLD

    household_wages = husband_wages + wife_wages

    additional_medicare_tax = max(
        0.0,
        household_wages - additional_medicare_threshold
    ) * ADDITIONAL_MEDICARE_RATE

    total_payroll_tax = (
        social_security_tax
        + medicare_tax
        + additional_medicare_tax
    )

    return (
        social_security_tax,
        medicare_tax,
        additional_medicare_tax,
        total_payroll_tax,
    )


def calculate_total_income_tax_split(ordinary_income, qualified_dividends, year_cache, sim_config):
    """
    Calculates total tax using split treatment and returns component detail.

    Returns
    -------
    tuple
        (federal_ordinary_tax, federal_qualified_dividend_tax, state_income_tax, total_tax)
    """

    if ordinary_income < 0 or qualified_dividends < 0:
        raise RuntimeError(
            f"Tax engine received negative income inputs: "
            f"ordinary_income={ordinary_income}, qualified_dividends={qualified_dividends}"
        )

    federal_ordinary_tax = 0.0
    federal_qualified_dividend_tax = 0.0
    state_income_tax = 0.0
    federal_marginal_rate = 0.0

    if sim_config.calculate_income_taxes:
        federal_ordinary_tax, federal_marginal_rate = calculate_us_federal_income_tax(
            ordinary_income, year_cache
        )
        federal_qualified_dividend_tax = calculate_us_federal_qualified_dividend_tax(
            ordinary_income, qualified_dividends, year_cache
        )

    if sim_config.calculate_state_taxes:
        state_taxable_income = ordinary_income + qualified_dividends
        state_income_tax = calculate_state_income_tax(
            state_taxable_income, year_cache, sim_config
        )

    total_tax = (
        federal_ordinary_tax
        + federal_qualified_dividend_tax
        + state_income_tax
    )

    return (
        federal_ordinary_tax,
        federal_qualified_dividend_tax,
        state_income_tax,
        total_tax,
        federal_marginal_rate,
    )

from math import inf


FEDERAL_ORDINARY_TAX_TABLES_2026 = {
    "Single": (
        16100,  # standard deduction
        (
            (12400, 0.10),
            (50400, 0.12),
            (105700, 0.22),
            (201775, 0.24),
            (256225, 0.32),
            (640600, 0.35),
            (inf, 0.37),
        ),
    ),
    "Other": (
        32200,  # standard deduction
        (
            (24800, 0.10),
            (100800, 0.12),
            (211400, 0.22),
            (403550, 0.24),
            (512450, 0.32),
            (768700, 0.35),
            (inf, 0.37),
        ),
    ),
}

# NOTE - calculate_us_federal_qualified_dividend_tax() hard codes having 3 brackets of 0, 0.15 and 0.20.  
#  The bands come from the tables below.

FEDERAL_QUALIFIED_DIVIDEND_TAX_TABLES_2026 = {
    "Single": (
        16100,  # standard deduction
        (
            (48350, 0.00),
            (533400, 0.15),
            (inf, 0.20),
        ),
    ),
    "Other": (
        32200,  # standard deduction
        (
            (96700, 0.00),
            (600050, 0.15),
            (inf, 0.20),
        ),
    ),
}


def _inflate_brackets(brackets_base, inflation_factor):
    return tuple(
        (upper if upper == inf else upper * inflation_factor, rate)
        for upper, rate in brackets_base
    )


def initialize_tax_engine_for_simulation(sim_config):
    filing_key = "Single" if sim_config.tax_filing_status == "Single" else "Other"

    ordinary_standard_deduction_base, ordinary_brackets_base = (
        FEDERAL_ORDINARY_TAX_TABLES_2026[filing_key]
    )
    qd_standard_deduction_base, qd_brackets_base = (
        FEDERAL_QUALIFIED_DIVIDEND_TAX_TABLES_2026[filing_key]
    )

    sim_config._tax_filing_key = filing_key
    sim_config._federal_standard_deduction_base = ordinary_standard_deduction_base
    sim_config._federal_ordinary_brackets_base = ordinary_brackets_base
    sim_config._federal_qd_brackets_base = qd_brackets_base

    state = getattr(sim_config, "state_of_residence", None)
    rules = STATE_TAX_RULES.get(state) if state else None

    if not rules or rules["type"] == "none":
        sim_config._state_tax_enabled = False
        sim_config._state_tax_type = "none"
        sim_config._state_tax_rate = 0.0
        sim_config._state_tax_brackets_base = None
    elif rules["type"] == "flat":
        sim_config._state_tax_enabled = True
        sim_config._state_tax_type = "flat"
        sim_config._state_tax_rate = rules["rate"]
        sim_config._state_tax_brackets_base = None
    else:
        sim_config._state_tax_enabled = True
        sim_config._state_tax_type = "progressive"
        sim_config._state_tax_rate = 0.0
        sim_config._state_tax_brackets_base = rules["brackets"][filing_key]

    years = sim_config.years_to_simulate + 1

    historical_mode_active = (
        sim_config.subplot_mode == "monte_carlo"
        and sim_config.sim_type == "portfolio_sim"
        and getattr(sim_config, "monte_carlo_mode", "pathBasedAnnualSampling") == "rollingHistoricalWindows"
        and getattr(sim_config, "_active_historical_sim_index", None) is not None
        and getattr(sim_config, "_hist_inflation", None) is not None
    )

    inflation_factors = [1.0] * years

    if historical_mode_active:
        start_idx = int(
            sim_config._hist_window_start_indices[sim_config._active_historical_sim_index]
        )
        for year in range(1, years):
            annual_inflation = float(sim_config._hist_inflation[start_idx + (year - 1)])
            inflation_factors[year] = inflation_factors[year - 1] * (1.0 + annual_inflation)
    else:
        multiplier = 1.0 + sim_config.inflation_rate
        for year in range(1, years):
            inflation_factors[year] = inflation_factors[year - 1] * multiplier

    sim_config._inflation_factors = inflation_factors
    sim_config._tax_year_cache = [None] * years


def prepare_tax_year_cache(year, sim_config):
    year_cache = sim_config._tax_year_cache[year]
    if year_cache is not None:
        return year_cache

    inflation_factor = sim_config._inflation_factors[year]

    ordinary_standard_deduction = (
        sim_config._federal_standard_deduction_base * inflation_factor
    )

    ordinary_brackets = _inflate_brackets(
        sim_config._federal_ordinary_brackets_base,
        inflation_factor,
    )

    qd_brackets = _inflate_brackets(
        sim_config._federal_qd_brackets_base,
        inflation_factor,
    )

    state_brackets = None
    if sim_config._state_tax_type == "progressive":
        state_brackets = _inflate_brackets(
            sim_config._state_tax_brackets_base,
            inflation_factor,
        )

    year_cache = {
        "ordinary_standard_deduction": ordinary_standard_deduction,
        "ordinary_brackets": ordinary_brackets,
        "qd_brackets": qd_brackets,
        "state_brackets": state_brackets,
        "social_security_wage_base": SOCIAL_SECURITY_WAGE_BASE_2026 * inflation_factor,
    }

    sim_config._tax_year_cache[year] = year_cache
    return year_cache


def calculate_us_federal_income_tax(total_income, year_cache):
    """
    Calculates U.S. federal ordinary income tax and marginal rate using cached,
    inflation-adjusted tax data for tax year 2026.

    Returns
    -------
    tuple
        (tax, marginal_rate)
    """

    taxable_income = total_income - year_cache["ordinary_standard_deduction"]
    if taxable_income <= 0.0:
        return 0.0, 0.0

    tax = 0.0
    lower_limit = 0.0
    marginal_rate = 0.0

    for upper_limit, rate in year_cache["ordinary_brackets"]:
        if taxable_income <= lower_limit:
            break

        if taxable_income <= upper_limit:
            taxable_slice = taxable_income - lower_limit
            tax += taxable_slice * rate
            marginal_rate = rate
            return tax, marginal_rate
        else:
            taxable_slice = upper_limit - lower_limit
            tax += taxable_slice * rate
            lower_limit = upper_limit

    # defensive fallback
    return tax, marginal_rate


def calculate_us_federal_qualified_dividend_tax(ordinary_income, qualified_dividends, year_cache):
    """
    Calculates federal tax on qualified dividends using cached,
    inflation-adjusted LTCG / qualified dividend thresholds.

    Assumes the qualified dividend table has exactly 3 brackets:
      - 0%
      - 15%
      - 20%
    """
    if qualified_dividends <= 0.0:
        return 0.0

    taxable_ordinary_income = ordinary_income - year_cache["ordinary_standard_deduction"]
    if taxable_ordinary_income < 0.0:
        taxable_ordinary_income = 0.0

    qd_brackets = year_cache["qd_brackets"]
    upper_0 = qd_brackets[0][0]
    upper_1 = qd_brackets[1][0]

    # Portion of qualified dividends that fits in the 0% band
    zero_band_room = upper_0 - taxable_ordinary_income
    if zero_band_room <= 0.0:
        zero_taxed = 0.0
    elif qualified_dividends <= zero_band_room:
        zero_taxed = qualified_dividends
    else:
        zero_taxed = zero_band_room

    remaining_after_zero = qualified_dividends - zero_taxed
    if remaining_after_zero <= 0.0:
        return 0.0

    # Portion that fits in the 15% band
    start_of_fifteen_band = taxable_ordinary_income + zero_taxed
    fifteen_band_room = upper_1 - start_of_fifteen_band
    if fifteen_band_room <= 0.0:
        fifteen_taxed = 0.0
    elif remaining_after_zero <= fifteen_band_room:
        fifteen_taxed = remaining_after_zero
    else:
        fifteen_taxed = fifteen_band_room

    twenty_taxed = remaining_after_zero - fifteen_taxed

    return fifteen_taxed * 0.15 + twenty_taxed * 0.20


def allocate_tax_proportionally(total_tax, by_person_income):
    """
    Linearly allocate a household tax bill across people based on
    their share of gross income.

    Args:
        total_tax (float)
        by_person_income (dict): {"husband": x, "wife": y}

    Returns:
        dict: {"husband": h_tax, "wife": w_tax}
    """
    total_income = sum(by_person_income.values())

    if total_income <= 0.0 or total_tax <= 0.0:
        return {k: 0.0 for k in by_person_income}

    return {
        k: total_tax * (v / total_income)
        for k, v in by_person_income.items()
    }


def allocate_tax_proportionally_couple(total_tax, husband_income, wife_income):
    """
    Allocate household tax across husband and wife based on income share.

    Returns
    -------
    tuple
        (husband_tax, wife_tax)
    """
    total_income = husband_income + wife_income

    if total_income <= 0.0 or total_tax <= 0.0:
        return 0.0, 0.0

    husband_tax = total_tax * (husband_income / total_income)
    wife_tax = total_tax - husband_tax
    return husband_tax, wife_tax


# --------------------------------------
# State income tax rules (planning-grade)
# --------------------------------------

STATE_TAX_RULES = {

    # -------------------------
    # No income tax
    # -------------------------
    "AK": {"type": "none"},
    "FL": {"type": "none"},
    "NV": {"type": "none"},
    "SD": {"type": "none"},
    "TN": {"type": "none"},
    "TX": {"type": "none"},
    "WA": {"type": "none"},
    "WY": {"type": "none"},

    # -------------------------
    # Flat tax states
    # -------------------------
    "AZ": {"type": "flat", "rate": 0.025},
    "CO": {"type": "flat", "rate": 0.044},
    "GA": {"type": "flat", "rate": 0.0549},
    "IL": {"type": "flat", "rate": 0.0495},
    "IN": {"type": "flat", "rate": 0.0323},
    "KY": {"type": "flat", "rate": 0.045},
    "MA": {"type": "flat", "rate": 0.050},
    "MI": {"type": "flat", "rate": 0.0425},
    "NC": {"type": "flat", "rate": 0.0475},
    "PA": {"type": "flat", "rate": 0.0307},
    "UT": {"type": "flat", "rate": 0.0485},

    # -------------------------
    # Progressive tax states
    # -------------------------
    "AL": {
        "type": "progressive",
        "brackets": {
            "Single": [(500, 0.02), (3000, 0.04), (float("inf"), 0.05)],
            "Other":  [(1000, 0.02), (6000, 0.04), (float("inf"), 0.05)],
        },
    },

    "AR": {
        "type": "progressive",
        "brackets": {
            "Single": [(4300, 0.02), (8400, 0.04), (float("inf"), 0.055)],
            "Other":  [(4300, 0.02), (8400, 0.04), (float("inf"), 0.055)],
        },
    },

    "CA": {
        "type": "progressive",
        "brackets": {
            "Single": [
                (10099, 0.01), (23942, 0.02), (37788, 0.04),
                (52455, 0.06), (66295, 0.08), (338639, 0.093),
                (float("inf"), 0.123),
            ],
            "Other": [
                (20198, 0.01), (47884, 0.02), (75576, 0.04),
                (104910, 0.06), (132590, 0.08), (677278, 0.093),
                (float("inf"), 0.123),
            ],
        },
    },

    "CT": {
        "type": "progressive",
        "brackets": {
            "Single": [(10000, 0.03), (50000, 0.05), (100000, 0.055), (float("inf"), 0.0699)],
            "Other":  [(20000, 0.03), (100000, 0.05), (200000, 0.055), (float("inf"), 0.0699)],
        },
    },

    "DC": {
        "type": "progressive",
        "brackets": {
            "Single": [(10000, 0.04), (40000, 0.06), (60000, 0.065), (250000, 0.085), (float("inf"), 0.0975)],
            "Other":  [(20000, 0.04), (80000, 0.06), (120000, 0.065), (250000, 0.085), (float("inf"), 0.0975)],
        },
    },

    "DE": {
        "type": "progressive",
        "brackets": {
            "Single": [(2000, 0.022), (5000, 0.039), (10000, 0.048), (20000, 0.052), (float("inf"), 0.066)],
            "Other":  [(2000, 0.022), (5000, 0.039), (10000, 0.048), (20000, 0.052), (float("inf"), 0.066)],
        },
    },

    "HI": {
        "type": "progressive",
        "brackets": {
            "Single": [(2400, 0.014), (4800, 0.032), (9600, 0.055), (float("inf"), 0.11)],
            "Other":  [(4800, 0.014), (9600, 0.032), (19200, 0.055), (float("inf"), 0.11)],
        },
    },

    "IA": {
        "type": "progressive",
        "brackets": {
            "Single": [(6000, 0.044), (30000, 0.0575), (float("inf"), 0.06)],
            "Other":  [(12000, 0.044), (60000, 0.0575), (float("inf"), 0.06)],
        },
    },

    "ID": {
        "type": "progressive",
        "brackets": {
            "Single": [(1600, 0.01), (4800, 0.03), (float("inf"), 0.058)],
            "Other":  [(3200, 0.01), (9600, 0.03), (float("inf"), 0.058)],
        },
    },

    "KS": {
        "type": "progressive",
        "brackets": {
            "Single": [(15000, 0.031), (30000, 0.0525), (float("inf"), 0.057)],
            "Other":  [(30000, 0.031), (60000, 0.0525), (float("inf"), 0.057)],
        },
    },

    "LA": {
        "type": "progressive",
        "brackets": {
            "Single": [(12500, 0.0185), (50000, 0.035), (float("inf"), 0.0425)],
            "Other":  [(25000, 0.0185), (100000, 0.035), (float("inf"), 0.0425)],
        },
    },

    "MD": {
        "type": "progressive",
        "brackets": {
            "Single": [(1000, 0.02), (2000, 0.03), (3000, 0.04), (float("inf"), 0.0575)],
            "Other":  [(1000, 0.02), (2000, 0.03), (3000, 0.04), (float("inf"), 0.0575)],
        },
    },

    "ME": {
        "type": "progressive",
        "brackets": {
            "Single": [(23000, 0.058), (54450, 0.0675), (float("inf"), 0.0715)],
            "Other":  [(46000, 0.058), (108900, 0.0675), (float("inf"), 0.0715)],
        },
    },

    "MN": {
        "type": "progressive",
        "brackets": {
            "Single": [(30000, 0.0535), (100000, 0.068), (float("inf"), 0.0985)],
            "Other":  [(60000, 0.0535), (200000, 0.068), (float("inf"), 0.0985)],
        },
    },

    "MO": {
        "type": "progressive",
        "brackets": {
            "Single": [(1000, 0.015), (3000, 0.02), (5000, 0.025), (float("inf"), 0.0495)],
            "Other":  [(2000, 0.015), (6000, 0.02), (10000, 0.025), (float("inf"), 0.0495)],
        },
    },

    "MS": {
        "type": "progressive",
        "brackets": {
            "Single": [(5000, 0.04), (float("inf"), 0.05)],
            "Other":  [(10000, 0.04), (float("inf"), 0.05)],
        },
    },

    "MT": {
        "type": "progressive",
        "brackets": {
            "Single": [(3600, 0.01), (6800, 0.02), (10400, 0.03), (float("inf"), 0.0675)],
            "Other":  [(7200, 0.01), (13600, 0.02), (20800, 0.03), (float("inf"), 0.0675)],
        },
    },

    "ND": {
        "type": "progressive",
        "brackets": {
            "Single": [(40000, 0.011), (float("inf"), 0.029)],
            "Other":  [(80000, 0.011), (float("inf"), 0.029)],
        },
    },

    "NE": {
        "type": "progressive",
        "brackets": {
            "Single": [(3600, 0.0246), (19000, 0.0351), (float("inf"), 0.0684)],
            "Other":  [(7200, 0.0246), (38000, 0.0351), (float("inf"), 0.0684)],
        },
    },

    "NJ": {
        "type": "progressive",
        "brackets": {
            "Single": [(20000, 0.014), (35000, 0.0175), (40000, 0.035), (75000, 0.05525), (float("inf"), 0.1075)],
            "Other":  [(20000, 0.014), (35000, 0.0175), (40000, 0.035), (75000, 0.05525), (float("inf"), 0.1075)],
        },
    },

    "NM": {
        "type": "progressive",
        "brackets": {
            "Single": [(5500, 0.017), (11000, 0.032), (float("inf"), 0.059)],
            "Other":  [(8000, 0.017), (16000, 0.032), (float("inf"), 0.059)],
        },
    },

    "NY": {
        "type": "progressive",
        "brackets": {
            "Single": [(8500, 0.04), (11700, 0.045), (13900, 0.0525), (21400, 0.059), (float("inf"), 0.109)],
            "Other":  [(17150, 0.04), (23600, 0.045), (27900, 0.0525), (43000, 0.059), (float("inf"), 0.109)],
        },
    },

    "OR": {
        "type": "progressive",
        "brackets": {
            "Single": [(3750, 0.0475), (9450, 0.0675), (float("inf"), 0.099)],
            "Other":  [(7500, 0.0475), (18900, 0.0675), (float("inf"), 0.099)],
        },
    },

    "RI": {
        "type": "progressive",
        "brackets": {
            "Single": [(68200, 0.0375), (155050, 0.0475), (float("inf"), 0.0599)],
            "Other":  [(68200, 0.0375), (155050, 0.0475), (float("inf"), 0.0599)],
        },
    },

    "SC": {
        "type": "progressive",
        "brackets": {
            "Single": [(3200, 0.03), (16040, 0.065), (float("inf"), 0.07)],
            "Other":  [(6400, 0.03), (32080, 0.065), (float("inf"), 0.07)],
        },
    },

    "VT": {
        "type": "progressive",
        "brackets": {
            "Single": [(40950, 0.0335), (99200, 0.066), (float("inf"), 0.0875)],
            "Other":  [(81850, 0.0335), (198400, 0.066), (float("inf"), 0.0875)],
        },
    },

    "VA": {
        "type": "progressive",
        "brackets": {
            "Single": [(3000, 0.02), (5000, 0.03), (17000, 0.05), (float("inf"), 0.0575)],
            "Other":  [(6000, 0.02), (10000, 0.03), (34000, 0.05), (float("inf"), 0.0575)],
        },
    },

    "WV": {
        "type": "progressive",
        "brackets": {
            "Single": [(10000, 0.03), (25000, 0.04), (float("inf"), 0.065)],
            "Other":  [(20000, 0.03), (50000, 0.04), (float("inf"), 0.065)],
        },
    },

    "WI": {
        "type": "progressive",
        "brackets": {
            "Single": [(13810, 0.0354), (27630, 0.0465), (float("inf"), 0.0765)],
            "Other":  [(27630, 0.0354), (55260, 0.0465), (float("inf"), 0.0765)],
        },
    },
}



def calculate_state_income_tax(total_income, year_cache, sim_config):
    if not sim_config._state_tax_enabled:
        return 0.0

    if sim_config._state_tax_type == "flat":
        return total_income * sim_config._state_tax_rate

    brackets = year_cache["state_brackets"]

    tax = 0.0
    lower = 0.0

    for upper, rate in brackets:
        if total_income <= upper:
            return tax + (total_income - lower) * rate
        tax += (upper - lower) * rate
        lower = upper

    return tax


def get_us_federal_marginal_tax_rate(total_income, year, sim_config):
    """
    Returns the marginal U.S. federal income tax rate (top bracket reached)
    as a decimal (e.g., 0.22).
    """
    if not getattr(sim_config, "calculate_income_taxes", False):
        return None

    year_cache = prepare_tax_year_cache(year, sim_config)

    taxable_income = total_income - year_cache["ordinary_standard_deduction"]
    if taxable_income <= 0.0:
        return year_cache["ordinary_brackets"][0][1]

    for upper, rate in year_cache["ordinary_brackets"]:
        if taxable_income <= upper:
            return rate

    return None