# test_gui_expenses_taxes.py

from __future__ import annotations

from types import ModuleType
import sys
import tkinter as tk
from tkinter import ttk

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
def stub_gui_taxes(monkeypatch):
    """
    gui_expenses_taxes imports TaxesEditFrame from src.warpsimlab.gui.gui_taxes.
    If gui_taxes isn't present/loaded in the test environment, create a stub
    module so import succeeds deterministically.
    """
    m = ModuleType("src.warpsimlab.gui.gui_taxes")

    class StubTaxesEditFrame(ttk.Frame):
        def __init__(self, parent, control_vars=None, title="Taxes", **kwargs):
            super().__init__(parent, **kwargs)
            self._captured = {
                "control_vars": control_vars,
                "title": title,
            }

    m.TaxesEditFrame = StubTaxesEditFrame
    monkeypatch.setitem(sys.modules, "src.warpsimlab.gui.gui_taxes", m)
    return m


def test_basic_mode_creates_expenses_only_and_returns_early(tk_root, stub_gui_taxes, monkeypatch):
    """
    In Basic mode, the class should:
      - create a left container
      - instantiate ExpensesEditFrame
      - return early (no separator, no TaxesEditFrame)
    """
    # Import after stubbing gui_taxes to ensure module import succeeds
    from src.warpsimlab.gui import gui_expenses_taxes as mod

    captured = {"expenses_called": 0, "taxes_called": 0}

    class StubExpensesEditFrame(ttk.Frame):
        def __init__(self, parent, expensesDict=None, title="Expenses", **kwargs):
            super().__init__(parent, **kwargs)
            captured["expenses_called"] += 1
            self._captured = {"expensesDict": expensesDict, "title": title}

    # Patch the already-imported class references inside the module under test
    monkeypatch.setattr(mod, "ExpensesEditFrame", StubExpensesEditFrame, raising=True)

    # Also patch TaxesEditFrame to count calls (should be 0 in Basic)
    class StubTaxesEditFrame(ttk.Frame):
        def __init__(self, parent, control_vars=None, title="Taxes", **kwargs):
            super().__init__(parent, **kwargs)
            captured["taxes_called"] += 1

    monkeypatch.setattr(mod, "TaxesEditFrame", StubTaxesEditFrame, raising=True)

    frame = mod.ExpensesTaxesFrame(
        tk_root,
        expensesDict={"expenses": []},
        control_vars={"x": 1},
        mode="Basic",
    )
    frame.pack()

    assert frame.mode == "Basic"
    assert captured["expenses_called"] == 1
    assert captured["taxes_called"] == 0

    # In Basic mode, no ttk.Separator should exist as a direct child
    separators = [w for w in frame.winfo_children() if isinstance(w, ttk.Separator)]
    assert separators == []


def test_advanced_mode_creates_expenses_separator_and_taxes(tk_root, stub_gui_taxes, monkeypatch):
    """
    In Advanced (non-Basic) mode, the class should:
      - create left container, separator, right container
      - instantiate both ExpensesEditFrame and TaxesEditFrame
    """
    from src.warpsimlab.gui import gui_expenses_taxes as mod

    captured = {"expenses_args": None, "taxes_args": None}

    class StubExpensesEditFrame(ttk.Frame):
        def __init__(self, parent, expensesDict=None, title="Expenses", **kwargs):
            super().__init__(parent, **kwargs)
            captured["expenses_args"] = {"expensesDict": expensesDict, "title": title}

    class StubTaxesEditFrame(ttk.Frame):
        def __init__(self, parent, control_vars=None, title="Taxes", **kwargs):
            super().__init__(parent, **kwargs)
            captured["taxes_args"] = {"control_vars": control_vars, "title": title}

    monkeypatch.setattr(mod, "ExpensesEditFrame", StubExpensesEditFrame, raising=True)
    monkeypatch.setattr(mod, "TaxesEditFrame", StubTaxesEditFrame, raising=True)

    control_vars = {"filing_status": "Married filing jointly"}
    expenses_dict = {"expenses": [{"start_year": 2025, "end_year": None, "cost": 1000, "comment": ""}]}

    frame = mod.ExpensesTaxesFrame(
        tk_root,
        expensesDict=expenses_dict,
        control_vars=control_vars,
        mode="Advanced",
    )
    frame.pack()

    assert frame.mode == "Advanced"
    assert captured["expenses_args"] == {"expensesDict": expenses_dict, "title": "Expenses"}
    assert captured["taxes_args"] == {"control_vars": control_vars, "title": "Taxes"}

    # Should have a vertical separator in Advanced mode
    separators = [w for w in frame.winfo_children() if isinstance(w, ttk.Separator)]
    assert len(separators) == 1
    assert separators[0].cget("orient") == "vertical"