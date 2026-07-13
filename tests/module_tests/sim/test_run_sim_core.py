from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest


@dataclass
class DummySimConfig:
    years_to_simulate: int = 2
    second_person_enabled: bool = True
    include_realestate: bool = True
    start_year: int = 2025

    calculate_income_taxes: bool = True
    calculate_payroll_taxes: bool = True
    calculate_state_taxes: bool = False
    tax_filing_status: str = "Single"
    state_of_residence: str | None = None

    use_fund_expenses: bool = False
    fund_expense: float = 0.0

    rebalance_every_year: bool = False
    plot_mode: str = "raw"
    subplot_mode: str = "deterministic"
    sim_type: str = "portfolio_sim"
    monte_carlo_mode: str = "pathBasedAnnualSampling"
    monte_carlo_plot_style: str = "fill"
    use_correlated_returns: bool = True

    inflation_rate: float = 0.05
    sim_initial_allocation_mode: str = "dont-rebalance"

    eq_mean: float = 0.07
    bd_mean: float = 0.03
    cs_mean: float = 0.01
    re_mean: float = 0.04

    eq_std: float = 0.15
    bd_std: float = 0.06
    cs_std: float = 0.01
    re_std: float = 0.12

    post_tax_equity_dividend_yield: float = 0.0
    post_tax_bond_interest_yield: float = 0.0
    post_tax_cash_interest_yield: float = 0.0

    include_rmd: bool = False
    retirement_withdraw_mode: str = "Off"
    retirement_withdraw_pct: float = 4.0
    retirement_withdraw_dollars: float = 0.0
    always_use_expense_mode: bool = True
    scenario_expense_multiplier: float = 1.0

    household_eq_target: float | None = None
    household_bd_target: float | None = None
    household_cs_target: float | None = None

    custom_stock: float = 0.6
    custom_bonds: float = 0.3
    custom_cash: float = 0.1

    return_correlation_matrix: tuple[tuple[float, ...], ...] = (
        (1.0, 0.2, 0.1, 0.3),
        (0.2, 1.0, 0.1, 0.2),
        (0.1, 0.1, 1.0, 0.0),
        (0.3, 0.2, 0.0, 1.0),
    )


class DummyPerson:
    def __init__(
        self,
        *,
        age: int = 40,
        retire_age: int = 65,
        income: float = 0.0,
        ss: float = 0.0,
        ss_age: int = 67,
        pension: float = 0.0,
        pension_age: int = 65,
        pension_inflation_adjustment_pct: float = 0.0,
        annuity: float = 0.0,
        annuity_age: int = 70,
        annual_401k_contribution: float = 0.0,
        annual_employer_match: float = 0.0,
    ):
        self.age = age
        self.retire_age = retire_age
        self.income = income
        self.ss = ss
        self.ss_age = ss_age
        self.pension = pension
        self.pension_age = pension_age
        self.pension_inflation_adjustment_pct = pension_inflation_adjustment_pct
        self.annuity = annuity
        self.annuity_age = annuity_age
        self.annual_401k_contribution = annual_401k_contribution
        self.annual_employer_match = annual_employer_match


class DummyPortfolio:
    pass


class DummyExpenses:
    pass


def _make_portfolio(
    total=100.0,
    *,
    pre_ratio=0.6,
    post_ratio=0.4,
    roth_ratio=0.0,
    hsa_ratio=0.0,
    re_post=20.0,
):
    pre = total * pre_ratio
    post = total * post_ratio
    roth = total * roth_ratio
    hsa = total * hsa_ratio

    return SimpleNamespace(
        eq_pre=pre * 0.5,
        bd_pre=pre * 0.3,
        cs_pre=pre * 0.2,

        eq_post=post * 0.5,
        bd_post=post * 0.3,
        cs_post=post * 0.2,

        eq_roth=roth * 0.5,
        bd_roth=roth * 0.3,
        cs_roth=roth * 0.2,

        eq_hsa=hsa * 0.5,
        bd_hsa=hsa * 0.3,
        cs_hsa=hsa * 0.2,

        re_post=re_post,

        total_value=total,
        total_value_pre=pre,
        total_value_post=post,
        total_value_roth=roth,
        total_value_hsa=hsa,
        total_value_cash=total * 0.2,
        total_value_bonds=total * 0.3,
    )


