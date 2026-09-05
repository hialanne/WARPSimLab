# run_sim_core_withdrawals.py

from .engines import (
    portfolioEngine,
    incomeEngine,
    withdrawalEngine,
    taxEngine,
    rothEngine,
    diagnosticEngine,
)

# -----------------------------------------------------------------------------
# Withdrawal-mode yearly simulation
# -----------------------------------------------------------------------------
#
# This file implements the yearly core logic for the income/withdrawal
# simulation path.
#
# In this mode, the simulator models household income together with a selected
# retirement withdrawal strategy. Instead of using projected household expenses
# to determine portfolio funding needs, the configured withdrawal strategy
# determines how much is withdrawn from the portfolio.
#
# This path is intended to evaluate the consequences of withdrawal strategies,
# such as percentage-based withdrawals, inflation-adjusted withdrawals, and
# fixed-dollar withdrawals. It shows how those strategies interact with income,
# taxes, RMDs, Roth flows, investment returns, fund expenses, and the remaining
# portfolio over time.
#
# Withdrawal mode is intentionally separate from expense mode. The two yearly
# paths contain substantial similar logic, but keeping each path complete and
# explicit makes the financial sequence easier to read, audit, test, and reason
# about. Readability of the simulation model is preferred over minimizing
# duplicated code.
# -----------------------------------------------------------------------------


