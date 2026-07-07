# expenseEngine.py

# ----------------------------
# Expense Functions
# ----------------------------

def _build_expense_inflation_factors(sim_config):
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


def initialize_expense_engine_for_simulation(sim_config):
    """
    Precompute inflation factors for expenses.

    Stores:
        sim_config._expense_inflation_factors
    """
    sim_config._expense_inflation_factors = _build_expense_inflation_factors(sim_config)


def calculate_expenses(expenses, year, sim_config):
    if not hasattr(sim_config, "_expense_inflation_factors"):
        initialize_expense_engine_for_simulation(sim_config)

    current_year = year + sim_config.start_year

    base_expense = expenses.get_total_expense_for_year(current_year)

    # Scenario scaling (applied to the base expense before inflation)
    base_expense *= sim_config.scenario_expense_multiplier

    # Adjust for inflation over the simulation period
    expenses_infl = base_expense * sim_config._expense_inflation_factors[year]

    return expenses_infl