# gui_init.py

import tkinter as tk
from tkinter import ttk
from datetime import datetime
import os

from src.warpsimlab.utils.constants import *
from src.warpsimlab.gui.gui_run import PortfolioSimulatorGUI_RunMixin
from src.warpsimlab.gui.gui_normalIncome import *
from src.warpsimlab.gui.gui_specialIncome import SpecialIncomeEditFrame
from src.warpsimlab.utils.io_utils import *
from src.warpsimlab.gui.gui_portfolio import *
from src.warpsimlab.dataClasses.portfolio import Portfolio 
from src.warpsimlab.gui.gui_historicalData import *
from src.warpsimlab.gui.gui_portfolioSimulation import *
from src.warpsimlab.gui.gui_simulationControls import *
from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.gui.gui_retirement import *
from src.warpsimlab.gui.gui_main import MainHomeFrame
from src.warpsimlab.gui.gui_tutorial import TutorialFrame
from src.warpsimlab.gui.gui_scenarioSnapshots import *
from src.warpsimlab.gui.gui_io import *
from src.warpsimlab.gui.gui_io import PortfolioSimulatorGUI_IOMixin
from src.warpsimlab.gui.gui_scenarioController import ScenarioController
from src.warpsimlab.gui.gui_expenses_taxes import ExpensesTaxesFrame
from src.warpsimlab.gui.gui_utils import (noop,set_tk_button_soft_disabled,create_dropdown_button, create_top_button)
from .gui_notes import NotesFrame
from src.warpsimlab.gui.gui_expenses import ExpensesEditFrame
from src.warpsimlab.gui.gui_taxes import TaxesEditFrame
from src.warpsimlab.gui.gui_roth import RothEditFrame
from src.warpsimlab.gui.gui_reportExecutiveSummary import ExecutiveSummaryReportFrame
from src.warpsimlab.gui.gui_reportYearByYearDetails import YearByYearDetailsReportFrame
from src.warpsimlab.gui.gui_reportHistoricalWindowRisk import HistoricalWindowRiskReportFrame
from src.warpsimlab.gui.gui_reportMonteCarloRisk import MonteCarloRiskReportFrame
from src.warpsimlab.gui.gui_realEstate import RealEstateEditFrame
from src.warpsimlab.gui.gui_derivedStatistics import DerivedStatisticsFrame
from src.warpsimlab.gui.gui_reportTaxes import TaxReportFrame
from src.warpsimlab.gui.gui_guidedtutorial import GuidedTutorialController
from src.warpsimlab.gui.gui_tutorial_definitions import (
    build_basic_tutorial_steps,
    build_advanced_building_tutorial_steps,
    build_advanced_analysis_tutorial_steps,
)


