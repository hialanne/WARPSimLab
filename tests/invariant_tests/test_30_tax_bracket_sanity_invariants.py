import numpy as np
import pytest

from tests.architectural_helpers import run_invariant_case as run_case

#pytest.skip("Skipping invariant tests for now", allow_module_level=True)



EPS = 1e-9


def test_tax_bracket_is_never_negative(make_case):
    core, cfg = run_case(
        make_case,
        calculate_income_taxes=True,
        calculate_state_taxes=True,
        second_person_enabled=True,
        years_to_simulate=5,
    )

    assert np.all(core["tax_bracket"] >= -EPS)


def test_tax_bracket_is_never_above_one(make_case):
    core, cfg = run_case(
        make_case,
        calculate_income_taxes=True,
        calculate_state_taxes=True,
        second_person_enabled=True,
        years_to_simulate=5,
    )

    assert np.all(core["tax_bracket"] <= 1.0 + EPS)


def test_tax_bracket_is_zero_when_income_taxes_are_disabled(make_case):
    core, cfg = run_case(
        make_case,
        calculate_income_taxes=False,
        calculate_state_taxes=False,
        second_person_enabled=True,
        years_to_simulate=5,
    )

    assert np.allclose(core["tax_bracket"], 0.0)