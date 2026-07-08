# portfolioEngine.py

import numpy as np

from src.warpsimlab.dataClasses.portfolioState import PortfolioState

EPS = 1e-12


DEBUG_COUPLE = False  # flip False to silence
DEBUG_REBALANCE = False  # flip False to silence

# Here's how to change this flag from other files:
#if year <= 3 and s == 0:
#    portfolioEngine.DEBUG_COUPLE = True
#else:
#    portfolioEngine.DEBUG_COUPLE = False



def _clamp_portfolio_components(port):
    for attr in [
        "eq_pre", "bd_pre", "cs_pre",
        "eq_post", "bd_post", "cs_post",
        "eq_roth", "bd_roth", "cs_roth",
        "hsa_eq", "hsa_bd", "hsa_cs",
    ]:
        if getattr(port, attr, 0.0) < 0.0:
            setattr(port, attr, 0.0)


def _clamp_post_tax_components(port):
    # Backward-compatible wrapper for older call sites.
    _clamp_portfolio_components(port)


def _rebalance_three_asset_bucket(port, eq_attr, bd_attr, cs_attr, eq_ratio, bd_ratio, cs_ratio):
    total = (
        getattr(port, eq_attr, 0.0)
        + getattr(port, bd_attr, 0.0)
        + getattr(port, cs_attr, 0.0)
    )

    if total <= 0.0:
        return

    setattr(port, eq_attr, total * eq_ratio)
    setattr(port, bd_attr, total * bd_ratio)
    setattr(port, cs_attr, total * cs_ratio)


def compute_household_allocation_targets(husband_portfolio, wife_portfolio, sim_config):
    """
    Computes household stock/bond/cash allocation from all investable assets:
    pre-tax, post-tax, Roth, and HSA.
    Excludes real estate.
    """

    h_eq = (
        husband_portfolio.equity_pre
        + husband_portfolio.equity_post
        + getattr(husband_portfolio, "equity_roth", 0.0)
        + getattr(husband_portfolio, "hsa_equity", 0.0)
    )
    h_bd = (
        husband_portfolio.bond_pre
        + husband_portfolio.bond_post
        + getattr(husband_portfolio, "bond_roth", 0.0)
        + getattr(husband_portfolio, "hsa_bond", 0.0)
    )
    h_cs = (
        husband_portfolio.cash_pre
        + husband_portfolio.cash_post
        + getattr(husband_portfolio, "cash_roth", 0.0)
        + getattr(husband_portfolio, "hsa_cash", 0.0)
    )

    w_eq = w_bd = w_cs = 0.0

    if sim_config.second_person_enabled and wife_portfolio is not None:
        w_eq = (
            wife_portfolio.equity_pre
            + wife_portfolio.equity_post
            + getattr(wife_portfolio, "equity_roth", 0.0)
            + getattr(wife_portfolio, "hsa_equity", 0.0)
        )
        w_bd = (
            wife_portfolio.bond_pre
            + wife_portfolio.bond_post
            + getattr(wife_portfolio, "bond_roth", 0.0)
            + getattr(wife_portfolio, "hsa_bond", 0.0)
        )
        w_cs = (
            wife_portfolio.cash_pre
            + wife_portfolio.cash_post
            + getattr(wife_portfolio, "cash_roth", 0.0)
            + getattr(wife_portfolio, "hsa_cash", 0.0)
        )

    total_eq = h_eq + w_eq
    total_bd = h_bd + w_bd
    total_cs = h_cs + w_cs

    total = total_eq + total_bd + total_cs

    if total > 0:
        sim_config.household_eq_target = total_eq / total
        sim_config.household_bd_target = total_bd / total
        sim_config.household_cs_target = total_cs / total
    else:
        sim_config.household_eq_target = 1 / 3
        sim_config.household_bd_target = 1 / 3
        sim_config.household_cs_target = 1 / 3


def _dbg_ps(ps, name):
    print(
        f"[DBG] {name}: "
        f"post(eq={ps.eq_post:.2f}, bd={ps.bd_post:.2f}, cs={ps.cs_post:.2f}) "
        f"pre(eq={ps.eq_pre:.2f}, bd={ps.bd_pre:.2f}, cs={ps.cs_pre:.2f}) "
        f"tot_post={ps.total_value_post:.2f} tot_pre={ps.total_value_pre:.2f} tot={ps.total_value:.2f}"
    )

