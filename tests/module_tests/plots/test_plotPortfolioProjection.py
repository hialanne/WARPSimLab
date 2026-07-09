# test_plotPortfolioProjection.py

import types
import matplotlib
matplotlib.use("Agg")  # safety if conftest.py not set yet

import matplotlib.pyplot as plt
import numpy as np
import pytest

from src.warpsimlab.plots.plotPortfolioProjection import draw_portfolio_projection


def make_person(age, retire_age):
    return types.SimpleNamespace(age=age, retire_age=retire_age)


def make_config(
    *,
    plot_mode="nominal",
    subplot_mode="pre_post_tax",
    years_to_simulate=3,
    constant_y_plots=False,
    overlay_tax_impacts=False,
    overlay_fund_expense_impacts=False,
    overlay_retirement_age=False,
    second_person_enabled=False,
    use_snapshot_annotations=False,
    annotation_strings=None,
):
    if annotation_strings is None:
        annotation_strings = []
    return types.SimpleNamespace(
        plot_mode=plot_mode,
        subplot_mode=subplot_mode,
        years_to_simulate=years_to_simulate,
        constant_y_plots=constant_y_plots,
        overlay_tax_impacts=overlay_tax_impacts,
        overlay_fund_expense_impacts=overlay_fund_expense_impacts,
        overlay_retirement_age=overlay_retirement_age,
        second_person_enabled=second_person_enabled,
        use_snapshot_annotations=use_snapshot_annotations,
        annotation_strings=annotation_strings,
    )


class DummySimulationData:
    """
    Minimal plotPortfolioProjection-compatible object.
    """
    def __init__(
        self,
        *,
        median,
        pre_tax_assets=None,
        post_tax_assets=None,
        realestate=None,
        median_without_taxes=None,
        median_without_fund_expenses=None,
        median_without_taxes_or_fund_expenses=None,
    ):
        self.percentiles = {"median": np.array(median)}
        self.pre_tax_assets = None if pre_tax_assets is None else np.array(pre_tax_assets)
        self.post_tax_assets = None if post_tax_assets is None else np.array(post_tax_assets)
        self.realestate = None if realestate is None else np.array(realestate)

        # overlays expect these attributes if enabled
        self.median_without_taxes = median_without_taxes
        self.median_without_fund_expenses = median_without_fund_expenses
        self.median_without_taxes_or_fund_expenses = median_without_taxes_or_fund_expenses


def _vertical_lines(ax):
    # Lines with constant xdata (axvline)
    out = []
    for line in ax.lines:
        xdata = line.get_xdata()
        if len(xdata) >= 2 and xdata[0] == xdata[1]:
            out.append(line)
    return out


def test_draw_portfolio_projection_pre_post_tax_creates_fills_and_line():
    years = [0, 1, 2, 3]
    sim = DummySimulationData(
        median=[100, 110, 120, 130],
        post_tax_assets=[60, 60, 60, 60],
        pre_tax_assets=[40, 50, 60, 70],
        realestate=None,
    )
    cfg = make_config(subplot_mode="pre_post_tax", years_to_simulate=3)

    fig, ax = plt.subplots()
    draw_portfolio_projection(ax, years, sim, sim_config=cfg)

    # fill_between makes PolyCollections stored in ax.collections
    assert len(ax.collections) >= 2  # post + pre fills at minimum

    # baseline median line exists (Line2D)
    assert any(len(line.get_xdata()) == len(years) for line in ax.lines)


def test_draw_portfolio_projection_baseline_line_turns_red_when_near_zero():
    years = [0, 1, 2]
    sim = DummySimulationData(
        median=[100, 0.0, 50],  # includes near zero -> baseline line should be red
        post_tax_assets=[50, 0, 25],
        pre_tax_assets=[50, 0, 25],
    )
    cfg = make_config(subplot_mode="pre_post_tax", years_to_simulate=2)

    fig, ax = plt.subplots()
    draw_portfolio_projection(ax, years, sim, sim_config=cfg)

    # baseline line is the one with ydata == median
    median = np.array(sim.percentiles["median"])
    baseline_lines = [ln for ln in ax.lines if np.array_equal(np.array(ln.get_ydata()), median)]
    assert baseline_lines, "Expected a baseline line plotted for median values"
    assert baseline_lines[0].get_color() == "red"


def test_draw_portfolio_projection_overlay_retirement_single_person():
    years = list(range(0, 11))  # 0..10
    sim = DummySimulationData(
        median=[100] * 11,
        post_tax_assets=[60] * 11,
        pre_tax_assets=[40] * 11,
    )
    husband = make_person(age=60, retire_age=65)  # index 5
    cfg = make_config(subplot_mode="pre_post_tax", years_to_simulate=10, overlay_retirement_age=True)

    fig, ax = plt.subplots()
    draw_portfolio_projection(ax, years, sim, sim_config=cfg, husband=husband, wife=None)

    vlines = _vertical_lines(ax)
    assert vlines
    assert any(line.get_xdata()[0] == 5 for line in vlines)


def test_draw_portfolio_projection_overlay_retirement_couple_uses_later_retirement():
    years = list(range(0, 21))  # 0..20
    sim = DummySimulationData(
        median=[100] * 21,
        post_tax_assets=[60] * 21,
        pre_tax_assets=[40] * 21,
    )
    husband = make_person(age=50, retire_age=60)  # 10
    wife = make_person(age=50, retire_age=65)     # 15 (later)
    cfg = make_config(
        subplot_mode="pre_post_tax",
        years_to_simulate=20,
        overlay_retirement_age=True,
        second_person_enabled=True,
    )

    fig, ax = plt.subplots()
    draw_portfolio_projection(ax, years, sim, sim_config=cfg, husband=husband, wife=wife)

    vlines = _vertical_lines(ax)
    assert vlines
    assert any(line.get_xdata()[0] == 15 for line in vlines)


def test_draw_portfolio_projection_overlay_tax_impacts_adds_fill():
    years = [0, 1, 2]
    median = np.array([100, 110, 120])
    without_taxes = np.array([105, 120, 140])

    sim = DummySimulationData(
        median=median,
        post_tax_assets=[60, 60, 60],
        pre_tax_assets=[40, 50, 60],
        median_without_taxes=without_taxes,
    )

    cfg = make_config(
        subplot_mode="pre_post_tax",
        years_to_simulate=2,
        overlay_tax_impacts=True,
        overlay_fund_expense_impacts=False,
    )

    fig, ax = plt.subplots()
    draw_portfolio_projection(ax, years, sim, sim_config=cfg)

    # Overlays are fill_between calls -> additional PolyCollections
    assert len(ax.collections) >= 3


def test_draw_portfolio_projection_sub_categories_handles_missing_cash_bonds_realestate():
    years = [0, 1, 2, 3]
    sim = DummySimulationData(
        median=[100, 110, 120, 130],
        # sub_categories uses cash/bonds/realestate via getattr; omit them to ensure it doesn't crash
        post_tax_assets=None,
        pre_tax_assets=None,
        realestate=None,
    )

    cfg = make_config(subplot_mode="sub_categories", years_to_simulate=3)
    cfg.include_realestate = False  # required by _plot_sub_category_assets

    fig, ax = plt.subplots()
    draw_portfolio_projection(ax, years, sim, sim_config=cfg)

    # should draw stacked areas => at least one collection
    assert len(ax.collections) >= 1