# plotPortfolioProjection.py

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap
import tkinter as tk
from tkinter import ttk

from src.utils.constants import *
from src.dataClasses.portfolioState import *


# Color constants
COLOR_TOTAL_REAL = "blue"
COLOR_TOTAL_NOMINAL = "darkblue"
COLOR_REALESTATE = "brown"
COLOR_FUND_EXPENSES = "orange"
COLOR_YEARLY_INCOME = "skyblue"
COLOR_NET_PROFIT = "red"
COLOR_PENSION = "orange"
COLOR_ANNUITY = "black"
COLOR_SS = "green"
COLOR_RMD = "purple"
COLOR_PRE_TAX = "lightgreen"
COLOR_POST_TAX = "lightcoral"
COLOR_ROTH = "mediumpurple"
COLOR_HSA = "teal"

COLOR_OVERLAY_TAXES = "firebrick"
COLOR_OVERLAY_FEES = "orange"
COLOR_OVERLAY_TAXES_FEES = "red"

ALPHA_OVERLAY = 0.35  # transparency for fills

# Custom dark blue to cyan colormap
BLUE_CYAN_CMAP = LinearSegmentedColormap.from_list(
    "blue_cyan",
    ["#00FFFF", "#00008B"]  # cyan to dark blue
)


def plot_portfolio_projection(  years_list, 
                                simulation_data,
                                sim_config=None,
                                annotate_plots=False,
                                sim_rebalance_string="",
                                husband=None,
                                wife=None):

    fig, ax = plt.subplots(figsize=(11, 7))

    draw_portfolio_projection(
        ax,
        years_list,
        simulation_data,
        sim_config=sim_config,
        annotate_plots=annotate_plots,
        sim_rebalance_string=sim_rebalance_string,
        husband=husband,
        wife=wife
    )

    plt.show(block=False)


def draw_portfolio_projection(
        ax,
        years_list,
        simulation_data,
        sim_config=None,
        annotate_plots=False,
        sim_rebalance_string="",
        husband=None,
        wife=None
    ):
    """
    Draws the portfolio projection into the provided matplotlib Axes.
    Phase 1: minimal refactor; uses plt.sca(ax) so existing plt.* helpers keep working.
    """

    # Make this axes the current target for pyplot calls (keeps helpers unchanged)
    plt.sca(ax)

    years_to_simulate = len(years_list) - 1
    if years_to_simulate <= 10:
        step = 1
    elif years_to_simulate <= 20:
        step = 2
    elif years_to_simulate <= 50:
        step = 5
    else:
        step = 10
    plt.xticks(np.arange(0, years_to_simulate + 1, step))

    # Plot nominal / median data
    _plot_assets(years_list, simulation_data, total_color=COLOR_TOTAL_NOMINAL, sim_config=sim_config)

    # Plot overlays
    _plot_overlays(years_list, simulation_data, sim_config, husband=husband, wife=wife)

    _draw_user_annotations_lower_left(ax, sim_config)
    _draw_scenario_annotations_lower_right(ax, sim_config)
    _draw_simulated_shortfall_rate_label(ax, simulation_data, sim_config)
    
    value_type = "Real" if getattr(sim_config, "plot_mode", "nominal") == "real" else "Nominal"
    plt.title(f"Portfolio Simulation ({value_type})")

    handles, labels = ax.get_legend_handles_labels()
    if hasattr(_plot_monte_carlo_assets, "_extra_handles"):
        for handle in _plot_monte_carlo_assets._extra_handles:
            handles.append(handle)
            labels.append(handle.get_label())
        del _plot_monte_carlo_assets._extra_handles
    if hasattr(_plot_overlays, "_extra_handles"):
        for handle in _plot_overlays._extra_handles:
            handles.append(handle)
            labels.append(handle.get_label())
        del _plot_overlays._extra_handles
    ax.legend(handles=handles, labels=labels, loc="upper left")

    # Always start y-axis at 0
    yMin = 0
    if sim_config.constant_y_plots:
        if sim_config.subplot_mode == "monte_carlo":
            yMax = simulation_data.percentiles["median"][0] * sim_config.years_to_simulate / 3
        else:
            yMax = simulation_data.percentiles["median"][0] * sim_config.years_to_simulate / 4.5
        plt.ylim(yMin, yMax)
    else:
        plt.ylim(bottom=yMin)

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
    plt.xlabel("Year")
    plt.ylabel("Portfolio Value ($)")
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)

    plt.subplots_adjust(left=0.15)

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))


