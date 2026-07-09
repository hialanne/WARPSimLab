# test_rmd.py

from src.warpsimlab.utils.rmd import calculate_rmd
from src.warpsimlab.utils.constants import RMD_START_AGE


def test_rmd_before_start_age_is_zero():
    result = calculate_rmd(100000, RMD_START_AGE - 1)

    assert result == 0


def test_rmd_at_valid_age():
    result = calculate_rmd(100000, 73)

    assert result > 0


def test_rmd_age_above_table_uses_fallback():
    result = calculate_rmd(100000, 150)

    assert result == 100000 / 2.0