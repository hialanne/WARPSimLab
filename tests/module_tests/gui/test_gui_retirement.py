# tests/gui/test_gui_retirement.py

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest


@pytest.fixture
def tk_root():
    """
    Withdrawn root for CI/headless friendliness.
    Avoid winfo_ismapped(); use winfo_manager()/state instead.
    """
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk not available: {e}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def mod_no_tooltip(monkeypatch):
    """
    Patch Tooltip to no-op to avoid timing / UI deps.
    """
    from src.warpsimlab.gui import gui_retirement as mod

    class DummyTooltip:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(mod, "Tooltip", DummyTooltip, raising=True)
    return mod


def _all_texts(widget: tk.Misc) -> list[str]:
    """
    Recursively collect text strings from common text-bearing ttk widgets.
    """
    out: list[str] = []

    def visit(node: tk.Misc):
        for child in node.winfo_children():
            if isinstance(
                child,
                (ttk.Label, ttk.Checkbutton, ttk.Button, ttk.Radiobutton),
            ):
                try:
                    out.append(child.cget("text"))
                except tk.TclError:
                    pass

            visit(child)

    visit(widget)
    return out


def _find_child_checkbutton_texts(widget: tk.Misc) -> list[str]:
    """
    Scan both direct children and children of child frames to find
    checkbutton texts (since gui_retirement nests inside frames).
    """
    out: list[str] = []

    def visit(node: tk.Misc):
        for c in node.winfo_children():
            if isinstance(c, ttk.Checkbutton):
                try:
                    out.append(c.cget("text"))
                except tk.TclError:
                    pass
            visit(c)

    visit(widget)
    return out


def _menu_values(option_menu: ttk.OptionMenu) -> tuple[str, ...]:
    """
    Read the menu entries from a ttk.OptionMenu.
    """
    menu = option_menu["menu"]
    end = menu.index("end")
    if end is None:
        return ()
    return tuple(menu.entrycget(i, "label") for i in range(end + 1))


def _state(widget: tk.Misc) -> str:
    """
    ttk widgets expose state differently; most support cget('state').
    """
    try:
        return str(widget.cget("state"))
    except tk.TclError:
        # Some containers (Frame) don't have 'state'
        return ""


def test_builds_intro_and_mode_checkboxes(mod_no_tooltip, tk_root):
    mod = mod_no_tooltip

    control_vars = {"_controls_dict": {}}
    frame = mod.RetirementEditFrame(
        tk_root,
        main_gui=None,
        control_vars=control_vars,
        persons=None,
        portfolio=None,
        title="Retirement",
    )
    frame.pack()

    texts = _all_texts(frame)

    # Top description label exists
    assert any("Defines how the simulation models retirement spending withdrawals" in t for t in texts)

    # Mode checkboxes exist (nested in frame, so scan recursively)
    cb_texts = _find_child_checkbutton_texts(frame)
    assert "Use Manually Entered Expenses" in cb_texts
    assert "Use Automatically Calculated Withdrawals" in cb_texts

    # Defaults: if use_mode missing, should set to "expenses"
    assert frame.controls["use_mode"] == "expenses"
    assert frame.use_expenses_var.get() is True
    assert frame.use_retirement_var.get() is False


def test_withdrawal_mode_menu_has_expected_options(mod_no_tooltip, tk_root):
    mod = mod_no_tooltip

    control_vars = {"_controls_dict": {}}
    frame = mod.RetirementEditFrame(tk_root, main_gui=None, control_vars=control_vars)
    frame.pack()

    values = _menu_values(frame.ret_mode_menu)
    assert values == (
        "Off",
        "Percentage",
        "Percentage + Inflation",
        "Fixed Dollar Amount",
        "Fixed Dollar Amount + Inflation",
    )

    # Default if missing: "Percentage + Inflation"
    assert frame.controls["retirement_withdraw_mode"] == "Percentage + Inflation"
    assert frame.ret_mode_var.get() == "Percentage + Inflation"


