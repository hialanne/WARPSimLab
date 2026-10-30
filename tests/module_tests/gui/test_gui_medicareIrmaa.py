from types import SimpleNamespace

import pytest

from src.warpsimlab.gui import gui_medicareIrmaa as mod


@pytest.fixture
def editor(tk_root):
    return mod.MedicareIrmaaEditFrame(tk_root,
        {"husband": SimpleNamespace(age=64, medicare_start_age=65, medicare_annual_cost=3000)},
        {"irmaa_enabled": True}, {"two_years_prior": None, "one_year_prior": None})


@pytest.mark.parametrize("age,keys", [(60, ()), (63, ("one_year_prior",)), (64, ("two_years_prior", "one_year_prior")), (70, ("two_years_prior", "one_year_prior"))])
def test_magi_requirements_at_medicare_boundaries(editor, age, keys):
    editor.persons["husband"].age = age
    assert editor._required_historical_magi_keys() == keys


def test_magi_warning_tracks_missing_history_and_enable_toggle(editor, tk_root):
    assert "2 required" in editor.magi_warning_var.get()
    editor._validate_magi("150,000", "two_years_prior")
    tk_root.update_idletasks()
    assert editor.historical_magi["two_years_prior"] == 150000
    assert "1 required" in editor.magi_warning_var.get()
    editor._validate_magi("0", "one_year_prior")
    tk_root.update_idletasks()
    assert editor.magi_warning_var.get() == ""
    editor._validate_magi(" ", "one_year_prior")
    tk_root.update_idletasks()
    assert editor.historical_magi["one_year_prior"] is None
    editor.irmaa_enabled_var.set(False)
    tk_root.update_idletasks()
    editor._update_magi_warning()
    assert editor.simulation_controls["irmaa_enabled"] is False
    assert editor.magi_warning_var.get() == ""


@pytest.mark.parametrize("field,raw", [("medicare_start_age", "121"), ("medicare_start_age", "65.5"), ("medicare_annual_cost", "-1"), ("medicare_annual_cost", "nan")])
def test_invalid_person_input_retains_previous_value(editor, tk_root, validation_errors, field, raw):
    before = getattr(editor.persons["husband"], field)
    editor._validate_person_field(raw, "husband", field)
    tk_root.update_idletasks()
    assert getattr(editor.persons["husband"], field) == before
    assert validation_errors


def test_valid_person_fields_and_bad_magi(editor, tk_root, validation_errors):
    editor._validate_person_field("67", "husband", "medicare_start_age")
    editor._validate_person_field("4,500", "husband", "medicare_annual_cost")
    editor._validate_magi("inf", "one_year_prior")
    tk_root.update_idletasks()
    assert editor.persons["husband"].medicare_start_age == 67
    assert editor.persons["husband"].medicare_annual_cost == 4500
    assert editor.historical_magi["one_year_prior"] is None
    assert validation_errors