def _dbg_minmax(ps, name):
    vals = [ps.eq_pre, ps.bd_pre, ps.cs_pre, ps.eq_post, ps.bd_post, ps.cs_post]
    print(
        f"[DBG] {name}: tot_post={ps.total_value_post:.6f} tot_pre={ps.total_value_pre:.6f} "
        f"min_component={min(vals):.12f} max_component={max(vals):.6f} "
        f"post(eq={ps.eq_post:.6f}, bd={ps.bd_post:.6f}, cs={ps.cs_post:.6f})"
    )

# ----------------------------
# Core Portfolio Functions
# ----------------------------

def initialize_portfolio(equity_pre, bond_pre, cash_pre, equity_post, bond_post, cash_post):
    """
    Initializes and returns the portfolio values for the simulation.
    """
    return equity_pre, bond_pre, cash_pre, equity_post, bond_post, cash_post


def create_sim_portfolio(portfolio, sim_config=None):
    """
    Initializes a PortfolioState from a Portfolio object and applies rebalancing.

    Roth model:
    - qualified tax-free bucket
    - no RMDs
    - included in net worth

    HSA model:
    - simplified tax-free bucket
    - no medical-expense tracking in this stage
    - included in net worth
    """

    sim_portfolio = PortfolioState(
        eq_pre=portfolio.equity_pre,
        bd_pre=portfolio.bond_pre,
        cs_pre=portfolio.cash_pre,

        eq_post=portfolio.equity_post,
        bd_post=portfolio.bond_post,
        cs_post=portfolio.cash_post,

        eq_roth=getattr(portfolio, "equity_roth", 0.0),
        bd_roth=getattr(portfolio, "bond_roth", 0.0),
        cs_roth=getattr(portfolio, "cash_roth", 0.0),

        hsa_eq=getattr(portfolio, "hsa_equity", 0.0),
        hsa_bd=getattr(portfolio, "hsa_bond", 0.0),
        hsa_cs=getattr(portfolio, "hsa_cash", 0.0),

        re_post=getattr(portfolio, "real_estate", 0.0) if sim_config.include_realestate else 0.0,
    )

    if sim_config.sim_rebalance == "dont-rebalance":
        for bucket_name, total_attr, eq_attr, bd_attr, cs_attr in [
            ("pre", "total_value_pre", "eq_pre", "bd_pre", "cs_pre"),
            ("post", "total_value_post", "eq_post", "bd_post", "cs_post"),
            ("roth", "total_value_roth", "eq_roth", "bd_roth", "cs_roth"),
            ("hsa", "total_value_hsa", "hsa_eq", "hsa_bd", "hsa_cs"),
        ]:
            total = getattr(sim_portfolio, total_attr)

            setattr(sim_portfolio, f"eq_ratio_{bucket_name}", getattr(sim_portfolio, eq_attr) / total if total > 0 else 0)
            setattr(sim_portfolio, f"bd_ratio_{bucket_name}", getattr(sim_portfolio, bd_attr) / total if total > 0 else 0)
            setattr(sim_portfolio, f"cs_ratio_{bucket_name}", getattr(sim_portfolio, cs_attr) / total if total > 0 else 0)

        return sim_portfolio

    rebalance_ratios = {
        "30-30-40": {"equity": 0.30, "bonds": 0.30, "cash": 0.40},
        "50-30-20": {"equity": 0.50, "bonds": 0.30, "cash": 0.20},
        "70-20-10": {"equity": 0.70, "bonds": 0.20, "cash": 0.10},
    }

    if sim_config.sim_rebalance == "maintain-current-allocation":
        eq_ratio = getattr(sim_config, "household_eq_target", 1 / 3)
        bd_ratio = getattr(sim_config, "household_bd_target", 1 / 3)
        cs_ratio = getattr(sim_config, "household_cs_target", 1 / 3)

    elif sim_config.sim_rebalance == "custom":
        eq_ratio = sim_config.custom_stock
        bd_ratio = sim_config.custom_bonds
        cs_ratio = sim_config.custom_cash

    elif sim_config.sim_rebalance in rebalance_ratios:
        ratios = rebalance_ratios[sim_config.sim_rebalance]
        eq_ratio = ratios["equity"]
        bd_ratio = ratios["bonds"]
        cs_ratio = ratios["cash"]

    else:
        return sim_portfolio

    for eq_attr, bd_attr, cs_attr in [
        ("eq_pre", "bd_pre", "cs_pre"),
        ("eq_post", "bd_post", "cs_post"),
        ("eq_roth", "bd_roth", "cs_roth"),
        ("hsa_eq", "hsa_bd", "hsa_cs"),
    ]:
        _rebalance_three_asset_bucket(
            sim_portfolio,
            eq_attr,
            bd_attr,
            cs_attr,
            eq_ratio,
            bd_ratio,
            cs_ratio,
        )

    return sim_portfolio


