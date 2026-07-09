# tests/helpers_validation.py

from types import SimpleNamespace

import numpy as np

from src.warpsimlab.sim.simulationObject import Simulation
from src.warpsimlab.sim.engines import monteCarloEngine


ASSET_ORDER = ("eq", "bd", "cs", "re")


def make_sim_config(**overrides):
    """
    Build a Simulation config with decimal return assumptions.
    Example:
      0.07 == 7%
      0.15 == 15% std dev
    """
    cfg = Simulation(
        start_year=2025,
        years_to_simulate=30,
        inflation_rate=0.02,
        num_sims=1000,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode="raw",
        subplot_mode="monte_carlo",
        include_rmd=False,
        calculate_income_taxes=False,
        calculate_payroll_taxes=False,
        tax_filing_status="married_filing_jointly",
        calculate_state_taxes=False,
        state_of_residence="CA",
        second_person_enabled=False,
        eq_mean=0.07,
        bd_mean=0.03,
        cs_mean=0.02,
        eq_std=0.15,
        bd_std=0.06,
        cs_std=0.01,
        sim_type="portfolio_sim",
        sim_rebalance="none",
        custom_stock=60.0,
        custom_bonds=30.0,
        custom_cash=10.0,
        annotate_plots=False,
        constant_y_plots=False,
        rebalance_every_year=False,
        include_realestate=True,
        re_mean=0.05,
        re_std=0.12,
        output_csv="None",
        csv_output_dir=None,
        retirement_withdraw_mode="None",
        retirement_withdraw_pct=0.04,
        retirement_withdraw_dollars=0,
        always_use_expense_mode=True,
        scenario_expense_multiplier=1.0,
        overlay_tax_impacts=False,
        overlay_fund_expense_impacts=False,
        overlay_household_expenses=False,
        overlay_profit_loss=False,
        overlay_retirement_age=False,
        use_snapshot_annotations=False,
        user_annotation_strings=[],
        root=None,
    )

    cfg.monte_carlo_mode = "pathBasedAnnualSampling"
    cfg.monte_carlo_plot_style = "fill"
    cfg.use_correlated_returns = True

    for key, value in overrides.items():
        setattr(cfg, key, value)

    return cfg


def target_means_vector(sim_config):
    return np.array(
        [
            sim_config.eq_mean,
            sim_config.bd_mean,
            sim_config.cs_mean,
            sim_config.re_mean,
        ],
        dtype=float,
    )


def target_stds_vector(sim_config):
    return np.array(
        [
            sim_config.eq_std,
            sim_config.bd_std,
            sim_config.cs_std,
            sim_config.re_std,
        ],
        dtype=float,
    )


def target_corr_matrix(sim_config):
    use_correlated = (
        sim_config.monte_carlo_mode == "pathBasedAnnualSampling"
        and bool(getattr(sim_config, "use_correlated_returns", True))
    )
    if use_correlated:
        return np.asarray(sim_config.return_correlation_matrix, dtype=float)
    return np.eye(4, dtype=float)


def sample_many_return_vectors(sim_config, sample_size, seed=12345):
    """
    Return shape: (sample_size, 4)
    Asset order: [equity, bonds, cash, real_estate]
    """
    np.random.seed(int(seed))
    draws = np.zeros((sample_size, 4), dtype=float)

    if sim_config.monte_carlo_mode == "pathBasedAnnualSampling":
        for i in range(sample_size):
            path = monteCarloEngine.generate_market_path(sim_config, years_to_simulate=1)
            draws[i, 0] = path["eq"][1]
            draws[i, 1] = path["bd"][1]
            draws[i, 2] = path["cs"][1]
            draws[i, 3] = path["re"][1]
        return draws

    if sim_config.monte_carlo_mode == "independentAnnualSampling":
        for i in range(sample_size):
            year_returns = monteCarloEngine.sample_independent_annual_returns(sim_config)
            draws[i, 0] = year_returns["eq"]
            draws[i, 1] = year_returns["bd"]
            draws[i, 2] = year_returns["cs"]
            draws[i, 3] = year_returns["re"]
        return draws

    raise ValueError(f"Unsupported monte_carlo_mode: {sim_config.monte_carlo_mode}")


def empirical_stats(draws):
    return {
        "mean": np.mean(draws, axis=0),
        "std": np.std(draws, axis=0, ddof=1),
        "corr": np.corrcoef(draws, rowvar=False),
    }


