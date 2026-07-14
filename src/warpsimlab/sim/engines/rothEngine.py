from . import portfolioEngine

ROTH_IRA_CONTRIBUTION = "roth_ira_contribution"
ROTH_WORKPLACE_CONTRIBUTION = "roth_workplace_contribution"
ROTH_CONVERSION = "roth_conversion"

ROTH_FLOW_TYPES = {
    ROTH_IRA_CONTRIBUTION,
    ROTH_WORKPLACE_CONTRIBUTION,
    ROTH_CONVERSION,
}


def _build_percent_of_inflation_factors(
    sim_config,
    inflation_adjustment_pct,
):
    """
    Build annual adjustment factors using a selected percentage of inflation.

    Examples:
        0.0   -> no inflation adjustment
        100.0 -> full inflation adjustment
        50.0  -> half of annual inflation
    """
    years = sim_config.years_to_simulate + 1
    factors = [1.0] * years

    adjustment_fraction = (
        float(inflation_adjustment_pct) / 100.0
    )

    historical_mode_active = (
        sim_config.subplot_mode == "monte_carlo"
        and sim_config.sim_type == "portfolio_sim"
        and getattr(
            sim_config,
            "monte_carlo_mode",
            "pathBasedAnnualSampling",
        ) == "rollingHistoricalWindows"
        and getattr(
            sim_config,
            "_active_historical_sim_index",
            None,
        ) is not None
        and getattr(
            sim_config,
            "_hist_inflation",
            None,
        ) is not None
    )

    if historical_mode_active:
        sim_index = sim_config._active_historical_sim_index
        start_idx = int(
            sim_config._hist_window_start_indices[sim_index]
        )

        for year in range(1, years):
            annual_inflation = float(
                sim_config._hist_inflation[
                    start_idx + year - 1
                ]
            )

            factors[year] = factors[year - 1] * (
                1.0
                + annual_inflation * adjustment_fraction
            )

        return factors

    annual_adjustment = (
        float(sim_config.inflation_rate)
        * adjustment_fraction
    )

    for year in range(1, years):
        factors[year] = factors[year - 1] * (
            1.0 + annual_adjustment
        )

    return factors


def _empty_flow_totals():
    return {
        ROTH_IRA_CONTRIBUTION: {
            "husband": 0.0,
            "wife": 0.0,
            "total": 0.0,
        },
        ROTH_WORKPLACE_CONTRIBUTION: {
            "husband": 0.0,
            "wife": 0.0,
            "total": 0.0,
        },
        ROTH_CONVERSION: {
            "husband": 0.0,
            "wife": 0.0,
            "total": 0.0,
        },
    }


def calculate_roth_flows_for_year(
    curr_husband_age,
    curr_wife_age,
    year,
    sim_config,
):
    """
    Calculate requested Roth flows active during the current year.

    This function only interprets the schedule. It does not mutate
    portfolios, calculate taxes, or cap flows to available assets.

    Returns
    -------
    dict
        Per-type requested amounts split between husband, wife, and total.
    """
    results = _empty_flow_totals()

    roth_flows = getattr(
        sim_config,
        "roth_flows",
        [],
    )

    for flow in roth_flows:
        if not flow.get("enabled", True):
            continue

        flow_type = flow.get(
            "type",
            ROTH_IRA_CONTRIBUTION,
        )

        if flow_type not in ROTH_FLOW_TYPES:
            continue

        owner = flow.get("owner", "husband")

        if owner not in {"husband", "wife"}:
            continue

        if (
            owner == "wife"
            and not sim_config.second_person_enabled
        ):
            continue

        owner_age = (
            curr_wife_age
            if owner == "wife"
            else curr_husband_age
        )

        start_age = int(
            flow.get("start_age", 0)
        )
        end_age = int(
            flow.get("end_age", 120)
        )

        if owner_age < start_age or owner_age > end_age:
            continue

        amount = max(
            0.0,
            float(flow.get("amount", 0.0)),
        )

        if amount <= 0.0:
            continue

        inflation_adjustment_pct = float(
            flow.get(
                "inflation_adjustment_pct",
                0.0,
            )
        )

        adjustment_factor = (
            _build_percent_of_inflation_factors(
                sim_config,
                inflation_adjustment_pct,
            )[year]
        )

        adjusted_amount = amount * adjustment_factor

        results[flow_type][owner] += adjusted_amount
        results[flow_type]["total"] += adjusted_amount

    return results

