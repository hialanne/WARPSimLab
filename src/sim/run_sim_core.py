# run_sim_core.py

import numpy as np

from .engines import (
    portfolioEngine,
    incomeEngine,
    withdrawalEngine,
    expenseEngine,
    taxEngine,
    statsCollector,
    monteCarloEngine,
)


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
            raise RuntimeError(
                "Historical rolling-window mode prepared zero windows. "
                "Check the historical data file and years_to_simulate."
            )

    expenseEngine.initialize_expense_engine_for_simulation(sim_config)

    # ---------------------------------------------------------
    # Compute household allocation target if using
    # "maintain-current-allocation"
    # ---------------------------------------------------------
    if sim_config.sim_rebalance == "maintain-current-allocation":
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
        "cash": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "bonds": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "real_estate": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "gross_income": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "net_income": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "net_profit": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "taxes": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "tax_bracket": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "roth_withdrawals": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "hsa_withdrawals": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "expense_amt": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "ira_401k": np.zeros((effective_num_sims, years_to_simulate + 1)),
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
                "bond_interest",
                "cash_interest",
                "qualified_dividends",
                "special_income",
            ]
        },

        "net_income_husband": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "net_income_wife": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "bond_interest": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "cash_interest": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "qualified_dividends": np.zeros((effective_num_sims, years_to_simulate + 1)),
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

    import cProfile
    import pstats

    # profiler = cProfile.Profile()
    # profiler.enable()



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

            # RMDs - needed by the income engine.  However, if we are calculating withdrawals and not expenses,
            #   this gets done in the withdrawalEngine in calculate_retirement_withdrawal as part of the main withdrawal.
            if use_expenses:
                rmd_h = withdrawalEngine.calculate_rmds(h_port, husband, curr_h_age, sim_config)
                withdrawalEngine.withdraw_rmds(h_port,rmd_h) 

                rmd_w = 0
                if second_person_enabled:
                    rmd_w = withdrawalEngine.calculate_rmds(w_port, wife, curr_w_age, sim_config)
                    withdrawalEngine.withdraw_rmds(w_port,rmd_w) 
            else:
                rmd_h = withdrawalEngine.calculate_rmds(h_port, husband, curr_h_age, sim_config)
                rmd_w = 0
                if second_person_enabled:
                    rmd_w = withdrawalEngine.calculate_rmds(w_port, wife, curr_w_age, sim_config)

            # Income breakdown
            income = incomeEngine.calculate_income_breakdown(husband, wife, curr_h_age, curr_w_age, rmd_h, rmd_w, year, sim_config)

            #print("income husband at breakdown: "+str(income["by_person"]["husband"]))
            #print("income wife at breakdown: "+str(income["by_person"]["wife"]))
            #print("income-total at breakdown: "+str(income["total"]))

            (
                bond_interest,
                cash_interest,
                qualified_dividends,
                post_tax_total,
                husband_post_tax_total,
                wife_post_tax_total,
            ) = portfolioEngine.estimate_household_post_tax_income_components(
                h_port, w_port, sim_config
            )

            income["by_class"]["bond_interest"] += bond_interest
            income["by_class"]["cash_interest"] += cash_interest
            income["by_class"]["qualified_dividends"] += qualified_dividends

            income["total"] += post_tax_total

            payroll_wages_husband = max(
                0.0,
                float(income.get("work_by_person", {}).get("husband", 0.0))
            )

            payroll_wages_wife = 0.0

            if second_person_enabled:
                payroll_wages_wife = max(
                    0.0,
                    float(income.get("work_by_person", {}).get("wife", 0.0))
                )

            h_401k_employee = 0.0
            h_401k_employer = 0.0
            w_401k_employee = 0.0
            w_401k_employer = 0.0

            emergency_pre_tax_used = 0.0
            net_cash_result = None
            baseline_total_tax = 0.0
            final_tax_delta = 0.0
            final_tax_delta_deducted = 0.0
            final_tax_delta_uncovered = 0.0


            if use_expenses:
                # 401k contributions
                h_401k_employee, h_401k_employer = (
                    incomeEngine.calculate_pre_tax_401k_contributions(
                        husband, curr_h_age, year, sim_config
                    )
                )
                incomeEngine.apply_employee_401k_to_income(
                    income, h_401k_employee, "husband"
                )
                portfolioEngine.apply_pre_tax_contribution(
                    h_port, h_401k_employee + h_401k_employer
                )

                if second_person_enabled:
                    w_401k_employee, w_401k_employer = (
                        incomeEngine.calculate_pre_tax_401k_contributions(
                            wife, curr_w_age, year, sim_config
                        )
                    )
                    incomeEngine.apply_employee_401k_to_income(
                        income, w_401k_employee, "wife"
                    )
                    portfolioEngine.apply_pre_tax_contribution(
                        w_port, w_401k_employee + w_401k_employer
                    )

            #print("income-total after 401k: "+str(income["total"]))

            (
                social_security_payroll_tax,
                medicare_tax,
                additional_medicare_tax,
                payroll_tax,
            ) = taxEngine.calculate_employee_payroll_tax_split(
                husband_wages=payroll_wages_husband,
                wife_wages=payroll_wages_wife,
                year_cache=year_cache,
                sim_config=sim_config,
            )

            if use_expenses:
                expense_amt = expenseEngine.calculate_expenses(expenses, year, sim_config)
                wd_pre_tax = 0
                wd_post_tax = 0
                wd_roth = 0
                wd_hsa = 0
            else:
                wd = withdrawalEngine.calculate_retirement_withdrawal(
                    h_port, w_port, husband, wife, year, sim_config
                )
                expense_amt = 0
                wd_pre_tax = wd["pre_tax"]
                wd_post_tax = wd["post_tax"]
                wd_roth = wd.get("roth", 0.0)
                wd_hsa = wd.get("hsa", 0.0)
                wd_rmd = wd.get("rmd", 0.0)

                income["by_class"]["withdrawal"] = wd["total"]

                # RMDs are already included in income because rmd_h/rmd_w were passed
                # into incomeEngine.calculate_income_breakdown().
                #
                # Additional retirement withdrawals should appear as household cash in pocket.
                # For tax calculation, we mark them non-taxable here, then existing code
                # adds wd_pre_tax back into ordinary income.
                additional_withdrawal_cash = max(0.0, wd["total"] - wd_rmd)

                income["total"] += additional_withdrawal_cash
                income["non_taxable_income"] = income.get("non_taxable_income", 0.0) + additional_withdrawal_cash

            if qualified_dividends > (income["total"]):
                print("qualified_dividends: "+str(qualified_dividends)+ " income-total: "+str(income["total"]))
                raise RuntimeError("Qualified dividends exceed total income")

            # print("h_port: "+str(h_port.total_value))

            if use_expenses:
                # ---------------------------------------------------------
                # One-pass approximation for emergency pre-tax withdrawals
                #
                # First pass:
                #   estimate net cash using income before any emergency pre-tax draw
                #
                # Then:
                #   apply net cash to the portfolio
                #   capture any gross pre-tax amount needed to cover a deficit
                #
                # Final pass:
                #   recompute taxes including that gross emergency pre-tax withdrawal
                #
                # This avoids embedding tax assumptions inside portfolioEngine and
                # avoids an iterative tax/withdrawal loop.
                # ---------------------------------------------------------

                qualified_dividends = income["by_class"].get("qualified_dividends", 0.0)

                baseline_ordinary_income = (
                    income["total"]
                    - qualified_dividends
                    - income.get("non_taxable_income", 0.0)
                    + wd_pre_tax
                )

                (
                    baseline_federal_ordinary_tax,
                    baseline_federal_qualified_dividend_tax,
                    baseline_state_income_tax,
                    baseline_total_tax,
                    baseline_federal_marginal_rate,
                ) = taxEngine.calculate_total_income_tax_split(
                    ordinary_income=baseline_ordinary_income,
                    qualified_dividends=qualified_dividends,
                    year_cache=year_cache,
                    sim_config=sim_config
                )

                baseline_total_tax += payroll_tax

                if sim_config.calculate_income_taxes or sim_config.calculate_payroll_taxes:
                    net_cash = income["total"] - baseline_total_tax - expense_amt
                else:
                    net_cash = income["total"] - expense_amt

                # print("income total: "+str(income["total"]))
                # print("expense_amt: "+str(expense_amt))
                # print("baseline_total_tax: "+str(baseline_total_tax))

                # print("h_port before apply: "+str(h_port.total_value))

                # Apply net cash and capture any emergency gross pre-tax draw
                if second_person_enabled:
                    net_cash_result = portfolioEngine.apply_net_income_couple(h_port, w_port, net_cash)
                else:
                    net_cash_result = portfolioEngine.apply_net_income_single(h_port, net_cash)

                # print("h_port after apply: "+str(h_port.total_value))
                # This code dumps logs of portfolio if it's draining.  
                #   Should drain, in order, before tax, after tax, roth, hsa.
                #print(
                #    year,
                #    h_port.total_value_pre + w_port.total_value_pre,
                #    h_port.total_value_post + w_port.total_value_post,
                #    h_port.total_value_roth + w_port.total_value_roth,
                #    net_cash_result["uncovered"],
                #)

                emergency_pre_tax_used = net_cash_result["pre_tax_used"]

                # Recompute final taxes only if the emergency pre-tax draw changed income
                if emergency_pre_tax_used > 0.0:
                    ordinary_income = baseline_ordinary_income + emergency_pre_tax_used

                    (
                        federal_ordinary_tax,
                        federal_qualified_dividend_tax,
                        state_income_tax,
                        total_tax,
                        federal_marginal_rate,
                    ) = taxEngine.calculate_total_income_tax_split(
                        ordinary_income=ordinary_income,
                        qualified_dividends=qualified_dividends,
                        year_cache=year_cache,
                        sim_config=sim_config
                    )
                    total_tax += payroll_tax
                else:
                    ordinary_income = baseline_ordinary_income
                    federal_ordinary_tax = baseline_federal_ordinary_tax
                    federal_qualified_dividend_tax = baseline_federal_qualified_dividend_tax
                    state_income_tax = baseline_state_income_tax
                    total_tax = baseline_total_tax
                    federal_marginal_rate = baseline_federal_marginal_rate

                final_tax_delta = max(0.0, total_tax - baseline_total_tax)

                #print("tax_bracket: "+str(tax_bracket))

                # ---------------------------------------------------------
                # Deduct the extra tax created by the emergency pre-tax draw.
                #
                # One-pass approximation:
                # the portfolio was already adjusted using net_cash based on
                # baseline tax. If final tax is higher after including emergency
                # pre-tax withdrawals, remove the tax delta directly from post-tax
                # assets without triggering another tax/withdrawal iteration.
                # ---------------------------------------------------------
                if sim_config.calculate_income_taxes and final_tax_delta > 0:
                    final_tax_delta_deducted = portfolioEngine.deduct_post_tax_amount(
                        h_port,
                        w_port,
                        final_tax_delta,
                        sim_config
                    )
                    final_tax_delta_uncovered = max(0.0, final_tax_delta - final_tax_delta_deducted)
                #print("final_tax_delta_uncovered expenses"+str(final_tax_delta_uncovered))

                if final_tax_delta < -1e-9:
                    raise RuntimeError("final_tax_delta should never be negative")

                if final_tax_delta_deducted < -1e-9:
                    raise RuntimeError("final_tax_delta_deducted should never be negative")

                if final_tax_delta_uncovered < -1e-9:
                    raise RuntimeError("final_tax_delta_uncovered should never be negative")

            else:
                qualified_dividends = income["by_class"].get("qualified_dividends", 0.0)

                ordinary_income = (
                    income["total"]
                    - qualified_dividends
                    - income.get("non_taxable_income", 0.0)
                    + wd_pre_tax
                )

                (
                    federal_ordinary_tax,
                    federal_qualified_dividend_tax,
                    state_income_tax,
                    total_tax,
                    federal_marginal_rate,
                ) = taxEngine.calculate_total_income_tax_split(
                    ordinary_income=ordinary_income,
                    qualified_dividends=qualified_dividends,
                    year_cache=year_cache,
                    sim_config=sim_config
                )
                total_tax += payroll_tax

            # print("h_port: "+str(h_port.total_value))

            # Portfolio returns (shared market path)
            fund_expense_rate = sim_config.fund_expense if sim_config.use_fund_expenses else 0.0

            fund_expenses = portfolioEngine.apply_returns_and_fund_expenses(
                h_port,
                year_returns["eq"],
                year_returns["bd"],
                year_returns["cs"],
                year_returns["re"],
                fund_expense_rate,
            )

            if second_person_enabled:
                fund_expenses += portfolioEngine.apply_returns_and_fund_expenses(
                    w_port,
                    year_returns["eq"],
                    year_returns["bd"],
                    year_returns["cs"],
                    year_returns["re"],
                    fund_expense_rate,
                )

            # Rebalance if requested
            if sim_config.rebalance_every_year:
                portfolioEngine.rebalance(h_port, sim_config)
                if second_person_enabled:
                    portfolioEngine.rebalance(w_port, sim_config)

            # print("h_port: "+str(h_port.total_value))

            # Store results
            total_assets = h_port.total_value + (w_port.total_value if second_person_enabled else 0) + \
                           (h_port.re_post + (w_port.re_post if second_person_enabled else 0) if sim_config.include_realestate else 0)
            pre_tax = h_port.total_value_pre + (w_port.total_value_pre if second_person_enabled else 0)
            post_tax = h_port.total_value_post + (w_port.total_value_post if second_person_enabled else 0)
            roth = h_port.total_value_roth + (w_port.total_value_roth if second_person_enabled else 0)
            hsa = h_port.total_value_hsa + (w_port.total_value_hsa if second_person_enabled else 0)

            cash = h_port.total_value_cash + (w_port.total_value_cash if second_person_enabled else 0)
            bonds = h_port.total_value_bonds + (w_port.total_value_bonds if second_person_enabled else 0)
            real_estate = h_port.re_post + (w_port.re_post if second_person_enabled else 0)
            net_income = (
                income["total"] - total_tax
                if sim_config.calculate_income_taxes or sim_config.calculate_payroll_taxes
                else income["total"]
            )
            if sim_config.second_person_enabled:
                ira_401k = (
                    h_401k_employee + h_401k_employer +
                    w_401k_employee + w_401k_employer
                )
            else:
                ira_401k = h_401k_employee + h_401k_employer

            gross_income = income["total"] + ira_401k + emergency_pre_tax_used
            net_profit = net_income - expense_amt

            #print("income-net: "+str(net_income))
            #print("income-total: "+str(income["total"]))
            #print("ira_401k: "+str(ira_401k))
            #print("emergency_pre_tax_used: "+str(emergency_pre_tax_used))


            results["year"][s,year] = sim_config.start_year + year
            results["total_assets"][s,year] = total_assets
            results["pre_tax_assets"][s,year] = pre_tax
            results["post_tax_assets"][s,year] = post_tax
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
            results["ira_401k"][s,year] = ira_401k
            results["fund_expenses"][s,year] = fund_expenses
            results["bond_interest"][s, year] = bond_interest
            results["cash_interest"][s, year] = cash_interest
            results["qualified_dividends"][s, year] = qualified_dividends
            results["federal_ordinary_tax"][s,year] = federal_ordinary_tax
            results["federal_qualified_dividend_tax"][s,year] = federal_qualified_dividend_tax
            results["payroll_tax"][s,year] = payroll_tax
            results["social_security_payroll_tax"][s,year] = social_security_payroll_tax
            results["medicare_tax"][s,year] = medicare_tax
            results["additional_medicare_tax"][s,year] = additional_medicare_tax
            results["state_income_tax"][s,year] = state_income_tax
            results["emergency_pre_tax_used"][s,year] = emergency_pre_tax_used
            results["roth_withdrawals"][s, year] = wd_roth
            results["hsa_withdrawals"][s, year] = wd_hsa
            results["final_tax_delta"][s,year] = final_tax_delta
            results["final_tax_delta_deducted"][s,year] = final_tax_delta_deducted
            results["final_tax_delta_uncovered"][s,year] = final_tax_delta_uncovered

            # Breakdown by class
            for key in results["breakdown_by_class"]:
                results["breakdown_by_class"][key][s,year] = income["by_class"][key]

            if second_person_enabled:
                husband_income_for_tax_alloc = income["by_person"]["husband"]
                wife_income_for_tax_alloc = income["by_person"]["wife"]

                if use_expenses and emergency_pre_tax_used > 0:
                    # Approximation: allocate emergency pre-tax withdrawal by current
                    # pre-tax portfolio weights, since portfolioEngine returned only the
                    # household total gross pre-tax draw.
                    h_pre = h_port.total_value_pre
                    w_pre = w_port.total_value_pre
                    total_pre = h_pre + w_pre

                    if total_pre > 0:
                        husband_income_for_tax_alloc += emergency_pre_tax_used * (h_pre / total_pre)
                        wife_income_for_tax_alloc += emergency_pre_tax_used * (w_pre / total_pre)
                    else:
                        husband_income_for_tax_alloc += emergency_pre_tax_used / 2
                        wife_income_for_tax_alloc += emergency_pre_tax_used / 2

                husband_tax_alloc, wife_tax_alloc = taxEngine.allocate_tax_proportionally_couple(
                    total_tax,
                    husband_income_for_tax_alloc,
                    wife_income_for_tax_alloc,
                )

                results["net_income_husband"][s,year] = husband_income_for_tax_alloc - husband_tax_alloc
                results["net_income_wife"][s,year] = wife_income_for_tax_alloc - wife_tax_alloc
            else:
                results["net_income_husband"][s,year] = net_income
                results["net_income_wife"][s,year] = 0


    # print('total_assets: '+str(results["total_assets"][0]))

    # profiler.disable()

    # stats = pstats.Stats(profiler)
    # stats.sort_stats("cumulative").print_stats(40)


    # --------------------------
    # Deflate arrays if real dollars requested
    # --------------------------
    if sim_config.plot_mode == "real":
        discount_factors = real_discount_factors
        #print('total_assets: '+str(results["total_assets"][0])+' discount_factors: '+str(discount_factors))

        results["total_assets"]         = results["total_assets"]       / discount_factors
        results["pre_tax_assets"]       = results["pre_tax_assets"]     / discount_factors
        results["post_tax_assets"]      = results["post_tax_assets"]    / discount_factors
        results["roth_assets"]          = results["roth_assets"]        / discount_factors
        results["hsa_assets"]           = results["hsa_assets"]         / discount_factors
        results["cash"]                 = results["cash"]               / discount_factors
        results["bonds"]                = results["bonds"]              / discount_factors
        results["real_estate"]          = results["real_estate"]        / discount_factors
        results["net_income"]           = results["net_income"]         / discount_factors
        results["gross_income"]         = results["gross_income"]       / discount_factors
        results["net_profit"]           = results["net_profit"]         / discount_factors
        results["taxes"]                = results["taxes"]              / discount_factors
        results["expense_amt"]          = results["expense_amt"]        / discount_factors
        results["ira_401k"]             = results["ira_401k"]           / discount_factors
        results["fund_expenses"]        = results["fund_expenses"]      / discount_factors
        results["bond_interest"]        = results["bond_interest"]      / discount_factors
        results["cash_interest"]        = results["cash_interest"]      / discount_factors
        results["qualified_dividends"]  = results["qualified_dividends"] / discount_factors

        results["federal_ordinary_tax"] = results["federal_ordinary_tax"] / discount_factors
        results["federal_qualified_dividend_tax"] = results["federal_qualified_dividend_tax"] / discount_factors
        results["state_income_tax"]     = results["state_income_tax"]   / discount_factors
        results["payroll_tax"] = results["payroll_tax"] / discount_factors
        results["social_security_payroll_tax"] = results["social_security_payroll_tax"] / discount_factors
        results["medicare_tax"] = results["medicare_tax"] / discount_factors
        results["additional_medicare_tax"] = results["additional_medicare_tax"] / discount_factors
        results["emergency_pre_tax_used"] = results["emergency_pre_tax_used"] / discount_factors
        results["roth_withdrawals"][s, year] /= real_discount_factors[s, year]
        results["hsa_withdrawals"][s, year] /= real_discount_factors[s, year]
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

    return results


