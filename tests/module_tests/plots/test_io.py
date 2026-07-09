# test_io.py

import csv
import types
import numpy as np
from pathlib import Path

from src.warpsimlab.plots.io import (
    write_summary_results_csv,
    write_income_results_csv,
    write_portfolio_results_csv
)


def make_config(tmp_path):
    return types.SimpleNamespace(
        csv_output_dir=str(tmp_path)
    )


# ---------------------------------------------------------
# write_summary_results_csv
# ---------------------------------------------------------

def test_write_summary_results_csv_creates_file(tmp_path):
    cfg = make_config(tmp_path)

    years = np.array([2025, 2026, 2027])

    results = {
        "year": years,
        "total_assets": [100, 200, 300],
        "pre_tax_assets": [50, 100, 150],
        "post_tax_assets": [50, 100, 150],
        "real_estate": [0, 0, 0],
        "gross_income": [10, 20, 30],
        "net_income": [8, 16, 24],
        "wages": [5, 10, 15],
        "rmd": [0, 0, 0],
        "social_security": [0, 0, 0],
        "pensions": [0, 0, 0],
        "annuities": [0, 0, 0],
        "fund_expenses": [1, 1, 1],
        "taxes": [2, 4, 6],
        "expenses": [3, 6, 9],
        "net_cash_flow": [5, 10, 15]
    }

    path = write_summary_results_csv(results, cfg)

    assert Path(path).exists()

    with open(path) as f:
        reader = list(csv.reader(f))

    # header + 3 rows
    assert len(reader) == 4

    header = reader[0]
    assert header[0] == "year"
    assert "total_assets" in header
    assert "taxes" in header

    # check first data row
    first_row = reader[1]
    assert int(first_row[0]) == 2025
    assert float(first_row[1]) == 100


# ---------------------------------------------------------
# write_income_results_csv
# ---------------------------------------------------------

def test_write_income_results_csv_basic(tmp_path):
    cfg = make_config(tmp_path)

    years = [2025, 2026]

    net_income = [100, 200]
    net_profit = [80, 150]
    taxes = [20, 50]

    breakdown = {
        "work": [50, 60],
        "pension": [0, 0],
        "annuity": [0, 0],
        "ss": [0, 0],
        "rmd": [0, 0],
        "withdrawal": [50, 140]
    }

    path = write_income_results_csv(
        years,
        net_income,
        net_profit,
        taxes,
        breakdown,
        cfg
    )

    assert Path(path).exists()

    with open(path) as f:
        reader = list(csv.reader(f))

    assert reader[0][0] == "year"
    assert "net_income" in reader[0]

    # first data row
    assert int(reader[1][0]) == 2025
    assert float(reader[1][1]) == 100


# ---------------------------------------------------------
# write_portfolio_results_csv
# ---------------------------------------------------------

class DummySimulationData:
    def __init__(self):
        self.baseline = [100, 200]
        self.cash = [10, 20]
        self.bonds = [30, 40]
        self.realestate = [0, 0]
        self.pre_tax_assets = [50, 100]
        self.post_tax_assets = [50, 100]


def test_write_portfolio_results_csv_basic(tmp_path):
    cfg = make_config(tmp_path)

    years = [2025, 2026]

    sim_data = DummySimulationData()

    path = write_portfolio_results_csv(years, sim_data, cfg)

    assert Path(path).exists()

    with open(path) as f:
        reader = list(csv.reader(f))

    assert reader[0][0] == "year"
    assert "total_assets" in reader[0]

    assert int(reader[1][0]) == 2025
    assert float(reader[1][1]) == 100