def allocate_funded_contributions(
    requested_ira_husband,
    requested_ira_wife,
    requested_workplace_husband,
    requested_workplace_wife,
    funded_total,
):
    """
    Allocate the amount that was actually funded across requested Roth
    contributions.

    If all requested contributions were funded, each requested amount is
    returned unchanged. If funding was insufficient, all contribution
    amounts are reduced proportionally.

    Returns
    -------
    dict
        Actual funded contribution amounts by type and owner.
    """
    requested = {
        ROTH_IRA_CONTRIBUTION: {
            "husband": max(
                0.0,
                float(requested_ira_husband),
            ),
            "wife": max(
                0.0,
                float(requested_ira_wife),
            ),
        },
        ROTH_WORKPLACE_CONTRIBUTION: {
            "husband": max(
                0.0,
                float(requested_workplace_husband),
            ),
            "wife": max(
                0.0,
                float(requested_workplace_wife),
            ),
        },
    }

    requested_total = sum(
        owner_amount
        for contribution_type in requested.values()
        for owner_amount in contribution_type.values()
    )

    funded_total = max(
        0.0,
        min(
            float(funded_total),
            requested_total,
        ),
    )

    if requested_total <= 0.0:
        scale = 0.0
    else:
        scale = funded_total / requested_total

    result = {
        ROTH_IRA_CONTRIBUTION: {
            "husband": (
                requested[ROTH_IRA_CONTRIBUTION]["husband"]
                * scale
            ),
            "wife": (
                requested[ROTH_IRA_CONTRIBUTION]["wife"]
                * scale
            ),
            "total": 0.0,
        },
        ROTH_WORKPLACE_CONTRIBUTION: {
            "husband": (
                requested[ROTH_WORKPLACE_CONTRIBUTION]["husband"]
                * scale
            ),
            "wife": (
                requested[ROTH_WORKPLACE_CONTRIBUTION]["wife"]
                * scale
            ),
            "total": 0.0,
        },
    }

    result[ROTH_IRA_CONTRIBUTION]["total"] = (
        result[ROTH_IRA_CONTRIBUTION]["husband"]
        + result[ROTH_IRA_CONTRIBUTION]["wife"]
    )

    result[ROTH_WORKPLACE_CONTRIBUTION]["total"] = (
        result[ROTH_WORKPLACE_CONTRIBUTION]["husband"]
        + result[ROTH_WORKPLACE_CONTRIBUTION]["wife"]
    )

    return result

def prepare_requested_roth_flows(
    *,
    curr_husband_age,
    curr_wife_age,
    year,
    payroll_wages_husband,
    payroll_wages_wife,
    second_person_enabled,
    sim_config,
):
    """
    Build the requested Roth flows for one simulation year.

    Workplace Roth contributions are capped by each owner's current
    gross wages. Roth IRA contributions and Roth conversions are not
    wage capped.

    This function does not mutate portfolios.
    """
    scheduled_flows = calculate_roth_flows_for_year(
        curr_husband_age=curr_husband_age,
        curr_wife_age=curr_wife_age,
        year=year,
        sim_config=sim_config,
    )

    requested_husband_roth_ira = scheduled_flows[
        ROTH_IRA_CONTRIBUTION
    ]["husband"]

    requested_wife_roth_ira = 0.0
    if second_person_enabled:
        requested_wife_roth_ira = scheduled_flows[
            ROTH_IRA_CONTRIBUTION
        ]["wife"]

    requested_husband_roth_workplace = min(
        scheduled_flows[
            ROTH_WORKPLACE_CONTRIBUTION
        ]["husband"],
        max(0.0, float(payroll_wages_husband)),
    )

    requested_wife_roth_workplace = 0.0
    if second_person_enabled:
        requested_wife_roth_workplace = min(
            scheduled_flows[
                ROTH_WORKPLACE_CONTRIBUTION
            ]["wife"],
            max(0.0, float(payroll_wages_wife)),
        )

    requested_husband_conversion = scheduled_flows[
        ROTH_CONVERSION
    ]["husband"]

    requested_wife_conversion = 0.0
    if second_person_enabled:
        requested_wife_conversion = scheduled_flows[
            ROTH_CONVERSION
        ]["wife"]

    requested_roth_contribution_total = (
        requested_husband_roth_ira
        + requested_wife_roth_ira
        + requested_husband_roth_workplace
        + requested_wife_roth_workplace
    )

    return {
        ROTH_IRA_CONTRIBUTION: {
            "husband": requested_husband_roth_ira,
            "wife": requested_wife_roth_ira,
            "total": (
                requested_husband_roth_ira
                + requested_wife_roth_ira
            ),
        },
        ROTH_WORKPLACE_CONTRIBUTION: {
            "husband": requested_husband_roth_workplace,
            "wife": requested_wife_roth_workplace,
            "total": (
                requested_husband_roth_workplace
                + requested_wife_roth_workplace
            ),
        },
        ROTH_CONVERSION: {
            "husband": requested_husband_conversion,
            "wife": requested_wife_conversion,
            "total": (
                requested_husband_conversion
                + requested_wife_conversion
            ),
        },
        "requested_contribution_total": (
            requested_roth_contribution_total
        ),
    }


