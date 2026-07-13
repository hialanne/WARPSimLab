# simulationObject.py

import numpy as np
from src.warpsimlab.utils.constants import EQUITY_MEAN, BOND_MEAN, CASH_MEAN, EQUITY_STD, BOND_STD, CASH_STD

class Simulation:
    def __init__(self, start_year, years_to_simulate, inflation_rate, num_sims, 
            fund_expense, use_fund_expenses, plot_mode, subplot_mode, 
            include_rmd, calculate_income_taxes, calculate_payroll_taxes, tax_filing_status, calculate_state_taxes, state_of_residence,
            second_person_enabled, 
            eq_mean, bd_mean, cs_mean,
            eq_std, bd_std, cs_std,
            husband_portfolio=None,
            wife_portfolio=None,        
            post_tax_equity_dividend_yield=None,
            post_tax_bond_interest_yield=None,
            post_tax_cash_interest_yield=None,
            sim_type=False,
            report_options=None,
            sim_initial_allocation_mode="none",
            monte_carlo_plot_style="fill",
            use_correlated_returns=True,
            monte_carlo_mode="pathBasedAnnualSampling",
            historical_asset_returns_file="us_asset_returns_1876_2025.csv",
            historical_inflation_file="us_inflation_1876_2025_real.csv",
            historical_window_mode="rolling_overlapping_all",
            disable_sequence_risk_for_historical=True,
            show_simulated_shortfall_rate=True,

            custom_stock=0.0, custom_bonds=0.0, custom_cash=100.0,
            annotate_plots=False,
            constant_y_plots=False,
            rebalance_every_year=False,
            include_realestate=False,
            re_mean=3.0, re_std=5.0,
            output_csv="None",
            csv_output_dir=None,

            retirement_withdraw_mode="None",
            retirement_withdraw_pct=4.0,
            retirement_withdraw_dollars=0,
            always_use_expense_mode=True,

            sequence_risk_enabled=False,
            sequence_risk_timing="None",
            sequence_risk_start_year_offset=0,
            sequence_risk_length="Medium",
            sequence_risk_depth="Moderate",

            scenario_expense_multiplier=1.0,            
            overlay_tax_impacts=False,
            overlay_fund_expense_impacts=False,
            overlay_household_expenses=False,
            overlay_profit_loss=True,
            overlay_retirement_age=False,
            use_snapshot_annotations=False,
            user_annotation_strings=None,
            scenario_explorer_annotations=None,
            special_income_streams=None,
            root=None
    ): 


        self.root = root
        self.start_year = start_year
        self.years_to_simulate = years_to_simulate
        self.inflation_rate = inflation_rate
        self.num_sims = num_sims
        self.fund_expense = fund_expense
        self.use_fund_expenses = use_fund_expenses
        self.output_csv = output_csv
        self.csv_output_dir = csv_output_dir
        
        self.plot_mode = plot_mode  # "raw" or "real"
        self.subplot_mode = subplot_mode # Currently controls all subplots, including logic for monte carlo.  Should be split.
        #self.monte_carlo = monte_carlo # This variable, not currently used, should be what controls the monte carlo simulation.

        self.include_rmd = include_rmd
        self.calculate_income_taxes = calculate_income_taxes
        self.calculate_payroll_taxes = calculate_payroll_taxes
        self.tax_filing_status = tax_filing_status
        self.calculate_state_taxes = calculate_state_taxes
        self.state_of_residence = state_of_residence

        self.second_person_enabled = second_person_enabled
        self.husband_portfolio = husband_portfolio
        self.wife_portfolio = wife_portfolio

        if special_income_streams is None:
            special_income_streams = []

        self.special_income_streams = [
            dict(stream)
            for stream in special_income_streams
        ]

        # Controls which sim we run.  Current is plots such as portfolio, income and summary,
        #   and reports such as execuative summary, year by year and assumptions.
        self.sim_type = sim_type

        if report_options is None:
            report_options = {}

        self.report_options = report_options

        self.annotate_plots = annotate_plots 
        self.constant_y_plots = constant_y_plots 
        self.rebalance_every_year = rebalance_every_year 
        self.include_realestate = include_realestate 

        self.retirement_withdraw_mode = retirement_withdraw_mode
        self.retirement_withdraw_pct = retirement_withdraw_pct
        self.retirement_withdraw_dollars = retirement_withdraw_dollars
        self.always_use_expense_mode = always_use_expense_mode

        self.sequence_risk_enabled = sequence_risk_enabled
        self.sequence_risk_timing = sequence_risk_timing
        self.sequence_risk_start_year_offset = sequence_risk_start_year_offset
        self.sequence_risk_length = sequence_risk_length
        self.sequence_risk_depth = sequence_risk_depth

        valid_sequence_risk_timing = {
            "None",
            "Early downturn",
            "Mid-retirement downturn",
            "Late downturn",
            "Custom",
        }
        if self.sequence_risk_timing not in valid_sequence_risk_timing:
            raise ValueError(
                f"Unsupported sequence_risk_timing: {self.sequence_risk_timing}"
            )

        valid_sequence_risk_length = {"Short", "Medium", "Long"}
        if self.sequence_risk_length not in valid_sequence_risk_length:
            raise ValueError(
                f"Unsupported sequence_risk_length: {self.sequence_risk_length}"
            )

        valid_sequence_risk_depth = {"Mild", "Moderate", "Severe"}
        if self.sequence_risk_depth not in valid_sequence_risk_depth:
            raise ValueError(
                f"Unsupported sequence_risk_depth: {self.sequence_risk_depth}"
            )

        self.sequence_risk_start_year_offset = max(
            0,
            int(self.sequence_risk_start_year_offset),
        )

        self.scenario_expense_multiplier = scenario_expense_multiplier
        self.overlay_tax_impacts = overlay_tax_impacts
        self.overlay_fund_expense_impacts = overlay_fund_expense_impacts
        self.overlay_household_expenses = overlay_household_expenses
        self.overlay_profit_loss = overlay_profit_loss
        self.overlay_retirement_age = overlay_retirement_age

        self.use_snapshot_annotations = use_snapshot_annotations

        if user_annotation_strings is None:
            user_annotation_strings = []
        if scenario_explorer_annotations is None:
            scenario_explorer_annotations = []

        self.user_annotation_strings = user_annotation_strings
        self.scenario_explorer_annotations = scenario_explorer_annotations

        self.sim_initial_allocation_mode = sim_initial_allocation_mode
        self.monte_carlo_plot_style = monte_carlo_plot_style
        self.use_correlated_returns = use_correlated_returns
        self.monte_carlo_mode = monte_carlo_mode
        self.historical_asset_returns_file = historical_asset_returns_file
        self.historical_inflation_file = historical_inflation_file
        self.historical_window_mode = historical_window_mode
        self.disable_sequence_risk_for_historical = disable_sequence_risk_for_historical
        self.show_simulated_shortfall_rate = show_simulated_shortfall_rate


        
        # Asset order for correlation/covariance logic:
        # [equity, bonds, cash, real_estate]
        #
        # This is intentionally hardcoded for the educational simulator.
        # Keep this aligned with run_sim_core.generate_market_path().

        self.return_asset_order = ("eq", "bd", "cs", "re")

        self.return_correlation_matrix = np.array([
            [1.00, -0.20, 0.00, 0.55],
            [-0.20, 1.00, 0.20, 0.10],
            [0.00, 0.20, 1.00, 0.05],
            [0.55, 0.10, 0.05, 1.00],
        ], dtype=float)

        valid_monte_carlo_plot_styles = {
            "fill",
            "line",
            "all_lines",
        }
        if self.monte_carlo_plot_style not in valid_monte_carlo_plot_styles:
            raise ValueError(
                f"Unsupported monte_carlo_plot_style: {self.monte_carlo_plot_style}. "
                f"Valid values are: {sorted(valid_monte_carlo_plot_styles)}"
            )

        valid_monte_carlo_modes = {
            "pathBasedAnnualSampling",
            "rollingHistoricalWindows",
        }
        if self.monte_carlo_mode not in valid_monte_carlo_modes:
            raise ValueError(
                f"Unsupported monte_carlo_mode: {self.monte_carlo_mode}. "
                f"Valid values are: {sorted(valid_monte_carlo_modes)}"
            )

        valid_historical_window_modes = {
            "rolling_overlapping_all",
        }
        if self.historical_window_mode not in valid_historical_window_modes:
            raise ValueError(
                f"Unsupported historical_window_mode: {self.historical_window_mode}. "
                f"Valid values are: {sorted(valid_historical_window_modes)}"
            )

        
        # --- Precomputed Monte Carlo sampling data ---
        # Built once per simulation run to avoid repeated covariance setup
        # in monteCarloEngine.generate_market_path().
        self._mc_means = None
        self._mc_std_devs = None
        self._mc_cov_matrix = None
        self._mc_cholesky = None
        # --- Precomputed historical rolling-window data ---
        self._hist_years = None
        self._hist_eq = None
        self._hist_bd = None
        self._hist_cs = None
        self._hist_re = None
        self._hist_inflation = None
        self._active_historical_sim_index = None
        self._hist_window_start_indices = None
        self._hist_num_windows = 0

        # --- Household allocation targets (used by "maintain-current-allocation") ---
        # These are fractions (0.0 - 1.0) and should sum to 1.0 when set.
        # They are computed once at the start of the simulation run.
        self.household_eq_target = None
        self.household_bd_target = None
        self.household_cs_target = None

        self.custom_stock = custom_stock
        self.custom_bonds = custom_bonds
        self.custom_cash = custom_cash

        self.eq_mean = eq_mean
        self.bd_mean = bd_mean
        self.cs_mean = cs_mean
        self.re_mean = re_mean

        # --- Taxable account income assumptions ---
        if post_tax_equity_dividend_yield is None:
            self.post_tax_equity_dividend_yield = 0.015 # Approximate average of S&P500 over the last 25 years.
        else:
            self.post_tax_equity_dividend_yield = post_tax_equity_dividend_yield

        if post_tax_bond_interest_yield is None:
            bond_price_return_assumption = 0.0
            self.post_tax_bond_interest_yield = max(0.0, self.bd_mean - bond_price_return_assumption)
        else:
            self.post_tax_bond_interest_yield = post_tax_bond_interest_yield

        if post_tax_cash_interest_yield is None:
            self.post_tax_cash_interest_yield = cs_mean
        else:
            self.post_tax_cash_interest_yield = post_tax_cash_interest_yield

        self.eq_std = eq_std
        self.bd_std = bd_std
        self.cs_std = cs_std
        self.re_std = re_std



