# person.py
class Person:
    def __init__(
        self, 
        age, 
        retire_age, 
        income, 
        ss, 
        ss_age, 
        pension, 
        pension_age, 
        annuity, 
        annuity_age,
        annual_401k_contribution=0.0,
        annual_employer_match=0.0,
        pension_inflation_adjustment_pct=0.0,
    ):
        self.age = age  # Current age
        self.retire_age = retire_age  # Age when they retire
        self.income = income  # Annual income
        self.ss = ss  # Social Security amount
        self.ss_age = ss_age  # Social Security amount
        self.pension = pension  # Pension amount
        self.pension_age = pension_age  # Age at which pension kicks in
        self.annuity = annuity  # Annuity amount
        self.annuity_age = annuity_age  # Age at which annuity kicks in
        self.annual_401k_contribution = annual_401k_contribution
        self.annual_employer_match = annual_employer_match 
        self.pension_inflation_adjustment_pct = pension_inflation_adjustment_pct 
