# io_utils.py

import os
import sys
import json
import numpy as np

from src.warpsimlab.dataClasses.person import Person



def load_financial_data_from_json(file_path):
    """
    Loads the JSON and returns the dict.
    Does NOT modify GUI.
    """
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return data

    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decode error in {file_path}: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error loading {file_path}: {e}")

    return None

def _get_market_history_path():
    """
    Return path to financialMarketHistory.json
    Works for:
    - python WARPSimLab.py
    - PyInstaller one-folder
    - PyInstaller one-file
    """
    if hasattr(sys, "_MEIPASS"):
        # Running under PyInstaller
        base_path = sys._MEIPASS
    else:
        # Running from source
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

    return os.path.join(base_path, "dataFiles", "financialMarketHistory.json")


def get_data_file_path(filename):
    """
    Return the full path to a file inside src/dataFiles.

    Works for:
    - python WARPSimLab.py
    - PyInstaller one-folder
    - PyInstaller one-file
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

    return os.path.join(base_path, "dataFiles", filename)


def _load_csv_rows(file_path):
    """
    Load a simple CSV file and return (header, rows).

    Returns
    -------
    tuple[list[str], list[list[str]]]
        header row and remaining data rows

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file is empty.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8-sig") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    if not lines:
        raise ValueError(f"CSV file is empty: {file_path}")

    rows = [line.split(",") for line in lines]
    header = [col.strip() for col in rows[0]]
    data_rows = [[cell.strip() for cell in row] for row in rows[1:]]

    return header, data_rows


def _require_columns(header, required_columns, file_path):
    """
    Validate required columns and return a name->index mapping.
    """
    col_index = {name: idx for idx, name in enumerate(header)}

    missing = [name for name in required_columns if name not in col_index]
    if missing:
        raise ValueError(
            f"Missing required columns in {file_path}: {missing}. "
            f"Found columns: {header}"
        )

    return col_index


def load_historical_asset_returns_csv(filename="us_asset_returns_1876_2025.csv"):
    """
    Load annual historical asset returns from src/dataFiles/<filename>.

    Accepted column names
    ---------------------
    Year or year
    Equity_Return_Pct or equity
    Bond_Return_Pct or bonds
    Cash_Return_Pct or cash
    Real_Estate_Return_Pct or real_estate

    Notes
    -----
    - Percentage values such as 10.5 are converted to decimal 0.105.
    - Rows are sorted by year ascending.
    - Duplicate years are rejected.
    """
    file_path = get_data_file_path(filename)
    header, data_rows = _load_csv_rows(file_path)

    # Accept the real CSV headers you generated, plus simpler aliases.
    aliases = {
        "year": ["year", "Year"],
        "equity": ["equity", "Equity_Return_Pct"],
        "bonds": ["bonds", "Bond_Return_Pct"],
        "cash": ["cash", "Cash_Return_Pct"],
        "real_estate": ["real_estate", "Real_Estate_Return_Pct"],
    }

    header_index = {name: idx for idx, name in enumerate(header)}

    resolved = {}
    missing = []

    for logical_name, candidates in aliases.items():
        found = None
        for candidate in candidates:
            if candidate in header_index:
                found = header_index[candidate]
                break
        if found is None:
            missing.append(f"{logical_name} (accepted: {candidates})")
        else:
            resolved[logical_name] = found

    if missing:
        raise ValueError(
            f"Missing required columns in {file_path}: {missing}. "
            f"Found columns: {header}"
        )

    parsed_rows = []

    for row_num, row in enumerate(data_rows, start=2):
        try:
            year = int(row[resolved["year"]])
            equity = float(row[resolved["equity"]]) / 100.0
            bonds = float(row[resolved["bonds"]]) / 100.0
            cash = float(row[resolved["cash"]]) / 100.0
            real_estate = float(row[resolved["real_estate"]]) / 100.0
        except IndexError:
            raise ValueError(
                f"Row {row_num} in {file_path} does not have enough columns."
            )
        except ValueError as e:
            raise ValueError(
                f"Invalid numeric value in row {row_num} of {file_path}: {e}"
            )

        parsed_rows.append((year, equity, bonds, cash, real_estate))

    if not parsed_rows:
        raise ValueError(f"No historical asset return rows found in {file_path}")

    parsed_rows.sort(key=lambda x: x[0])

    years = np.array([r[0] for r in parsed_rows], dtype=int)

    if len(np.unique(years)) != len(years):
        raise ValueError(f"Duplicate years found in historical asset returns file: {file_path}")

    equity = np.array([r[1] for r in parsed_rows], dtype=float)
    bonds = np.array([r[2] for r in parsed_rows], dtype=float)
    cash = np.array([r[3] for r in parsed_rows], dtype=float)
    real_estate = np.array([r[4] for r in parsed_rows], dtype=float)

    return {
        "file_path": file_path,
        "years": years,
        "eq": equity,
        "bd": bonds,
        "cs": cash,
        "re": real_estate,
        "num_years": len(years),
    }