def _income(*, total=100.0, husband=60.0, wife=40.0):
    return {
        "total": total,
        "by_class": {
            "work": 50.0,
            "pension": 0.0,
            "annuity": 0.0,
            "ss": 20.0,
            "rmd": 10.0,
            "withdrawal": 0.0,
            "bond_interest": 0.0,
            "cash_interest": 0.0,
            "qualified_dividends": 0.0,
            "special_income": 0.0,
        },
        "by_person": {"husband": husband, "wife": wife},
    }


def _post_tax_tuple(
    *,
    bond_interest=0.0,
    cash_interest=0.0,
    qualified_dividends=0.0,
    husband_total=0.0,
    wife_total=0.0,
):
    total = bond_interest + cash_interest + qualified_dividends
    return (
        bond_interest,
        cash_interest,
        qualified_dividends,
        total,
        husband_total,
        wife_total,
    )


def _tax_split(
    *,
    federal_ordinary_tax=7.0,
    federal_qualified_dividend_tax=2.0,
    state_income_tax=1.0,
    total_tax=10.0,
    federal_marginal_rate=0.12,
):
    return (
        federal_ordinary_tax,
        federal_qualified_dividend_tax,
        state_income_tax,
        total_tax,
        federal_marginal_rate,
    )


def _patch_baseline(monkeypatch, mod, sim_config: DummySimConfig):
    monkeypatch.setattr(mod.taxEngine, "initialize_tax_engine_for_simulation", lambda cfg: None)
    monkeypatch.setattr(mod.incomeEngine, "initialize_income_engine_for_simulation", lambda h, w, cfg: None)
    monkeypatch.setattr(mod.monteCarloEngine, "prepare_market_path_sampling", lambda cfg: None)
    monkeypatch.setattr(mod.expenseEngine, "initialize_expense_engine_for_simulation", lambda cfg: None)

    monkeypatch.setattr(
        mod.taxEngine,
        "prepare_tax_year_cache",
        lambda year, cfg: {
            "year": year,
            "social_security_wage_base": 200000.0,
            "additional_medicare_threshold": 200000.0,
        }
    )

    monkeypatch.setattr(
        mod.taxEngine,
        "calculate_employee_payroll_tax_split",
        lambda *a, **k: (
            0.0,  # social_security_tax
            0.0,  # medicare_tax
            0.0,  # additional_medicare_tax
            0.0,  # payroll_tax
        ),
    )

    monkeypatch.setattr(
        mod.portfolioEngine,
        "create_sim_portfolio",
        lambda p, c: _make_portfolio(),
    )
    monkeypatch.setattr(
        mod.portfolioEngine,
        "create_empty_sim_portfolio",
        lambda c: _make_portfolio(0.0, re_post=0.0),
    )
    monkeypatch.setattr(
        mod.portfolioEngine,
        "compute_household_allocation_targets",
        lambda *a, **k: None,
    )

    monkeypatch.setattr(
        mod.monteCarloEngine,
        "generate_market_path",
        lambda cfg, years, sim_index: {
            "eq": [0.0] * (years + 1),
            "bd": [0.0] * (years + 1),
            "cs": [0.0] * (years + 1),
            "re": [0.0] * (years + 1),
        },
    )

    monkeypatch.setattr(mod.withdrawalEngine, "calculate_rmds", lambda *a, **k: 0.0)
    monkeypatch.setattr(mod.withdrawalEngine, "withdraw_rmds", lambda *a, **k: None)
    monkeypatch.setattr(mod.withdrawalEngine, "use_expenses_this_year", lambda *a, **k: True)

    monkeypatch.setattr(
        mod.withdrawalEngine,
        "calculate_retirement_withdrawal",
        lambda *a, **k: {
            "pre_tax": 20.0,
            "post_tax": 10.0,
            "roth": 0.0,
            "hsa": 0.0,
            "rmd": 0.0,
            "total": 30.0,
            "by_person": {
                "husband": 18.0,
                "wife": 12.0,
            },
            "rmd_by_person": {
                "husband": 0.0,
                "wife": 0.0,
            },
        },
    )

    monkeypatch.setattr(
        mod.incomeEngine,
        "calculate_income_breakdown",
        lambda *a, **k: _income(),
    )
    monkeypatch.setattr(
        mod.incomeEngine,
        "calculate_pre_tax_401k_contributions",
        lambda *a, **k: (0.0, 0.0),
    )
    monkeypatch.setattr(
        mod.incomeEngine,
        "apply_employee_401k_to_income",
        lambda *a, **k: None,
    )

    monkeypatch.setattr(
        mod.portfolioEngine,
        "estimate_household_post_tax_income_components",
        lambda *a, **k: _post_tax_tuple(),
    )
    monkeypatch.setattr(
        mod.portfolioEngine,
        "apply_pre_tax_contribution",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        mod.portfolioEngine,
        "apply_net_income_couple",
        lambda *a, **k: {
            "post_tax_used": 0.0,
            "pre_tax_used": 0.0,
            "uncovered": 0.0,
        },
    )
    monkeypatch.setattr(
        mod.portfolioEngine,
        "apply_net_income_single",
        lambda *a, **k: {
            "post_tax_used": 0.0,
            "pre_tax_used": 0.0,
            "uncovered": 0.0,
        },
    )
    monkeypatch.setattr(
        mod.portfolioEngine,
        "deduct_post_tax_amount",
        lambda *a, **k: 0.0,
    )
    monkeypatch.setattr(
        mod.portfolioEngine,
        "apply_returns_and_fund_expenses",
        lambda *a, **k: 0.0,
    )
    monkeypatch.setattr(
        mod.portfolioEngine,
        "rebalance",
        lambda *a, **k: None,
    )

    monkeypatch.setattr(
        mod.expenseEngine,
        "calculate_expenses",
        lambda *a, **k: 30.0,
    )
    monkeypatch.setattr(
        mod.taxEngine,
        "calculate_total_income_tax_split",
        lambda *a, **k: _tax_split(),
    )
    monkeypatch.setattr(
        mod.taxEngine,
        "allocate_tax_proportionally_couple",
        lambda total_tax, h_inc, w_inc: (6.0, 4.0),
    )


