import numpy as np

from tests.architectural_helpers import run_invariant_case as run_case


def test_wife_outputs_zero_when_second_person_disabled(make_case):
    core, cfg = run_case(make_case, second_person_enabled=False)

    assert np.allclose(core["net_income_wife"], 0.0)


def test_wife_outputs_present_when_second_person_enabled(make_case):
    core, cfg = run_case(make_case, second_person_enabled=True)

    assert np.all(core["net_income_wife"] >= 0.0)