def simulate_withdrawal_year(
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
):

    # -------------------------------------------------------------------------
    # Withdrawal-mode yearly flow
    # -------------------------------------------------------------------------
    #
    # The yearly calculation proceeds roughly in this order:
    #
    #   1. Calculate required minimum distributions (RMDs). In withdrawal mode,
    #      the actual RMD withdrawals are applied later as part of the retirement
    #      withdrawal calculation.
    #
    #   2. Build household income from wages, Social Security, pensions,
    #      annuities, RMDs, special income, and taxable investment income.
    #
    #   3. Prepare scheduled Roth flows. Traditional 401(k) and HSA
    #      contributions are not currently made in withdrawal mode.
    #
    #   4. Limit Roth conversions so they do not consume pre-tax assets already
    #      needed to satisfy the year's RMDs, then apply the conversions.
    #
    #   5. Calculate payroll taxes.
    #
    #   6. Calculate the retirement withdrawal required by the selected
    #      withdrawal strategy. The withdrawal also includes any additional cash
    #      requested for Roth contributions.
    #
    #   7. Reduce discretionary Roth contributions if the portfolio cannot fund
    #      the full requested withdrawal.
    #
    #   8. Separate retirement-withdrawal cash used for Roth contributions from
    #      withdrawal cash available to the household.
    #
    #   9. Calculate income taxes using the taxable portions of RMDs, pre-tax
    #      withdrawals, taxable HSA withdrawals, Roth conversions, and other
    #      taxable income.
    #
    #  10. If available household cash is insufficient to pay the tax bill,
    #      withdraw additional portfolio assets to fund the tax shortfall and
    #      recalculate taxes when those withdrawals create additional taxable
    #      income.
    #
    #  11. Deposit the Roth contributions that were actually funded.
    #
    #  12. Apply market returns and fund expenses to the remaining portfolio.
    #
    #  13. Rebalance the portfolio if requested.
    #
    #  14. Build the reporting values returned to run_sim_core.py.
    #
    # The ordering is significant. In particular, RMDs, Roth conversions,
    # retirement withdrawals, Roth contribution funding, and tax-funding
    # withdrawals can all change the assets and taxable income available to
    # later steps.
    # -------------------------------------------------------------------------


    # RMD amounts are needed for income reporting. Actual RMD withdrawal
    # occurs inside calculate_retirement_withdrawal() in Withdrawal mode.
    rmd_h = withdrawalEngine.calculate_rmds(h_port, husband, curr_h_age, sim_config)

    rmd_w = 0
    if second_person_enabled:
        rmd_w = withdrawalEngine.calculate_rmds(w_port, wife, curr_w_age, sim_config)

    # Income breakdown
    income = incomeEngine.calculate_income_breakdown(
        husband, wife, curr_h_age, curr_w_age, rmd_h, rmd_w, year, sim_config
    )
    income["by_class"]["roth_conversion"] = 0.0

    (
        bond_interest,
        cash_interest,
        qualified_equity_distributions,
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
    income["by_class"]["qualified_equity_distributions"] += qualified_equity_distributions

    income["total"] += post_tax_total
    income["by_person"]["husband"] += husband_post_tax_total

    if second_person_enabled:
        income["by_person"]["wife"] += wife_post_tax_total

    payroll_wages_husband = max(0.0, float(income.get("work_by_person", {}).get("husband", 0.0)))
    payroll_wages_wife = 0.0

    if second_person_enabled:
        payroll_wages_wife = max(0.0, float(income.get("work_by_person", {}).get("wife", 0.0)))

    # Withdrawal mode does not currently make traditional 401k or HSA contributions.
    h_401k_employee = 0.0
    h_401k_employer = 0.0
    w_401k_employee = 0.0
    w_401k_employer = 0.0

    h_hsa = {"employee": 0.0, "employer": 0.0, "total": 0.0}
    w_hsa = {"employee": 0.0, "employer": 0.0, "total": 0.0}

    emergency_pre_tax_used = 0.0
    qualified_hsa_withdrawal = 0.0
    uncovered_expense = 0.0
    cash_flow_shortfall = 0.0
    final_tax_delta = 0.0
    final_tax_delta_deducted = 0.0
    final_tax_delta_uncovered = 0.0

    # Prepare requested Roth flows.
    requested_roth_flows = rothEngine.prepare_requested_roth_flows(
        curr_husband_age=curr_h_age,
        curr_wife_age=curr_w_age,
        year=year,
        payroll_wages_husband=payroll_wages_husband,
        payroll_wages_wife=payroll_wages_wife,
        second_person_enabled=second_person_enabled,
        sim_config=sim_config,
    )

    # Preserve the already-determined RMD in pre-tax assets until it is physically withdrawn.
    roth_conversion = requested_roth_flows[rothEngine.ROTH_CONVERSION]

    roth_conversion["husband"] = min(
        roth_conversion["husband"], max(0.0, float(h_port.total_value_pre) - rmd_h)
    )

    if second_person_enabled:
        roth_conversion["wife"] = min(
            roth_conversion["wife"], max(0.0, float(w_port.total_value_pre) - rmd_w)
        )
    else:
        roth_conversion["wife"] = 0.0

    roth_conversion["total"] = roth_conversion["husband"] + roth_conversion["wife"]

    applied_roth_conversions = rothEngine.apply_roth_conversions(
        husband_portfolio=h_port,
        wife_portfolio=w_port,
        requested_flows=requested_roth_flows,
        second_person_enabled=second_person_enabled,
    )

    husband_roth_conversion = applied_roth_conversions["husband"]
    wife_roth_conversion = applied_roth_conversions["wife"]
    roth_conversion_total = applied_roth_conversions["total"]

    # A Roth conversion is taxable ordinary income, but it is not spendable household cash.
    income["by_class"]["roth_conversion"] = roth_conversion_total

    requested_roth_contribution_total = requested_roth_flows["requested_contribution_total"]


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

    wd = withdrawalEngine.calculate_retirement_withdrawal(
        h_port,
        w_port,
        husband,
        wife,
        year,
        sim_config,
        rmd_h=rmd_h,
        rmd_w=rmd_w,
        additional_cash_needed=requested_roth_contribution_total,
    )

    expense_amt = 0
    wd_pre_tax = wd["pre_tax"]
    wd_roth = wd.get("roth", 0.0)
    wd_hsa = wd.get("hsa", 0.0)
    taxable_hsa_withdrawal = wd_hsa

    withdrawal_uncovered = max(0.0, float(wd.get("uncovered", 0.0)))

    # Contributions are discretionary relative to the base retirement withdrawal.
    roth_funding_result = rothEngine.resolve_contribution_shortfall(
        requested_flows=requested_roth_flows,
        uncovered_amount=withdrawal_uncovered,
    )

    funded_roth_contributions = roth_funding_result["funded_contributions"]
    uncovered_expense = roth_funding_result["remaining_uncovered"]

    # Separate withdrawal cash used for Roth contributions from household spending.
    retirement_cash = rothEngine.separate_retirement_contribution_funding(
        withdrawal_result=wd,
        actual_contribution_total=funded_roth_contributions["total"],
        sim_config=sim_config,
    )

    additional_withdrawal_cash = retirement_cash["household"]
    husband_additional_withdrawal = retirement_cash["husband"]
    wife_additional_withdrawal = retirement_cash["wife"]

    income["total"] += additional_withdrawal_cash
    income["by_person"]["husband"] += husband_additional_withdrawal

    if second_person_enabled:
        income["by_person"]["wife"] += wife_additional_withdrawal

    income["non_taxable_income"] = income.get("non_taxable_income", 0.0) + additional_withdrawal_cash

    if qualified_equity_distributions > income["total"] + 1.0:
        diagnosticEngine.raise_internal_error("Qualified dividends exceed total income", sim_config,
                                              context={"year": year, "qualified_equity_distributions": qualified_equity_distributions,
                                                       "income_total": income["total"],
                                                       "difference": qualified_equity_distributions - income["total"]})

    qualified_equity_distributions = income["by_class"].get("qualified_equity_distributions", 0.0)

    ordinary_income = (
        income["total"]
        - qualified_equity_distributions
        - income.get("non_taxable_income", 0.0)
        + wd_pre_tax
        + wd_hsa
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
        qualified_equity_distributions=qualified_equity_distributions,
        year_cache=year_cache,
        sim_config=sim_config,
    )

    total_tax += payroll_tax
    baseline_total_tax = total_tax

    taxes_enabled = (
        sim_config.calculate_income_taxes
        or sim_config.calculate_payroll_taxes
        or sim_config.calculate_state_taxes
    )

    initial_tax_cash_shortfall = max(0.0, total_tax - income["total"]) if taxes_enabled else 0.0

    # Taxes take priority over discretionary Roth contributions. Cash already withdrawn for
    # a contribution can be redirected to taxes before another portfolio withdrawal is made.
    if initial_tax_cash_shortfall > 0.0 and funded_roth_contributions["total"] > 0.0:
        revised_roth_funding = rothEngine.resolve_contribution_shortfall(
            requested_flows=requested_roth_flows,
            uncovered_amount=withdrawal_uncovered + initial_tax_cash_shortfall,
        )
        revised_funded_roth_contributions = revised_roth_funding["funded_contributions"]

        if revised_funded_roth_contributions["total"] < funded_roth_contributions["total"]:
            revised_retirement_cash = rothEngine.separate_retirement_contribution_funding(
                withdrawal_result=wd,
                actual_contribution_total=revised_funded_roth_contributions["total"],
                sim_config=sim_config,
            )

            released_household_cash = revised_retirement_cash["household"] - additional_withdrawal_cash
            released_husband_cash = revised_retirement_cash["husband"] - husband_additional_withdrawal
            released_wife_cash = revised_retirement_cash["wife"] - wife_additional_withdrawal

            income["total"] += released_household_cash
            income["by_person"]["husband"] += released_husband_cash

            if second_person_enabled:
                income["by_person"]["wife"] += released_wife_cash

            income["non_taxable_income"] += released_household_cash

            funded_roth_contributions = revised_funded_roth_contributions
            retirement_cash = revised_retirement_cash
            additional_withdrawal_cash = retirement_cash["household"]
            husband_additional_withdrawal = retirement_cash["husband"]
            wife_additional_withdrawal = retirement_cash["wife"]

    income["by_class"]["withdrawal"] = additional_withdrawal_cash
    tax_funding = withdrawalEngine.fund_tax_cash_shortfall(h_port, w_port, total_tax, income["total"], sim_config)

    if tax_funding["total"] > 0.0:
        income["total"] += tax_funding["total"]
        income["by_person"]["husband"] += tax_funding["by_person"]["husband"]

        if second_person_enabled:
            income["by_person"]["wife"] += tax_funding["by_person"]["wife"]

        income["non_taxable_income"] += tax_funding["total"]
        income["by_class"]["tax_funding_withdrawal"] = tax_funding["total"]

        wd_pre_tax += tax_funding["pre_tax"]
        wd_roth += tax_funding["roth"]
        wd_hsa += tax_funding["hsa"]
        taxable_hsa_withdrawal += tax_funding["hsa"]

        if tax_funding["pre_tax"] > 0.0 or tax_funding["hsa"] > 0.0:
            ordinary_income += tax_funding["pre_tax"] + tax_funding["hsa"]

            (
                federal_ordinary_tax,
                federal_qualified_dividend_tax,
                state_income_tax,
                total_tax,
                federal_marginal_rate,
            ) = taxEngine.calculate_total_income_tax_split(
                ordinary_income=ordinary_income,
                qualified_equity_distributions=qualified_equity_distributions,
                year_cache=year_cache,
                sim_config=sim_config,
            )

            total_tax += payroll_tax

    final_tax_delta = max(0.0, total_tax - baseline_total_tax)
    final_tax_delta_deducted = 0.0
    final_tax_delta_uncovered = final_tax_delta

    # Deposit only Roth contributions that were actually funded.

    deposited_roth_contributions = rothEngine.deposit_funded_roth_contributions(
        husband_portfolio=h_port,
        wife_portfolio=w_port,
        funded_contributions=funded_roth_contributions,
        second_person_enabled=second_person_enabled,
    )

    if abs(deposited_roth_contributions["total"] - funded_roth_contributions["total"]) > 1e-6:
        diagnosticEngine.raise_internal_error("Deposited Roth contributions do not match the funded contribution total", sim_config,
                                              context={"year": year,
                                                       "deposited_total": deposited_roth_contributions["total"],
                                                       "funded_total": funded_roth_contributions["total"],
                                                       "difference": deposited_roth_contributions["total"] - funded_roth_contributions["total"]})

    # Portfolio returns and fund expenses.
    equity_total_return = year_returns["eq"]
    equity_dividend_yield = sim_config._post_tax_equity_dividend_yield
    taxable_equity_price_return = equity_total_return - equity_dividend_yield
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

    if sim_config.rebalance_every_year:
        portfolioEngine.rebalance(h_port, sim_config)
        if second_person_enabled:
            portfolioEngine.rebalance(w_port, sim_config)

    # Reporting values.

    if taxes_enabled:
        net_income = income["total"] - total_tax
    else:
        net_income = income["total"]

    if second_person_enabled:
        ira_401k = h_401k_employee + h_401k_employer + w_401k_employee + w_401k_employer
        employee_401k_total = h_401k_employee + w_401k_employee
    else:
        ira_401k = h_401k_employee + h_401k_employer
        employee_401k_total = h_401k_employee

    hsa_employee_total = h_hsa["employee"] + (w_hsa["employee"] if second_person_enabled else 0.0)
    hsa_employer_total = h_hsa["employer"] + (w_hsa["employer"] if second_person_enabled else 0.0)
    hsa_total_contributions = hsa_employee_total + hsa_employer_total

    gross_income = income["total"] + employee_401k_total + emergency_pre_tax_used + hsa_employee_total

    # Retirement-mode income already excludes withdrawal cash redirected into Roth contributions.
    net_profit = net_income

    # Preserve existing person-level tax allocation timing. This intentionally occurs
    # after portfolio returns and rebalancing, matching the current run_sim_core.py.
    if second_person_enabled:
        husband_income_for_tax_alloc = income["by_person"]["husband"] + husband_roth_conversion
        wife_income_for_tax_alloc = income["by_person"]["wife"] + wife_roth_conversion

        expected_person_income_total = income["total"] + emergency_pre_tax_used + roth_conversion_total
        actual_person_income_total = husband_income_for_tax_alloc + wife_income_for_tax_alloc

        if abs(actual_person_income_total - expected_person_income_total) > 1.0:
            diagnosticEngine.raise_internal_error("Person-level income does not match household income", sim_config,
                                                  context={"year": year, "second_person_enabled": second_person_enabled,
                                                           "income_total": income["total"],
                                                           "husband_income": income["by_person"]["husband"],
                                                           "wife_income": income["by_person"]["wife"],
                                                           "husband_roth_conversion": husband_roth_conversion,
                                                           "wife_roth_conversion": wife_roth_conversion,
                                                           "emergency_pre_tax_used": emergency_pre_tax_used,
                                                           "expected_total": expected_person_income_total,
                                                           "actual_total": actual_person_income_total,
                                                           "difference": actual_person_income_total - expected_person_income_total})

        husband_tax_alloc, wife_tax_alloc = taxEngine.allocate_tax_proportionally_couple(
            total_tax, husband_income_for_tax_alloc, wife_income_for_tax_alloc
        )

        net_income_husband = husband_income_for_tax_alloc - husband_tax_alloc
        net_income_wife = wife_income_for_tax_alloc - wife_tax_alloc
    else:
        net_income_husband = net_income
        net_income_wife = 0.0

    return {
        "income": income,
        "gross_income": gross_income,
        "net_income": net_income,
        "net_profit": net_profit,
        "net_income_husband": net_income_husband,
        "net_income_wife": net_income_wife,
        "total_tax": total_tax,
        "federal_marginal_rate": federal_marginal_rate,
        "federal_ordinary_tax": federal_ordinary_tax,
        "federal_qualified_dividend_tax": federal_qualified_dividend_tax,
        "state_income_tax": state_income_tax,
        "payroll_tax": payroll_tax,
        "social_security_payroll_tax": social_security_payroll_tax,
        "medicare_tax": medicare_tax,
        "additional_medicare_tax": additional_medicare_tax,
        "expense_amt": expense_amt,
        "uncovered_expense": uncovered_expense,
        "cash_flow_shortfall": cash_flow_shortfall,
        "rmd_h": rmd_h,
        "rmd_w": rmd_w,
        "wd_roth": wd_roth,
        "wd_hsa": wd_hsa,
        "pre_tax_withdrawal": wd_pre_tax,
        "qualified_hsa_withdrawal": qualified_hsa_withdrawal,
        "taxable_hsa_withdrawal": taxable_hsa_withdrawal,
        "emergency_pre_tax_used": emergency_pre_tax_used,
        "ira_401k": ira_401k,
        "employee_401k_total": employee_401k_total,
        "hsa_employee_total": hsa_employee_total,
        "hsa_employer_total": hsa_employer_total,
        "hsa_total_contributions": hsa_total_contributions,
        "funded_roth_contributions": funded_roth_contributions,
        "roth_conversion_total": roth_conversion_total,
        "bond_interest": bond_interest,
        "cash_interest": cash_interest,
        "qualified_equity_distributions": qualified_equity_distributions,
        "fund_expenses": fund_expenses,
        "final_tax_delta": final_tax_delta,
        "final_tax_delta_deducted": final_tax_delta_deducted,
        "final_tax_delta_uncovered": final_tax_delta_uncovered,
    }