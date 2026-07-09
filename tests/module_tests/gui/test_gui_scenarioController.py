# test_gui_scenarioController.py

from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.fixture
def dummy_gui():
    """
    Minimal object providing attributes used by ScenarioController.
    """
    class DummyBtn:
        def __init__(self):
            self.state = None

        def config(self, **kw):
            if "state" in kw:
                self.state = kw["state"]

    return SimpleNamespace(
        root=object(),
        income_btn=DummyBtn(),
        operating_balance_btn=DummyBtn(),
        portfolio_balance_btn=DummyBtn(),
        summary_btn=DummyBtn(),
        temp_overrides_btn=DummyBtn(),
        simulation_controls={"enable_second_person": False},
        simulation_settings={"fund_expense": 0.5},
        husband=SimpleNamespace(retire_age=65),
        wife=SimpleNamespace(retire_age=63),
        husband_portfolio=SimpleNamespace(),
        wife_portfolio=SimpleNamespace(),
        expensesDict={},
        inflation=3.0,
        build_simulation_from_gui=lambda **k: SimpleNamespace(
            second_person_enabled=False,
            annotate_plots=False
        )
    )


def test_start_or_focus_calls_start_session(monkeypatch, dummy_gui):
    from src.warpsimlab.gui import gui_scenarioController as mod

    ctrl = mod.ScenarioController(dummy_gui)

    called = {"start": 0}

    monkeypatch.setattr(ctrl, "_start_session", lambda: called.__setitem__("start", 1))

    ctrl.start_or_focus()

    assert called["start"] == 1


def test_start_or_focus_focuses_existing_window(monkeypatch, dummy_gui):
    from src.warpsimlab.gui import gui_scenarioController as mod

    ctrl = mod.ScenarioController(dummy_gui)

    called = {"lift": 0, "focus": 0}

    class DummyWin:
        def lift(self):
            called["lift"] += 1
        def focus_force(self):
            called["focus"] += 1

    ctrl.session_active = True
    ctrl.window = DummyWin()

    ctrl.start_or_focus()

    assert called["lift"] == 1
    assert called["focus"] == 1


def test_stop_session_resets_state(monkeypatch, dummy_gui):
    from src.warpsimlab.gui import gui_scenarioController as mod

    ctrl = mod.ScenarioController(dummy_gui)

    ctrl.session_active = True

    class DummyWin:
        def destroy(self):
            pass

    ctrl.window = DummyWin()
    ctrl.income_fig = None
    ctrl.portfolio_fig = None

    ctrl._stop_session()

    assert ctrl.session_active is False
    assert ctrl.window is None


def test_schedule_update_sets_pending_job(monkeypatch, dummy_gui):
    from src.warpsimlab.gui import gui_scenarioController as mod

    ctrl = mod.ScenarioController(dummy_gui)

    class DummyWindow:
        def after(self, ms, fn):
            return "jobid"

    ctrl.window = DummyWindow()
    ctrl.session_active = True

    ctrl.schedule_update()

    assert ctrl._pending_job_id == "jobid"


def test_cancel_pending_update_clears_job(monkeypatch, dummy_gui):
    from src.warpsimlab.gui import gui_scenarioController as mod

    ctrl = mod.ScenarioController(dummy_gui)

    cancelled = {"count": 0}

    class DummyWindow:
        def after_cancel(self, job):
            cancelled["count"] += 1

    ctrl.window = DummyWindow()
    ctrl._pending_job_id = "job1"

    ctrl._cancel_pending_update()

    assert cancelled["count"] == 1
    assert ctrl._pending_job_id is None


def test_build_snapshots_from_truth(monkeypatch, dummy_gui):
    from src.warpsimlab.gui import gui_scenarioController as mod

    ctrl = mod.ScenarioController(dummy_gui)

    ctrl._build_snapshots_from_truth()

    assert "husband" in ctrl.person_snapshots
    assert "husband" in ctrl.portfolio_snapshots

    assert ctrl.retirement_snapshots is not None
    assert ctrl.retirement_snapshots.inflation == dummy_gui.inflation