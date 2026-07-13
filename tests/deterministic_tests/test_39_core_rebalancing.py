import numpy as np
import pytest

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.dataClasses.person import Person
from src.warpsimlab.dataClasses.portfolio import Portfolio
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios
from src.warpsimlab.sim.simulationObject import Simulation


def make_person():
    return Person(
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


def make_portfolio(
    *,
    equity_pre=0.0,
    bond_pre=0.0,
    cash_pre=0.0,
    equity_post=0.0,
    bond_post=0.0,
    cash_post=0.0,
    equity_roth=0.0,
    bond_roth=0.0,
    cash_roth=0.0,
    hsa_equity=0.0,
    hsa_bond=0.0,
    hsa_cash=0.0,
):
    return Portfolio(
        equity_pre=equity_pre,
        equity_post=equity_post,
        bond_pre=bond_pre,
        bond_post=bond_post,
        cash_pre=cash_pre,
        cash_post=cash_post,
        real_estate=0.0,
        equity_roth=equity_roth,
        bond_roth=bond_roth,
        cash_roth=cash_roth,
        hsa_cash=hsa_cash,
        hsa_equity=hsa_equity,
        hsa_bond=hsa_bond,
    )


def make_config(
    *,
    sim_initial_allocation_mode="dont-rebalance",
    rebalance_every_year=False,
    second_person_enabled=False,
    custom_stock=0.0,
    custom_bonds=0.0,
    custom_cash=1.0,
):
    config = Simulation(
        start_year=2026,
        years_to_simulate=1,
        inflation_rate=0.0,
        num_sims=1,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode="raw",
        subplot_mode="baseline",
        include_rmd=False,
        calculate_income_taxes=False,
        calculate_payroll_taxes=False,
        tax_filing_status="Single",
        calculate_state_taxes=False,
        state_of_residence="TX",
        second_person_enabled=second_person_enabled,
        eq_mean=0.0,
        bd_mean=0.0,
        cs_mean=0.0,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        sim_type="portfolio_sim",
        sim_initial_allocation_mode=sim_initial_allocation_mode,
        custom_stock=custom_stock,
        custom_bonds=custom_bonds,
        custom_cash=custom_cash,
        rebalance_every_year=rebalance_every_year,
        include_realestate=False,
        re_mean=0.0,
        re_std=0.0,
        output_csv="None",
        retirement_withdraw_mode="Off",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=0.0,
        always_use_expense_mode=True,
        sequence_risk_enabled=False,
        scenario_expense_multiplier=1.0,
        overlay_tax_impacts=False,
        overlay_fund_expense_impacts=False,
        overlay_household_expenses=False,
        overlay_profit_loss=False,
        overlay_retirement_age=False,
        show_simulated_shortfall_rate=False,
        use_snapshot_annotations=False,
        user_annotation_strings=[],
        root=None,
    )

    # portfolioEngine currently reads this compatibility name.
    config.sim_rebalance = sim_initial_allocation_mode

    return config


def install_market_path(
    monkeypatch,
    *,
    equity_return=0.0,
    bond_return=0.0,
    cash_return=0.0,
):
    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        assert years_to_simulate == 1

        return {
            "eq": np.array([0.0, equity_return], dtype=float),
            "bd": np.array([0.0, bond_return], dtype=float),
            "cs": np.array([0.0, cash_return], dtype=float),
            "re": np.zeros(2, dtype=float),
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )


def run_one_year(
    monkeypatch,
    *,
    husband_portfolio,
    wife_portfolio=None,
    sim_initial_allocation_mode="dont-rebalance",
    rebalance_every_year=False,
    second_person_enabled=False,
    custom_stock=0.0,
    custom_bonds=0.0,
    custom_cash=1.0,
    equity_return=0.0,
    bond_return=0.0,
    cash_return=0.0,
):
    install_market_path(
        monkeypatch,
        equity_return=equity_return,
        bond_return=bond_return,
        cash_return=cash_return,
    )

    if wife_portfolio is None:
        wife_portfolio = make_portfolio()

    return simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        make_person(),
        make_person(),
        DynamicExpenses(),
        make_config(
            sim_initial_allocation_mode=(
                sim_initial_allocation_mode
            ),
            rebalance_every_year=rebalance_every_year,
            second_person_enabled=second_person_enabled,
            custom_stock=custom_stock,
            custom_bonds=custom_bonds,
            custom_cash=custom_cash,
        ),
        num_sims=1,
    )


