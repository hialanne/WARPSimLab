# test_utilities.py

import pytest

from src.warpsimlab.utils.utilities import parse_money_strict


def test_parse_money_valid_string():
    result = parse_money_strict("1,234.50")

    assert result == 1234.50


def test_parse_money_number():
    result = parse_money_strict(100)

    assert result == 100.0


def test_parse_money_empty_string_raises():
    with pytest.raises(ValueError):
        parse_money_strict("")


def test_parse_money_invalid_string_raises():
    with pytest.raises(ValueError):
        parse_money_strict("abc")