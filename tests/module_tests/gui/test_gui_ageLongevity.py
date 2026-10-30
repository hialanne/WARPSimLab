from types import SimpleNamespace

import pytest

from src.warpsimlab.gui import gui_ageLongevity as mod


@pytest.fixture
def editor(tk_root):
    persons = {"husband": SimpleNamespace(age=60, modeled_death_age=None),
               "wife": SimpleNamespace(age=55, modeled_death_age=None)}
    return mod.AgeLongevityEditFrame(tk_root, persons,
        {"second_person_enabled": True},
        {"longevity_mode": mod.LONGEVITY_FIXED, "years_to_simulate": 20, "fixed_years_to_simulate": 20})


def test_switch_custom_horizon_then_restore_fixed(editor, tk_root):
    editor.longevity_mode_var.set(mod.LONGEVITY_CUSTOM)
    tk_root.update_idletasks()
    assert editor.persons["husband"].modeled_death_age == 80
    assert editor.persons["wife"].modeled_death_age == 75
    editor._validate_death_age("90", "wife")
    tk_root.update_idletasks()
    assert editor.simulation_settings["years_to_simulate"] == 35
    editor.second_person_var.set(False)
    assert editor.simulation_settings["years_to_simulate"] == 20
    editor.longevity_mode_var.set(mod.LONGEVITY_FIXED)
    tk_root.update_idletasks()
    assert editor.simulation_settings["years_to_simulate"] == 20
    assert all(p.modeled_death_age is None for p in editor.persons.values())


@pytest.mark.parametrize("mode", [mod.LONGEVITY_AVERAGE, mod.LONGEVITY_LONGER_LIFE])
def test_automatic_longevity_updates_ages_and_horizon(editor, tk_root, mode):
    editor.longevity_mode_var.set(mode)
    tk_root.update_idletasks()
    for key, person in editor.persons.items():
        assert person.modeled_death_age == editor._resolve_automatic_death_age(key, person.age, mode)
    assert editor.simulation_settings["years_to_simulate"] == max(p.modeled_death_age - p.age for p in editor.persons.values())
    editor._validate_age("70", "husband")
    tk_root.update_idletasks()
    assert editor.persons["husband"].age == 70
    assert editor.persons["husband"].modeled_death_age == editor._resolve_automatic_death_age("husband", 70, mode)


@pytest.mark.parametrize("field,raw", [("age", "-1"), ("age", "121"), ("age", "60.5"), ("years", "0"), ("years", "bad")])
def test_invalid_inputs_preserve_model(editor, tk_root, validation_errors, field, raw):
    if field == "age":
        editor._validate_age(raw, "husband")
    else:
        editor._validate_years(raw)
    tk_root.update_idletasks()
    assert editor.persons["husband"].age == 60
    assert editor.simulation_settings["years_to_simulate"] == 20
    assert validation_errors
    assert tk_root._warpsimlab_validation_failed


def test_custom_death_age_rejects_age_before_current(editor, tk_root, validation_errors):
    editor.longevity_mode_var.set(mod.LONGEVITY_CUSTOM)
    editor._validate_death_age("59", "husband")
    tk_root.update_idletasks()
    assert editor.persons["husband"].modeled_death_age == 80
    assert validation_errors
    editor._validate_death_age("60", "husband")
    editor.second_person_var.set(False)
    assert editor.simulation_settings["years_to_simulate"] == 1


def test_automatic_invalid_age_is_atomic(editor, tk_root, validation_errors):
    editor.longevity_mode_var.set(mod.LONGEVITY_AVERAGE)
    before = editor.persons["husband"].modeled_death_age
    editor._validate_age("120", "husband")
    tk_root.update_idletasks()
    assert editor.persons["husband"].age == 60
    assert editor.persons["husband"].modeled_death_age == before
    assert validation_errors


def test_fixed_years_commit(editor, tk_root):
    editor._validate_years("1,000")
    tk_root.update_idletasks()
    assert editor.simulation_settings["fixed_years_to_simulate"] == 1000
    assert editor.simulation_settings["years_to_simulate"] == 1000
    assert editor.years_var.get() == "1000"
