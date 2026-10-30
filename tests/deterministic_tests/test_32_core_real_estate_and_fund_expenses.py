import numpy as np
import pytest
from tests.architectural_helpers import make_person, make_portfolio, make_simulation

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


def make_config(
    *,
    include_realestate=False,
    use_fund_expenses=False,
    fund_expense=0.0,
):
    return make_simulation(
        fund_expense=fund_expense,
        use_fund_expenses=use_fund_expenses,
        results_mode="baseline",
        sim_initial_allocation_mode="dont-rebalance",
        include_realestate=include_realestate,
        retirement_withdraw_dollars=0.0,
    )


def install_market_path(
    monkeypatch,
    *,
    equity_return=0.0,
    bond_return=0.0,
    cash_return=0.0,
    real_estate_return=0.0,
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
            "re": np.array([0.0, real_estate_return], dtype=float),
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )


def run_one_year(
    monkeypatch,
    husband_portfolio,
    *,
    include_realestate=False,
    use_fund_expenses=False,
    fund_expense=0.0,
    equity_return=0.0,
    bond_return=0.0,
    cash_return=0.0,
    real_estate_return=0.0,
):
    install_market_path(
        monkeypatch,
        equity_return=equity_return,
        bond_return=bond_return,
        cash_return=cash_return,
        real_estate_return=real_estate_return,
    )

    husband = make_person()
    wife = make_person()
    wife_portfolio = make_portfolio()
    expenses = DynamicExpenses()

    sim_config = make_config(
        include_realestate=include_realestate,
        use_fund_expenses=use_fund_expenses,
        fund_expense=fund_expense,
    )

    return simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        num_sims=1,
    )


def test_included_real_estate_receives_market_return(monkeypatch):
    husband_portfolio = make_portfolio(
        real_estate=100_000.0,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        include_realestate=True,
        real_estate_return=0.10,
    )

    assert results["real_estate"][0, 0] == pytest.approx(
        100_000.0
    )
    assert results["real_estate"][0, 1] == pytest.approx(
        110_000.0
    )

    assert results["total_assets"][0, 0] == pytest.approx(
        100_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        110_000.0
    )


def test_excluded_real_estate_is_not_loaded_into_simulation(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        real_estate=100_000.0,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        include_realestate=False,
        real_estate_return=0.10,
    )

    assert results["real_estate"][0, 0] == pytest.approx(0.0)
    assert results["real_estate"][0, 1] == pytest.approx(0.0)
    assert results["total_assets"][0, 0] == pytest.approx(0.0)
    assert results["total_assets"][0, 1] == pytest.approx(0.0)


def test_zero_real_estate_return_preserves_included_value(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        real_estate=75_000.0,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        include_realestate=True,
        real_estate_return=0.0,
    )

    assert results["real_estate"][0, 0] == pytest.approx(
        75_000.0
    )
    assert results["real_estate"][0, 1] == pytest.approx(
        75_000.0
    )


def test_fund_expense_reduces_all_investment_account_buckets(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        equity_pre=10_000.0,
        bond_pre=20_000.0,
        cash_pre=30_000.0,
        equity_post=10_000.0,
        bond_post=20_000.0,
        cash_post=30_000.0,
        equity_roth=10_000.0,
        bond_roth=20_000.0,
        cash_roth=30_000.0,
        hsa_equity=10_000.0,
        hsa_bond=20_000.0,
        hsa_cash=30_000.0,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        use_fund_expenses=True,
        fund_expense=0.01,
    )

    expected_bucket_value = 60_000.0 * 0.99
    expected_total_value = 240_000.0 * 0.99

    assert results["pre_tax_assets"][0, 0] == pytest.approx(
        60_000.0
    )
    assert results["post_tax_assets"][0, 0] == pytest.approx(
        60_000.0
    )
    assert results["roth_assets"][0, 0] == pytest.approx(
        60_000.0
    )
    assert results["hsa_assets"][0, 0] == pytest.approx(
        60_000.0
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        expected_bucket_value
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        expected_bucket_value
    )
    assert results["roth_assets"][0, 1] == pytest.approx(
        expected_bucket_value
    )
    assert results["hsa_assets"][0, 1] == pytest.approx(
        expected_bucket_value
    )

    assert results["total_assets"][0, 1] == pytest.approx(
        expected_total_value
    )


