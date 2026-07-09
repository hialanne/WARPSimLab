# test_dynamicExpenses.py

from __future__ import annotations

import pytest

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses


def test_add_expense_creates_record():
    d = DynamicExpenses()

    d.add_expense(2025, 1000, 2030, "Test expense")

    assert len(d.expenses) == 1

    exp = d.expenses[0]
    assert exp["start_year"] == 2025
    assert exp["end_year"] == 2030
    assert exp["cost"] == 1000
    assert exp["comment"] == "Test expense"


def test_remove_expense_valid_index():
    d = DynamicExpenses()

    d.add_expense(2025, 100)
    d.add_expense(2026, 200)

    d.remove_expense(0)

    assert len(d.expenses) == 1
    assert d.expenses[0]["cost"] == 200


def test_remove_expense_invalid_index_raises():
    d = DynamicExpenses()

    with pytest.raises(IndexError):
        d.remove_expense(0)


def test_update_expense_updates_only_provided_fields():
    d = DynamicExpenses()

    d.add_expense(2025, 1000, 2030, "original")

    d.update_expense(0, cost=1500, comment="updated")

    exp = d.expenses[0]

    assert exp["start_year"] == 2025
    assert exp["end_year"] == 2030
    assert exp["cost"] == 1500
    assert exp["comment"] == "updated"


def test_update_expense_invalid_index_raises():
    d = DynamicExpenses()

    with pytest.raises(IndexError):
        d.update_expense(0, cost=100)


def test_get_expenses_returns_copy():
    d = DynamicExpenses()

    d.add_expense(2025, 1000)

    expenses_copy = d.get_expenses()

    assert expenses_copy == d.expenses
    assert expenses_copy is not d.expenses

    # ensure mutation of returned list does not affect internal list
    expenses_copy[0]["cost"] = 9999
    assert d.expenses[0]["cost"] == 1000


def test_get_total_expense_for_year_within_range():
    d = DynamicExpenses()

    d.add_expense(2025, 100, 2027)
    d.add_expense(2026, 200, 2028)

    assert d.get_total_expense_for_year(2026) == 300


def test_get_total_expense_for_year_before_start():
    d = DynamicExpenses()

    d.add_expense(2025, 100)

    assert d.get_total_expense_for_year(2024) == 0


def test_get_total_expense_for_year_open_ended():
    d = DynamicExpenses()

    d.add_expense(2020, 500, None)

    assert d.get_total_expense_for_year(2035) == 500


def test_get_total_expense_multiple_rules():
    d = DynamicExpenses()

    d.add_expense(2020, 100)          # open ended
    d.add_expense(2022, 200, 2024)    # bounded
    d.add_expense(2025, 300)          # future

    assert d.get_total_expense_for_year(2023) == 300