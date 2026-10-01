# mortalityEngine.py


def is_person_alive(person, current_age):
    """
    Return True while the person is alive under deterministic modeled mortality.

    modeled_death_age is the first deceased age. A value of None means the
    person remains alive for the configured simulation horizon.
    """
    if person.modeled_death_age is None:
        return True

    return current_age < person.modeled_death_age


def get_household_mortality_state(husband, wife, curr_h_age, curr_w_age, second_person_enabled):
    """
    Return the household's mortality state for one simulation year.

    second_person_enabled describes household composition and is never changed
    by mortality.
    """
    husband_alive = is_person_alive(husband, curr_h_age)
    wife_alive = False

    if second_person_enabled:
        wife_alive = is_person_alive(wife, curr_w_age)

    household_members_alive = int(husband_alive) + int(wife_alive)

    survivor_state = False
    if second_person_enabled and household_members_alive == 1:
        survivor_state = True

    survivor_expense_factor = 1.0
    if survivor_state:
        survivor_expense_factor = 0.75
    elif household_members_alive == 0:
        survivor_expense_factor = 0.0

    return {
        "husband_alive": husband_alive,
        "wife_alive": wife_alive,
        "household_members_alive": household_members_alive,
        "survivor_state": survivor_state,
        "survivor_expense_factor": survivor_expense_factor,
    }


def detect_death_events(previous_husband_alive, previous_wife_alive, mortality_state, second_person_enabled):
    """
    Detect transitions from alive in the previous year to deceased this year.
    """
    husband_death_event = previous_husband_alive and not mortality_state["husband_alive"]
    wife_death_event = False

    if second_person_enabled:
        wife_death_event = previous_wife_alive and not mortality_state["wife_alive"]

    return {
        "husband_death_event": husband_death_event,
        "wife_death_event": wife_death_event,
    }