def estimate_post_tax_income_components(sim_portfolio, sim_config):
    equity_div_yield = sim_config._post_tax_equity_dividend_yield
    bond_yield = sim_config._post_tax_bond_interest_yield
    cash_yield = sim_config._post_tax_cash_interest_yield

    eq_post = sim_portfolio.eq_post
    bd_post = sim_portfolio.bd_post
    cs_post = sim_portfolio.cs_post

    qualified_dividends = eq_post * equity_div_yield
    bond_interest = bd_post * bond_yield
    cash_interest = cs_post * cash_yield

    ordinary_total = bond_interest + cash_interest
    total = ordinary_total + qualified_dividends

    return {
        "bond_interest": bond_interest,
        "cash_interest": cash_interest,
        "qualified_dividends": qualified_dividends,
        "ordinary_total": ordinary_total,
        "qualified_total": qualified_dividends,
        "total": total,
    }


def apply_post_tax_income_components_to_income(income, post_tax_income, second_person_enabled):
    """
    Apply estimated household post-tax income components into the simulation's
    structured income dictionary.

    Group 1 behavior:
      - bond interest, cash interest, and qualified dividends are all added to
        income["total"]
      - Group 2 will split ordinary vs qualified tax handling more precisely
    """
    income["by_class"]["bond_interest"] += post_tax_income["bond_interest"]
    income["by_class"]["cash_interest"] += post_tax_income["cash_interest"]
    income["by_class"]["qualified_dividends"] += post_tax_income["qualified_dividends"]

    income["by_person"]["husband"] += post_tax_income["by_person"]["husband"]["total"]
    if second_person_enabled:
        income["by_person"]["wife"] += post_tax_income["by_person"]["wife"]["total"]

    income["total"] += post_tax_income["total"]

    return income

def estimate_household_post_tax_income_components(h_port, w_port, sim_config):
    eq_yield = sim_config._post_tax_equity_dividend_yield
    bd_yield = sim_config._post_tax_bond_interest_yield
    cs_yield = sim_config._post_tax_cash_interest_yield

    h_qd = h_port.eq_post * eq_yield
    h_bi = h_port.bd_post * bd_yield
    h_ci = h_port.cs_post * cs_yield
    h_total = h_qd + h_bi + h_ci

    if sim_config.second_person_enabled:
        w_qd = w_port.eq_post * eq_yield
        w_bi = w_port.bd_post * bd_yield
        w_ci = w_port.cs_post * cs_yield
        w_total = w_qd + w_bi + w_ci
    else:
        w_qd = 0.0
        w_bi = 0.0
        w_ci = 0.0
        w_total = 0.0

    bond_interest = h_bi + w_bi
    cash_interest = h_ci + w_ci
    qualified_dividends = h_qd + w_qd

    # --- Clamp tiny floating-point negatives ---
    EPS = 1e-12
    if -EPS < bond_interest < 0.0:
        bond_interest = 0.0
    if -EPS < cash_interest < 0.0:
        cash_interest = 0.0
    if -EPS < qualified_dividends < 0.0:
        qualified_dividends = 0.0

    total = bond_interest + cash_interest + qualified_dividends

    return (
        bond_interest,
        cash_interest,
        qualified_dividends,
        total,
        h_total,
        w_total,
    )


