from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.outputDialogs.summaryDialog.summaryIncome import build_income_tab


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")

    root.withdraw()
    yield root
    root.destroy()


def _make_results():
    def values(*items):
        return np.array(items, dtype=float)

    return {
        "year": np.array([2025, 2026, 2027, 2028]),
        "wages": values(80000, 70000, 0, 0),
        "employee_401k_contributions": values(10000, 9000, 0, 0),
        "hsa_employee_contributions": values(2000, 1800, 0, 0),
        "rmd": values(0, 0, 0, 5000),
        "social_security": values(0, 0, 30000, 30000),
        "pensions": values(0, 0, 12000, 12000),
        "annuities": values(0, 0, 6000, 6000),
        "special_income": values(1000, 2000, 3000, 4000),
        "bond_interest": values(1000, 1100, 1200, 1300),
        "cash_interest": values(500, 600, 700, 800),
        "qualified_equity_distributions": values(750, 800, 850, 900),
        "withdrawal": values(0, 0, 10000, 12000),
        "emergency_pre_tax_used": values(0, 0, 0, 2000),
        "gross_income": values(95250, 85300, 63750, 74000),
    }


def _make_dialog():
    dialog = SimpleNamespace(
        results=_make_results(),
        _report_header_font=("Arial", 14, "bold"),
        _report_body_font=("Courier New", 12),
        _report_body_bold_font=("Courier New", 12, "bold"),
    )

    dialog._get_display_indices = lambda: [0, 1, 2, 3]

    def add_year_headers(tab, column_indices, header_font):
        for col in range(5):
            ttk.Label(tab, text=f"Header {col}", font=header_font).grid(row=0, column=col)

    dialog._add_year_headers = add_year_headers

    return dialog


def _widget_texts(widget):
    texts = []

    for child in widget.winfo_children():
        if "text" in child.keys():
            texts.append(str(child.cget("text")))

        texts.extend(_widget_texts(child))

    return texts


def test_income_tab_builds(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog()

    tab = build_income_tab(dialog, notebook)

    assert tab.winfo_exists()
    assert notebook.tab(notebook.tabs()[0], "text") == "Income"


def test_gross_wages_adds_employee_contributions_back(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog()

    tab = build_income_tab(dialog, notebook)
    texts = _widget_texts(tab)

    gross_wages_index = texts.index("Gross Wages")
    gross_wages_values = texts[gross_wages_index + 1:gross_wages_index + 5]

    assert gross_wages_values == ["$92,000", "$80,800", "$0", "$0"]


def test_pensions_and_annuities_are_combined(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog()

    tab = build_income_tab(dialog, notebook)
    texts = _widget_texts(tab)

    row_index = texts.index("Pensions and Annuities")
    row_values = texts[row_index + 1:row_index + 5]

    assert row_values == ["$0", "$0", "$18,000", "$18,000"]


def test_income_tab_contains_all_major_income_rows(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog()

    tab = build_income_tab(dialog, notebook)
    texts = _widget_texts(tab)

    expected_labels = {
        "Gross Wages",
        "RMD",
        "Social Security",
        "Pensions and Annuities",
        "Special Income",
        "Bond Interest",
        "Cash Interest",
        "Qualified Equity Distributions",
        "Portfolio Withdrawals",
        "Emergency Pre-Tax Withdrawal",
        "Gross Income",
    }

    assert expected_labels.issubset(set(texts))


def test_income_note_is_present(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog()

    tab = build_income_tab(dialog, notebook)
    texts = _widget_texts(tab)

    assert any("Gross Income includes all modeled income" in text for text in texts)