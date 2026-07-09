# test_gui_historicalData.py

from __future__ import annotations

import tkinter as tk
from types import SimpleNamespace

import pytest


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def patched_module(monkeypatch):
    from src.warpsimlab.gui import gui_historicalData as mod

    # Disable tooltips during testing
    class DummyTooltip:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(mod, "Tooltip", DummyTooltip, raising=True)

    return mod


def _make_data():
    return SimpleNamespace(
        eq_mean=7,
        bd_mean=3,
        cs_mean=1,
        re_mean=4,
        eq_std=15,
        bd_std=5,
        cs_std=1,
        re_std=6,
        inflation=2,
        historical_market="25_year_data",
    )


def test_initial_values_loaded_into_stringvars(tk_root, patched_module):
    mod = patched_module
    data = _make_data()

    frame = mod.HistoricalEditFrame(tk_root, data)
    frame.pack()

    assert frame.eq_mean_var.get() == "7"
    assert frame.bd_mean_var.get() == "3"
    assert frame.cs_mean_var.get() == "1"
    assert frame.re_mean_var.get() == "4"

    assert frame.eq_std_var.get() == "15"
    assert frame.bd_std_var.get() == "5"
    assert frame.cs_std_var.get() == "1"
    assert frame.re_std_var.get() == "6"

    assert frame.inflation_var.get() == "2"


def test_stringvar_updates_data_object(tk_root, patched_module):
    mod = patched_module
    data = _make_data()

    frame = mod.HistoricalEditFrame(tk_root, data)
    frame.pack()

    assert frame._validate_historical_field_on_focusout("8.5", "eq_mean_var") is True

    tk_root.update()
    tk_root.update_idletasks()

    assert data.eq_mean == 8.5
    assert frame.eq_mean_var.get() == "8.5"


def test_invalid_numeric_input_is_ignored(tk_root, patched_module):
    mod = patched_module
    data = _make_data()

    frame = mod.HistoricalEditFrame(tk_root, data)
    frame.pack()

    assert frame._validate_historical_field_on_focusout("invalid", "eq_mean_var") is True

    tk_root.update()
    tk_root.update_idletasks()

    assert data.eq_mean == 7
    assert frame.eq_mean_var.get() == "7"


def test_historical_market_selection_updates_data(tk_root, patched_module):
    mod = patched_module
    data = _make_data()

    frame = mod.HistoricalEditFrame(tk_root, data)
    frame.pack()

    frame.historical_market_var.set("50_year_data")

    assert data.historical_market == "50_year_data"


def test_update_market_fields_populates_vars(monkeypatch, tk_root, patched_module):
    mod = patched_module
    data = _make_data()

    fake_values = {
        "eq_mean": 9,
        "bd_mean": 4,
        "cs_mean": 2,
        "re_mean": 5,
        "eq_std": 12,
        "bd_std": 6,
        "cs_std": 1.5,
        "re_std": 7,
        "inflation": 3,
    }

    monkeypatch.setattr(
        mod,
        "load_market_data",
        lambda selection: fake_values,
        raising=True,
    )

    frame = mod.HistoricalEditFrame(tk_root, data)
    frame.pack()

    frame.historical_market_var.set("50_year_data")
    frame.update_market_fields()

    assert frame.eq_mean_var.get() == "9"
    assert frame.bd_mean_var.get() == "4"
    assert frame.cs_mean_var.get() == "2"
    assert frame.re_mean_var.get() == "5"

    assert frame.eq_std_var.get() == "12"
    assert frame.bd_std_var.get() == "6"
    assert frame.cs_std_var.get() == "1.5"
    assert frame.re_std_var.get() == "7"

    assert frame.inflation_var.get() == "3"

    assert data.eq_mean == 9
    assert data.bd_mean == 4
    assert data.cs_mean == 2
    assert data.re_mean == 5

    assert data.eq_std == 12
    assert data.bd_std == 6
    assert data.cs_std == 1.5
    assert data.re_std == 7

    assert data.inflation == 3
