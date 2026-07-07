# gui_retirement.py

import tkinter as tk
import copy
from tkinter import ttk

from src.utils.tooltip import Tooltip


class RetirementEditFrame(ttk.Frame):

    def __init__(self, parent, main_gui, control_vars, persons=None, portfolio=None, title="Retirement", **kwargs):
        super().__init__(parent, padding=10, **kwargs)

        self.controls = control_vars["_controls_dict"]
        self.main_gui = main_gui  # <-- store the main GUI reference
        self.control_vars = control_vars
        self.persons = persons
        self.portfolio = portfolio
        self.title = title

        ttk.Label(
            self,
            text="Defines how the simulation models retirement spending withdrawals, RMDs, and optional sequence-of-returns scenarios.",
            font=("Arial", 11),
            wraplength=900,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.left_frame = ttk.Frame(self)
        self.left_frame.grid(row=1, column=0, sticky="nw", padx=(0, 30))

        self.right_frame = ttk.Frame(self)
        self.right_frame.grid(row=1, column=1, sticky="ne")

        self._row = 0
        self._add_use_mode_checkboxes(parent=self.left_frame)
        self._add_withdrawal_controls(parent=self.left_frame)
        self._row += 1
        self._add_include_rmd(parent=self.left_frame)

        self._right_row = 0
        self._add_sequence_risk_controls(parent=self.right_frame)


    def _next_row(self, which="left"):
        if which == "right":
            r = self._right_row
            self._right_row += 1
            return r

        r = self._row
        self._row += 1
        return r


    # -----------------------------
    # Mode Selection Checkboxes
    # -----------------------------
    def _add_use_mode_checkboxes(self, parent):
        INTRO_TEXT = (
            "Choose how to calculate withdrawals:\n"
            "- Use manually entered expenses\n"
            "- Use automatic retirement withdrawal rules"
        )

        # Intro label, italicized and wrapped
        ttk.Label(
            parent,
            text=INTRO_TEXT,
            justify="left",
            wraplength=400,
            font=("Arial", 11, "italic")
        ).grid(row=self._next_row("left"), column=0, sticky="w", pady=(0, 8))

        # Initialize default
        if "use_mode" not in self.controls:
            self.controls["use_mode"] = "expenses"

        self.use_expenses_var = tk.BooleanVar(value=(self.controls["use_mode"] == "expenses"))
        self.use_retirement_var = tk.BooleanVar(value=(self.controls["use_mode"] == "retirement"))

        def on_use_expenses_changed():
            if self.use_expenses_var.get():
                self.use_retirement_var.set(False)
                self.controls["use_mode"] = "expenses"
                self.controls["always_use_expense_mode"] = True
            else:
                if not self.use_retirement_var.get():
                    self.use_expenses_var.set(True)
            self._update_withdrawal_visibility()

        def on_use_retirement_changed():
            if self.use_retirement_var.get():
                self.use_expenses_var.set(False)
                self.controls["use_mode"] = "retirement"
                self.controls["always_use_expense_mode"] = False
            else:
                if not self.use_expenses_var.get():
                    self.use_retirement_var.set(True)
            self._update_withdrawal_visibility()

        # Checkbuttons
        # Use Manually Entered Expenses checkbox
        self.use_expenses_cb = ttk.Checkbutton(
            parent, text="Use Manually Entered Expenses", variable=self.use_expenses_var,
            command=on_use_expenses_changed
        )
        self.use_expenses_cb.grid(row=self._next_row("left"), column=0, sticky="w", pady=2)

        Tooltip(
            self.use_expenses_cb,
            "If selected, withdrawals are taken from the amounts you manually enterd in the Expenses tab.\n"
            "  This mode uses income and expenses for the simulationn.",
            font=("Arial", 11)
        )

        # Use Automatically Calculated Withdrawals checkbox
        self.use_retirement_cb = ttk.Checkbutton(
            parent, text="Use Automatically Calculated Withdrawals", variable=self.use_retirement_var,
            command=on_use_retirement_changed
        )
        self.use_retirement_cb.grid(row=self._next_row("left"), column=0, sticky="w", pady=2)

        Tooltip(
            self.use_retirement_cb,
            "If selected, this mode withdrawals money from your portfolio at some rate.  This money is then spent.\n"
            "  This simulates different witdrawl rates from a portfolio.",
            font=("Arial", 11)
        )

    # -----------------------------
    # Withdrawal Controls
    # -----------------------------
    def _add_withdrawal_controls(self, parent):
        # Initialize default mode
        if "retirement_withdraw_mode" not in self.controls:
            self.controls["retirement_withdraw_mode"] = "Percentage + Inflation"

        self.ret_mode_var = tk.StringVar(value=self.controls["retirement_withdraw_mode"])
        mode_options = [
            "Off",
            "Percentage",
            "Percentage + Inflation",
            "Fixed Dollar Amount",
            "Fixed Dollar Amount + Inflation"
        ]

        # Retirement Mode Frame
        self.ret_mode_frame = ttk.Frame(parent)
        self.ret_mode_frame.grid(row=self._next_row("left"), column=0, columnspan=2, sticky="w", pady=5)
        ttk.Label(self.ret_mode_frame, text="Retirement Withdrawals Mode:").pack(side="left")
        self.ret_mode_menu = ttk.OptionMenu(
            self.ret_mode_frame, self.ret_mode_var, self.ret_mode_var.get(), *mode_options
        )
        self.ret_mode_menu.pack(side="left", padx=5)

        # Tooltip for the option menu
        Tooltip(
            self.ret_mode_menu,
            "Percentage: withdraw a fixed % of portfolio per year\n"
            "Fixed Amount: withdraw a fixed dollar amount per year\n"
            "+ Inflation: adjusts the withdrawal for inflation\n"
            "Includes RMDs if enabled; uses after-tax funds if possible.",
            font=("Arial", 11)
        )

        # Track mode changes
        def on_mode_change(*args):
            self.controls["retirement_withdraw_mode"] = self.ret_mode_var.get()
            state = "normal" if self.ret_mode_var.get() != "Off" else "disabled"
            self.pct_entry.config(state=state)
            self.dollars_entry.config(state=state)

        self.ret_mode_var.trace_add("write", on_mode_change)

        # Percentage entry
        if "retirement_withdraw_pct" not in self.controls:
            self.controls["retirement_withdraw_pct"] = 4.0
        self.pct_var = tk.StringVar(value=self._format_retirement_field(self.controls["retirement_withdraw_pct"]))
        self.pct_frame = ttk.Frame(parent)
        self.pct_frame.grid(row=self._next_row("left"), column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(self.pct_frame, text="Total Annual Withdrawal %:").pack(side="left")

        vcmd = (self.register(self._validate_retirement_field), "%P", "retirement_withdraw_pct")

        self.pct_entry = ttk.Entry(
            self.pct_frame,
            textvariable=self.pct_var,
            width=6,
            validate="focusout",
            validatecommand=vcmd
        )

        self.pct_entry.pack(side="left", padx=5)
        # Add tooltip for Percentage entry
        Tooltip(
            self.pct_entry,
            "Enter the total annual withdrawal as a percentage of your portfolio.\n"
            "Used only if 'Use Manually Entered Expenses' is selected.",
            font=("Arial", 11)
        )



        # Dollar entry
        if "retirement_withdraw_dollars" not in self.controls:
            self.controls["retirement_withdraw_dollars"] = 0.0

        self.dollars_var = tk.StringVar(value=self._format_retirement_field(self.controls["retirement_withdraw_dollars"]))
        self.dollars_frame = ttk.Frame(parent)
        self.dollars_frame.grid(row=self._next_row("left"), column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(self.dollars_frame, text="Total Annual Withdrawal $:").pack(side="left")

        vcmd = (self.register(self._validate_retirement_field), "%P", "retirement_withdraw_dollars")

        self.dollars_entry = ttk.Entry(
            self.dollars_frame,
            textvariable=self.dollars_var,
            width=10,
            validate="focusout",
            validatecommand=vcmd
        )

        self.dollars_entry.pack(side="left", padx=5)
        # Add tooltip for Dollar entry
        Tooltip(
            self.dollars_entry,
            "Enter the total annual withdrawal as a fixed dollar amount.\n"
            "Used only if 'Use Manually Entered Expenses' is selected.",
            font=("Arial", 11)
        )

        # Initialize visibility depending on mode
        self._update_withdrawal_visibility()

    # -----------------------------
    # Show/hide controls without moving RMD
    # -----------------------------
    def _update_withdrawal_visibility(self):
        use_retirement = self.controls.get("use_mode", "expenses") == "retirement"

        state = "normal" if use_retirement else "disabled"

        for w in self.ret_mode_frame.winfo_children():
            w.configure(state=state)

        for w in self.pct_frame.winfo_children():
            w.configure(state=state)

        for w in self.dollars_frame.winfo_children():
            w.configure(state=state)


    def _parse_retirement_field(self, field, value):

        text = value.strip()

        if text == "":
            raise ValueError("Blank")

        if text in {"-", "+", ".", "-.", "+."}:
            raise ValueError("Invalid")

        v = float(text)

        if field == "retirement_withdraw_pct" and v < 0:
            raise ValueError("Invalid")

        if field == "retirement_withdraw_dollars" and v < 0:
            raise ValueError("Invalid")

        return v


    def _format_retirement_field(self, value):
        return f"{value:.2f}".rstrip("0").rstrip(".")


    def _validate_retirement_field(self, proposed_value, field):

        var = self.pct_var if field == "retirement_withdraw_pct" else self.dollars_var
        current_value = self.controls[field]

        try:
            parsed = self._parse_retirement_field(field, proposed_value)
            self.controls[field] = parsed
            self.after_idle(lambda: var.set(self._format_retirement_field(parsed)))
            return True

        except ValueError:
            self.after_idle(lambda: var.set(self._format_retirement_field(current_value)))
            self.bell()
            return True


    def _parse_sequence_start_year_offset(self, value):
        text = value.strip()

        if text == "":
            raise ValueError("Blank")

        if text in {"-", "+"}:
            raise ValueError("Invalid")

        v = int(text)

        if v < 0:
            raise ValueError("Invalid")

        return v


    def _validate_sequence_start_year_offset(self, proposed_value):
        current_value = self.controls.get("sequence_risk_start_year_offset", 0)

        try:
            parsed = self._parse_sequence_start_year_offset(proposed_value)
            self.controls["sequence_risk_start_year_offset"] = parsed
            self.after_idle(lambda: self.sequence_risk_start_year_offset_var.set(str(parsed)))
            return True

        except ValueError:
            self.after_idle(
                lambda: self.sequence_risk_start_year_offset_var.set(str(current_value))
            )
            self.bell()
            return True


    # -----------------------------
    # RMD Checkbox
    # -----------------------------
    def _add_include_rmd(self, parent):
        ttk.Label(parent, text="").grid(row=self._next_row("left"), column=0)

        # Create a frame for the RMD checkbox to fix row shifting
        self.rmd_frame = ttk.Frame(parent)
        self.rmd_frame.grid(row=self._next_row(), column=0, sticky="w", pady=5)

        if "include_rmd" not in self.controls:
            self.controls["include_rmd"] = True

        var = tk.BooleanVar(value=self.controls["include_rmd"])
        var.trace_add(
            "write",
            lambda *args: self.controls.__setitem__("include_rmd", var.get())
        )

        # Create the RMD checkbox
        self.rmd_cb = ttk.Checkbutton(
            self.rmd_frame,
            text="Include RMDs",
            variable=var
        )
        self.rmd_cb.pack(side="left")

        # Add tooltip
        Tooltip(
            self.rmd_cb,
            "If selected, Required Minimum Distributions (RMDs) are included in the simulation.\n"
            "RMDs are withdrawals that must be taken annually from certain retirement accounts starting at about age 73.",
            font=("Arial", 11)
        )


    def _add_sequence_risk_controls(self, parent):
        ttk.Label(
            parent,
            text="Sequence-of-Returns Scenarios (Optional)",
            font=("Arial", 11, "bold")
        ).grid(row=self._next_row("right"), column=0, columnspan=2, sticky="w", pady=(0, 6))

        ttk.Label(
            parent,
            text=(
                "Use these controls to explore how a downturn at different points in retirement "
                "might affect withdrawal outcomes. These settings are educational scenario inputs only."
            ),
            justify="left",
            wraplength=360,
            font=("Arial", 10, "italic")
        ).grid(row=self._next_row("right"), column=0, columnspan=2, sticky="w", pady=(0, 10))

        if "sequence_risk_enabled" not in self.controls:
            self.controls["sequence_risk_enabled"] = False
        if "sequence_risk_timing" not in self.controls:
            self.controls["sequence_risk_timing"] = "Early downturn"
        if "sequence_risk_start_year_offset" not in self.controls:
            self.controls["sequence_risk_start_year_offset"] = 0
        if "sequence_risk_length" not in self.controls:
            self.controls["sequence_risk_length"] = "Medium"
        if "sequence_risk_depth" not in self.controls:
            self.controls["sequence_risk_depth"] = "Moderate"

        self.sequence_risk_enabled_var = tk.BooleanVar(
            value=self.controls["sequence_risk_enabled"]
        )
        self.sequence_risk_timing_var = tk.StringVar(
            value=self.controls["sequence_risk_timing"]
        )
        self.sequence_risk_start_year_offset_var = tk.StringVar(
            value=str(self.controls["sequence_risk_start_year_offset"])
        )
        self.sequence_risk_length_var = tk.StringVar(
            value=self.controls["sequence_risk_length"]
        )
        self.sequence_risk_depth_var = tk.StringVar(
            value=self.controls["sequence_risk_depth"]
        )

        self.sequence_risk_enabled_var.trace_add(
            "write",
            lambda *args: self.controls.__setitem__(
                "sequence_risk_enabled",
                self.sequence_risk_enabled_var.get()
            )
        )

        def on_sequence_timing_changed(*args):
            self.controls["sequence_risk_timing"] = self.sequence_risk_timing_var.get()
            if hasattr(self, "sequence_start_year_frame"):
                self._update_sequence_risk_visibility()

        self.sequence_risk_timing_var.trace_add("write", on_sequence_timing_changed)

        self.sequence_risk_length_var.trace_add(
            "write",
            lambda *args: self.controls.__setitem__(
                "sequence_risk_length",
                self.sequence_risk_length_var.get()
            )
        )

        self.sequence_risk_depth_var.trace_add(
            "write",
            lambda *args: self.controls.__setitem__(
                "sequence_risk_depth",
                self.sequence_risk_depth_var.get()
            )
        )

        self.sequence_enabled_cb = ttk.Checkbutton(
            parent,
            text="Include Sequence-of-Returns Scenarios",
            variable=self.sequence_risk_enabled_var,
            command=self._update_sequence_risk_visibility
        )
        self.sequence_enabled_cb.grid(
            row=self._next_row("right"),
            column=0,
            columnspan=2,
            sticky="w",
            pady=2
        )

        Tooltip(
            self.sequence_enabled_cb,
            "Turns on optional sequence-of-returns scenario inputs for retirement modeling.",
            font=("Arial", 11)
        )

        self.sequence_timing_frame = ttk.Frame(parent)
        self.sequence_timing_frame.grid(
            row=self._next_row("right"),
            column=0,
            columnspan=2,
            sticky="w",
            pady=4
        )

        ttk.Label(self.sequence_timing_frame, text="Scenario Timing:").pack(side="left")
        self.sequence_timing_menu = ttk.OptionMenu(
            self.sequence_timing_frame,
            self.sequence_risk_timing_var,
            self.sequence_risk_timing_var.get(),
            "Early downturn",
            "Mid-retirement downturn",
            "Late downturn",
            "Custom"
        )
        self.sequence_timing_menu.pack(side="left", padx=5)

        Tooltip(
            self.sequence_timing_menu,
            "Choose when the downturn occurs. Select Custom to enter a year offset from simulation start.",
            font=("Arial", 11)
        )

        self.sequence_start_year_frame = ttk.Frame(parent)
        self.sequence_start_year_frame.grid(
            row=self._next_row("right"),
            column=0,
            columnspan=2,
            sticky="w",
            pady=4
        )

        ttk.Label(self.sequence_start_year_frame, text="Years From Simulation Start:").pack(side="left")

        vcmd = (
            self.register(self._validate_sequence_start_year_offset),
            "%P"
        )

        self.sequence_start_year_entry = ttk.Entry(
            self.sequence_start_year_frame,
            textvariable=self.sequence_risk_start_year_offset_var,
            width=6,
            validate="focusout",
            validatecommand=vcmd
        )
        self.sequence_start_year_entry.pack(side="left", padx=5)

        Tooltip(
            self.sequence_start_year_entry,
            "Used only when Scenario Timing is Custom.\n"
            "Enter the number of years after simulation start when the downturn begins.\n"
            "Example: 5 means the downturn begins 5 years into the simulation.",
            font=("Arial", 11)
        )

        self.sequence_length_frame = ttk.Frame(parent)
        self.sequence_length_frame.grid(
            row=self._next_row("right"),
            column=0,
            columnspan=2,
            sticky="w",
            pady=4
        )

        ttk.Label(self.sequence_length_frame, text="Scenario Length:").pack(side="left")
        self.sequence_length_menu = ttk.OptionMenu(
            self.sequence_length_frame,
            self.sequence_risk_length_var,
            self.sequence_risk_length_var.get(),
            "Short",
            "Medium",
            "Long"
        )
        self.sequence_length_menu.pack(side="left", padx=5)

        Tooltip(
            self.sequence_length_menu,
            "Controls the duration category of the downturn scenario.",
            font=("Arial", 11)
        )

        self.sequence_depth_frame = ttk.Frame(parent)
        self.sequence_depth_frame.grid(
            row=self._next_row("right"),
            column=0,
            columnspan=2,
            sticky="w",
            pady=4
        )

        ttk.Label(self.sequence_depth_frame, text="Scenario Depth:").pack(side="left")
        self.sequence_depth_menu = ttk.OptionMenu(
            self.sequence_depth_frame,
            self.sequence_risk_depth_var,
            self.sequence_risk_depth_var.get(),
            "Mild",
            "Moderate",
            "Severe"
        )
        self.sequence_depth_menu.pack(side="left", padx=5)

        Tooltip(
            self.sequence_depth_menu,
            "Controls the severity category of the downturn scenario.",
            font=("Arial", 11)
        )

        self._update_sequence_risk_visibility()


    def _update_sequence_risk_visibility(self):
        required_attrs = (
            "sequence_timing_frame",
            "sequence_start_year_frame",
            "sequence_length_frame",
            "sequence_depth_frame",
            "sequence_risk_enabled_var",
            "sequence_risk_timing_var",
        )

        if not all(hasattr(self, attr) for attr in required_attrs):
            return

        enabled = self.sequence_risk_enabled_var.get()
        base_state = "normal" if enabled else "disabled"

        for frame in (
            self.sequence_timing_frame,
            self.sequence_length_frame,
            self.sequence_depth_frame,
        ):
            for widget in frame.winfo_children():
                try:
                    widget.configure(state=base_state)
                except tk.TclError:
                    pass

        custom_state = (
            "normal"
            if enabled and self.sequence_risk_timing_var.get() == "Custom"
            else "disabled"
        )

        for widget in self.sequence_start_year_frame.winfo_children():
            try:
                widget.configure(state=custom_state)
            except tk.TclError:
                pass