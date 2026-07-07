# plotOperatingBalance.py

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch

def _plot_retirement_age_overlay(husband, wife, years_to_simulate, sim_config, plot_func_container):
    if not (getattr(sim_config, "overlay_retirement_age", False) and husband is not None):
        return

    if getattr(sim_config, "second_person_enabled", False) and wife is not None:
        retirement_index = max(husband.retire_age - husband.age, wife.retire_age - wife.age)
    else:
        retirement_index = husband.retire_age - husband.age

    retirement_index = min(max(retirement_index, 0), years_to_simulate)

    plt.axvline(
        x=retirement_index,
        color="black",
        linewidth=2,
        linestyle="-",
        zorder=3
    )

    import matplotlib.lines as mlines
    retirement_line = mlines.Line2D([], [], color="black", linewidth=2, linestyle="-", label="Retirement Year")

    if not hasattr(plot_func_container, "_extra_handles"):
        plot_func_container._extra_handles = []
    plot_func_container._extra_handles.append(retirement_line)


def draw_operating_balance(
    ax,
    years_to_simulate,
    net_profit,
    operating_balance,
    portfolio_value,   # NEW
    husband,
    wife,
    sim_config
):

    """
    Bars for cumulative operating balance (year 0 = 0, then accumulates),
    in the general style of plotYearlyIncome.
    """
    plt.sca(ax)

    x = np.arange(years_to_simulate + 1)

    # X-axis tick spacing (same logic)
    if years_to_simulate <= 10:
        step = 1
    elif years_to_simulate <= 20:
        step = 2
    elif years_to_simulate <= 50:
        step = 5
    else:
        step = 10
    plt.xticks(np.arange(0, years_to_simulate + 1, step))

    operating_balance = np.array(operating_balance)

    portfolio_value = np.array(portfolio_value, dtype=float)

    # Guard against any mismatch (defensive)
    n = min(len(operating_balance), len(portfolio_value))
    operating_balance = operating_balance[:n]
    portfolio_value = portfolio_value[:n]
    x = x[:n]

    # Bars: operating balance (3-state color)
    # Blue: operating_balance >= 0
    # Orange: operating_balance < 0 and deficit is covered by portfolio_value
    # Red: operating_balance < 0 and deficit exceeds portfolio_value
    colors = []
    for ob, pv in zip(operating_balance, portfolio_value):
        if ob >= 0:
            colors.append("skyblue")
        else:
            deficit = -ob
            colors.append("orange" if pv >= deficit else "red")

    plt.bar(
        x,
        operating_balance,
        color=colors
    )

    # Optional: a zero baseline helps interpret negatives
    plt.axhline(0, color="black", linewidth=1)

    # Retirement overlay (easy / already implemented)
    _plot_retirement_age_overlay(husband, wife, years_to_simulate, sim_config, plot_operating_balance)

    value_type = "Real" if getattr(sim_config, "plot_mode", "nominal") == "real" else "Nominal"
    ax.set_title(f"Cumulative Household Cashflow ({value_type})", pad=20)

    subtitle_text = "Running total of household income - expenses - taxes.\nExcludes investment returns."

    ax.text(
        0.5,
        0.98,
        subtitle_text,
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=10,
        bbox=dict(
            boxstyle="round,pad=0.3",
            facecolor="white",
            edgecolor="none",
            alpha=0.7
        ),
        zorder=5
    )

    plt.xlabel("Year")
    plt.ylabel("Amount ($)")

    subtitle_text = f"Start Year: {sim_config.start_year} | Inflation: {sim_config.inflation_rate*100:.1f}%"
    plt.gcf().text(0.5, -0.05, subtitle_text, ha="center", fontsize=10)

    plt.grid(True, axis="y", linestyle="--", alpha=0.7)

    handles = [
        Patch(facecolor="skyblue", edgecolor="skyblue", label="Operating Balance (Positive)"),
        Patch(facecolor="orange", edgecolor="orange", label="Operating Balance (Negative, Covered)"),
        Patch(
            facecolor="red",
            edgecolor="red",
            label="Deficit Exceeds Portfolio\nSimulated cumulative cashflow deficit"
        ),
    ]

    # Append retirement proxy line if it exists
    if hasattr(plot_operating_balance, "_extra_handles"):
        handles.extend(plot_operating_balance._extra_handles)
        del plot_operating_balance._extra_handles

    ax.legend(handles=handles, loc="upper left")

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))

    plt.tight_layout()


def plot_operating_balance(
    years_to_simulate,
    net_profit,
    operating_balance,
    portfolio_value,
    husband,
    wife,
    sim_config
):
    fig, ax = plt.subplots(figsize=(12, 6))

    draw_operating_balance(
        ax,
        years_to_simulate,
        net_profit,
        operating_balance,
        portfolio_value,   # NEW
        husband,
        wife,
        sim_config
    )
    plt.show(block=False)