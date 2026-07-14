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