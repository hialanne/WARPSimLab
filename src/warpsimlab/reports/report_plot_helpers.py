# report_plot_helpers.py

import os
import matplotlib.pyplot as plt
import numpy as np

from src.warpsimlab.plots.plotOperatingBalance import draw_operating_balance
from src.warpsimlab.plots.plotPortfolioProjection import draw_portfolio_projection
from src.warpsimlab.plots.plotYearlyIncome import draw_yearly_income
from src.warpsimlab.plots.portfolioPlotData import PortfolioPlotData

def _ensure_output_folder(output_folder):
    os.makedirs(output_folder, exist_ok=True)


def save_portfolio_projection_report_plot(
    output_folder,
    filename,
    years_list,
    portfolio_plot_data,
    sim_config,
    husband=None,
    wife=None,
    summary_results=None,
):
    """
    Save a portfolio projection plot for report use.

    This function intentionally does not call plt.show().
    Existing interactive plot behavior remains owned by plot_portfolio_projection().
    """
    _ensure_output_folder(output_folder)
    image_path = os.path.join(output_folder, filename)

    fig, ax = plt.subplots(figsize=(14, 8))

    if summary_results is not None:
        portfolio_plot_data = _build_portfolio_only_plot_data(
            portfolio_plot_data,
            summary_results,
        )

    try:
        draw_portfolio_projection(
            ax,
            years_list,
            portfolio_plot_data,
            sim_config=sim_config,
            annotate_plots=getattr(sim_config, "annotate_plots", False),
            sim_rebalance_string=getattr(sim_config, "sim_rebalance", ""),
            husband=husband,
            wife=wife,
        )

        fig.savefig(image_path, dpi=200, bbox_inches="tight")
        
        return image_path

    finally:
        plt.close(fig)


def save_historical_window_highlight_report_plot(
    output_folder,
    filename,
    years_list,
    total_assets,
    start_years,
    best_indices,
    worst_indices,
    *,
    plot_mode="real",
):
    """
    Save a Historical Window insight plot.

    Background:
        all historical portfolio paths in light gray

    Highlights:
        five strongest historical windows in blue
        five weakest historical windows in red

    Labels:
        retirement start year at the right edge of each highlighted line
    """
    _ensure_output_folder(output_folder)
    image_path = os.path.join(output_folder, filename)

    years_list = np.asarray(years_list)
    total_assets = np.asarray(total_assets, dtype=float)
    start_years = np.asarray(start_years)

    if total_assets.ndim != 2:
        raise ValueError(
            f"Expected total_assets to be 2D, got shape {total_assets.shape}"
        )

    num_paths, num_years = total_assets.shape
    x = years_list[:num_years]

    fig, ax = plt.subplots(figsize=(14, 8))

    try:
        # Draw all historical paths as context.
        for index in range(num_paths):
            ax.plot(
                x,
                total_assets[index, :num_years],
                color="gray",
                linewidth=0.9,
                alpha=0.45,
                zorder=1,
            )

        def draw_highlight(indices, color, label):
            for position, index in enumerate(indices):
                if index < 0 or index >= num_paths:
                    continue

                y = total_assets[index, :num_years]

                ax.plot(
                    x,
                    y,
                    color=color,
                    linewidth=1.8,
                    alpha=0.95,
                    zorder=3,
                    label=label if position == 0 else None,
                )

                try:
                    label_year = int(start_years[index])
                except (IndexError, TypeError, ValueError):
                    label_year = index

                '''
                ax.text(
                    x[-1] + 0.35,
                    y[-1],
                    str(label_year),
                    color=color,
                    fontsize=9,
                    fontweight="bold",
                    va="center",
                    ha="left",
                    zorder=4,
                )
                '''
                label_offset = (position - (len(indices) - 1) / 2.0) * 0.035
                y_range = ax.get_ylim()[1] - ax.get_ylim()[0]
                label_y = y[-1] + (label_offset * y_range)

                ax.text(
                    x[-1] + 0.35,
                    label_y,
                    str(label_year),
                    color=color,
                    fontsize=9,
                    fontweight="bold",
                    va="center",
                    ha="left",
                    zorder=4,
                )

        draw_highlight(
            best_indices,
            "blue",
            "Five strongest historical windows",
        )
        draw_highlight(
            worst_indices,
            "red",
            "Five weakest historical windows",
        )

        value_type = "Real" if plot_mode == "real" else "Nominal"

        ax.set_title(
            f"Historical Window Outcomes: Strongest and Weakest Retirement Starts ({value_type} Dollars)"
        )
        ax.set_xlabel("Years Into Retirement")
        ax.set_ylabel("Portfolio Value ($)")
        ax.grid(True, axis="y", linestyle="--", alpha=0.5)
        ax.set_ylim(bottom=0)

        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda value, _: f"${value:,.0f}")
        )

        ax.legend(loc="upper left")

        # Leave room for right-side start-year labels.
        ax.set_xlim(x[0], x[-1] + 3)

        fig.savefig(image_path, dpi=200, bbox_inches="tight")
        return image_path

    finally:
        plt.close(fig)