def load_historical_inflation_csv(filename="us_inflation_1876_2025_real.csv"):
    """
    Load annual historical inflation data from src/dataFiles/<filename>.

    Accepted column names
    ---------------------
    Year or year
    Inflation_Rate_Pct or inflation

    Notes
    -----
    - Values are expected to be annual percentage inflation rates.
    - Returned inflation array is converted to decimal form.
    - Rows are sorted by year ascending.
    - Duplicate years are rejected.
    """
    file_path = get_data_file_path(filename)
    header, data_rows = _load_csv_rows(file_path)

    aliases = {
        "year": ["year", "Year"],
        "inflation": ["inflation", "Inflation_Rate_Pct"],
    }

    header_index = {name: idx for idx, name in enumerate(header)}

    resolved = {}
    missing = []

    for logical_name, candidates in aliases.items():
        found = None
        for candidate in candidates:
            if candidate in header_index:
                found = header_index[candidate]
                break
        if found is None:
            missing.append(f"{logical_name} (accepted: {candidates})")
        else:
            resolved[logical_name] = found

    if missing:
        raise ValueError(
            f"Missing required columns in {file_path}: {missing}. "
            f"Found columns: {header}"
        )

    parsed_rows = []

    for row_num, row in enumerate(data_rows, start=2):
        try:
            year = int(row[resolved["year"]])
            inflation = float(row[resolved["inflation"]]) / 100.0
        except IndexError:
            raise ValueError(
                f"Row {row_num} in {file_path} does not have enough columns."
            )
        except ValueError as e:
            raise ValueError(
                f"Invalid numeric value in row {row_num} of {file_path}: {e}"
            )

        parsed_rows.append((year, inflation))

    if not parsed_rows:
        raise ValueError(f"No historical inflation rows found in {file_path}")

    parsed_rows.sort(key=lambda x: x[0])

    years = np.array([r[0] for r in parsed_rows], dtype=int)

    if len(np.unique(years)) != len(years):
        raise ValueError(f"Duplicate years found in historical inflation file: {file_path}")

    inflation = np.array([r[1] for r in parsed_rows], dtype=float)

    return {
        "file_path": file_path,
        "years": years,
        "inflation": inflation,
        "num_years": len(years),
    }


def load_market_data(default_dataset="25_year_data"):
    """
    Load historical market data from financialMarketHistory.json.
    If the file doesn't exist or is invalid, fall back to built-in constants.

    Returns a dictionary with keys: 'eq_mean', 'bd_mean', 'cs_mean', 'eq_std', 'bd_std', 'cs_std'.
    The returned values are from the selected default_dataset (e.g., "25_year_data").
    """
    built_in = {
        "25_year_data": {
            "eq_mean": 7.98,
            "bd_mean": 3.93,
            "cs_mean": 2.0,
            "re_mean": 2.0,
            "eq_std": 22.0,
            "bd_std": 6.0,
            "cs_std": 0.2,
            "re_std": 0.2,
            "inflation": 2.8
        },
        "50_year_data": {
            "eq_mean": 12.2,
            "bd_mean": 6.7,
            "cs_mean": 3.5,
            "re_mean": 3.5,
            "eq_std": 18.0,
            "bd_std": 7.0,
            "cs_std": 0.3,
            "re_std": 0.3,
            "inflation": 3.5
        },
        "100_year_data": {
            "eq_mean": 10.52,
            "bd_mean": 5.5,
            "cs_mean": 3.5,
            "re_mean": 3.5,
            "eq_std": 19.0,
            "bd_std": 7.0,
            "cs_std": 0.4,
            "re_std": 0.4,
            "inflation": 3.9
        },
        "depression": {
            "eq_mean": -12.1,
            "bd_mean": 4.7,
            "cs_mean": 2,
            "re_mean": 2,
            "eq_std": 26.95,
            "bd_std": 5.92,
            "cs_std": 1,
            "re_std": 1,
            "inflation": -1.6
        },
        "irrational_exuberance": {
            "eq_mean": 16.1,
            "bd_mean": 7.7,
            "cs_mean": 7.46,
            "re_mean": 7.46,
            "eq_std": 13.3,
            "bd_std": 9.7,
            "cs_std": 0.5,
            "re_std": 0.5,
            "inflation": 3.0
        }
    }

    # Try reading the JSON file
    market_file = _get_market_history_path()

    if os.path.exists(market_file):
        try:
            with open(market_file, "r") as f:
                data = json.load(f)
            # Return the requested dataset if present
            return data.get(default_dataset, built_in.get(default_dataset))
        except (json.JSONDecodeError, IOError):
            # On error, fall back to built-in
            print('Error parsing market history file.\n')
            return built_in.get(default_dataset)
    else:
        # File doesn't exist
        print('Did not find market history file.\n')
        return built_in.get(default_dataset)


def save_financial_data_to_file(file_path, data):
    """
    Save the given financial data dictionary to a JSON file.

    Args:
        file_path (str): Path to save the JSON file.
        data (dict): The structured financial data.
    """
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