def equity_total(results, year):
    return (
        results["total_assets"][0, year]
        - results["bonds"][0, year]
        - results["cash"][0, year]
    )


def test_dont_rebalance_preserves_initial_allocation(monkeypatch):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=60_000.0,
            bond_pre=30_000.0,
            cash_pre=10_000.0,
        ),
        sim_initial_allocation_mode="dont-rebalance",
    )

    assert results["total_assets"][0, 0] == pytest.approx(
        100_000.0
    )
    assert equity_total(results, 0) == pytest.approx(
        60_000.0
    )
    assert results["bonds"][0, 0] == pytest.approx(
        30_000.0
    )
    assert results["cash"][0, 0] == pytest.approx(
        10_000.0
    )

    assert equity_total(results, 1) == pytest.approx(
        60_000.0
    )
    assert results["bonds"][0, 1] == pytest.approx(
        30_000.0
    )
    assert results["cash"][0, 1] == pytest.approx(
        10_000.0
    )


def test_initial_70_20_10_allocation_is_applied(monkeypatch):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=20_000.0,
            bond_pre=30_000.0,
            cash_pre=50_000.0,
        ),
        sim_initial_allocation_mode="70-20-10",
    )

    assert results["pre_tax_assets"][0, 0] == pytest.approx(
        100_000.0
    )
    assert equity_total(results, 0) == pytest.approx(
        70_000.0
    )
    assert results["bonds"][0, 0] == pytest.approx(
        20_000.0
    )
    assert results["cash"][0, 0] == pytest.approx(
        10_000.0
    )

    assert results["total_assets"][0, 0] == pytest.approx(
        100_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        100_000.0
    )


def test_custom_initial_allocation_is_applied(monkeypatch):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_post=80_000.0,
            bond_post=10_000.0,
            cash_post=10_000.0,
        ),
        sim_initial_allocation_mode="custom",
        custom_stock=0.50,
        custom_bonds=0.30,
        custom_cash=0.20,
    )

    assert results["post_tax_assets"][0, 0] == pytest.approx(
        100_000.0
    )
    assert equity_total(results, 0) == pytest.approx(
        50_000.0
    )
    assert results["bonds"][0, 0] == pytest.approx(
        30_000.0
    )
    assert results["cash"][0, 0] == pytest.approx(
        20_000.0
    )


def test_initial_allocation_includes_roth_and_hsa(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=100_000.0,
            bond_post=100_000.0,
            cash_roth=100_000.0,
            hsa_equity=100_000.0,
        ),
        sim_initial_allocation_mode="50-30-20",
    )

    assert results["pre_tax_assets"][0, 0] == pytest.approx(
        100_000.0
    )
    assert results["post_tax_assets"][0, 0] == pytest.approx(
        100_000.0
    )
    assert results["roth_assets"][0, 0] == pytest.approx(
        100_000.0
    )
    assert results["hsa_assets"][0, 0] == pytest.approx(
        100_000.0
    )

    assert results["total_assets"][0, 0] == pytest.approx(
        400_000.0
    )
    assert equity_total(results, 0) == pytest.approx(
        200_000.0
    )
    assert results["bonds"][0, 0] == pytest.approx(
        120_000.0
    )
    assert results["cash"][0, 0] == pytest.approx(
        80_000.0
    )


