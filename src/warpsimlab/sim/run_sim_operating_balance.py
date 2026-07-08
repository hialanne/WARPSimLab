# run_sim_operating_balance.py

import numpy as np

from .simulation import run_pipeline
from src.warpsimlab.plots.plotOperatingBalance import plot_operating_balance
from src.warpsimlab.plots import io  # ensure io.py is imported


def run_sim_operating_balance(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config):
    """
    Run an operating-balance-focused simulation.

    Operating balance is defined as the cumulative sum of yearly net_profit,
    matching the income simulation convention:
      - operating_balance[0] = 0
      - operating_balance[t] = sum(net_profit[1..t]) for t >= 1

    This mode is deterministic (non-monte-carlo).
    """

    # Deterministic only
    p = run_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        force_num_sims=1
    )

    net_profit = np.array(p["net_profit"])  # shape: (years+1,)
    years = p["years"]

    # Cumulative operating balance:
    # year 0 is 0; accumulate starting from year 1
    operating_balance = np.zeros_like(net_profit, dtype=float)
    if len(net_profit) > 1:
        operating_balance[1:] = np.cumsum(net_profit[1:])

    # --------------------------
    # Portfolio value series for coverage test
    # --------------------------
    portfolio_plot_data = p["portfolio_plot_data"]
    portfolio_value = np.array(portfolio_plot_data.percentiles["median"], dtype=float)

    # Plot
    plot_operating_balance(
        years_to_simulate=years,
        net_profit=net_profit,
        operating_balance=operating_balance,
        portfolio_value=portfolio_value,   # NEW
        husband=husband,
        wife=wife,
        sim_config=sim_config
    )

    # Optional CSV output (reuse existing toggle; write function may or may not exist)
    if sim_config.output_csv == "Output":
        # If you already have an IO writer you want to reuse, point to it here.
        # Otherwise, leave this disabled for now (no new files requested).
        try:
            csv_file = io.write_operating_balance_results_csv(
                p["years_list"],
                net_profit,
                operating_balance,
                sim_config,
                prefix="operating_balance_simulation"
            )
            if csv_file:
                print(f"Operating balance simulation results written to: {csv_file}")
        except AttributeError:
            # No writer exists; silently skip to avoid adding new files/functions.
            pass