def apply_returns_and_fund_expenses(
    sim_portfolio,
    eq_return,
    bd_return,
    cs_return,
    re_return,
    fund_expense,
):
    eq_mult = 1.0 + eq_return
    bd_mult = 1.0 + bd_return
    cs_mult = 1.0 + cs_return
    re_mult = 1.0 + re_return
    exp_mult = 1.0 - fund_expense

    for attr in ["eq_pre", "eq_post", "eq_roth", "hsa_eq"]:
        setattr(sim_portfolio, attr, getattr(sim_portfolio, attr) * eq_mult)

    for attr in ["bd_pre", "bd_post", "bd_roth", "hsa_bd"]:
        setattr(sim_portfolio, attr, getattr(sim_portfolio, attr) * bd_mult)

    for attr in ["cs_pre", "cs_post", "cs_roth", "hsa_cs"]:
        setattr(sim_portfolio, attr, getattr(sim_portfolio, attr) * cs_mult)

    sim_portfolio.re_post *= re_mult

    total_before = sim_portfolio.total_value

    for attr in [
        "eq_pre", "bd_pre", "cs_pre",
        "eq_post", "bd_post", "cs_post",
        "eq_roth", "bd_roth", "cs_roth",
        "hsa_eq", "hsa_bd", "hsa_cs",
    ]:
        setattr(sim_portfolio, attr, getattr(sim_portfolio, attr) * exp_mult)

    fund_expenses = total_before * fund_expense

    _clamp_portfolio_components(sim_portfolio)

    return fund_expenses


def apply_returns(sim_portfolio, eq_return, bd_return, cs_return, re_return):
    """
    Apply already-determined returns to a portfolio.

    This function is intentionally deterministic.
    It does not sample randomness internally.

    Parameters
    ----------
    sim_portfolio : PortfolioState
        The portfolio state to update in place.
    eq_return : float
        Equity return for the current simulation-year.
    bd_return : float
        Bond return for the current simulation-year.
    cs_return : float
        Cash return for the current simulation-year.
    re_return : float
        Real estate return for the current simulation-year.
    """

    sim_portfolio.eq_pre += sim_portfolio.eq_pre * eq_return
    sim_portfolio.bd_pre += sim_portfolio.bd_pre * bd_return
    sim_portfolio.cs_pre += sim_portfolio.cs_pre * cs_return

    sim_portfolio.eq_post += sim_portfolio.eq_post * eq_return
    sim_portfolio.bd_post += sim_portfolio.bd_post * bd_return
    sim_portfolio.cs_post += sim_portfolio.cs_post * cs_return

    sim_portfolio.re_post += sim_portfolio.re_post * re_return

    # This code is slowing down monte carlo slightly.  I'm pretty sure we
    #   never come in here with a negative return, thus we should be oK.
    

def apply_fund_expenses(sim_portfolio, fund_expense):
    """
    Reduce the portfolio components proportionally by the fund expense (0-1).
    Returns the dollar amount removed.
    """

    total_before = (
        sim_portfolio.eq_pre  +
        sim_portfolio.bd_pre  +
        sim_portfolio.cs_pre  +
        sim_portfolio.eq_post +
        sim_portfolio.bd_post +
        sim_portfolio.cs_post
    )

    deltaFundExpenses = 1 - fund_expense
    sim_portfolio.eq_pre  *= deltaFundExpenses
    sim_portfolio.bd_pre  *= deltaFundExpenses
    sim_portfolio.cs_pre  *= deltaFundExpenses
    sim_portfolio.eq_post *= deltaFundExpenses
    sim_portfolio.bd_post *= deltaFundExpenses
    sim_portfolio.cs_post *= deltaFundExpenses

    total_after = (
        sim_portfolio.eq_pre  +
        sim_portfolio.bd_pre  +
        sim_portfolio.cs_pre  +
        sim_portfolio.eq_post +
        sim_portfolio.bd_post +
        sim_portfolio.cs_post
    )

    total = total_before - total_after

    if total > 0.0:
        return total
    else:
        return 0.0


