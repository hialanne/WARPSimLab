# gui_init.py

#
# Version string is defined after imports.
#

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
from src.warpsimlab.gui.scenario.gui_scenarioSnapshots import *
from src.warpsimlab.gui.gui_io import *
from src.warpsimlab.gui.gui_io import PortfolioSimulatorGUI_IOMixin
from src.warpsimlab.gui.scenario.gui_scenarioController import ScenarioController
from src.warpsimlab.gui.gui_navigation import PortfolioSimulatorGUI_NavigationMixin
from src.warpsimlab.gui.gui_editors import PortfolioSimulatorGUI_EditorsMixin
from src.warpsimlab.gui.reports.gui_reports import PortfolioSimulatorGUI_ReportsMixin
from .gui_notes import NotesFrame
from src.warpsimlab.gui.gui_expenses import ExpensesEditFrame
from src.warpsimlab.gui.gui_taxes import TaxesEditFrame
from src.warpsimlab.gui.gui_roth import RothEditFrame
from src.warpsimlab.gui.gui_realEstate import RealEstateEditFrame
from src.warpsimlab.gui.gui_derivedStatistics import DerivedStatisticsFrame
from src.warpsimlab.gui.gui_guidedtutorial import GuidedTutorialController
from src.warpsimlab.gui.gui_tutorial_definitions import (
    build_basic_tutorial_steps,
    build_advanced_building_tutorial_steps,
    build_advanced_analysis_tutorial_steps,
)

from src.warpsimlab.gui.gui_settings import load_display_settings, save_display_settings
from src.warpsimlab.gui.gui_display import PortfolioSimulatorGUI_DisplayMixin


WARPSIMLAB_VERSION = "4.2.2"
WARPSIMLAB_TITLE = f"WARPSimLab version {WARPSIMLAB_VERSION}"

SCREEN_DEBUG = False


class PortfolioSimulatorGUI(
    PortfolioSimulatorGUI_DisplayMixin, PortfolioSimulatorGUI_NavigationMixin,
    PortfolioSimulatorGUI_EditorsMixin, PortfolioSimulatorGUI_ReportsMixin,
    PortfolioSimulatorGUI_RunMixin, PortfolioSimulatorGUI_IOMixin
):
    def __init__(self, root):
        self.root = root
        self.legal_accepted = False

        root.title(WARPSIMLAB_TITLE)

        # Diagnostic code to replicate a Mac's dark mode.
        # self._apply_dark_mode_diagnostic_theme()

        self.display_settings = load_display_settings()
        self._apply_main_window_startup_settings()

        # Diagnostic prints for dialog and subdialog diagnostics. Comment out in production.
        if SCREEN_DEBUG:
            self._print_display_diagnostics()

        ttk.Label(root, text=WARPSIMLAB_TITLE, font=("Arial", 16)).pack(pady=10)

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
            annual_hsa_contribution=DEFAULT_HUSBAND_HSA_CONTRIB,
            annual_hsa_employer_contribution=DEFAULT_HUSBAND_HSA_EMPLOYER_CONTRIB,
            pension_inflation_adjustment_pct=DEFAULT_HUSBAND_PENSION_INFLATION_ADJ,
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
            annual_hsa_contribution=DEFAULT_WIFE_HSA_CONTRIB,
            annual_hsa_employer_contribution=DEFAULT_WIFE_HSA_EMPLOYER_CONTRIB,
            pension_inflation_adjustment_pct=DEFAULT_WIFE_PENSION_INFLATION_ADJ,
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
            real_estate=DEFAULT_REAL_ESTATE_H,
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
            real_estate=DEFAULT_REAL_ESTATE_W,
        )

        self._init_vars()
        self._build_fields()

        # Guided tutorial controller
        self.guided_tutorial_controller = GuidedTutorialController(self)

        self.scenario_controller = ScenarioController(self)

        # Rebuild now that the Scenario Explorer controller exists.
        self._rebuild_results_menu()

        self.root.protocol("WM_DELETE_WINDOW", self._close_application)

        self._build_run_button()
        self.edit_main_home()

        # This should be commented out in production.
        # self._print_content_geometry_diagnostics()


    def _close_application(self):
        """
        Save remembered display layouts and close WARPSimLab.
        """
        scenario_controller = getattr(self, "scenario_controller", None)

        if scenario_controller is not None and scenario_controller.session_active:
            scenario_controller.capture_current_layout()

        self._save_main_window_geometry()
        save_display_settings(self.display_settings)
        self.root.destroy()


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
            "years_to_simulate": DEFAULT_YEARS,
            "num_sims": DEFAULT_SIMULATIONS,
            "fund_expense": DEFAULT_FUND_EXPENSE,
            "use_fund_expenses": True,
            "initial_allocation_mode": "maintain-current-allocation",
            "custom_stock": 0.0,
            "custom_bonds": 0.0,
            "custom_cash": 100.0,
        }

        default_csv_dir = os.path.join(os.path.expanduser("~"), "Desktop", "WARPSimLab")

        self.simulation_controls = {
            "enable_second_person": bool(DEFAULT_ENABLE_SECOND_PERSON),
            "include_realestate": False,
            "plot_mode": "real",
            "subplot_mode": "fill",
            "monte_carlo_plot_style": "fill",
            "use_correlated_returns": True,
            # "monte_carlo_mode": "pathBasedAnnualSampling",
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
            "state_of_residence": DEFAULT_STATE_OF_RESIDENCE,
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
            "user_annotation_strings": [],
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
                "operating_balance_visuals": {"include_cumulative_operating_balance": True},
                "include_assumptions_appendix": True,
                "output_format": "HTML",
                "open_report_in_browser": False,
            },
            "year_by_year_details": {
                "generate_html": True,
                "generate_csv": True,
                "table_detail": "Compact",
                "insert_5_year_breaks": True,
                "open_report_in_browser": False,
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
                    "open_report_in_browser": False,
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
                    "open_report_in_browser": False,
                },
            },
            "tax_report": {
                "output": {
                    "generate_html": True,
                    "generate_csv": False,
                    "open_report_in_browser": False,
                },
                "sections": {
                    "include_roth_analysis": True,
                    "include_hsa_analysis": True,
                    "include_rmd_analysis": True,
                    "include_educational_commentary": True,
                },
            },
            "spending_comparison": {
                "spending_percentages": [70, 80, 90, 100, 110, 120, 130],
                "output": {
                    "generate_html": True,
                    "open_report_in_browser": False,
                },
            },
            "asset_allocation_comparison": {
                "equity_percentages": [0, 20, 40, 60, 80, 100],
                "output": {
                    "generate_html": True,
                    "open_report_in_browser": False,
                },
            },
            "retirement_ss_comparison": {
                "retirement_ages": [62, 64, 66, 68, 70],
                "social_security_ages": [62, 64, 66, 68, 70],
                "output": {
                    "generate_html": True,
                    "open_report_in_browser": False,
                },
            },
        }

        # Dynamic expenses
        self.expensesDict = DynamicExpenses()
        for expense in DEFAULT_EXPENSE_ENTRIES:
            self.expensesDict.add_expense(
                expense["start_year"], expense["cost"], expense["end_year"], expense["comment"],
                expense.get("is_hsa_eligible", False)
            )

        # Special income streams
        self.special_income_streams = [dict(stream) for stream in DEFAULT_SPECIAL_INCOME_STREAMS]

        # Scheduled Roth contributions and conversions
        self.roth_flows = [dict(flow) for flow in DEFAULT_ROTH_FLOWS]