def _draw_simulated_shortfall_rate_label(ax, simulation_data, sim_config):
    if not getattr(sim_config, "show_simulated_shortfall_rate", False):
        return

    rate = getattr(simulation_data, "simulated_shortfall_rate", None)
    if rate is None:
        raise ValueError(
            "show_simulated_shortfall_rate is True, but simulation_data.simulated_shortfall_rate is missing"
        )

    #label = f"{rate:.0f}% of modeled scenarios fell below $0"
    label = f"{rate:.0f}% of scenarios fell below $0"

    ax.text(
        0.98,
        0.98,
        label,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=12,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.85),
        zorder=10,
    )

def _plot_assets(years_list, simulation_data, total_color=COLOR_TOTAL_REAL, sim_config=None):
    """
    Dispatcher for plotting portfolio assets depending on the subplot_mode.
    """
    mode = getattr(sim_config, "subplot_mode", "pre_post_tax")
    
    if mode == "pre_post_tax":
        _plot_pre_post_tax_assets(years_list, simulation_data)
    elif mode == "monte_carlo":
        monte_carlo_plot_style = getattr(sim_config, "monte_carlo_plot_style", "fill")

        if monte_carlo_plot_style == "all_lines":
            _plot_monte_carlo_all_lines(years_list, simulation_data, total_color)
        else:
            _plot_monte_carlo_assets(years_list, simulation_data, total_color, sim_config)
    elif mode == "sub_categories":
        _plot_sub_category_assets(years_list, simulation_data, sim_config)
    else:
        median_values = simulation_data.percentiles["median"]

        fill_color = BLUE_CYAN_CMAP(0.3)  # light blue, not cyan

        plt.fill_between(
            years_list,
            0,
            median_values,
            color=fill_color,
            alpha=0.4
        )

    
        # Draw line on top
        plt.plot(
            years_list,
            median_values,
            color=total_color,
            linewidth=2,
            label="Total Assets"
        )

# -------------------
# Mode-specific helpers
# -------------------
def _plot_pre_post_tax_assets(years_list, simulation_data):
    """
    Plot tax-bucket stacked areas:
        Real Estate
        Post-Tax
        Pre-Tax
        Roth
        HSA
    """

    median = np.asarray(simulation_data.percentiles["median"])

    realestate = getattr(simulation_data, "realestate", None)
    if realestate is None:
        realestate = np.zeros_like(median)

    post_tax = getattr(simulation_data, "post_tax_assets", None)
    if post_tax is None:
        post_tax = np.zeros_like(median)

    pre_tax = getattr(simulation_data, "pre_tax_assets", None)
    if pre_tax is None:
        pre_tax = np.zeros_like(median)

    roth = getattr(simulation_data, "roth_assets", None)
    if roth is None:
        roth = np.zeros_like(median)

    hsa = getattr(simulation_data, "hsa_assets", None)
    if hsa is None:
        hsa = np.zeros_like(median)

    bottom = np.zeros_like(median)

    if np.any(realestate > 0):
        plt.fill_between(
            years_list,
            bottom,
            bottom + realestate,
            color=COLOR_REALESTATE,
            alpha=0.5,
            label="Real Estate Assets",
        )
        bottom += realestate

    if np.any(post_tax > 0):
        plt.fill_between(
            years_list,
            bottom,
            bottom + post_tax,
            color=COLOR_POST_TAX,
            alpha=0.5,
            label="Post-Tax Assets",
        )
        bottom += post_tax

    if np.any(pre_tax > 0):
        plt.fill_between(
            years_list,
            bottom,
            bottom + pre_tax,
            color=COLOR_PRE_TAX,
            alpha=0.5,
            label="Pre-Tax Assets",
        )
        bottom += pre_tax

    if np.any(roth > 0):
        plt.fill_between(
            years_list,
            bottom,
            bottom + roth,
            color=COLOR_ROTH,
            alpha=0.5,
            label="Roth Assets",
        )
        bottom += roth

    if np.any(hsa > 0):
        plt.fill_between(
            years_list,
            bottom,
            bottom + hsa,
            color=COLOR_HSA,
            alpha=0.5,
            label="HSA Assets",
        )
        bottom += hsa

    _plot_baseline_line(years_list, simulation_data, COLOR_TOTAL_REAL)


