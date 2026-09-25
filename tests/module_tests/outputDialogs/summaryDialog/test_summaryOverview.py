from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.outputDialogs.summaryDialog.summaryOverview import build_summary_tab


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")

    root.withdraw()
    yield root
    root.destroy()


def _make_results(funding_gap=0.0, shortfall_rate=0.0):
    return {
        "pre_tax_assets": np.array([100000, 90000, 80000], dtype=float),
        "post_tax_assets": np.array([50000, 45000, 40000], dtype=float),
        "roth_assets": np.array([10000, 12000, 14000], dtype=float),
        "hsa_assets": np.array([5000, 6000, 7000], dtype=float),
        "taxes": np.array([15000, 10000, 8000], dtype=float),
        "expenses": np.array([50000, 50000, 50000], dtype=float),
        "funding_gap": np.array([0, 0, funding_gap], dtype=float),
        "fund_expenses": np.array([1000, 900, 800], dtype=float),
        "simulated_shortfall_rate": shortfall_rate,
    }


def _make_dialog(second_person_enabled=True, funding_gap=0.0, shortfall_rate=0.0):
    return SimpleNamespace(
        results=_make_results(funding_gap, shortfall_rate),
        husband=SimpleNamespace(age=60, retire_age=65),
        wife=SimpleNamespace(age=58, retire_age=66),
        sim_config=SimpleNamespace(
            second_person_enabled=second_person_enabled,
            eq_mean=0.07,
            bd_mean=0.03,
            cs_mean=0.02,
            inflation_rate=0.025,
            fund_expense=0.001,
        ),
        _report_header_font=("Arial", 14, "bold"),
        _report_body_font=("Courier New", 12),
        _report_body_bold_font=("Courier New", 12, "bold"),
    )


def _all_labels(widget):
    labels = []

    for child in widget.winfo_children():
        if isinstance(child, ttk.Label):
            labels.append(child)

        labels.extend(_all_labels(child))

    return labels


def _widget_texts(widget):
    return [str(label.cget("text")) for label in _all_labels(widget)]


def test_summary_overview_tab_builds(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog()

    tab = build_summary_tab(dialog, notebook)

    assert tab.winfo_exists()
    assert notebook.tab(notebook.tabs()[0], "text") == "Summary"


def test_summary_portfolio_totals_include_roth_and_hsa(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog()

    tab = build_summary_tab(dialog, notebook)
    texts = _widget_texts(tab)

    assert any("Portfolio Start:" in text and "$165,000" in text for text in texts)
    assert any("Portfolio End:" in text and "$141,000" in text for text in texts)


def test_summary_displays_second_person_when_enabled(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog(second_person_enabled=True)

    tab = build_summary_tab(dialog, notebook)
    texts = _widget_texts(tab)

    assert any("Wife Age:" in text and "58" in text for text in texts)
    assert any("Wife Retirement Age:" in text and "66" in text for text in texts)


def test_summary_omits_second_person_when_disabled(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog(second_person_enabled=False)

    tab = build_summary_tab(dialog, notebook)
    texts = _widget_texts(tab)

    assert not any("Wife Age:" in text for text in texts)
    assert not any("Wife Retirement Age:" in text for text in texts)


def test_positive_lifetime_funding_gap_is_red(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog(funding_gap=5000)

    tab = build_summary_tab(dialog, notebook)
    labels = _all_labels(tab)

    funding_gap_label = next(label for label in labels if "Lifetime Funding Gap:" in label.cget("text"))

    assert "$5,000" in funding_gap_label.cget("text")
    assert str(funding_gap_label.cget("foreground")) == "red"


def test_summary_displays_assumption_values(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog()

    tab = build_summary_tab(dialog, notebook)
    texts = _widget_texts(tab)

    assert any("Expected Annual Stock Return:" in text and "7.00%" in text for text in texts)
    assert any("Expected Annual Bond Return:" in text and "3.00%" in text for text in texts)
    assert any("Expected Annual Cash Return:" in text and "2.00%" in text for text in texts)
    assert any("Expected Inflation Rate:" in text and "2.50%" in text for text in texts)
    assert any("Fund Expense Rate:" in text and "0.10%" in text for text in texts)


def test_summary_displays_shortfall_rate(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog(shortfall_rate=12.0)

    tab = build_summary_tab(dialog, notebook)
    texts = _widget_texts(tab)

    assert any("12% of modeled scenarios resulted" in text for text in texts)