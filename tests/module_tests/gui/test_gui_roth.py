# tests/module_tests/gui/test_gui_roth.py

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk not available: {e}")

    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def patched_module(monkeypatch):
    from src.warpsimlab.gui import gui_roth as mod

    class DummyTooltip:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr(mod, "Tooltip", DummyTooltip, raising=True)
    return mod


def _make_flow(**overrides):
    flow = {
        "owner": "husband",
        "type": "roth_ira_contribution",
        "name": "Test Roth",
        "amount": 1000.0,
        "start_age": 40,
        "end_age": 70,
        "enabled": True,
        "inflation_adjustment_pct": 0.0,
    }
    flow.update(overrides)
    return flow


def _make_frame(tk_root, patched_module, monkeypatch, flow=None, enable_second_person=True):
    mod = patched_module
    flows = [_make_flow() if flow is None else flow]

    frame = mod.RothEditFrame(
        tk_root,
        roth_flows=flows,
        enable_second_person=enable_second_person,
    )
    frame.pack()

    monkeypatch.setattr(frame, "after_idle", lambda fn: fn(), raising=True)

    shown_errors = []
    monkeypatch.setattr(
        mod.messagebox,
        "showerror",
        lambda *args, **kwargs: shown_errors.append((args, kwargs)),
    )

    return frame, flows, shown_errors


def test_initial_flow_values_loaded(tk_root, patched_module):
    flow = _make_flow()
    frame = patched_module.RothEditFrame(tk_root, roth_flows=[flow])
    frame.pack()

    item = frame.row_vars[0]

    assert item["vars"]["owner"].get() == "husband"
    assert item["vars"]["type"].get() == frame.TYPE_LABELS["roth_ira_contribution"]
    assert item["vars"]["name"].get() == "Test Roth"
    assert item["vars"]["amount"].get() == "1000.0"
    assert item["vars"]["start_age"].get() == "40"
    assert item["vars"]["end_age"].get() == "70"
    assert item["vars"]["enabled"].get() is True
    assert item["vars"]["inflation_adjustment_pct"].get() == "0.0"


def test_canonical_roth_types_are_preserved(tk_root, patched_module):
    flows = [
        _make_flow(type="roth_ira_contribution"),
        _make_flow(type="roth_workplace_contribution"),
        _make_flow(type="roth_conversion"),
    ]

    frame = patched_module.RothEditFrame(tk_root, roth_flows=flows)
    frame.pack()

    assert [flow["type"] for flow in flows] == [
        "roth_ira_contribution",
        "roth_workplace_contribution",
        "roth_conversion",
    ]


def test_type_combobox_updates_to_canonical_value(tk_root, patched_module):
    flow = _make_flow()
    frame = patched_module.RothEditFrame(tk_root, roth_flows=[flow])
    frame.pack()

    type_var = frame.row_vars[0]["vars"]["type"]
    type_var.set(frame.TYPE_LABELS["roth_conversion"])

    assert flow["type"] == "roth_conversion"


def test_owner_values_respect_second_person_state(tk_root, patched_module):
    frame_single = patched_module.RothEditFrame(
        tk_root,
        roth_flows=[_make_flow()],
        enable_second_person=False,
    )
    frame_single.pack()

    assert frame_single._owner_values() == ["husband"]

    frame_couple = patched_module.RothEditFrame(
        tk_root,
        roth_flows=[_make_flow()],
        enable_second_person=True,
    )
    frame_couple.pack()

    assert frame_couple._owner_values() == ["husband", "wife"]


def test_amount_zero_is_accepted(tk_root, patched_module, monkeypatch):
    flow = _make_flow()
    frame, _, shown_errors = _make_frame(tk_root, patched_module, monkeypatch, flow)
    amount_var = frame.row_vars[0]["vars"]["amount"]

    assert frame._validate_float_field("0", flow, "amount", amount_var, 0.0, allow_negative=False) is True

    assert flow["amount"] == pytest.approx(0.0)
    assert amount_var.get() == "0.0"
    assert shown_errors == []


def test_negative_amount_is_rejected_without_changing_flow(tk_root, patched_module, monkeypatch):
    flow = _make_flow(amount=1000.0)
    frame, _, shown_errors = _make_frame(tk_root, patched_module, monkeypatch, flow)
    amount_var = frame.row_vars[0]["vars"]["amount"]

    assert frame._validate_float_field("-1", flow, "amount", amount_var, 0.0, allow_negative=False) is True

    assert flow["amount"] == pytest.approx(1000.0)
    assert amount_var.get() == "1000.0"
    assert len(shown_errors) == 1
    assert shown_errors[0][0][0] == "Invalid Input"


@pytest.mark.parametrize("bad_value", ["NaN", "inf", "-inf"])
def test_amount_rejects_nonfinite_values(tk_root, patched_module, monkeypatch, bad_value):
    flow = _make_flow(amount=1000.0)
    frame, _, shown_errors = _make_frame(tk_root, patched_module, monkeypatch, flow)
    amount_var = frame.row_vars[0]["vars"]["amount"]

    assert frame._validate_float_field(
        bad_value,
        flow,
        "amount",
        amount_var,
        0.0,
        allow_negative=False,
    ) is True

    assert flow["amount"] == pytest.approx(1000.0)
    assert amount_var.get() == "1000.0"
    assert len(shown_errors) == 1