def _plot_monte_carlo_assets(years_list, simulation_data, total_color, sim_config=None):
    percentiles = simulation_data.percentiles

    plot_style = getattr(sim_config, "monte_carlo_plot_style", "fill")

    percentile_keys = [
        "pct1", "pct10", "pct20", "pct30", "pct40",
        "median",
        "pct60", "pct70", "pct80", "pct90", "pct99"
    ]

    if plot_style == "line":
        LINE_SPECS = [
            ("pct1",   BLUE_CYAN_CMAP(0.40), 2.0, 0.40, "98% of projected results within this range"),
            ("pct10",  BLUE_CYAN_CMAP(0.50), 2.0, 0.50, "80% of projected results within this range"),

            ("pct20",  BLUE_CYAN_CMAP(0.60), 2.0, 0.60, "60% of projected results within this range"),
            ("pct30",  BLUE_CYAN_CMAP(0.70), 2.0, 0.70, "40% of projected results within this range"),
            ("pct40",  BLUE_CYAN_CMAP(0.80), 2.0, 0.80, "20% of projected results within this range"),

            ("median", BLUE_CYAN_CMAP(0.95), 3.5, 1.00, "Median Total Assets"),

            ("pct60",  BLUE_CYAN_CMAP(0.80), 2.0, 0.80, None),
            ("pct70",  BLUE_CYAN_CMAP(0.70), 2.0, 0.70, None),
            ("pct80",  BLUE_CYAN_CMAP(0.60), 2.0, 0.60, None),

            ("pct90",  BLUE_CYAN_CMAP(0.50), 2.0, 0.50, None),
            ("pct99",  BLUE_CYAN_CMAP(0.40), 2.0, 0.40, None),
        ]

        import matplotlib.lines as mlines

        extra_handles = []

        for key, color, linewidth, alpha, legend_label in LINE_SPECS:
            if key not in percentiles:
                continue

            values = np.array(percentiles[key])

            plt.plot(
                years_list[:len(values)],
                values,
                color=color,
                linewidth=linewidth,
                alpha=alpha,
                label=None
            )

            if legend_label is not None:
                extra_handles.append(
                    mlines.Line2D(
                        [],
                        [],
                        color=color,
                        linewidth=linewidth,
                        alpha=alpha,
                        label=legend_label
                    )
                )

        _plot_monte_carlo_assets._extra_handles = extra_handles
    else:
        # EXISTING FILL CODE (leave as-is)
        MONTE_CARLO_BANDS = [
            ("pct1",  "pct10", 0.40, "98% of projected results within this range"),
            ("pct10", "pct20", 0.50, "80% of projected results within this range"),
            ("pct20", "pct30", 0.60, "60% of projected results within this range"),
            ("pct30", "pct40", 0.70, "40% of projected results within this range"),
            ("pct40", "median", 0.80, "20% of projected results within this range"),
            ("median", "pct60", 0.80, None),
            ("pct60", "pct70", 0.70, None),
            ("pct70", "pct80", 0.60, None),
            ("pct80", "pct90", 0.50, None),
            ("pct90", "pct99", 0.40, None),
        ]
        depth_values = np.linspace(0.35, 0.85, 5)

        for i, (lower, upper, alpha, label) in enumerate(MONTE_CARLO_BANDS):
            if lower not in percentiles or upper not in percentiles:
                continue

            lower_values = np.array(percentiles[lower])
            upper_values = np.array(percentiles[upper])

            min_len = min(len(years_list), len(lower_values), len(upper_values))

            if i <= 4:
                depth_index = i
            else:
                depth_index = 9 - i

            band_color = BLUE_CYAN_CMAP(depth_values[depth_index])

            plt.fill_between(
                years_list[:min_len],
                lower_values[:min_len],
                upper_values[:min_len],
                color=band_color,
                alpha=alpha,
                label=label
            )

        # Median line
        if "median" in percentiles:
            median_values = np.array(percentiles["median"])
            plt.plot(
                years_list[:len(median_values)],
                median_values,
                color=BLUE_CYAN_CMAP(0.95),
                linewidth=4,
                label="Median Total Assets"
            )


