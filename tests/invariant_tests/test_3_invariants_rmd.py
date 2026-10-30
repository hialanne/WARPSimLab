import numpy as np

from tests.architectural_helpers import run_invariant_case as run_case


def test_rmd_zero_when_disabled(make_case):
    core, cfg = run_case(make_case, include_rmd=False)

    rmd = core["breakdown_by_class"]["rmd"]

    assert np.allclose(rmd, 0.0)


def test_rmd_non_negative_when_enabled(make_case):
    core, cfg = run_case(
        make_case,
        include_rmd=True,
        husband_age=75,
        wife_age=72,
    )

    rmd = core["breakdown_by_class"]["rmd"]

    assert np.all(rmd >= 0.0)


def test_rmd_eventually_positive_for_old_age(make_case):
    core, cfg = run_case(
        make_case,
        include_rmd=True,
        husband_age=75,
        wife_age=72,
    )

    rmd = core["breakdown_by_class"]["rmd"]

    assert np.any(rmd > 0.0)