def rebalance(sim_portfolio, sim_config):
    """
    Rebalance all investable buckets:
    pre-tax, post-tax, Roth, and HSA.
    """

    if sim_config.sim_rebalance == "maintain-current-allocation":
        eq_ratio = getattr(sim_config, "household_eq_target", 1 / 3)
        bd_ratio = getattr(sim_config, "household_bd_target", 1 / 3)
        cs_ratio = getattr(sim_config, "household_cs_target", 1 / 3)

    elif sim_config.sim_rebalance == "dont-rebalance":
        buckets = [
            ("pre", "eq_pre", "bd_pre", "cs_pre"),
            ("post", "eq_post", "bd_post", "cs_post"),
            ("roth", "eq_roth", "bd_roth", "cs_roth"),
            ("hsa", "hsa_eq", "hsa_bd", "hsa_cs"),
        ]

        for bucket_name, eq_attr, bd_attr, cs_attr in buckets:
            eq_ratio = getattr(sim_portfolio, f"eq_ratio_{bucket_name}", 0.0)
            bd_ratio = getattr(sim_portfolio, f"bd_ratio_{bucket_name}", 0.0)
            cs_ratio = getattr(sim_portfolio, f"cs_ratio_{bucket_name}", 0.0)

            if eq_ratio + bd_ratio + cs_ratio <= 1e-12:
                continue

            _rebalance_three_asset_bucket(
                sim_portfolio,
                eq_attr,
                bd_attr,
                cs_attr,
                eq_ratio,
                bd_ratio,
                cs_ratio,
            )

        return

    elif sim_config.sim_rebalance == "custom":
        eq_ratio = sim_config.custom_stock
        bd_ratio = sim_config.custom_bonds
        cs_ratio = sim_config.custom_cash

    else:
        rebalance_ratios = {
            "30-30-40": {"equity": 0.30, "bonds": 0.30, "cash": 0.40},
            "50-30-20": {"equity": 0.50, "bonds": 0.30, "cash": 0.20},
            "70-20-10": {"equity": 0.70, "bonds": 0.20, "cash": 0.10},
        }

        if sim_config.sim_rebalance not in rebalance_ratios:
            print("Bad, bad, bad in rebalance")
            return

        ratios = rebalance_ratios[sim_config.sim_rebalance]
        eq_ratio = ratios["equity"]
        bd_ratio = ratios["bonds"]
        cs_ratio = ratios["cash"]

    for eq_attr, bd_attr, cs_attr in [
        ("eq_pre", "bd_pre", "cs_pre"),
        ("eq_post", "bd_post", "cs_post"),
        ("eq_roth", "bd_roth", "cs_roth"),
        ("hsa_eq", "hsa_bd", "hsa_cs"),
    ]:
        _rebalance_three_asset_bucket(
            sim_portfolio,
            eq_attr,
            bd_attr,
            cs_attr,
            eq_ratio,
            bd_ratio,
            cs_ratio,
        )

    _clamp_portfolio_components(sim_portfolio)


def apply_net_income_proportionally(sim_portfolio, net_change):
    """
    Applies net change proportionally to sim_portfolio components.
    Note we only apply this to the after tax portfolio
    """
    total_portfolio_post = sim_portfolio.total_value_post
    if total_portfolio_post > 0:
        sim_portfolio.eq_post += net_change * (sim_portfolio.eq_post / total_portfolio_post)
        sim_portfolio.bd_post += net_change * (sim_portfolio.bd_post / total_portfolio_post)
        sim_portfolio.cs_post += net_change * (sim_portfolio.cs_post / total_portfolio_post)
    else:
        # Badness.  We didn't have initial post tax money to form ratios.  If possible, use pre.
        total_portfolio_pre = sim_portfolio.total_value_pre
        if total_portfolio_pre > 0:
            sim_portfolio.eq_post += net_change * (sim_portfolio.eq_pre / total_portfolio_pre)
            sim_portfolio.bd_post += net_change * (sim_portfolio.bd_pre / total_portfolio_pre)
            sim_portfolio.cs_post += net_change * (sim_portfolio.cs_pre / total_portfolio_pre)
        else:
            sim_portfolio.eq_post = net_change * 1/3
            sim_portfolio.bd_post = net_change * 1/3
            sim_portfolio.cs_post = net_change * 1/3

    # --- Safety clamp (diagnostic) ---
    if sim_portfolio.eq_post < 0.0:
        sim_portfolio.eq_post = 0.0

    if sim_portfolio.bd_post < 0.0:
        sim_portfolio.bd_post = 0.0

    if sim_portfolio.cs_post < 0.0:
        sim_portfolio.cs_post = 0.0

    return sim_portfolio.total_value


