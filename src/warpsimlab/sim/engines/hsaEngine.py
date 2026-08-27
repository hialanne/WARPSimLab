from . import portfolioEngine


def calculate_hsa_contributions(person, current_age, year, gross_wages, employee_401k_contribution, sim_config):
    """
    Calculate employee and employer HSA contributions for one person.

    Employee HSA contributions:
      - require positive work income
      - stop at retirement
      - are capped by wages remaining after the employee 401(k) contribution

    Employer HSA contributions:
      - require positive work income
      - stop at retirement
      - are not deducted from employee wages

    WARPSimLab does not enforce HSA eligibility or statutory contribution limits.
    """
    gross_wages = max(0.0, float(gross_wages))

    if current_age >= person.retire_age or gross_wages <= 0.0:
        return {"employee": 0.0, "employer": 0.0, "total": 0.0}

    if not hasattr(sim_config, "_income_inflation_factors"):
        raise RuntimeError("Income engine not initialized before HSA contribution calculation.")

    infl_factor = sim_config._income_inflation_factors[year]

    requested_employee = max(0.0, float(person.annual_hsa_contribution) * infl_factor)
    requested_employer = max(0.0, float(person.annual_hsa_employer_contribution) * infl_factor)

    available_employee_wages = max(0.0, gross_wages - max(0.0, float(employee_401k_contribution)))
    employee_contribution = min(requested_employee, available_employee_wages)
    employer_contribution = requested_employer

    return {
        "employee": employee_contribution,
        "employer": employer_contribution,
        "total": employee_contribution + employer_contribution,
    }


def apply_employee_hsa_to_income(income, employee_contribution, person_key):
    """
    Reduce spendable and taxable work income for an employee HSA contribution.
    """
    if employee_contribution <= 0.0:
        return

    income["total"] -= employee_contribution
    income["by_person"][person_key] -= employee_contribution
    income["by_class"]["work"] -= employee_contribution


def deposit_hsa_contributions(sim_portfolio, contributions):
    """
    Deposit employee and employer HSA contributions into one person's HSA.
    """
    amount = contributions["total"]

    if amount <= 0.0:
        return 0.0

    return portfolioEngine.apply_hsa_contribution(sim_portfolio, amount)