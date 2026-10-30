import pytest

from src.warpsimlab.utils import longevity as mod


@pytest.mark.parametrize("sex,age,target,expected", [
    ("male", 119, 0.5, 120), ("female", 119, 0.25, 120),
    # At age 118 survival to 119 is 1 - .957970 = .042030.
    ("male", 118, 0.05, 119), ("female", 118, 0.01, 120),
])
def test_first_age_crossing_conditional_survival(sex, age, target, expected):
    assert mod.modeled_death_age_for_survival(age, sex, target) == expected


@pytest.mark.parametrize("age", [0, 40, 65, 90, 119])
def test_longer_life_target_never_shortens_horizon(age):
    for sex in ("male", "female"):
        average = mod.modeled_death_age_for_survival(age, sex, 0.5)
        longer = mod.modeled_death_age_for_survival(age, sex, 0.25)
        assert age < average <= longer <= 120


@pytest.mark.parametrize("age,sex,target", [
    (-1, "male", .5), (120, "male", .5), (65.0, "male", .5),
    ("65", "male", .5), (65, "unknown", .5),
    (65, "male", 0), (65, "female", 1), (65, "male", float("nan")),
])
def test_invalid_lookup_inputs(age, sex, target):
    with pytest.raises(ValueError):
        mod.modeled_death_age_for_survival(age, sex, target)
