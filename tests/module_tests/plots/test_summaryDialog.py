# test_summaryDialog.py

import types
import numpy as np
import pytest

try:
    import tkinter as tk
except Exception:  # pragma: no cover
    tk = None

from src.warpsimlab.plots.summaryDialog import SummaryDialog


def make_person(age, retire_age):
    return types.SimpleNamespace(age=age, retire_age=retire_age)


def make_results(n=5, start_year=2025):
    years = np.arange(start_year, start_year + n)

    # Minimal set of keys referenced across the three tabs
    return {
        "year": years,
        "pre_tax_assets": np.linspace(100, 200, n),
        "post_tax_assets": np.linspace(50, 100, n),
        "real_estate": np.zeros(n),
        "total_assets": np.linspace(150, 300, n),
        "wages": np.linspace(80, 0, n),
        "rmd": np.zeros(n),
        "special_income": np.zeros(n),
        "social_security": np.zeros(n),
        "pensions": np.zeros(n),
        "annuities": np.zeros(n),
        "withdrawal": np.zeros(n),
        "emergency_pre_tax_used": np.zeros(n),
        "bond_interest": np.zeros(n),
        "cash_interest": np.zeros(n),
        "qualified_dividends": np.zeros(n),
        "gross_income": np.linspace(80, 40, n),
        "ira_401k": np.zeros(n),
        "employee_401k_contributions": np.zeros(n),
        "roth_ira_contributions": np.zeros(n),
        "roth_workplace_contributions": np.zeros(n),
        "roth_conversions": np.zeros(n),
        "roth_total_flows": np.zeros(n),
        "taxes": np.zeros(n),
        "tax_bracket": np.zeros(n),
        "net_income": np.linspace(60, 30, n),

        "expenses": np.linspace(50, 55, n),
        "net_cash_flow": np.linspace(10, -25, n),
        "fund_expenses": np.zeros(n),
    }


def make_config(root, *, second_person_enabled=False, always_use_expense_mode=True):
    # Only the fields referenced by SummaryDialog are included here.
    return types.SimpleNamespace(
        root=root,
        second_person_enabled=second_person_enabled,
        always_use_expense_mode=always_use_expense_mode,
        eq_mean=0.07,
        bd_mean=0.03,
        cs_mean=0.01,
        inflation_rate=0.02,
        fund_expense=0.001,
    )


def test_summary_dialog_constructs_and_destroys():
    """
    Smoke test only.

    This verifies the dialog can be constructed with a minimal results payload.
    It will skip automatically if Tk cannot initialize (common in headless CI).
    """
    if tk is None:
        pytest.skip("tkinter not available in this environment")

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk could not initialize (likely headless environment without display)")

    root.withdraw()  # avoid showing any real window

    results = make_results(n=5, start_year=2025)
    husband = make_person(age=60, retire_age=65)
    wife = make_person(age=60, retire_age=67)
    sim_config = make_config(root, second_person_enabled=True, always_use_expense_mode=True)

    dlg = SummaryDialog(results=results, husband=husband, wife=wife, sim_config=sim_config, title="Test Summary")
    dlg.update_idletasks()
    dlg.destroy()
    root.destroy()