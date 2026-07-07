# gui_normalIncome.py

import tkinter as tk
from tkinter import ttk

from src.utils.tooltip import Tooltip

class NormalIncomeEditFrame(ttk.Frame):
    """
    Edit personal data for Husband and optional Wife.
    This frame owns all Tkinter StringVars and writes changes
    directly back to the Person objects on Save.

    persons = {
        "husband": Person,
        "wife": Person   # optional
    }
    """

    def __init__(
        self,
        parent,
        persons,
        simulation_controls=None,
        refresh_callback=None,
        title="Edit Person",
        mode="Basic",
        **kwargs
    ):
        super().__init__(parent, padding=10, **kwargs)
        self.persons = persons
        self.title = title
        self.simulation_controls = simulation_controls
        self.refresh_callback = refresh_callback
        self.mode = mode

        self._enable_second_person_var = tk.BooleanVar(
            value=self.simulation_controls["enable_second_person"]
        )

        self._enable_second_person_var.trace_add(
            "write",
            self._on_enable_second_person_changed
        )

        def fmt_money(value):
            return f"{float(value):,.0f}"

        # Build internal StringVars from Person objects
        self.vars = {}
        for key, person in persons.items():
            self.vars[key] = {
                "age": tk.StringVar(value=str(person.age)),
                "income": tk.StringVar(value=fmt_money(person.income)),
                "retire_age": tk.StringVar(value=str(person.retire_age)),
                "ss": tk.StringVar(value=fmt_money(person.ss)),
                "ss_age": tk.StringVar(value=str(person.ss_age)),
                "pension": tk.StringVar(value=fmt_money(person.pension)),
                "pension_age": tk.StringVar(value=str(person.pension_age)),
                "annuity": tk.StringVar(value=fmt_money(person.annuity)),
                "annuity_age": tk.StringVar(value=str(person.annuity_age)),
                "annual_401k_contribution": tk.StringVar(
                    value=fmt_money(person.annual_401k_contribution)
                ),
                "annual_employer_match": tk.StringVar(
                    value=fmt_money(person.annual_employer_match)
                ),
                "pension_inflation_adjustment_pct": tk.StringVar(
                    value=str(getattr(person, "pension_inflation_adjustment_pct", 0.0))
                ),
            }


        ttk.Label(
            self,
            text="Defines each person's age, income, and retirement timeline used in the simulation.",
            font=("Arial", 11),
            wraplength=600,
            justify="left",
        ).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))

        self._build_fields()


    def _on_enable_second_person_changed(self, *_):
        new_value = self._enable_second_person_var.get()
        self.simulation_controls["enable_second_person"] = new_value

        if self.refresh_callback:
            self.refresh_callback()


    def _build_fields(self):
        husband_vars = self.vars["husband"]
        wife_vars = self.vars.get("wife")

        row = 1

        # Left block headers
        ttk.Label(self, text="Husband", font=("Arial", 12, "bold")).grid(
            row=row, column=1, sticky="w", pady=(10, 5), padx=(30, 0)
        )
        if wife_vars:
            ttk.Label(self, text="Wife", font=("Arial", 12, "bold")).grid(
                row=row, column=2, sticky="w", pady=(10, 5), padx=(30, 0)
            )

        # Right block headers (Full mode only)
        if self.mode != "Basic":
            ttk.Label(self, text="Husband", font=("Arial", 12, "bold")).grid(
                row=row, column=4, sticky="w", pady=(10, 5), padx=(30, 0)
            )
            if wife_vars:
                ttk.Label(self, text="Wife", font=("Arial", 12, "bold")).grid(
                    row=row, column=5, sticky="w", pady=(10, 5), padx=(30, 0)
                )

        row += 1

        fields_full_left = [
            ("Age", "age", "Current age in years"),
            ("Income ($)", "income", "Annual gross earned income"),
            ("Retirement Age", "retire_age", "Age at which earned income stops"),
            (
                "401k / IRA Contribution ($/yr)",
                "annual_401k_contribution",
                "Annual retirement account contribution",
            ),
            (
                "Employer Match ($/yr)",
                "annual_employer_match",
                "Annual employer retirement contribution",
            ),
        ]

        fields_full_right = [
            ("Social Security ($)", "ss", "Annual Social Security benefit"),
            ("Social Security Start Age", "ss_age", "Age Social Security payments begin"),
            ("Pension ($)", "pension", "Annual pension income"),
            ("Pension Start Age", "pension_age", "Age pension payments begin"),
            (
                "Pension Inflation Adjustment (%)",
                "pension_inflation_adjustment_pct",
                "Percent (0-100). You will apply this in the simulator.",
            ),
            ("Annuity ($)", "annuity", "Annual annuity income"),
            ("Annuity Start Age", "annuity_age", "Age annuity payments begin"),
        ]


        fields_basic = [
            ("Age", "age", "Current age in years"),
            ("Income ($)", "income", "Annual gross earned income"),
            ("Retirement Age", "retire_age", "Age at which earned income stops"),
            ("Social Security ($)", "ss", "Annual Social Security benefit"),
        ]


        def _add_row(r, label_text, key, tooltip_text, col_offset):
            label_padx = (25, 5) if col_offset == 3 else 5

            ttk.Label(self, text=label_text).grid(
                row=r, column=0 + col_offset, sticky="w", padx=label_padx, pady=2
            )

            vcmd_h = (
                self.register(self._validate_person_field_on_focusout),
                "%P",
                "husband",
                key,
            )

            entry_h = ttk.Entry(
                self,
                textvariable=husband_vars[key],
                width=14,
                validate="focusout",
                validatecommand=vcmd_h,
            )
            entry_h.grid(row=r, column=1 + col_offset, sticky="w", padx=5)
            Tooltip(entry_h, tooltip_text, font=("Arial", 11))
            
            if wife_vars:
                vcmd_w = (
                    self.register(self._validate_person_field_on_focusout),
                    "%P",
                    "wife",
                    key,
                )

                entry_w = ttk.Entry(
                    self,
                    textvariable=wife_vars[key],
                    width=14,
                    validate="focusout",
                    validatecommand=vcmd_w,
                )
                entry_w.grid(row=r, column=2 + col_offset, sticky="w", padx=5)
                Tooltip(entry_w, tooltip_text, font=("Arial", 11))

        if self.mode == "Basic":
            for label_text, key, tooltip_text in fields_basic:
                _add_row(row, label_text, key, tooltip_text, col_offset=0)
                row += 1
        else:
            # Draw left block
            left_start_row = row
            for label_text, key, tooltip_text in fields_full_left:
                _add_row(row, label_text, key, tooltip_text, col_offset=0)
                row += 1

            # Draw right block starting at same row as left
            right_row = left_start_row
            for label_text, key, tooltip_text in fields_full_right:
                _add_row(right_row, label_text, key, tooltip_text, col_offset=3)
                right_row += 1

            # Continue after whichever block is taller
            row = max(row, right_row)

        ttk.Checkbutton(
            self,
            text="Enable Second Person",
            variable=self._enable_second_person_var,
        ).grid(
            row=row,
            column=0,
            columnspan=6,
            sticky="w",
            padx=5,
            pady=(8, 4),
        )


    def _parse_person_field(self, field_key, raw_value):
        text = raw_value.strip().replace(",", "")

        if text == "":
            raise ValueError("Blank value is not allowed.")

        int_fields = {
            "age",
            "retire_age",
            "ss_age",
            "pension_age",
            "annuity_age",
        }

        float_fields = {
            "income",
            "ss",
            "pension",
            "annuity",
            "annual_401k_contribution",
            "annual_employer_match",
            "pension_inflation_adjustment_pct",
        }

        if field_key in int_fields:
            if text in {"-", "+"}:
                raise ValueError("Invalid integer.")
            value = int(text)

            if value < 0 or value > 120:
                raise ValueError("Invalid age.")

            return value

        if field_key in float_fields:
            cleaned = text
            if cleaned in {"-", "+", ".", "-.", "+."}:
                raise ValueError("Invalid number.")
            if "e" in cleaned.lower():
                raise ValueError("Scientific notation not allowed.")
            value = float(cleaned)
            if field_key != "pension_inflation_adjustment_pct" and value < 0:
                raise ValueError("Value cannot be negative.")
            return value

        raise ValueError(f"Unknown field: {field_key}")


    def _format_person_field(self, field_key, value):
        int_fields = {
            "age",
            "retire_age",
            "ss_age",
            "pension_age",
            "annuity_age",
        }

        money_fields = {
            "income",
            "ss",
            "pension",
            "annuity",
            "annual_401k_contribution",
            "annual_employer_match",
        }

        if field_key in int_fields:
            return str(int(value))

        if field_key in money_fields:
            return f"{float(value):,.0f}"

        if field_key == "pension_inflation_adjustment_pct":
            return str(value)

        return str(value)


    def _validate_person_field_on_focusout(self, proposed_value, person_key, field_key):
        #print("VALIDATE FOCUSOUT", person_key, field_key, repr(proposed_value))
        
        person = self.persons[person_key]
        var = self.vars[person_key][field_key]

        try:
            parsed = self._parse_person_field(field_key, proposed_value)
            setattr(person, field_key, parsed)
            self.after_idle(lambda: var.set(self._format_person_field(field_key, parsed)))
            return True
        except ValueError:
            current_value = getattr(person, field_key)
            self.after_idle(lambda: var.set(self._format_person_field(field_key, current_value)))
            self.bell()
            return True