def save_income_projection_report_plot(
    output_folder,
    filename,
    years_to_simulate,
    net_profit,
    net_income,
    breakdown,
    taxes,
    expenses,
    husband,
    wife,
    sim_config,
):
    """
    Save an income projection plot for report use.

    This function intentionally does not call plt.show().
    Existing interactive plot behavior remains owned by plot_yearly_income().
    """
    _ensure_output_folder(output_folder)
    image_path = os.path.join(output_folder, filename)

    fig, ax = plt.subplots(figsize=(14, 7))

    try:
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
            sim_config,
        )

        fig.savefig(image_path, dpi=200, bbox_inches="tight")
        return image_path

    finally:
        plt.close(fig)


def save_cumulative_operating_balance_report_plot(
    output_folder,
    filename,
    years_to_simulate,
    net_profit,
    portfolio_plot_data,
    husband,
    wife,
    sim_config,
):
    """
    Save a cumulative operating balance plot for report use.

    This mirrors run_sim_operating_balance.py packaging:
      - operating_balance[0] = 0
      - operating_balance[t] = sum(net_profit[1..t]) for t >= 1

    This function intentionally does not call plt.show().
    Existing interactive plot behavior remains owned by plot_operating_balance().
    """
    _ensure_output_folder(output_folder)
    image_path = os.path.join(output_folder, filename)

    net_profit = np.array(net_profit, dtype=float)

    operating_balance = np.zeros_like(net_profit, dtype=float)
    if len(net_profit) > 1:
        operating_balance[1:] = np.cumsum(net_profit[1:])

    portfolio_value = np.array(
        portfolio_plot_data.percentiles["median"],
        dtype=float,
    )

    fig, ax = plt.subplots(figsize=(14, 7))

    try:
        draw_operating_balance(
            ax,
            years_to_simulate,
            net_profit,
            operating_balance,
            portfolio_value,
            husband,
            wife,
            sim_config,
        )

        fig.savefig(image_path, dpi=200, bbox_inches="tight")
        return image_path

    finally:
        plt.close(fig)

def _build_portfolio_only_plot_data(portfolio_plot_data, summary_results):
    """
    Build report-only portfolio plot data that excludes real estate.

    Portfolio-only includes:
        pre-tax + post-tax + Roth + HSA
    """

    pre_tax_assets = np.array(summary_results["pre_tax_assets"], dtype=float)
    post_tax_assets = np.array(summary_results["post_tax_assets"], dtype=float)

    roth_assets = np.array(
        summary_results.get("roth_assets", np.zeros_like(pre_tax_assets)),
        dtype=float,
    )
    hsa_assets = np.array(
        summary_results.get("hsa_assets", np.zeros_like(pre_tax_assets)),
        dtype=float,
    )

    portfolio_only = pre_tax_assets + post_tax_assets + roth_assets + hsa_assets

    percentiles = dict(portfolio_plot_data.percentiles)
    percentiles["median"] = portfolio_only

    return PortfolioPlotData(
        years=portfolio_plot_data.years,
        percentiles=percentiles,
        total_label="Total Portfolio",
        median_without_fund_expenses=None,
        median_without_taxes=None,
        median_without_taxes_or_fund_expenses=None,
        cash=portfolio_plot_data.cash,
        bonds=portfolio_plot_data.bonds,
        realestate=None,
        pre_tax_assets=pre_tax_assets,
        post_tax_assets=post_tax_assets,
        roth_assets=roth_assets,
        hsa_assets=hsa_assets,
        raw_total_assets=None,
        simulated_shortfall_rate=getattr(
            portfolio_plot_data,
            "simulated_shortfall_rate",
            None,
        ),
    )


