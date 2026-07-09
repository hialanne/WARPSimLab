# test_plotYearlyIncome.py

import types
import matplotlib
matplotlib.use("Agg")  # safety if conftest.py not set yet

import matplotlib.pyplot as plt
import matplotlib.collections as mcoll
import numpy as np
import pytest

from src.warpsimlab.plots.plotYearlyIncome import draw_yearly_income


def make_person(age, retire_age):
    return types.SimpleNamespace(age=age, retire_age=retire_age)


def make_config(
    *,
    start_year=2025,
    inflation_rate=0.02,
    plot_mode="nominal",
    subplot_mode="total",
    sim_type="income_sim",
    annotate_plots=False,
    always_use_expense_mode=True,
    overlay_household_expenses=False,
    overlay_profit_loss=False,
    overlay_retirement_age=False,
    second_person_enabled=False,
    use_snapshot_annotations=False,
    annotation_strings=None,
):
    if annotation_strings is None:
        annotation_strings = []

    return types.SimpleNamespace(
        start_year=start_year,
        inflation_rate=inflation_rate,
        plot_mode=plot_mode,
        subplot_mode=subplot_mode,
        sim_type=sim_type,
        annotate_plots=annotate_plots,
        always_use_expense_mode=always_use_expense_mode,
        overlay_household_expenses=overlay_household_expenses,
        overlay_profit_loss=overlay_profit_loss,
        overlay_retirement_age=overlay_retirement_age,
        second_person_enabled=second_person_enabled,
        use_snapshot_annotations=use_snapshot_annotations,
        annotation_strings=annotation_strings,
    )

def _vertical_lines(ax):
    out = []
    for ln in ax.lines:
        x = ln.get_xdata()
        if len(x) >= 2 and x[0] == x[1]:
            out.append(ln)
    return out


def test_draw_yearly_income_total_mode_draws_one_bar_series():
    years_to_simulate = 3
    xlen = years_to_simulate + 1

    breakdown = {
        "work": [0] * xlen,
        "pension": [0] * xlen,
        "annuity": [0] * xlen,
        "ss": [0] * xlen,
        "rmd": [0] * xlen,
        "withdrawal": [0] * xlen,
    }

    net_income = np.array([10, 20, 30, 40], dtype=float)

    fig, ax = plt.subplots()
    draw_yearly_income(
        ax=ax,
        years_to_simulate=years_to_simulate,
        net_profit=[0] * xlen,
        net_income=net_income,
        breakdown=breakdown,
        taxes=[0] * xlen,
        expenses=[0] * xlen,
        husband=make_person(age=40, retire_age=65),
        wife=None,
        sim_config=make_config(subplot_mode="total", always_use_expense_mode=True),
    )

    bars = [p for p in ax.patches if p.get_width() > 0]
    assert len(bars) == xlen


def test_draw_yearly_income_sub_categories_draws_stacked_bars():
    years_to_simulate = 2
    xlen = years_to_simulate + 1

    breakdown = {
        "work": [10, 10, 10],
        "pension": [1, 1, 1],
        "annuity": [2, 2, 2],
        "ss": [3, 3, 3],
        "special_income": [4, 4, 4],
    }

    fig, ax = plt.subplots()
    draw_yearly_income(
        ax=ax,
        years_to_simulate=years_to_simulate,
        net_profit=[0] * xlen,
        net_income=None,
        breakdown=breakdown,
        taxes=[0] * xlen,
        expenses=[0] * xlen,
        husband=make_person(age=40, retire_age=65),
        wife=None,
        sim_config=make_config(subplot_mode="sub_categories", always_use_expense_mode=True),
    )

    # Stacked: 6 categories * 3 years = 18 bars
    bars = [p for p in ax.patches if p.get_width() > 0]
    assert len(bars) == 5 * xlen


