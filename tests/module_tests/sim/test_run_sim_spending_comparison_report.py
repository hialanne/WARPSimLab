from __future__ import annotations

import numpy as np
import pytest

from src.warpsimlab.sim import run_sim_spending_comparison_report as mod


def test_distribution_returns_zeroes_for_empty_values():
    result = mod._distribution([])

    assert result == {
        "minimum": 0.0,
        "10th_percentile": 0.0,
        "25th_percentile": 0.0,
        "median": 0.0,
        "75th_percentile": 0.0,
        "90th_percentile": 0.0,
        "maximum": 0.0,
    }


def test_distribution_calculates_expected_statistics():
    result = mod._distribution([0.0, 100.0, 200.0, 300.0, 400.0])

    assert result["minimum"] == pytest.approx(0.0)
    assert result["10th_percentile"] == pytest.approx(40.0)
    assert result["25th_percentile"] == pytest.approx(100.0)
    assert result["median"] == pytest.approx(200.0)
    assert result["75th_percentile"] == pytest.approx(300.0)
    assert result["90th_percentile"] == pytest.approx(360.0)
    assert result["maximum"] == pytest.approx(400.0)


def test_build_depletion_statistics_counts_depleted_windows():
    total_assets = np.array(
        [
            [100.0, 80.0, 0.0],
            [100.0, 90.0, 70.0],
            [100.0, 40.0, 0.0],
        ]
    )
    years = np.array([2026, 2027, 2028])

    result = mod._build_depletion_statistics(total_assets, years)

    assert result["historical_window_count"] == 3
    assert result["windows_reaching_zero_count"] == 2
    assert result["windows_reaching_zero_percent"] == pytest.approx(200.0 / 3.0)
    assert result["earliest_reaching_zero_year"] == 2028
    assert result["median_reaching_zero_year"] == 2028
    assert result["latest_reaching_zero_year"] == 2028


def test_build_depletion_statistics_handles_no_depletion():
    total_assets = np.array(
        [
            [100.0, 90.0, 80.0],
            [100.0, 110.0, 120.0],
        ]
    )
    years = np.array([2026, 2027, 2028])

    result = mod._build_depletion_statistics(total_assets, years)

    assert result["historical_window_count"] == 2
    assert result["windows_reaching_zero_count"] == 0
    assert result["windows_reaching_zero_percent"] == pytest.approx(0.0)
    assert result["earliest_reaching_zero_year"] is None
    assert result["median_reaching_zero_year"] is None
    assert result["latest_reaching_zero_year"] is None


def test_build_case_result_calculates_deterministic_financial_totals():
    deterministic_pipeline_result = {
        "core": {
            "total_assets": np.array([[100000.0, 90000.0, 80000.0]]),
            "expense_amt": np.array([[0.0, 40000.0, 42000.0]]),
            "taxes": np.array([[0.0, 5000.0, 6000.0]]),
            "cash_flow_shortfall": np.array([[0.0, 10000.0, 12000.0]]),
            "uncovered_expense": np.array([[0.0, 0.0, 2000.0]]),
        }
    }

    historical_pipeline_result = {
        "core": {
            "total_assets": np.array(
                [
                    [100000.0, 90000.0, 80000.0],
                    [100000.0, 50000.0, 0.0],
                ]
            ),
            "year": np.array(
                [
                    [2026, 2027, 2028],
                    [2026, 2027, 2028],
                ]
            ),
        }
    }

    result = mod._build_case_result(
        100.0,
        deterministic_pipeline_result,
        historical_pipeline_result,
    )

    assert result["spending_percentage"] == pytest.approx(100.0)
    assert result["scenario_expense_multiplier"] == pytest.approx(1.0)
    assert result["is_current_spending"] is True

    assert result["deterministic_ending_portfolio"] == pytest.approx(80000.0)
    assert result["deterministic_first_year_expenses"] == pytest.approx(40000.0)
    assert result["deterministic_lifetime_expenses"] == pytest.approx(82000.0)
    assert result["deterministic_lifetime_taxes"] == pytest.approx(11000.0)
    assert result["deterministic_lifetime_cash_flow_shortfall"] == pytest.approx(22000.0)
    assert result["deterministic_lifetime_uncovered_expense"] == pytest.approx(2000.0)

    assert result["depletion"]["historical_window_count"] == 2
    assert result["depletion"]["windows_reaching_zero_count"] == 1
    assert result["depletion"]["windows_reaching_zero_percent"] == pytest.approx(50.0)

    assert result["ending_portfolio"]["minimum"] == pytest.approx(0.0)
    assert result["ending_portfolio"]["median"] == pytest.approx(40000.0)
    assert result["ending_portfolio"]["maximum"] == pytest.approx(80000.0)


def test_build_case_result_marks_nonbaseline_spending():
    deterministic_pipeline_result = {
        "core": {
            "total_assets": np.array([[100.0, 80.0]]),
            "expense_amt": np.array([[0.0, 20.0]]),
            "taxes": np.array([[0.0, 5.0]]),
            "cash_flow_shortfall": np.array([[0.0, 0.0]]),
            "uncovered_expense": np.array([[0.0, 0.0]]),
        }
    }

    historical_pipeline_result = {
        "core": {
            "total_assets": np.array([[100.0, 80.0]]),
            "year": np.array([[2026, 2027]]),
        }
    }

    result = mod._build_case_result(
        80.0,
        deterministic_pipeline_result,
        historical_pipeline_result,
    )

    assert result["spending_percentage"] == pytest.approx(80.0)
    assert result["scenario_expense_multiplier"] == pytest.approx(0.8)
    assert result["is_current_spending"] is False