def test_controls_disabled_when_using_expenses_enabled_when_using_retirement(mod_no_tooltip, tk_root):
    mod = mod_no_tooltip

    control_vars = {"_controls_dict": {}}
    frame = mod.RetirementEditFrame(tk_root, main_gui=None, control_vars=control_vars)
    frame.pack()

    # Default is use_mode == "expenses" => controls disabled
    assert frame.controls["use_mode"] == "expenses"
    assert _state(frame.ret_mode_menu) == "disabled" or _state(frame.ret_mode_menu) == ""  # menu is a Menubutton
    assert _state(frame.pct_entry) == "disabled"
    assert _state(frame.dollars_entry) == "disabled"

    # Switch to retirement via UI var and invoke callback through the checkbutton
    frame.use_retirement_cb.invoke()

    assert frame.controls["use_mode"] == "retirement"
    assert frame.controls["always_use_expense_mode"] is False
    assert frame.use_expenses_var.get() is False
    assert frame.use_retirement_var.get() is True

    # Now controls enabled
    assert _state(frame.pct_entry) == "normal"
    assert _state(frame.dollars_entry) == "normal"
    # OptionMenu is a composite; the menubutton typically reports state
    assert _state(frame.ret_mode_menu) in ("normal", "")


def test_pct_and_dollars_write_back_to_controls_and_ignore_invalid(monkeypatch, mod_no_tooltip, tk_root):
    mod = mod_no_tooltip

    control_vars = {"_controls_dict": {}}
    frame = mod.RetirementEditFrame(tk_root, main_gui=None, control_vars=control_vars)
    frame.pack()

    shown_errors = []
    monkeypatch.setattr(mod.messagebox, "showerror", lambda *args, **kwargs: shown_errors.append((args, kwargs)))

    assert frame.controls["retirement_withdraw_pct"] == 4.0
    assert frame.controls["retirement_withdraw_dollars"] == 0.0

    assert frame._validate_retirement_field("5.5", "retirement_withdraw_pct") is True
    tk_root.update()
    tk_root.update_idletasks()
    assert frame.controls["retirement_withdraw_pct"] == pytest.approx(5.5)
    assert frame.pct_var.get() == frame._format_retirement_field(5.5)

    assert frame._validate_retirement_field("12000", "retirement_withdraw_dollars") is True
    tk_root.update()
    tk_root.update_idletasks()
    assert frame.controls["retirement_withdraw_dollars"] == pytest.approx(12000.0)
    assert frame.dollars_var.get() == frame._format_retirement_field(12000.0)

    prev_pct = frame.controls["retirement_withdraw_pct"]
    assert frame._validate_retirement_field("bad", "retirement_withdraw_pct") is True
    tk_root.update()
    tk_root.update_idletasks()
    assert frame.controls["retirement_withdraw_pct"] == pytest.approx(prev_pct)
    assert frame.pct_var.get() == frame._format_retirement_field(prev_pct)

    prev_dollars = frame.controls["retirement_withdraw_dollars"]
    assert frame._validate_retirement_field("bad", "retirement_withdraw_dollars") is True
    tk_root.update()
    tk_root.update_idletasks()
    assert frame.controls["retirement_withdraw_dollars"] == pytest.approx(prev_dollars)
    assert frame.dollars_var.get() == frame._format_retirement_field(prev_dollars)

    assert len(shown_errors) == 2
    assert all(args[0] == "Invalid Input" for args, _kwargs in shown_errors)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("retirement_withdraw_pct", "-1"),
        ("retirement_withdraw_pct", "NaN"),
        ("retirement_withdraw_pct", "inf"),
        ("retirement_withdraw_dollars", "-1"),
        ("retirement_withdraw_dollars", "NaN"),
        ("retirement_withdraw_dollars", "inf"),
    ],
)
def test_retirement_withdrawal_fields_reject_negative_and_nonfinite_values(
    monkeypatch,
    mod_no_tooltip,
    tk_root,
    field,
    bad_value,
):
    mod = mod_no_tooltip

    control_vars = {"_controls_dict": {}}
    frame = mod.RetirementEditFrame(tk_root, main_gui=None, control_vars=control_vars)
    frame.pack()

    shown_errors = []
    monkeypatch.setattr(mod.messagebox, "showerror", lambda *args, **kwargs: shown_errors.append((args, kwargs)))

    original_value = frame.controls[field]

    assert frame._validate_retirement_field(bad_value, field) is True
    tk_root.update()
    tk_root.update_idletasks()

    assert frame.controls[field] == pytest.approx(original_value)
    assert len(shown_errors) == 1


