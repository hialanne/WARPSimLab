from copy import deepcopy
from dataclasses import dataclass, field

import numpy as np


@dataclass(kw_only=True)
class SimulationConfig:
    # Required input fields: preserve existing constructor's required arguments.
    start_year: int
    years_to_simulate: int
    inflation_rate: float
    num_sims: int
    fund_expense: float
    use_fund_expenses: bool
    inflation_mode: str
    results_mode: str
    include_rmd: bool
    calculate_income_taxes: bool
    calculate_payroll_taxes: bool
    tax_filing_status: str
    calculate_state_taxes: bool
    state_of_residence: str
    second_person_enabled: bool
    eq_mean: float
    bd_mean: float
    cs_mean: float
    eq_std: float
    bd_std: float
    cs_std: float

    # Optional investment and market assumptions.
    post_tax_equity_dividend_yield: float | None = None
    post_tax_bond_interest_yield: float | None = None
    post_tax_cash_interest_yield: float | None = None
    sim_initial_allocation_mode: str = "original-allocation"
    use_correlated_returns: bool = True
    custom_stock: float = 0.0
    custom_bonds: float = 0.0
    custom_cash: float = 1.0
    rebalance_every_year: bool = False
    include_realestate: bool = False
    re_mean: float = 3.0
    re_std: float = 5.0

    # Simulation selection and historical market settings.
    sim_type: str | bool = False
    risk_analysis_plot_style: str = "fill"
    risk_analysis_mode: str = "monte_carlo"
    historical_asset_returns_file: str = "us_asset_returns_1876_2025.csv"
    historical_inflation_file: str = "us_inflation_1876_2025_real.csv"
    historical_window_mode: str = "rolling_overlapping_all"
    historical_window_start_year: int | None = None
    historical_window_stop_year: int | None = None
    historical_window_stride: int = 1

    # Tax, household and inflation settings.
    irmaa_enabled: bool = False
    historical_magi: dict | None = None
    special_income_streams: list | None = None
    roth_flows: list | None = None
    inflation_delta: float = 0.0

    # Retirement, withdrawals, and sequence-risk assumptions.
    retirement_withdraw_mode: str = "Off"
    retirement_withdraw_pct: float = 4.0
    retirement_withdraw_dollars: float = 0
    always_use_expense_mode: bool = True
    sequence_risk_enabled: bool = False
    sequence_risk_timing: str = "None"
    sequence_risk_start_year_offset: int = 0
    sequence_risk_length: str = "Medium"
    sequence_risk_depth: str = "Moderate"
    qcd_settings: dict | None = None

    # Scenario configuration and overlays.
    scenario_expense_multiplier: float = 1.0
    overlay_tax_impacts: bool = False
    overlay_fund_expense_impacts: bool = False
    overlay_household_expenses: bool = False
    overlay_profit_loss: bool = True
    overlay_retirement_age: bool = False
    use_snapshot_annotations: bool = False
    user_annotation_strings: list | None = None
    scenario_explorer_annotations: list | None = None

    # Presentation, output, and metadata.
    report_options: dict | None = None
    show_simulated_shortfall_rate: bool = True
    calculate_simulated_shortfall_rate: bool | None = None
    annotate_plots: bool = False
    constant_y_plots: bool = False
    output_csv: str = "None"
    csv_output_dir: str | None = None
    warpsimlab_version: str = "Unknown"
    loaded_data_file: str | None = None

    # Fixed correlation inputs (the covariance / Cholesky are run state).
    return_asset_order: tuple[str, ...] = ("eq", "bd", "cs", "re")
    return_correlation_matrix: np.ndarray = field(default_factory=lambda: np.array([
        [1.00, -0.20, 0.00, 0.55],
        [-0.20, 1.00, 0.20, 0.10],
        [0.00, 0.20, 1.00, 0.05],
        [0.55, 0.10, 0.05, 1.00],
    ], dtype=float))

    def __post_init__(self):
        if self.sim_initial_allocation_mode in (
            "none", "dont-rebalance", "maintain-current-allocation"
        ):
            self.sim_initial_allocation_mode = "original-allocation"

        if self.post_tax_equity_dividend_yield is None:
            self.post_tax_equity_dividend_yield = 0.015

        if self.post_tax_bond_interest_yield is None:
            self.post_tax_bond_interest_yield = max(0.0, self.bd_mean)

        if self.post_tax_cash_interest_yield is None:
            self.post_tax_cash_interest_yield = self.cs_mean

        if self.calculate_simulated_shortfall_rate is None:
            self.calculate_simulated_shortfall_rate = self.show_simulated_shortfall_rate

        if self.historical_magi is None:
            self.historical_magi = {"two_years_prior": None, "one_year_prior": None}
        else:
            self.historical_magi = deepcopy(self.historical_magi)

        if self.special_income_streams is None:
            self.special_income_streams = []
        else:
            self.special_income_streams = deepcopy(self.special_income_streams)

        if self.roth_flows is None:
            self.roth_flows = []
        else:
            self.roth_flows = deepcopy(self.roth_flows)

        if self.qcd_settings is None:
            self.qcd_settings = {
                "husband": {
                    "enabled": False, "mode": "Fixed Amount", "amount": 0.0,
                    "percent": 0.0, "start_age": 70.5, "end_age": None,
                },
                "wife": {
                    "enabled": False, "mode": "Fixed Amount", "amount": 0.0,
                    "percent": 0.0, "start_age": 70.5, "end_age": None,
                },
            }
        else:
            self.qcd_settings = deepcopy(self.qcd_settings)

        if self.report_options is None:
            self.report_options = {}
        else:
            self.report_options = deepcopy(self.report_options)

        if self.user_annotation_strings is None:
            self.user_annotation_strings = []
        else:
            self.user_annotation_strings = deepcopy(self.user_annotation_strings)

        if self.scenario_explorer_annotations is None:
            self.scenario_explorer_annotations = []
        else:
            self.scenario_explorer_annotations = deepcopy(self.scenario_explorer_annotations)

        self.return_correlation_matrix = self.return_correlation_matrix.copy()