def test_draw_yearly_income_expense_overlay_draws_hlines():
    years_to_simulate = 2
    xlen = years_to_simulate + 1

    breakdown = {
        "work": [0] * xlen,
        "pension": [0] * xlen,
        "annuity": [0] * xlen,
        "ss": [0] * xlen,
        "rmd": [0] * xlen,
        "withdrawal": [0] * xlen,
    }

    expenses = [0, 100, 200]

    fig, ax = plt.subplots()
    draw_yearly_income(
        ax=ax,
        years_to_simulate=years_to_simulate,
        net_profit=[0] * xlen,
        net_income=np.array([0, 0, 0], dtype=float),
        breakdown=breakdown,
        taxes=[0] * xlen,
        expenses=expenses,
        husband=make_person(age=40, retire_age=65),
        wife=None,
        sim_config=make_config(
            always_use_expense_mode=True,
            overlay_household_expenses=True,
            subplot_mode="total",
        ),
    )

    # plt.hlines creates LineCollections
    hline_collections = [c for c in ax.collections if isinstance(c, mcoll.LineCollection)]
    assert hline_collections, "Expected LineCollection(s) from expense overlay"


def test_draw_yearly_income_profit_loss_overlay_adds_lines():
    years_to_simulate = 3
    xlen = years_to_simulate + 1

    breakdown = {
        "work": [0] * xlen,
        "pension": [0] * xlen,
        "annuity": [0] * xlen,
        "ss": [0] * xlen,
        "rmd": [0] * xlen,
        "withdrawal": [0] * xlen,
    }

    # year0 ignored by overlay; remaining include a zero crossing
    net_profit = [0, 10, -10, 5]

    fig, ax = plt.subplots()
    draw_yearly_income(
        ax=ax,
        years_to_simulate=years_to_simulate,
        net_profit=net_profit,
        net_income=np.array([0, 0, 0, 0], dtype=float),
        breakdown=breakdown,
        taxes=[0] * xlen,
        expenses=[0] * xlen,
        husband=make_person(age=40, retire_age=65),
        wife=None,
        sim_config=make_config(
            always_use_expense_mode=True,
            overlay_profit_loss=True,
            subplot_mode="total",
            sim_type="cashflow_sim",
        ),
    )

    # Overlay draws multiple line segments + two empty legend helper lines
    assert len(ax.lines) >= 2


def test_draw_yearly_income_retirement_overlay_single_person():
    years_to_simulate = 10
    xlen = years_to_simulate + 1

    breakdown = {
        "work": [0] * xlen,
        "pension": [0] * xlen,
        "annuity": [0] * xlen,
        "ss": [0] * xlen,
        "rmd": [0] * xlen,
        "withdrawal": [0] * xlen,
    }

    husband = make_person(age=60, retire_age=65)  # index 5
    cfg = make_config(
        always_use_expense_mode=True,
        overlay_retirement_age=True,
        subplot_mode="total",
    )

    fig, ax = plt.subplots()
    draw_yearly_income(
        ax=ax,
        years_to_simulate=years_to_simulate,
        net_profit=[0] * xlen,
        net_income=np.array([0] * xlen, dtype=float),
        breakdown=breakdown,
        taxes=[0] * xlen,
        expenses=[0] * xlen,
        husband=husband,
        wife=None,
        sim_config=cfg,
    )

    vlines = _vertical_lines(ax)
    assert vlines
    assert any(line.get_xdata()[0] == 5 for line in vlines)


def test_draw_yearly_income_retirement_overlay_couple_uses_later_retirement():
    years_to_simulate = 20
    xlen = years_to_simulate + 1

    breakdown = {
        "work": [0] * xlen,
        "pension": [0] * xlen,
        "annuity": [0] * xlen,
        "ss": [0] * xlen,
        "rmd": [0] * xlen,
        "withdrawal": [0] * xlen,
    }

    husband = make_person(age=50, retire_age=60)  # 10
    wife = make_person(age=50, retire_age=65)     # 15
    cfg = make_config(
        always_use_expense_mode=True,
        overlay_retirement_age=True,
        subplot_mode="total",
        second_person_enabled=True,
    )

    fig, ax = plt.subplots()
    draw_yearly_income(
        ax=ax,
        years_to_simulate=years_to_simulate,
        net_profit=[0] * xlen,
        net_income=np.array([0] * xlen, dtype=float),
        breakdown=breakdown,
        taxes=[0] * xlen,
        expenses=[0] * xlen,
        husband=husband,
        wife=wife,
        sim_config=cfg,
    )

    vlines = _vertical_lines(ax)
    assert vlines
    assert any(line.get_xdata()[0] == 15 for line in vlines)