# gui_portfolioSimulation.py

import tkinter as tk
from tkinter import ttk

from src.warpsimlab.utils.tooltip import Tooltip

class PortfolioSimulationEditFrame(ttk.Frame):
    """
    Frame to edit portfolio simulation settings.

    This editor modifies values directly inside the provided
    sim_vars["_settings_dict"] dictionary.

    Boolean and radiobutton controls update immediately using Tkinter
    variable traces. Numeric entry fields validate and save on focus-out.
    There is no separate save step.

    Settings include:
        - Simulation time horizon and number of Monte Carlo runs
        - Optional fund expense modeling
        - Portfolio rebalance strategy (preset or custom allocation)

    Custom allocation fields are shown only when "Custom" rebalance
    is selected.
    """
    
    def __init__(self, parent, sim_vars, title="Simulation Settings"):
        super().__init__(parent, padding=10)
        self.sim_vars = sim_vars  # sim_vars["_settings_dict"] contains the main Python dict

        settings = self.sim_vars["_settings_dict"]

        self.tooltips_text = {
            "start_year_var": "The calendar year at which the simulation begins.",
            "years_to_simulate_var": "Number of years to simulate. Must be a positive integer.",
            "sims_var": "Number of simulation runs to perform for Monte Carlo analysis. Higher numbers give more accurate distributions.",
            "use_fund_expenses_var": "If selected, the simulation deducts fund expenses annually from the portfolio.",
            "fund_expense_var": "Average annual fund expenses as a percentage. Only active if 'Use and Show Fund Expenses' is checked.",
            "maintain-current-allocation": "Choose to maintain the current portfolio allocation,\nor chose a pre-set rebalance strategy or use 'Custom' to define your own portfolio allocations.  \nPercentages are Stocks, Bonds and Cash",
            "custom_stock_var": "Custom percentage of your portfolio allocated to stocks.",
            "custom_bonds_var": "Custom percentage of your portfolio allocated to bonds.",
            "custom_cash_var": "Custom percentage of your portfolio allocated to cash."
        }

        self.columnconfigure(0, weight=0)  # radiobuttons
        self.columnconfigure(1, weight=0)  # labels for custom block
        self.columnconfigure(2, weight=1)  # entries for custom block (expand if room)

        row = 0

        ttk.Label(self, text=title, font=("Arial", 12, "bold")).grid(row=row, column=0, sticky="w", pady=(0, 5))
        row += 1

        ttk.Label(self, text="Start year to simulate:").grid(row=row, column=0, sticky="w")
        self.start_year_var = tk.StringVar(value=self._format_sim_field("start_year", settings["start_year"]))
        vcmd = (self.register(self._validate_sim_field), "%P", "start_year")

        self.start_year_entry = ttk.Entry(
            self,
            textvariable=self.start_year_var,
            width=14,
            validate="focusout",
            validatecommand=vcmd
        )

        self.start_year_entry.grid(row=row, column=1, sticky="w")
        Tooltip(self.start_year_entry, self.tooltips_text["start_year_var"], font=("Arial", 11))
        row += 1

        ttk.Label(self, text="Years to Simulate:").grid(row=row, column=0, sticky="w")
        self.years_to_simulate_var = tk.StringVar(value=self._format_sim_field("years_to_simulate", settings["years_to_simulate"]))

        vcmd = (self.register(self._validate_sim_field), "%P", "years_to_simulate")

        self.years_to_simulate_entry = ttk.Entry(
            self,
            textvariable=self.years_to_simulate_var,
            width=14,
            validate="focusout",
            validatecommand=vcmd
        )

        self.years_to_simulate_entry.grid(row=row, column=1, sticky="w")
        Tooltip(self.years_to_simulate_entry, self.tooltips_text["years_to_simulate_var"], font=("Arial", 11))
        row += 1

        ttk.Label(self, text="Number of Simulations:").grid(row=row, column=0, sticky="w")

        self.sims_var = tk.StringVar(value=self._format_sim_field("num_sims", settings["num_sims"]))

        vcmd = (self.register(self._validate_sim_field), "%P", "num_sims")

        self.sims_entry = ttk.Entry(
            self,
            textvariable=self.sims_var,
            width=14,
            validate="focusout",
            validatecommand=vcmd
        )

        self.sims_entry.grid(row=row, column=1, sticky="w")
        Tooltip(self.sims_entry, self.tooltips_text["sims_var"], font=("Arial", 11))
        row += 1


        sep1 = ttk.Separator(self, orient="horizontal")
        sep1.grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1

        # --- Fund Expense Options ---
        ttk.Label(self, text="Simulate Fund Expense Impacts", font=("Arial", 12, "bold")).grid(row=row, column=0, sticky="w", pady=(0, 2))
        row += 1

        self.use_fund_expenses_var = tk.BooleanVar(value=settings["use_fund_expenses"])
        self.use_fund_expenses_cb = ttk.Checkbutton(self,text="Use and Show Fund Expenses",variable=self.use_fund_expenses_var)
        self.use_fund_expenses_cb.grid(row=row, column=0, sticky="w")
        Tooltip(self.use_fund_expenses_cb,self.tooltips_text["use_fund_expenses_var"],font=("Arial", 11))
        self._bind_var(self.use_fund_expenses_var,lambda x, s=settings: s.__setitem__("use_fund_expenses", x))
        row += 1

        ttk.Label(self, text="Average fund expenses annual (%):").grid(row=row, column=0, sticky="w")
        self.fund_expense_var = tk.StringVar(value=self._format_sim_field("fund_expense", settings["fund_expense"]))
        vcmd = (self.register(self._validate_sim_field), "%P", "fund_expense")

        self.fund_expense_entry = ttk.Entry(
            self,
            textvariable=self.fund_expense_var,
            width=12,
            validate="focusout",
            validatecommand=vcmd
        )

        self.fund_expense_entry.grid(row=row, column=1, sticky="w", padx=5)
        Tooltip(self.fund_expense_entry,self.tooltips_text["fund_expense_var"],font=("Arial", 11))
        self.use_fund_expenses_var.trace_add("write", lambda *args: self._toggle_fund_expense_entry())
        self._toggle_fund_expense_entry()
        row += 1

        sep2 = ttk.Separator(self, orient="horizontal")
        sep2.grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1

        # --- Rebalance Options ---
        ttk.Label(self, text="Simulate Re-balanced Portfolio", font=("Arial", 12, "bold")).grid(row=row, column=0, sticky="w")
        row += 1

        self.rebalance_var = tk.StringVar(value=settings["rebalance"])
        self._bind_var(self.rebalance_var, lambda x, s=settings: s.__setitem__("rebalance", x))

        # Create Radiobuttons as variables
        rb_current = ttk.Radiobutton(self, text="Maintain Current Allocation", variable=self.rebalance_var, value="maintain-current-allocation")
        rb_dont = ttk.Radiobutton(self, text="Don't Rebalance", variable=self.rebalance_var, value="dont-rebalance")
        rb_30 = ttk.Radiobutton(self, text="Conservative (30-30-40)", variable=self.rebalance_var, value="30-30-40")
        rb_50 = ttk.Radiobutton(self, text="Balanced (50-30-20)", variable=self.rebalance_var, value="50-30-20")
        rb_70 = ttk.Radiobutton(self, text="Agressive (70-20-10)", variable=self.rebalance_var, value="70-20-10")
        rb_custom = ttk.Radiobutton(self, text="Custom", variable=self.rebalance_var, value="custom")

        # Place them with grid
        for i, rb in enumerate([rb_current, rb_dont, rb_30, rb_50, rb_70, rb_custom]):
            rb.grid(row=row + i, column=0, columnspan=2, sticky="w", pady=0 )

        self.custom_anchor_row = row + 4  # rb_70 is the 5th item in the list (0-based index 4)
        
        # Attach tooltip to one or more of the Radiobuttons (e.g., first one)
        Tooltip(rb_current, self.tooltips_text["maintain-current-allocation"], font=("Arial", 11))

        # --- Custom portfolio entries ---
        self.custom_stock_var = tk.StringVar(value=self._format_sim_field("custom_stock", settings["custom_stock"]))
        self.custom_bonds_var = tk.StringVar(value=self._format_sim_field("custom_bonds", settings["custom_bonds"]))
        self.custom_cash_var = tk.StringVar(value=self._format_sim_field("custom_cash", settings["custom_cash"]))

        self.custom_stock_label = ttk.Label(self, text="Percent Stock:")

        vcmd = (self.register(self._validate_sim_field), "%P", "custom_stock")

        self.custom_stock_entry = ttk.Entry(
            self,
            textvariable=self.custom_stock_var,
            width=14,
            validate="focusout",
            validatecommand=vcmd
        )
        self.custom_bonds_label = ttk.Label(self, text="Percent Bonds:")

        vcmd = (self.register(self._validate_sim_field), "%P", "custom_bonds")

        self.custom_bonds_entry = ttk.Entry(
            self,
            textvariable=self.custom_bonds_var,
            width=14,
            validate="focusout",
            validatecommand=vcmd
        )

        self.custom_cash_label = ttk.Label(self, text="Percent Cash:")

        vcmd = (self.register(self._validate_sim_field), "%P", "custom_cash")

        self.custom_cash_entry = ttk.Entry(
            self,
            textvariable=self.custom_cash_var,
            width=14,
            validate="focusout",
            validatecommand=vcmd
        )

        self.rebalance_var.trace_add("write", lambda *args: self.toggle_custom_entries())
        self.toggle_custom_entries()  # initialize visibility

    # ------------------------
    # Helper methods
    # ------------------------
    def _toggle_fund_expense_entry(self):
        if self.use_fund_expenses_var.get():
            self.fund_expense_entry.config(state="normal")
        else:
            self.fund_expense_entry.config(state="disabled")


    def toggle_custom_entries(self):
        if self.rebalance_var.get() == "custom":
            r = self.custom_anchor_row  # align with "70-20-10"

            # Shift the whole custom block to the right within the existing 2-column form,
            # so it visually sits to the right of the radiobuttons but DOES NOT add new columns.
            label_padx = (140, 5)  # adjust this number to tuck labels into the empty space
            entry_padx = (0, 0)

            self.custom_stock_label.grid(row=r, column=0, sticky="w", padx=label_padx, pady=0)
            self.custom_stock_entry.grid(row=r, column=1, sticky="w", padx=entry_padx, pady=0)
            Tooltip(self.custom_stock_entry, self.tooltips_text["custom_stock_var"], font=("Arial", 11))

            self.custom_bonds_label.grid(row=r + 1, column=0, sticky="w", padx=label_padx, pady=0)
            self.custom_bonds_entry.grid(row=r + 1, column=1, sticky="w", padx=entry_padx, pady=0)
            Tooltip(self.custom_bonds_entry, self.tooltips_text["custom_bonds_var"], font=("Arial", 11))

            self.custom_cash_label.grid(row=r + 2, column=0, sticky="w", padx=label_padx, pady=0)
            self.custom_cash_entry.grid(row=r + 2, column=1, sticky="w", padx=entry_padx, pady=0)
            Tooltip(self.custom_cash_entry, self.tooltips_text["custom_cash_var"], font=("Arial", 11))
        else:
            self.custom_stock_label.grid_forget()
            self.custom_stock_entry.grid_forget()
            self.custom_bonds_label.grid_forget()
            self.custom_bonds_entry.grid_forget()
            self.custom_cash_label.grid_forget()
            self.custom_cash_entry.grid_forget()


    def _parse_sim_field(self, field, value):

        text = value.strip()

        if text == "":
            raise ValueError("Blank")

        if text in {"-", "+", ".", "-.", "+."}:
            raise ValueError("Invalid")

        if field in {"start_year", "years_to_simulate", "num_sims"}:
            v = int(text)

            if v <= 0:
                raise ValueError("Invalid")

            return v

        v = float(text)

        v = float(text)

        if field in {"fund_expense", "custom_stock", "custom_bonds", "custom_cash"} and v < 0:
            raise ValueError("Invalid")

        return v


    def _format_sim_field(self, field, value):

        if field in {"start_year", "years_to_simulate", "num_sims"}:
            return str(int(value))

        return f"{value:.2f}".rstrip("0").rstrip(".")


    def _validate_sim_field(self, proposed_value, field):

        settings = self.sim_vars["_settings_dict"]

        var_name = "sims_var" if field == "num_sims" else f"{field}_var"
        var = getattr(self, var_name)

        current_value = settings[field]

        try:
            parsed = self._parse_sim_field(field, proposed_value)
            settings[field] = parsed
            self.after_idle(lambda: var.set(self._format_sim_field(field, parsed)))
            return True

        except ValueError:
            self.after_idle(lambda: var.set(self._format_sim_field(field, current_value)))
            self.bell()
            return True


    def _bind_var(self, var, setter, cast=None):
        def callback(*_):
            try:
                value = var.get()
                if cast:
                    value = cast(value)
                setter(value)
            except (ValueError, TypeError):
                pass  # ignore invalid intermediate input
        var.trace_add("write", callback)
