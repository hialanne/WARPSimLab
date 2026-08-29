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


def _withdraw_cash_by_order(h_port, w_port, amount, sim_config):
    remaining = max(0.0, float(amount))
    result = {
        "total": 0.0, "pre_tax": 0.0, "post_tax": 0.0, "roth": 0.0, "hsa": 0.0,
        "real_estate": 0.0, "uncovered": 0.0, "by_person": {"husband": 0.0, "wife": 0.0},
    }

    def owner_name(port):
        if port is h_port:
            return "husband"
        if port is w_port:
            return "wife"
        raise RuntimeError("Withdrawal used an unknown portfolio object")


    def order_by_bucket(p1, p2, total_attr):
        return [p1, p2] if getattr(p1, total_attr) >= getattr(p2, total_attr) else [p2, p1]


    def withdraw_from_bucket(port, requested, bucket):
        requested = max(0.0, float(requested))
        if requested <= 0.0:
            return 0.0

        if bucket == "post":
            total, attrs, result_key = port.total_value_post, ("eq_post", "bd_post", "cs_post"), "post_tax"
        elif bucket == "pre":
            total, attrs, result_key = port.total_value_pre, ("eq_pre", "bd_pre", "cs_pre"), "pre_tax"
        elif bucket == "roth":
            total, attrs, result_key = port.total_value_roth, ("eq_roth", "bd_roth", "cs_roth"), "roth"
        elif bucket == "hsa":
            total, attrs, result_key = port.total_value_hsa, ("hsa_eq", "hsa_bd", "hsa_cs"), "hsa"
        else:
            raise ValueError(f"Unknown withdrawal bucket: {bucket}")

        total = max(0.0, float(total))
        if total <= 0.0:
            return 0.0

        take = min(requested, total)
        ratio = take / total

        for attr in attrs:
            current = float(getattr(port, attr))
            setattr(port, attr, max(0.0, current - current * ratio))

        result[result_key] += take
        result["by_person"][owner_name(port)] += take
        result["total"] += take
        return take


    def withdraw_from_real_estate(port, requested):
        requested = max(0.0, float(requested))
        if requested <= 0.0:
            return 0.0

        available = max(0.0, float(port.re_post))
        if available <= 0.0:
            return 0.0

        take = min(requested, available)
        port.re_post = max(0.0, port.re_post - take)
        result["real_estate"] += take
        result["by_person"][owner_name(port)] += take
        result["total"] += take
        return take

    withdrawal_order = [
        ("post", "total_value_post"), ("pre", "total_value_pre"),
        ("roth", "total_value_roth"), ("hsa", "total_value_hsa"),
    ]

    if sim_config.second_person_enabled:
        for bucket, total_attr in withdrawal_order:
            for port in order_by_bucket(h_port, w_port, total_attr):
                remaining -= withdraw_from_bucket(port, remaining, bucket)
                if remaining <= 0.0:
                    return result

        for port in order_by_bucket(h_port, w_port, "re_post"):
            remaining -= withdraw_from_real_estate(port, remaining)
            if remaining <= 0.0:
                return result
    else:
        for bucket, total_attr in withdrawal_order:
            remaining -= withdraw_from_bucket(h_port, remaining, bucket)
            if remaining <= 0.0:
                return result

        remaining -= withdraw_from_real_estate(h_port, remaining)

    result["uncovered"] = max(0.0, remaining)
    return result


def fund_tax_cash_shortfall(h_port, w_port, tax_due, cash_available, sim_config):
    tax_due = max(0.0, float(tax_due))
    cash_available = max(0.0, float(cash_available))
    cash_required = max(0.0, tax_due - cash_available)

    result = _withdraw_cash_by_order(h_port, w_port, cash_required, sim_config)
    result["required"] = cash_required
    return result


def calculate_retirement_withdrawal(
    h_port,
    w_port,
    husband,
    wife,
    year,
    sim_config,
    *,
    rmd_h,
    rmd_w=0.0,
    additional_cash_needed=0.0,
):
    """
    Retirement withdrawals.

    additional_cash_needed is an optional scheduled after-tax cash use,
    such as a Roth IRA or Roth workplace-plan contribution. It increases
    the requested portfolio withdrawal but does not change the cached base
    retirement-withdrawal amount.

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
        total_portfolio = h_port.total_value + (w_port.total_value if sim_config.second_person_enabled else 0.0)
        mode = sim_config.retirement_withdraw_mode

        if mode in ["Percentage", "Percentage + Inflation"]:
            sim_config._ret_withdraw_base_dollars = total_portfolio * sim_config.retirement_withdraw_pct / 100.0
        elif mode in ["Fixed Dollar Amount", "Fixed Dollar Amount + Inflation"]:
            sim_config._ret_withdraw_base_dollars = sim_config.retirement_withdraw_dollars
        else:
            sim_config._ret_withdraw_base_dollars = 0.0

    mode = sim_config.retirement_withdraw_mode
    base = sim_config._ret_withdraw_base_dollars

    rmd_h = max(0.0, float(rmd_h))

    if sim_config.second_person_enabled:
        rmd_w = max(0.0, float(rmd_w))
    else:
        rmd_w = 0.0

    if rmd_h > h_port.total_value_pre + 1e-6:
        raise RuntimeError("Husband RMD exceeds remaining pre-tax assets")

    if sim_config.second_person_enabled and rmd_w > w_port.total_value_pre + 1e-6:
        raise RuntimeError("Wife RMD exceeds remaining pre-tax assets")

    withdraw_rmds(h_port, rmd_h)

    if sim_config.second_person_enabled:
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
    additional_cash_needed = max(0.0, float(additional_cash_needed))
    withdrawal_amount += additional_cash_needed

    remaining = max(0.0, withdrawal_amount - rmd_total)
    withdrawal = _withdraw_cash_by_order(h_port, w_port, remaining, sim_config)

    return {
        "total": rmd_total + withdrawal["total"],
        "rmd": rmd_total,
        "pre_tax": withdrawal["pre_tax"],
        "post_tax": withdrawal["post_tax"],
        "roth": withdrawal["roth"],
        "hsa": withdrawal["hsa"],
        "real_estate": withdrawal["real_estate"],
        "uncovered": withdrawal["uncovered"],
        "by_person": {
            "husband": rmd_h + withdrawal["by_person"]["husband"],
            "wife": rmd_w + withdrawal["by_person"]["wife"],
        },
        "rmd_by_person": {"husband": rmd_h, "wife": rmd_w},
    }

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




