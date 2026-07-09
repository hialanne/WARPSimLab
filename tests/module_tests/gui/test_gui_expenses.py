# test_gui_expenses.py

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
def no_tooltip(monkeypatch):
    from src.warpsimlab.gui import gui_expenses as mod

    class DummyTooltip:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(mod, "Tooltip", DummyTooltip, raising=True)
    return mod


def _make_expense(start=2025, end=None, cost=1000.0, comment="test"):
    return {
        "start_year": start,
        "end_year": end,
        "cost": cost,
        "comment": comment,
    }


def test_initial_rows_created_from_model(tk_root, no_tooltip):
    mod = no_tooltip

    expenses = [_make_expense(), _make_expense(2030, 2040, 2000)]
    model = SimpleNamespace(expenses=expenses)

    frame = mod.ExpensesEditFrame(tk_root, model)
    frame.pack()

    assert frame.expensesDict is model
    assert len(frame.row_vars) == 2

    # rows start at grid row 3
    assert frame.row_vars[0]["row"] == 3
    assert frame.row_vars[1]["row"] == 4

    # add button positioned after rows
    assert int(frame.add_button.grid_info()["row"]) == frame.next_row


def test_add_new_expense_updates_model_and_ui(tk_root, no_tooltip):
    mod = no_tooltip

    model = SimpleNamespace(expenses=[])
    frame = mod.ExpensesEditFrame(tk_root, model)
    frame.pack()

    frame._add_new_expense()

    assert len(model.expenses) == 1
    assert len(frame.row_vars) == 1

    new_exp = model.expenses[0]
    assert new_exp["start_year"] is None
    assert new_exp["cost"] is None
    assert new_exp["end_year"] is None
    assert new_exp["comment"] == ""


def test_stringvar_updates_model_values(tk_root, no_tooltip):
    mod = no_tooltip

    exp = _make_expense()
    model = SimpleNamespace(expenses=[exp])

    frame = mod.ExpensesEditFrame(tk_root, model)
    frame.pack()

    expense_id_str = str(id(exp))

    assert frame._validate_expense_field_on_focusout("2030", expense_id_str, "start_year") is True
    assert frame._validate_expense_field_on_focusout("1500", expense_id_str, "cost") is True

    tk_root.update()
    tk_root.update_idletasks()

    row = frame.row_vars[0]
    comment_entry = row["widgets"][3]

    comment_entry.delete(0, "end")
    comment_entry.insert(0, "updated")
    comment_entry.event_generate("<KeyRelease>")

    tk_root.update()
    tk_root.update_idletasks()

    assert exp["start_year"] == 2030
    assert exp["cost"] == 1500.0
    assert exp["comment"] == "updated"


def test_delete_row_removes_model_and_widgets(tk_root, no_tooltip):
    mod = no_tooltip

    e1 = _make_expense()
    e2 = _make_expense(2030)

    model = SimpleNamespace(expenses=[e1, e2])

    frame = mod.ExpensesEditFrame(tk_root, model)
    frame.pack()

    assert len(frame.row_vars) == 2

    frame._delete_row(e1)

    assert e1 not in model.expenses
    assert len(frame.row_vars) == 1


def test_regrid_rows_after_delete(tk_root, no_tooltip):
    mod = no_tooltip

    expenses = [_make_expense(), _make_expense(), _make_expense()]
    model = SimpleNamespace(expenses=expenses)

    frame = mod.ExpensesEditFrame(tk_root, model)
    frame.pack()

    frame._delete_row(expenses[1])

    assert len(frame.row_vars) == 2

    # rows should compact to 3 and 4
    assert frame.row_vars[0]["row"] == 3
    assert frame.row_vars[1]["row"] == 4

    # add button should follow
    assert int(frame.add_button.grid_info()["row"]) == frame.next_row