@dataclass
class RunContext:
    # Monte Carlo preparation and RNG.
    mc_means: np.ndarray | None = None
    mc_std_devs: np.ndarray | None = None
    mc_cov_matrix: np.ndarray | None = None
    mc_cholesky: np.ndarray | None = None
    mc_rng: np.random.Generator | None = None
    mc_seed: int | None = None

    # Loaded market history and filtered window map.
    hist_years: np.ndarray | None = None
    hist_eq: np.ndarray | None = None
    hist_bd: np.ndarray | None = None
    hist_cs: np.ndarray | None = None
    hist_re: np.ndarray | None = None
    hist_inflation: np.ndarray | None = None
    hist_window_start_indices: np.ndarray | None = None
    hist_num_windows: int = 0

    # Normalized execution assumptions, distinct from config inputs.
    post_tax_equity_dividend_yield_normalized: float | None = None
    post_tax_bond_interest_yield_normalized: float | None = None
    post_tax_cash_interest_yield_normalized: float | None = None

    # Path-independent tax and Medicare preparation.
    tax_2026_anchor_factor: float | None = None
    state_tax_enabled: bool | None = None
    state_tax_type: str | None = None
    state_tax_rate: float | None = None
    medicare_2026_anchor_factor: float | None = None


@dataclass
class PathContext:
    # Window selected for this path before initializing inflation caches.
    active_historical_sim_index: int | None = None

    # Path-specific inflation and pension preparation.
    income_inflation_factors: list | np.ndarray | None = None
    expense_inflation_factors: list | np.ndarray | None = None
    inflation_factors: list | None = None
    husband_pension_factors: list | np.ndarray | None = None
    wife_pension_factors: list | np.ndarray | None = None
    medicare_inflation_factors: list | None = None

    # Path-specific tax and Roth state.
    tax_year_cache: list = field(default_factory=list)
    roth_inflation_factor_cache: dict = field(default_factory=dict)
    roth_scheduled_flows: list = field(default_factory=list)

    # Lazily captured retirement withdrawal state.
    ret_withdraw_base_dollars: float | None = None


@dataclass
class SimData:
    config: SimulationConfig
    run: RunContext
    path: PathContext
