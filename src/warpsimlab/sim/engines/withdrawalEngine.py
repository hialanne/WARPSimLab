# withdrawalEngine.py

from src.warpsimlab.dataClasses.portfolioState import *
from src.warpsimlab.utils.constants import UNIFORM_LIFETIME_TABLE, RMD_START_AGE


def _get_withdrawal_inflation_factor(year, sim_config):
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
        factor = 1.0
        for y in range(1, year + 1):
            annual_inflation = float(sim_config._hist_inflation[start_idx + (y - 1)])
            factor *= (1.0 + annual_inflation)
        return factor

    return (1.0 + sim_config.inflation_rate) ** year


def calculate_rmd(balance, age):
    """Return RMD for a given balance and age using the uniform lifetime table."""
    if age < RMD_START_AGE:
        return 0
    divisor = UNIFORM_LIFETIME_TABLE.get(age, 2.0)  # fallback for age>120
    return balance / divisor


def calculate_rmds(sim_portfolio, person, age, sim_config):
    """
    Calculate RMDs and apply them proportionally to pre-tax assets.
    Returns the RMD amount.
    """
    if not sim_config.include_rmd:
        return 0

    total_pre = sim_portfolio.eq_pre + sim_portfolio.bd_pre + sim_portfolio.cs_pre
    if total_pre <= 0:
        return 0

    rmd = calculate_rmd(total_pre, age)

    return rmd


def withdraw_rmds(sim_portfolio, rmd):
    total_pre = sim_portfolio.eq_pre + sim_portfolio.bd_pre + sim_portfolio.cs_pre
    if total_pre <= 0:
        return 0

    sim_portfolio.eq_pre -= rmd * (sim_portfolio.eq_pre / total_pre)
    sim_portfolio.bd_pre -= rmd * (sim_portfolio.bd_pre / total_pre)
    sim_portfolio.cs_pre -= rmd * (sim_portfolio.cs_pre / total_pre)

    return rmd


