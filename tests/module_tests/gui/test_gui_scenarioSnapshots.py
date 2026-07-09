# test_gui_scenarioSnapshots.py

from __future__ import annotations

import pytest

from src.warpsimlab.gui.gui_scenarioSnapshots import ScenarioSnapshots


def test_defaults_are_assigned():
    s = ScenarioSnapshots()

    assert s.inflation == 0.0
    assert s.fund_expense == 0.0
    assert s.custom_stock_percent == 0.0
    assert s.custom_bonds_percent == 0.0
    assert s.custom_cash_percent == 0.0
    assert s.rebalance_var == "dont-rebalance"
    assert s.historical_data_multiplier == 1.0
    assert s.use_snapshot_annotations is False

    assert s.scenario_withdraw_pct is None
    assert s.scenario_expense_multiplier is None

    assert s.adjust_hist_for_infl_delta is False
    assert s.delta_inflation == 0.0


def test_annotation_strings_defaults_to_new_list_when_none():
    s1 = ScenarioSnapshots(annotation_strings=None)
    s2 = ScenarioSnapshots(annotation_strings=None)

    assert isinstance(s1.annotation_strings, list)
    assert s1.annotation_strings == []

    # Ensure not the same list object across instances
    assert s1.annotation_strings is not s2.annotation_strings


def test_annotation_strings_preserves_reference_when_provided():
    annotations = [[{"text": "hello", "color": None}]]
    s = ScenarioSnapshots(annotation_strings=annotations)

    assert s.annotation_strings is annotations
    assert s.annotation_strings == [[{"text": "hello", "color": None}]]


def test_can_set_optional_scenario_fields():
    s = ScenarioSnapshots(
        scenario_withdraw_pct=6.5,
        scenario_expense_multiplier=1.25,
        use_snapshot_annotations=True,
    )

    assert s.scenario_withdraw_pct == pytest.approx(6.5)
    assert s.scenario_expense_multiplier == pytest.approx(1.25)
    assert s.use_snapshot_annotations is True


def test_inflation_delta_fields():
    s = ScenarioSnapshots(adjust_hist_for_infl_delta=True, delta_inflation=0.75)

    assert s.adjust_hist_for_infl_delta is True
    assert s.delta_inflation == pytest.approx(0.75)