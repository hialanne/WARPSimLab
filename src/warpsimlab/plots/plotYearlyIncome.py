# plotYearlyIncome.py

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import tkinter as tk
from tkinter import ttk

from src.warpsimlab.utils.constants import *
from src.warpsimlab.dataClasses.portfolioState import *


# Color constants
COLOR_HUSBAND = "blue"
COLOR_WIFE = "green"
COLOR_TOTAL_REAL = "blue"
COLOR_TOTAL_NOMINAL = "darkblue"
COLOR_REALESTATE = "brown"
COLOR_FUND_EXPENSES = "orange"
COLOR_YEARLY_INCOME = "skyblue"
COLOR_NET_PROFIT = "red"
COLOR_PENSION = "orange"
COLOR_ANNUITY = "gold"
COLOR_SS = "green"
COLOR_RMD = "purple"
COLOR_PRE_TAX = "lightgreen"
COLOR_POST_TAX = "lightcoral"


def draw_yearly_income(
        ax,
        years_to_simulate,
        net_profit,
        net_income,
        breakdown,
        taxes,
        expenses,
        husband,
        wife,
        sim_config
    ):
    """
    Draws the yearly income chart into the provided matplotlib Axes.
    Phase 1: minimal refactor; uses plt.sca(ax) so existing plt.* calls keep working.
    """

    # Make this axes the current target for pyplot calls (keeps helpers unchanged)
    plt.sca(ax)

    x = np.arange(years_to_simulate + 1)

    # ------------------------------------------------------------
    # X-axis ticks for readability
    # ------------------------------------------------------------
    if years_to_simulate <= 10:
        step = 1
    elif years_to_simulate <= 20:
        step = 2
    elif years_to_simulate <= 50:
        step = 5
    else:
        step = 10

    plt.xticks(np.arange(0, years_to_simulate, step))

    # ------------------------------------------------------------
    # Sub-income breakdown (stacked bars)
    # ------------------------------------------------------------
    if sim_config.subplot_mode == "sub_categories":
        colors = {
            'work': "skyblue",
            'pension': "mediumpurple",
            'annuity': "gold",
            'ss': "mediumseagreen",
            'rmd': "orange",
            'withdrawal': "darkblue",
            'bond_interest': "saddlebrown",
            'cash_interest': "gray",
            'qualified_dividends': "forestgreen",
            'special_income': "slateblue",
            'income': "skyblue",
        }
        display_labels = {
            "work": "Wages",
            "pension": "Pension",
            "annuity": "Annuity",
            "ss": "Social Security",
            "rmd": "RMD",
            "withdrawal": "Portfolio Withdrawals",
            "bond_interest": "Bond Interest",
            "cash_interest": "Cash Interest",
            "qualified_dividends": "Qualified Dividends",
            "special_income": "Special Income",
            "income": "Net Income",
        }
        bottom = np.zeros(years_to_simulate + 1)
        if sim_config.sim_type == "income_sim":
            plot_keys = [
                'work',
                'pension',
                'annuity',
                'ss',
                'special_income',
            ]
        elif sim_config.sim_type == "cashflow_sim":
            plot_keys = [
                'income',
                'rmd',
                'withdrawal',
                'cash_interest',
                'bond_interest',
                'qualified_dividends',
            ]
        else:
            plot_keys = list(breakdown.keys())

        for key in plot_keys:
            values = np.array(breakdown[key])

            label = display_labels[key]

            plt.bar(
                x,
                values,
                bottom=bottom,
                color=colors[key],
                label=label
            )
            bottom += values

    # ------------------------------------------------------------
    # Total combined income only
    # ------------------------------------------------------------
    elif net_income is not None:
        if sim_config.sim_type == "cashflow_sim":
            total_label = "Cash Flow"
        else:
            total_label = "Net Income"

        plt.bar(
            x,
            net_income,
            color="skyblue",
            label=total_label
        )

    if sim_config.annotate_plots:
        income_sources = {
            "SS": breakdown['ss'],
            "Pension": breakdown['pension'],
            "Annuity": breakdown['annuity'],
            "RMD": breakdown['rmd'],
            "Portfolio Withdrawals": breakdown['withdrawal']
        }

        colors = {
            "SS": "black",
            "Pension": "black",
            "Annuity": "black",
            "RMD": "black",
            "Portfolio Withdrawals": "black"
        }

        for label, values in income_sources.items():
            values = np.array(values)
            first_idx = np.where(values > 0)[0]
            if first_idx.size > 0:
                idx = first_idx[0]
                plt.annotate(
                    f"Start {label}",
                    xy=(x[idx], values[idx]),
                    xytext=(0, 10),
                    textcoords='offset points',
                    ha='center',
                    fontsize=9,
                    color=colors[label],
                    arrowprops=dict(arrowstyle="->", color=colors[label], lw=1)
                )

    # ------------------------------------------------------------
    # Household expense overlay (short horizontal segments)
    # ------------------------------------------------------------
    if sim_config.always_use_expense_mode and sim_config.overlay_household_expenses:
        x = np.arange(years_to_simulate + 1)
        expenses = np.array(expenses)

        segment_half_width = 0.35
        label_added = False

        for i in range(len(expenses)):
            if expenses[i] > 0:
                plt.hlines(
                    y=expenses[i],
                    xmin=x[i] - segment_half_width,
                    xmax=x[i] + segment_half_width,
                    colors="black",
                    linewidth=2,
                    label="Household Expenses" if not label_added else None
                )
                label_added = True

    x = np.arange(years_to_simulate + 1)
    _plot_net_profit_overlay(x, net_profit, sim_config)

    # Keep using plot_yearly_income as the handle container for legend extras (existing behavior)
    _plot_retirement_age_overlay(husband, wife, years_to_simulate, sim_config, plot_yearly_income)

    if sim_config.sim_type == "income_sim":
        if sim_config.always_use_expense_mode:
            sim_type_text = "Income and Expenses"
        else:
            sim_type_text = "Income and Withdrawals"
    elif sim_config.sim_type == "cashflow_sim":
        if sim_config.always_use_expense_mode:
            sim_type_text = "Cash Flow and Expenses"
        else:
            sim_type_text = "Cash Flow and Withdrawals"

    value_type = "Real" if getattr(sim_config, "plot_mode", "nominal") == "real" else "Nominal"

    plt.title(f"{sim_type_text} ({value_type})")
    plt.xlabel("Year")
    plt.ylabel("Amount ($)")

    # Optional subtitle with extra info
    subtitle_text = f"Start Year: {sim_config.start_year} | Inflation: {sim_config.inflation_rate*100:.1f}%"
    plt.gcf().text(0.5, -0.05, subtitle_text, ha='center', fontsize=10)

    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.legend(loc="upper left")

    # Use provided ax (do not re-fetch plt.gca())
    handles, labels = ax.get_legend_handles_labels()
    if hasattr(plot_yearly_income, "_extra_handles"):
        for handle in plot_yearly_income._extra_handles:
            handles.append(handle)
            labels.append(handle.get_label())
        del plot_yearly_income._extra_handles

    ax.legend(handles=handles, labels=labels, loc="upper left")

    plt.tight_layout()

    _draw_user_annotations_lower_left(ax, sim_config)
    _draw_scenario_annotations_lower_right(ax, sim_config)

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{int(v):,}'))