def save_tax_by_year_report_plot(
    output_folder,
    filename,
    yearly_tax_rows,
):
    _ensure_output_folder(output_folder)
    image_path = os.path.join(output_folder, filename)

    years = [row["Year"] for row in yearly_tax_rows]
    federal = [row["Federal Income Tax"] for row in yearly_tax_rows]
    state = [row["State Income Tax"] for row in yearly_tax_rows]
    payroll = [row["Payroll Tax"] for row in yearly_tax_rows]
    total = [row["Total Taxes"] for row in yearly_tax_rows]

    fig, ax = plt.subplots(figsize=(14, 7))

    try:
        ax.plot(years, federal, label="Federal Income Tax")
        ax.plot(years, state, label="State Income Tax")
        ax.plot(years, payroll, label="Payroll Tax")
        ax.plot(years, total, label="Total Taxes", linewidth=2)

        ax.set_title("Taxes by Year")
        ax.set_xlabel("Year")
        ax.set_ylabel("Taxes")
        ax.grid(True, axis="y", linestyle="--", alpha=0.5)
        ax.legend(loc="upper left")

        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda value, _: f"${value:,.0f}")
        )

        fig.savefig(image_path, dpi=200, bbox_inches="tight")
        return image_path

    finally:
        plt.close(fig)


def save_effective_tax_rate_report_plot(
    output_folder,
    filename,
    yearly_tax_rows,
):
    _ensure_output_folder(output_folder)
    image_path = os.path.join(output_folder, filename)

    years = [row["Year"] for row in yearly_tax_rows]
    effective_rates = [
        row["Effective Tax Rate"] * 100.0
        for row in yearly_tax_rows
    ]

    fig, ax = plt.subplots(figsize=(14, 7))

    try:
        ax.plot(years, effective_rates, linewidth=2)

        ax.set_title("Effective Tax Rate by Year")
        ax.set_xlabel("Year")
        ax.set_ylabel("Effective Tax Rate")
        ax.grid(True, axis="y", linestyle="--", alpha=0.5)

        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda value, _: f"{value:.0f}%")
        )

        fig.savefig(image_path, dpi=200, bbox_inches="tight")
        return image_path

    finally:
        plt.close(fig)


def save_taxable_income_source_report_plot(
    output_folder,
    filename,
    yearly_tax_rows,
):
    _ensure_output_folder(output_folder)
    image_path = os.path.join(output_folder, filename)

    years = [row["Year"] for row in yearly_tax_rows]

    rmd = [row["RMD"] for row in yearly_tax_rows]
    traditional = [row["Traditional Withdrawals"] for row in yearly_tax_rows]
    roth = [row["Roth Withdrawals"] for row in yearly_tax_rows]
    hsa = [row["HSA Withdrawals"] for row in yearly_tax_rows]

    fig, ax = plt.subplots(figsize=(14, 7))

    try:
        ax.plot(years, rmd, label="RMD")
        ax.plot(years, traditional, label="Traditional Withdrawals")
        ax.plot(years, roth, label="Roth Withdrawals")
        ax.plot(years, hsa, label="HSA Withdrawals")

        ax.set_title("Retirement Withdrawal Sources by Year")
        ax.set_xlabel("Year")
        ax.set_ylabel("Amount")
        ax.grid(True, axis="y", linestyle="--", alpha=0.5)
        ax.legend(loc="upper left")

        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda value, _: f"${value:,.0f}")
        )

        fig.savefig(image_path, dpi=200, bbox_inches="tight")
        return image_path

    finally:
        plt.close(fig)