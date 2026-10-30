from types import SimpleNamespace

import pytest

from src.warpsimlab.sim.engines import mortalityEngine as mod


@pytest.mark.parametrize("death,age,alive", [(None, 150, True), (80, 79, True), (80, 80, False), (80, 81, False)])
def test_death_age_is_first_deceased_age(death, age, alive):
    assert mod.is_person_alive(SimpleNamespace(modeled_death_age=death), age) is alive


@pytest.mark.parametrize("second,h_age,w_age,count,survivor,factor", [
    (True, 79, 79, 2, False, 1), (True, 80, 79, 1, True, .75),
    (True, 79, 80, 1, True, .75), (True, 80, 80, 0, False, 0),
    (False, 79, 0, 1, False, 1), (False, 80, 0, 0, False, 0),
])
def test_household_composition_and_survivor_expenses(second, h_age, w_age, count, survivor, factor):
    husband = SimpleNamespace(modeled_death_age=80)
    wife = SimpleNamespace(modeled_death_age=80) if second else None
    state = mod.get_household_mortality_state(husband, wife, h_age, w_age, second)
    assert state == dict(husband_alive=h_age < 80, wife_alive=second and w_age < 80,
                         household_members_alive=count, survivor_state=survivor,
                         survivor_expense_factor=factor)
    assert husband.modeled_death_age == 80


@pytest.mark.parametrize("previous,current,event", [(True, False, True), (False, False, False), (True, True, False)])
def test_death_events_only_on_transition(previous, current, event):
    state = {"husband_alive": current, "wife_alive": current}
    assert mod.detect_death_events(previous, previous, state, True) == {
        "husband_death_event": event, "wife_death_event": event}
    assert mod.detect_death_events(previous, True, state, False)["wife_death_event"] is False
