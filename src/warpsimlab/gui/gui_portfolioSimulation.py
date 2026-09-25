# gui_portfolioSimulation.py

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox

from src.warpsimlab.gui.gui_validation import mark_validation_failed, parse_finite_float, parse_integer
from src.warpsimlab.utils.tooltip import Tooltip
from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin


class PortfolioSimulationEditFrame(ScalableFrameMixin, ttk.Frame):
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

        self.sim_vars = sim_vars
        settings = self.sim_vars["_settings_dict"]

        self._body_font = tkfont.nametofont("TkDefaultFont").copy()
        self._header_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._header_text_font = tkfont.Font(root=self, family="Arial", size=11)
        self._section_font = tkfont.Font(root=self, family="Arial", size=12, weight="bold")
        self._tooltip_font = tkfont.Font(root=self, family="Arial", size=11)

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._header_font)
        self._register_scalable_font(self._header_text_font)
        self._register_scalable_font(self._section_font)
        self._register_scalable_font(self._tooltip_font)
        self._apply_gui_scale()

        self.tooltips_text = {
            "start_year_var": "The calendar year at which the simulation begins.",
            "years_to_simulate_var": "Number of years to simulate. Must be a positive integer.",
            "sims_var": (
                "Number of simulation runs to perform for Monte Carlo analysis. "
                "Higher numbers give more accurate distributions."
            ),
            "use_fund_expenses_var": (
                "If selected, the simulation deducts fund expenses annually from the portfolio."
            ),
            "fund_expense_var": (
                "Average annual fund expenses as a percentage. "
                "Only active if 'Use and Show Fund Expenses' is checked."
            ),
            "maintain-current-allocation": (
                "Choose to maintain the current portfolio allocation,\n"
                "choose a pre-set rebalance strategy, or use 'Custom' to define your own "
                "portfolio allocations.\n"
                "Percentages are Stocks, Bonds and Cash."
            ),
            "custom_stock_var": "Custom percentage of your portfolio allocated to stocks.",
            "custom_bonds_var": "Custom percentage of your portfolio allocated to bonds.",
            "custom_cash_var": "Custom percentage of your portfolio allocated to cash.",
        }

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)

        row = 0

        header_frame = ttk.Frame(self)
        header_frame.grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Label(
            header_frame, text="Simulation > Settings", font=self._header_font
        ).pack(side="left")

        ttk.Label(
            header_frame,
            text=(
                " - Configure the simulation period, Monte Carlo runs, "
                "fund expenses, and portfolio rebalancing."
            ),
            font=self._header_text_font,
        ).pack(side="left")

        row += 1

        ttk.Label(
            self, text="Start year to simulate:", font=self._body_font
        ).grid(row=row, column=0, sticky="w")

        self.start_year_var = tk.StringVar(
            value=self._format_sim_field("start_year", settings["start_year"])
        )
        vcmd = self.register(self._validate_sim_field), "%P", "start_year"

        self.start_year_entry = ttk.Entry(
            self, textvariable=self.start_year_var, width=14, font=self._body_font,
            validate="focusout", validatecommand=vcmd
        )
        self.start_year_entry.grid(row=row, column=1, sticky="w")

        Tooltip(
            self.start_year_entry, self.tooltips_text["start_year_var"],
            font=self._tooltip_font
        )

        row += 1

        ttk.Label(
            self, text="Years to Simulate:", font=self._body_font
        ).grid(row=row, column=0, sticky="w")

        self.years_to_simulate_var = tk.StringVar(
            value=self._format_sim_field("years_to_simulate", settings["years_to_simulate"])
        )
        vcmd = self.register(self._validate_sim_field), "%P", "years_to_simulate"

        self.years_to_simulate_entry = ttk.Entry(
            self, textvariable=self.years_to_simulate_var, width=14, font=self._body_font,
            validate="focusout", validatecommand=vcmd
        )
        self.years_to_simulate_entry.grid(row=row, column=1, sticky="w")

        Tooltip(
            self.years_to_simulate_entry, self.tooltips_text["years_to_simulate_var"],
            font=self._tooltip_font
        )

        row += 1

        ttk.Label(
            self, text="Number of Simulations:", font=self._body_font
        ).grid(row=row, column=0, sticky="w")

        self.sims_var = tk.StringVar(
            value=self._format_sim_field("num_sims", settings["num_sims"])
        )
        vcmd = self.register(self._validate_sim_field), "%P", "num_sims"

        self.sims_entry = ttk.Entry(
            self, textvariable=self.sims_var, width=14, font=self._body_font,
            validate="focusout", validatecommand=vcmd
        )
        self.sims_entry.grid(row=row, column=1, sticky="w")

        Tooltip(
            self.sims_entry, self.tooltips_text["sims_var"],
            font=self._tooltip_font
        )

        row += 1

        sep1 = ttk.Separator(self, orient="horizontal")
        sep1.grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1

        # --- Fund Expense Options ---
        ttk.Label(
            self, text="Simulate Fund Expense Impacts", font=self._section_font
        ).grid(row=row, column=0, sticky="w", pady=(0, 2))

        row += 1

        self.use_fund_expenses_var = tk.BooleanVar(value=settings["use_fund_expenses"])
        self.use_fund_expenses_cb = ttk.Checkbutton(
            self,
            text="Use and Show Fund Expenses",
            variable=self.use_fund_expenses_var,
            style="PortfolioSimulation.TCheckbutton"
        )
        self.use_fund_expenses_cb.grid(row=row, column=0, sticky="w")

        Tooltip(
            self.use_fund_expenses_cb, self.tooltips_text["use_fund_expenses_var"],
            font=self._tooltip_font
        )

        self._bind_var(
            self.use_fund_expenses_var,
            lambda x, s=settings: s.__setitem__("use_fund_expenses", x)
        )

        row += 1

        ttk.Label(
            self, text="Average fund expenses annual (%):", font=self._body_font
        ).grid(row=row, column=0, sticky="w")

        self.fund_expense_var = tk.StringVar(
            value=self._format_sim_field("fund_expense", settings["fund_expense"])
        )
        vcmd = self.register(self._validate_sim_field), "%P", "fund_expense"

        self.fund_expense_entry = ttk.Entry(
            self, textvariable=self.fund_expense_var, width=12, font=self._body_font,
            validate="focusout", validatecommand=vcmd
        )
        self.fund_expense_entry.grid(row=row, column=1, sticky="w", padx=5)

        Tooltip(
            self.fund_expense_entry, self.tooltips_text["fund_expense_var"],
            font=self._tooltip_font
        )

        self.use_fund_expenses_var.trace_add(
            "write", lambda *args: self._toggle_fund_expense_entry()
        )
        self._toggle_fund_expense_entry()

        row += 1

        sep2 = ttk.Separator(self, orient="horizontal")
        sep2.grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1

        # --- Rebalance Options ---
        ttk.Label(
            self, text="Simulate Re-balanced Portfolio", font=self._section_font
        ).grid(row=row, column=0, sticky="w")

        row += 1

        self.initial_allocation_mode_var = tk.StringVar(
            value=settings["initial_allocation_mode"]
        )
        self._bind_var(
            self.initial_allocation_mode_var,
            lambda x, s=settings: s.__setitem__("initial_allocation_mode", x)
        )

        rb_current = ttk.Radiobutton(
            self, text="Maintain Current Allocation",
            variable=self.initial_allocation_mode_var,
            value="maintain-current-allocation",
            style="PortfolioSimulation.TRadiobutton"
        )
        rb_dont = ttk.Radiobutton(
            self, text="Don't Rebalance",
            variable=self.initial_allocation_mode_var,
            value="dont-rebalance",
            style="PortfolioSimulation.TRadiobutton"
        )
        rb_30 = ttk.Radiobutton(
            self, text="Conservative (30-30-40)",
            variable=self.initial_allocation_mode_var,
            value="30-30-40",
            style="PortfolioSimulation.TRadiobutton"
        )
        rb_50 = ttk.Radiobutton(
            self, text="Balanced (50-30-20)",
            variable=self.initial_allocation_mode_var,
            value="50-30-20",
            style="PortfolioSimulation.TRadiobutton"
        )
        rb_70 = ttk.Radiobutton(
            self, text="Aggressive (70-20-10)",
            variable=self.initial_allocation_mode_var,
            value="70-20-10",
            style="PortfolioSimulation.TRadiobutton"
        )
        rb_custom = ttk.Radiobutton(
            self, text="Custom",
            variable=self.initial_allocation_mode_var,
            value="custom",
            style="PortfolioSimulation.TRadiobutton"
        )

        radiobuttons = [rb_current, rb_dont, rb_30, rb_50, rb_70, rb_custom]

        for i, rb in enumerate(radiobuttons):
            rb.grid(row=row + i, column=0, columnspan=2, sticky="w", pady=0)

        self.custom_anchor_row = row + 4

        Tooltip(
            rb_current, self.tooltips_text["maintain-current-allocation"],
            font=self._tooltip_font
        )

        # --- Custom portfolio entries ---
        self.custom_stock_var = tk.StringVar(
            value=self._format_sim_field("custom_stock", settings["custom_stock"])
        )
        self.custom_bonds_var = tk.StringVar(
            value=self._format_sim_field("custom_bonds", settings["custom_bonds"])
        )
        self.custom_cash_var = tk.StringVar(
            value=self._format_sim_field("custom_cash", settings["custom_cash"])
        )
        self._custom_total_check_id = None

        self.custom_stock_label = ttk.Label(
            self, text="Percent Stock:", font=self._body_font
        )

        vcmd = self.register(self._validate_sim_field), "%P", "custom_stock"
        self.custom_stock_entry = ttk.Entry(
            self, textvariable=self.custom_stock_var, width=14, font=self._body_font,
            validate="focusout", validatecommand=vcmd
        )

        self.custom_bonds_label = ttk.Label(
            self, text="Percent Bonds:", font=self._body_font
        )

        vcmd = self.register(self._validate_sim_field), "%P", "custom_bonds"
        self.custom_bonds_entry = ttk.Entry(
            self, textvariable=self.custom_bonds_var, width=14, font=self._body_font,
            validate="focusout", validatecommand=vcmd
        )

        self.custom_cash_label = ttk.Label(
            self, text="Percent Cash:", font=self._body_font
        )

        vcmd = self.register(self._validate_sim_field), "%P", "custom_cash"
        self.custom_cash_entry = ttk.Entry(
            self, textvariable=self.custom_cash_var, width=14, font=self._body_font,
            validate="focusout", validatecommand=vcmd
        )

        self._custom_tooltips_created = False

        self.initial_allocation_mode_var.trace_add(
            "write", lambda *args: self.toggle_custom_entries()
        )
        self.toggle_custom_entries()


    def _apply_scaled_styles(self):
        style = ttk.Style(self)
        style.configure("PortfolioSimulation.TCheckbutton", font=self._body_font)
        style.configure("PortfolioSimulation.TRadiobutton", font=self._body_font)


    # ------------------------
    # Helper methods
    # ------------------------
    def _toggle_fund_expense_entry(self):
        if self.use_fund_expenses_var.get():
            self.fund_expense_entry.config(state="normal")
        else:
            self.fund_expense_entry.config(state="disabled")


    def toggle_custom_entries(self):
        if self.initial_allocation_mode_var.get() == "custom":
            r = self.custom_anchor_row

            label_padx = (140, 5)
            entry_padx = (0, 0)

            self.custom_stock_label.grid(
                row=r, column=0, sticky="w", padx=label_padx, pady=0
            )
            self.custom_stock_entry.grid(
                row=r, column=1, sticky="w", padx=entry_padx, pady=0
            )

            self.custom_bonds_label.grid(
                row=r + 1, column=0, sticky="w", padx=label_padx, pady=0
            )
            self.custom_bonds_entry.grid(
                row=r + 1, column=1, sticky="w", padx=entry_padx, pady=0
            )

            self.custom_cash_label.grid(
                row=r + 2, column=0, sticky="w", padx=label_padx, pady=0
            )
            self.custom_cash_entry.grid(
                row=r + 2, column=1, sticky="w", padx=entry_padx, pady=0
            )

            if not self._custom_tooltips_created:
                Tooltip(
                    self.custom_stock_entry, self.tooltips_text["custom_stock_var"],
                    font=self._tooltip_font
                )
                Tooltip(
                    self.custom_bonds_entry, self.tooltips_text["custom_bonds_var"],
                    font=self._tooltip_font
                )
                Tooltip(
                    self.custom_cash_entry, self.tooltips_text["custom_cash_var"],
                    font=self._tooltip_font
                )
                self._custom_tooltips_created = True
        else:
            self.custom_stock_label.grid_forget()
            self.custom_stock_entry.grid_forget()
            self.custom_bonds_label.grid_forget()
            self.custom_bonds_entry.grid_forget()
            self.custom_cash_label.grid_forget()
            self.custom_cash_entry.grid_forget()


    def _parse_sim_field(self, field, value):
        if field in {"start_year", "years_to_simulate", "num_sims"}:
            return parse_integer(value, minimum=1)

        if field == "fund_expense":
            return parse_finite_float(value, minimum=0)

        if field in {"custom_stock", "custom_bonds", "custom_cash"}:
            return parse_finite_float(value, minimum=0, maximum=100)

        raise ValueError(f"Unknown field: {field}")


    def _sim_field_label(self, field):
        labels = {
            "start_year": "Start Year",
            "years_to_simulate": "Years to Simulate",
            "num_sims": "Number of Simulations",
            "fund_expense": "Fund Expense",
            "custom_stock": "Custom Stock Allocation",
            "custom_bonds": "Custom Bond Allocation",
            "custom_cash": "Custom Cash Allocation",
        }
        return labels.get(field, field)


    def _format_sim_field(self, field, value):
        if field in {"start_year", "years_to_simulate", "num_sims"}:
            return str(int(value))

        return f"{value:.2f}".rstrip("0").rstrip(".")


    def _schedule_custom_allocation_check(self):
        if self._custom_total_check_id is not None:
            self.after_cancel(self._custom_total_check_id)

        self._custom_total_check_id = self.after_idle(
            self._validate_custom_allocation_total
        )


    def _validate_custom_allocation_total(self):
        self._custom_total_check_id = None

        if self.initial_allocation_mode_var.get() != "custom":
            return

        focus_widget = self.focus_get()
        custom_entries = {
            self.custom_stock_entry,
            self.custom_bonds_entry,
            self.custom_cash_entry,
        }

        if focus_widget in custom_entries:
            return

        settings = self.sim_vars["_settings_dict"]
        total = settings["custom_stock"] + settings["custom_bonds"] + settings["custom_cash"]

        if abs(total - 100.0) <= 1.0e-9:
            return

        mark_validation_failed(self)
        messagebox.showerror(
            "Invalid Input",
            f"Simulation Settings / Custom Asset Allocation must total 100%. Current total is {total:g}%.",
            parent=self.winfo_toplevel(),
        )


    def _validate_sim_field(self, proposed_value, field):
        settings = self.sim_vars["_settings_dict"]

        if field == "num_sims":
            var_name = "sims_var"
        else:
            var_name = f"{field}_var"

        var = getattr(self, var_name)
        current_value = settings[field]

        try:
            parsed = self._parse_sim_field(field, proposed_value)
            settings[field] = parsed
            self.after_idle(lambda: var.set(self._format_sim_field(field, parsed)))

            if field in {"custom_stock", "custom_bonds", "custom_cash"}:
                self._schedule_custom_allocation_check()

            return True

        except ValueError as exc:
            self.after_idle(
                lambda: var.set(self._format_sim_field(field, current_value))
            )
            mark_validation_failed(self)
            messagebox.showerror(
                "Invalid Input",
                f"Simulation Settings / {self._sim_field_label(field)}: {exc}",
                parent=self.winfo_toplevel(),
            )
            return True


    def _bind_var(self, var, setter, cast=None):
        def callback(*_):
            try:
                value = var.get()

                if cast:
                    value = cast(value)

                setter(value)

            except (ValueError, TypeError):
                pass

        var.trace_add("write", callback)