@pytest.fixture
def mod():
    from src.warpsimlab.sim import run_sim_core as mod

    return mod


def _run(mod, monkeypatch, sim_config: DummySimConfig):
    _patch_baseline(monkeypatch, mod, sim_config)
    return mod.simulate_yearly_portfolios(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
        num_sims=1,
    )


def test_simulate_yearly_portfolios_exposes_expected_shapes(mod, monkeypatch):
    sim_config = DummySimConfig()
    _patch_baseline(monkeypatch, mod, sim_config)

    results = mod.simulate_yearly_portfolios(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
        num_sims=2,
    )

    years = sim_config.years_to_simulate + 1
    assert results["total_assets"].shape == (2, years)
    assert results["net_income"].shape == (2, years)
    assert results["taxes"].shape == (2, years)
    assert results["gross_income"].shape == (2, years)
    assert results["federal_ordinary_tax"].shape == (2, years)
    assert results["federal_qualified_dividend_tax"].shape == (2, years)
    assert results["state_income_tax"].shape == (2, years)
    assert results["breakdown_by_class"]["work"].shape == (2, years)
    assert results["roth_assets"].shape == (2, years)
    assert results["hsa_assets"].shape == (2, years)
    assert results["roth_withdrawals"].shape == (2, years)
    assert results["hsa_withdrawals"].shape == (2, years)


