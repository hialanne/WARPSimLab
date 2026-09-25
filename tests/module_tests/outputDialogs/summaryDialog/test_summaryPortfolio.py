from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.outputDialogs.summaryDialog.summaryPortfolio import build_portfolio_tab


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")

    root.withdraw()
    yield root
    root.destroy()


def _make_results(include_roth_hsa=True):
    results = {
        "year": np.array([2025, 2026, 2027, 2028, 2029, 2030]),
        "pre_tax_assets": np.array([100000, 90000, 80000, 70000, 60000, 50000], dtype=float),
        "post_tax_assets": np.array([50000, 48000, 46000, 44000, 42000, 40000], dtype=float),
        "real_estate": np.array([200000, 205000, 210000, 215000, 220000, 225000], dtype=float),
        "total_assets": np.array([365000, 360500, 356000, 351500, 347000, 342500], dtype=float),
    }

    if include_roth_hsa:
        results["roth_assets"] = np.array([10000, 12000, 14000, 16000, 18000, 20000], dtype=float)
        results["hsa_assets"] = np.array([5000, 5500, 6000, 6500, 7000, 7500], dtype=float)

    return results


def _make_dialog(include_roth_hsa=True, second_person_enabled=True):
    return SimpleNamespace(
        results=_make_results(include_roth_hsa),
        husband=SimpleNamespace(age=60, retire_age=62),
        wife=SimpleNamespace(age=59, retire_age=63),
        sim_config=SimpleNamespace(second_person_enabled=second_person_enabled),
        _report_header_font=("Arial", 14, "bold"),
        _report_body_font=("Courier New", 12),
        _report_body_bold_font=("Courier New", 12, "bold"),
    )


def _widget_texts(widget):
    texts = []

    for child in widget.winfo_children():
        if "text" in child.keys():
            texts.append(str(child.cget("text")))

        texts.extend(_widget_texts(child))

    return texts


def test_portfolio_tab_builds(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog()

    tab = build_portfolio_tab(dialog, notebook)

    assert tab.winfo_exists()
    assert len(notebook.tabs()) == 1
    assert notebook.tab(notebook.tabs()[0], "text") == "Portfolio"


def test_portfolio_tab_uses_later_retirement_for_couple(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog()

    tab = build_portfolio_tab(dialog, notebook)
    texts = _widget_texts(tab)

    assert "Start of Simulation" in texts
    assert "Retirement" in texts
    assert "End of Simulation" in texts

    # Husband retires in 2 years; wife retires in 4 years.
    assert "Portfolio Value in 2029" in texts


def test_portfolio_total_includes_roth_and_hsa(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog()

    tab = build_portfolio_tab(dialog, notebook)
    texts = _widget_texts(tab)

    total_lines = [text for text in texts if text.startswith("Total Portfolio:")]

    assert len(total_lines) == 3
    assert "$165,000" in total_lines[0]


def test_portfolio_missing_roth_and_hsa_default_to_zero(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog(include_roth_hsa=False)

    tab = build_portfolio_tab(dialog, notebook)
    texts = _widget_texts(tab)

    roth_lines = [text for text in texts if text.startswith("Roth Assets:")]
    hsa_lines = [text for text in texts if text.startswith("HSA Assets:")]
    total_lines = [text for text in texts if text.startswith("Total Portfolio:")]

    assert "$0" in roth_lines[0]
    assert "$0" in hsa_lines[0]
    assert "$150,000" in total_lines[0]


def test_single_person_retirement_uses_husband_retirement(tk_root):
    notebook = ttk.Notebook(tk_root)
    dialog = _make_dialog(second_person_enabled=False)

    tab = build_portfolio_tab(dialog, notebook)
    texts = _widget_texts(tab)

    assert "Portfolio Value in 2027" in texts