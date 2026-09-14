from types import SimpleNamespace

import pytest

from src.warpsimlab.gui.scenario import gui_scenarioController as mod


class DummyButton:
    def __init__(self):
        self.state = None

    def config(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs["state"]


class DummyWindow:
    def __init__(self):
        self.lift_count = 0
        self.focus_count = 0
        self.destroy_count = 0
        self.cancelled_jobs = []
        self.after_calls = []
        self.focus_set_count = 0

    def lift(self):
        self.lift_count += 1

    def focus_force(self):
        self.focus_count += 1

    def focus_set(self):
        self.focus_set_count += 1

    def destroy(self):
        self.destroy_count += 1

    def after(self, ms, callback):
        self.after_calls.append((ms, callback))
        return "job-1"

    def after_cancel(self, job):
        self.cancelled_jobs.append(job)


class DummyValue:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


@pytest.fixture
def main_gui():
    return SimpleNamespace(
        root=object(),
        results_button=DummyButton(),
        simulation_controls={
            "second_person_enabled": False,
            "include_realestate": False,
        },
        simulation_settings={"fund_expense": 0.5},
        display_settings={"scenario_explorer": {"layout_mode": None, "layout": None}},
        husband=SimpleNamespace(retire_age=65),
        wife=SimpleNamespace(retire_age=63),
        husband_portfolio=SimpleNamespace(),
        wife_portfolio=SimpleNamespace(),
        expensesDict={},
        inflation=3.0,
    )


def test_initializes_explicit_component_boundaries(main_gui):
    controller = mod.ScenarioController(main_gui)

    assert controller.main_gui is main_gui
    assert isinstance(controller.session_state, mod.ScenarioSessionState)
    assert isinstance(controller.state_manager, mod.ScenarioStateManager)
    assert isinstance(controller.plot_manager, mod.ScenarioPlotManager)

    assert controller.state_manager.main_gui is main_gui
    assert controller.state_manager.session_state is controller.session_state
    assert controller.plot_manager.main_gui is main_gui

    assert controller.session_active is False
    assert controller.window is None
    assert controller.sliders_frame is None
    assert controller.results_frame is None


def test_initial_mode_and_plot_style(main_gui):
    controller = mod.ScenarioController(main_gui)

    assert controller.mode == mod.SCENARIO_MODE_SCENARIO_VIEW
    assert controller.plot_style == mod.SCENARIO_PLOT_STYLE_FILL


def test_start_or_focus_starts_session_when_inactive(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    called = {"start": 0}

    monkeypatch.setattr(controller, "_start_session", lambda: called.__setitem__("start", called["start"] + 1))

    controller.start_or_focus()

    assert called["start"] == 1


def test_start_or_focus_focuses_existing_window(main_gui):
    controller = mod.ScenarioController(main_gui)
    window = DummyWindow()

    controller.session_active = True
    controller.window = window

    controller.start_or_focus()

    assert window.lift_count == 1
    assert window.focus_count == 1


def test_start_or_focus_does_not_start_second_session(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    window = DummyWindow()
    called = {"start": 0}

    controller.session_active = True
    controller.window = window
    monkeypatch.setattr(controller, "_start_session", lambda: called.__setitem__("start", called["start"] + 1))

    controller.start_or_focus()

    assert called["start"] == 0


def test_resolve_panels_for_scenario_view(main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.mode = mod.SCENARIO_MODE_SCENARIO_VIEW

    left, right = controller._resolve_panels_for_mode()

    assert left == {
        "plot_family": mod.PLOT_FAMILY_CASHFLOW,
        "result_source": mod.RESULT_SOURCE_SCENARIO,
    }
    assert right == {
        "plot_family": mod.PLOT_FAMILY_PORTFOLIO,
        "result_source": mod.RESULT_SOURCE_SCENARIO,
    }


@pytest.mark.parametrize(
    "mode,plot_family",
    [
        (mod.SCENARIO_MODE_INCOME_COMPARE, mod.PLOT_FAMILY_INCOME),
        (mod.SCENARIO_MODE_CASHFLOW_COMPARE, mod.PLOT_FAMILY_CASHFLOW),
        (mod.SCENARIO_MODE_PORTFOLIO_COMPARE, mod.PLOT_FAMILY_PORTFOLIO),
    ],
)
def test_resolve_panels_for_compare_modes(main_gui, mode, plot_family):
    controller = mod.ScenarioController(main_gui)
    controller.mode = mode

    left, right = controller._resolve_panels_for_mode()

    assert left == {
        "plot_family": plot_family,
        "result_source": mod.RESULT_SOURCE_BASELINE,
    }
    assert right == {
        "plot_family": plot_family,
        "result_source": mod.RESULT_SOURCE_SCENARIO,
    }


def test_create_persistent_plots_delegates_to_plot_manager(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.window = DummyWindow()
    received = {}

    def fake_create(window):
        received["window"] = window

    monkeypatch.setattr(controller.plot_manager, "create_persistent_plots", fake_create)

    controller._create_persistent_plots()

    assert received["window"] is controller.window


def test_capture_current_layout_delegates_to_plot_manager(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.window = DummyWindow()
    received = {}

    monkeypatch.setattr(
        controller.plot_manager,
        "capture_current_layout",
        lambda window: received.__setitem__("window", window),
    )

    controller.capture_current_layout()

    assert received["window"] is controller.window


def test_position_windows_delegates_to_plot_manager(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.window = DummyWindow()
    received = {}

    monkeypatch.setattr(
        controller.plot_manager,
        "position_windows",
        lambda window: received.__setitem__("window", window),
    )

    controller._position_windows()

    assert received["window"] is controller.window


def test_build_snapshots_from_truth_delegates_to_state_manager(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    called = {"count": 0}

    monkeypatch.setattr(
        controller.state_manager,
        "build_snapshots_from_truth",
        lambda: called.__setitem__("count", called["count"] + 1),
    )

    controller._build_snapshots_from_truth()

    assert called["count"] == 1


def test_apply_slider_values_returns_when_sliders_missing(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    called = {"count": 0}

    monkeypatch.setattr(
        controller.state_manager,
        "apply_control_values",
        lambda values: called.__setitem__("count", called["count"] + 1),
    )

    controller.sliders_frame = None
    controller._apply_slider_values_to_snapshots()

    assert called["count"] == 0


def test_apply_slider_values_passes_control_values_to_state_manager(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    values = object()
    received = {}

    controller.sliders_frame = SimpleNamespace(get_values=lambda: values)
    monkeypatch.setattr(
        controller.state_manager,
        "apply_control_values",
        lambda received_values: received.__setitem__("values", received_values),
    )

    controller._apply_slider_values_to_snapshots()

    assert received["values"] is values


def test_compute_baseline_results_passes_main_gui_realestate_and_plot_style(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.plot_style = mod.SCENARIO_PLOT_STYLE_SUB_CATEGORIES
    main_gui.simulation_controls["include_realestate"] = True
    received = {}

    def fake_compute(include_realestate, plot_style):
        received["include_realestate"] = include_realestate
        received["plot_style"] = plot_style

    monkeypatch.setattr(controller.state_manager, "compute_baseline_results", fake_compute)

    controller._compute_baseline_results()

    assert received["include_realestate"] is True
    assert received["plot_style"] == mod.SCENARIO_PLOT_STYLE_SUB_CATEGORIES


def test_compute_scenario_results_passes_scenario_realestate_and_plot_style(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.include_realestate_var = DummyValue(True)
    controller.plot_style = mod.SCENARIO_PLOT_STYLE_PRE_POST_TAX
    expected_result = {"scenario": True}
    received = {}

    def fake_compute(include_realestate, plot_style):
        received["include_realestate"] = include_realestate
        received["plot_style"] = plot_style
        return expected_result

    monkeypatch.setattr(controller.state_manager, "compute_scenario_results", fake_compute)

    result = controller._compute_scenario_results()

    assert result is expected_result
    assert received["include_realestate"] is True
    assert received["plot_style"] == mod.SCENARIO_PLOT_STYLE_PRE_POST_TAX


def test_render_panels_passes_explicit_render_inputs(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.mode = mod.SCENARIO_MODE_PORTFOLIO_COMPARE
    controller.session_state.baseline_results = {"baseline": True}
    controller.session_state.scenario_results = {"scenario": True}
    controller.sliders_frame = SimpleNamespace(enable_annotations=DummyValue(True))
    received = {}

    def fake_render(
        left_panel,
        right_panel,
        baseline_results,
        scenario_results,
        mode,
        annotations_enabled,
        sync_axes=False,
    ):
        received["left_panel"] = left_panel
        received["right_panel"] = right_panel
        received["baseline_results"] = baseline_results
        received["scenario_results"] = scenario_results
        received["mode"] = mode
        received["annotations_enabled"] = annotations_enabled
        received["sync_axes"] = sync_axes

    monkeypatch.setattr(controller.plot_manager, "render_panels", fake_render)

    controller._render_panels()

    assert received["left_panel"]["result_source"] == mod.RESULT_SOURCE_BASELINE
    assert received["right_panel"]["result_source"] == mod.RESULT_SOURCE_SCENARIO
    assert received["baseline_results"] is controller.session_state.baseline_results
    assert received["scenario_results"] is controller.session_state.scenario_results
    assert received["mode"] == mod.SCENARIO_MODE_PORTFOLIO_COMPARE
    assert received["annotations_enabled"] is True
    assert received["sync_axes"] is True


def test_render_panels_scenario_view_does_not_sync_axes(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.mode = mod.SCENARIO_MODE_SCENARIO_VIEW
    controller.sliders_frame = None
    received = {}

    def fake_render(*args, **kwargs):
        received["annotations_enabled"] = args[5]
        received["sync_axes"] = kwargs["sync_axes"]

    monkeypatch.setattr(controller.plot_manager, "render_panels", fake_render)

    controller._render_panels()

    assert received["annotations_enabled"] is False
    assert received["sync_axes"] is False


def test_run_scenario_simulation_updates_results_then_renders(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    calls = []
    view_model = object()

    controller.results_frame = SimpleNamespace(
        update_results=lambda value: calls.append(("results", value))
    )

    monkeypatch.setattr(
        controller,
        "_compute_scenario_results",
        lambda: calls.append(("compute", None)),
    )
    monkeypatch.setattr(
        controller.state_manager,
        "build_results_view_model",
        lambda: view_model,
    )
    monkeypatch.setattr(
        controller,
        "_render_panels",
        lambda: calls.append(("render", None)),
    )

    controller._run_scenario_simulation()

    assert calls == [
        ("compute", None),
        ("results", view_model),
        ("render", None),
    ]


def test_run_scenario_simulation_renders_without_results_frame(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    calls = []

    controller.results_frame = None

    monkeypatch.setattr(
        controller,
        "_compute_scenario_results",
        lambda: calls.append("compute"),
    )
    monkeypatch.setattr(
        controller,
        "_render_panels",
        lambda: calls.append("render"),
    )

    controller._run_scenario_simulation()

    assert calls == ["compute", "render"]


def test_run_and_redraw_returns_when_session_inactive(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    called = {"count": 0}

    monkeypatch.setattr(
        controller,
        "_apply_slider_values_to_snapshots",
        lambda: called.__setitem__("count", called["count"] + 1),
    )

    controller.session_active = False
    controller.run_and_redraw()

    assert called["count"] == 0


def test_run_and_redraw_returns_when_plots_missing(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.session_active = True

    monkeypatch.setattr(controller.plot_manager, "has_plots", lambda: False)

    called = {"apply": 0, "run": 0}
    monkeypatch.setattr(
        controller,
        "_apply_slider_values_to_snapshots",
        lambda: called.__setitem__("apply", called["apply"] + 1),
    )
    monkeypatch.setattr(
        controller,
        "_run_scenario_simulation",
        lambda: called.__setitem__("run", called["run"] + 1),
    )

    controller.run_and_redraw()

    assert called["apply"] == 0
    assert called["run"] == 0
    assert controller._is_redrawing is False


def test_run_and_redraw_applies_values_then_runs_simulation(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.session_active = True
    calls = []

    monkeypatch.setattr(controller.plot_manager, "has_plots", lambda: True)
    monkeypatch.setattr(
        controller,
        "_apply_slider_values_to_snapshots",
        lambda: calls.append("apply"),
    )
    monkeypatch.setattr(
        controller,
        "_run_scenario_simulation",
        lambda: calls.append("run"),
    )

    controller.run_and_redraw()

    assert calls == ["apply", "run"]
    assert controller._is_redrawing is False


def test_run_and_redraw_marks_followup_when_reentrant(main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.session_active = True
    controller._is_redrawing = True

    controller.run_and_redraw()

    assert controller._needs_redraw is True


def test_run_and_redraw_schedules_followup_when_needed(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.session_active = True
    controller._needs_redraw = True
    calls = []

    monkeypatch.setattr(controller.plot_manager, "has_plots", lambda: True)
    monkeypatch.setattr(controller, "_apply_slider_values_to_snapshots", lambda: None)
    monkeypatch.setattr(controller, "_run_scenario_simulation", lambda: None)
    monkeypatch.setattr(controller, "schedule_update", lambda: calls.append("schedule"))

    controller.run_and_redraw()

    assert calls == ["schedule"]
    assert controller._needs_redraw is False
    assert controller._is_redrawing is False


def test_schedule_update_returns_when_session_inactive(main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.window = DummyWindow()
    controller.session_active = False

    controller.schedule_update()

    assert controller._pending_job_id is None
    assert controller.window.after_calls == []


def test_schedule_update_marks_followup_when_redrawing(main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.window = DummyWindow()
    controller.session_active = True
    controller._is_redrawing = True

    controller.schedule_update()

    assert controller._needs_redraw is True
    assert controller.window.after_calls == []


def test_schedule_update_cancels_existing_job_and_schedules_new_one(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.window = DummyWindow()
    controller.session_active = True
    controller._pending_job_id = "old-job"

    controller.schedule_update()

    assert controller.window.cancelled_jobs == ["old-job"]
    assert len(controller.window.after_calls) == 1
    assert controller.window.after_calls[0][0] == controller._debounce_ms
    assert controller._pending_job_id == "job-1"


def test_scheduled_callback_clears_job_before_redraw(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.window = DummyWindow()
    controller.session_active = True
    calls = []

    monkeypatch.setattr(
        controller,
        "run_and_redraw",
        lambda: calls.append(controller._pending_job_id),
    )

    controller.schedule_update()
    callback = controller.window.after_calls[0][1]
    callback()

    assert calls == [None]
    assert controller._pending_job_id is None


def test_cancel_pending_update_is_safe_when_no_job(main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.window = DummyWindow()

    controller._cancel_pending_update()

    assert controller.window.cancelled_jobs == []
    assert controller._pending_job_id is None


def test_cancel_pending_update_cancels_and_clears_job(main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.window = DummyWindow()
    controller._pending_job_id = "job-1"

    controller._cancel_pending_update()

    assert controller.window.cancelled_jobs == ["job-1"]
    assert controller._pending_job_id is None


def test_resync_returns_when_session_inactive(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.window = DummyWindow()
    controller.session_active = False
    called = {"count": 0}

    monkeypatch.setattr(
        controller,
        "_build_snapshots_from_truth",
        lambda: called.__setitem__("count", called["count"] + 1),
    )

    controller.resync()

    assert called["count"] == 0


def test_resync_rebuilds_baseline_and_scenario_in_order(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.window = DummyWindow()
    controller.session_active = True
    controller.mode = mod.SCENARIO_MODE_PORTFOLIO_COMPARE
    controller.plot_style = mod.SCENARIO_PLOT_STYLE_HISTORICAL_RISK
    controller._needs_redraw = True

    calls = []

    monkeypatch.setattr(controller, "_cancel_pending_update", lambda: calls.append("cancel"))
    monkeypatch.setattr(controller, "_build_snapshots_from_truth", lambda: calls.append("build_snapshots"))
    monkeypatch.setattr(controller, "_build_controls_ui", lambda: calls.append("build_ui"))
    monkeypatch.setattr(controller, "_apply_slider_values_to_snapshots", lambda: calls.append("apply_values"))
    monkeypatch.setattr(
        controller.state_manager,
        "capture_baseline_from_scenario",
        lambda: calls.append("capture_baseline"),
    )
    monkeypatch.setattr(controller, "_compute_baseline_results", lambda: calls.append("baseline_results"))
    monkeypatch.setattr(controller, "run_and_redraw", lambda: calls.append("run"))

    controller.resync()

    assert controller.mode == mod.SCENARIO_MODE_SCENARIO_VIEW
    assert controller.plot_style == mod.SCENARIO_PLOT_STYLE_FILL
    assert controller._needs_redraw is False
    assert calls == [
        "cancel",
        "build_snapshots",
        "build_ui",
        "apply_values",
        "capture_baseline",
        "baseline_results",
        "run",
    ]


def test_mode_change_updates_mode_and_renders_only(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.session_active = True
    controller.mode_var = DummyValue("Compare Portfolio")
    calls = []

    monkeypatch.setattr(controller, "_cancel_pending_update", lambda: calls.append("cancel"))
    monkeypatch.setattr(controller, "_render_panels", lambda: calls.append("render"))

    controller._on_mode_changed()

    assert controller.mode == mod.SCENARIO_MODE_PORTFOLIO_COMPARE
    assert calls == ["cancel", "render"]


def test_plot_style_change_recomputes_baseline_and_scenario(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.session_active = True
    controller.window = DummyWindow()
    controller.plot_style_var = DummyValue("Historical Risk")
    controller.plot_style_dropdown = SimpleNamespace(selection_clear=lambda: None)
    calls = []

    monkeypatch.setattr(controller, "_cancel_pending_update", lambda: calls.append("cancel"))
    monkeypatch.setattr(controller, "_compute_baseline_results", lambda: calls.append("baseline"))
    monkeypatch.setattr(controller, "run_and_redraw", lambda: calls.append("scenario"))

    controller._on_plot_style_dropdown_selected()

    assert controller.plot_style == mod.SCENARIO_PLOT_STYLE_HISTORICAL_RISK
    assert calls == ["cancel", "baseline", "scenario"]
    assert controller.window.focus_set_count == 1


def test_stop_session_returns_when_inactive(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    called = {"close": 0}

    monkeypatch.setattr(
        controller.plot_manager,
        "close_plots",
        lambda: called.__setitem__("close", called["close"] + 1),
    )

    controller._stop_session()

    assert called["close"] == 0


def test_stop_session_cleans_up_session_state(monkeypatch, main_gui):
    controller = mod.ScenarioController(main_gui)
    controller.session_active = True
    controller.window = DummyWindow()
    controller._pending_job_id = "job-1"
    controller._needs_redraw = True
    controller._is_redrawing = True
    controller.session_state.baseline_results = {"baseline": True}
    controller.session_state.scenario_results = {"scenario": True}

    calls = []

    monkeypatch.setattr(controller, "capture_current_layout", lambda: calls.append("capture"))
    monkeypatch.setattr(controller.plot_manager, "close_plots", lambda: calls.append("close"))

    controller._stop_session()

    assert "capture" in calls
    assert "close" in calls
    assert controller.window is None
    assert controller.session_active is False
    assert controller._pending_job_id is None
    assert controller._needs_redraw is False
    assert controller._is_redrawing is False
    assert controller.session_state.baseline_results is None
    assert controller.session_state.scenario_results is None