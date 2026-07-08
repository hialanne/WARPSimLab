# dynamicExpenses.py

class DynamicExpenses:
    """
    Hold a dynamic list of yearly expenses.
    Each expense is a dict with: start_year, end_year (optional), cost, comment
    """

    def __init__(self):
        self.expenses = []

    def add_expense(self, start_year, cost, end_year=None, comment=""):
        """
        Add a new expense.
        """
        expense = {
            "start_year": start_year,
            "end_year": end_year,
            "cost": cost,
            "comment": comment
        }
        self.expenses.append(expense)

    def remove_expense(self, index):
        """
        Remove expense by index.
        """
        if 0 <= index < len(self.expenses):
            self.expenses.pop(index)
        else:
            raise IndexError("Expense index out of range")

    def update_expense(self, index, start_year=None, cost=None, end_year=None, comment=None):
        """
        Update fields of an existing expense by index.
        Only provided fields will be updated.
        """
        if 0 <= index < len(self.expenses):
            exp = self.expenses[index]
            if start_year is not None:
                exp["start_year"] = start_year
            if end_year is not None:
                exp["end_year"] = end_year
            if cost is not None:
                exp["cost"] = cost
            if comment is not None:
                exp["comment"] = comment
        else:
            raise IndexError("Expense index out of range")

    def get_expenses(self):
        """
        Return a copy of all expenses for safe GUI iteration.
        """
        return [exp.copy() for exp in self.expenses]

    def get_total_expense_for_year(self, year):
        """
        Return the total cost of all expenses applicable for the given year.
        Open-ended expenses (end_year=None) are considered ongoing indefinitely.
        """
        total = 0
        for exp in self.expenses:
            start = exp["start_year"]
            end = exp["end_year"]  # could be None
            # if end is None, treat it as "forever" / no limit
            if end is None or start <= year <= end:
                if year >= start:  # always after start year
                    total += exp["cost"]
        return total