def test_single_person_branch_zeros_wife_income(mod, monkeypatch):
    sim_config = DummySimConfig(second_person_enabled=False)
    _patch_baseline(monkeypatch, mod, sim_config)
    monkeypatch.setattr(mod.incomeEngine, "calculate_income_breakdown", lambda *a, **k: _income(husband=100.0, wife=0.0))
    monkeypatch.setattr(mod.taxEngine, "calculate_total_income_tax_split", lambda *a, **k: _tax_split(total_tax=5.0, federal_marginal_rate=0.10))

    results = mod.simulate_yearly_portfolios(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
        num_sims=1,
    )

    assert results["net_income_wife"][0, 1] == pytest.approx(0.0)


def test_stores_post_tax_income_components(mod, monkeypatch):
    sim_config = DummySimConfig()
    _patch_baseline(monkeypatch, mod, sim_config)
    monkeypatch.setattr(
        mod.portfolioEngine,
        "estimate_household_post_tax_income_components",
        lambda *a, **k: _post_tax_tuple(
            bond_interest=3.0,
            cash_interest=2.0,
            qualified_dividends=5.0,
            husband_total=6.0,
            wife_total=4.0,
        ),
    )

    results = mod.simulate_yearly_portfolios(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
        num_sims=1,
    )

    assert results["bond_interest"][0, 1] == pytest.approx(3.0)
    assert results["cash_interest"][0, 1] == pytest.approx(2.0)
    assert results["qualified_dividends"][0, 1] == pytest.approx(5.0)
    assert results["breakdown_by_class"]["bond_interest"][0, 1] == pytest.approx(3.0)
    assert results["breakdown_by_class"]["cash_interest"][0, 1] == pytest.approx(2.0)
    assert results["breakdown_by_class"]["qualified_dividends"][0, 1] == pytest.approx(5.0)


def test_no_income_tax_keeps_net_income_equal_to_total_income(mod, monkeypatch):
    sim_config = DummySimConfig(
        calculate_income_taxes=False,
        calculate_payroll_taxes=False,
    )
    _patch_baseline(monkeypatch, mod, sim_config)
    monkeypatch.setattr(mod.taxEngine, "calculate_total_income_tax_split", lambda *a, **k: _tax_split(total_tax=99.0, federal_marginal_rate=0.0))

    results = mod.simulate_yearly_portfolios(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
        num_sims=1,
    )

    assert results["net_income"][0, 1] == pytest.approx(100.0)
    assert results["taxes"][0, 1] == pytest.approx(99.0)


def test_emergency_pre_tax_flow_updates_tax_delta_and_gross_income(mod, monkeypatch):
    sim_config = DummySimConfig()
    _patch_baseline(monkeypatch, mod, sim_config)
    monkeypatch.setattr(mod.expenseEngine, "calculate_expenses", lambda *a, **k: 150.0)

    call_counter = {"n": 0}

    def fake_tax_split(*args, **kwargs):
        call_counter["n"] += 1
        if call_counter["n"] == 1:
            return _tax_split(
                federal_ordinary_tax=7.0,
                federal_qualified_dividend_tax=2.0,
                state_income_tax=1.0,
                total_tax=10.0,
                federal_marginal_rate=0.22,
            )
        return _tax_split(
            federal_ordinary_tax=12.0,
            federal_qualified_dividend_tax=2.0,
            state_income_tax=2.0,
            total_tax=16.0,
            federal_marginal_rate=0.22,
        )

    monkeypatch.setattr(mod.taxEngine, "calculate_total_income_tax_split", fake_tax_split)
    monkeypatch.setattr(
        mod.portfolioEngine,
        "apply_net_income_couple",
        lambda *a, **k: {"post_tax_used": 40.0, "pre_tax_used": 25.0, "uncovered": 0.0},
    )
    monkeypatch.setattr(mod.portfolioEngine, "deduct_post_tax_amount", lambda *a, **k: 6.0)

    results = mod.simulate_yearly_portfolios(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
        num_sims=1,
    )

    assert results["emergency_pre_tax_used"][0, 1] == pytest.approx(25.0)
    assert results["final_tax_delta"][0, 1] == pytest.approx(6.0)
    assert results["final_tax_delta_deducted"][0, 1] == pytest.approx(6.0)
    assert results["final_tax_delta_uncovered"][0, 1] == pytest.approx(0.0)
    assert results["taxes"][0, 1] == pytest.approx(16.0)
    assert results["gross_income"][0, 1] == pytest.approx(125.0)


