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


@pytest.mark.parametrize("loader,header,rows,expected", [
    ("load_historical_asset_returns_csv", "Year,Equity_Return_Pct,Bond_Return_Pct,Cash_Return_Pct,Real_Estate_Return_Pct", "2026,10,-5,2,3\n2025,-20,4,1,0", {"eq": [-.2, .1], "bd": [.04, -.05], "cs": [.01, .02], "re": [0, .03]}),
    ("load_historical_asset_returns_csv", "year,equity,bonds,cash,real_estate", "2026,10,-5,2,3\n2025,-20,4,1,0", {"eq": [-.2, .1]}),
    ("load_historical_inflation_csv", "Year,Inflation_Rate_Pct", "2026,5\n2025,-2", {"inflation": [-.02, .05]}),
    ("load_historical_inflation_csv", "year,inflation", "2026,5\n2025,-2", {"inflation": [-.02, .05]}),
])
def test_historical_csv_aliases_sorting_and_percentage_conversion(tmp_path, monkeypatch, loader, header, rows, expected):
    import numpy as np
    from src.warpsimlab.utils import io_utils as mod
    path = tmp_path / "history.csv"
    path.write_text(header + "\n\n" + rows + "\n", encoding="utf-8-sig")
    monkeypatch.setattr(mod, "get_data_file_path", lambda filename: str(path))
    result = getattr(mod, loader)()
    np.testing.assert_array_equal(result["years"], [2025, 2026])
    assert result["num_years"] == 2
    for key, values in expected.items():
        np.testing.assert_allclose(result[key], values)


@pytest.mark.parametrize("loader,header,row", [
    ("load_historical_asset_returns_csv", "year,equity,bonds,cash,real_estate", "2025,10,5,2,3"),
    ("load_historical_inflation_csv", "year,inflation", "2025,3"),
])
@pytest.mark.parametrize("problem,match", [("empty", "empty"), ("header", "No historical"), ("missing", "Missing required"), ("short", "enough columns"), ("numeric", "Invalid numeric"), ("duplicate", "Duplicate years")])
def test_historical_csv_rejects_invalid_input(tmp_path, monkeypatch, loader, header, row, problem, match):
    from src.warpsimlab.utils import io_utils as mod
    contents = {"empty": "\n", "header": header, "missing": "year\n2025",
                "short": header + "\n2025", "numeric": header + "\n" + row.replace("2025", "bad"),
                "duplicate": header + "\n" + row + "\n" + row}[problem]
    path = tmp_path / "history.csv"
    path.write_text(contents)
    monkeypatch.setattr(mod, "get_data_file_path", lambda filename: str(path))
    with pytest.raises(ValueError, match=match):
        getattr(mod, loader)()


def test_load_financial_json_decode_error_and_market_fallback(tmp_path, monkeypatch, capsys):
    from src.warpsimlab.utils import io_utils as mod
    path = tmp_path / "bad.json"
    path.write_text("{")
    assert mod.load_financial_data_from_json(path) is None
    assert "JSON decode error" in capsys.readouterr().out
    monkeypatch.setattr(mod, "_get_market_history_path", lambda: str(path))
    assert mod.load_market_data()["eq_mean"] == 7.98
    path.write_text(json.dumps({"custom": {"eq_mean": 12}}))
    assert mod.load_market_data("custom") == {"eq_mean": 12}
