# gui_scenarioSliders.py

import tkinter as tk
from tkinter import ttk

from src.utils.tooltip import *

class ScenarioSlidersFrame(ttk.LabelFrame):
    def __init__(
        self,
        parent,
        main_gui=None,
        persons=None,
        portfolio=None,
        retirement_snapshots=None,
        *,
        show_enable_overrides_checkbox=True,
        allow_main_gui_override_flag=True,
        show_wife=True,
        baseline_persons=None,
    ):
        super().__init__(
            parent,
            text="Scenario assumptions for educational exploration only.\nThese settings do not change saved data",
            padding=10
        )

        self.main_gui = main_gui

        self.husband = persons["husband"]

        # Wife may be omitted when enable_second_person is False
        self.wife = persons.get("wife") if persons else None
        if not show_wife:
            self.wife = None

        # Baselines used for SS adjustment logic (do not mutate baselines)
        self.baseline_persons = baseline_persons if baseline_persons is not None else {}

        self.portfolio = portfolio
        self.retirement_snapshots = retirement_snapshots

        self.inflation = retirement_snapshots.inflation
        self.fund_expense = retirement_snapshots.fund_expense
        self.historical_data_multiplier = retirement_snapshots.historical_data_multiplier


        # --------------------
        # Enable Temporary Portfolio Overrides checkbox (optional)
        # --------------------
        self.enable_overrides = tk.BooleanVar(value=True if not show_enable_overrides_checkbox else False)

        if show_enable_overrides_checkbox:
            self.enable_overrides_cb = ttk.Checkbutton(
                self,
                text="Enable Temporary Portfolio Overrides",
                variable=self.enable_overrides,
                command=self._update_slider_state
            )
            self.enable_overrides_cb.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

            Tooltip(
                self.enable_overrides_cb,
                "When selected, allows you to temporarily adjust simulation inputs.\n"
                "These changes do not modify saved portfolio data.",
                font=("Arial", 11)
            )
        else:
            self.enable_overrides_cb = None

        # Annotate Plots variable (widget is placed in ScenarioController bottom row)
        self.enable_annotations = tk.BooleanVar(value=True)  # ON by default

        # New: whether to apply inflation delta to return assumptions
        self.adjust_hist_for_infl_delta = tk.BooleanVar(value=True)

        # --------------------
        # Sliders container
        # --------------------
        self.sliders_container = ttk.Frame(self)
        self.sliders_container.grid(row=1, column=0, columnspan=2, sticky="nsew")

        # 3 columns x 3 rows
        for c in range(3):
            self.sliders_container.columnconfigure(c, weight=1, uniform="slidercols")
        for r in range(3):
            self.sliders_container.rowconfigure(r, weight=1)

        # --------------------
        # 3x3 cell frames (each cell holds label + slider)
        # --------------------
        def _make_cell(row, col, padx):
            cell = ttk.Frame(self.sliders_container)
            cell.grid(row=row, column=col, sticky="nsew", padx=padx, pady=(0, 8))
            cell.columnconfigure(0, weight=1)
            return cell

        PAD = 6
        cell00 = _make_cell(0, 0, padx=(PAD, PAD))
        cell10 = _make_cell(1, 0, padx=(PAD, PAD))
        cell20 = _make_cell(2, 0, padx=(PAD, PAD))

        cell01 = _make_cell(0, 1, padx=(PAD, PAD))
        cell11 = _make_cell(1, 1, padx=(PAD, PAD))

        #cell21 = _make_cell(2, 1, padx=(PAD, PAD))
        # Dynamic Withdrawal / Expense Slider (2,1)
        self.dynamic_value = tk.DoubleVar()

        self.dynamic_label_var = tk.StringVar()
        self.dynamic_label = ttk.Label(cell21 := _make_cell(2, 1, padx=(PAD, PAD)), textvariable=self.dynamic_label_var)
        self.dynamic_label.grid(row=0, column=0, sticky="w", pady=(0, 2))

        self.dynamic_slider = ttk.Scale(
            cell21,
            orient="horizontal",
            variable=self.dynamic_value,
            command=self._update_dynamic_slider_label
        )
        self.dynamic_slider.grid(row=1, column=0, sticky="ew")

        Tooltip(
            self.dynamic_slider,
            "Adjusts either withdrawal percentage or expense multiplier depending on Retirement mode.",
            font=("Arial", 11)
        )

        cell02 = _make_cell(0, 2, padx=(PAD, PAD))
        cell12 = _make_cell(1, 2, padx=(PAD, PAD))
        cell22 = _make_cell(2, 2, padx=(PAD, PAD))

        # --------------------
        # Column 1: Husband, Wife, Inflation
        # --------------------
        # Husband Retirement Age (0,0)
        self.tmp_ret_age_h = tk.IntVar(value=self.husband.retire_age)
        self.tmp_ret_age_h.trace_add("write", self._update_husband_label)
        self.husband_label_var = tk.StringVar(value=f"Husband Retirement Age: {self.tmp_ret_age_h.get()}")
        self.husband_label = ttk.Label(cell00, textvariable=self.husband_label_var)
        self.husband_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.husband_slider = ttk.Scale(
            cell00, from_=55, to=75, orient="horizontal",
            variable=self.tmp_ret_age_h
        )
        self.husband_slider.grid(row=1, column=0, sticky="ew")
        Tooltip(
            self.husband_slider,
            "Adjust the husband's retirement age for the simulation. This affects retirement date and scales Social Security appropriately. Pensions/annuity amounts are not changed.",
            font=("Arial", 11)
        )

        # Wife Retirement Age (1,0) optional
        if self.wife is not None:
            self.tmp_ret_age_w = tk.IntVar(value=self.wife.retire_age)
            self.tmp_ret_age_w.trace_add("write", self._update_wife_label)
            self.wife_label_var = tk.StringVar(value=f"Wife Retirement Age: {self.tmp_ret_age_w.get()}")
            self.wife_label = ttk.Label(cell10, textvariable=self.wife_label_var)
            self.wife_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
            self.wife_slider = ttk.Scale(
                cell10, from_=55, to=75, orient="horizontal",
                variable=self.tmp_ret_age_w
            )
            self.wife_slider.grid(row=1, column=0, sticky="ew")
            Tooltip(
                self.wife_slider,
                "Adjust the wife's retirement age for the simulation. This affects retirement date and scales Social Security appropriately. Pensions/annuity amounts are not changed.",
                font=("Arial", 11)
            )
        else:
            self.tmp_ret_age_w = None
            self.wife_label_var = None
            self.wife_label = None
            self.wife_slider = None

        # Inflation (2,0)
        self.inflation_value = tk.DoubleVar(value=self.inflation)
        self.inflation_label_var = tk.StringVar(value=f"Inflation Rate (%): {self.inflation_value.get():.1f}")
        self.inflation_label = ttk.Label(cell20, textvariable=self.inflation_label_var)
        self.inflation_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.inflation_slider = ttk.Scale(
            cell20, from_=0, to=10, orient="horizontal",
            variable=self.inflation_value,
            command=self._update_inflation_label
        )
        self.inflation_slider.grid(row=1, column=0, sticky="ew")
        Tooltip(
            self.inflation_slider,
            "Set a hypothetical annual inflation rate (%) for the simulation.",
            font=("Arial", 11)
        )

        # --------------------
        # Column 2: Fund Expenses, Market Adjustment, (empty)
        # --------------------
        # Fund Expenses (0,1)
        self.fund_expense_value = tk.DoubleVar(value=self.fund_expense)
        self.fund_expense_label_var = tk.StringVar(value=f"Fund Expenses (%): {self.fund_expense_value.get():.2f}")
        self.fund_expense_label = ttk.Label(cell01, textvariable=self.fund_expense_label_var)
        self.fund_expense_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.fund_expense_slider = ttk.Scale(
            cell01, from_=0, to=5, orient="horizontal",
            variable=self.fund_expense_value,
            command=self._update_fund_expenses_label
        )
        self.fund_expense_slider.grid(row=1, column=0, sticky="ew")
        Tooltip(
            self.fund_expense_slider,
            "Set the annual fund expense ratio (%) applied to investments in the simulation.",
            font=("Arial", 11)
        )

        # Hypothetical Market Adjustment (1,1)
        self.market_adjustment_percent = tk.DoubleVar(value=self.historical_data_multiplier)
        self.market_adjustment_label_var = tk.StringVar(
            value=f"Hypothetical Market Adjustment: {int(self.market_adjustment_percent.get()):>3}%"
        )
        self.market_adjustment_label = ttk.Label(cell11, textvariable=self.market_adjustment_label_var, anchor="w")
        self.market_adjustment_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.market_adjustment_slider = ttk.Scale(
            cell11, from_=50, to=200, orient="horizontal",
            variable=self.market_adjustment_percent,
            command=self._update_market_adjustment_label
        )
        self.market_adjustment_slider.grid(row=1, column=0, sticky="ew")
        Tooltip(
            self.market_adjustment_slider,
            "Scale historical return assumptions to explore better/worse periods.",
            font=("Arial", 11)
        )

        self._configure_dynamic_slider()

        # --------------------
        # Column 3: Stocks, Bonds, Cash
        # --------------------
        stocks_pct, bonds_pct, cash_pct = self._compute_initial_portfolio_percents()

        # Stocks (0,2)
        self.stocks_percent = tk.DoubleVar(value=stocks_pct)
        self.stocks_label_var = tk.StringVar(value=f"Percent Stock: {self.stocks_percent.get()}%")
        self.stocks_label = ttk.Label(cell02, textvariable=self.stocks_label_var)
        self.stocks_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.stocks_slider = ttk.Scale(
            cell02, from_=0, to=100, orient="horizontal",
            variable=self.stocks_percent, command=lambda e=None: self._update_stocks_label()
        )
        self.stocks_slider.grid(row=1, column=0, sticky="ew")
        Tooltip(
            self.stocks_slider,
            "Adjust stock percentage in the combined portfolio.",
            font=("Arial", 11)
        )

        # Bonds (1,2)
        self.bonds_percent = tk.DoubleVar(value=bonds_pct)
        self.bonds_label_var = tk.StringVar(value=f"Percent Bonds: {self.bonds_percent.get()}%")
        self.bonds_label = ttk.Label(cell12, textvariable=self.bonds_label_var)
        self.bonds_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.bonds_slider = ttk.Scale(
            cell12, from_=0, to=100, orient="horizontal",
            variable=self.bonds_percent, command=lambda e=None: self._update_bonds_label()
        )
        self.bonds_slider.grid(row=1, column=0, sticky="ew")
        Tooltip(
            self.bonds_slider,
            "Adjust bond percentage in the combined portfolio.",
            font=("Arial", 11)
        )

        # Cash (2,2) calculated
        self.cash_percent = tk.DoubleVar(value=cash_pct)
        self.cash_label_var = tk.StringVar(value=f"Percent Cash (calculated): {self.cash_percent.get()}%")
        self.cash_label = ttk.Label(cell22, textvariable=self.cash_label_var)
        self.cash_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.cash_dummy_slider = ttk.Scale(
            cell22, from_=0, to=100, orient="horizontal", state="disabled",
            variable=self.cash_percent
        )
        self.cash_dummy_slider.grid(row=1, column=0, sticky="ew")
        Tooltip(
            self.cash_dummy_slider,
            "Cash = 100% - (Stock % + Bonds %).",
            font=("Arial", 11)
        )

        # Force update labels and cash
        self._update_stocks_label()
        self._update_bonds_label()


        # Force update labels and cash
        self._update_stocks_label()
        self._update_bonds_label()

        # --------------------
        # Initialize slider states
        # --------------------

        # store flags for _update_slider_state
        self.allow_main_gui_override_flag = allow_main_gui_override_flag

        if show_enable_overrides_checkbox:
            self.enable_overrides.set(False)
            self._update_slider_state()
            self.enable_overrides.trace_add("write", self._update_slider_state)
        else:
            # Scenario: overrides are always active; do not gray out anything
            self.enable_overrides.set(True)
            self._update_slider_state()


    # --------------------
    # Slider update callbacks
    # --------------------
    def _update_husband_label(self, *args):
        self.husband.retire_age = self.tmp_ret_age_h.get()
        self.husband_label_var.set(f"Husband Retirement Age: {self.husband.retire_age}")

    def _update_wife_label(self, *args):
        self.wife.retire_age = self.tmp_ret_age_w.get()
        self.wife_label_var.set(f"Wife Retirement Age: {self.wife.retire_age}")

    def _update_inflation_label(self, val):
        self.inflation_label_var.set(f"Inflation Rate (%): {float(val):.1f}")

    def _update_fund_expenses_label(self, val):
        self.fund_expense_label_var.set(f"Fund Expenses (%): {float(val):.2f}")

    def _update_stocks_label(self):
        new_stocks = self.stocks_percent.get()
        bonds = self.bonds_percent.get()
        cash = 100 - (new_stocks + bonds)
        if cash < 0:
            # Reduce Bonds first
            bonds += cash  # cash is negative
            self.bonds_percent.set(bonds)
            cash = 0
        self.stocks_label_var.set(f"Percent Stock: {round(new_stocks)}%")
        self.bonds_label_var.set(f"Percent Bonds: {round(bonds)}%")
        self.cash_label_var.set(f"Percent Cash (calculated): {round(cash)}%")
        self.cash_percent.set(round(cash))

    def _update_bonds_label(self):
        new_bonds = self.bonds_percent.get()
        stocks = self.stocks_percent.get()
        cash = 100 - (stocks + new_bonds)
        if cash < 0:
            stocks += cash  # cash negative
            self.stocks_percent.set(stocks)
            cash = 0
        self.stocks_label_var.set(f"Percent Stock: {round(stocks)}%")
        self.bonds_label_var.set(f"Percent Bonds: {round(new_bonds)}%")
        self.cash_label_var.set(f"Percent Cash (calculated): {round(cash)}%")
        self.cash_percent.set(round(cash))

    def _update_market_adjustment_label(self, val):
        val_int = int(float(val))
        self.market_adjustment_label_var.set(
            f"Hypothetical Market Adjustment: {val_int:>3}%"
        )
        self.retirement_snapshots.historical_data_multiplier = float(val)


    # --------------------
    # Portfolio snapshot updates
    # --------------------
    def _compute_initial_portfolio_percents(self):
        h_port = self.portfolio["husband"]
        w_port = self.portfolio.get("wife") if self.portfolio else None

        w_eq_pre  = w_port.equity_pre if w_port else 0
        w_eq_post = w_port.equity_post if w_port else 0
        w_bd_pre  = w_port.bond_pre if w_port else 0
        w_bd_post = w_port.bond_post if w_port else 0
        w_cs_pre  = w_port.cash_pre if w_port else 0
        w_cs_post = w_port.cash_post if w_port else 0

        total_equity = h_port.equity_pre + h_port.equity_post + w_eq_pre + w_eq_post
        total_bonds  = h_port.bond_pre   + h_port.bond_post   + w_bd_pre + w_bd_post
        total_cash   = h_port.cash_pre   + h_port.cash_post   + w_cs_pre + w_cs_post

        total_portfolio = total_equity + total_bonds + total_cash

        if total_portfolio > 0:
            stocks_pct = (total_equity / total_portfolio) * 100
            bonds_pct  = (total_bonds / total_portfolio) * 100
            cash_pct   = 100 - stocks_pct - bonds_pct
        else:
            stocks_pct, bonds_pct, cash_pct = 0, 0, 100

        #print("stocks: "+str(stocks_pct)+" bonds: "+str(bonds_pct)+" cash:"+str(cash_pct))
        return round(stocks_pct), round(bonds_pct), round(cash_pct)



    # --------------------
    # Enable/disable sliders
    # --------------------
    def _update_slider_state(self, *args):
        enabled = bool(self.enable_overrides.get())
        state = "normal" if enabled else "disabled"
        fg = "black" if enabled else "gray"

        # Sliders/labels that always exist
        slider_label_pairs = [
            (self.husband_slider, self.husband_label),
            (self.inflation_slider, self.inflation_label),
            (self.fund_expense_slider, self.fund_expense_label),
            (self.market_adjustment_slider, self.market_adjustment_label),
            (self.stocks_slider, self.stocks_label),
            (self.bonds_slider, self.bonds_label),
        ]

        # Wife controls are optional
        if self.wife_slider is not None and self.wife_label is not None:
            slider_label_pairs.insert(1, (self.wife_slider, self.wife_label))

        for slider, label in slider_label_pairs:
            slider.configure(state=state)
            label.configure(foreground=fg)

        self.cash_label.configure(foreground=fg)

        # Adjust SS benefits based on baseline persons if provided
        baseline_h = self.baseline_persons.get("husband", self.main_gui.husband if self.main_gui else None)
        if baseline_h is not None:
            self.adjust_retirement_benefits_year_by_year(self.husband, baseline_h)

        if self.wife is not None:
            baseline_w = self.baseline_persons.get("wife", self.main_gui.wife if self.main_gui else None)
            if baseline_w is not None:
                self.adjust_retirement_benefits_year_by_year(self.wife, baseline_w)


    # --------------------
    # Adjust retirement benefits
    # --------------------
    def adjust_retirement_benefits_year_by_year(self, snapshot, baseline):
        ss_factors = {62:0.70, 63:0.75, 64:0.80, 65:0.867, 66:0.933, 67:1.0, 68:1.08, 69:1.16, 70:1.24}
        baseline_age = min(max(baseline.retire_age, 62), 70)
        new_age = min(max(snapshot.retire_age, 62), 70)
        baseline_factor = ss_factors[baseline_age]
        new_factor = ss_factors[new_age]

        baseline_pia = baseline.ss / baseline_factor if baseline_factor > 0 else baseline.ss
        snapshot.ss = round(baseline_pia * new_factor, 2)
        snapshot.pension = baseline.pension
        snapshot.annuity = baseline.annuity
        snapshot.ss_age = snapshot.retire_age
        snapshot.pension_age = snapshot.retire_age
        snapshot.annuity_age = snapshot.retire_age

    def _configure_dynamic_slider(self):
        controls = self.main_gui.simulation_controls
        manual = controls.get("manual_expenses", True)

        if manual:
            # Expense Multiplier Mode
            self.dynamic_slider.configure(from_=50, to=150)

            if self.retirement_snapshots.scenario_expense_multiplier is None:
                self.dynamic_value.set(100)
            else:
                # snapshot stores multiplier (e.g., 1.0), slider displays percent (e.g., 100)
                self.dynamic_value.set(self.retirement_snapshots.scenario_expense_multiplier * 100.0)

            self.dynamic_label_var.set(f"Expense Multiplier: {self.dynamic_value.get():.0f}%")
        else:
            # Withdrawal Percent Mode
            self.dynamic_slider.configure(from_=0, to=10)
            if self.retirement_snapshots.scenario_withdraw_pct is None:
                self.dynamic_value.set(
                    self.main_gui.simulation_controls.get("retirement_withdraw_pct", 4.0)
                )
            else:
                self.dynamic_value.set(self.retirement_snapshots.scenario_withdraw_pct)

            self.dynamic_label_var.set(f"Withdrawal %: {self.dynamic_value.get():.2f}%")


    def _update_dynamic_slider_label(self, val):
        val = float(val)
        controls = self.main_gui.simulation_controls
        manual = controls.get("manual_expenses", True)

        if manual:
            self.dynamic_label_var.set(f"Expense Multiplier: {val:.0f}%")
            # store as multiplier (1.0 == 100%)
            self.retirement_snapshots.scenario_expense_multiplier = val / 100.0
        else:
            self.dynamic_label_var.set(f"Withdrawal %: {val:.2f}%")
            self.retirement_snapshots.scenario_withdraw_pct = val