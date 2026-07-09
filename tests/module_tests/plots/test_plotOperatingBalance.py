# test_plotOperatingBalance.py

import types
import matplotlib
matplotlib.use("Agg")  # safety if conftest.py not set yet

import matplotlib.pyplot as plt
import pytest

from src.warpsimlab.plots.plotOperatingBalance import draw_operating_balance


def make_person(age, retire_age):
    return types.SimpleNamespace(age=age, retire_age=retire_age)


def make_config(
    *,
    start_year=2025,
    inflation_rate=0.02,
    plot_mode="nominal",
    overlay_retirement_age=False,
    second_person_enabled=False,
):
    return types.SimpleNamespace(
        start_year=start_year,
        inflation_rate=inflation_rate,
        plot_mode=plot_mode,
        overlay_retirement_age=overlay_retirement_age,
        second_person_enabled=second_person_enabled,
    )


def _rgba_tuple(color):
    # Normalize facecolor to RGBA tuple
    if isinstance(color, tuple):
        return color
    return tuple(color)


def test_draw_operating_balance_draws_expected_number_of_bars():
    years_to_simulate = 3
    operating_balance = [0, 10, -5, -20]
    portfolio_value = [0, 0, 10, 10]  # last year deficit (20) exceeds portfolio (10)

    fig, ax = plt.subplots()

    draw_operating_balance(
        ax=ax,
        years_to_simulate=years_to_simulate,
        net_profit=[0, 0, 0, 0],
        operating_balance=operating_balance,
        portfolio_value=portfolio_value,
        husband=make_person(age=40, retire_age=65),
        wife=None,
        sim_config=make_config(overlay_retirement_age=False),
    )

    # Matplotlib bars are Rectangle patches; filter out non-bar patches
    bar_patches = [p for p in ax.patches if p.get_width() > 0]
    assert len(bar_patches) == years_to_simulate + 1


def test_draw_operating_balance_color_logic_positive_covered_uncovered():
    """
    Color rules (per code):
      - skyblue when operating_balance >= 0
      - orange when operating_balance < 0 and portfolio_value >= deficit
      - red when operating_balance < 0 and portfolio_value < deficit
    """
    years_to_simulate = 2
    operating_balance = [5, -10, -10]
    portfolio_value = [0, 10, 9]  # year1 covered (deficit=10, pv=10), year2 uncovered (pv=9)

    fig, ax = plt.subplots()

    draw_operating_balance(
        ax=ax,
        years_to_simulate=years_to_simulate,
        net_profit=[0, 0, 0],
        operating_balance=operating_balance,
        portfolio_value=portfolio_value,
        husband=make_person(age=40, retire_age=65),
        wife=None,
        sim_config=make_config(overlay_retirement_age=False),
    )

    bars = [p for p in ax.patches if p.get_width() > 0]
    assert len(bars) == 3

    # Compare RGBA values (stable)
    skyblue = matplotlib.colors.to_rgba("skyblue")
    orange = matplotlib.colors.to_rgba("orange")
    red = matplotlib.colors.to_rgba("red")

    assert _rgba_tuple(bars[0].get_facecolor()) == pytest.approx(skyblue)
    assert _rgba_tuple(bars[1].get_facecolor()) == pytest.approx(orange)
    assert _rgba_tuple(bars[2].get_facecolor()) == pytest.approx(red)


def test_draw_operating_balance_retirement_overlay_single_person():
    years_to_simulate = 10
    husband = make_person(age=60, retire_age=65)  # retirement_index = 5
    cfg = make_config(overlay_retirement_age=True, second_person_enabled=False)

    fig, ax = plt.subplots()

    draw_operating_balance(
        ax=ax,
        years_to_simulate=years_to_simulate,
        net_profit=[0] * (years_to_simulate + 1),
        operating_balance=[0] * (years_to_simulate + 1),
        portfolio_value=[0] * (years_to_simulate + 1),
        husband=husband,
        wife=None,
        sim_config=cfg,
    )

    # Retirement overlay is an axvline -> a Line2D in ax.lines with constant xdata
    vertical_lines = []
    for line in ax.lines:
        xdata = line.get_xdata()
        if len(xdata) >= 2 and xdata[0] == xdata[1]:
            vertical_lines.append(line)

    assert len(vertical_lines) >= 1
    # At least one vertical line should be at x=5
    assert any(line.get_xdata()[0] == 5 for line in vertical_lines)


def test_draw_operating_balance_retirement_overlay_couple_uses_later_retirement():
    years_to_simulate = 20
    husband = make_person(age=50, retire_age=60)  # index 10
    wife = make_person(age=50, retire_age=65)     # index 15 (later)
    cfg = make_config(overlay_retirement_age=True, second_person_enabled=True)

    fig, ax = plt.subplots()

    draw_operating_balance(
        ax=ax,
        years_to_simulate=years_to_simulate,
        net_profit=[0] * (years_to_simulate + 1),
        operating_balance=[0] * (years_to_simulate + 1),
        portfolio_value=[0] * (years_to_simulate + 1),
        husband=husband,
        wife=wife,
        sim_config=cfg,
    )

    vertical_lines = []
    for line in ax.lines:
        xdata = line.get_xdata()
        if len(xdata) >= 2 and xdata[0] == xdata[1]:
            vertical_lines.append(line)

    assert len(vertical_lines) >= 1
    assert any(line.get_xdata()[0] == 15 for line in vertical_lines)