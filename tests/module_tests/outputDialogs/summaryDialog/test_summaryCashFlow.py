from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.outputDialogs.summaryDialog.summaryCashFlow import build_cash_flow_tab


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
        "gross_income": values(90000, 80000, 60000, 50000),
        "employee_401k_contributions": values(10000, 9000, 0, 0),
        "hsa_employee_contributions": values(2000, 1800, 0, 0),
        "taxes": values(15000, 14000, 8000, 7000),
        "tax_bracket": values(0.22, 0.22, 0.12, 0.12),
        "net_income": values(63000, 55200, 52000, 43000),
        "hsa_employer_contributions": values(1000, 1000, 0, 0),
        "roth_ira_contributions": values(0, 0, 0, 0),
        "roth_workplace_contributions": values(0, 0, 0, 0),
        "hsa_qualified_withdrawals": values(0, 0, 1000, 1000),
        "hsa_taxable_withdrawals": values(0, 0, 0, 0),
        "expenses": values(50000, 50000, 50000, 50000),
        "net_cash_flow": values(14000, 6200, 3000, -6000),
        "fund_expenses": values(1000, 950, 900, 850),
    }


def _make_dialog(expense_mode=True):
    dialog = SimpleNamespace(
        results=_make_results(),
        sim_config=SimpleNamespace(always_use_expense_mode=expense_mode),
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


def _all_labels(widget):
    labels = []

    for child in widget.winfo_children():
        if isinstance(child, ttk.Label):
            labels.append(child)

        labels.extend(_all_labels(child))

    return labels


def _widget_texts(widget):
    return [str(label.cget("text")) for label in _all_labels(widget)]


def test_cash_flow_tab_builds(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog()

    tab = build_cash_flow_tab(dialog, notebook)

    assert tab.winfo_exists()
    assert notebook.tab(notebook.tabs()[0], "text") == "Cash Flow"


def test_tax_bracket_is_formatted_as_percentage(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog()

    tab = build_cash_flow_tab(dialog, notebook)
    texts = _widget_texts(tab)

    tax_bracket_index = texts.index("Tax Bracket")
    tax_bracket_values = texts[tax_bracket_index + 1:tax_bracket_index + 5]

    assert tax_bracket_values == ["22%", "22%", "12%", "12%"]


def test_expense_mode_includes_expense_and_net_cash_flow_rows(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog(expense_mode=True)

    tab = build_cash_flow_tab(dialog, notebook)
    texts = _widget_texts(tab)

    assert "Household Expenses" in texts
    assert "Net Cash Flow" in texts


def test_withdrawal_mode_omits_expense_and_net_cash_flow_rows(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog(expense_mode=False)

    tab = build_cash_flow_tab(dialog, notebook)
    texts = _widget_texts(tab)

    assert "Household Expenses" not in texts
    assert "Net Cash Flow" not in texts


def test_negative_net_cash_flow_is_red(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog(expense_mode=True)

    tab = build_cash_flow_tab(dialog, notebook)
    labels = _all_labels(tab)

    negative_label = next(label for label in labels if label.cget("text") == "$-6,000")

    assert str(negative_label.cget("foreground")) == "red"

def test_cash_flow_note_changes_with_mode(tk_root):
    expense_notebook = ttk.Notebook(tk_root)
    expense_tab = build_cash_flow_tab(_make_dialog(expense_mode=True), expense_notebook)
    expense_texts = _widget_texts(expense_tab)

    withdrawal_notebook = ttk.Notebook(tk_root)
    withdrawal_tab = build_cash_flow_tab(_make_dialog(expense_mode=False), withdrawal_notebook)
    withdrawal_texts = _widget_texts(withdrawal_tab)

    assert any("Net Cash Flow also reflects household expenses" in text for text in expense_texts)
    assert any("retirement withdrawal cash" in text for text in withdrawal_texts)