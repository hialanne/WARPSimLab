from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.warpsimlab.gui.gui_specialIncome import SpecialIncomeEditFrame


def test_legacy_stream_normalization_and_edits(tk_root):
    stream = {"owner": "wife", "inflation_adjustment_pct": 50}
    frame = SpecialIncomeEditFrame(tk_root, [stream], second_person_enabled=False)
    assert stream["owner"] == "husband"
    assert stream["adjustment_mode"] == "inflation"
    assert stream["adjustment_pct"] == 50
    variables = frame.row_vars[0]["vars"]
    variables["name"].set("Consulting")
    variables["taxable"].set(False)
    variables["enabled"].set(False)
    assert stream["name"] == "Consulting"
    assert stream["taxable"] is False
    assert stream["enabled"] is False
    variables["adjustment_mode"].set("Fixed Annual")
    assert stream["adjustment_mode"] == "fixed"
    assert stream["adjustment_pct"] == 5
    variables["adjustment_mode"].set("None")
    assert stream["adjustment_pct"] == 0
    assert str(frame.row_vars[0]["widgets"][8].cget("state")) == "disabled"


def test_add_delete_and_regrid_streams(tk_root):
    streams = []
    frame = SpecialIncomeEditFrame(tk_root, streams)
    frame._add_new_stream()
    frame._add_new_stream()
    first, second = streams
    assert first is not second
    # Give the rows distinct values before deleting to verify the surviving model.
    frame.row_vars[0]["vars"]["name"].set("First")
    frame.row_vars[1]["vars"]["owner"].set("wife")
    frame._delete_stream(first)
    assert streams == [second]
    assert streams[0] is second
    assert second["owner"] == "wife"
    assert len(frame.row_vars) == 1
    assert int(frame.row_vars[0]["widgets"][0].grid_info()["row"]) == 2
    assert int(frame.add_button.grid_info()["row"]) == 3


@pytest.mark.parametrize("field,raw,valid,expected", [
    ("amount", "1,500", True, 1500), ("amount", "0", True, 0),
    ("amount", "-1", False, 0), ("amount", "nan", False, 0),
    ("adjustment_pct", "-5", True, -5), ("adjustment_pct", "1e2", False, 100),
    ("start_age", "120", True, 120), ("end_age", "121", False, 120),
    ("start_age", "-1", False, 0),
])
def test_stream_field_validation(tk_root, validation_errors, field, raw, valid, expected):
    streams = []
    frame = SpecialIncomeEditFrame(tk_root, streams)
    frame._add_new_stream()
    stream = streams[0]
    var = frame.row_vars[0]["vars"][field]
    if field in ("start_age", "end_age"):
        frame._validate_int_field(raw, stream, field, var, str(stream[field]))
    else:
        frame._validate_float_field(raw, stream, field, var, str(stream[field]), str(field == "adjustment_pct"))
    tk_root.update_idletasks()
    assert stream[field] == expected
    assert bool(validation_errors) is (not valid)


def test_delete_second_of_identical_streams_preserves_first_model():
    first, second = {"name": "Consulting"}, {"name": "Consulting"}
    streams = [first, second]
    frame = SimpleNamespace(special_income_streams=streams,
        row_vars=[{"stream": first, "widgets": [Mock()]},
                  {"stream": second, "widgets": [Mock()]}], _regrid_rows=Mock())
    assert first == second and first is not second
    SpecialIncomeEditFrame._delete_stream(frame, second)
    assert len(streams) == 1
    assert streams[0] is first
    assert frame.row_vars[0]["stream"] is streams[0]
