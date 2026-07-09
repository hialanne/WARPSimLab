# test_constants.py

from src.warpsimlab.utils.constants import (
    DEFAULT_HUSBAND_AGE,
    DEFAULT_WIFE_AGE,
    DEFAULT_INFLATION,
    RMD_START_AGE,
    UNIFORM_LIFETIME_TABLE,
)


def test_basic_default_values_are_positive():
    assert DEFAULT_HUSBAND_AGE > 0
    assert DEFAULT_WIFE_AGE > 0
    assert DEFAULT_INFLATION > 0


def test_rmd_start_age_is_in_table():
    assert RMD_START_AGE in UNIFORM_LIFETIME_TABLE


def test_uniform_lifetime_table_has_expected_range():
    assert min(UNIFORM_LIFETIME_TABLE.keys()) == 73
    assert max(UNIFORM_LIFETIME_TABLE.keys()) >= 120