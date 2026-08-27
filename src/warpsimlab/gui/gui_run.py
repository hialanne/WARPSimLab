# gui_run.py

import json
from tkinter import filedialog, messagebox
import os
import copy

from src.warpsimlab.dataClasses.person import Person
from src.warpsimlab.sim.simulation import run_simulation
from src.warpsimlab.sim.validation import SimulationValidationError
from src.warpsimlab.utils.constants import *
from src.warpsimlab.dataClasses.portfolio import Portfolio  # import the new class
from src.warpsimlab.sim.simulationObject import Simulation
from src.warpsimlab.gui.gui_normalIncome import *
from src.warpsimlab.utils.io_utils import *
from src.warpsimlab.utils.utilities import *
from src.warpsimlab.gui.gui_annotations import build_normal_run_annotations


class PortfolioSimulatorGUI_RunMixin:
    """Contains all action-related methods for PortfolioSimulatorGUI:
    running the simulation, saving JSON settings, and resetting defaults.
    """

    def _build_report_options(self, sim_type):
        if sim_type == "summary_report":
            return copy.deepcopy(
                self.report_options["executive_summary"]
            )

        if sim_type == "year_by_year_report":
            return copy.deepcopy(
                self.report_options["year_by_year_details"]
            )

        if sim_type == "tax_report":
            return copy.deepcopy(
                self.report_options["tax_report"]
            )

        if sim_type == "historical_window_risk_report":
            return copy.deepcopy(
                self.report_options["historical_window_risk"]
            )

        if sim_type == "monte_carlo_risk_report":
            return copy.deepcopy(
                self.report_options["monte_carlo_risk"]
            )

        if sim_type == "spending_comparison_report":
            return copy.deepcopy(
                self.report_options["spending_comparison"]
            )

        if sim_type == "asset_allocation_comparison_report":
            return copy.deepcopy(
                self.report_options["asset_allocation_comparison"]
            )

        if sim_type == "retirement_ss_comparison_report":
            return copy.deepcopy(
                self.report_options["retirement_ss_comparison"]
            )

        return {}


    def _simulation_int(self, name, value):
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise SimulationValidationError(f"{name} must be an integer.") from exc

    def _simulation_float(self, name, value):
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise SimulationValidationError(f"{name} must be numeric.") from exc

    def build_simulation_from_gui(self, sim_type=None, use_snapshots=False, retirement_snapshots=None):

        report_options = self._build_report_options(sim_type)
        
        sim_cfg = self.simulation_settings
        controls = self.simulation_controls

        if use_snapshots:
            inflation               = retirement_snapshots.inflation
            fund_expense            = retirement_snapshots.fund_expense
            initial_allocation_mode = "custom"
            custom_stock = self._simulation_float(
                "Scenario stock allocation", retirement_snapshots.custom_stock_percent) / 100
            custom_bonds = self._simulation_float(
                "Scenario bond allocation", retirement_snapshots.custom_bonds_percent) / 100
            custom_cash = self._simulation_float(
                "Scenario cash allocation", retirement_snapshots.custom_cash_percent) / 100
            historical_multiplier = self._simulation_float(
                "Scenario historical data multiplier", retirement_snapshots.historical_data_multiplier) / 100
            adjust_hist_for_infl_delta = bool(
                getattr(retirement_snapshots, "adjust_hist_for_infl_delta", False)
            )
            delta_inflation = self._simulation_float(
                "Scenario inflation adjustment", getattr(retirement_snapshots, "delta_inflation", 0.0)
            ) if adjust_hist_for_infl_delta else 0.0

            use_snapshot_annotations = retirement_snapshots.use_snapshot_annotations
            scenario_explorer_annotations = retirement_snapshots.annotation_strings
            user_annotation_strings = controls.get("user_annotation_strings", [])
            scenario_withdraw_pct   = retirement_snapshots.scenario_withdraw_pct
            scenario_expense_multiplier = retirement_snapshots.scenario_expense_multiplier
        else:
            inflation               = self.inflation
            fund_expense            = sim_cfg.get("fund_expense")
            initial_allocation_mode = sim_cfg.get("initial_allocation_mode", "none")
            custom_stock = self._simulation_float("Custom stock allocation", sim_cfg.get("custom_stock", 0)) / 100
            custom_bonds = self._simulation_float("Custom bond allocation", sim_cfg.get("custom_bonds", 0)) / 100
            custom_cash = self._simulation_float("Custom cash allocation", sim_cfg.get("custom_cash", 0)) / 100
            historical_multiplier   = 1
            delta_inflation = 0.0

            use_snapshot_annotations = controls.get("annotate_plots")
            user_annotation_strings = controls.get("user_annotation_strings", [])
            scenario_explorer_annotations = build_normal_run_annotations(controls)
   

        # --- Market data ---
        market_data = {
            "eq_mean": self.eq_mean,
            "bd_mean": self.bd_mean,
            "cs_mean": self.cs_mean,
            "re_mean": self.re_mean,
            "eq_std": self.eq_std,
            "bd_std": self.bd_std,
            "cs_std": self.cs_std,
            "re_std": self.re_std,
            "inflation": self.inflation,
        }
        
        #Overrides 
        #print("inflation "+str(inflation))
        #print("fund_expense "+str(fund_expense))
        #print("custom_stock "+str(custom_stock))
        #print("custom_bonds "+str(custom_bonds))
        #print("custom_cash "+str(custom_cash))
        #print("historical_multiplier "+str(historical_multiplier))


        # --- Build Simulation object ---
        sim_config = Simulation(
            root=self.root,
            start_year=self._simulation_int("Simulation start year", sim_cfg.get("start_year", 2023)),
            years_to_simulate=self._simulation_int("Years to simulate", sim_cfg.get("years_to_simulate", 30)),
            inflation_rate=self._simulation_float("Inflation rate", inflation) / 100,
            num_sims=self._simulation_int("Number of simulations", sim_cfg.get("num_sims", 500)),
            fund_expense=self._simulation_float("Fund expense", fund_expense) / 100,
            use_fund_expenses=sim_cfg.get("use_fund_expenses", True),

            sim_type=sim_type,

            report_options=report_options,

            eq_mean=(self._simulation_float("Equity mean return", market_data["eq_mean"]) * historical_multiplier
                     + delta_inflation) / 100,
            bd_mean=(self._simulation_float("Bond mean return", market_data["bd_mean"]) * historical_multiplier
                     + delta_inflation) / 100,
            cs_mean=(self._simulation_float("Cash mean return", market_data["cs_mean"]) * historical_multiplier
                     + delta_inflation) / 100,
            re_mean=(self._simulation_float("Real estate mean return", market_data["re_mean"]) * historical_multiplier
                     + delta_inflation) / 100,
            eq_std=self._simulation_float("Equity standard deviation", market_data["eq_std"]) / 100,
            bd_std=self._simulation_float("Bond standard deviation", market_data["bd_std"]) / 100,
            cs_std=self._simulation_float("Cash standard deviation", market_data["cs_std"]) / 100,
            re_std=self._simulation_float("Real estate standard deviation", market_data["re_std"]) / 100,

            sim_initial_allocation_mode=initial_allocation_mode,
            custom_stock=custom_stock,
            custom_bonds=custom_bonds,
            custom_cash=custom_cash,

            include_rmd=controls.get("include_rmd", False),
            retirement_withdraw_mode=controls.get("retirement_withdraw_mode", "Off"),

            retirement_withdraw_pct=(
                scenario_withdraw_pct
                if use_snapshots and scenario_withdraw_pct is not None
                else controls.get("retirement_withdraw_pct", 4.0)
            ),
            
            retirement_withdraw_dollars=controls.get("retirement_withdraw_dollars", 0.0),
            sequence_risk_enabled=controls.get("sequence_risk_enabled", False),
            sequence_risk_timing=controls.get("sequence_risk_timing", "None"),
            sequence_risk_start_year_offset=controls.get("sequence_risk_start_year_offset", 0),
            sequence_risk_length=controls.get("sequence_risk_length", "Medium"),
            sequence_risk_depth=controls.get("sequence_risk_depth", "Moderate"),
            always_use_expense_mode=controls.get("always_use_expense_mode", False),
            calculate_income_taxes=controls.get("calculate_income_taxes", False),
            calculate_payroll_taxes=controls.get("calculate_payroll_taxes", True),
            tax_filing_status=controls.get("tax_filing_status", "single"),
            calculate_state_taxes=controls.get("calculate_state_taxes", False),
            state_of_residence=controls.get("state_of_residence", ""),

            plot_mode=controls.get("plot_mode", "real"),
            subplot_mode=controls.get("subplot_mode", "fill"),
            monte_carlo_plot_style=controls.get("monte_carlo_plot_style", "fill"),
            use_correlated_returns=controls.get("use_correlated_returns", True),
            monte_carlo_mode=controls.get("monte_carlo_mode", "pathBasedAnnualSampling"),
            historical_asset_returns_file=controls.get(
                "historical_asset_returns_file",
                "us_asset_returns_1876_2025.csv"
            ),
            historical_inflation_file=controls.get(
                "historical_inflation_file",
                "us_inflation_1876_2025_real.csv"
            ),
            historical_window_mode=controls.get(
                "historical_window_mode",
                "rolling_overlapping_all"
            ),
            disable_sequence_risk_for_historical=controls.get(
                "disable_sequence_risk_for_historical",
                True
            ),
            show_simulated_shortfall_rate=controls.get("show_simulated_shortfall_rate", True),
            output_csv=controls.get("output_csv", False),
            csv_output_dir=controls.get("csv_output_dir", ""),

            annotate_plots=controls.get("annotate_plots", False),
            constant_y_plots=controls.get("constant_y_plots", False),
            rebalance_every_year=controls.get("rebalance_every_year", True),
            include_realestate=controls.get("include_realestate", False),
            second_person_enabled=controls.get("enable_second_person", False),

            husband_portfolio=self._portfolio_for_sim(self.husband_portfolio),
            wife_portfolio=(
                self._portfolio_for_sim(self.wife_portfolio)
                if controls.get("enable_second_person", False)
                else None
            ),

            special_income_streams=[
                dict(stream)
                for stream in getattr(
                    self,
                    "special_income_streams",
                    [],
                )
            ],

            roth_flows=[
                dict(flow)
                for flow in getattr(
                    self,
                    "roth_flows",
                    [],
                )
            ],

            overlay_tax_impacts=controls.get("overlay_tax_impacts", False),
            overlay_fund_expense_impacts=controls.get("overlay_fund_expense_impacts", False),
            overlay_household_expenses=controls.get("overlay_household_expenses", False),
            overlay_profit_loss=controls.get("overlay_profit_loss", True),
            overlay_retirement_age=controls.get("overlay_retirement_age", False),

            use_snapshot_annotations=use_snapshot_annotations,
            user_annotation_strings=user_annotation_strings,
            scenario_explorer_annotations=scenario_explorer_annotations,
            scenario_expense_multiplier=(
                scenario_expense_multiplier
                if use_snapshots and scenario_expense_multiplier is not None
                else 1.0
            ),
        )

        #sprint("initial_allocation_mode in gui_run:" + str(initial_allocation_mode))

        # Normalize incompatible plot options:
        # In Monte Carlo mode, do not draw or label fund expense overlays.
        if getattr(sim_config, "subplot_mode", None) == "monte_carlo":
            sim_config.overlay_fund_expense_impacts = False

        # Testing code for the reports
        #print(sim_config.sim_type)
        #print(sim_config.report_options)

        return sim_config


    def _portfolio_for_sim(self, p: Portfolio) -> Portfolio:
        """
        Build the Portfolio instance that will be passed into the simulation.

        Advanced mode: exact clone of truth.
        Basic mode: only cash_post is preserved; all other fields are set to 0.0.
        """
        sim_p = Portfolio(
            equity_pre=self._simulation_float("Pre-tax equity", p.equity_pre),
            equity_post=self._simulation_float("Post-tax equity", p.equity_post),
            equity_roth=self._simulation_float("Roth equity", getattr(p, "equity_roth", 0.0)),

            bond_pre=self._simulation_float("Pre-tax bonds", p.bond_pre),
            bond_post=self._simulation_float("Post-tax bonds", p.bond_post),
            bond_roth=self._simulation_float("Roth bonds", getattr(p, "bond_roth", 0.0)),

            cash_pre=self._simulation_float("Pre-tax cash", p.cash_pre),
            cash_post=self._simulation_float("Post-tax cash", p.cash_post),
            cash_roth=self._simulation_float("Roth cash", getattr(p, "cash_roth", 0.0)),

            hsa_cash=self._simulation_float("HSA cash", getattr(p, "hsa_cash", 0.0)),
            hsa_equity=self._simulation_float("HSA equity", getattr(p, "hsa_equity", 0.0)),
            hsa_bond=self._simulation_float("HSA bonds", getattr(p, "hsa_bond", 0.0)),

            real_estate=self._simulation_float("Real estate", p.real_estate),
        )

        if self.mode_var.get() == "Basic":
            sim_p.equity_pre = 0.0
            sim_p.equity_post = 0.0
            sim_p.equity_roth = 0.0

            sim_p.bond_pre = 0.0
            sim_p.bond_post = 0.0
            sim_p.bond_roth = 0.0

            sim_p.cash_pre = 0.0
            sim_p.cash_roth = 0.0

            sim_p.hsa_cash = 0.0
            sim_p.hsa_equity = 0.0
            sim_p.hsa_bond = 0.0

            sim_p.real_estate = 0.0
            # cash_post intentionally preserved

        return sim_p


    def _person_for_sim(self, p: Person) -> Person:
        """
        Build the Person instance that will be passed into the simulation.

        Advanced mode: exact clone of truth.
        Basic mode: only fields visible in Basic UI are active (age, income, retire_age, ss).
                   All other income types are zeroed, and ss_age is set to retire_age
                   to avoid hidden settings affecting results.
        """
        sim_p = Person(
            age=self._simulation_int("Age", p.age),
            retire_age=self._simulation_int("Retirement age", p.retire_age),
            income=self._simulation_float("Income", p.income),
            ss=self._simulation_float("Social Security", p.ss),
            ss_age=self._simulation_int("Social Security age", p.ss_age),
            pension=self._simulation_float("Pension", p.pension),
            pension_age=self._simulation_int("Pension age", p.pension_age),
            annuity=self._simulation_float("Annuity", p.annuity),
            annuity_age=self._simulation_int("Annuity age", p.annuity_age),
            annual_401k_contribution=self._simulation_float(
                "401(k) contribution", getattr(p, "annual_401k_contribution", 0.0)
            ),
            annual_employer_match=self._simulation_float(
                "Employer match", getattr(p, "annual_employer_match", 0.0)
            ),
            annual_hsa_contribution=self._simulation_float(
                "HSA contribution", getattr(p, "annual_hsa_contribution", 0.0)
            ),
            annual_hsa_employer_contribution=self._simulation_float(
                "Employer HSA contribution", getattr(p, "annual_hsa_employer_contribution", 0.0)
            ),
            pension_inflation_adjustment_pct=self._simulation_float(
                "Pension inflation adjustment", getattr(p, "pension_inflation_adjustment_pct", 0.0)
            ),
        )

        if self.mode_var.get() == "Basic":
            sim_p.pension = 0.0
            sim_p.annuity = 0.0
            sim_p.annual_401k_contribution = 0.0
            sim_p.annual_employer_match = 0.0
            sim_p.annual_hsa_contribution = 0.0
            sim_p.annual_hsa_employer_contribution = 0.0
            sim_p.pension_inflation_adjustment_pct = 0.0

            # Avoid hidden SS start age influencing results in Basic mode
            sim_p.ss_age = sim_p.retire_age

            # pension_age / annuity_age become irrelevant since amounts are 0,
            # but you can normalize them if you want:
            sim_p.pension_age = sim_p.retire_age
            sim_p.annuity_age = sim_p.retire_age

        return sim_p

    def commit_pending_gui_edits(self):
        """
        Force pending GUI edits to validate and write through to backing data
        before running simulations or opening result dialogs.

        Returns False when any GUI validator reports invalid input.
        """
        self.root._warpsimlab_validation_failed = False

        focus_widget = self.root.focus_get()

        if focus_widget is not None:
            widget_class = focus_widget.winfo_class()

            if widget_class in {"TEntry", "Entry", "Spinbox", "TSpinbox"}:
                focus_widget.tk.call(focus_widget._w, "validate")

        container = getattr(self, "edit_frame_container", None)
        if container is not None:
            self._validate_entries_recursive(container)

        self.root.update_idletasks()
        return not self.root._warpsimlab_validation_failed


    def _validate_entries_recursive(self, parent):
        for child in parent.winfo_children():
            widget_class = child.winfo_class()

            if widget_class in {"TEntry", "Entry", "Spinbox", "TSpinbox"}:
                state = str(child.cget("state")) if "state" in child.keys() else "normal"
                if state != "disabled":
                    child.tk.call(child._w, "validate")

            self._validate_entries_recursive(child)


    def run_simulation_from_gui(self, sim_type=None):
        if not self.commit_pending_gui_edits():
            return

        try:
            husband = self._person_for_sim(self.husband)
            wife = self._person_for_sim(self.wife) if self.simulation_controls.get("enable_second_person") else None

            husband_portfolio = self._portfolio_for_sim(self.husband_portfolio)
            wife_portfolio = self._portfolio_for_sim(self.wife_portfolio) if wife else None

            sim_config = self.build_simulation_from_gui(sim_type=sim_type)

            run_simulation(
                husband_portfolio=husband_portfolio,
                wife_portfolio=wife_portfolio,
                husband=husband,
                wife=wife,
                expenses=self.expensesDict,
                sim_config=sim_config
            )
        except SimulationValidationError as exc:
            messagebox.showerror("Simulation Input Error", str(exc), parent=self.root)
            return
