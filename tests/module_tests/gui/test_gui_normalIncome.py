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

    sim_controls = {"enable_second_person": False}
    frame = mod.NormalIncomeEditFrame(tk_root, persons, simulation_controls=sim_controls, mode="Basic")
    frame.pack()

    # age is int
    assert frame._validate_person_field_on_focusout("41", "husband", "age") is True
    tk_root.update()
    tk_root.update_idletasks()
    assert husband.age == 41
    assert frame.vars["husband"]["age"].get() == "41"

    # income is float
    assert frame._validate_person_field_on_focusout("123456.78", "husband", "income") is True
    tk_root.update()
    tk_root.update_idletasks()
    assert husband.income == pytest.approx(123456.78)
    assert frame.vars["husband"]["income"].get() == "123,457"

    # invalid numeric input should be ignored (no change)
    prev_retire = husband.retire_age
    assert frame._validate_person_field_on_focusout("not-a-number", "husband", "retire_age") is True
    tk_root.update()
    tk_root.update_idletasks()
    assert husband.retire_age == prev_retire
    assert frame.vars["husband"]["retire_age"].get() == str(prev_retire)


def test_enable_second_person_checkbox_updates_controls_and_calls_refresh(tk_root, mod_no_tooltip):
    mod = mod_no_tooltip

    called = {"n": 0}

    def refresh():
        called["n"] += 1

    husband = DummyPerson()
    persons = {"husband": husband}
    sim_controls = {"enable_second_person": False}

    frame = mod.NormalIncomeEditFrame(
        tk_root,
        persons,
        simulation_controls=sim_controls,
        refresh_callback=refresh,
        mode="Basic",
    )
    frame.pack()

    # Toggle the BooleanVar; trace_add should call _on_enable_second_person_changed
    frame._enable_second_person_var.set(True)

    assert sim_controls["enable_second_person"] is True
    assert called["n"] >= 1


def test_basic_mode_builds_basic_fields_only_single_person(tk_root, mod_no_tooltip):
    mod = mod_no_tooltip

    husband = DummyPerson()
    persons = {"husband": husband}
    sim_controls = {"enable_second_person": False}

    frame = mod.NormalIncomeEditFrame(tk_root, persons, simulation_controls=sim_controls, mode="Basic")
    frame.pack()

    # Basic mode uses fields_basic of length 4; for single person, entries == 4
    assert _count_entries(frame) == 4

    # Should have only the left "Husband" header (no right-block header)
    texts = _label_texts(frame)
    assert texts.count("Husband") == 1


def test_basic_mode_builds_basic_fields_for_two_people(tk_root, mod_no_tooltip):
    mod = mod_no_tooltip

    husband = DummyPerson()
    wife = DummyPerson()
    persons = {"husband": husband, "wife": wife}
    sim_controls = {"enable_second_person": True}

    frame = mod.NormalIncomeEditFrame(tk_root, persons, simulation_controls=sim_controls, mode="Basic")
    frame.pack()

    # Basic mode fields_basic length 4; for two people, entries == 4 * 2
    assert _count_entries(frame) == 8

    texts = _label_texts(frame)
    # Left headers Husband + Wife
    assert texts.count("Husband") == 1
    assert "Wife" in texts


def test_advanced_mode_builds_full_left_and_right_blocks(tk_root, mod_no_tooltip):
    mod = mod_no_tooltip

    husband = DummyPerson()
    wife = DummyPerson()
    persons = {"husband": husband, "wife": wife}
    sim_controls = {"enable_second_person": True}

    frame = mod.NormalIncomeEditFrame(tk_root, persons, simulation_controls=sim_controls, mode="Advanced")
    frame.pack()

    # Full mode: left block fields_full_left len=5; right block fields_full_right len=7; total=12.
    # Two people => entries == 12 * 2
    assert _count_entries(frame) == 24

    texts = _label_texts(frame)
    # In full mode, right block headers add another "Husband" (+ maybe "Wife") label.
    assert texts.count("Husband") == 2
    assert texts.count("Wife") == 2