def resolve_funded_contributions(
    *,
    requested_flows,
    funded_total,
):
    """
    Allocate actual Roth contribution funding across the requested
    IRA and workplace contributions.
    """
    funded = allocate_funded_contributions(
        requested_ira_husband=(
            requested_flows[
                ROTH_IRA_CONTRIBUTION
            ]["husband"]
        ),
        requested_ira_wife=(
            requested_flows[
                ROTH_IRA_CONTRIBUTION
            ]["wife"]
        ),
        requested_workplace_husband=(
            requested_flows[
                ROTH_WORKPLACE_CONTRIBUTION
            ]["husband"]
        ),
        requested_workplace_wife=(
            requested_flows[
                ROTH_WORKPLACE_CONTRIBUTION
            ]["wife"]
        ),
        funded_total=funded_total,
    )

    actual_contribution_total = (
        funded[ROTH_IRA_CONTRIBUTION]["total"]
        + funded[ROTH_WORKPLACE_CONTRIBUTION]["total"]
    )

    return {
        ROTH_IRA_CONTRIBUTION: funded[
            ROTH_IRA_CONTRIBUTION
        ],
        ROTH_WORKPLACE_CONTRIBUTION: funded[
            ROTH_WORKPLACE_CONTRIBUTION
        ],
        "total": actual_contribution_total,
    }


def resolve_contribution_shortfall(
    *,
    requested_flows,
    uncovered_amount,
):
    """
    Apply a cash shortfall to discretionary Roth contributions first.

    Any uncovered amount up to the requested contribution total reduces
    Roth contributions. Any remaining uncovered amount is returned for
    the caller to treat according to the surrounding simulation mode.

    Returns
    -------
    dict
        funded_contributions:
            Actual Roth contribution amounts by type and owner.

        remaining_uncovered:
            Uncovered amount left after all requested Roth contributions
            have been eliminated.
    """
    requested_total = max(
        0.0,
        float(
            requested_flows.get(
                "requested_contribution_total",
                0.0,
            )
        ),
    )

    uncovered_amount = max(
        0.0,
        float(uncovered_amount),
    )

    funded_total = max(
        0.0,
        requested_total - uncovered_amount,
    )

    remaining_uncovered = max(
        0.0,
        uncovered_amount - requested_total,
    )

    funded_contributions = resolve_funded_contributions(
        requested_flows=requested_flows,
        funded_total=funded_total,
    )

    return {
        "funded_contributions": funded_contributions,
        "remaining_uncovered": remaining_uncovered,
    }


