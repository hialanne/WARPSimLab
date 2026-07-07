# gui_run.py

import json
from tkinter import filedialog, messagebox
import os
import copy

from src.dataClasses.person import Person
from src.sim.simulation import run_simulation
from src.utils.constants import *
from src.dataClasses.portfolio import Portfolio  # import the new class
from src.sim.simulationObject import Simulation
from src.gui.gui_normalIncome import *
from src.utils.io_utils import *
from src.utils.utilities import *
from src.gui.gui_annotations import build_normal_run_annotations


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

        return {}


    def build_simulation_from_gui(self, sim_type=None, use_snapshots=False, retirement_snapshots=None):

        report_options = self._build_report_options(sim_type)
        
        sim_cfg = self.simulation_settings
        controls = self.simulation_controls

        if use_snapshots:
            inflation               = retirement_snapshots.inflation
            fund_expense            = retirement_snapshots.fund_expense
            rebalance               = "custom"
            custom_stock            = float(retirement_snapshots.custom_stock_percent / 100)
            custom_bonds            = float(retirement_snapshots.custom_bonds_percent / 100)
            custom_cash             = float(retirement_snapshots.custom_cash_percent / 100)
            historical_multiplier   = float(retirement_snapshots.historical_data_multiplier / 100)
            adjust_hist_for_infl_delta = bool(
                getattr(retirement_snapshots, "adjust_hist_for_infl_delta", False)
            )
            delta_inflation = float(
                getattr(retirement_snapshots, "delta_inflation", 0.0)
            ) if adjust_hist_for_infl_delta else 0.0

            use_snapshot_annotations = retirement_snapshots.use_snapshot_annotations
            scenario_explorer_annotations = retirement_snapshots.annotation_strings
            user_annotation_strings = controls.get("user_annotation_strings", [])
            scenario_withdraw_pct   = retirement_snapshots.scenario_withdraw_pct
            scenario_expense_multiplier = retirement_snapshots.scenario_expense_multiplier
        else:
            inflation               = self.inflation
            fund_expense            = sim_cfg.get("fund_expense")
            rebalance               = sim_cfg.get("rebalance", "none")
            custom_stock            = float(sim_cfg.get("custom_stock", 0)) / 100
            custom_bonds            = float(sim_cfg.get("custom_bonds", 0)) / 100
            custom_cash             = float(sim_cfg.get("custom_cash", 0)) / 100
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
            start_year=int(sim_cfg.get("start_year", 2023)),
            years_to_simulate=int(sim_cfg.get("years_to_simulate", 30)),
            inflation_rate=float(inflation) / 100,   ########### This one can be replaced by the snapshots
            num_sims=int(sim_cfg.get("num_sims", 500)),
            fund_expense=float(fund_expense) / 100,
            use_fund_expenses=sim_cfg.get("use_fund_expenses", True),

            sim_type=sim_type,

            report_options=report_options,

            eq_mean=(float(market_data["eq_mean"]) * historical_multiplier + delta_inflation) / 100,
            bd_mean=(float(market_data["bd_mean"]) * historical_multiplier + delta_inflation) / 100,
            cs_mean=(float(market_data["cs_mean"]) * historical_multiplier + delta_inflation) / 100,
            re_mean=(float(market_data["re_mean"]) * historical_multiplier + delta_inflation) / 100,
            eq_std=float(market_data["eq_std"]) / 100,
            bd_std=float(market_data["bd_std"]) / 100,
            cs_std=float(market_data["cs_std"]) / 100,
            re_std=float(market_data["re_std"]) / 100,

            sim_rebalance=rebalance,
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

            plot_mode=controls.get("plot_mode", "combined"),
            subplot_mode=controls.get("subplot_mode", False),
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
                for stream in getattr(self, "special_income_streams", [])
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
            equity_pre=float(p.equity_pre),
            equity_post=float(p.equity_post),
            equity_roth=float(getattr(p, "equity_roth", 0.0)),

            bond_pre=float(p.bond_pre),
            bond_post=float(p.bond_post),
            bond_roth=float(getattr(p, "bond_roth", 0.0)),

            cash_pre=float(p.cash_pre),
            cash_post=float(p.cash_post),
            cash_roth=float(getattr(p, "cash_roth", 0.0)),

            hsa_cash=float(getattr(p, "hsa_cash", 0.0)),
            hsa_equity=float(getattr(p, "hsa_equity", 0.0)),
            hsa_bond=float(getattr(p, "hsa_bond", 0.0)),

            real_estate=float(p.real_estate),
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
            age=int(p.age),
            retire_age=int(p.retire_age),
            income=float(p.income),
            ss=float(p.ss),
            ss_age=int(p.ss_age),
            pension=float(p.pension),
            pension_age=int(p.pension_age),
            annuity=float(p.annuity),
            annuity_age=int(p.annuity_age),
            annual_401k_contribution=float(getattr(p, "annual_401k_contribution", 0.0)),
            annual_employer_match=float(getattr(p, "annual_employer_match", 0.0)),
            pension_inflation_adjustment_pct=float(getattr(p, "pension_inflation_adjustment_pct", 0.0)),
        )

        if self.mode_var.get() == "Basic":
            sim_p.pension = 0.0
            sim_p.annuity = 0.0
            sim_p.annual_401k_contribution = 0.0
            sim_p.annual_employer_match = 0.0
            sim_p.pension_inflation_adjustment_pct = 0.0

            # Avoid hidden SS start age influencing results in Basic mode
            sim_p.ss_age = int(sim_p.retire_age)

            # pension_age / annuity_age become irrelevant since amounts are 0,
            # but you can normalize them if you want:
            sim_p.pension_age = int(sim_p.retire_age)
            sim_p.annuity_age = int(sim_p.retire_age)

        return sim_p

    def commit_pending_gui_edits(self):
        """
        Force pending GUI edits to validate and write through to backing data
        before running simulations or opening result dialogs.

        This preserves the current UX: users do not need Apply/OK buttons.
        """
        # First, try to validate the widget that currently has focus.
        focus_widget = self.root.focus_get()

        if focus_widget is not None:
            try:
                widget_class = focus_widget.winfo_class()

                # ttk.Entry often reports "TEntry"; tk.Entry reports "Entry"
                if widget_class in {"TEntry", "Entry", "Spinbox", "TSpinbox"}:
                    # Trigger the widget's validate command explicitly if it has one.
                    # This works even when focus does not naturally leave the widget.
                    focus_widget.tk.call(focus_widget._w, "validate")
            except Exception:
                # Do not block the simulation because of commit logic.
                pass

        # Then validate all visible entry-like widgets in the current editor area.
        # This catches cases where focus is on a menu/button but the user edited
        # a field that still has stale text.
        container = getattr(self, "edit_frame_container", None)
        if container is not None:
            self._validate_entries_recursive(container)

        # Let any after_idle callbacks finish, since your validators use after_idle(...)
        self.root.update_idletasks()


    def _validate_entries_recursive(self, parent):
        for child in parent.winfo_children():
            try:
                widget_class = child.winfo_class()

                if widget_class in {"TEntry", "Entry", "Spinbox", "TSpinbox"}:
                    state = str(child.cget("state")) if "state" in child.keys() else "normal"
                    if state != "disabled":
                        try:
                            child.tk.call(child._w, "validate")
                        except Exception:
                            pass

                # Recurse into nested frames
                self._validate_entries_recursive(child)

            except Exception:
                # Ignore widgets that do not behave like standard Tk widgets
                pass


    def run_simulation_from_gui(self, sim_type=None):
        self.commit_pending_gui_edits()
        husband = self._person_for_sim(self.husband)
        wife = self._person_for_sim(self.wife) if self.simulation_controls.get("enable_second_person") else None

        husband_portfolio = self._portfolio_for_sim(self.husband_portfolio)
        wife_portfolio = self._portfolio_for_sim(self.wife_portfolio) if wife else None
        #print("Normal Path")
            
        # Build Simulation from GUI values
        sim_config = self.build_simulation_from_gui(sim_type=sim_type)

        # Pass to simulation
        run_simulation(
            husband_portfolio=husband_portfolio, 
            wife_portfolio=wife_portfolio,
            husband=husband,
            wife=wife,
            expenses=self.expensesDict,
            sim_config=sim_config
        )


