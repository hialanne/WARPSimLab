# test_gui_taxes.py
#
# Drop-in GUI tests for src.warpsimlab.gui.gui_taxes.TaxesEditFrame
# Matches the current implementation in gui_taxes.py (no Tooltip, uses _state_combo/_state_var,
# and uses _sync_state_tax_enabled driven by calculate_income_taxes).
#
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import pytest

@pytest.fixture
def tk_root():
    """Hidden Tk root. Skip if Tk isn't available."""
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk not available: {e}")
    root.withdraw()
    yield root
    root.destroy()


def _control_vars(**overrides):
    # Provide keys that gui_taxes expects to exist.
    d = {
        "calculate_income_taxes": True,
        "calculate_payroll_taxes": True,
        "tax_filing_status": "Married filing jointly",
        "calculate_state_taxes": False,
        "state_of_residence": "CA",
    }
    d.update(overrides)
    return {"_controls_dict": d}


def test_init_requires_expected_keys_present(tk_root):
    """
    gui_taxes.py currently raises KeyError if required keys are missing.
    This test documents that behavior (conservative: don't change production code).
    """
    from src.warpsimlab.gui import gui_taxes as mod

    control_vars = {"_controls_dict": {}}
    with pytest.raises(KeyError):
        mod.TaxesEditFrame(tk_root, control_vars=control_vars)


def test_state_selector_disabled_when_federal_taxes_off(tk_root):
    """
    _sync_state_tax_enabled() enables/disables the state combobox based on
    controls["calculate_income_taxes"].
    """
    from src.warpsimlab.gui import gui_taxes as mod

    control_vars = _control_vars(calculate_income_taxes=False, state_of_residence="CO")
    frame = mod.TaxesEditFrame(tk_root, control_vars=control_vars)
    frame.pack()

    # __init__ calls _sync_state_tax_enabled()
    assert str(frame._state_combo.cget("state")) == "disabled"

def test_state_selector_readonly_when_federal_taxes_on(tk_root):
    from src.warpsimlab.gui import gui_taxes as mod

    control_vars = _control_vars(calculate_income_taxes=True, state_of_residence="CO")
    frame = mod.TaxesEditFrame(tk_root, control_vars=control_vars)
    frame.pack()

    assert str(frame._state_combo.cget("state")) == "readonly"


def test_toggling_calculate_income_taxes_updates_state_selector_state(tk_root):
    """
    We locate the 'Calculate Income Taxes' checkbutton and toggle it,
    verifying that the trace callback updates the controls dict and
    calls _sync_state_tax_enabled().
    """
    from src.warpsimlab.gui import gui_taxes as mod

    control_vars = _control_vars(calculate_income_taxes=True, state_of_residence="CA")
    frame = mod.TaxesEditFrame(tk_root, control_vars=control_vars)
    frame.pack()

    assert control_vars["_controls_dict"]["calculate_income_taxes"] is True
    assert str(frame._state_combo.cget("state")) == "readonly"

    # Find the "Calculate Income Taxes" checkbutton and toggle it off/on.
    income_cb = None
    for child in frame.winfo_children():
        if isinstance(child, ttk.Checkbutton) and child.cget("text") == "Calculate Income Taxes":
            income_cb = child
            break

    assert income_cb is not None, "Could not find 'Calculate Income Taxes' checkbutton"

    # Invoke toggles variable -> trace updates dict and calls _sync_state_tax_enabled()
    income_cb.invoke()
    assert control_vars["_controls_dict"]["calculate_income_taxes"] is False
    assert str(frame._state_combo.cget("state")) == "disabled"

    income_cb.invoke()
    assert control_vars["_controls_dict"]["calculate_income_taxes"] is True
    assert str(frame._state_combo.cget("state")) == "readonly"


def test_state_selection_updates_controls_dict(tk_root):
    from src.warpsimlab.gui import gui_taxes as mod

    control_vars = _control_vars(calculate_income_taxes=True, state_of_residence="CA")
    frame = mod.TaxesEditFrame(tk_root, control_vars=control_vars)
    frame.pack()

    frame._state_var.set("NY")
    assert control_vars["_controls_dict"]["state_of_residence"] == "NY"


def test_filing_status_selection_updates_controls_dict(tk_root):
    """
    gui_taxes.py uses a StringVar local to _add_filing_status; it isn't stored.
    So we find the filing-status Combobox and set its textvariable directly.
    """
    from src.warpsimlab.gui import gui_taxes as mod
    from tkinter import ttk

    control_vars = _control_vars(tax_filing_status="Single")
    frame = mod.TaxesEditFrame(tk_root, control_vars=control_vars)
    frame.pack()

    # Find the filing status combobox by matching its values list.
    filing_combo = None
    for child in frame.winfo_children():
        if isinstance(child, ttk.Combobox):
            vals = tuple(child.cget("values"))
            if vals == mod.TaxesEditFrame.FILING_STATUSES:
                filing_combo = child
                break

    assert filing_combo is not None, "Could not find Tax Filing Status combobox"

    filing_combo.set("Married filing jointly")
    assert control_vars["_controls_dict"]["tax_filing_status"] == "Married filing jointly"

    filing_combo.set("Single")
    assert control_vars["_controls_dict"]["tax_filing_status"] == "Single"