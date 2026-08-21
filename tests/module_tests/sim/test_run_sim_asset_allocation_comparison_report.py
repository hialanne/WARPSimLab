from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.sim import run_sim_asset_allocation_comparison_report as mod


def test_portfolio_components_combines_all_account_types():
    portfolio = SimpleNamespace(
        equity_pre=100.0,
        equity_post=200.0,
        equity_roth=300.0,
        hsa_equity=400.0,
        bond_pre=10.0,
        bond_post=20.0,
        bond_roth=30.0,
        hsa_bond=40.0,
        cash_pre=1.0,
        cash_post=2.0,
        cash_roth=3.0,
        hsa_cash=4.0,
    )

    equity, bonds, cash = mod._portfolio_components(portfolio)

    assert equity == pytest.approx(1000.0)
    assert bonds == pytest.approx(100.0)
    assert cash == pytest.approx(10.0)


def test_portfolio_components_none_returns_zeroes():
    assert mod._portfolio_components(None) == (0.0, 0.0, 0.0)


def test_current_household_allocation_single_person_ignores_wife():
    husband_portfolio = SimpleNamespace(
        equity_pre=60.0,
        bond_pre=30.0,
        cash_pre=10.0,
    )

    wife_portfolio = SimpleNamespace(
        equity_pre=1000.0,
        bond_pre=0.0,
        cash_pre=0.0,
    )

    sim_config = SimpleNamespace(
        second_person_enabled=False,
    )

    result = mod._current_household_allocation(
        husband_portfolio,
        wife_portfolio,
        sim_config,
    )

    assert result["equity"] == pytest.approx(0.60)
    assert result["bonds"] == pytest.approx(0.30)
    assert result["cash"] == pytest.approx(0.10)


def test_current_household_allocation_combines_couple():
    husband_portfolio = SimpleNamespace(
        equity_pre=60.0,
        bond_pre=30.0,
        cash_pre=10.0,
    )

    wife_portfolio = SimpleNamespace(
        equity_pre=40.0,
        bond_pre=30.0,
        cash_pre=30.0,
    )

    sim_config = SimpleNamespace(
        second_person_enabled=True,
    )

    result = mod._current_household_allocation(
        husband_portfolio,
        wife_portfolio,
        sim_config,
    )

    assert result["equity"] == pytest.approx(0.50)
    assert result["bonds"] == pytest.approx(0.30)
    assert result["cash"] == pytest.approx(0.20)


def test_current_household_allocation_empty_portfolio_defaults_to_cash():
    sim_config = SimpleNamespace(
        second_person_enabled=False,
    )

    result = mod._current_household_allocation(
        None,
        None,
        sim_config,
    )

    assert result["equity"] == pytest.approx(0.0)
    assert result["bonds"] == pytest.approx(0.0)
    assert result["cash"] == pytest.approx(1.0)


def test_derive_allocation_preserves_existing_bond_cash_ratio():
    current_allocation = {
        "equity": 0.60,
        "bonds": 0.30,
        "cash": 0.10,
    }

    result = mod._derive_allocation(
        0.50,
        current_allocation,
    )

    assert result["equity"] == pytest.approx(0.50)
    assert result["bonds"] == pytest.approx(0.375)
    assert result["cash"] == pytest.approx(0.125)

    assert (
        result["equity"]
        + result["bonds"]
        + result["cash"]
    ) == pytest.approx(1.0)


def test_derive_allocation_all_equity_accepts_100_percent_equity():
    current_allocation = {
        "equity": 1.0,
        "bonds": 0.0,
        "cash": 0.0,
    }

    result = mod._derive_allocation(
        1.0,
        current_allocation,
    )

    assert result == {
        "equity": 1.0,
        "bonds": 0.0,
        "cash": 0.0,
    }


def test_derive_allocation_all_equity_cannot_invent_bond_cash_split():
    current_allocation = {
        "equity": 1.0,
        "bonds": 0.0,
        "cash": 0.0,
    }

    with pytest.raises(
        ValueError,
        match="contains no bonds or cash",
    ):
        mod._derive_allocation(
            0.80,
            current_allocation,
        )


def test_build_depletion_statistics_counts_windows_and_years():
    total_assets = np.array(
        [
            [100.0, 80.0, 60.0],
            [100.0, 50.0, 0.0],
            [100.0, 0.0, 0.0],
            [100.0, 120.0, 140.0],
        ]
    )
    years = np.array([2026, 2027, 2028])

    result = mod._build_depletion_statistics(
        total_assets,
        years,
    )

    assert result["historical_window_count"] == 4
    assert result["windows_reaching_zero_count"] == 2
    assert result["windows_reaching_zero_percent"] == pytest.approx(50.0)
    assert result["earliest_reaching_zero_year"] == 2027
    assert result["latest_reaching_zero_year"] == 2028


def test_find_historical_plot_cases_uses_actual_current_case():
    cases = [
        {
            "equity_percentage": 40.0,
            "is_current_allocation": False,
        },
        {
            "equity_percentage": 60.0,
            "is_current_allocation": False,
        },
        {
            "equity_percentage": 80.0,
            "is_current_allocation": False,
        },
        {
            "equity_percentage": 60.0,
            "is_current_allocation": True,
        },
    ]

    result = mod._find_historical_plot_cases(
        cases,
        current_equity_percentage=60.0,
    )

    assert result["minus_20"]["equity_percentage"] == pytest.approx(40.0)
    assert result["plus_20"]["equity_percentage"] == pytest.approx(80.0)

    assert result["current"]["equity_percentage"] == pytest.approx(60.0)
    assert result["current"]["is_current_allocation"] is True


def test_build_shared_historical_plot_limits_uses_all_three_cases():
    plot_cases = {
        "minus_20": {
            "historical_portfolio_plot_data": SimpleNamespace(
                years=np.array([0.0, 1.0, 2.0]),
                percentiles={
                    "pct99": np.array([100.0, 200.0, 300.0]),
                },
            )
        },
        "current": {
            "historical_portfolio_plot_data": SimpleNamespace(
                years=np.array([0.0, 1.0, 2.0]),
                percentiles={
                    "pct99": np.array([100.0, 400.0, 500.0]),
                },
            )
        },
        "plus_20": {
            "historical_portfolio_plot_data": SimpleNamespace(
                years=np.array([0.0, 1.0, 2.0]),
                percentiles={
                    "pct99": np.array([150.0, 250.0, 350.0]),
                },
            )
        },
    }

    result = mod._build_shared_historical_plot_limits(
        plot_cases
    )

    assert result["x_min"] == pytest.approx(0.0)
    assert result["x_max"] == pytest.approx(2.0)
    assert result["y_min"] == pytest.approx(0.0)
    assert result["y_max"] == pytest.approx(525.0)