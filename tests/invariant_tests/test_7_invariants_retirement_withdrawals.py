import numpy as np

from src.warpsimlab.sim.simulation import run_pipeline


def run_case(make_case, **overrides):
    hp, wp, h, w, e, cfg = make_case(**overrides)

    result = run_pipeline(
        hp,
        wp,
        h,
        w,
        e,
        cfg,
    )

    return result["core"], cfg


def test_withdrawal_mode_off_still_includes_rmd_when_required(make_case):
    core, cfg = run_case(
        make_case,
        always_use_expense_mode=False,
        include_rmd=True,
        retirement_withdraw_mode="Off",
        husband_age=75,
        wife_age=72,
        second_person_enabled=True,
    )

    withdrawal = core["breakdown_by_class"]["withdrawal"]
    rmd = core["breakdown_by_class"]["rmd"]

    assert np.all(withdrawal >= rmd - 1e-8)
    assert np.any(rmd > 0.0)


def test_withdrawal_zero_when_mode_off_and_rmd_disabled(make_case):
    core, cfg = run_case(
        make_case,
        always_use_expense_mode=False,
        include_rmd=False,
        retirement_withdraw_mode="Off",
        husband_age=60,
        wife_age=58,
        second_person_enabled=False,
    )

    withdrawal = core["breakdown_by_class"]["withdrawal"]
    rmd = core["breakdown_by_class"]["rmd"]

    assert np.allclose(rmd, 0.0)
    assert np.allclose(withdrawal, 0.0)


def test_inflation_withdrawal_mode_is_never_below_rmd(make_case):
    core, cfg = run_case(
        make_case,
        always_use_expense_mode=False,
        include_rmd=True,
        retirement_withdraw_mode="Fixed Dollar Amount + Inflation",
        retirement_withdraw_dollars=1.0,
        husband_age=75,
        wife_age=72,
        second_person_enabled=True,
    )

    withdrawal = core["breakdown_by_class"]["withdrawal"]
    rmd = core["breakdown_by_class"]["rmd"]

    assert np.all(withdrawal >= rmd - 1e-8)