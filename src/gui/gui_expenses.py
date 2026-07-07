# gui_expenses.py

import tkinter as tk
from tkinter import ttk

from src.utils.tooltip import Tooltip

class ExpensesEditFrame(ttk.Frame):
    """
    Edit a dynamic list of yearly expenses stored in a DynamicExpenses object.
    Each expense has: start_year, end_year, cost, comment.
    """

    def __init__(self, parent, expensesDict, title="Expenses"):
        super().__init__(parent, padding=10)
        self.expensesDict = expensesDict  # DynamicExpenses instance

        # Title
        ttk.Label(self, text=title, font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=5, pady=(0,5))

        INTRO_TEXT = (
            "Expenses (not including federal or state taxes)\n"
            "  Taxes are calculated by the simulator:\n"
        )

        # Intro label, italicized and wrapped
        ttk.Label(
            self,
            text=INTRO_TEXT,
            justify="left",
            wraplength=400,
            font=("Arial", 11, "italic")
        ).grid(row=1, column=0, columnspan=5, sticky="w", pady=(0, 8))
        # Row 1: Headers
        headers = ["Start Year", "End Year", "Cost", "Comment", "Delete"]
        for col, header in enumerate(headers):
            ttk.Label(self, text=header).grid(row=2, column=col, padx=5, pady=2)

        # Storage for temporary variables per row
        self.row_vars = []

        # Track next row index (start after title + header)
        self.next_row = 3  # row 0: title, row 1: intro, row2: headers

        # Populate initial expenses
        for exp in self.expensesDict.expenses:
            self._add_expense_row(exp)

        # Button to add new expense
        self.add_button = ttk.Button(self,text="Add Expense",command=self._add_new_expense)
        self.add_button.grid(row=999, column=0, pady=(10,5), sticky="w")  # temporary row; updated dynamically
        Tooltip(self.add_button, "Click to add a new expense row",
            font=("Arial", 11)) 

        # Ensure Add Expense button is correctly positioned
        self._update_add_button_position()


    def _add_new_expense(self):
        expense = {
            "start_year": None,
            "end_year": None,
            "cost": None,
            "comment": ""
        }

        self.expensesDict.expenses.append(expense)
        self._add_expense_row(expense)

    def _add_expense_row(self, expense):
        """
        Add a UI row bound directly to an existing expense dict.
        """
        row = self.next_row

        start_var = tk.StringVar(value=str(expense["start_year"]))
        end_var = tk.StringVar(value="" if expense["end_year"] is None else str(expense["end_year"]))
        cost_var = tk.StringVar(value=str(expense["cost"]))
        comment_var = tk.StringVar(value=str(expense["comment"]))

        comment_var.trace_add(
            "write",
            lambda *_: expense.__setitem__("comment", comment_var.get())
        )

        # --- UI widgets ---

        vcmd_start = (
            self.register(self._validate_expense_field_on_focusout),
            "%P",
            str(id(expense)),
            "start_year",
        )
        start_entry = ttk.Entry(
            self,
            textvariable=start_var,
            width=10,
            validate="focusout",
            validatecommand=vcmd_start,
        )
        start_entry.grid(row=row, column=0, padx=5, pady=2)
        Tooltip(start_entry, "Year this expense starts", font=("Arial", 11))

        vcmd_end = (
            self.register(self._validate_expense_field_on_focusout),
            "%P",
            str(id(expense)),
            "end_year",
        )
        end_entry = ttk.Entry(
            self,
            textvariable=end_var,
            width=10,
            validate="focusout",
            validatecommand=vcmd_end,
        )
        end_entry.grid(row=row, column=1, padx=5, pady=2)
        Tooltip(end_entry, "Year this expense ends (leave blank if ongoing)", font=("Arial", 11))

        vcmd_cost = (
            self.register(self._validate_expense_field_on_focusout),
            "%P",
            str(id(expense)),
            "cost",
        )
        cost_entry = ttk.Entry(
            self,
            textvariable=cost_var,
            width=10,
            validate="focusout",
            validatecommand=vcmd_cost,
        )
        cost_entry.grid(row=row, column=2, padx=5, pady=2)
        Tooltip(cost_entry, "Cost of this expense per year", font=("Arial", 11))

        comment_entry = ttk.Entry(self, textvariable=comment_var, width=20)
        comment_entry.grid(row=row, column=3, padx=5, pady=2)
        Tooltip(comment_entry, "Optional comment or description",
            font=("Arial", 11))

        del_button = ttk.Button(
            self,
            text="Delete",
            command=lambda e=expense, r=row: self._delete_row(e)
        )
        del_button.grid(row=row, column=4, padx=5, pady=2)
        Tooltip(del_button, "Delete this expense row",
            font=("Arial", 11))

        self.row_vars.append({
            "row": row,
            "expense": expense,
            "start_var": start_var,
            "end_var": end_var,
            "cost_var": cost_var,
            "comment_var": comment_var,
            "widgets": [start_entry, end_entry, cost_entry, comment_entry, del_button]
        })

        self.next_row += 1
        self._update_add_button_position()


    def _find_row_item(self, expense_id_str):
        for item in self.row_vars:
            if str(id(item["expense"])) == expense_id_str:
                return item
        return None


    def _parse_expense_field(self, field_key, raw_value):
        text = raw_value.strip().replace(",", "")

        if field_key == "start_year":
            if text == "":
                raise ValueError("Start year is required.")
            if text in {"-", "+"}:
                raise ValueError("Invalid year.")
            value = int(text)
            if value < 1900 or value > 3000:
                raise ValueError("Invalid year.")
            return value

        if field_key == "end_year":
            if text == "":
                return None
            if text in {"-", "+"}:
                raise ValueError("Invalid year.")
            value = int(text)
            if value < 1900 or value > 3000:
                raise ValueError("Invalid year.")
            return value

        if field_key == "cost":
            if text == "":
                raise ValueError("Cost is required.")
            if text in {"-", "+", ".", "-.", "+."}:
                raise ValueError("Invalid cost.")
            value = float(text)
            if value < 0:
                raise ValueError("Cost cannot be negative.")
            return value

        raise ValueError(f"Unknown field: {field_key}")


    def _format_expense_field(self, field_key, value):
        if field_key in {"start_year", "end_year"}:
            if value in ("", None):
                return ""
            return str(int(value))

        if field_key == "cost":
            if value in ("", None):
                return ""
            return f"{float(value):,.0f}"

        return str(value)


    def _validate_expense_cross_fields(self, expense):
        start_year = expense.get("start_year")
        end_year = expense.get("end_year")

        if start_year in ("", None):
            raise ValueError("Start year is required.")

        if end_year is not None and end_year < start_year:
            raise ValueError("End year cannot be before start year.")


    def _validate_expense_field_on_focusout(self, proposed_value, expense_id_str, field_key):
        item = self._find_row_item(expense_id_str)
        if item is None:
            return True

        expense = item["expense"]

        original_start = expense.get("start_year")
        original_end = expense.get("end_year")
        original_cost = expense.get("cost")

        try:
            parsed = self._parse_expense_field(field_key, proposed_value)
            expense[field_key] = parsed
            self._validate_expense_cross_fields(expense)

            if field_key == "start_year":
                self.after_idle(
                    lambda: item["start_var"].set(
                        self._format_expense_field(field_key, parsed)
                    )
                )
            elif field_key == "end_year":
                self.after_idle(
                    lambda: item["end_var"].set(
                        self._format_expense_field(field_key, parsed)
                    )
                )
            elif field_key == "cost":
                self.after_idle(
                    lambda: item["cost_var"].set(
                        self._format_expense_field(field_key, parsed)
                    )
                )

            return True

        except ValueError:
            expense["start_year"] = original_start
            expense["end_year"] = original_end
            expense["cost"] = original_cost

            self.after_idle(
                lambda: item["start_var"].set(
                    self._format_expense_field("start_year", original_start)
                )
            )
            self.after_idle(
                lambda: item["end_var"].set(
                    self._format_expense_field("end_year", original_end)
                )
            )
            self.after_idle(
                lambda: item["cost_var"].set(
                    self._format_expense_field("cost", original_cost)
                )
            )

            self.bell()
            return True


    def _delete_row(self, expense):
        """
        Remove UI row and immediately remove the expense from the model.
        Reassign grid rows to maintain continuity.
        """
        # Remove expense from model and destroy widgets
        for item in self.row_vars:
            if item["expense"] == expense:
                for w in item["widgets"]:
                    w.destroy()
                self.row_vars.remove(item)
                break

        if expense in self.expensesDict.expenses:
            self.expensesDict.expenses.remove(expense)

        # Re-grid all remaining rows
        self._regrid_rows()

    def _regrid_rows(self):
        """
        Reassigns grid row numbers for all current expense rows.
        Ensures Add button is immediately after last row.
        """
        for i, item in enumerate(self.row_vars):
            row_index = 3 + i   # row 0: title, row 1: intro, row2: headers
            for col, widget in enumerate(item["widgets"]):
                widget.grid_configure(row=row_index, column=col)
            item["row"] = row_index

        # Update next_row and reposition Add button
        self.next_row = 3 + len(self.row_vars)
        self._update_add_button_position()

    def _update_add_button_position(self):
        if not hasattr(self, "add_button"):
            return
        self.add_button.grid_configure(row=self.next_row, column=0, sticky="w")
