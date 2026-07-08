# gui_taxes.py

import tkinter as tk
from tkinter import ttk


class TaxesEditFrame(ttk.Frame):
    """
    Tax-related controls.
    """

    FILING_STATUSES = (
        "Single",
        "Married filing jointly",
    )

    US_STATES = (
        "",  # allows "no selection"
        "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
        "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
        "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
        "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
        "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"
    )

    def __init__(self, parent, control_vars, title="Taxes", **kwargs):
        super().__init__(parent, padding=10, **kwargs)

        self.controls = control_vars["_controls_dict"]

        ttk.Label(self, text=title, font=("Arial", 12, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        self._row = 1

        self._add_section_header("Federal Taxes")
        self._add_text("Taxes are approximated.  Examples are:")
        self._add_text("  100% of social security is taxed.")
        self._add_text("  After tax interest and dividends are not taxed until spent.")


        self._add_calculate_income_taxes()
        self._add_filing_status()

        self._add_separator()

        self._add_section_header("State Taxes")
        self._add_calculate_state_taxes()
        self._add_state_selector()

        self._add_separator()

        self._add_section_header("Payroll Taxes")
        self._add_calculate_payroll_taxes()

        self._sync_state_tax_enabled()

    # ------------------------------------------------
    # Helpers
    # ------------------------------------------------
    def _next_row(self):
        r = self._row
        self._row += 1
        return r

    # ------------------------------------------------
    # Controls
    # ------------------------------------------------
    def _add_calculate_income_taxes(self):
        key = "calculate_income_taxes"

        if key not in self.controls:
            raise KeyError(f"{key} not found in simulation_controls")

        var = tk.BooleanVar(value=self.controls[key])

        var.trace_add(
            "write",
            lambda *args: (
                self.controls.__setitem__(key, var.get()),
                self._sync_state_tax_enabled()
            )
        )

        ttk.Checkbutton(
            self,
            text="Calculate Income Taxes",
            variable=var
        ).grid(
            row=self._next_row(),
            column=0,
            sticky="w",
            pady=(5, 8)
        )


    def _add_calculate_payroll_taxes(self):
        key = "calculate_payroll_taxes"

        if key not in self.controls:
            raise KeyError(f"{key} not found in simulation_controls")

        var = tk.BooleanVar(value=self.controls[key])

        var.trace_add(
            "write",
            lambda *args: self.controls.__setitem__(key, var.get())
        )

        ttk.Checkbutton(
            self,
            text="Calculate Payroll Taxes",
            variable=var
        ).grid(
            row=self._next_row(),
            column=0,
            sticky="w",
            pady=(2, 8)
        )


    def _add_calculate_state_taxes(self):
        key = "calculate_state_taxes"

        if key not in self.controls:
            raise KeyError(f"{key} not found in simulation_controls")

        var = tk.BooleanVar(value=self.controls[key])

        var.trace_add(
            "write",
            lambda *args: self.controls.__setitem__(key, var.get())
        )

        cb = ttk.Checkbutton(
            self,
            text="Calculate State Income Taxes",
            variable=var
        )

        cb.grid(
            row=self._next_row(),
            column=0,
            sticky="w",
            pady=(2, 2)
        )


    def _add_state_selector(self):
        key = "state_of_residence"

        if key not in self.controls:
            raise KeyError(f"{key} not found in simulation_controls")

        ttk.Label(
            self,
            text="State of Residence"
        ).grid(
            row=self._next_row(),
            column=0,
            sticky="w",
            pady=(2, 2)
        )

        var = tk.StringVar(value=self.controls[key])

        combo = ttk.Combobox(
            self,
            textvariable=var,
            values=self.US_STATES,
            state="readonly",
            width=6
        )

        combo.grid(
            row=self._next_row(),
            column=0,
            sticky="w",
            pady=(0, 8)
        )

        var.trace_add(
            "write",
            lambda *args: self.controls.__setitem__(key, var.get())
        )

        self._state_combo = combo
        self._state_var = var


    def _add_filing_status(self):
        key = "tax_filing_status"

        if key not in self.controls:
            raise KeyError(f"{key} not found in simulation_controls")

        ttk.Label(
            self,
            text="Tax Filing Status"
        ).grid(
            row=self._next_row(),
            column=0,
            sticky="w",
            pady=(2, 2)
        )

        var = tk.StringVar(value=self.controls[key])

        combo = ttk.Combobox(
            self,
            textvariable=var,
            values=self.FILING_STATUSES,
            state="readonly",
            width=28
        )

        combo.grid(
            row=self._next_row(),
            column=0,
            sticky="w",
            pady=(0, 8)
        )

        var.trace_add(
            "write",
            lambda *args: self.controls.__setitem__(key, var.get())
        )


    def _sync_state_tax_enabled(self):
        federal_on = self.controls["calculate_income_taxes"]

        state = "readonly" if federal_on else "disabled"
        self._state_combo.configure(state=state)


    def _add_section_header(self, text):
        ttk.Label(
            self,
            text=text,
            font=("Arial", 10, "bold")
        ).grid(
            row=self._next_row(),
            column=0,
            sticky="w",
            pady=(6, 2)
        )


    def _add_text(self, text):
        ttk.Label(
            self,
            text=text,
            font=("Arial", 10)
        ).grid(
            row=self._next_row(),
            column=0,
            sticky="w",
            pady=(2, 2)
        )


    def _add_separator(self, pady=(6, 6)):
        ttk.Separator(self, orient="horizontal").grid(
            row=self._next_row(),
            column=0,
            sticky="ew",
            pady=pady
        )