def apply_net_income_proportionally_pre(sim_portfolio, net_change):
    """
    Applies net change proportionally to sim_portfolio components.
    Note we only apply this to the after tax portfolio
    """
    total_portfolio_pre = sim_portfolio.total_value_pre
    if total_portfolio_pre > 0:
        sim_portfolio.eq_pre += net_change * (sim_portfolio.eq_pre / total_portfolio_pre)
        sim_portfolio.bd_pre += net_change * (sim_portfolio.bd_pre / total_portfolio_pre)
        sim_portfolio.cs_pre += net_change * (sim_portfolio.cs_pre / total_portfolio_pre)
    else:
        print("SHOULD NEVER BE HERE - apply_net_income_proportionally_pre")
        sim_portfolio.eq_pre = net_change * 1/3
        sim_portfolio.bd_pre = net_change * 1/3
        sim_portfolio.cs_pre = net_change * 1/3

    if sim_portfolio.eq_pre < 0.0:
        sim_portfolio.eq_pre = 0.0

    if sim_portfolio.bd_pre < 0.0:
        sim_portfolio.bd_pre = 0.0

    if sim_portfolio.cs_pre < 0.0:
        sim_portfolio.cs_pre = 0.0

    return sim_portfolio.total_value


def create_empty_sim_portfolio(sim_config):
    """
    Returns a zero-valued PortfolioState for disabled second person.
    """
    return PortfolioState(
        eq_pre=0.0,
        bd_pre=0.0,
        cs_pre=0.0,
        eq_post=0.0,
        bd_post=0.0,
        cs_post=0.0,
        eq_roth=0.0,
        bd_roth=0.0,
        cs_roth=0.0,
        hsa_eq=0.0,
        hsa_bd=0.0,
        hsa_cs=0.0,
        re_post=0.0,
    )


def get_pre_tax_ratios(sim_portfolio):
    """
    Returns current pre-tax allocation ratios.
    """
    total_pre = sim_portfolio.eq_pre + sim_portfolio.bd_pre + sim_portfolio.cs_pre

    if total_pre > 0:
        return {
            "equity": sim_portfolio.eq_pre / total_pre,
            "bonds": sim_portfolio.bd_pre / total_pre,
            "cash": sim_portfolio.cs_pre / total_pre,
        }

    # Fallback if portfolio is empty
    return {
        "equity": 1/3,
        "bonds": 1/3,
        "cash": 1/3,
    }

def apply_pre_tax_contribution(sim_portfolio, amount):
    """
    Applies a pre-tax contribution to a portfolio in-place.
    Allocation is proportional to existing pre-tax assets.
    """
    if amount <= 0:
        return

    total_pre = sim_portfolio.eq_pre + sim_portfolio.bd_pre + sim_portfolio.cs_pre

    if total_pre > 0:
        sim_portfolio.eq_pre += amount * (sim_portfolio.eq_pre / total_pre)
        sim_portfolio.bd_pre += amount * (sim_portfolio.bd_pre / total_pre)
        sim_portfolio.cs_pre += amount * (sim_portfolio.cs_pre / total_pre)
    else:
        sim_portfolio.eq_pre += amount * 1/3
        sim_portfolio.bd_pre += amount * 1/3
        sim_portfolio.cs_pre += amount * 1/3


def deduct_post_tax_amount(h_port, w_port, amount, sim_config):
    """
    Deduct a dollar amount from household post-tax assets.

    This is a pure asset-movement helper. It does not compute taxes.
    It removes funds proportionally from post-tax assets across the
    household and within each portfolio across eq/bd/cs post.

    Returns:
        actual_deducted (float): amount successfully removed
    """
    amount = float(max(amount, 0.0))
    if amount <= 0:
        return 0.0

    second_person_enabled = getattr(sim_config, "second_person_enabled", True)

    if h_port.total_value_post < 0.0:
        h_post = 0.0
    else:
        h_post = h_port.total_value_post

    if second_person_enabled:
        if w_port.total_value_post < 0.0:
            w_post = 0.0
        else:
            w_post = w_port.total_value_post
    else:
        w_post = 0.0

    total_post = h_post + w_post

    if total_post <= 0:
        return 0.0

    if amount <= total_post:
        to_take = amount
    else:
        to_take = total_post

    h_take = to_take * (h_post / total_post) if h_post > 0 else 0.0
    w_take = to_take - h_take if second_person_enabled else 0.0

    def deduct_from_one_port(port, take):
        take = float(max(take, 0.0))
        total = max(port.total_value_post, 0.0)
        if take <= 0 or total <= 0:
            return 0.0

        if take <= total:
            actual = take
        else:
            actual = total

        ratio = actual / total

        port.eq_post -= port.eq_post * ratio
        port.bd_post -= port.bd_post * ratio
        port.cs_post -= port.cs_post * ratio

        # safety clamp
        if port.eq_post < 0.0:
            port.eq_post = 0.0

        if port.bd_post < 0.0:
            port.bd_post = 0.0

        if port.cs_post < 0.0:
            port.cs_post = 0.0

        return actual

    deducted = 0.0
    deducted += deduct_from_one_port(h_port, h_take)

    if second_person_enabled:
        deducted += deduct_from_one_port(w_port, w_take)

    return deducted

    