def test_fund_expense_reduces_equity_bonds_and_cash(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        equity_pre=10_000.0,
        bond_pre=20_000.0,
        cash_pre=30_000.0,
        equity_post=10_000.0,
        bond_post=20_000.0,
        cash_post=30_000.0,
        equity_roth=10_000.0,
        bond_roth=20_000.0,
        cash_roth=30_000.0,
        hsa_equity=10_000.0,
        hsa_bond=20_000.0,
        hsa_cash=30_000.0,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        use_fund_expenses=True,
        fund_expense=0.01,
    )

    expected_equity = 40_000.0 * 0.99
    expected_bonds = 80_000.0 * 0.99
    expected_cash = 120_000.0 * 0.99

    actual_equity = (
        results["total_assets"][0, 1]
        - results["bonds"][0, 1]
        - results["cash"][0, 1]
    )

    assert actual_equity == pytest.approx(expected_equity)
    assert results["bonds"][0, 1] == pytest.approx(
        expected_bonds
    )
    assert results["cash"][0, 1] == pytest.approx(
        expected_cash
    )


def test_reported_fund_expense_matches_asset_reduction(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        equity_pre=100_000.0,
        equity_post=50_000.0,
        equity_roth=25_000.0,
        hsa_equity=25_000.0,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        use_fund_expenses=True,
        fund_expense=0.01,
    )

    starting_assets = results["total_assets"][0, 0]
    ending_assets = results["total_assets"][0, 1]
    actual_reduction = starting_assets - ending_assets

    assert starting_assets == pytest.approx(200_000.0)
    assert ending_assets == pytest.approx(198_000.0)
    assert actual_reduction == pytest.approx(2_000.0)

    assert results["fund_expenses"][0, 1] == pytest.approx(
        actual_reduction
    )


def test_fund_expense_does_not_reduce_real_estate(monkeypatch):
    husband_portfolio = make_portfolio(
        equity_pre=100_000.0,
        real_estate=50_000.0,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        include_realestate=True,
        use_fund_expenses=True,
        fund_expense=0.02,
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        98_000.0
    )
    assert results["real_estate"][0, 1] == pytest.approx(
        50_000.0
    )
    assert results["fund_expenses"][0, 1] == pytest.approx(
        2_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        148_000.0
    )


def test_fund_expense_is_applied_after_positive_return(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        equity_pre=100_000.0,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        use_fund_expenses=True,
        fund_expense=0.02,
        equity_return=0.10,
    )

    value_after_return = 100_000.0 * 1.10
    expected_expense = value_after_return * 0.02
    expected_ending_value = value_after_return * 0.98

    assert value_after_return == pytest.approx(110_000.0)
    assert expected_expense == pytest.approx(2_200.0)
    assert expected_ending_value == pytest.approx(107_800.0)

    assert results["fund_expenses"][0, 1] == pytest.approx(
        expected_expense
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        expected_ending_value
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        expected_ending_value
    )


def test_disabled_fund_expenses_do_not_reduce_assets(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        equity_pre=100_000.0,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        use_fund_expenses=False,
        fund_expense=0.05,
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        100_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        100_000.0
    )
    assert results["fund_expenses"][0, 1] == pytest.approx(
        0.0
    )


def test_zero_fund_expense_rate_does_not_reduce_assets(
    monkeypatch,
):
    husband_portfolio = make_portfolio(
        equity_pre=100_000.0,
    )

    results = run_one_year(
        monkeypatch,
        husband_portfolio,
        use_fund_expenses=True,
        fund_expense=0.0,
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        100_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        100_000.0
    )
    assert results["fund_expenses"][0, 1] == pytest.approx(
        0.0
    )