def calculate_retirement_withdrawal(h_port, w_port, husband, wife, year, sim_config):
    """
    Retirement withdrawals.

    Withdrawal order:
        1. post-tax
        2. pre-tax
        3. Roth
        4. HSA
        5. net real-estate equity

    Roth and HSA are modeled as simplified tax-free buckets.
    RMDs apply only to pre-tax assets.
    """

    if not hasattr(sim_config, "_ret_withdraw_base_dollars") or sim_config._ret_withdraw_base_dollars is None:
        total_portfolio = h_port.total_value + (
            w_port.total_value if sim_config.second_person_enabled else 0.0
        )

        mode = sim_config.retirement_withdraw_mode

        if mode in ["Percentage", "Percentage + Inflation"]:
            sim_config._ret_withdraw_base_dollars = (
                total_portfolio * sim_config.retirement_withdraw_pct / 100.0
            )
        elif mode in ["Fixed Dollar Amount", "Fixed Dollar Amount + Inflation"]:
            sim_config._ret_withdraw_base_dollars = sim_config.retirement_withdraw_dollars
        else:
            sim_config._ret_withdraw_base_dollars = 0.0

    mode = sim_config.retirement_withdraw_mode
    base = sim_config._ret_withdraw_base_dollars

    rmd_h = calculate_rmds(h_port, husband, husband.age + year, sim_config)
    withdraw_rmds(h_port, rmd_h)

    rmd_w = 0.0
    if sim_config.second_person_enabled:
        rmd_w = calculate_rmds(w_port, wife, wife.age + year, sim_config)
        withdraw_rmds(w_port, rmd_w)

    rmd_total = rmd_h + rmd_w

    if mode == "Off":
        withdrawal_amount = rmd_total
    elif mode == "Percentage":
        withdrawal_amount = base
    elif mode == "Percentage + Inflation":
        withdrawal_amount = base * _get_withdrawal_inflation_factor(year, sim_config)
    elif mode == "Fixed Dollar Amount":
        withdrawal_amount = base
    elif mode == "Fixed Dollar Amount + Inflation":
        withdrawal_amount = base * _get_withdrawal_inflation_factor(year, sim_config)
    else:
        withdrawal_amount = rmd_total

    withdrawal_amount = max(withdrawal_amount, rmd_total)
    remaining = withdrawal_amount - rmd_total

    total_withdrawn = rmd_total

    withdrawn_pre = 0.0
    withdrawn_post = 0.0
    withdrawn_roth = 0.0
    withdrawn_hsa = 0.0
    withdrawn_real_estate = 0.0

    withdrawn_husband = rmd_h
    withdrawn_wife = rmd_w

    def result():
        return {
            "total": total_withdrawn,
            "rmd": rmd_total,
            "pre_tax": withdrawn_pre,
            "post_tax": withdrawn_post,
            "roth": withdrawn_roth,
            "hsa": withdrawn_hsa,
            "real_estate": withdrawn_real_estate,
            "uncovered": max(0.0, remaining),
            "by_person": {
                "husband": withdrawn_husband,
                "wife": withdrawn_wife,
            },
            "rmd_by_person": {
                "husband": rmd_h,
                "wife": rmd_w,
            },
        }


    if remaining <= 0.0:
        return result()


    def order_by_bucket(p1, p2, total_attr):
        if getattr(p1, total_attr) >= getattr(p2, total_attr):
            return [p1, p2]
        return [p2, p1]


    def withdraw_from_bucket(port, amount, bucket):
        nonlocal withdrawn_pre
        nonlocal withdrawn_post
        nonlocal withdrawn_roth
        nonlocal withdrawn_hsa
        nonlocal withdrawn_husband
        nonlocal withdrawn_wife

        amount = max(0.0, float(amount))
        if amount <= 0.0:
            return 0.0

        if bucket == "post":
            total = port.total_value_post
            attrs = ("eq_post", "bd_post", "cs_post")
        elif bucket == "pre":
            total = port.total_value_pre
            attrs = ("eq_pre", "bd_pre", "cs_pre")
        elif bucket == "roth":
            total = port.total_value_roth
            attrs = ("eq_roth", "bd_roth", "cs_roth")
        elif bucket == "hsa":
            total = port.total_value_hsa
            attrs = ("hsa_eq", "hsa_bd", "hsa_cs")
        else:
            raise ValueError(f"Unknown withdrawal bucket: {bucket}")

        total = max(0.0, float(total))
        if total <= 0.0:
            return 0.0

        take = min(amount, total)
        ratio = take / total

        for attr in attrs:
            current = float(getattr(port, attr))
            updated = current - current * ratio

            if updated < 0.0 and updated > -1e-9:
                updated = 0.0

            setattr(port, attr, max(0.0, updated))

        if bucket == "post":
            withdrawn_post += take
        elif bucket == "pre":
            withdrawn_pre += take
        elif bucket == "roth":
            withdrawn_roth += take
        elif bucket == "hsa":
            withdrawn_hsa += take

        if port is h_port:
            withdrawn_husband += take
        elif port is w_port:
            withdrawn_wife += take
        else:
            raise RuntimeError(
                "Withdrawal used an unknown portfolio object"
            )

        return take


    def withdraw_from_real_estate(port, amount):
        nonlocal withdrawn_real_estate
        nonlocal withdrawn_husband
        nonlocal withdrawn_wife

        if amount <= 0.0:
            return 0.0

        available = max(0.0, float(port.re_post))
        if available <= 0.0:
            return 0.0

        take = min(amount, available)
        port.re_post -= take

        if port.re_post < 0.0:
            port.re_post = 0.0

        withdrawn_real_estate += take

        if port is h_port:
            withdrawn_husband += take
        elif port is w_port:
            withdrawn_wife += take
        else:
            raise RuntimeError("Real-estate withdrawal used an unknown portfolio object")

        return take

    withdrawal_order = [
        ("post", "total_value_post"),
        ("pre", "total_value_pre"),
        ("roth", "total_value_roth"),
        ("hsa", "total_value_hsa"),
    ]

    if sim_config.second_person_enabled:
        for bucket, total_attr in withdrawal_order:
            for port in order_by_bucket(h_port, w_port, total_attr):
                taken = withdraw_from_bucket(port, remaining, bucket)
                remaining -= taken
                total_withdrawn += taken

                if remaining <= 0.0:
                    return result()
    else:
        for bucket, total_attr in withdrawal_order:
            taken = withdraw_from_bucket(h_port, remaining, bucket)
            remaining -= taken
            total_withdrawn += taken

            if remaining <= 0.0:
                return result()

    if remaining > 0.0:
        if sim_config.second_person_enabled:
            for port in order_by_bucket(h_port, w_port, "re_post"):
                taken = withdraw_from_real_estate(port, remaining)
                remaining -= taken
                total_withdrawn += taken

                if remaining <= 0.0:
                    return result()
        else:
            taken = withdraw_from_real_estate(h_port, remaining)
            remaining -= taken
            total_withdrawn += taken

    return result()


def use_expenses_this_year(sim_config, husband, wife, year):
    """
    Determine whether manual expenses should be used for this simulation year.
    Manual expenses are used until both husband and wife are retired.

    Args:
        sim_config: Simulation configuration object
        husband: Person object
        wife: Person object
        year: int, current year of the simulation (0-based)

    Returns:
        bool: True if manual expenses should be used this year, False for retirement withdrawals
    """
    if sim_config.always_use_expense_mode:
        return True

    # Current ages
    curr_h_age = husband.age + year
    curr_w_age = wife.age + year if sim_config.second_person_enabled else 0

    # Check retirement status
    if sim_config.second_person_enabled:
        both_retired = curr_h_age >= husband.retire_age and curr_w_age >= wife.retire_age
    else:
        both_retired = curr_h_age >= husband.retire_age

    return not both_retired




