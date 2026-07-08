# statsCollector.py

import numpy as np

# ----------------------------
# Actual Stats Collector Function
# ----------------------------

def compute_portfolio_statistics(total_results, years, inflation_rate):
    """
    Compute median, 10th percentile, 90th percentile
    for a portfolio over time.

    Args:
        total_results (ndarray): 2D array with shape (num_sims, years + 1)
        years (int): Number of years in the simulation
        inflation_rate (float): Annual inflation rate

    Returns:
        dict: A dictionary containing:
            - 'median' (ndarray)
            - 'pct10' (ndarray)
            - 'pct90' (ndarray)
            - 'real_median' (ndarray)
            - 'real_pct10' (ndarray)
            - 'real_pct90' (ndarray)
    """
    pct1  = np.percentile(total_results, 1 , axis=0)
    pct10 = np.percentile(total_results, 10, axis=0)
    pct20 = np.percentile(total_results, 20, axis=0)
    pct30 = np.percentile(total_results, 30, axis=0)
    pct40 = np.percentile(total_results, 40, axis=0)
    median = np.median(total_results, axis=0)
    pct60 = np.percentile(total_results, 60, axis=0)
    pct70 = np.percentile(total_results, 70, axis=0)
    pct80 = np.percentile(total_results, 80, axis=0)
    pct90 = np.percentile(total_results, 90, axis=0)
    pct99 = np.percentile(total_results, 99, axis=0)

    # Debug print
    # print('total_results: '+str(total_results)+' median: '+str(median)+' real_median: '+str(real_median)+'\n')

    return {
        'pct1':  pct1,
        'pct10': pct10,
        'pct20': pct20,
        'pct30': pct30,
        'pct40': pct40,
        'median': median,
        'pct60': pct60,
        'pct70': pct70,
        'pct80': pct80,
        'pct90': pct90,
        'pct99': pct99,
    }

def optional_stats(results, years, inflation_rate, enabled=True):

    if not enabled or results is None:
        return None

    stats = compute_portfolio_statistics(results, years, inflation_rate)
    return stats['median']

def aggregate_year_end_values(sim_h, sim_w, config):
    # Total portfolio (H + W)
    total_value = sim_h.total_value
    cash_value  = sim_h.cs_pre + sim_h.cs_post
    bonds_value = sim_h.bd_pre + sim_h.bd_post

    realestate_value = 0
    if config.include_realestate:
        realestate_value = sim_h.re_post

    if config.second_person_enabled:
        total_value += sim_w.total_value
        cash_value  += sim_w.cs_pre + sim_w.cs_post
        bonds_value += sim_w.bd_pre + sim_w.bd_post

        if config.include_realestate:
            realestate_value += sim_w.re_post

    # Add real estate to total_value
    total_value += realestate_value

    return total_value, cash_value, bonds_value, realestate_value


