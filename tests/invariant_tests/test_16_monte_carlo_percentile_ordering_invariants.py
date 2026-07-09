import numpy as np
import pytest

from src.warpsimlab.sim.simulation import run_pipeline


# pytest.skip("Skipping invariant tests for now", allow_module_level=True)



EPS = 1e-9


def run_case(make_case, **overrides):
    husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config = make_case(
        subplot_mode="monte_carlo",
        num_sims=25,
        years_to_simulate=5,
        **overrides,
    )

    result = run_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
    )

    return result, sim_config


def test_monte_carlo_percentiles_are_ordered(make_case):
    result, cfg = run_case(make_case)

    percentiles = result["portfolio_plot_data"].percentiles

    np.testing.assert_array_less(percentiles["pct10"] - EPS, percentiles["median"] + EPS)
    np.testing.assert_array_less(percentiles["median"] - EPS, percentiles["pct90"] + EPS)


def test_monte_carlo_percentile_shapes_match_years(make_case):
    result, cfg = run_case(make_case)

    years_list = result["years_list"]
    percentiles = result["portfolio_plot_data"].percentiles

    assert percentiles["pct10"].shape == years_list.shape
    assert percentiles["median"].shape == years_list.shape
    assert percentiles["pct90"].shape == years_list.shape


def test_monte_carlo_overlay_shapes_match_baseline_when_present(make_case):
    result, cfg = run_case(
        make_case,
        overlay_tax_impacts=True,
        overlay_fund_expense_impacts=True,
    )

    plot_data = result["portfolio_plot_data"]
    baseline = plot_data.percentiles["median"]

    if plot_data.median_without_taxes is not None:
        assert plot_data.median_without_taxes.shape == baseline.shape

    if plot_data.median_without_fund_expenses is not None:
        assert plot_data.median_without_fund_expenses.shape == baseline.shape

    if plot_data.median_without_taxes_or_fund_expenses is not None:
        assert plot_data.median_without_taxes_or_fund_expenses.shape == baseline.shape