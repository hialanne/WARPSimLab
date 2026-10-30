from copy import deepcopy
from types import SimpleNamespace

import pytest

from src.warpsimlab.gui import gui_annotations as mod


@pytest.mark.parametrize("controls,label", [({}, None), ({"results_mode": "fill"}, None),
    ({"results_mode": "risk_analysis"}, "Monte Carlo"),
    ({"results_mode": "risk_analysis", "risk_analysis_mode": "historical_windows"}, "Historical Windows")])
def test_normal_annotations_only_label_multi_path_runs(controls, label):
    before = deepcopy(controls)
    expected = [] if label is None else [[{"text": f"Percentile Bands ({label})", "color": "black"}]]
    assert mod.build_normal_run_annotations(controls) == expected
    assert controls == before


@pytest.mark.parametrize("manual,couple", [(True, True), (False, False)])
def test_scenario_annotations_highlight_only_changed_assumptions(manual, couple):
    gui = SimpleNamespace(husband=SimpleNamespace(retire_age=65), wife=SimpleNamespace(retire_age=62),
        inflation=3, simulation_settings={"fund_expense": .2},
        simulation_controls={"manual_expenses": manual, "retirement_withdraw_pct": 4})
    annotations = mod.build_scenario_explorer_annotations(main_gui=gui,
        tmp_ret_age_h=66, tmp_ret_age_w=62 if couple else None,
        inflation=3, fund_expense=.3, historical_data_multiplier=90,
        stocks=60, bonds=30, cash=10, baseline_stocks=60, baseline_bonds=20, baseline_cash=20,
        wife_snapshot=object() if couple else None, scenario_expense_multiplier=1.1, scenario_withdraw_pct=5)
    fragments = [item for row in annotations for item in row]
    def color(text):
        return next(item["color"] for item in fragments if text in item["text"])
    assert color("Husband 66") == "red"
    if couple:
        assert color("Wife 62") == "black"
    assert color("Inflation rate") == "black"
    assert color("Fund Expenses") == "red"
    assert color("Stock 60") == "black"
    assert color("Bond 30") == "red"
    assert color("Expense Multiplier" if manual else "Withdrawal %") == "red"
