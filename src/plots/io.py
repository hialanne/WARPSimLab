# sim/io.py

import csv
import os
import numpy as np


# ----------------------------
# Yearly Summary CSV
# ----------------------------

def write_summary_results_csv(results, sim_config, prefix="summary"):
    """
    Writes all yearly summary simulation results to CSV.
    """
    output_dir = sim_config.csv_output_dir
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{prefix}.csv")

    years = results.get("year", np.arange(len(next(iter(results.values())))))

    keys = [
        "total_assets",
        "pre_tax_assets",
        "post_tax_assets",
        "real_estate",
        "gross_income",
        "net_income",
        "wages",
        "rmd",
        "social_security",
        "pensions",
        "annuities",
        "fund_expenses",
        "taxes",
        "expenses",
        "net_cash_flow"
    ]
    columns = ["year"] + keys

    with open(filename, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for i in range(len(years)):
            row = [years[i]] + [results[k][i] for k in keys]
            writer.writerow(row)

    return filename

def write_income_results_csv(
    years,
    net_income,
    net_profit,
    yearly_taxes,
    breakdown,
    sim_config,
    prefix="income_simulation"
):
    """
    Writes yearly net income, net profit, taxes, and income breakdown to CSV.
    """

    output_dir = sim_config.csv_output_dir
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{prefix}.csv")

    # Columns
    keys = ["net_income", "net_profit", "taxes"]
    breakdown_keys = list(breakdown.keys())  # e.g., work, pension, annuity, ss, rmd
    columns = ["year"] + keys + breakdown_keys

    with open(filename, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for i, year in enumerate(years):
            row = [
                year,
                net_income[i],
                net_profit[i],
                yearly_taxes[i],
            ]
            row += [breakdown[k][i] for k in breakdown_keys]
            writer.writerow(row)

    return filename


def write_portfolio_results_csv(years, simulation_data, sim_config, prefix="portfolio_simulation"):
    """
    Writes baseline portfolio simulation results (inflation-adjusted) to CSV.
    Only first simulation run is included.
    """

    output_dir = sim_config.csv_output_dir
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{prefix}.csv")

    # Columns
    columns = [
        "year",
        "total_assets",
        "cash",
        "bonds",
        "real_estate",
        "pre_tax_assets",
        "post_tax_assets"
    ]

    with open(filename, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for i, year in enumerate(years):
            row = [
                year,
                simulation_data.baseline[i],
                simulation_data.cash[i],
                simulation_data.bonds[i],
                simulation_data.realestate[i],
                simulation_data.pre_tax_assets[i],
                simulation_data.post_tax_assets[i]
            ]
            writer.writerow(row)

    return filename