def test_retirement_withdrawal_branch_adds_pre_tax_to_ordinary_income(mod, monkeypatch):
    sim_config = DummySimConfig()
    _patch_baseline(monkeypatch, mod, sim_config)
    monkeypatch.setattr(mod.withdrawalEngine, "use_expenses_this_year", lambda *a, **k: False)
    monkeypatch.setattr(
        mod.withdrawalEngine,
        "calculate_retirement_withdrawal",
        lambda *a, **k: {
            "pre_tax": 20.0,
            "post_tax": 10.0,
            "roth": 0.0,
            "hsa": 0.0,
            "rmd": 0.0,
            "total": 30.0,
            "by_person": {
                "husband": 18.0,
                "wife": 12.0,
            },
            "rmd_by_person": {
                "husband": 0.0,
                "wife": 0.0,
            },
        },
    )

    seen = {}

    def fake_tax_split(*args, **kwargs):
        seen["ordinary_income"] = kwargs["ordinary_income"]
        seen["qualified_dividends"] = kwargs["qualified_dividends"]
        return _tax_split(
            federal_ordinary_tax=10.0,
            federal_qualified_dividend_tax=1.0,
            state_income_tax=1.0,
            total_tax=12.0,
        )

    monkeypatch.setattr(mod.taxEngine, "calculate_total_income_tax_split", fake_tax_split)

    results = mod.simulate_yearly_portfolios(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
        num_sims=1,
    )

    assert seen["ordinary_income"] == pytest.approx(120.0)
    assert seen["qualified_dividends"] == pytest.approx(0.0)
    assert results["breakdown_by_class"]["withdrawal"][0, 1] == pytest.approx(30.0)
    assert results["taxes"][0, 1] == pytest.approx(12.0)


def test_allocates_couple_net_income_after_tax(mod, monkeypatch):
    sim_config = DummySimConfig()
    _patch_baseline(monkeypatch, mod, sim_config)
    monkeypatch.setattr(mod.taxEngine, "allocate_tax_proportionally_couple", lambda total_tax, h_inc, w_inc: (6.0, 4.0))

    results = mod.simulate_yearly_portfolios(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
        num_sims=1,
    )

    assert results["net_income_husband"][0, 1] == pytest.approx(54.0)
    assert results["net_income_wife"][0, 1] == pytest.approx(36.0)


def test_real_mode_deflates_selected_series(mod, monkeypatch):
    sim_config = DummySimConfig(plot_mode="real", inflation_rate=0.10)
    _patch_baseline(monkeypatch, mod, sim_config)
    monkeypatch.setattr(mod.expenseEngine, "calculate_expenses", lambda *a, **k: 10.0)
    monkeypatch.setattr(mod.taxEngine, "calculate_total_income_tax_split", lambda *a, **k: _tax_split(total_tax=5.0, federal_marginal_rate=0.10))
    monkeypatch.setattr(mod.taxEngine, "allocate_tax_proportionally_couple", lambda total_tax, h_inc, w_inc: (3.0, 2.0))

    results = mod.simulate_yearly_portfolios(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
        num_sims=1,
    )

    assert results["net_income"][0, 1] == pytest.approx(95.0 / 1.10)
    assert results["taxes"][0, 1] == pytest.approx(5.0 / 1.10)
    assert results["expense_amt"][0, 1] == pytest.approx(10.0 / 1.10)
