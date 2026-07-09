# test_io_utils.py

from __future__ import annotations

import json
import os
import pytest

from src.warpsimlab.utils.io_utils import (
    load_financial_data_from_json,
    load_market_data,
    save_financial_data_to_file,
)


def test_load_financial_data_valid_json(tmp_path):
    file = tmp_path / "data.json"
    data = {"a": 1, "b": 2}

    file.write_text(json.dumps(data))

    result = load_financial_data_from_json(file)

    assert result == data


def test_load_financial_data_missing_file_returns_none(tmp_path):
    missing = tmp_path / "missing.json"

    result = load_financial_data_from_json(missing)

    assert result is None


def test_save_financial_data_to_file(tmp_path):
    file = tmp_path / "out.json"

    data = {"x": 123}

    save_financial_data_to_file(file, data)

    loaded = json.loads(file.read_text())

    assert loaded == data


def test_load_market_data_returns_dict():
    data = load_market_data()

    assert isinstance(data, dict)
    assert "eq_mean" in data
    assert "bd_mean" in data