def _plot_monte_carlo_all_lines(years_list, simulation_data, total_color):
    """
    Plot every Monte Carlo simulation path as a faint line.
    Overlay the median on top for readability.
    """

    all_paths = getattr(simulation_data, "raw_total_assets", None)
    if all_paths is None:
        raise AttributeError(
            "simulation_data.raw_total_assets is missing. "
            "Pass raw_total_assets into PortfolioPlotData before using all_lines mode."
        )

    all_paths = np.asarray(all_paths)

    if all_paths.ndim != 2:
        raise ValueError(
            f"Expected raw_total_assets to be 2D, got shape {all_paths.shape}"
        )

    num_sims, num_years = all_paths.shape
    x = np.asarray(years_list[:num_years])

    # Draw every simulation path - alpha was originally 0.06  Line width was 0.8.
    max_lines = min(num_sims, 500)
    indices = np.linspace(0, num_sims - 1, max_lines, dtype=int)

    for s in indices:
        plt.plot(
            x,
            all_paths[s, :num_years],
            color="steelblue",
            linewidth=1,
            alpha=0.2
        )

    # Overlay median for readability
    if "median" in simulation_data.percentiles:
        median_values = np.asarray(simulation_data.percentiles["median"])
        plt.plot(
            years_list[:len(median_values)],
            median_values,
            color=total_color,
            linewidth=3,
            label="Median Total Assets"
        )


def _plot_sub_category_assets(years_list, simulation_data, sim_config):
    """
    Plot stacked assets by sub-category: cash, bonds, equity, real estate.
    """
    #cash = getattr(simulation_data, "cash", np.zeros_like(simulation_data.percentiles["median"]))
    #bonds = getattr(simulation_data, "bonds", np.zeros_like(simulation_data.percentiles["median"]))
    #realestate = getattr(simulation_data, "realestate", np.zeros_like(simulation_data.percentiles["median"])) if sim_config.include_realestate else np.zeros_like(cash)
    median = np.asarray(simulation_data.percentiles["median"])

    cash = getattr(simulation_data, "cash", None)
    if cash is None:
        cash = np.zeros_like(median)

    bonds = getattr(simulation_data, "bonds", None)
    if bonds is None:
        bonds = np.zeros_like(median)

    if sim_config.include_realestate:
        realestate = getattr(simulation_data, "realestate", None)
        if realestate is None:
            realestate = np.zeros_like(median)
    else:
        realestate = np.zeros_like(median)
    
    # Equity is the residual
    equity = simulation_data.percentiles["median"] - cash - bonds - realestate

    bottom = np.zeros_like(cash)

    if sim_config.include_realestate and simulation_data.realestate is not None:
        plt.fill_between(years_list, bottom, bottom + realestate, color=COLOR_REALESTATE, alpha=0.6, label="Real Estate")
        bottom += realestate

    plt.fill_between(years_list, bottom, bottom + cash, color="steelblue", alpha=0.6, label="Cash")
    bottom += cash
    plt.fill_between(years_list, bottom, bottom + bonds, color="gold", alpha=0.6, label="Bonds")
    bottom += bonds
    plt.fill_between(years_list, bottom, bottom + equity, color="lightblue", alpha=0.4, label="Stocks")

    _plot_baseline_line(years_list, simulation_data, COLOR_TOTAL_REAL)


