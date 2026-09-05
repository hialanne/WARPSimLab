# run_sim_core.py

import numpy as np

from .engines import (
    portfolioEngine,
    incomeEngine,
    withdrawalEngine,
    expenseEngine,
    taxEngine,
    monteCarloEngine,
    rothEngine,
    diagnosticEngine,
)
from .run_sim_core_expenses import simulate_expense_year
from .run_sim_core_withdrawals import simulate_withdrawal_year

PROFILE_SIMULATION = False
DEBUG_SIMULATION = False


def _find_first_withdrawal_year(sim_config, husband, wife, years_to_simulate):
    """
    Option B anchor helper.

    We define the first withdrawal year as the first simulation year where
    the simulator stops using expense mode and begins using retirement
    withdrawal mode, based on withdrawalEngine.use_expenses_this_year().

    Returns
    -------
    int or None
        First withdrawal simulation-year index, or None if the simulation
        never enters withdrawal mode within the modeled horizon.
    """
    for year in range(1, years_to_simulate + 1):
        use_expenses = withdrawalEngine.use_expenses_this_year(
            sim_config, husband, wife, year
        )
        if not use_expenses:
            return year
    return None

def simulate_yearly_portfolios(
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    sim_config,
    num_sims
):
    """
    Core simulation engine for portfolio, summary, or income simulations.
    
    Returns:
        results: dict containing arrays/lists for each tracked quantity.
            Keys:
                - total_assets
                - pre_tax_assets
                - post_tax_assets
                - cash
                - bonds
                - real_estate
                - net_income
                - net_profit
                - breakdown_by_class
                - net_income_husband
                - net_income_wife
                - taxes
    """

    #print("DEBUG tax_filing_status:", sim_config.tax_filing_status)
    #print("DEBUG second_person_enabled:", sim_config.second_person_enabled)

    #print('num_sims: '+str(num_sims))
    years_to_simulate = sim_config.years_to_simulate
    second_person_enabled = sim_config.second_person_enabled

    monte_carlo_mode = getattr(sim_config, "monte_carlo_mode", "pathBasedAnnualSampling")

    historical_window_mode_active = (
        sim_config.subplot_mode == "monte_carlo"
        and sim_config.sim_type == "portfolio_sim"
        and monte_carlo_mode == "rollingHistoricalWindows"
    )

    # Historical rolling-window mode uses one simulation per valid window.
    # Ignore the incoming num_sims in that mode.
    effective_num_sims = num_sims

    withdrawal_start_year = _find_first_withdrawal_year(
        sim_config,
        husband,
        wife,
        years_to_simulate,
    )

    monteCarloEngine.prepare_market_path_sampling(sim_config)
    
    if historical_window_mode_active:
        effective_num_sims = int(getattr(sim_config, "_hist_num_windows", 0))
        if effective_num_sims <= 0:
            diagnosticEngine.raise_internal_error("Historical rolling-window mode prepared zero windows.", sim_config,
                                                  context={"effective_num_sims": effective_num_sims,
                                                           "years_to_simulate": years_to_simulate})

    expenseEngine.initialize_expense_engine_for_simulation(sim_config)

    # ---------------------------------------------------------
    # Compute household allocation target if using
    # "maintain-current-allocation"
    # ---------------------------------------------------------
    if sim_config.sim_initial_allocation_mode == "maintain-current-allocation":
        portfolioEngine.compute_household_allocation_targets(
            husband_portfolio,
            wife_portfolio,
            sim_config
        )

    # --------------------------
    # Initialize results containers
    # --------------------------
    results = {
        "year": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "total_assets": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "pre_tax_assets": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "post_tax_assets": np.zeros((effective_num_sims, years_to_simulate + 1)),
        
        "pre_tax_equity": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "pre_tax_bonds": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "pre_tax_cash": np.zeros((effective_num_sims, years_to_simulate + 1)),

        "post_tax_equity": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "post_tax_bonds": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "post_tax_cash": np.zeros((effective_num_sims, years_to_simulate + 1)),

        "roth_equity": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "roth_bonds": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "roth_cash": np.zeros((effective_num_sims, years_to_simulate + 1)),

        "hsa_equity": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "hsa_bonds": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "hsa_cash": np.zeros((effective_num_sims, years_to_simulate + 1)),

        "cash": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "bonds": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "real_estate": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "gross_income": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "net_income": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "net_profit": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "taxes": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "tax_bracket": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "pre_tax_withdrawals": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "roth_withdrawals": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "hsa_qualified_withdrawals": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "hsa_taxable_withdrawals": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "hsa_withdrawals": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "expense_amt": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "uncovered_expense": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "cash_flow_shortfall": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "ira_401k": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "rmd_husband": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "rmd_wife": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "employee_401k_contributions": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "hsa_employee_contributions": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "hsa_employer_contributions": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "hsa_total_contributions": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "roth_ira_contributions": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "roth_workplace_contributions": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "roth_conversions": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "roth_total_flows": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "roth_assets": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "hsa_assets": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "fund_expenses": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "breakdown_by_class": {
            k: np.zeros((effective_num_sims, years_to_simulate + 1))
            for k in [
                "work",
                "pension",
                "annuity",
                "ss",
                "rmd",
                "withdrawal",
                "tax_funding_withdrawal",
                "bond_interest",
                "cash_interest",
                "qualified_equity_distributions",
                "special_income",
                "roth_conversion",
            ]
        },

        "net_income_husband": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "net_income_wife": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "bond_interest": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "cash_interest": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "qualified_equity_distributions": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "federal_ordinary_tax": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "federal_qualified_dividend_tax": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "payroll_tax": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "social_security_payroll_tax": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "medicare_tax": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "additional_medicare_tax": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "state_income_tax": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "emergency_pre_tax_used": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "final_tax_delta": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "final_tax_delta_deducted": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "final_tax_delta_uncovered": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "sequence_risk_active": np.zeros((effective_num_sims,), dtype=bool),
        "sequence_risk_start_year": np.full((effective_num_sims,), -1, dtype=int),
        "sequence_risk_end_year": np.full((effective_num_sims,), -1, dtype=int), 
        
        "historical_window_start_year": np.full((effective_num_sims,), -1, dtype=int),
        "historical_window_end_year": np.full((effective_num_sims,), -1, dtype=int),
    }

    sim_config._post_tax_equity_dividend_yield = max(
        0.0,
        float(getattr(sim_config, "post_tax_equity_dividend_yield", 0.0)),
    )
    sim_config._post_tax_bond_interest_yield = max(
        0.0,
        float(getattr(sim_config, "post_tax_bond_interest_yield", 0.0)),
    )
    sim_config._post_tax_cash_interest_yield = max(
        0.0,
        float(getattr(sim_config, "post_tax_cash_interest_yield", 0.0)),
    )

    real_discount_factors = np.ones((effective_num_sims, years_to_simulate + 1), dtype=float)

    if PROFILE_SIMULATION:
        import cProfile
        import pstats

        profiler = cProfile.Profile()
        profiler.enable()

    # --------------------------
    # Simulation loop
    # --------------------------
    for s in range(effective_num_sims):
        # Initialize portfolios
        h_port = portfolioEngine.create_sim_portfolio(husband_portfolio, sim_config)
        if second_person_enabled:
            w_port = portfolioEngine.create_sim_portfolio(wife_portfolio, sim_config)
        else:
            w_port = portfolioEngine.create_empty_sim_portfolio(sim_config)

        if historical_window_mode_active:
            sim_config._active_historical_sim_index = s
        else:
            sim_config._active_historical_sim_index = None

        # Rebuild inflation-driven caches for the active simulation path/window.
        taxEngine.initialize_tax_engine_for_simulation(sim_config)
        incomeEngine.initialize_income_engine_for_simulation(husband, wife, sim_config)
        expenseEngine.initialize_expense_engine_for_simulation(sim_config)
        rothEngine.initialize_roth_engine_for_simulation(sim_config, husband, wife)

        # Optional but recommended: reset per-simulation cached withdrawal base.
        sim_config._ret_withdraw_base_dollars = None
        
        market_path = monteCarloEngine.generate_market_path(
            sim_config,
            years_to_simulate,
            sim_index=s,
        )

        historical_mode_disables_sequence_risk = (
            historical_window_mode_active
            and bool(getattr(sim_config, "disable_sequence_risk_for_historical", True))
        )

        if historical_mode_disables_sequence_risk:
            sequence_risk_meta = {
                "enabled": bool(getattr(sim_config, "sequence_risk_enabled", False)),
                "applied": False,
                "start_year": None,
                "end_year": None,
                "length_years": 0,
                "timing": getattr(sim_config, "sequence_risk_timing", "None"),
                "depth": getattr(sim_config, "sequence_risk_depth", "Moderate"),
            }
        else:
            market_path, sequence_risk_meta = monteCarloEngine.apply_sequence_risk_overlay(
                market_path=market_path,
                sim_config=sim_config,
                years_to_simulate=years_to_simulate,
                withdrawal_start_year=withdrawal_start_year,
            )

        historical_window_mode_active = (
            sim_config.subplot_mode == "monte_carlo"
            and sim_config.sim_type == "portfolio_sim"
            and monte_carlo_mode == "rollingHistoricalWindows"
        )

        if historical_window_mode_active:
            start_idx = int(sim_config._hist_window_start_indices[s])
            end_idx = start_idx + years_to_simulate - 1

            results["historical_window_start_year"][s] = int(sim_config._hist_years[start_idx])
            results["historical_window_end_year"][s] = int(sim_config._hist_years[end_idx])

        results["sequence_risk_active"][s] = sequence_risk_meta["applied"]
        results["sequence_risk_start_year"][s] = (
            sequence_risk_meta["start_year"]
            if sequence_risk_meta["start_year"] is not None else -1
        )
        results["sequence_risk_end_year"][s] = (
            sequence_risk_meta["end_year"]
            if sequence_risk_meta["end_year"] is not None else -1
        )

        if sim_config.plot_mode == "real":
            if historical_window_mode_active:
                real_discount_factors[s, :] = monteCarloEngine.build_historical_inflation_factor_path(
                    sim_config=sim_config,
                    years_to_simulate=years_to_simulate,
                    sim_index=s,
                )
            else:
                real_discount_factors[s, :] = np.array(
                    [(1.0 + sim_config.inflation_rate) ** t for t in range(years_to_simulate + 1)],
                    dtype=float,
                )

        # Year 0 - initial state
        results["year"][s,0] = sim_config.start_year
        results["total_assets"][s,0] = h_port.total_value + (w_port.total_value if second_person_enabled else 0) + \
                                       (h_port.re_post + (w_port.re_post if second_person_enabled else 0) if sim_config.include_realestate else 0)
        results["pre_tax_assets"][s,0] = h_port.total_value_pre + (w_port.total_value_pre if second_person_enabled else 0)

        results["pre_tax_equity"][s,0] = (h_port.eq_pre + (w_port.eq_pre if second_person_enabled else 0))
        results["pre_tax_bonds"][s,0] = (h_port.bd_pre + (w_port.bd_pre if second_person_enabled else 0))
        results["pre_tax_cash"][s,0] = (h_port.cs_pre + (w_port.cs_pre if second_person_enabled else 0))

        results["post_tax_equity"][s,0] = (h_port.eq_post + (w_port.eq_post if second_person_enabled else 0))
        results["post_tax_bonds"][s,0] = (h_port.bd_post + (w_port.bd_post if second_person_enabled else 0))
        results["post_tax_cash"][s,0] = (h_port.cs_post + (w_port.cs_post if second_person_enabled else 0))

        results["roth_equity"][s,0] = (h_port.eq_roth + (w_port.eq_roth if second_person_enabled else 0))
        results["roth_bonds"][s,0] = (h_port.bd_roth + (w_port.bd_roth if second_person_enabled else 0))
        results["roth_cash"][s,0] = (h_port.cs_roth+ (w_port.cs_roth if second_person_enabled else 0)) 

        results["hsa_equity"][s,0] = (h_port.hsa_eq + (w_port.hsa_eq if second_person_enabled else 0))
        results["hsa_bonds"][s,0] = (h_port.hsa_bd + (w_port.hsa_bd if second_person_enabled else 0))
        results["hsa_cash"][s,0] = (h_port.hsa_cs + (w_port.hsa_cs if second_person_enabled else 0))
        
        results["post_tax_assets"][s,0] = h_port.total_value_post + (w_port.total_value_post if second_person_enabled else 0)

        results["roth_assets"][s,0] = h_port.total_value_roth + (w_port.total_value_roth if second_person_enabled else 0)
        results["hsa_assets"][s,0] = h_port.total_value_hsa + (w_port.total_value_hsa if second_person_enabled else 0)
        results["cash"][s,0] = h_port.total_value_cash + (w_port.total_value_cash if second_person_enabled else 0)
        results["bonds"][s,0] = h_port.total_value_bonds + (w_port.total_value_bonds if second_person_enabled else 0)
        results["real_estate"][s,0] = h_port.re_post + (w_port.re_post if second_person_enabled else 0)

        sim_config._ret_withdraw_base_dollars = None
        sim_config._ret_withdraw_base_year = None

        # Years 1..N
        for year in range(1, years_to_simulate + 1):
            year_cache = taxEngine.prepare_tax_year_cache(year, sim_config)
            
            curr_h_age = husband.age + year
            curr_w_age = wife.age + year if second_person_enabled else 0

            use_expenses = withdrawalEngine.use_expenses_this_year(sim_config, husband, wife, year)

            year_returns = {
                "eq": market_path["eq"][year],
                "bd": market_path["bd"][year],
                "cs": market_path["cs"][year],
                "re": market_path["re"][year],
            }

            if use_expenses:
                model_result = simulate_expense_year(
                    h_port,
                    w_port,
                    husband,
                    wife,
                    expenses,
                    sim_config,
                    year,
                    year_cache,
                    curr_h_age,
                    curr_w_age,
                    year_returns,
                    second_person_enabled,
                )
            else:
                model_result = simulate_withdrawal_year(
                    h_port,
                    w_port,
                    husband,
                    wife,
                    sim_config,
                    year,
                    year_cache,
                    curr_h_age,
                    curr_w_age,
                    year_returns,
                    second_person_enabled,
                )

            income = model_result["income"]

            gross_income = model_result["gross_income"]
            net_income = model_result["net_income"]
            net_profit = model_result["net_profit"]
            net_income_husband = model_result["net_income_husband"]
            net_income_wife = model_result["net_income_wife"]

            total_tax = model_result["total_tax"]
            federal_marginal_rate = model_result["federal_marginal_rate"]
            federal_ordinary_tax = model_result["federal_ordinary_tax"]
            federal_qualified_dividend_tax = model_result["federal_qualified_dividend_tax"]
            state_income_tax = model_result["state_income_tax"]

            payroll_tax = model_result["payroll_tax"]
            social_security_payroll_tax = model_result["social_security_payroll_tax"]
            medicare_tax = model_result["medicare_tax"]
            additional_medicare_tax = model_result["additional_medicare_tax"]

            expense_amt = model_result["expense_amt"]
            uncovered_expense = model_result["uncovered_expense"]
            cash_flow_shortfall = model_result["cash_flow_shortfall"]

            rmd_h = model_result["rmd_h"]
            rmd_w = model_result["rmd_w"]

            pre_tax_withdrawal = model_result["pre_tax_withdrawal"]
            wd_roth = model_result["wd_roth"]
            wd_hsa = model_result["wd_hsa"]
            qualified_hsa_withdrawal = model_result["qualified_hsa_withdrawal"]
            taxable_hsa_withdrawal = model_result["taxable_hsa_withdrawal"]
            emergency_pre_tax_used = model_result["emergency_pre_tax_used"]

            ira_401k = model_result["ira_401k"]
            employee_401k_total = model_result["employee_401k_total"]
            hsa_employee_total = model_result["hsa_employee_total"]
            hsa_employer_total = model_result["hsa_employer_total"]
            hsa_total_contributions = model_result["hsa_total_contributions"]

            funded_roth_contributions = model_result["funded_roth_contributions"]
            roth_conversion_total = model_result["roth_conversion_total"]

            bond_interest = model_result["bond_interest"]
            cash_interest = model_result["cash_interest"]
            qualified_equity_distributions = model_result["qualified_equity_distributions"]

            fund_expenses = model_result["fund_expenses"]

            final_tax_delta = model_result["final_tax_delta"]
            final_tax_delta_deducted = model_result["final_tax_delta_deducted"]
            final_tax_delta_uncovered = model_result["final_tax_delta_uncovered"]

            if DEBUG_SIMULATION:
                if s == 0 and year >= years_to_simulate - 2:
                    print("")
                    print("DEBUG FINAL YEARS")
                    print("year index:", year)
                    print("calendar year:", sim_config.start_year + year)
                    print("husband age:", curr_h_age)
                    print("use_expenses:", use_expenses)
                    print("income total:", income["total"])
                    print("income by class:", income["by_class"])
                    print("gross work income:", income["by_class"].get("work", 0.0))
                    print("bond interest:", bond_interest)
                    print("cash interest:", cash_interest)
                    print("qualified equity distributions:", qualified_equity_distributions)
                    print("emergency pre-tax:", emergency_pre_tax_used)
                    print("federal ordinary tax:", federal_ordinary_tax)
                    print("federal qualified tax:", federal_qualified_dividend_tax)
                    print("state tax:", state_income_tax)
                    print("payroll tax:", payroll_tax)
                    print("total tax:", total_tax)

            # Store results
            total_assets = h_port.total_value + (w_port.total_value if second_person_enabled else 0) + \
                           (h_port.re_post + (w_port.re_post if second_person_enabled else 0) if sim_config.include_realestate else 0)
            pre_tax = h_port.total_value_pre + (w_port.total_value_pre if second_person_enabled else 0)
            post_tax = h_port.total_value_post + (w_port.total_value_post if second_person_enabled else 0)
            roth = h_port.total_value_roth + (w_port.total_value_roth if second_person_enabled else 0)
            hsa = h_port.total_value_hsa + (w_port.total_value_hsa if second_person_enabled else 0)

            pre_tax_equity = (h_port.eq_pre + (w_port.eq_pre if second_person_enabled else 0))
            pre_tax_bonds = (h_port.bd_pre + (w_port.bd_pre if second_person_enabled else 0))
            pre_tax_cash = (h_port.cs_pre + (w_port.cs_pre if second_person_enabled else 0))

            post_tax_equity = (h_port.eq_post + (w_port.eq_post if second_person_enabled else 0))
            post_tax_bonds = (h_port.bd_post + (w_port.bd_post if second_person_enabled else 0))
            post_tax_cash = (h_port.cs_post + (w_port.cs_post if second_person_enabled else 0))

            roth_equity = (h_port.eq_roth + (w_port.eq_roth if second_person_enabled else 0))
            roth_bonds = (h_port.bd_roth + (w_port.bd_roth if second_person_enabled else 0))
            roth_cash = (h_port.cs_roth + (w_port.cs_roth if second_person_enabled else 0))

            hsa_equity = (h_port.hsa_eq + (w_port.hsa_eq if second_person_enabled else 0))
            hsa_bonds = (h_port.hsa_bd + (w_port.hsa_bd if second_person_enabled else 0))
            hsa_cash = (h_port.hsa_cs + (w_port.hsa_cs if second_person_enabled else 0))

            cash = h_port.total_value_cash + (w_port.total_value_cash if second_person_enabled else 0)
            bonds = h_port.total_value_bonds + (w_port.total_value_bonds if second_person_enabled else 0)
            real_estate = h_port.re_post + (w_port.re_post if second_person_enabled else 0)

            #print("income-net: "+str(net_income))
            #print("income-total: "+str(income["total"]))
            #print("ira_401k: "+str(ira_401k))
            #print("emergency_pre_tax_used: "+str(emergency_pre_tax_used))


            results["year"][s,year] = sim_config.start_year + year
            results["total_assets"][s,year] = total_assets
            results["pre_tax_assets"][s,year] = pre_tax
            results["post_tax_assets"][s,year] = post_tax

            results["pre_tax_equity"][s,year] = pre_tax_equity
            results["pre_tax_bonds"][s,year] = pre_tax_bonds
            results["pre_tax_cash"][s,year] = pre_tax_cash

            results["post_tax_equity"][s,year] = post_tax_equity
            results["post_tax_bonds"][s,year] = post_tax_bonds
            results["post_tax_cash"][s,year] = post_tax_cash

            results["roth_equity"][s,year] = roth_equity
            results["roth_bonds"][s,year] = roth_bonds
            results["roth_cash"][s,year] = roth_cash

            results["hsa_equity"][s,year] = hsa_equity
            results["hsa_bonds"][s,year] = hsa_bonds
            results["hsa_cash"][s,year] = hsa_cash

            results["roth_assets"][s,year] = roth
            results["hsa_assets"][s,year] = hsa
            results["cash"][s,year] = cash
            results["bonds"][s,year] = bonds
            results["real_estate"][s,year] = real_estate
            results["gross_income"][s,year] = gross_income
            results["net_income"][s,year] = net_income
            results["net_profit"][s,year] = net_profit
            results["taxes"][s,year] = total_tax
            results["tax_bracket"][s,year] = federal_marginal_rate
            results["expense_amt"][s,year] = expense_amt
            results["uncovered_expense"][s, year] = uncovered_expense
            results["cash_flow_shortfall"][s, year] = cash_flow_shortfall
            results["ira_401k"][s, year] = ira_401k
            results["employee_401k_contributions"][s, year] = employee_401k_total
            results["hsa_employee_contributions"][s, year] = hsa_employee_total
            results["hsa_employer_contributions"][s, year] = hsa_employer_total
            results["hsa_total_contributions"][s, year] = hsa_total_contributions

            results["roth_ira_contributions"][s, year] = (
                funded_roth_contributions[
                    rothEngine.ROTH_IRA_CONTRIBUTION
                ]["total"]
            )

            results["roth_workplace_contributions"][s, year] = (
                funded_roth_contributions[
                    rothEngine.ROTH_WORKPLACE_CONTRIBUTION
                ]["total"]
            )

            results["roth_conversions"][s, year] = (
                roth_conversion_total
            )

            results["roth_total_flows"][s, year] = (
                funded_roth_contributions["total"]
                + roth_conversion_total
            )

            results["rmd_husband"][s, year] = rmd_h
            results["rmd_wife"][s, year] = rmd_w
            results["fund_expenses"][s, year] = fund_expenses            
            results["bond_interest"][s, year] = bond_interest
            results["cash_interest"][s, year] = cash_interest
            results["qualified_equity_distributions"][s, year] = qualified_equity_distributions
            results["federal_ordinary_tax"][s,year] = federal_ordinary_tax
            results["federal_qualified_dividend_tax"][s,year] = federal_qualified_dividend_tax
            results["payroll_tax"][s,year] = payroll_tax
            results["social_security_payroll_tax"][s,year] = social_security_payroll_tax
            results["medicare_tax"][s,year] = medicare_tax
            results["additional_medicare_tax"][s,year] = additional_medicare_tax
            results["state_income_tax"][s,year] = state_income_tax
            results["emergency_pre_tax_used"][s,year] = emergency_pre_tax_used
            results["pre_tax_withdrawals"][s, year] = pre_tax_withdrawal
            results["roth_withdrawals"][s, year] = wd_roth
            results["hsa_withdrawals"][s, year] = wd_hsa
            results["hsa_qualified_withdrawals"][s, year] = qualified_hsa_withdrawal
            results["hsa_taxable_withdrawals"][s, year] = taxable_hsa_withdrawal
            results["final_tax_delta"][s,year] = final_tax_delta
            results["final_tax_delta_deducted"][s,year] = final_tax_delta_deducted
            results["final_tax_delta_uncovered"][s,year] = final_tax_delta_uncovered

            # Breakdown by class
            for key in results["breakdown_by_class"]:
                results["breakdown_by_class"][key][s, year] = (
                    income["by_class"][key]
                )
            results["net_income_husband"][s, year] = net_income_husband
            results["net_income_wife"][s, year] = net_income_wife

    # print('total_assets: '+str(results["total_assets"][0]))

    if PROFILE_SIMULATION:
        profiler.disable()

        stats = pstats.Stats(profiler)
        stats.sort_stats("cumulative").print_stats(40)

    # --------------------------
    # Deflate arrays if real dollars requested
    # --------------------------
    if sim_config.plot_mode == "real":
        discount_factors = real_discount_factors
        #print('total_assets: '+str(results["total_assets"][0])+' discount_factors: '+str(discount_factors))

        results["total_assets"]         = results["total_assets"]       / discount_factors
        results["pre_tax_assets"]       = results["pre_tax_assets"]     / discount_factors
        results["post_tax_assets"]      = results["post_tax_assets"]    / discount_factors
        
        results["pre_tax_equity"]       = results["pre_tax_equity"]     / discount_factors
        results["pre_tax_bonds"]        = results["pre_tax_bonds"]      / discount_factors
        results["pre_tax_cash"]         = results["pre_tax_cash"]       / discount_factors

        results["post_tax_equity"]      = results["post_tax_equity"]    / discount_factors
        results["post_tax_bonds"]       = results["post_tax_bonds"]     / discount_factors
        results["post_tax_cash"]        = results["post_tax_cash"]      / discount_factors

        results["roth_equity"]          = results["roth_equity"]        / discount_factors
        results["roth_bonds"]           = results["roth_bonds"]         / discount_factors
        results["roth_cash"]            = results["roth_cash"]          / discount_factors
        results["roth_assets"]          = results["roth_assets"]        / discount_factors

        results["hsa_equity"]           = results["hsa_equity"]         / discount_factors
        results["hsa_bonds"]            = results["hsa_bonds"]          / discount_factors
        results["hsa_cash"]             = results["hsa_cash"]           / discount_factors
        results["hsa_assets"]           = results["hsa_assets"]         / discount_factors
        results["cash"]                 = results["cash"]               / discount_factors
        results["bonds"]                = results["bonds"]              / discount_factors
        results["real_estate"]          = results["real_estate"]        / discount_factors
        results["net_income"]           = results["net_income"]         / discount_factors
        results["net_income_husband"]   = (results["net_income_husband"] / discount_factors)
        results["net_income_wife"]      = (results["net_income_wife"]   / discount_factors)
        results["gross_income"]         = results["gross_income"]       / discount_factors
        results["net_profit"]           = results["net_profit"]         / discount_factors
        results["taxes"]                = results["taxes"]              / discount_factors
        results["expense_amt"]          = results["expense_amt"]        / discount_factors
        results["uncovered_expense"]    = (results["uncovered_expense"] / discount_factors)
        results["ira_401k"]             = results["ira_401k"]           / discount_factors
        results["employee_401k_contributions"] = (
            results["employee_401k_contributions"]
            / discount_factors
        )
        results["roth_ira_contributions"] = (
            results["roth_ira_contributions"] / discount_factors
        )
        results["roth_workplace_contributions"] = (
            results["roth_workplace_contributions"] / discount_factors
        )
        results["roth_conversions"] = (
            results["roth_conversions"] / discount_factors
        )
        results["roth_total_flows"] = (
            results["roth_total_flows"] / discount_factors
        )
        results["hsa_employee_contributions"] = (
            results["hsa_employee_contributions"] / discount_factors
        )
        results["hsa_employer_contributions"] = (
            results["hsa_employer_contributions"] / discount_factors
        )
        results["hsa_total_contributions"] = (
            results["hsa_total_contributions"] / discount_factors
        )
        results["rmd_husband"] = results["rmd_husband"] / discount_factors
        results["rmd_wife"] = results["rmd_wife"] / discount_factors
        results["fund_expenses"]        = results["fund_expenses"]      / discount_factors
        results["bond_interest"]        = results["bond_interest"]      / discount_factors
        results["cash_interest"]        = results["cash_interest"]      / discount_factors
        results["qualified_equity_distributions"]  = results["qualified_equity_distributions"] / discount_factors

        results["federal_ordinary_tax"] = results["federal_ordinary_tax"] / discount_factors
        results["federal_qualified_dividend_tax"] = results["federal_qualified_dividend_tax"] / discount_factors
        results["state_income_tax"]     = results["state_income_tax"]   / discount_factors
        results["payroll_tax"] = results["payroll_tax"] / discount_factors
        results["social_security_payroll_tax"] = results["social_security_payroll_tax"] / discount_factors
        results["medicare_tax"] = results["medicare_tax"] / discount_factors
        results["additional_medicare_tax"] = results["additional_medicare_tax"] / discount_factors
        results["emergency_pre_tax_used"] = results["emergency_pre_tax_used"] / discount_factors
        results["pre_tax_withdrawals"] = results["pre_tax_withdrawals"] / discount_factors
        results["cash_flow_shortfall"] = (results["cash_flow_shortfall"] / discount_factors)
        results["roth_withdrawals"] = (results["roth_withdrawals"] / discount_factors)
        results["hsa_withdrawals"] = (results["hsa_withdrawals"] / discount_factors)
        results["hsa_qualified_withdrawals"] = results["hsa_qualified_withdrawals"] / discount_factors
        results["hsa_taxable_withdrawals"] = results["hsa_taxable_withdrawals"] / discount_factors
        results["final_tax_delta"] = results["final_tax_delta"] / discount_factors
        results["final_tax_delta_deducted"] = results["final_tax_delta_deducted"] / discount_factors
        results["final_tax_delta_uncovered"] = results["final_tax_delta_uncovered"] / discount_factors

        results["breakdown_by_class"]["work"]     = results["breakdown_by_class"]["work"]     / discount_factors
        results["breakdown_by_class"]["pension"]  = results["breakdown_by_class"]["pension"] / discount_factors
        results["breakdown_by_class"]["annuity"]  = results["breakdown_by_class"]["annuity"] / discount_factors
        results["breakdown_by_class"]["ss"]       = results["breakdown_by_class"]["ss"]       / discount_factors
        results["breakdown_by_class"]["rmd"]      = results["breakdown_by_class"]["rmd"]      / discount_factors
        results["breakdown_by_class"]["withdrawal"] = results["breakdown_by_class"]["withdrawal"] / discount_factors
        results["breakdown_by_class"]["special_income"] = results["breakdown_by_class"]["special_income"] / discount_factors
        results["breakdown_by_class"]["bond_interest"] = (results["breakdown_by_class"]["bond_interest"] / discount_factors)
        results["breakdown_by_class"]["cash_interest"] = (results["breakdown_by_class"]["cash_interest"] / discount_factors)
        results["breakdown_by_class"]["qualified_equity_distributions"] = \
                (results["breakdown_by_class"]["qualified_equity_distributions"] / discount_factors)
        results["breakdown_by_class"]["roth_conversion"] /= discount_factors
        results["breakdown_by_class"]["tax_funding_withdrawal"] /= discount_factors
    return results


