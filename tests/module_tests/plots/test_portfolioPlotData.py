# test_portfolioPlotData.py

import numpy as np

from src.warpsimlab.plots.portfolioPlotData import PortfolioPlotData


def test_portfolio_plot_data_converts_years_to_numpy():
    data = PortfolioPlotData(
        years=[2025, 2026, 2027],
        percentiles={"median": [100, 110, 120]}
    )

    assert isinstance(data.years, np.ndarray)
    assert np.array_equal(data.years, np.array([2025, 2026, 2027]))


def test_portfolio_plot_data_converts_percentiles_to_numpy():
    data = PortfolioPlotData(
        years=[2025, 2026],
        percentiles={
            "median": [100, 200],
            "pct10": [80, 150]
        }
    )

    assert isinstance(data.percentiles["median"], np.ndarray)
    assert isinstance(data.percentiles["pct10"], np.ndarray)

    assert np.array_equal(data.percentiles["median"], np.array([100, 200]))
    assert np.array_equal(data.percentiles["pct10"], np.array([80, 150]))


def test_optional_arrays_are_converted_when_present():
    data = PortfolioPlotData(
        years=[1, 2],
        percentiles={"median": [10, 20]},
        cash=[1, 2],
        bonds=[3, 4],
        realestate=[5, 6],
        pre_tax_assets=[7, 8],
        post_tax_assets=[9, 10]
    )

    assert isinstance(data.cash, np.ndarray)
    assert isinstance(data.bonds, np.ndarray)
    assert isinstance(data.realestate, np.ndarray)
    assert isinstance(data.pre_tax_assets, np.ndarray)
    assert isinstance(data.post_tax_assets, np.ndarray)


def test_optional_fields_remain_none_when_not_provided():
    data = PortfolioPlotData(
        years=[1, 2],
        percentiles={"median": [10, 20]}
    )

    assert data.cash is None
    assert data.bonds is None
    assert data.realestate is None
    assert data.pre_tax_assets is None
    assert data.post_tax_assets is None


def test_median_without_variants_are_converted():
    data = PortfolioPlotData(
        years=[1, 2],
        percentiles={"median": [10, 20]},
        median_without_fund_expenses=[9, 18],
        median_without_taxes=[8, 16],
        median_without_taxes_or_fund_expenses=[7, 14]
    )

    assert isinstance(data.median_without_fund_expenses, np.ndarray)
    assert isinstance(data.median_without_taxes, np.ndarray)
    assert isinstance(data.median_without_taxes_or_fund_expenses, np.ndarray)

    assert np.array_equal(data.median_without_fund_expenses, np.array([9, 18]))
    assert np.array_equal(data.median_without_taxes, np.array([8, 16]))
    assert np.array_equal(data.median_without_taxes_or_fund_expenses, np.array([7, 14]))