@pytest.mark.parametrize(
    "field",
    [
        "retirement_withdraw_pct",
        "retirement_withdraw_dollars",
    ],
)
def test_retirement_withdrawal_zero_is_valid(monkeypatch, mod_no_tooltip, tk_root, field):
    mod = mod_no_tooltip

    control_vars = {"_controls_dict": {}}
    frame = mod.RetirementEditFrame(tk_root, main_gui=None, control_vars=control_vars)
    frame.pack()

    shown_errors = []
    monkeypatch.setattr(mod.messagebox, "showerror", lambda *args, **kwargs: shown_errors.append((args, kwargs)))

    assert frame._validate_retirement_field("0", field) is True
    tk_root.update()
    tk_root.update_idletasks()

    assert frame.controls[field] == pytest.approx(0.0)
    assert shown_errors == []


def test_sequence_start_year_offset_accepts_nonnegative_integer(monkeypatch, mod_no_tooltip, tk_root):
    mod = mod_no_tooltip

    control_vars = {"_controls_dict": {}}
    frame = mod.RetirementEditFrame(tk_root, main_gui=None, control_vars=control_vars)
    frame.pack()

    shown_errors = []
    monkeypatch.setattr(mod.messagebox, "showerror", lambda *args, **kwargs: shown_errors.append((args, kwargs)))

    assert frame._validate_sequence_start_year_offset("150") is True
    tk_root.update()
    tk_root.update_idletasks()

    assert frame.controls["sequence_risk_start_year_offset"] == 150
    assert frame.sequence_risk_start_year_offset_var.get() == "150"
    assert shown_errors == []


@pytest.mark.parametrize("bad_value", ["-1", "1.5", "bad", ""])
def test_sequence_start_year_offset_rejects_invalid_values(
    monkeypatch,
    mod_no_tooltip,
    tk_root,
    bad_value,
):
    mod = mod_no_tooltip

    control_vars = {"_controls_dict": {}}
    frame = mod.RetirementEditFrame(tk_root, main_gui=None, control_vars=control_vars)
    frame.pack()

    shown_errors = []
    monkeypatch.setattr(mod.messagebox, "showerror", lambda *args, **kwargs: shown_errors.append((args, kwargs)))

    original_value = frame.controls["sequence_risk_start_year_offset"]

    assert frame._validate_sequence_start_year_offset(bad_value) is True
    tk_root.update()
    tk_root.update_idletasks()

    assert frame.controls["sequence_risk_start_year_offset"] == original_value
    assert frame.sequence_risk_start_year_offset_var.get() == str(original_value)
    assert len(shown_errors) == 1


def test_include_rmd_checkbox_default_and_writeback(mod_no_tooltip, tk_root):
    mod = mod_no_tooltip

    control_vars = {"_controls_dict": {}}
    frame = mod.RetirementEditFrame(tk_root, main_gui=None, control_vars=control_vars)
    frame.pack()

    # Default include_rmd True if missing
    assert frame.controls["include_rmd"] is True

    # The checkbutton lives in rmd_frame
    assert isinstance(frame.rmd_cb, ttk.Checkbutton)
    assert frame.rmd_cb.cget("text") == "Include RMDs"

    # Toggle via invoke() and verify writeback
    frame.rmd_cb.invoke()
    assert frame.controls["include_rmd"] is False

    frame.rmd_cb.invoke()
    assert frame.controls["include_rmd"] is True


def test_mode_change_updates_controls_retirement_withdraw_mode(mod_no_tooltip, tk_root):
    mod = mod_no_tooltip

    control_vars = {"_controls_dict": {}}
    frame = mod.RetirementEditFrame(tk_root, main_gui=None, control_vars=control_vars)
    frame.pack()

    # Set to "Off" should update controls and disable entries (via trace)
    frame.ret_mode_var.set("Off")
    assert frame.controls["retirement_withdraw_mode"] == "Off"
    assert _state(frame.pct_entry) == "disabled"
    assert _state(frame.dollars_entry) == "disabled"

    # Set to "Percentage" should enable entries (still depends on use_mode; but on_mode_change
    # directly toggles entries based on Off vs not Off)
    frame.ret_mode_var.set("Percentage")
    assert frame.controls["retirement_withdraw_mode"] == "Percentage"
    assert _state(frame.pct_entry) == "normal"
    assert _state(frame.dollars_entry) == "normal"