def _withdraw_from_bucket(port, amount, bucket):
    amount = float(max(amount, 0.0))
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
        raise ValueError(f"Unknown bucket: {bucket}")

    total = max(total, 0.0)
    if total <= 0.0:
        return 0.0

    take = min(amount, total)
    ratio = take / total

    for attr in attrs:
        setattr(port, attr, getattr(port, attr) - getattr(port, attr) * ratio)

    _clamp_portfolio_components(port)

    return take


# NOTE ON PRE-TAX WITHDRAWALS
# ---------------------------
# These net-income functions move assets only.
# If a deficit requires drawing from pre-tax assets, the functions return the
# gross pre-tax amount withdrawn.
#
# Taxes on that pre-tax withdrawal are NOT estimated here.
# They are computed later in run_sim_core.py by adding the gross withdrawal
# into ordinary income and then running the tax engine.
#
# This uses a one-pass approximation:
#   1. determine cash deficit and gross asset withdrawals
#   2. compute/recompute taxes using the gross pre-tax withdrawal
#
# This avoids embedding tax law assumptions inside portfolioEngine.

def apply_net_income_couple(h_port, w_port, net_cash):
    result = {
        "post_tax_used": 0.0,
        "pre_tax_used": 0.0,
        "roth_used": 0.0,
        "hsa_used": 0.0,
        "uncovered": 0.0,
    }

    if net_cash >= 0:
        half = net_cash / 2
        h_port.eq_post += half
        w_port.eq_post += half
        return result

    deficit = -net_cash

    def household_total(bucket):
        if bucket == "post":
            return h_port.total_value_post + w_port.total_value_post
        if bucket == "pre":
            return h_port.total_value_pre + w_port.total_value_pre
        if bucket == "roth":
            return h_port.total_value_roth + w_port.total_value_roth
        if bucket == "hsa":
            return h_port.total_value_hsa + w_port.total_value_hsa
        raise ValueError(f"Unknown bucket: {bucket}")

    def port_total(port, bucket):
        if bucket == "post":
            return port.total_value_post
        if bucket == "pre":
            return port.total_value_pre
        if bucket == "roth":
            return port.total_value_roth
        if bucket == "hsa":
            return port.total_value_hsa
        raise ValueError(f"Unknown bucket: {bucket}")

    for bucket, result_key in [
        ("post", "post_tax_used"),
        ("pre", "pre_tax_used"),
        ("roth", "roth_used"),
        ("hsa", "hsa_used"),
    ]:
        if deficit <= 0.0:
            break

        total = household_total(bucket)
        if total <= 0.0:
            continue

        use_amount = min(deficit, total)

        h_total = port_total(h_port, bucket)
        w_total = port_total(w_port, bucket)

        h_use = use_amount * (h_total / total) if h_total > 0.0 else 0.0
        w_use = use_amount - h_use if w_total > 0.0 else 0.0

        actually_used = 0.0
        actually_used += _withdraw_from_bucket(h_port, h_use, bucket)
        actually_used += _withdraw_from_bucket(w_port, w_use, bucket)

        result[result_key] += actually_used
        deficit -= actually_used

    if deficit > 0.0:
        result["uncovered"] = deficit

    _clamp_portfolio_components(h_port)
    _clamp_portfolio_components(w_port)

    return result


def apply_net_income_single(port, net_cash):
    result = {
        "post_tax_used": 0.0,
        "pre_tax_used": 0.0,
        "roth_used": 0.0,
        "hsa_used": 0.0,
        "uncovered": 0.0,
    }

    if net_cash >= 0:
        port.eq_post += net_cash
        return result

    deficit = -net_cash

    for bucket, result_key in [
        ("post", "post_tax_used"),
        ("pre", "pre_tax_used"),
        ("roth", "roth_used"),
        ("hsa", "hsa_used"),
    ]:
        if deficit <= 0.0:
            break

        used = _withdraw_from_bucket(port, deficit, bucket)
        result[result_key] += used
        deficit -= used

    if deficit > 0.0:
        result["uncovered"] = deficit

    _clamp_portfolio_components(port)

    return result  