def assert_sampler_matches_targets(
    sim_config,
    draws,
    *,
    mean_atol=0.003,
    std_atol=0.003,
    corr_atol=0.035,
):
    stats = empirical_stats(draws)

    expected_mean = target_means_vector(sim_config)
    expected_std = target_stds_vector(sim_config)
    expected_corr = target_corr_matrix(sim_config)

    np.testing.assert_allclose(stats["mean"], expected_mean, atol=mean_atol, rtol=0.0)
    np.testing.assert_allclose(stats["std"], expected_std, atol=std_atol, rtol=0.0)
    np.testing.assert_allclose(stats["corr"], expected_corr, atol=corr_atol, rtol=0.0)


def extract_median_series(percentiles):
    """
    Adapt this helper if your compute_portfolio_statistics() output uses
    a different structure.
    """
    if isinstance(percentiles, dict):
        for key in ("median", "p50", 50, "50"):
            if key in percentiles:
                return np.asarray(percentiles[key], dtype=float)

    for attr in ("median", "p50"):
        if hasattr(percentiles, attr):
            return np.asarray(getattr(percentiles, attr), dtype=float)

    if hasattr(percentiles, "__getitem__"):
        try:
            return np.asarray(percentiles[50], dtype=float)
        except Exception:
            pass
        try:
            return np.asarray(percentiles["50"], dtype=float)
        except Exception:
            pass

    arr = np.asarray(percentiles, dtype=float)
    if arr.ndim == 2 and arr.shape[0] % 2 == 1:
        return arr[arr.shape[0] // 2]

    raise AssertionError(
        "Could not extract median series from percentiles. "
        "Update extract_median_series() to match your percentiles structure."
    )


def assert_all_paths_identical(paths, *, atol=1e-12):
    arr = np.asarray(paths, dtype=float)
    assert arr.ndim == 2, f"Expected 2D array, got shape {arr.shape}"

    for i in range(1, arr.shape[0]):
        np.testing.assert_allclose(arr[i], arr[0], atol=atol, rtol=0.0)


def build_synthetic_core(total_assets):
    total_assets = np.asarray(total_assets, dtype=float)
    num_sims, width = total_assets.shape
    zeros = np.zeros_like(total_assets)

    breakdown_keys = [
        "work",
        "pension",
        "annuity",
        "ss",
        "rmd",
        "withdrawal",
        "bond_interest",
        "cash_interest",
        "qualified_dividends",
        "special_income",
    ]

    return {
        "year": np.tile(np.arange(width, dtype=float), (num_sims, 1)),
        "total_assets": total_assets,
        "pre_tax_assets": zeros.copy(),
        "post_tax_assets": zeros.copy(),
        "roth_assets": zeros.copy(),
        "hsa_assets": zeros.copy(),
        "roth_withdrawals": zeros.copy(),
        "hsa_withdrawals": zeros.copy(),
        "cash": zeros.copy(),
        "bonds": zeros.copy(),
        "real_estate": zeros.copy(),
        "gross_income": zeros.copy(),
        "net_income": zeros.copy(),
        "net_profit": zeros.copy(),
        "taxes": zeros.copy(),
        "tax_bracket": zeros.copy(),
        "payroll_tax": zeros.copy(),
        "social_security_payroll_tax": zeros.copy(),
        "medicare_tax": zeros.copy(),
        "additional_medicare_tax": zeros.copy(),
        "expense_amt": zeros.copy(),
        "ira_401k": zeros.copy(),
        "fund_expenses": zeros.copy(),
        "bond_interest": zeros.copy(),
        "cash_interest": zeros.copy(),
        "qualified_dividends": zeros.copy(),
        "federal_ordinary_tax": zeros.copy(),
        "federal_qualified_dividend_tax": zeros.copy(),
        "state_income_tax": zeros.copy(),
        "emergency_pre_tax_used": zeros.copy(),
        "final_tax_delta": zeros.copy(),
        "final_tax_delta_deducted": zeros.copy(),
        "final_tax_delta_uncovered": zeros.copy(),
        "net_income_husband": zeros.copy(),
        "net_income_wife": zeros.copy(),
        "breakdown_by_class": {k: zeros.copy() for k in breakdown_keys},
    }


def make_dummy_people():
    husband = SimpleNamespace(
        age=40,
        retire_age=100,
        income=0.0,
        ss=0.0,
        ss_age=99,
        pension=0.0,
        pension_age=99,
        annuity=0.0,
        annuity_age=99,
        annual_401k_contribution=0.0,
        annual_employer_match=0.0,
        pension_inflation_adjustment_pct=0.0,
    )

    wife = SimpleNamespace(
        age=0,
        retire_age=100,
        income=0.0,
        ss=0.0,
        ss_age=99,
        pension=0.0,
        pension_age=99,
        annuity=0.0,
        annuity_age=99,
        annual_401k_contribution=0.0,
        annual_employer_match=0.0,
        pension_inflation_adjustment_pct=0.0,
    )

    return husband, wife


class FakePortfolio:
    def __init__(self):
        self.eq_pre = 30.0
        self.bd_pre = 20.0
        self.cs_pre = 10.0

        self.eq_post = 20.0
        self.bd_post = 10.0
        self.cs_post = 10.0

        self.eq_roth = 0.0
        self.bd_roth = 0.0
        self.cs_roth = 0.0

        self.hsa_eq = 0.0
        self.hsa_bd = 0.0
        self.hsa_cs = 0.0

        self.re_post = 20.0

        self.eq_ratio_pre = 0.0
        self.bd_ratio_pre = 0.0
        self.cs_ratio_pre = 0.0
        self.eq_ratio_post = 0.0
        self.bd_ratio_post = 0.0
        self.cs_ratio_post = 0.0

    @property
    def total_value_pre(self):
        return self.eq_pre + self.bd_pre + self.cs_pre

    @property
    def total_value_post(self):
        return self.eq_post + self.bd_post + self.cs_post

    @property
    def total_value_roth(self):
        return self.eq_roth + self.bd_roth + self.cs_roth

    @property
    def total_value_hsa(self):
        return self.hsa_eq + self.hsa_bd + self.hsa_cs

    @property
    def total_value(self):
        return (
            self.total_value_pre
            + self.total_value_post
            + self.total_value_roth
            + self.total_value_hsa
        )

    @property
    def total_value_cash(self):
        return self.cs_pre + self.cs_post + self.cs_roth + self.hsa_cs

    @property
    def total_value_bonds(self):
        return self.bd_pre + self.bd_post + self.bd_roth + self.hsa_bd


def install_minimal_core_engine_mocks(run_sim_core_module, monkeypatch):
    breakdown_keys = [
        "work",
        "pension",
        "annuity",
        "ss",
        "rmd",
        "withdrawal",
        "bond_interest",
        "cash_interest",
        "qualified_dividends",
        "special_income",
    ]

    def create_sim_portfolio(*args, **kwargs):
        return FakePortfolio()

    def create_empty_sim_portfolio(*args, **kwargs):
        return FakePortfolio()

    def compute_household_allocation_targets(*args, **kwargs):
        return None

    def estimate_household_post_tax_income_components(*args, **kwargs):
        return (
            0.0,  # bond_interest
            0.0,  # cash_interest
            0.0,  # qualified_dividends
            0.0,  # total
            0.0,  # husband total
            0.0,  # wife total
        )

    def apply_returns_and_fund_expenses(port, eq, bd, cs, re, fund_expense):
        eq_mult = 1.0 + eq
        bd_mult = 1.0 + bd
        cs_mult = 1.0 + cs
        re_mult = 1.0 + re
        exp_mult = 1.0 - fund_expense

        for attr in ["eq_pre", "eq_post", "eq_roth", "hsa_eq"]:
            setattr(port, attr, getattr(port, attr) * eq_mult)

        for attr in ["bd_pre", "bd_post", "bd_roth", "hsa_bd"]:
            setattr(port, attr, getattr(port, attr) * bd_mult)

        for attr in ["cs_pre", "cs_post", "cs_roth", "hsa_cs"]:
            setattr(port, attr, getattr(port, attr) * cs_mult)

        port.re_post *= re_mult

        total_before = port.total_value

        for attr in [
            "eq_pre", "bd_pre", "cs_pre",
            "eq_post", "bd_post", "cs_post",
            "eq_roth", "bd_roth", "cs_roth",
            "hsa_eq", "hsa_bd", "hsa_cs",
        ]:
            setattr(port, attr, getattr(port, attr) * exp_mult)

        return total_before * fund_expense

    def apply_post_tax_income_components_to_income(income, *args, **kwargs):
        return income

    def apply_pre_tax_contribution(*args, **kwargs):
        return None

    def apply_net_income_single(*args, **kwargs):
        return {
            "post_tax_used": 0.0,
            "pre_tax_used": 0.0,
            "uncovered": 0.0,
        }

    def apply_net_income_couple(*args, **kwargs):
        return {
            "post_tax_used": 0.0,
            "pre_tax_used": 0.0,
            "uncovered": 0.0,
        }

    def deduct_post_tax_amount(*args, **kwargs):
        return 0.0

    def apply_returns(port, eq, bd, cs, re):
        growth = 1.0 + (0.60 * eq + 0.30 * bd + 0.10 * cs)
        port.total_value *= growth
        port.total_value_pre *= growth
        port.total_value_post *= growth
        port.total_value_cash *= (1.0 + cs)
        port.total_value_bonds *= (1.0 + bd)
        port.re_post *= (1.0 + re)

    def apply_fund_expenses(*args, **kwargs):
        return 0.0

    def rebalance(*args, **kwargs):
        return None

    monkeypatch.setattr(run_sim_core_module.portfolioEngine, "create_sim_portfolio", create_sim_portfolio)
    monkeypatch.setattr(run_sim_core_module.portfolioEngine, "create_empty_sim_portfolio", create_empty_sim_portfolio)
    monkeypatch.setattr(run_sim_core_module.portfolioEngine, "compute_household_allocation_targets", compute_household_allocation_targets)
    monkeypatch.setattr(run_sim_core_module.portfolioEngine, "estimate_household_post_tax_income_components", estimate_household_post_tax_income_components)
    monkeypatch.setattr(run_sim_core_module.portfolioEngine, "apply_post_tax_income_components_to_income", apply_post_tax_income_components_to_income)
    monkeypatch.setattr(run_sim_core_module.portfolioEngine, "apply_pre_tax_contribution", apply_pre_tax_contribution)
    monkeypatch.setattr(run_sim_core_module.portfolioEngine, "apply_net_income_single", apply_net_income_single)
    monkeypatch.setattr(run_sim_core_module.portfolioEngine, "apply_net_income_couple", apply_net_income_couple)
    monkeypatch.setattr(run_sim_core_module.portfolioEngine, "deduct_post_tax_amount", deduct_post_tax_amount)
    monkeypatch.setattr(run_sim_core_module.portfolioEngine, "apply_returns", apply_returns)
    monkeypatch.setattr(run_sim_core_module.portfolioEngine, "apply_fund_expenses", apply_fund_expenses)
    monkeypatch.setattr(run_sim_core_module.portfolioEngine, "rebalance", rebalance)

    monkeypatch.setattr(run_sim_core_module.withdrawalEngine, "use_expenses_this_year", lambda *args, **kwargs: False)
    monkeypatch.setattr(run_sim_core_module.withdrawalEngine, "calculate_rmds", lambda *args, **kwargs: 0.0)
    monkeypatch.setattr(run_sim_core_module.withdrawalEngine, "withdraw_rmds", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        run_sim_core_module.withdrawalEngine,
        "calculate_retirement_withdrawal",
        lambda *args, **kwargs: {"pre_tax": 0.0, "post_tax": 0.0, "total": 0.0},
    )

    monkeypatch.setattr(
        run_sim_core_module.incomeEngine,
        "calculate_income_breakdown",
        lambda *args, **kwargs: {
            "total": 0.0,
            "by_person": {"husband": 0.0, "wife": 0.0},
            "by_class": {k: 0.0 for k in breakdown_keys},
        },
    )
    monkeypatch.setattr(
        run_sim_core_module.incomeEngine,
        "calculate_pre_tax_401k_contributions",
        lambda *args, **kwargs: (0.0, 0.0)
        )
    monkeypatch.setattr(run_sim_core_module.incomeEngine, "apply_employee_401k_to_income", lambda *args, **kwargs: None)

    monkeypatch.setattr(
        run_sim_core_module.taxEngine,
        "calculate_total_income_tax_split",
        lambda *args, **kwargs: (
            0.0,  # federal_ordinary_tax
            0.0,  # federal_qualified_dividend_tax
            0.0,  # state_income_tax
            0.0,  # total_tax
            0.0,  # federal_marginal_rate
        )
    )
    monkeypatch.setattr(run_sim_core_module.taxEngine, "get_us_federal_marginal_tax_rate", lambda *args, **kwargs: 0.0)
    monkeypatch.setattr(
        run_sim_core_module.taxEngine,
        "allocate_tax_proportionally",
        lambda *args, **kwargs: {"husband": 0.0, "wife": 0.0},
    )

    monkeypatch.setattr(run_sim_core_module.expenseEngine, "calculate_expenses", lambda *args, **kwargs: 0.0)