class PortfolioSimulatorGUI(PortfolioSimulatorGUI_RunMixin, PortfolioSimulatorGUI_IOMixin):
    def __init__(self, root):
        self.root = root

        self.legal_accepted = False

        def center_window(window, width, height):
            """Center a Tkinter window on the screen."""
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            window.geometry(f"{width}x{height}+{x}+{y}")

        root.title("WARPSimLab version 4.0")

        window_width = 1200
        window_height = 750
        center_window(root, window_width, window_height)

        ttk.Label(root, text="WARPSimLab version 4.0", font=("Arial", 16)).pack(pady=10)

        self.frame = ttk.Frame(root)
        self.frame.pack(pady=5, padx=10, fill="both", expand=True)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)

        self.husband = Person(
            age=DEFAULT_HUSBAND_AGE,
            retire_age=DEFAULT_HUSBAND_RETIRE,
            income=DEFAULT_HUSBAND_INCOME,
            ss=DEFAULT_HUSBAND_SOC,
            ss_age=DEFAULT_HUSBAND_SOC_AGE,
            pension=DEFAULT_HUSBAND_PENSION,
            pension_age=DEFAULT_HUSBAND_PENSION_AGE,
            annuity=DEFAULT_HUSBAND_ANNUITY,
            annuity_age=DEFAULT_HUSBAND_ANNUITY_AGE,
            annual_401k_contribution=DEFAULT_HUSBAND_401K_CONTRIB,
            annual_employer_match=DEFAULT_HUSBAND_401K_MATCH,
            pension_inflation_adjustment_pct=0.0, 
        )

        self.wife = Person(
            age=DEFAULT_WIFE_AGE,
            retire_age=DEFAULT_WIFE_RETIRE,
            income=DEFAULT_WIFE_INCOME,
            ss=DEFAULT_WIFE_SOC,
            ss_age=DEFAULT_WIFE_SOC_AGE,
            pension=DEFAULT_WIFE_PENSION,
            pension_age=DEFAULT_WIFE_PENSION_AGE,
            annuity=DEFAULT_WIFE_ANNUITY,
            annuity_age=DEFAULT_WIFE_ANNUITY_AGE,
            annual_401k_contribution=DEFAULT_WIFE_401K_CONTRIB,
            annual_employer_match=DEFAULT_WIFE_401K_MATCH,
            pension_inflation_adjustment_pct=0.0, 
        )

        self.husband_portfolio = Portfolio(
            equity_pre=DEFAULT_EQUITY_PRE_H,
            equity_post=DEFAULT_EQUITY_POST_H,
            equity_roth=DEFAULT_EQUITY_ROTH_H,
            bond_pre=DEFAULT_BOND_PRE_H,
            bond_post=DEFAULT_BOND_POST_H,
            bond_roth=DEFAULT_BOND_ROTH_H,
            cash_pre=DEFAULT_CASH_PRE_H,
            cash_post=DEFAULT_CASH_POST_H,
            cash_roth=DEFAULT_CASH_ROTH_H,
            hsa_cash=DEFAULT_HSA_CASH_H,
            hsa_equity=DEFAULT_HSA_EQUITY_H,
            hsa_bond=DEFAULT_HSA_BOND_H,
            real_estate=DEFAULT_REAL_ESTATE_H
        )

        self.wife_portfolio = Portfolio(
            equity_pre=DEFAULT_EQUITY_PRE_W,
            equity_post=DEFAULT_EQUITY_POST_W,
            equity_roth=DEFAULT_EQUITY_ROTH_W,
            bond_pre=DEFAULT_BOND_PRE_W,
            bond_post=DEFAULT_BOND_POST_W,
            bond_roth=DEFAULT_BOND_ROTH_W,
            cash_pre=DEFAULT_CASH_PRE_W,
            cash_post=DEFAULT_CASH_POST_W,
            cash_roth=DEFAULT_CASH_ROTH_W,
            hsa_cash=DEFAULT_HSA_CASH_W,
            hsa_equity=DEFAULT_HSA_EQUITY_W,
            hsa_bond=DEFAULT_HSA_BOND_W,
            real_estate=DEFAULT_REAL_ESTATE_W
        )

        self._init_vars()

        self._build_fields()

        # Guided tutorial controller
        self.guided_tutorial_controller = GuidedTutorialController(self)

        # Scenario controller
        self.scenario_controller = ScenarioController(self)

        self._build_run_button()

        self.edit_main_home()


    # ------------------------
    # Initialize Variables
    # ------------------------
    def _init_vars(self):
        # Load market data
        market_values = load_market_data()  # defaults to "25_year_data"

        self.eq_mean = market_values["eq_mean"]
        self.bd_mean = market_values["bd_mean"]
        self.cs_mean = market_values["cs_mean"]
        self.re_mean = market_values["re_mean"]

        self.eq_std = market_values["eq_std"]
        self.bd_std = market_values["bd_std"]
        self.cs_std = market_values["cs_std"]
        self.re_std = market_values["re_std"]

        self.inflation = market_values["inflation"]
        self.historical_market = "25_year_data"

        # Default simulation settings
        self.simulation_settings = {
            "start_year": datetime.now().year,
            "years_to_simulate": 30,
            "num_sims": 1000,
            "fund_expense": 0.5,
            "use_fund_expenses": True,
            "initial_allocation_mode": "maintain-current-allocation",
            "custom_stock": 0.0,
            "custom_bonds": 0.0,
            "custom_cash": 100.0
        }

        default_csv_dir = os.path.join(os.path.expanduser("~"), "Desktop", "WARPSimLab")

        self.simulation_controls = {
            "enable_second_person": True,
            "include_realestate": False,
            "plot_mode": "real",
            "subplot_mode": "fill",
            "monte_carlo_plot_style": "fill",
            "use_correlated_returns": True,
            #"monte_carlo_mode": "pathBasedAnnualSampling",
            "monte_carlo_mode": "rollingHistoricalWindows",
            "historical_asset_returns_file": "us_asset_returns_1876_2025.csv",
            "historical_inflation_file": "us_inflation_1876_2025_real.csv",
            "historical_window_mode": "rolling_overlapping_all",
            "disable_sequence_risk_for_historical": True,
            "show_simulated_shortfall_rate": True,
            "include_rmd": True,
            "calculate_income_taxes": True,
            "calculate_payroll_taxes": True,
            "tax_filing_status": "Married filing jointly",
            "calculate_state_taxes": True,
            "state_of_residence": "NM",
            "constant_y_plots": False,
            "rebalance_every_year": True,
            "output_csv": "None",
            "csv_output_dir": default_csv_dir,
            "overlay_tax_impacts": False,
            "overlay_fund_expense_impacts": False,
            "overlay_household_expenses": False,
            "overlay_profit_loss": True,
            "overlay_retirement_age": False,
            "retirement_withdraw_mode": "Percentage + Inflation",
            "retirement_withdraw_pct": 4.0,
            "retirement_withdraw_dollars": 0.0,
            "sequence_risk_enabled": False,
            "sequence_risk_timing": "Early downturn",
            "sequence_risk_length": "Medium",
            "sequence_risk_depth": "Moderate",
            "sequence_risk_start_year_offset": 0,
            "always_use_expense_mode": True,
            "annotate_plots": False,
            "user_annotation_strings": []
        }

        self.report_options = {
            "executive_summary": {
                "include_simulation_summary": True,

                "portfolio_visuals": {
                    "include_normal_projection": True,
                    "include_subcategories_projection": False,
                    "include_monte_carlo_analysis": False,
                    "include_historical_windows_analysis": False,
                },

                "income_visuals": {
                    "include_normal_income": True,
                    "include_subcategories_income": False,
                },

                "cashflow_visuals": {
                    "include_normal_cashflow": True,
                    "include_subcategories_cashflow": False,
                },

                "operating_balance_visuals": {
                    "include_cumulative_operating_balance": True,
                },

                "include_assumptions_appendix": True,

                "output_format": "HTML",
            },
            "year_by_year_details": {
                "generate_html": True,
                "generate_csv": True,
                "table_detail": "Compact",
                "insert_5_year_breaks": True,
            },
            "historical_window_risk": {
                "general": {
                    "include_executive_summary": True,
                    "include_method_explanation": True,
                },
                "analysis": {
                    "include_portfolio_projection": True,
                    "include_portfolio_sustainability": True,
                    "include_historical_window_insights": True,
                    "include_percentile_table": True,
                },
                "output": {
                    "generate_html": True,
                    "generate_csv": False,
                },
            },
            "monte_carlo_risk": {
                "general": {
                    "include_executive_summary": True,
                    "include_method_explanation": True,
                },
                "analysis": {
                    "include_portfolio_projection": True,
                    "include_portfolio_sustainability": True,
                    "include_monte_carlo_insights": True,
                    "include_percentile_table": True,
                },
                "output": {
                    "generate_html": True,
                    "generate_csv": False,
                },
            },
            "tax_report": {
                "output": {
                    "generate_html": True,
                    "generate_csv": False,
                },
                "sections": {
                    "include_roth_analysis": True,
                    "include_hsa_analysis": True,
                    "include_rmd_analysis": True,
                    "include_educational_commentary": True,
                },
            },
        }

        # Dynamic expenses
        self.expensesDict = DynamicExpenses()
        self.expensesDict.add_expense(start_year=2026, cost=75000, comment="Initial yearly expense")
        self.expensesDict.add_expense(start_year=2026, end_year=2030, cost=5000, comment="Car or something")

        # Special income streams
        self.special_income_streams = []

        # Scheduled Roth contributions and conversions
        self.roth_flows = []


    def _sync_tax_status_from_second_person(self):
        if self.simulation_controls["enable_second_person"]:
            self.simulation_controls["tax_filing_status"] = "Married filing jointly"
        else:
            self.simulation_controls["tax_filing_status"] = "Single"

    def _advanced_only(self) -> bool:
        return self.mode_var.get() == "Advanced"


    def _apply_mode_to_top_buttons(self):
        is_basic = (self.mode_var.get() == "Basic")
        legal_enabled = getattr(self, "legal_accepted", False)

        basic_enabled = legal_enabled
        advanced_enabled = (not is_basic) and legal_enabled

        set_tk_button_soft_disabled(
            self.home_button,
            basic_enabled,
            self._show_home_menu,
            noop_command=noop
        )

        set_tk_button_soft_disabled(
            self.cashflow_button,
            basic_enabled,
            self._show_cashflow_menu,
            noop_command=noop
        )

        if hasattr(self, "balance_sheet_menu") and hasattr(self, "_balance_sheet_real_estate_index"):
            state = "normal" if advanced_enabled else "disabled"
            self.balance_sheet_menu.entryconfig(self._balance_sheet_real_estate_index, state=state)

        if hasattr(self, "balance_sheet_menu") and hasattr(self, "_balance_sheet_derived_statistics_index"):
            state = "normal" if advanced_enabled else "disabled"
            self.balance_sheet_menu.entryconfig(self._balance_sheet_derived_statistics_index, state=state)

        set_tk_button_soft_disabled(
            self.balance_sheet_button,
            basic_enabled,
            self._show_balance_sheet_menu,
            noop_command=noop
        )

        set_tk_button_soft_disabled(
            self.edit_retirement_button,
            advanced_enabled,
            self._cmd_edit_retirement_controls,
            noop_command=noop
        )

        set_tk_button_soft_disabled(
            self.simulation_button,
            advanced_enabled,
            self._show_simulation_menu,
            noop_command=noop
        )

        set_tk_button_soft_disabled(
            self.results_button,
            basic_enabled,
            self._show_results_menu,
            noop_command=noop
        )

        self._apply_mode_to_reports_button()

        if (
            hasattr(self, "cashflow_menu")
            and hasattr(self, "_cashflow_special_income_index")
        ):
            state = "normal" if advanced_enabled else "disabled"
            self.cashflow_menu.entryconfig(
                self._cashflow_special_income_index,
                state=state,
            )

        if (
            hasattr(self, "cashflow_menu")
            and hasattr(self, "_cashflow_roth_index")
        ):
            state = "normal" if advanced_enabled else "disabled"
            self.cashflow_menu.entryconfig(
                self._cashflow_roth_index,
                state=state,
            )

        if (
            hasattr(self, "cashflow_menu")
            and hasattr(self, "_cashflow_taxes_index")
        ):
            state = "normal" if advanced_enabled else "disabled"
            self.cashflow_menu.entryconfig(
                self._cashflow_taxes_index,
                state=state,
            )

        self._apply_mode_to_results_button()

    def _rebuild_results_menu(self):
        if not hasattr(self, "results_menu"):
            return

        self.results_menu.delete(0, "end")

        is_advanced = (self.mode_var.get() == "Advanced")

        # Always available
        self.results_menu.add_command(
            label="Income Plots",
            command=lambda: self.run_simulation_from_gui(sim_type="income_sim")
        )

        if is_advanced:
            self.results_menu.add_command(
                label="Cash Flow Plots",
                command=lambda: self.run_simulation_from_gui(sim_type="cashflow_sim")
            )

        self.results_menu.add_command(
            label="Portfolio Plots",
            command=lambda: self.run_simulation_from_gui(sim_type="portfolio_sim")
        )

        self.results_menu.add_command(
            label="Simulation Summary",
            command=lambda: self.run_simulation_from_gui(sim_type="summary_sim")
        )

        if is_advanced:
            self.results_menu.add_separator()
            self.results_menu.add_command(
                label="Scenario Explorer",
                command=self.scenario_controller.start_or_focus
            )
            self.results_menu.add_command(
                label="Cumulative Operating Balance",
                command=lambda: self.run_simulation_from_gui(sim_type="operating_balance_sim")
            )


    def _apply_mode_to_results_button(self):
        if not hasattr(self, "results_button"):
            return

        legal_enabled = getattr(self, "legal_accepted", False)

        set_tk_button_soft_disabled(
            self.results_button,
            legal_enabled,
            self._show_results_menu,
            noop_command=noop
        )

        self._rebuild_results_menu()


    def _on_mode_changed(self):
        container = getattr(self, "edit_frame_container", None)
        if container is not None:
            for widget in container.winfo_children():
                widget.destroy()

        self._apply_mode_to_top_buttons()

        tutorial_controller = getattr(
            self,
            "guided_tutorial_controller",
            None,
        )

        if (
            tutorial_controller is not None
            and tutorial_controller.active
        ):
            tutorial_controller.refresh_current_step()
            return

        self.edit_main_home()


    def _on_second_person_changed(self):
        # one-way sync
        self._sync_tax_status_from_second_person()

        tutorial_controller = getattr(
            self,
            "guided_tutorial_controller",
            None,
        )

        if (
            tutorial_controller is not None
            and tutorial_controller.active
        ):
            tutorial_controller.refresh_current_step()
            return

        # rebuild the person editor (existing behavior)
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        self.edit_person_data()


    def _build_top_fields(self, parent):
        # --- BUTTON FRAME ---
        self.button_frame = ttk.Frame(parent)
        self.button_frame.grid(row=0, column=0, columnspan=3, sticky="w", pady=5)
        self.mode_var = tk.StringVar(value="Basic")


        # Store all buttons as instance variables

        self.file_button, self.file_menu, self._show_file_menu = create_dropdown_button(
            self.button_frame,
            text="File \u25BE",
            menu_labels_and_commands=[
                ("Load Examples", self.load_examples_from_json),
                ("Load Financial Data", self.load_values_from_json),
                ("Save Financial Data", self.save_values_to_json),
                ("Exit", self.root.destroy),
            ],
            row=0,
            column=0,
            padx=(0,10),
            pady=2,
        )

        self.home_button, self.home_menu, self._show_home_menu = create_dropdown_button(
            self.button_frame,
            text="Home \u25BE",
            menu_labels_and_commands=[
                ("Start", self.edit_main_home),
                ("Tutorials", self.edit_tutorial),
                ("Notes", self.edit_notes),
            ],
            row=0,
            column=1,
            padx=(0,15),
            pady=2,
        ) 

        self.cashflow_button, self.cashflow_menu, self._show_cashflow_menu = create_dropdown_button(
            self.button_frame,
            text="Cash Flow \u25BE",
            menu_labels_and_commands=[],  # empty
            row=0,
            column=2,
            padx=(25,10),
            pady=2,
        )

        self.cashflow_menu.add_command(
            label="Normal Income",
            command=self.edit_person_data
        )

        self.cashflow_menu.add_command(
            label="Special Income",
            command=self.edit_special_income
        )
        self._cashflow_special_income_index = self.cashflow_menu.index("end")

        self.cashflow_menu.add_command(
            label="Roth Contributions / Conversions",
            command=self.edit_roth
        )
        self._cashflow_roth_index = self.cashflow_menu.index("end")

        self.cashflow_menu.add_command(
            label="Expenses",
            command=self.edit_expenses
        )

        self.cashflow_menu.add_command(
            label="Taxes",
            command=self.edit_taxes
        )
        self._cashflow_taxes_index = self.cashflow_menu.index("end")

        self.balance_sheet_button, self.balance_sheet_menu, self._show_balance_sheet_menu = create_dropdown_button(
            self.button_frame,
            text="Balance Sheet \u25BE",
            menu_labels_and_commands=[],
            row=0,
            column=3,
            padx=(0,15),
            pady=2,
        )

        self.balance_sheet_menu.add_command(
            label="Portfolio",
            command=self.edit_portfolio_data
        )

        self.balance_sheet_menu.add_command(
            label="Real Estate",
            command=self.edit_real_estate
        )
        self._balance_sheet_real_estate_index = self.balance_sheet_menu.index("end")

        self.balance_sheet_menu.add_command(
            label="Derived Statistics",
            command=self.edit_derived_statistics
        )
        self._balance_sheet_derived_statistics_index = self.balance_sheet_menu.index("end")

        self.edit_retirement_button = create_top_button(
            self.button_frame,
            text="Retirement",
            command=self.edit_retirement_controls,
            grid_kwargs={"row": 0, "column": 4, "padx": (25,10), "pady": 2}
        )
        self._cmd_edit_retirement_controls = self.edit_retirement_controls

        self.simulation_button, self.simulation_menu, self._show_simulation_menu = create_dropdown_button(
            self.button_frame,
            text="Simulation \u25BE",
            menu_labels_and_commands=[
                ("Assumptions", self.edit_simulation_assumptions),
                ("Settings", self.edit_simulation_settings),
                ("Controls", self.edit_simulation_controls),
            ],
            row=0,
            column=5,
            padx=(0,15),
            pady=2,
        )

        self.results_button, self.results_menu, self._show_results_menu = create_dropdown_button(
            self.button_frame,
            text="Results \u25BE",
            menu_labels_and_commands=[],
            row=0,
            column=6,
            padx=(25,15),
            pady=2,
        )

        self.reports_button, self.reports_menu, self._show_reports_menu = create_dropdown_button(
            self.button_frame,
            text="Reports \u25BE",
            menu_labels_and_commands=[],
            row=0,
            column=7,
            padx=(0, 15),
            pady=2,
        )

        # --- MODE BUTTON WITH DROPDOWN (reliable tk.Menubutton wiring) ---
        self.button_frame.grid_columnconfigure(8, weight=1)
        
        # Create the menubutton (button look)
        self.mode_button = tk.Menubutton(
            self.button_frame,
            text="Mode \u25BE",   # small down triangle
            relief="raised",
            borderwidth=2,
            font=("Arial", 14),
            indicatoron=True,
            direction="below",
        )
        self.mode_button.grid(row=0, column=8, padx=(30, 10), pady=2, sticky="e")

        # Create the menu and attach it explicitly
        self.mode_menu = tk.Menu(self.mode_button, tearoff=0)

        self.mode_menu.add_radiobutton(
            label="Basic",
            variable=self.mode_var,
            value="Basic",
            command=self._on_mode_changed
        )
        self.mode_menu.add_radiobutton(
            label="Advanced",
            variable=self.mode_var,
            value="Advanced",
            command=self._on_mode_changed
        )

        self.mode_button["menu"] = self.mode_menu

        # --- EDIT FRAME CONTAINER ---
        self.edit_frame_container = ttk.Frame(parent)
        self.edit_frame_container.grid(row=1, column=0, columnspan=4, sticky="nsew", pady=(5,0))

        self._rebuild_results_menu()
        self._apply_mode_to_top_buttons()


    def _build_fields(self):
        top_frame = ttk.Frame(self.frame)
        top_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        self.top_frame = top_frame  # save as an instance variable


        # Make columns resize properly
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.columnconfigure(2, weight=1) 
        self.frame.columnconfigure(3, weight=1) 


        self._build_top_fields(top_frame)


    def edit_main_home(self):
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        home_frame = MainHomeFrame(
            self.edit_frame_container,
            title="Home",
            parent_gui=self  # important!
        )
        home_frame.pack(padx=10, pady=5, fill="x")
        self.home_frame = home_frame


    def edit_tutorial_blank(self):
        """
        Clear the main editor area for a tutorial instruction-only step.
        """
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()


    def start_basic_tutorial(self):
        """
        Start the Basic Tutorial.
        """
        self.guided_tutorial_controller.start(
            tutorial_title="Basic Tutorial",
            steps=build_basic_tutorial_steps(self),
        )


    def start_advanced_building_tutorial(self):
        """
        Start Advanced Tutorial 1: Building the Simulation.
        """
        self.guided_tutorial_controller.start(
            tutorial_title="Advanced Tutorial 1: Building the Simulation",
            steps=build_advanced_building_tutorial_steps(self),
        )


    def start_advanced_analysis_tutorial(self):
        """
        Start Advanced Tutorial 2: Analyzing Results.
        """
        self.guided_tutorial_controller.start(
            tutorial_title="Advanced Tutorial 2: Analyzing Results",
            steps=build_advanced_analysis_tutorial_steps(self),
        )


    def edit_tutorial(self):
        # Clear any existing editor frame
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        tutorial_frame = TutorialFrame(
            self.edit_frame_container,
            start_basic_tutorial_callback=self.start_basic_tutorial,
            start_advanced_building_tutorial_callback=(
                self.start_advanced_building_tutorial
            ),
            start_advanced_analysis_tutorial_callback=(
                self.start_advanced_analysis_tutorial
            ),
            title="Tutorials",
        )

        tutorial_frame.pack(padx=10, pady=5, fill="x")


    def edit_notes(self):
        # Clear any existing editor frame
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        notes_frame = NotesFrame(
            self.edit_frame_container,
            title="Notes"
        )
        notes_frame.pack(padx=10, pady=5, fill="x")


    def edit_person_data(self):
        # Remove previous edit frames
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        persons = {"husband": self.husband}

        if self.simulation_controls["enable_second_person"]:
            persons["wife"] = self.wife

        person_frame = NormalIncomeEditFrame(
            self.edit_frame_container,
            persons,
            simulation_controls=self.simulation_controls,
            refresh_callback=self._on_second_person_changed,
            title="Personal Data",
            mode=self.mode_var.get()
        )

        person_frame.pack(padx=10, pady=5, fill="x")


    def edit_special_income(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        special_income_frame = SpecialIncomeEditFrame(
            self.edit_frame_container,
            special_income_streams=self.special_income_streams,
            enable_second_person=self.simulation_controls.get("enable_second_person", False),
            title="Special Income"
        )

        special_income_frame.pack(padx=10, pady=5, fill="x")


    def edit_roth(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        roth_frame = RothEditFrame(
            self.edit_frame_container,
            roth_flows=self.roth_flows,
            enable_second_person=self.simulation_controls.get(
                "enable_second_person",
                False,
            ),
            title="Roth Contributions / Conversions",
        )

        roth_frame.pack(
            padx=10,
            pady=5,
            fill="x",
        )


    def edit_expenses(self):
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        expenses_frame = ExpensesEditFrame(
            self.edit_frame_container,
            expensesDict=self.expensesDict,
            title="Expenses"
        )
        expenses_frame.pack(padx=10, pady=5, fill="x")


    def edit_taxes(self):
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        control_vars = {
            "_controls_dict": self.simulation_controls
        }

        taxes_frame = TaxesEditFrame(
            self.edit_frame_container,
            control_vars=control_vars,
            title="Taxes"
        )
        taxes_frame.pack(padx=10, pady=5, fill="x")


    def edit_expenses_taxes(self):
        # Clear any existing editor frame
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        control_vars = {
            "_controls_dict": self.simulation_controls
        }

        self.expenses_taxes_editor_frame = ExpensesTaxesFrame(
            self.edit_frame_container,
            expensesDict=self.expensesDict,
            control_vars=control_vars,
            title="Expenses & Taxes",
            mode=self.mode_var.get()
        )

        # Use pack like your other editors for consistency
        self.expenses_taxes_editor_frame.pack(anchor="w", pady=(20, 10), fill="both", expand=True)
    
    
    def edit_portfolio_data(self):
        # Remove previous edit frames
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        husband_portfolio = self.husband_portfolio
        wife_portfolio = self.wife_portfolio if self.simulation_controls["enable_second_person"] else None

        portfolio_frame = PortfolioEditFrame(
            self.edit_frame_container,
            husband_portfolio=husband_portfolio,
            wife_portfolio=wife_portfolio,
            title="Portfolio Data",
            mode=self.mode_var.get()
        )
        portfolio_frame.pack(padx=10, pady=5, fill="x")


    def edit_real_estate(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        husband_portfolio = self.husband_portfolio
        wife_portfolio = self.wife_portfolio if self.simulation_controls["enable_second_person"] else None

        real_estate_frame = RealEstateEditFrame(
            self.edit_frame_container,
            husband_portfolio=husband_portfolio,
            wife_portfolio=wife_portfolio,
            title="Real Estate",
            mode=self.mode_var.get()
        )

        real_estate_frame.pack(padx=10, pady=5, fill="x")


    def edit_derived_statistics(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        husband_portfolio = self.husband_portfolio
        wife_portfolio = self.wife_portfolio if self.simulation_controls["enable_second_person"] else None

        derived_statistics_frame = DerivedStatisticsFrame(
            self.edit_frame_container,
            husband_portfolio=husband_portfolio,
            wife_portfolio=wife_portfolio,
            title="Derived Statistics",
            mode=self.mode_var.get()
        )

        derived_statistics_frame.pack(padx=10, pady=5, fill="x")


    # ------------------------
    # Build Retirement editor in edit_frame_container
    # ------------------------
    def edit_retirement_controls(self):
        if not self._advanced_only():
            return
        # existing code...        # Remove previous editor frame
        
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        control_vars = {"_controls_dict": self.simulation_controls}

        persons = {"husband": self.husband}
        if self.simulation_controls["enable_second_person"]:
            persons["wife"] = self.wife

        portfolio = {"husband": self.husband_portfolio}
        if self.simulation_controls["enable_second_person"]:
            portfolio["wife"] = self.wife_portfolio

        self.retirement_editor_frame = RetirementEditFrame(
            self.edit_frame_container,
            main_gui=self, 
            control_vars=control_vars,
            persons=persons,
            portfolio=portfolio,
            title="Retirement"
        )
        self.retirement_editor_frame.pack(anchor="w", pady=(20, 10))


    def edit_simulation_assumptions(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        historical_frame = HistoricalEditFrame(
            self.edit_frame_container,
            historical_data=self,
            title="Assumptions"
        )
        historical_frame.pack(padx=10, pady=5, fill="x")


    def edit_simulation_settings(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        sim_vars = {
            "_settings_dict": self.simulation_settings
        }

        simulation_frame = PortfolioSimulationEditFrame(
            self.edit_frame_container,
            sim_vars=sim_vars,
            title="Settings"
        )
        simulation_frame.pack(padx=10, pady=5, fill="x")
        

    def edit_simulation_controls(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        control_vars = {"_controls_dict": self.simulation_controls}

        self.simulation_controls_editor_frame = SimulationControlsEditFrame(
            self.edit_frame_container,
            control_vars=control_vars,
            title="Controls"
        )
        self.simulation_controls_editor_frame.pack(anchor="w", pady=(20, 10))


    def _rebuild_reports_menu(self):
        if not hasattr(self, "reports_menu"):
            return

        self.reports_menu.delete(0, "end")

        self.reports_menu.add_command(
            label="Executive Summary",
            command=self.edit_report_executive_summary
        )

        self.reports_menu.add_command(
            label="Year-by-Year Details",
            command=self.edit_report_year_by_year_details
        )

        self.reports_menu.add_command(
            label="Tax Report",
            command=self.edit_report_taxes
        )

        self.reports_menu.add_separator()

        self.reports_menu.add_command(
            label="Historical Window Risk Report",
            command=self.edit_report_historical_window_risk
        )

        self.reports_menu.add_command(
            label="Monte Carlo Risk Report",
            command=self.edit_report_monte_carlo_risk
        )
        

    def edit_report_executive_summary(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = ExecutiveSummaryReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["executive_summary"],
            parent_gui=self,
            title="Executive Summary"
        )
        frame.pack(padx=10, pady=5, fill="x")


    def edit_report_year_by_year_details(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = YearByYearDetailsReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["year_by_year_details"],
            parent_gui=self,
            title="Year-by-Year Details"
        )
        frame.pack(padx=10, pady=5, fill="x")


    def edit_report_taxes(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = TaxReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["tax_report"],
            parent_gui=self,
            title="Tax Report"
        )
        frame.pack(padx=10, pady=5, fill="x")


    def edit_report_historical_window_risk(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = HistoricalWindowRiskReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["historical_window_risk"],
            parent_gui=self,
            title="Historical Window Risk Report"
        )
        frame.pack(padx=10, pady=5, fill="x")


    def edit_report_monte_carlo_risk(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = MonteCarloRiskReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["monte_carlo_risk"],
            parent_gui=self,
            title="Monte Carlo Risk Report"
        )
        frame.pack(padx=10, pady=5, fill="x")

    def _apply_mode_to_reports_button(self):
        if not hasattr(self, "reports_button"):
            return

        legal_enabled = getattr(self, "legal_accepted", False)
        advanced_enabled = self._advanced_only() and legal_enabled

        set_tk_button_soft_disabled(
            self.reports_button,
            advanced_enabled,
            self._show_reports_menu,
            noop_command=noop
        )

        self._rebuild_reports_menu()


    def _build_run_button(self):
        style = ttk.Style()
        style.configure("Big.TButton", font=("Arial", 14, "bold"), padding=(10, 10))
        style.configure("BigFaded.TButton", font=("Arial", 14, "bold"), padding=(10, 10))
        style.map(
            "BigFaded.TButton",
            foreground=[
                ("disabled", "gray60"),
                ("!disabled", "black"),
            ],
        )