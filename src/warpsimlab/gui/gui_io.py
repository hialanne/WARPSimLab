# gui_io.py

import json
from tkinter import filedialog, messagebox
import os
from pathlib import Path

from src.warpsimlab.dataClasses.person import Person
from src.warpsimlab.sim.simulation import run_simulation
from src.warpsimlab.utils.constants import *
from src.warpsimlab.dataClasses.portfolio import Portfolio  # import the new class
from src.warpsimlab.sim.simulationObject import Simulation
from src.warpsimlab.gui.gui_normalIncome import *
from src.warpsimlab.utils.io_utils import *
from src.warpsimlab.utils.utilities import *


class PortfolioSimulatorGUI_IOMixin:
    """Handles saving and loading GUI data to/from JSON."""

    def get_default_warpsimlab_dir(self):
        """Return the default WARPSimLab directory on the Desktop."""
        default_dir = Path.home() / "Desktop" / "WARPSimLab Data"
        default_dir.mkdir(parents=True, exist_ok=True)
        return default_dir


    def load_values_from_json(self):
        """
        Load financial data from the default location or allow user selection.
        """

        default_file = self.get_default_warpsimlab_dir() / "financialDataWAS.json"

        if default_file.exists():
            file_path = default_file
        else:
            file_path = filedialog.askopenfilename(
                title="Select Financial Data JSON",
                initialdir=str(self.get_default_warpsimlab_dir()),
                filetypes=[("JSON Files", "*.json")]
            )

        if not file_path:
            return

        self._load_from_json(file_path)


    def load_examples_from_json(self):
        """
        Load example financial data from src/dataFiles directory.
        """

        example_dir = self._get_examples_directory()

        file_path = filedialog.askopenfilename(
            title="Select Example Financial Data JSON",
            initialdir=example_dir,
            filetypes=[("JSON Files", "*.json")]
        )

        if not file_path:
            return

        self._load_from_json(file_path)

    def _get_examples_directory(self):
        """
        Return path to src/dataFiles
        Works for:
        - python WARPSimLab.py
        - PyInstaller one-folder
        - PyInstaller one-file
        """
        if hasattr(sys, "_MEIPASS"):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..")
            )

        return os.path.join(base_path, "exampleFiles")


    def _load_from_json(self, file_path):
        try:
            # Load JSON
            data = load_financial_data_from_json(file_path)

            # --- Husband ---
            self.husband.age           = data.get("DEFAULT_HUSBAND_AGE", self.husband.age)
            self.husband.retire_age    = data.get("DEFAULT_HUSBAND_RETIRE", self.husband.retire_age)
            self.husband.income        = data.get("DEFAULT_HUSBAND_INCOME", self.husband.income)
            self.husband.ss            = data.get("DEFAULT_HUSBAND_SOC", self.husband.ss)
            self.husband.ss_age        = data.get("DEFAULT_HUSBAND_SOC_AGE", self.husband.ss_age)
            self.husband.pension       = data.get("DEFAULT_HUSBAND_PENSION", self.husband.pension)
            self.husband.pension_age   = data.get("DEFAULT_HUSBAND_PENSION_AGE", self.husband.pension_age)
            self.husband.pension_inflation_adjustment_pct = data.get("DEFAULT_HUSBAND_PENSION_INFLATION_ADJ",self.husband.pension_inflation_adjustment_pct)
            self.husband.annuity       = data.get("DEFAULT_HUSBAND_ANNUITY", self.husband.annuity)
            self.husband.annuity_age   = data.get("DEFAULT_HUSBAND_ANNUITY_AGE", self.husband.annuity_age)
            self.husband.annual_401k_contribution = data.get(
                "DEFAULT_HUSBAND_401K_CONTRIB", self.husband.annual_401k_contribution
            )
            self.husband.annual_employer_match = data.get(
                "DEFAULT_HUSBAND_401K_MATCH", self.husband.annual_employer_match
            )

            # --- Husband Portfolio ---
            h_port = self.husband_portfolio
            h_port.equity_pre  = data.get("DEFAULT_EQUITY_PRE_H", h_port.equity_pre)
            h_port.equity_post = data.get("DEFAULT_EQUITY_POST_H", h_port.equity_post)
            h_port.equity_roth = data.get("DEFAULT_EQUITY_ROTH_H", getattr(h_port, "equity_roth", 0.0))
            h_port.bond_pre    = data.get("DEFAULT_BOND_PRE_H", h_port.bond_pre)
            h_port.bond_post   = data.get("DEFAULT_BOND_POST_H", h_port.bond_post)
            h_port.bond_roth = data.get("DEFAULT_BOND_ROTH_H", getattr(h_port, "bond_roth", 0.0))
            h_port.cash_pre    = data.get("DEFAULT_CASH_PRE_H", h_port.cash_pre)
            h_port.cash_post   = data.get("DEFAULT_CASH_POST_H", h_port.cash_post)
            h_port.cash_roth = data.get("DEFAULT_CASH_ROTH_H", getattr(h_port, "cash_roth", 0.0))
            h_port.hsa_cash = data.get("DEFAULT_HSA_CASH_H", getattr(h_port, "hsa_cash", 0.0))
            h_port.hsa_equity = data.get("DEFAULT_HSA_EQUITY_H", getattr(h_port, "hsa_equity", 0.0))
            h_port.hsa_bond = data.get("DEFAULT_HSA_BOND_H", getattr(h_port, "hsa_bond", 0.0))
            h_port.real_estate = data.get("DEFAULT_REAL_ESTATE_H", h_port.real_estate)

            # --- Second person enabled? ---
            second_person_flag = data.get("DEFAULT_ENABLE_SECOND_PERSON", 0)
            self.simulation_controls["enable_second_person"] = second_person_flag

            if second_person_flag:
                # Ensure Tk updates GUI traces
                self.root.update_idletasks()

                # --- Wife ---
                self.wife.age         = data.get("DEFAULT_WIFE_AGE", self.wife.age)
                self.wife.retire_age  = data.get("DEFAULT_WIFE_RETIRE", self.wife.retire_age)
                self.wife.income      = data.get("DEFAULT_WIFE_INCOME", self.wife.income)
                self.wife.ss          = data.get("DEFAULT_WIFE_SOC", self.wife.ss)
                self.wife.ss_age      = data.get("DEFAULT_WIFE_SOC_AGE", self.wife.ss_age)
                self.wife.pension     = data.get("DEFAULT_WIFE_PENSION", self.wife.pension)
                self.wife.pension_age = data.get("DEFAULT_WIFE_PENSION_AGE", self.wife.pension_age)
                self.wife.pension_inflation_adjustment_pct = data.get("DEFAULT_WIFE_PENSION_INFLATION_ADJ",self.wife.pension_inflation_adjustment_pct)
                self.wife.annuity     = data.get("DEFAULT_WIFE_ANNUITY", self.wife.annuity)
                self.wife.annuity_age = data.get("DEFAULT_WIFE_ANNUITY_AGE", self.wife.annuity_age)
                self.wife.annual_401k_contribution = data.get(
                    "DEFAULT_WIFE_401K_CONTRIB", self.wife.annual_401k_contribution
                )
                self.wife.annual_employer_match = data.get(
                    "DEFAULT_WIFE_401K_MATCH", self.wife.annual_employer_match
                )

                # --- Wife Portfolio ---
                w_port = self.wife_portfolio
                w_port.equity_pre  = data.get("DEFAULT_EQUITY_PRE_W", w_port.equity_pre)
                w_port.equity_post = data.get("DEFAULT_EQUITY_POST_W", w_port.equity_post)
                w_port.equity_roth = data.get("DEFAULT_EQUITY_ROTH_W", getattr(w_port, "equity_roth", 0.0))
                w_port.bond_pre    = data.get("DEFAULT_BOND_PRE_W", w_port.bond_pre)
                w_port.bond_post   = data.get("DEFAULT_BOND_POST_W", w_port.bond_post)
                w_port.bond_roth = data.get("DEFAULT_BOND_ROTH_W", getattr(w_port, "bond_roth", 0.0))
                w_port.cash_pre    = data.get("DEFAULT_CASH_PRE_W", w_port.cash_pre)
                w_port.cash_post   = data.get("DEFAULT_CASH_POST_W", w_port.cash_post)
                w_port.cash_roth = data.get("DEFAULT_CASH_ROTH_W", getattr(w_port, "cash_roth", 0.0))
                w_port.hsa_cash = data.get("DEFAULT_HSA_CASH_W", getattr(w_port, "hsa_cash", 0.0))
                w_port.hsa_equity = data.get("DEFAULT_HSA_EQUITY_W", getattr(w_port, "hsa_equity", 0.0))
                w_port.hsa_bond = data.get("DEFAULT_HSA_BOND_W", getattr(w_port, "hsa_bond", 0.0))
                w_port.real_estate = data.get("DEFAULT_REAL_ESTATE_W", w_port.real_estate)

            # --- Simulation / global settings ---
            self.simulation_settings['years_to_simulate'] = data.get("DEFAULT_YEARS", 30)
            self.simulation_settings['num_sims'] = data.get("DEFAULT_SIMULATIONS", 500)
            self.simulation_settings['fund_expense'] = data.get("DEFAULT_FUND_EXPENSE", 0.0)

            # --- Expenses ---
            self.expensesDict.expenses.clear()
            for exp in data.get("EXPENSES", []):
                start_year = exp.get("start_year")
                end_year   = exp.get("end_year")
                cost       = exp.get("cost")
                comment    = exp.get("comment", "")
                if start_year is not None and cost is not None:
                    self.expensesDict.add_expense(start_year, cost, end_year, comment)
            self.special_income_streams.clear()

            for stream in data.get("SPECIAL_INCOME_STREAMS", []):
                self.special_income_streams.append(dict(stream))

            container = getattr(self, "edit_frame_container", None)
            if container is not None:
                for widget in container.winfo_children():
                    widget.destroy()

            messagebox.showinfo("Loaded", f"Financial data loaded successfully from:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")



    def save_values_to_json(self):
        """
        Save all current GUI inputs (personal, portfolio, simulation, expenses)
        to a JSON file using the DEFAULT_ keys convention.
        """

        # --- Build the JSON structure using upper-case DEFAULT_ keys ---
        updated_values = {
            # Husband Personal Information
            "DEFAULT_HUSBAND_AGE":      self.husband.age,
            "DEFAULT_HUSBAND_RETIRE":   self.husband.retire_age,
            "DEFAULT_HUSBAND_INCOME":   parse_money_strict(self.husband.income,'husband.income'), 
            "DEFAULT_HUSBAND_SOC":      parse_money_strict(self.husband.ss,'husband.ss'),  
            "DEFAULT_HUSBAND_SOC_AGE":  self.husband.ss_age,
            "DEFAULT_HUSBAND_PENSION":  parse_money_strict(self.husband.pension,'husband.pension'), 
            "DEFAULT_HUSBAND_PENSION_AGE": self.husband.pension_age,
            "DEFAULT_HUSBAND_PENSION_INFLATION_ADJ": self.husband.pension_inflation_adjustment_pct,
            "DEFAULT_HUSBAND_ANNUITY":  parse_money_strict(self.husband.annuity,'husband.annuity'), 
            "DEFAULT_HUSBAND_ANNUITY_AGE": self.husband.annuity_age,
            "DEFAULT_HUSBAND_401K_CONTRIB": parse_money_strict(
                self.husband.annual_401k_contribution, "husband.annual_401k_contribution"
            ),
            "DEFAULT_HUSBAND_401K_MATCH": parse_money_strict(
                self.husband.annual_employer_match, "husband.annual_employer_match"
            ),

            # Husband Portfolio
            "DEFAULT_EQUITY_PRE_H": self.husband_portfolio.equity_pre,
            "DEFAULT_EQUITY_POST_H": self.husband_portfolio.equity_post,
            "DEFAULT_BOND_PRE_H": self.husband_portfolio.bond_pre,
            "DEFAULT_BOND_POST_H": self.husband_portfolio.bond_post,
            "DEFAULT_CASH_PRE_H": self.husband_portfolio.cash_pre,
            "DEFAULT_CASH_POST_H": self.husband_portfolio.cash_post,
            "DEFAULT_EQUITY_ROTH_H": self.husband_portfolio.equity_roth,
            "DEFAULT_BOND_ROTH_H": self.husband_portfolio.bond_roth,
            "DEFAULT_CASH_ROTH_H": self.husband_portfolio.cash_roth,

            "DEFAULT_HSA_CASH_H": self.husband_portfolio.hsa_cash,
            "DEFAULT_HSA_EQUITY_H": self.husband_portfolio.hsa_equity,
            "DEFAULT_HSA_BOND_H": self.husband_portfolio.hsa_bond,

            "DEFAULT_REAL_ESTATE_H": self.husband_portfolio.real_estate,
        }

        # Wife data (if enabled)
        if self.simulation_controls.get("enable_second_person", 0):
            updated_values.update({
                "DEFAULT_ENABLE_SECOND_PERSON": 1,
                "DEFAULT_WIFE_AGE": self.wife.age,
                "DEFAULT_WIFE_RETIRE": self.wife.retire_age,
                "DEFAULT_WIFE_INCOME": parse_money_strict(self.wife.income,'wife.income'), 
                "DEFAULT_WIFE_SOC": parse_money_strict(self.wife.ss,'wife.ss'),
                "DEFAULT_WIFE_SOC_AGE": self.wife.ss_age,
                "DEFAULT_WIFE_PENSION": parse_money_strict(self.wife.pension,'wife.pension'), 
                "DEFAULT_WIFE_PENSION_AGE": self.wife.pension_age,
                "DEFAULT_WIFE_PENSION_INFLATION_ADJ": self.wife.pension_inflation_adjustment_pct,
                "DEFAULT_WIFE_ANNUITY": parse_money_strict(self.wife.annuity,'wife.annuity'), 
                "DEFAULT_WIFE_ANNUITY_AGE": self.wife.annuity_age,
                "DEFAULT_WIFE_401K_CONTRIB": parse_money_strict(
                    self.wife.annual_401k_contribution, "wife.annual_401k_contribution"
                ),
                "DEFAULT_WIFE_401K_MATCH": parse_money_strict(
                    self.wife.annual_employer_match, "wife.annual_employer_match"
                ),

                # Wife Portfolio
                "DEFAULT_EQUITY_PRE_W": self.wife_portfolio.equity_pre,
                "DEFAULT_EQUITY_POST_W": self.wife_portfolio.equity_post,
                "DEFAULT_BOND_PRE_W": self.wife_portfolio.bond_pre,
                "DEFAULT_BOND_POST_W": self.wife_portfolio.bond_post,
                "DEFAULT_CASH_PRE_W": self.wife_portfolio.cash_pre,
                "DEFAULT_CASH_POST_W": self.wife_portfolio.cash_post,
                "DEFAULT_EQUITY_ROTH_W": self.wife_portfolio.equity_roth,
                "DEFAULT_BOND_ROTH_W": self.wife_portfolio.bond_roth,
                "DEFAULT_CASH_ROTH_W": self.wife_portfolio.cash_roth,

                "DEFAULT_HSA_CASH_W": self.wife_portfolio.hsa_cash,
                "DEFAULT_HSA_EQUITY_W": self.wife_portfolio.hsa_equity,
                "DEFAULT_HSA_BOND_W": self.wife_portfolio.hsa_bond,

                "DEFAULT_REAL_ESTATE_W": self.wife_portfolio.real_estate,
            })
        else:
            updated_values["DEFAULT_ENABLE_SECOND_PERSON"] = 0

        # Simulation / global settings
        updated_values.update({
            "DEFAULT_YEARS": int(self.simulation_settings.get('years_to_simulate', 30)),
            "DEFAULT_SIMULATIONS": int(self.simulation_settings.get('num_sims', 500)),
            "DEFAULT_FUND_EXPENSE": float(self.simulation_settings.get('fund_expense', 0)),
            "SPECIAL_INCOME_STREAMS": self.special_income_streams,
            
            # Store dynamic expenses as a JSON array
            "EXPENSES": [
                {
                    "start_year": exp["start_year"],
                    "end_year": exp["end_year"],
                    "cost": exp["cost"],
                    "comment": exp["comment"]
                }
                for exp in getattr(self.expensesDict, "expenses", [])
            ]

        })

        # --- Ask user where to save ---
        default_dir = self.get_default_warpsimlab_dir()
        file_path = filedialog.asksaveasfilename(
            title="Save Financial Data",
            initialdir=str(default_dir),      # Desktop/WARPSimLab Data
            initialfile="financialDataWAS.json",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")]
        )
        if not file_path:
            return  # user canceled

        # --- Save JSON to file ---
        try:
            save_financial_data_to_file(file_path, updated_values)
            messagebox.showinfo("Saved", "Financial data saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")



    def print_gui_state_table(self):
        """Print all current GUI values in a neat table format."""
    
        def money(var):
            try:
                return float(var.get().replace(",", ""))
            except Exception:
                return var.get()
    
        def percent(var):
            try:
                return float(var.get())
            except Exception:
                return var.get()
    
        def bool_str(var):
            return "Yes" if var.get() else "No"

        # Header
        print("\n" + "-"*60)
        print(f"{'Parameter':35} | {'Value'}")
        print("-"*60)
    
        # Personal data
        h = self.husband
        print(f"{'Husband Age':35} | {h.age}")
        print(f"{'Husband Retirement Age':35} | {h.retire_age}")
        print(f"{'Husband Income':35} | {h.income}")
        print(f"{'Husband Social Security':35} | {h.ss} at age {h.ss_age}")
        print(f"{'Husband Pension':35} | {h.pension} at age {h.pension_age}")
        print(f"{'Husband Annuity':35} | {h.annuity} at age {h.annuity_age}")

        if self.enable_second_person.get():
            print('Second person enabled\n')
        else:
            print('Second person disabled\n')
        w = self.wife
        print(f"{'Wife Age':35} | {w.age}")
        print(f"{'Wife Retirement Age':35} | {w.retire_age}")
        print(f"{'Wife Income':35} | {w.income}")
        print(f"{'Wife Social Security':35} | {w.ss} at age {w.ss_age}")
        print(f"{'Wife Pension':35} | {w.pension} at age {w.pension_age}")
        print(f"{'Wife Annuity':35} | {w.annuity} at age {w.annuity_age}")

        # Portfolio
        print('Husband\n')
        print(f"{'Equity Pre-Tax':35} | {money(self.equity_pre_h_var)}")
        print(f"{'Equity Post-Tax':35} | {money(self.equity_post_h_var)}")
        print(f"{'Bond Pre-Tax':35} | {money(self.bond_pre_h_var)}")
        print(f"{'Bond Post-Tax':35} | {money(self.bond_post_h_var)}")
        print(f"{'Cash Pre-Tax':35} | {money(self.cash_pre_h_var)}")
        print(f"{'Cash Post-Tax':35} | {money(self.cash_post_h_var)}")
        print(f"{'Real Estate':35} | {money(self.real_estate_h_var)}")

        print('Wife\n')
        print(f"{'Equity Pre-Tax':35} | {money(self.equity_pre_w_var)}")
        print(f"{'Equity Post-Tax':35} | {money(self.equity_post_w_var)}")
        print(f"{'Bond Pre-Tax':35} | {money(self.bond_pre_w_var)}")
        print(f"{'Bond Post-Tax':35} | {money(self.bond_post_w_var)}")
        print(f"{'Cash Pre-Tax':35} | {money(self.cash_pre_w_var)}")
        print(f"{'Cash Post-Tax':35} | {money(self.cash_post_w_var)}")
        print(f"{'Real Estate':35} | {money(self.real_estate_w_var)}")

        # Simulation parameters
        print(f"{'Years':35} | {self.years_var.get()}")
        print(f"{'Number of Simulations':35} | {self.sims_var.get()}")
        print(f"{'Average Fund Expenses':35} | {self.fund_expense_var.get()}")
        print(f"{'Include RMDs':35} | {bool_str(self.include_rmd_var)}")
        print(f"{'Show Sub Categories':35} | {bool_str(self.show_sub_categories_var)}")
        print(f"{'Show Husband/Wife Assets':35} | {bool_str(self.show_husband_wife_assets_var)}")
        print(f"{'Show Pre/Post Tax Assets':35} | {bool_str(self.show_pre_post_tax_assets_var)}")
        print(f"{'Annotate Plots':35} | {bool_str(self.annotate_plots_var)}")
        print(f"{'Constant Y Plots':35} | {bool_str(self.constant_y_plots_var)}")
        print(f"{'Rebalance Every Year':35} | {bool_str(self.rebalance_every_year_var)}")
        print(f"{'Include Real Estate':35} | {bool_str(self.include_realestate_var)}")

        # Market assumptions
        print(f"{'Inflation Rate (%)':35} | {self.inflation_var.get()}")
        print(f"{'Equity Mean (%)':35} | {percent(self.eq_mean_var)}")
        print(f"{'Bond Mean (%)':35} | {percent(self.bd_mean_var)}")
        print(f"{'Cash Mean (%)':35} | {percent(self.cs_mean_var)}")
        print(f"{'Real Estate Mean (%)':35} | {percent(self.re_mean_var)}")
        print(f"{'Equity Std (%)':35} | {percent(self.eq_std_var)}")
        print(f"{'Bond Std (%)':35} | {percent(self.bd_std_var)}")
        print(f"{'Cash Std (%)':35} | {percent(self.cs_std_var)}")
        print(f"{'Real Estate Std (%)':35} | {percent(self.re_std_var)}")

        # Rebalance / custom allocations
        print(f"{'Rebalance Option':35} | {self.rebalance_var.get()}")
        if self.rebalance_var.get() == "custom":
            print(f"{'Custom Stocks (%)':35} | {percent(self.custom_stock_var)}")
            print(f"{'Custom Bonds (%)':35} | {percent(self.custom_bonds_var)}")
            print(f"{'Custom Cash (%)':35} | {percent(self.custom_cash_var)}")

        # Expenses
        print(f"{'Expenses':35} | {money(self.expenses_var)}")

        # Market data
        print(f"{'Selected Market Data':35} | {self.historical_market_var.get()}")

        # Second person enabled
        print(f"{'Enable Second Person':35} | {bool_str(self.enable_second_person)}")
    
        # Footer
        print("-"*60 + "\n")


def print_simulation_members(sim_obj):
    """
    Print all attributes and values of a Simulation object for debugging.
    """
    if sim_obj is None:
        print("Simulation object is None")
        return

    print("\n" + "="*60)
    print(f"Simulation object: {sim_obj}")
    print("="*60)

    # Print all instance variables
    print("\nInstance attributes:")
    for attr, value in vars(sim_obj).items():
        print(f"{attr:35} : {value}")

    # Print all class-level attributes (methods etc.)
    print("\nOther attributes (methods, class vars, etc.):")
    for attr in dir(sim_obj):
        if attr.startswith("__") and attr.endswith("__"):
            continue
        if attr not in vars(sim_obj):
            print(attr)
    
    print("="*60 + "\n")