def test_age_150_is_accepted(tk_root, patched_module, monkeypatch):
    flow = _make_flow(start_age=40, end_age=150)
    frame, _, shown_errors = _make_frame(tk_root, patched_module, monkeypatch, flow)
    end_age_var = frame.row_vars[0]["vars"]["end_age"]

    assert frame._validate_int_field("150", flow, "end_age", end_age_var, 120) is True

    assert flow["end_age"] == 150
    assert end_age_var.get() == "150"
    assert shown_errors == []


def test_negative_age_is_rejected(tk_root, patched_module, monkeypatch):
    flow = _make_flow(start_age=40, end_age=70)
    frame, _, shown_errors = _make_frame(tk_root, patched_module, monkeypatch, flow)
    start_age_var = frame.row_vars[0]["vars"]["start_age"]

    assert frame._validate_int_field("-1", flow, "start_age", start_age_var, 0) is True

    assert flow["start_age"] == 40
    assert flow["end_age"] == 70
    assert start_age_var.get() == "40"
    assert len(shown_errors) == 1


def test_end_age_before_start_age_is_rejected(tk_root, patched_module, monkeypatch):
    flow = _make_flow(start_age=40, end_age=70)
    frame, _, shown_errors = _make_frame(tk_root, patched_module, monkeypatch, flow)
    end_age_var = frame.row_vars[0]["vars"]["end_age"]

    assert frame._validate_int_field("39", flow, "end_age", end_age_var, 120) is True

    assert flow["start_age"] == 40
    assert flow["end_age"] == 70
    assert end_age_var.get() == "70"
    assert len(shown_errors) == 1
    assert shown_errors[0][0][0] == "Invalid Input"


def test_start_age_after_end_age_is_rejected(tk_root, patched_module, monkeypatch):
    flow = _make_flow(start_age=40, end_age=70)
    frame, _, shown_errors = _make_frame(tk_root, patched_module, monkeypatch, flow)
    start_age_var = frame.row_vars[0]["vars"]["start_age"]

    assert frame._validate_int_field("71", flow, "start_age", start_age_var, 0) is True

    assert flow["start_age"] == 40
    assert flow["end_age"] == 70
    assert start_age_var.get() == "40"
    assert len(shown_errors) == 1


def test_equal_start_and_end_age_is_accepted(tk_root, patched_module, monkeypatch):
    flow = _make_flow(start_age=40, end_age=70)
    frame, _, shown_errors = _make_frame(tk_root, patched_module, monkeypatch, flow)
    end_age_var = frame.row_vars[0]["vars"]["end_age"]

    assert frame._validate_int_field("40", flow, "end_age", end_age_var, 120) is True

    assert flow["start_age"] == 40
    assert flow["end_age"] == 40
    assert shown_errors == []


def test_inflation_adjustment_allows_negative_value(tk_root, patched_module, monkeypatch):
    flow = _make_flow(inflation_adjustment_pct=0.0)
    frame, _, shown_errors = _make_frame(tk_root, patched_module, monkeypatch, flow)
    inflation_var = frame.row_vars[0]["vars"]["inflation_adjustment_pct"]

    assert frame._validate_float_field(
        "-25",
        flow,
        "inflation_adjustment_pct",
        inflation_var,
        0.0,
        allow_negative=True,
    ) is True

    assert flow["inflation_adjustment_pct"] == pytest.approx(-25.0)
    assert inflation_var.get() == "-25.0"
    assert shown_errors == []


@pytest.mark.parametrize("bad_value", ["NaN", "inf", "-inf"])
def test_inflation_adjustment_rejects_nonfinite_values(
    tk_root,
    patched_module,
    monkeypatch,
    bad_value,
):
    flow = _make_flow(inflation_adjustment_pct=10.0)
    frame, _, shown_errors = _make_frame(tk_root, patched_module, monkeypatch, flow)
    inflation_var = frame.row_vars[0]["vars"]["inflation_adjustment_pct"]

    assert frame._validate_float_field(
        bad_value,
        flow,
        "inflation_adjustment_pct",
        inflation_var,
        0.0,
        allow_negative=True,
    ) is True

    assert flow["inflation_adjustment_pct"] == pytest.approx(10.0)
    assert inflation_var.get() == "10.0"
    assert len(shown_errors) == 1


def test_add_new_flow_uses_expected_defaults(tk_root, patched_module):
    flows = []
    frame = patched_module.RothEditFrame(tk_root, roth_flows=flows)
    frame.pack()

    frame._add_new_flow()

    assert len(flows) == 1
    assert flows[0] == {
        "owner": "husband",
        "type": "roth_ira_contribution",
        "name": "",
        "amount": 0.0,
        "start_age": 0,
        "end_age": 120,
        "enabled": True,
        "inflation_adjustment_pct": 0.0,
    }


def test_delete_flow_removes_flow(tk_root, patched_module):
    flow = _make_flow()
    flows = [flow]

    frame = patched_module.RothEditFrame(tk_root, roth_flows=flows)
    frame.pack()

    frame._delete_flow(flow)

    assert flows == []
    assert frame.row_vars == []