def plot_yearly_income(
        years_to_simulate,
        net_profit,
        net_income,
        breakdown,
        taxes,
        expenses,
        husband,
        wife,
        sim_config
    ):

    fig, ax = plt.subplots(figsize=(12, 6))

    draw_yearly_income(
        ax,
        years_to_simulate,
        net_profit,
        net_income,
        breakdown,
        taxes,
        expenses,
        husband,
        wife,
        sim_config
    )

    plt.show(block=False)


# -------------------
# Helper for retirement age overlay
# -------------------
def _plot_retirement_age_overlay(husband, wife, years_to_simulate, sim_config, plot_func_container):
    """
    Plots a vertical line for retirement age on the yearly income chart.
    Creates a proxy handle for the legend.
    """
    if not (sim_config.overlay_retirement_age and husband is not None):
        return

    # Determine last retirement index between husband and wife
    if getattr(sim_config, "second_person_enabled", False) and wife is not None:
        retirement_index = max(husband.retire_age - husband.age, wife.retire_age - wife.age)
    else:
        retirement_index = husband.retire_age - husband.age

    # Clamp to simulation range
    retirement_index = min(max(retirement_index, 0), years_to_simulate)

    # Plot vertical line
    plt.axvline(
        x=retirement_index,
        color="black",
        linewidth=2,
        linestyle="-",
        zorder=3
    )

    # Create proxy line for legend
    import matplotlib.lines as mlines
    retirement_line = mlines.Line2D([], [], color="black", linewidth=2, linestyle="-", label="Retirement Year")

    # Store for later legend merge
    if not hasattr(plot_func_container, "_extra_handles"):
        plot_func_container._extra_handles = []
    plot_func_container._extra_handles.append(retirement_line)


