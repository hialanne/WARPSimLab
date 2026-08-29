# run_sim_core_expenses.py

from .engines import (
    portfolioEngine,
    incomeEngine,
    withdrawalEngine,
    expenseEngine,
    taxEngine,
    rothEngine,
    hsaEngine,
)


def simulate_expense_year(
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
):
    # RMDs
    rmd_h = withdrawalEngine.calculate_rmds(h_port, husband, curr_h_age, sim_config)
    withdrawalEngine.withdraw_rmds(h_port, rmd_h)

    rmd_w = 0
    if second_person_enabled:
        rmd_w = withdrawalEngine.calculate_rmds(w_port, wife, curr_w_age, sim_config)
        withdrawalEngine.withdraw_rmds(w_port, rmd_w)

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

    # 401k contributions
    h_401k_employee, h_401k_employer = incomeEngine.calculate_pre_tax_401k_contributions(
        husband, curr_h_age, year, sim_config
    )
    incomeEngine.apply_employee_401k_to_income(income, h_401k_employee, "husband")
    portfolioEngine.apply_pre_tax_contribution(h_port, h_401k_employee + h_401k_employer)

    w_401k_employee = 0.0
    w_401k_employer = 0.0

    if second_person_enabled:
        w_401k_employee, w_401k_employer = incomeEngine.calculate_pre_tax_401k_contributions(
            wife, curr_w_age, year, sim_config
        )
        incomeEngine.apply_employee_401k_to_income(income, w_401k_employee, "wife")
        portfolioEngine.apply_pre_tax_contribution(w_port, w_401k_employee + w_401k_employer)

    # HSA contributions
    h_hsa = hsaEngine.calculate_hsa_contributions(
        husband, curr_h_age, year, payroll_wages_husband, h_401k_employee, sim_config
    )
    hsaEngine.apply_employee_hsa_to_income(income, h_hsa["employee"], "husband")
    hsaEngine.deposit_hsa_contributions(h_port, h_hsa)
    payroll_wages_husband = max(0.0, payroll_wages_husband - h_hsa["employee"])

    w_hsa = {"employee": 0.0, "employer": 0.0, "total": 0.0}

    if second_person_enabled:
        w_hsa = hsaEngine.calculate_hsa_contributions(
            wife, curr_w_age, year, payroll_wages_wife, w_401k_employee, sim_config
        )
        hsaEngine.apply_employee_hsa_to_income(income, w_hsa["employee"], "wife")
        hsaEngine.deposit_hsa_contributions(w_port, w_hsa)
        payroll_wages_wife = max(0.0, payroll_wages_wife - w_hsa["employee"])

    # Roth flows
    requested_roth_flows = rothEngine.prepare_requested_roth_flows(
        curr_husband_age=curr_h_age,
        curr_wife_age=curr_w_age,
        year=year,
        payroll_wages_husband=payroll_wages_husband,
        payroll_wages_wife=payroll_wages_wife,
        second_person_enabled=second_person_enabled,
        sim_config=sim_config,
    )

    applied_roth_conversions = rothEngine.apply_roth_conversions(
        husband_portfolio=h_port,
        wife_portfolio=w_port,
        requested_flows=requested_roth_flows,
        second_person_enabled=second_person_enabled,
    )

    husband_roth_conversion = applied_roth_conversions["husband"]
    wife_roth_conversion = applied_roth_conversions["wife"]
    roth_conversion_total = applied_roth_conversions["total"]

    # A Roth conversion is taxable ordinary income, but is not spendable household cash.
    income["by_class"]["roth_conversion"] = roth_conversion_total

    requested_roth_contribution_total = requested_roth_flows["requested_contribution_total"]

    # Payroll taxes
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

    # User expenses and qualified HSA expenses
    expense_breakdown = expenseEngine.calculate_expense_breakdown(expenses, year, sim_config)
    expense_amt = expense_breakdown["total"]

    qualified_hsa_result = hsaEngine.pay_qualified_hsa_expenses(
        h_port, w_port, expense_breakdown["hsa_eligible"], second_person_enabled
    )
    qualified_hsa_withdrawal = qualified_hsa_result["paid"]

    cash_expense_amt = expense_breakdown["non_hsa"] + qualified_hsa_result["uncovered"]

    wd_pre_tax = 0.0
    wd_roth = 0.0
    wd_hsa = qualified_hsa_withdrawal

    if qualified_equity_distributions > income["total"]:
        print(
            "qualified_equity_distributions: "
            + str(qualified_equity_distributions)
            + " income-total: "
            + str(income["total"])
        )
        raise RuntimeError("Qualified dividends exceed total income")

    # One-pass approximation for emergency pre-tax withdrawals.
    qualified_equity_distributions = income["by_class"].get("qualified_equity_distributions", 0.0)

    baseline_ordinary_income = (
        income["total"]
        - qualified_equity_distributions
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
        qualified_equity_distributions=qualified_equity_distributions,
        year_cache=year_cache,
        sim_config=sim_config,
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
            - cash_expense_amt
            - requested_roth_contribution_total
        )
    else:
        net_cash = income["total"] - cash_expense_amt - requested_roth_contribution_total

    # Apply net cash and capture any emergency gross pre-tax draw.
    if second_person_enabled:
        net_cash_result = portfolioEngine.apply_net_income_couple(h_port, w_port, net_cash)
    else:
        net_cash_result = portfolioEngine.apply_net_income_single(h_port, net_cash)

    cash_flow_shortfall = sum(
        net_cash_result.get(key, 0.0)
        for key in ("post_tax_used", "pre_tax_used", "roth_used", "hsa_used", "real_estate_used")
    )

    emergency_pre_tax_used = net_cash_result["pre_tax_used"]
    taxable_hsa_withdrawal = net_cash_result["hsa_used"]
    wd_hsa = qualified_hsa_withdrawal + taxable_hsa_withdrawal

    combined_uncovered = max(0.0, float(net_cash_result.get("uncovered", 0.0)))

    # Roth contributions are discretionary. Apply the cash shortfall to them before reporting uncovered expenses.
    roth_funding_result = rothEngine.resolve_contribution_shortfall(
        requested_flows=requested_roth_flows,
        uncovered_amount=combined_uncovered,
    )

    funded_roth_contributions = roth_funding_result["funded_contributions"]
    uncovered_expense = roth_funding_result["remaining_uncovered"]

    # Recompute final taxes if taxable portfolio withdrawals changed income.
    if emergency_pre_tax_used > 0.0 or taxable_hsa_withdrawal > 0.0:
        ordinary_income = baseline_ordinary_income + emergency_pre_tax_used + taxable_hsa_withdrawal

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
    else:
        federal_ordinary_tax = baseline_federal_ordinary_tax
        federal_qualified_dividend_tax = baseline_federal_qualified_dividend_tax
        state_income_tax = baseline_state_income_tax
        total_tax = baseline_total_tax
        federal_marginal_rate = baseline_federal_marginal_rate

    final_tax_delta = max(0.0, total_tax - baseline_total_tax)
    final_tax_delta_deducted = 0.0
    final_tax_delta_uncovered = 0.0

    # Deduct the extra tax created by taxable emergency withdrawals.
    if sim_config.calculate_income_taxes and final_tax_delta > 0:
        final_tax_delta_deducted = portfolioEngine.deduct_post_tax_amount(
            h_port, w_port, final_tax_delta, sim_config
        )
        final_tax_delta_uncovered = max(0.0, final_tax_delta - final_tax_delta_deducted)

    if final_tax_delta < -1e-9:
        raise RuntimeError("final_tax_delta should never be negative")

    if final_tax_delta_deducted < -1e-9:
        raise RuntimeError("final_tax_delta_deducted should never be negative")

    if final_tax_delta_uncovered < -1e-9:
        raise RuntimeError("final_tax_delta_uncovered should never be negative")

    # Deposit only Roth contributions that were actually funded.
    deposited_roth_contributions = rothEngine.deposit_funded_roth_contributions(
        husband_portfolio=h_port,
        wife_portfolio=w_port,
        funded_contributions=funded_roth_contributions,
        second_person_enabled=second_person_enabled,
    )

    if abs(deposited_roth_contributions["total"] - funded_roth_contributions["total"]) > 1e-6:
        raise RuntimeError("Deposited Roth contributions do not match the funded contribution total")

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

    # Rebalance if requested.
    if sim_config.rebalance_every_year:
        portfolioEngine.rebalance(h_port, sim_config)
        if second_person_enabled:
            portfolioEngine.rebalance(w_port, sim_config)

    # Reporting values.
    net_income = income["total"] - total_tax if taxes_enabled else income["total"]

    if second_person_enabled:
        ira_401k = h_401k_employee + h_401k_employer + w_401k_employee + w_401k_employer
        employee_401k_total = h_401k_employee + w_401k_employee
    else:
        ira_401k = h_401k_employee + h_401k_employer
        employee_401k_total = h_401k_employee

    hsa_employee_total = h_hsa["employee"] + (w_hsa["employee"] if second_person_enabled else 0.0)
    hsa_employer_total = h_hsa["employer"] + (w_hsa["employer"] if second_person_enabled else 0.0)
    hsa_total_contributions = hsa_employee_total + hsa_employer_total

    gross_income = (
        income["total"]
        + employee_401k_total
        + emergency_pre_tax_used
        + hsa_employee_total
        + taxable_hsa_withdrawal
    )

    net_profit = net_income - expense_amt - funded_roth_contributions["total"]

    # Preserve existing person-level tax allocation timing. This intentionally occurs
    # after portfolio returns and rebalancing, matching the current run_sim_core.py.
    if second_person_enabled:
        husband_income_for_tax_alloc = income["by_person"]["husband"] + husband_roth_conversion
        wife_income_for_tax_alloc = income["by_person"]["wife"] + wife_roth_conversion

        if emergency_pre_tax_used > 0.0:
            h_pre = h_port.total_value_pre
            w_pre = w_port.total_value_pre
            total_pre = h_pre + w_pre

            if total_pre > 0.0:
                husband_income_for_tax_alloc += emergency_pre_tax_used * h_pre / total_pre
                wife_income_for_tax_alloc += emergency_pre_tax_used * w_pre / total_pre
            else:
                husband_income_for_tax_alloc += emergency_pre_tax_used / 2.0
                wife_income_for_tax_alloc += emergency_pre_tax_used / 2.0

        expected_person_income_total = income["total"] + emergency_pre_tax_used + roth_conversion_total
        actual_person_income_total = husband_income_for_tax_alloc + wife_income_for_tax_alloc

        if abs(actual_person_income_total - expected_person_income_total) > 1e-6:
            raise RuntimeError("Person-level income does not match household income")

        husband_tax_alloc, wife_tax_alloc = taxEngine.allocate_tax_proportionally_couple(
            total_tax,
            husband_income_for_tax_alloc,
            wife_income_for_tax_alloc,
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