# test_person.py

from __future__ import annotations

import pytest

from src.warpsimlab.dataClasses.person import Person


def test_person_assigns_required_fields():
    p = Person(
        age=40,
        retire_age=67,
        income=120_000,
        ss=24_000,
        ss_age=67,
        pension=10_000,
        pension_age=65,
        annuity=5_000,
        annuity_age=70,
    )

    assert p.age == 40
    assert p.retire_age == 67
    assert p.income == 120_000
    assert p.ss == 24_000
    assert p.ss_age == 67
    assert p.pension == 10_000
    assert p.pension_age == 65
    assert p.annuity == 5_000
    assert p.annuity_age == 70


def test_person_optional_fields_default_to_zero():
    p = Person(
        age=30,
        retire_age=65,
        income=80_000,
        ss=0,
        ss_age=67,
        pension=0,
        pension_age=0,
        annuity=0,
        annuity_age=0,
    )

    assert p.annual_401k_contribution == 0.0
    assert p.annual_employer_match == 0.0
    assert p.pension_inflation_adjustment_pct == 0.0


def test_person_optional_fields_preserve_passed_values():
    p = Person(
        age=55,
        retire_age=62,
        income=150_000,
        ss=30_000,
        ss_age=70,
        pension=20_000,
        pension_age=60,
        annuity=12_000,
        annuity_age=65,
        annual_401k_contribution=22_500.0,
        annual_employer_match=7_500.0,
        pension_inflation_adjustment_pct=2.5,
    )

    assert p.annual_401k_contribution == pytest.approx(22_500.0)
    assert p.annual_employer_match == pytest.approx(7_500.0)
    assert p.pension_inflation_adjustment_pct == pytest.approx(2.5)