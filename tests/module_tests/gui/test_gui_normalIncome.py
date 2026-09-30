# test_gui_normalIncome.py

from __future__ import annotations

from dataclasses import dataclass

import tkinter as tk
from tkinter import ttk

import pytest


@dataclass
class DummyPerson:
    age: int = 40
    income: float = 100000.0
    retire_age: int = 65
    ss: float = 20000.0
    ss_age: int = 67
    pension: float = 0.0
    pension_age: int = 0
    annuity: float = 0.0
    annuity_age: int = 0
    annual_401k_contribution: float = 0.0
    annual_employer_match: float = 0.0
    annual_hsa_contribution: float = 0.0
    annual_hsa_employer_contribution: float = 0.0
    pension_inflation_adjustment_pct: float = 0.0


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk not available: {e}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def mod_no_tooltip(monkeypatch):
    from src.warpsimlab.gui import gui_normalIncome as mod

    class DummyTooltip:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(mod, "Tooltip", DummyTooltip, raising=True)
    return mod


def _count_entries(frame: ttk.Frame) -> int:
    return sum(isinstance(w, ttk.Entry) for w in frame.winfo_children())


def _label_texts(frame: ttk.Frame) -> list[str]:
    out = []
    for w in frame.winfo_children():
        if isinstance(w, ttk.Label):
            try:
                out.append(w.cget("text"))
            except tk.TclError:
                pass
    return out


def test_bind_var_updates_person_and_ignores_invalid(monkeypatch, tk_root, mod_no_tooltip):
    mod = mod_no_tooltip

    husband = DummyPerson(age=40, income=100000.0, retire_age=65)
    persons = {"husband": husband}

    frame = mod.NormalIncomeEditFrame(tk_root, persons, mode="Basic")
    frame.pack()

    shown_errors = []
    monkeypatch.setattr(mod.messagebox, "showerror", lambda *args, **kwargs: shown_errors.append((args, kwargs)))

    # income is float
    assert frame._validate_person_field_on_focusout("123456.78", "husband", "income") is True
    tk_root.update()
    tk_root.update_idletasks()
    assert husband.income == pytest.approx(123456.78)
    assert frame.vars["husband"]["income"].get() == "123,457"

    # invalid numeric input should be rejected without changing the model
    prev_retire = husband.retire_age
    assert frame._validate_person_field_on_focusout("not-a-number", "husband", "retire_age") is True
    tk_root.update()
    tk_root.update_idletasks()

    assert husband.retire_age == prev_retire
    assert frame.vars["husband"]["retire_age"].get() == str(prev_retire)
    assert len(shown_errors) == 1
    assert shown_errors[0][0][0] == "Invalid Input"


def test_basic_mode_builds_basic_fields_only_single_person(tk_root, mod_no_tooltip):
    mod = mod_no_tooltip

    husband = DummyPerson()
    persons = {"husband": husband}

    frame = mod.NormalIncomeEditFrame(tk_root, persons, mode="Basic")
    frame.pack()

    # Basic mode has 3 fields for one person.
    assert _count_entries(frame) == 3

    # Should have only the left "Husband" header.
    texts = _label_texts(frame)
    assert texts.count("Husband") == 1


def test_basic_mode_builds_basic_fields_for_two_people(tk_root, mod_no_tooltip):
    mod = mod_no_tooltip

    husband = DummyPerson()
    wife = DummyPerson()
    persons = {"husband": husband, "wife": wife}

    frame = mod.NormalIncomeEditFrame(tk_root, persons, mode="Basic")
    frame.pack()

    # Basic mode has 3 fields per person.
    assert _count_entries(frame) == 6

    texts = _label_texts(frame)
    assert texts.count("Husband") == 1
    assert texts.count("Wife") == 1


def test_advanced_mode_builds_full_left_and_right_blocks(tk_root, mod_no_tooltip):
    mod = mod_no_tooltip

    husband = DummyPerson()
    wife = DummyPerson()
    persons = {"husband": husband, "wife": wife}

    frame = mod.NormalIncomeEditFrame(tk_root, persons, mode="Advanced")
    frame.pack()

    # Advanced mode has 13 fields per person: 6 left and 7 right.
    assert _count_entries(frame) == 26

    texts = _label_texts(frame)
    assert texts.count("Husband") == 2
    assert texts.count("Wife") == 2