# -------------------
# Utility for drawing baseline line
# -------------------
def _plot_baseline_line(years_list, simulation_data, line_color, label_prefix=""):
    """
    Plot the baseline portfolio line, turning red if it ever effectively hits zero.
    """
    NEAR_ZERO_THRESHOLD = 1e-6
    color = "red" if np.any(simulation_data.percentiles["median"] <= NEAR_ZERO_THRESHOLD) else line_color
    label = f"Median Total Assets ({label_prefix})" if label_prefix else "Total Assets"
    plt.plot(years_list, simulation_data.percentiles["median"], color=color, linewidth=2, label=label)


def _plot_overlays(years_list, simulation_data, sim_config, husband=None, wife=None):
    """
    Plot optional overlays above the baseline.
    Assumes baseline is already net of taxes and fund expenses.
    Each overlay represents the portfolio value including the given deduction.
    """

    median = simulation_data.percentiles["median"]

    # Taxes overlay
    if sim_config.overlay_tax_impacts and not sim_config.overlay_fund_expense_impacts:
        plt.fill_between(
            years_list,
            median,
            simulation_data.median_without_taxes,
            color=COLOR_OVERLAY_TAXES,
            alpha=ALPHA_OVERLAY,
            label="With Taxes"
        )

    # Fund expenses overlay
    if not sim_config.overlay_tax_impacts and sim_config.overlay_fund_expense_impacts:
        plt.fill_between(
            years_list,
            median,
            simulation_data.median_without_fund_expenses,
            color=COLOR_OVERLAY_FEES,
            alpha=ALPHA_OVERLAY,
            label="With Fund Expenses"
        )

    # Taxes + Fund Expenses overlay
    if sim_config.overlay_tax_impacts and sim_config.overlay_fund_expense_impacts:
            plt.fill_between(
                years_list,
                median,
                simulation_data.median_without_taxes,
                color=COLOR_OVERLAY_TAXES_FEES,
                alpha=ALPHA_OVERLAY,
                label="Taxes Impacts"
            )
            plt.fill_between(
                years_list,
                simulation_data.median_without_taxes,
                simulation_data.median_without_taxes_or_fund_expenses,
                color=COLOR_OVERLAY_FEES,
                alpha=ALPHA_OVERLAY,
                label="Fund Expense Impacts"
            )

    # Retirement year overlay
    if sim_config.overlay_retirement_age and husband is not None:
        if getattr(sim_config, "second_person_enabled", False) and wife is not None:
            retirement_index = max(
                husband.retire_age - husband.age,
                wife.retire_age - wife.age
            )
        else:
            retirement_index = husband.retire_age - husband.age

        # Clamp to simulation range
        retirement_index = min(max(retirement_index, 0), len(years_list) - 1)

        # Draw vertical line
        import matplotlib.lines as mlines
        plt.axvline(
            x=retirement_index,
            color="black",
            linewidth=2,
            linestyle="-",
            zorder=3
        )

        # Add to extra handles for legend
        retirement_line = mlines.Line2D([], [], color="black", linewidth=2, linestyle="-", label="Retirement Year")
        if not hasattr(_plot_overlays, "_extra_handles"):
            _plot_overlays._extra_handles = []
        _plot_overlays._extra_handles.append(retirement_line)



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
    annotations = getattr(sim_config, "scenario_explorer_annotations", None)
    if not annotations:
        return

    _draw_annotation_block(ax, annotations, corner="lower_right")
