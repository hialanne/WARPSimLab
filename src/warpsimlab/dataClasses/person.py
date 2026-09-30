# person.py


class Person:
    def __init__(
        self, age, retire_age, income, ss, ss_age, pension, pension_age, annuity, annuity_age,
        annual_401k_contribution=0.0, annual_employer_match=0.0, annual_hsa_contribution=0.0,
        annual_hsa_employer_contribution=0.0, pension_inflation_adjustment_pct=0.0,
        modeled_death_age=None, medicare_start_age=65, medicare_annual_cost=0.0
    ):
        self.age = age
        self.retire_age = retire_age
        self.income = income
        self.ss = ss
        self.ss_age = ss_age
        self.pension = pension
        self.pension_age = pension_age
        self.annuity = annuity
        self.annuity_age = annuity_age
        self.annual_401k_contribution = annual_401k_contribution
        self.annual_employer_match = annual_employer_match
        self.annual_hsa_contribution = annual_hsa_contribution
        self.annual_hsa_employer_contribution = annual_hsa_employer_contribution
        self.pension_inflation_adjustment_pct = pension_inflation_adjustment_pct
        self.modeled_death_age = modeled_death_age
        self.medicare_start_age = medicare_start_age
        self.medicare_annual_cost = medicare_annual_cost