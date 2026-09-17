# gui_scenarioSliders.py

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from src.warpsimlab.utils.tooltip import *
from dataclasses import dataclass
from src.warpsimlab.gui.scenario.gui_scenarioState import compute_portfolio_percentages

@dataclass
class ScenarioControlValues:
    husband_ret_age: int
    husband_ss_age: int
    wife_ret_age: int | None
    wife_ss_age: int | None
    inflation: float
    fund_expense: float
    stocks: float
    bonds: float
    cash: float
    dynamic_value: float
    calculate_real_dollars: bool
    enable_annotations: bool

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
        show_wife=True,
    ):
        super().__init__(
            parent,
            text="These settings do not change\nsaved data",
            padding=10
        )

        self.main_gui = main_gui
        self.normal_label_font = tkfont.nametofont("TkDefaultFont").copy()
        self.changed_label_font = self.normal_label_font.copy()
        self.changed_label_font.configure(weight="bold")
        self._highlight_controls = []

        self.husband = persons["husband"]

        # Wife may be omitted when second_person_enabled is False
        if persons:
            self.wife = persons.get("wife")
        else:
            self.wife = None

        if not show_wife:
            self.wife = None

        self.portfolio = portfolio
        self.retirement_snapshots = retirement_snapshots

        self.inflation = main_gui.inflation
        self.fund_expense = retirement_snapshots.fund_expense

        # --------------------
        # Enable Temporary Portfolio Overrides checkbox (optional)
        # --------------------
        self.enable_overrides = tk.BooleanVar(value=not show_enable_overrides_checkbox)

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
        self.calculate_real_dollars = tk.BooleanVar(value=True)

        # --------------------
        # Sliders container
        # --------------------
        self.sliders_container = ttk.Frame(self)
        self.sliders_container.grid(row=1, column=0, columnspan=2, sticky="nsew")

        self.sliders_container.columnconfigure(0, weight=1)

        timing_group = ttk.Frame(self.sliders_container)
        economic_group = ttk.Frame(self.sliders_container)
        portfolio_group = ttk.Frame(self.sliders_container)

        timing_group.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        economic_group.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        portfolio_group.grid(row=2, column=0, sticky="ew")

        timing_group.columnconfigure(0, weight=1)
        economic_group.columnconfigure(0, weight=1)
        portfolio_group.columnconfigure(0, weight=1)

        def _make_cell(parent, row):
            cell = ttk.Frame(parent)
            cell.grid(row=row, column=0, sticky="ew", pady=(0, 6))
            cell.columnconfigure(0, weight=1)
            return cell

        cell00 = _make_cell(timing_group, 0)
        cell10 = _make_cell(timing_group, 1)
        cell20 = _make_cell(timing_group, 2)
        cell30 = _make_cell(timing_group, 3)

        cell01 = _make_cell(economic_group, 0)
        cell11 = _make_cell(economic_group, 1)
        cell21 = _make_cell(economic_group, 2)

        cell02 = _make_cell(portfolio_group, 0)
        cell12 = _make_cell(portfolio_group, 1)
        cell22 = _make_cell(portfolio_group, 2)

        self.dynamic_value = tk.DoubleVar()
        self.dynamic_label_var = tk.StringVar()
        self.dynamic_label = ttk.Label(cell21, textvariable=self.dynamic_label_var)
        self.dynamic_label.grid(row=0, column=0, sticky="w", pady=(0, 2))

        self.dynamic_slider = ttk.Scale(
            cell21, orient="horizontal", variable=self.dynamic_value, command=self._update_dynamic_slider_label
        )
        self.dynamic_slider.grid(row=1, column=0, sticky="ew")

        Tooltip(
            self.dynamic_slider,
            "Adjusts either withdrawal percentage or expense multiplier depending on Retirement mode.",
            font=("Arial", 11)
        )

        # --------------------
        # Retirement and Social Security
        # --------------------

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

        # Husband Social Security Age (1,0)
        self.tmp_ss_age_h = tk.IntVar(value=self.husband.ss_age)
        self.tmp_ss_age_h.trace_add("write", self._update_husband_ss_label)
        self.husband_ss_label_var = tk.StringVar(value=f"Husband Social Security Age: {self.tmp_ss_age_h.get()}")
        self.husband_ss_label = ttk.Label(cell10, textvariable=self.husband_ss_label_var)
        self.husband_ss_label.grid(row=0, column=0, sticky="w", pady=(0, 2))

        self.husband_ss_slider = ttk.Scale(
            cell10, from_=62, to=70, orient="horizontal", variable=self.tmp_ss_age_h
        )
        self.husband_ss_slider.grid(row=1, column=0, sticky="ew")
        Tooltip(
            self.husband_ss_slider,
            "Adjust the husband's Social Security start age for the simulation.",
            font=("Arial", 11)
        )

        # Wife Retirement Age (2,0) optional
        if self.wife is not None:
            self.tmp_ret_age_w = tk.IntVar(value=self.wife.retire_age)
            self.tmp_ret_age_w.trace_add("write", self._update_wife_label)
            self.wife_label_var = tk.StringVar(value=f"Wife Retirement Age: {self.tmp_ret_age_w.get()}")
            self.wife_label = ttk.Label(cell20, textvariable=self.wife_label_var)
            self.wife_label.grid(row=0, column=0, sticky="w", pady=(0, 2))

            self.wife_slider = ttk.Scale(
                cell20, from_=55, to=75, orient="horizontal", variable=self.tmp_ret_age_w
            )
            self.wife_slider.grid(row=1, column=0, sticky="ew")
            Tooltip(
                self.wife_slider,
                "Adjust the wife's retirement age for the simulation.",
                font=("Arial", 11)
            )

            self.tmp_ss_age_w = tk.IntVar(value=self.wife.ss_age)
            self.tmp_ss_age_w.trace_add("write", self._update_wife_ss_label)
            self.wife_ss_label_var = tk.StringVar(value=f"Wife Social Security Age: {self.tmp_ss_age_w.get()}")
            self.wife_ss_label = ttk.Label(cell30, textvariable=self.wife_ss_label_var)
            self.wife_ss_label.grid(row=0, column=0, sticky="w", pady=(0, 2))

            self.wife_ss_slider = ttk.Scale(
                cell30, from_=62, to=70, orient="horizontal", variable=self.tmp_ss_age_w
            )
            self.wife_ss_slider.grid(row=1, column=0, sticky="ew")
            Tooltip(
                self.wife_ss_slider,
                "Adjust the wife's Social Security start age for the simulation.",
                font=("Arial", 11)
            )
        else:
            self.tmp_ret_age_w = None
            self.wife_label_var = None
            self.wife_label = None
            self.wife_slider = None
            self.tmp_ss_age_w = None
            self.wife_ss_label_var = None
            self.wife_ss_label = None
            self.wife_ss_slider = None

        # Inflation
        self.inflation_value = tk.DoubleVar(value=self.inflation)
        self.inflation_label_var = tk.StringVar(value=f"Inflation Rate (%): {self.inflation_value.get():.1f}")
        self.inflation_label = ttk.Label(cell01, textvariable=self.inflation_label_var)

        self.inflation_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.inflation_slider = ttk.Scale(
            cell01, from_=0, to=10, orient="horizontal",
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
        # Economic assumptions
        # --------------------
        # Fund Expenses
        self.fund_expense_value = tk.DoubleVar(value=self.fund_expense)
        self.fund_expense_label_var = tk.StringVar(value=f"Fund Expenses (%): {self.fund_expense_value.get():.2f}")
        self.fund_expense_label = ttk.Label(cell11, textvariable=self.fund_expense_label_var)
        self.fund_expense_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.fund_expense_slider = ttk.Scale(
            cell11, from_=0, to=2.5, orient="horizontal",
            variable=self.fund_expense_value,
            command=self._update_fund_expenses_label
        )
        self.fund_expense_slider.grid(row=1, column=0, sticky="ew")
        Tooltip(
            self.fund_expense_slider,
            "Set the annual fund expense ratio (%) applied to investments in the simulation.",
            font=("Arial", 11)
        )

        self._configure_dynamic_slider()

        # --------------------
        # Portfolio allocation
        # --------------------

        stocks_pct, bonds_pct, cash_pct = compute_portfolio_percentages(self.portfolio)

        # Stocks (0,2)
        self.stocks_percent = tk.DoubleVar(value=stocks_pct)
        self.stocks_label_var = tk.StringVar(value=f"Stock: {self.stocks_percent.get()}%")
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
        self.bonds_label_var = tk.StringVar(value=f"Bonds: {self.bonds_percent.get()}%")
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
        self.cash_label_var = tk.StringVar(value=f"Cash (calculated): {self.cash_percent.get()}%")
        self.cash_label = ttk.Label(cell22, textvariable=self.cash_label_var)

        Tooltip(
            self.cash_label,
            "Cash = 100% - (Stock % + Bonds %).",
            font=("Arial", 11)
        )

        # Force update labels and cash
        self._update_stocks_label()
        self._update_bonds_label()

        # --------------------
        # Initialize slider states
        # --------------------

        if show_enable_overrides_checkbox:
            self.enable_overrides.set(False)
            self._update_slider_state()
            self.enable_overrides.trace_add("write", self._update_slider_state)
        else:
            # Scenario: overrides are always active; do not gray out anything
            self.enable_overrides.set(True)
            self._update_slider_state()

        self._initialize_changed_highlighting()


    # --------------------
    # Changed-control highlighting
    # --------------------
    def _initialize_changed_highlighting(self):
        self._highlight_controls = [
            (self.tmp_ret_age_h, self.husband_label),
            (self.tmp_ss_age_h, self.husband_ss_label),
            (self.inflation_value, self.inflation_label),
            (self.fund_expense_value, self.fund_expense_label),
            (self.dynamic_value, self.dynamic_label),
            (self.stocks_percent, self.stocks_label),
            (self.bonds_percent, self.bonds_label),
            (self.cash_percent, self.cash_label),
        ]

        if self.tmp_ret_age_w is not None:
            self._highlight_controls.append((self.tmp_ret_age_w, self.wife_label))
        if self.tmp_ss_age_w is not None:
            self._highlight_controls.append((self.tmp_ss_age_w, self.wife_ss_label))

        self._highlight_controls = [
            (variable, label, self._numeric_value(variable.get())) for variable, label in self._highlight_controls
        ]

        for variable, _label, _baseline in self._highlight_controls:
            variable.trace_add("write", lambda *_args: self._refresh_changed_highlights())

        self._refresh_changed_highlights()


    def _numeric_value(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return value


    def _refresh_changed_highlights(self):
        for variable, label, baseline in self._highlight_controls:
            current = self._numeric_value(variable.get())

            if isinstance(current, float) and isinstance(baseline, float):
                changed = abs(current - baseline) > 1e-9
            else:
                changed = current != baseline

            if changed:
                label.configure(font=self.changed_label_font)
            else:
                label.configure(font=self.normal_label_font)

    # --------------------
    # Slider update callbacks
    # --------------------
    def _update_husband_label(self, *args):
        self.husband_label_var.set(f"Husband Retirement Age: {self.tmp_ret_age_h.get()}")


    def _update_husband_ss_label(self, *args):
        self.husband_ss_label_var.set(f"Husband Social Security Age: {self.tmp_ss_age_h.get()}")


    def _update_wife_ss_label(self, *args):
        self.wife_ss_label_var.set(f"Wife Social Security Age: {self.tmp_ss_age_w.get()}")


    def _update_wife_label(self, *args):
        self.wife_label_var.set(f"Wife Retirement Age: {self.tmp_ret_age_w.get()}")


    def _update_inflation_label(self, val):
        value = round(float(val), 1)
        self.inflation_value.set(value)
        self.inflation_label_var.set(f"Inflation Rate (%): {value:.1f}")


    def _update_fund_expenses_label(self, val):
        self.fund_expense_label_var.set(f"Fund Expenses (%): {float(val):.2f}")


    def _update_stocks_label(self):
        new_stocks = round(self.stocks_percent.get())
        self.stocks_percent.set(new_stocks)

        bonds = self.bonds_percent.get()
        cash = 100 - (new_stocks + bonds)
        if cash < 0:
            bonds = round(bonds + cash)
            self.bonds_percent.set(bonds)
            cash = 0

        self.stocks_label_var.set(f"Stock: {new_stocks}%")
        self.bonds_label_var.set(f"Bonds: {round(bonds)}%")
        self.cash_label_var.set(f"Cash (calculated): {round(cash)}%")
        self.cash_percent.set(cash)


    def _update_bonds_label(self):
        new_bonds = round(self.bonds_percent.get())
        self.bonds_percent.set(new_bonds)

        stocks = self.stocks_percent.get()
        cash = 100 - (stocks + new_bonds)
        if cash < 0:
            stocks = round(stocks + cash)
            self.stocks_percent.set(stocks)
            cash = 0

        self.stocks_label_var.set(f"Stock: {round(stocks)}%")
        self.bonds_label_var.set(f"Bonds: {new_bonds}%")
        self.cash_label_var.set(f"Cash (calculated): {round(cash)}%")
        self.cash_percent.set(cash)


    def get_values(self):
        wife_ret_age = None
        wife_ss_age = None

        if self.tmp_ret_age_w is not None:
            wife_ret_age = self.tmp_ret_age_w.get()

        if self.tmp_ss_age_w is not None:
            wife_ss_age = self.tmp_ss_age_w.get()

        return ScenarioControlValues(
            husband_ret_age=self.tmp_ret_age_h.get(), husband_ss_age=self.tmp_ss_age_h.get(),
            wife_ret_age=wife_ret_age, wife_ss_age=wife_ss_age, inflation=self.inflation_value.get(),
            fund_expense=self.fund_expense_value.get(), stocks=self.stocks_percent.get(),
            bonds=self.bonds_percent.get(), cash=self.cash_percent.get(), dynamic_value=self.dynamic_value.get(),
            calculate_real_dollars=self.calculate_real_dollars.get(), enable_annotations=self.enable_annotations.get()
        )

    # --------------------
    # Enable/disable sliders
    # --------------------
    def _update_slider_state(self, *args):
        enabled = bool(self.enable_overrides.get())
        if enabled:
            state = "normal"
        else:
            state = "disabled"

        # Sliders/labels that always exist
        slider_label_pairs = [
            (self.husband_slider, self.husband_label),
            (self.husband_ss_slider, self.husband_ss_label),
            (self.inflation_slider, self.inflation_label),
            (self.fund_expense_slider, self.fund_expense_label),
            (self.stocks_slider, self.stocks_label),
            (self.bonds_slider, self.bonds_label),
        ]

        if self.wife_slider is not None and self.wife_label is not None:
            slider_label_pairs.append((self.wife_slider, self.wife_label))
        if self.wife_ss_slider is not None and self.wife_ss_label is not None:
            slider_label_pairs.append((self.wife_ss_slider, self.wife_ss_label))

        for slider, label in slider_label_pairs:
            slider.configure(state=state)

            if enabled:
                label.configure(foreground="")
            else:
                label.configure(foreground="gray")

        if enabled:
            self.cash_label.configure(foreground="")
        else:
            self.cash_label.configure(foreground="gray")


    def _configure_dynamic_slider(self):
        controls = self.main_gui.simulation_controls
        expense_mode = controls.get("always_use_expense_mode", False)

        if expense_mode:
            self.dynamic_slider.configure(from_=50, to=200)

            if self.retirement_snapshots.scenario_expense_multiplier is None:
                self.dynamic_value.set(100)
            else:
                self.dynamic_value.set(self.retirement_snapshots.scenario_expense_multiplier * 100.0)

            self.dynamic_label_var.set(f"Expense Multiplier: {self.dynamic_value.get():.0f}%")
        else:
            self.dynamic_slider.configure(from_=0, to=10)

            if self.retirement_snapshots.scenario_withdraw_pct is None:
                self.dynamic_value.set(self.main_gui.simulation_controls.get("retirement_withdraw_pct", 4.0))
            else:
                self.dynamic_value.set(self.retirement_snapshots.scenario_withdraw_pct)

            self.dynamic_label_var.set(f"Withdrawal: {self.dynamic_value.get():.1f}%")


    def _update_dynamic_slider_label(self, val):
        value = float(val)
        controls = self.main_gui.simulation_controls
        expense_mode = controls.get("always_use_expense_mode", False)

        if expense_mode:
            value = round(value)
            self.dynamic_value.set(value)
            self.dynamic_label_var.set(f"Expense Multiplier: {value:.0f}%")
        else:
            value = round(value, 1)
            self.dynamic_value.set(value)
            self.dynamic_label_var.set(f"Withdrawal: {value:.1f}%")