def test_no_annual_rebalance_allows_allocation_drift(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=70_000.0,
            bond_pre=20_000.0,
            cash_pre=10_000.0,
        ),
        sim_initial_allocation_mode="70-20-10",
        rebalance_every_year=False,
        equity_return=0.10,
    )

    assert results["total_assets"][0, 1] == pytest.approx(
        107_000.0
    )
    assert equity_total(results, 1) == pytest.approx(
        77_000.0
    )
    assert results["bonds"][0, 1] == pytest.approx(
        20_000.0
    )
    assert results["cash"][0, 1] == pytest.approx(
        10_000.0
    )

    assert equity_total(results, 1) / 107_000.0 == (
        pytest.approx(77_000.0 / 107_000.0)
    )
    assert equity_total(results, 1) / 107_000.0 != (
        pytest.approx(0.70)
    )


def test_annual_rebalance_restores_selected_target(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=70_000.0,
            bond_pre=20_000.0,
            cash_pre=10_000.0,
        ),
        sim_initial_allocation_mode="70-20-10",
        rebalance_every_year=True,
        equity_return=0.10,
    )

    ending_total = 107_000.0

    assert results["total_assets"][0, 1] == pytest.approx(
        ending_total
    )
    assert equity_total(results, 1) == pytest.approx(
        ending_total * 0.70
    )
    assert results["bonds"][0, 1] == pytest.approx(
        ending_total * 0.20
    )
    assert results["cash"][0, 1] == pytest.approx(
        ending_total * 0.10
    )


def test_annual_rebalance_preserves_total_value(monkeypatch):
    without_rebalance = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=50_000.0,
            bond_pre=30_000.0,
            cash_pre=20_000.0,
        ),
        sim_initial_allocation_mode="50-30-20",
        rebalance_every_year=False,
        equity_return=0.10,
        bond_return=-0.05,
        cash_return=0.02,
    )

    with_rebalance = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=50_000.0,
            bond_pre=30_000.0,
            cash_pre=20_000.0,
        ),
        sim_initial_allocation_mode="50-30-20",
        rebalance_every_year=True,
        equity_return=0.10,
        bond_return=-0.05,
        cash_return=0.02,
    )

    assert with_rebalance["total_assets"][0, 1] == (
        pytest.approx(
            without_rebalance["total_assets"][0, 1]
        )
    )

    expected_total = (
        50_000.0 * 1.10
        + 30_000.0 * 0.95
        + 20_000.0 * 1.02
    )

    assert with_rebalance["total_assets"][0, 1] == (
        pytest.approx(expected_total)
    )


def test_maintain_current_uses_household_allocation(
    monkeypatch,
):
    results = run_one_year(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=80_000.0,
            bond_pre=20_000.0,
        ),
        wife_portfolio=make_portfolio(
            bond_post=40_000.0,
            cash_post=60_000.0,
        ),
        sim_initial_allocation_mode=(
            "maintain-current-allocation"
        ),
        second_person_enabled=True,
    )

    household_total = 200_000.0
    expected_equity_ratio = 80_000.0 / household_total
    expected_bond_ratio = 60_000.0 / household_total
    expected_cash_ratio = 60_000.0 / household_total

    assert expected_equity_ratio == pytest.approx(0.40)
    assert expected_bond_ratio == pytest.approx(0.30)
    assert expected_cash_ratio == pytest.approx(0.30)

    assert results["total_assets"][0, 0] == pytest.approx(
        household_total
    )
    assert equity_total(results, 0) == pytest.approx(
        household_total * expected_equity_ratio
    )
    assert results["bonds"][0, 0] == pytest.approx(
        household_total * expected_bond_ratio
    )
    assert results["cash"][0, 0] == pytest.approx(
        household_total * expected_cash_ratio
    )

    assert results["pre_tax_assets"][0, 0] == pytest.approx(
        100_000.0
    )
    assert results["post_tax_assets"][0, 0] == pytest.approx(
        100_000.0
    )