# -------------------
# Helper for plotting net profit overlay
# -------------------
def _plot_net_profit_overlay(x, net_profit, sim_config):
    """
    Plots net profit as a line overlay, handling positive/negative segments
    and zero crossings for a smooth visual.
    """

    if sim_config.sim_type != "cashflow_sim":
        return

    if not (sim_config.always_use_expense_mode and sim_config.overlay_profit_loss):
        return

    y_vals = np.array(net_profit[1:])  # skip year 0
    x_vals = x[1:]
    start_idx = 0

    for i in range(1, len(y_vals)):
        # Check zero crossing
        if y_vals[i-1] * y_vals[i] < 0:
            # Linear interpolation for zero crossing
            x_zero = x_vals[i-1] - y_vals[i-1] * (x_vals[i] - x_vals[i-1]) / (y_vals[i] - y_vals[i-1])

            # Plot segment up to crossing
            plt.plot(x_vals[start_idx:i], y_vals[start_idx:i],
                     color="blue" if y_vals[start_idx] >= 0 else "red", linewidth=2)
            # Plot crossing segment
            plt.plot([x_vals[i-1], x_zero], [y_vals[i-1], 0],
                     color="blue" if y_vals[start_idx] >= 0 else "red", linewidth=2)
            plt.plot([x_zero, x_vals[i]], [0, y_vals[i]],
                     color="blue" if y_vals[i] >= 0 else "red", linewidth=2)

            # Start next segment
            start_idx = i
            y_vals[i-1] = 0  # smooth transition

    # Plot final segment
    plt.plot(x_vals[start_idx:], y_vals[start_idx:],
             color="blue" if y_vals[start_idx] >= 0 else "red", linewidth=2)

    # Legend helpers
    plt.plot([], [], color="blue", linewidth=2, label="Net Cash Flow (Positive)")
    plt.plot([], [], color="red", linewidth=2, label="Net Cash Flow (Negative)")


def _draw_annotation_block(ax, annotations, *, corner="lower_right"):
    if not annotations:
        return

    fontsize = 9
    line_spacing = 0.035

    if corner == "lower_right":
        start_x = 0.92
        start_y = 0.02
        text_ha = "right"
        reverse_spans = True
    elif corner == "lower_left":
        start_x = 0.08
        start_y = 0.05
        text_ha = "left"
        reverse_spans = False
    else:
        raise ValueError(f"Unsupported annotation corner: {corner}")

    fig = plt.gcf()
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    max_line_width = 0
    for line in annotations:
        line_width = 0
        for span in line:
            text = span.get("text", "")
            t = ax.text(0, 0, text, fontsize=fontsize)
            bbox = t.get_window_extent(renderer=renderer)
            line_width += bbox.width
            t.remove()
        max_line_width = max(max_line_width, line_width)

    inv = ax.transAxes.inverted()
    dx = inv.transform((max_line_width, 0))[0] - inv.transform((0, 0))[0]
    dy = line_spacing * len(annotations)

    import matplotlib.patches as patches

    rect_x = start_x - dx if corner == "lower_right" else start_x
    rect = patches.FancyBboxPatch(
        (rect_x, start_y),
        dx,
        dy,
        boxstyle="round,pad=0.01",
        facecolor="white",
        edgecolor="none",
        alpha=0.8,
        transform=ax.transAxes,
        zorder=5
    )
    ax.add_patch(rect)

    for line_index, line in enumerate(reversed(annotations)):
        y = start_y + line_index * line_spacing

        if reverse_spans:
            x = start_x
            spans = reversed(line)
        else:
            x = start_x
            spans = line

        for span in spans:
            text = span.get("text", "")
            color = span.get("color") or "black"

            t = ax.text(
                x,
                y,
                text,
                transform=ax.transAxes,
                fontsize=fontsize,
                va="bottom",
                ha=text_ha,
                color=color,
                zorder=6
            )

            bbox = t.get_window_extent(renderer=renderer)
            dx_span = inv.transform((bbox.width, 0))[0] - inv.transform((0, 0))[0]

            if reverse_spans:
                x -= dx_span
            else:
                x += dx_span

def _draw_user_annotations_lower_left(ax, sim_config):
    if not getattr(sim_config, "use_snapshot_annotations", True):
        return

    annotations = getattr(sim_config, "user_annotation_strings", None)
    if not annotations:
        return

    _draw_annotation_block(ax, annotations, corner="lower_left")


def _draw_scenario_annotations_lower_right(ax, sim_config):
    if not getattr(sim_config, "use_snapshot_annotations", True):
        return

    annotations = getattr(sim_config, "scenario_explorer_annotations", None)
    if not annotations:
        return

    _draw_annotation_block(ax, annotations, corner="lower_right")