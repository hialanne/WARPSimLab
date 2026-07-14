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
    rothEngine,
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
        "uncovered_expense": np.zeros((effective_num_sims, years_to_simulate + 1)),
        "ira_401k": np.zeros((effective_num_sims, years_to_simulate + 1)),
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
                "bond_interest",
                "cash_interest",
                "qualified_dividends",
                "special_income",
                "roth_conversion",
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
            income["by_class"]["roth_conversion"] = 0.0

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
                h_port,
                w_port,
                sim_config,
                bond_return=year_returns["bd"],
                cash_return=year_returns["cs"],
            )

            income["by_class"]["bond_interest"] += bond_interest
            income["by_class"]["cash_interest"] += cash_interest
            income["by_class"]["qualified_dividends"] += qualified_dividends

            income["total"] += post_tax_total
            income["by_person"]["husband"] += husband_post_tax_total

            if second_person_enabled:
                income["by_person"]["wife"] += wife_post_tax_total

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
            uncovered_expense = 0.0
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

            # ---------------------------------------------------------
            # Scheduled Roth flows
            #
            # Sprint 1 applies conversions only.
            #
            # A Roth conversion:
            #   - moves existing pre-tax assets into Roth assets
            #   - creates ordinary taxable income
            #   - does not create spendable household cash
            #   - occurs before tax calculation and annual returns
            # ---------------------------------------------------------
            roth_flows_for_year = (
                rothEngine.calculate_roth_flows_for_year(
                    curr_husband_age=curr_h_age,
                    curr_wife_age=curr_w_age,
                    year=year,
                    sim_config=sim_config,
                )
            )

            requested_husband_conversion = (
                roth_flows_for_year[
                    rothEngine.ROTH_CONVERSION
                ]["husband"]
            )

            requested_wife_conversion = (
                roth_flows_for_year[
                    rothEngine.ROTH_CONVERSION
                ]["wife"]
            )

            husband_roth_conversion = (
                portfolioEngine.convert_pre_tax_to_roth(
                    h_port,
                    requested_husband_conversion,
                )
            )

            wife_roth_conversion = 0.0

            if second_person_enabled:
                wife_roth_conversion = (
                    portfolioEngine.convert_pre_tax_to_roth(
                        w_port,
                        requested_wife_conversion,
                    )
                )

            roth_conversion_total = (
                husband_roth_conversion
                + wife_roth_conversion
            )

            # Record the taxable conversion separately from cash income.
            # Do not add this to income["total"].
            income["by_class"]["roth_conversion"] = (
                roth_conversion_total
            )
            # ---------------------------------------------------------
            # Requested Roth contributions
            #
            # IRA contributions are scheduled after-tax cash uses.
            #
            # Workplace contributions are also after-tax cash uses, but
            # each owner's requested amount is capped by current gross wages.
            # They do not reduce ordinary taxable income or payroll wages.
            # ---------------------------------------------------------
            requested_husband_roth_ira = (
                roth_flows_for_year[
                    rothEngine.ROTH_IRA_CONTRIBUTION
                ]["husband"]
            )

            requested_wife_roth_ira = (
                roth_flows_for_year[
                    rothEngine.ROTH_IRA_CONTRIBUTION
                ]["wife"]
            )

            requested_husband_roth_workplace = min(
                roth_flows_for_year[
                    rothEngine.ROTH_WORKPLACE_CONTRIBUTION
                ]["husband"],
                payroll_wages_husband,
            )

            requested_wife_roth_workplace = 0.0

            if second_person_enabled:
                requested_wife_roth_workplace = min(
                    roth_flows_for_year[
                        rothEngine.ROTH_WORKPLACE_CONTRIBUTION
                    ]["wife"],
                    payroll_wages_wife,
                )

            requested_roth_contribution_total = (
                requested_husband_roth_ira
                + requested_wife_roth_ira
                + requested_husband_roth_workplace
                + requested_wife_roth_workplace
            )

            actual_husband_roth_ira = 0.0
            actual_wife_roth_ira = 0.0
            actual_husband_roth_workplace = 0.0
            actual_wife_roth_workplace = 0.0

            actual_roth_ira_total = 0.0
            actual_roth_workplace_total = 0.0
            actual_roth_contribution_total = 0.0

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
                    h_port,
                    w_port,
                    husband,
                    wife,
                    year,
                    sim_config,
                    additional_cash_needed=(
                        requested_roth_contribution_total
                    ),
                )
                expense_amt = 0
                wd_pre_tax = wd["pre_tax"]
                wd_post_tax = wd["post_tax"]
                wd_roth = wd.get("roth", 0.0)
                wd_hsa = wd.get("hsa", 0.0)
                wd_rmd = wd.get("rmd", 0.0)
                # Contributions are discretionary relative to the base retirement
                # withdrawal. Any uncovered amount reduces the Roth contribution first.
                withdrawal_uncovered = max(
                    0.0,
                    float(wd.get("uncovered", 0.0)),
                )

                actual_roth_contribution_total = max(
                    0.0,
                    requested_roth_contribution_total
                    - withdrawal_uncovered,
                )

                funded_roth_contributions = (
                    rothEngine.allocate_funded_contributions(
                        requested_ira_husband=(
                            requested_husband_roth_ira
                        ),
                        requested_ira_wife=(
                            requested_wife_roth_ira
                        ),
                        requested_workplace_husband=(
                            requested_husband_roth_workplace
                        ),
                        requested_workplace_wife=(
                            requested_wife_roth_workplace
                        ),
                        funded_total=(
                            actual_roth_contribution_total
                        ),
                    )
                )

                actual_husband_roth_ira = (
                    funded_roth_contributions[
                        rothEngine.ROTH_IRA_CONTRIBUTION
                    ]["husband"]
                )

                actual_wife_roth_ira = (
                    funded_roth_contributions[
                        rothEngine.ROTH_IRA_CONTRIBUTION
                    ]["wife"]
                )

                actual_husband_roth_workplace = (
                    funded_roth_contributions[
                        rothEngine.ROTH_WORKPLACE_CONTRIBUTION
                    ]["husband"]
                )

                actual_wife_roth_workplace = (
                    funded_roth_contributions[
                        rothEngine.ROTH_WORKPLACE_CONTRIBUTION
                    ]["wife"]
                )

                actual_roth_ira_total = (
                    funded_roth_contributions[
                        rothEngine.ROTH_IRA_CONTRIBUTION
                    ]["total"]
                )

                actual_roth_workplace_total = (
                    funded_roth_contributions[
                        rothEngine.ROTH_WORKPLACE_CONTRIBUTION
                    ]["total"]
                )

                income["by_class"]["withdrawal"] = wd["total"]

                # RMDs are already included in income because rmd_h/rmd_w were passed
                # into incomeEngine.calculate_income_breakdown().
                #
                # Additional retirement withdrawals should appear as household cash in pocket.
                # For tax calculation, we mark them non-taxable here, then existing code
                # adds wd_pre_tax back into ordinary income.
                additional_withdrawal_cash = max(
                    0.0,
                    wd["total"]
                    - wd_rmd
                    - actual_roth_contribution_total,
                )

                husband_gross_additional_withdrawal = max(
                    0.0,
                    wd["by_person"]["husband"]
                    - wd["rmd_by_person"]["husband"],
                )

                wife_gross_additional_withdrawal = max(
                    0.0,
                    wd["by_person"]["wife"]
                    - wd["rmd_by_person"]["wife"],
                )

                gross_person_additional_total = (
                    husband_gross_additional_withdrawal
                    + wife_gross_additional_withdrawal
                )

                if gross_person_additional_total > 0.0:
                    husband_contribution_funding = (
                        actual_roth_contribution_total
                        * husband_gross_additional_withdrawal
                        / gross_person_additional_total
                    )
                else:
                    husband_contribution_funding = 0.0

                wife_contribution_funding = (
                    actual_roth_contribution_total
                    - husband_contribution_funding
                )

                husband_additional_withdrawal = max(
                    0.0,
                    husband_gross_additional_withdrawal
                    - husband_contribution_funding,
                )

                wife_additional_withdrawal = max(
                    0.0,
                    wife_gross_additional_withdrawal
                    - wife_contribution_funding,
                )

                person_additional_total = (
                    husband_additional_withdrawal
                    + wife_additional_withdrawal
                )

                if abs( person_additional_total - additional_withdrawal_cash ) > 1e-6:
                    raise RuntimeError(
                        "Person-level retirement withdrawals do not "
                        "match the household withdrawal total"
                    )

                income["total"] += additional_withdrawal_cash
                income["by_person"]["husband"] += (husband_additional_withdrawal)

                if second_person_enabled:
                    income["by_person"]["wife"] += (wife_additional_withdrawal)

                income["non_taxable_income"] = (income.get("non_taxable_income", 0.0) + additional_withdrawal_cash)

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
                    + roth_conversion_total
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

                taxes_enabled = (
                    sim_config.calculate_income_taxes
                    or sim_config.calculate_payroll_taxes
                    or sim_config.calculate_state_taxes
                )

                if taxes_enabled:
                    net_cash = (
                        income["total"]
                        - baseline_total_tax
                        - expense_amt
                        - requested_roth_contribution_total
                    )
                else:
                    net_cash = (
                        income["total"]
                        - expense_amt
                        - requested_roth_contribution_total
                    )

                # print("income total: "+str(income["total"]))
                # print("expense_amt: "+str(expense_amt))
                # print("baseline_total_tax: "+str(baseline_total_tax))

                # Apply net cash and capture any emergency gross pre-tax draw
                if second_person_enabled:
                    net_cash_result = portfolioEngine.apply_net_income_couple(
                        h_port,
                        w_port,
                        net_cash,
                    )
                else:
                    net_cash_result = portfolioEngine.apply_net_income_single(
                        h_port,
                        net_cash,
                    )

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

                combined_uncovered = max(
                    0.0,
                    float(
                        net_cash_result.get(
                            "uncovered",
                            0.0,
                        )
                    ),
                )

                # Contributions are discretionary. If the portfolio cannot fund
                # the complete cash requirement, reduce contributions before
                # reporting ordinary expenses as uncovered.
                actual_roth_contribution_total = max(
                    0.0,
                    requested_roth_contribution_total
                    - combined_uncovered,
                )

                uncovered_expense = max(
                    0.0,
                    combined_uncovered
                    - requested_roth_contribution_total,
                )

                funded_roth_contributions = (
                    rothEngine.allocate_funded_contributions(
                        requested_ira_husband=(
                            requested_husband_roth_ira
                        ),
                        requested_ira_wife=(
                            requested_wife_roth_ira
                        ),
                        requested_workplace_husband=(
                            requested_husband_roth_workplace
                        ),
                        requested_workplace_wife=(
                            requested_wife_roth_workplace
                        ),
                        funded_total=(
                            actual_roth_contribution_total
                        ),
                    )
                )

                actual_husband_roth_ira = (
                    funded_roth_contributions[
                        rothEngine.ROTH_IRA_CONTRIBUTION
                    ]["husband"]
                )

                actual_wife_roth_ira = (
                    funded_roth_contributions[
                        rothEngine.ROTH_IRA_CONTRIBUTION
                    ]["wife"]
                )

                actual_husband_roth_workplace = (
                    funded_roth_contributions[
                        rothEngine.ROTH_WORKPLACE_CONTRIBUTION
                    ]["husband"]
                )

                actual_wife_roth_workplace = (
                    funded_roth_contributions[
                        rothEngine.ROTH_WORKPLACE_CONTRIBUTION
                    ]["wife"]
                )

                actual_roth_ira_total = (
                    funded_roth_contributions[
                        rothEngine.ROTH_IRA_CONTRIBUTION
                    ]["total"]
                )

                actual_roth_workplace_total = (
                    funded_roth_contributions[
                        rothEngine.ROTH_WORKPLACE_CONTRIBUTION
                    ]["total"]
                )

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
                    + roth_conversion_total
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

            # ---------------------------------------------------------
            # Deposit only the Roth contributions that were actually funded.
            #
            # Contributions are added before annual returns, so they participate
            # in the current year's return under the simulator's annual timing model.
            # ---------------------------------------------------------
            portfolioEngine.apply_roth_contribution(
                h_port,
                (
                    actual_husband_roth_ira
                    + actual_husband_roth_workplace
                ),
            )

            if second_person_enabled:
                portfolioEngine.apply_roth_contribution(
                    w_port,
                    (
                        actual_wife_roth_ira
                        + actual_wife_roth_workplace
                    ),
                )

            equity_total_return = year_returns["eq"]
            equity_dividend_yield = sim_config._post_tax_equity_dividend_yield
            taxable_equity_price_return = (
                equity_total_return - equity_dividend_yield
            )

            # Portfolio returns (shared market path)
            fund_expense_rate = sim_config.fund_expense if sim_config.use_fund_expenses else 0.0

            fund_expenses = portfolioEngine.apply_returns_and_fund_expenses(
                h_port,
                equity_total_return,
                taxable_equity_price_return,
                year_returns["bd"],
                year_returns["cs"],
                year_returns["re"],
                fund_expense_rate,
            )

            if second_person_enabled:
                fund_expenses += portfolioEngine.apply_returns_and_fund_expenses(
                    w_port,
                    equity_total_return,
                    taxable_equity_price_return,
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

            taxes_enabled = (
                sim_config.calculate_income_taxes
                or sim_config.calculate_payroll_taxes
                or sim_config.calculate_state_taxes
            )

            net_income = (
                income["total"] - total_tax
                if taxes_enabled
                else income["total"]
            )

            if sim_config.second_person_enabled:
                ira_401k = h_401k_employee + h_401k_employer + w_401k_employee + w_401k_employer
                employee_401k_total = h_401k_employee + w_401k_employee
            else:
                ira_401k = h_401k_employee + h_401k_employer
                employee_401k_total = h_401k_employee

            gross_income = income["total"] + employee_401k_total + emergency_pre_tax_used

            if use_expenses:
                net_profit = (
                    net_income
                    - expense_amt
                    - actual_roth_contribution_total
                )
            else:
                # Retirement-mode income already excludes the withdrawal cash
                # redirected into Roth contributions.
                net_profit = net_income

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
            results["uncovered_expense"][s, year] = uncovered_expense
            results["ira_401k"][s, year] = ira_401k

            results["roth_ira_contributions"][s, year] = (
                actual_roth_ira_total
            )

            results["roth_workplace_contributions"][s, year] = (
                actual_roth_workplace_total
            )

            results["roth_conversions"][s, year] = (
                roth_conversion_total
            )

            results["roth_total_flows"][s, year] = (
                actual_roth_ira_total
                + actual_roth_workplace_total
                + roth_conversion_total
            )

            results["fund_expenses"][s, year] = fund_expenses            
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
                results["breakdown_by_class"][key][s, year] = (
                    income["by_class"][key]
                )

            # ---------------------------------------------------------
            # Allocate household income and taxes by person.
            # ---------------------------------------------------------
            if second_person_enabled:
                husband_income_for_tax_alloc = (
                    income["by_person"]["husband"]
                    + husband_roth_conversion
                )

                wife_income_for_tax_alloc = (
                    income["by_person"]["wife"]
                    + wife_roth_conversion
                )

                if use_expenses and emergency_pre_tax_used > 0.0:
                    h_pre = h_port.total_value_pre
                    w_pre = w_port.total_value_pre
                    total_pre = h_pre + w_pre

                    if total_pre > 0.0:
                        husband_income_for_tax_alloc += (
                            emergency_pre_tax_used
                            * h_pre
                            / total_pre
                        )
                        wife_income_for_tax_alloc += (
                            emergency_pre_tax_used
                            * w_pre
                            / total_pre
                        )
                    else:
                        husband_income_for_tax_alloc += (
                            emergency_pre_tax_used / 2.0
                        )
                        wife_income_for_tax_alloc += (
                            emergency_pre_tax_used / 2.0
                        )

                expected_person_income_total = (
                    income["total"]
                    + emergency_pre_tax_used
                    + roth_conversion_total
                )

                actual_person_income_total = (
                    husband_income_for_tax_alloc
                    + wife_income_for_tax_alloc
                )

                if abs(
                    actual_person_income_total
                    - expected_person_income_total
                ) > 1e-6:
                    raise RuntimeError(
                        "Person-level income does not match household income"
                    )

                (
                    husband_tax_alloc,
                    wife_tax_alloc,
                ) = taxEngine.allocate_tax_proportionally_couple(
                    total_tax,
                    husband_income_for_tax_alloc,
                    wife_income_for_tax_alloc,
                )

                results["net_income_husband"][s, year] = (
                    husband_income_for_tax_alloc
                    - husband_tax_alloc
                )

                results["net_income_wife"][s, year] = (
                    wife_income_for_tax_alloc
                    - wife_tax_alloc
                )

            else:
                results["net_income_husband"][s, year] = net_income
                results["net_income_wife"][s, year] = 0.0

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
        results["net_income_husband"]   = (results["net_income_husband"] / discount_factors)
        results["net_income_wife"]      = (results["net_income_wife"]   / discount_factors)
        results["gross_income"]         = results["gross_income"]       / discount_factors
        results["net_profit"]           = results["net_profit"]         / discount_factors
        results["taxes"]                = results["taxes"]              / discount_factors
        results["expense_amt"]          = results["expense_amt"]        / discount_factors
        results["uncovered_expense"]    = (results["uncovered_expense"] / discount_factors)
        results["ira_401k"]             = results["ira_401k"]           / discount_factors
        results["roth_ira_contributions"] = (
            results["roth_ira_contributions"]
            / discount_factors
        )
        results["roth_workplace_contributions"] = (
            results["roth_workplace_contributions"]
            / discount_factors
        )
        results["roth_conversions"] = (
            results["roth_conversions"]
            / discount_factors
        )
        results["roth_total_flows"] = (
            results["roth_total_flows"]
            / discount_factors
        )
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
        results["roth_withdrawals"] = (results["roth_withdrawals"] / discount_factors)
        results["hsa_withdrawals"] = (results["hsa_withdrawals"] / discount_factors)
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
        results["breakdown_by_class"]["qualified_dividends"] = (results["breakdown_by_class"]["qualified_dividends"] / discount_factors)

    return results