def separate_retirement_contribution_funding(
    *,
    withdrawal_result,
    actual_contribution_total,
):
    """
    Separate retirement withdrawals used to fund Roth contributions
    from retirement withdrawals available as spendable cash.

    RMD amounts are excluded because they are already represented by
    the income engine.
    """
    actual_contribution_total = max(
        0.0,
        float(actual_contribution_total),
    )

    withdrawal_total = max(
        0.0,
        float(withdrawal_result.get("total", 0.0)),
    )

    rmd_total = max(
        0.0,
        float(withdrawal_result.get("rmd", 0.0)),
    )

    household_spendable_withdrawal = max(
        0.0,
        withdrawal_total
        - rmd_total
        - actual_contribution_total,
    )

    by_person = withdrawal_result.get("by_person", {})
    rmd_by_person = withdrawal_result.get("rmd_by_person", {})

    husband_gross_additional_withdrawal = max(
        0.0,
        float(by_person.get("husband", 0.0))
        - float(rmd_by_person.get("husband", 0.0)),
    )

    wife_gross_additional_withdrawal = max(
        0.0,
        float(by_person.get("wife", 0.0))
        - float(rmd_by_person.get("wife", 0.0)),
    )

    gross_person_additional_total = (
        husband_gross_additional_withdrawal
        + wife_gross_additional_withdrawal
    )

    if gross_person_additional_total > 0.0:
        husband_contribution_funding = (
            actual_contribution_total
            * husband_gross_additional_withdrawal
            / gross_person_additional_total
        )
    else:
        husband_contribution_funding = 0.0

    wife_contribution_funding = (
        actual_contribution_total
        - husband_contribution_funding
    )

    husband_spendable_withdrawal = max(
        0.0,
        husband_gross_additional_withdrawal
        - husband_contribution_funding,
    )

    wife_spendable_withdrawal = max(
        0.0,
        wife_gross_additional_withdrawal
        - wife_contribution_funding,
    )

    person_spendable_total = (
        husband_spendable_withdrawal
        + wife_spendable_withdrawal
    )

    if abs(
        person_spendable_total
        - household_spendable_withdrawal
    ) > 1e-6:
        raise RuntimeError(
            "Person-level retirement withdrawals do not "
            "match the household withdrawal total"
        )

    return {
        "household": household_spendable_withdrawal,
        "husband": husband_spendable_withdrawal,
        "wife": wife_spendable_withdrawal,
    }


def apply_roth_conversions(
    *,
    husband_portfolio,
    wife_portfolio,
    requested_flows,
    second_person_enabled,
):
    """
    Apply requested Roth conversions to the owners' portfolios.

    Conversion amounts are capped by available pre-tax assets by
    portfolioEngine.convert_pre_tax_to_roth().

    Returns
    -------
    dict
        Actual conversion amounts by owner and household total.
    """
    requested_husband_conversion = requested_flows[
        ROTH_CONVERSION
    ]["husband"]

    requested_wife_conversion = 0.0

    if second_person_enabled:
        requested_wife_conversion = requested_flows[
            ROTH_CONVERSION
        ]["wife"]

    husband_conversion = (
        portfolioEngine.convert_pre_tax_to_roth(
            husband_portfolio,
            requested_husband_conversion,
        )
    )

    wife_conversion = 0.0

    if second_person_enabled:
        wife_conversion = (
            portfolioEngine.convert_pre_tax_to_roth(
                wife_portfolio,
                requested_wife_conversion,
            )
        )

    return {
        "husband": husband_conversion,
        "wife": wife_conversion,
        "total": (
            husband_conversion
            + wife_conversion
        ),
    }

def deposit_funded_roth_contributions(
    *,
    husband_portfolio,
    wife_portfolio,
    funded_contributions,
    second_person_enabled,
):
    """
    Deposit funded Roth IRA and workplace contributions into each
    owner's Roth portfolio.

    Returns
    -------
    dict
        Deposited contribution amounts by owner and household total.
    """
    husband_amount = (
        funded_contributions[
            ROTH_IRA_CONTRIBUTION
        ]["husband"]
        + funded_contributions[
            ROTH_WORKPLACE_CONTRIBUTION
        ]["husband"]
    )

    wife_amount = 0.0

    if second_person_enabled:
        wife_amount = (
            funded_contributions[
                ROTH_IRA_CONTRIBUTION
            ]["wife"]
            + funded_contributions[
                ROTH_WORKPLACE_CONTRIBUTION
            ]["wife"]
        )

    portfolioEngine.apply_roth_contribution(
        husband_portfolio,
        husband_amount,
    )

    if second_person_enabled:
        portfolioEngine.apply_roth_contribution(
            wife_portfolio,
            wife_amount,
        )

    return {
        "husband": husband_amount,
        "wife": wife_amount,
        "total": husband_amount + wife_amount,
    }