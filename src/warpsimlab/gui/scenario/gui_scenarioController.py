# gui_scenarioController.py

import tkinter as tk
from tkinter import ttk

SCENARIO_MODE_SCENARIO_VIEW = "scenario_view"
SCENARIO_MODE_INCOME_COMPARE = "income_compare"
SCENARIO_MODE_CASHFLOW_COMPARE = "cashflow_compare"
SCENARIO_MODE_PORTFOLIO_COMPARE = "portfolio_compare"

SCENARIO_PLOT_STYLE_FILL = "fill"
SCENARIO_PLOT_STYLE_HISTORICAL_RISK = "historical_risk"
SCENARIO_PLOT_STYLE_SUB_CATEGORIES = "sub_categories"
SCENARIO_PLOT_STYLE_PRE_POST_TAX = "pre_post_tax"

SCENARIO_PLOT_STYLE_OPTIONS = [
    ("Fill", SCENARIO_PLOT_STYLE_FILL),
    ("Historical Risk", SCENARIO_PLOT_STYLE_HISTORICAL_RISK),
    ("Sub Categories", SCENARIO_PLOT_STYLE_SUB_CATEGORIES),
    ("Tax-Deferred / Taxable Savings", SCENARIO_PLOT_STYLE_PRE_POST_TAX),
]

SCENARIO_REBALANCING_OPTIONS = [
    ("Not Rebalancing", False),
    ("Annual Rebalancing", True),
]

SCENARIO_MODE_OPTIONS = [
    ("Scenario View", SCENARIO_MODE_SCENARIO_VIEW),
    ("Compare Income", SCENARIO_MODE_INCOME_COMPARE),
    ("Compare Cash Flow", SCENARIO_MODE_CASHFLOW_COMPARE),
    ("Compare Portfolio", SCENARIO_MODE_PORTFOLIO_COMPARE),
]

from src.warpsimlab.gui.scenario.gui_scenarioSliders import ScenarioSlidersFrame
from src.warpsimlab.gui.scenario.gui_scenarioPlots import (
    ScenarioPlotManager, PLOT_FAMILY_INCOME, PLOT_FAMILY_CASHFLOW, 
    PLOT_FAMILY_PORTFOLIO, RESULT_SOURCE_BASELINE, RESULT_SOURCE_SCENARIO
)

from src.warpsimlab.gui.gui_utils import set_tk_button_soft_disabled, noop
from src.warpsimlab.gui.scenario.gui_scenarioState import ScenarioSessionState, ScenarioStateManager
from src.warpsimlab.gui.scenario.gui_scenarioResults import ScenarioResultsFrame

class ScenarioController:
    """
    Controls lifecycle of the Scenario Dashboard (Scenario mode).
    """

    def __init__(self, main_gui):
        self.main_gui = main_gui
        self.session_state = ScenarioSessionState()
        self.plot_manager = ScenarioPlotManager(self.main_gui, self._stop_session)
        self.state_manager = ScenarioStateManager(self.main_gui, self.session_state)
        self.session_active = False
        self.window = None

        self.sliders_frame = None              # ScenarioSlidersFrame widget
        self.results_frame = None

        self._pending_job_id = None
        self._debounce_ms = 150  # adjust if desired (200-400)

        self._is_redrawing = False
        self._needs_redraw = False

        self.mode = SCENARIO_MODE_SCENARIO_VIEW
        self.mode_var = None
        self.plot_style = SCENARIO_PLOT_STYLE_FILL
        self.plot_style_var = None
        self.rebalancing_var = None
        self.include_realestate_var = None

        self.mode_label_to_value = {label: value for label, value in SCENARIO_MODE_OPTIONS}
        self.mode_value_to_label = {value: label for label, value in SCENARIO_MODE_OPTIONS}

        self.plot_style_label_to_value = {label: value for label, value in SCENARIO_PLOT_STYLE_OPTIONS}
        self.plot_style_value_to_label = {value: label for label, value in SCENARIO_PLOT_STYLE_OPTIONS}

    # ----------------------------------------------------------
    # Public entry point from button
    # ----------------------------------------------------------
    def start_or_focus(self):
        if self.session_active and self.window is not None:
            self.window.lift()
            self.window.focus_force()
            return

        self._start_session()


    def _set_results_menu_enabled(self, enabled):
        """
        Enable/disable the top Results menu button while Scenario Explorer is active.
        """
        if not hasattr(self.main_gui, "results_button"):
            return

        show_cmd = getattr(self.main_gui, "_show_results_menu", None)
        if show_cmd is None:
            return

        set_tk_button_soft_disabled(
            self.main_gui.results_button,
            enabled,
            show_cmd,
            noop_command=noop
        )


    # ----------------------------------------------------------
    # Start session
    # ----------------------------------------------------------
    def _start_session(self):
        if self.session_active:
            return

        self.session_active = True

        # Disable Results menu while Scenario Explorer is active
        self._set_results_menu_enabled(False)

        # Create control window
        self.window = tk.Toplevel(self.main_gui.root)
        self.window.title("Scenario Dashboard")

        # If user closes via X
        self.window.protocol(
            "WM_DELETE_WINDOW",
            self._stop_session,
        )

        # Create both Matplotlib plot windows.
        # This method also restores or automatically positions them.
        self._create_persistent_plots()

        # Build snapshots + controls UI + run once
        self.resync()


    # ----------------------------------------------------------
    # Stop session
    # ----------------------------------------------------------
    def _stop_session(self):
        if not self.session_active:
            return

        self._cancel_pending_update()

        self.capture_current_layout()

        self._needs_redraw = False
        self._is_redrawing = False

        # Restore Results/top-bar state through the main GUI policy
        if hasattr(self.main_gui, "_apply_mode_to_top_buttons"):
            self.main_gui._apply_mode_to_top_buttons()
        elif hasattr(self.main_gui, "_apply_mode_to_results_button"):
            self.main_gui._apply_mode_to_results_button()
        else:
            self._set_results_menu_enabled(True)

        # Close window if exists
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:
                pass

        self.plot_manager.close_plots()

        self.session_state.baseline_results = None
        self.session_state.scenario_results = None

        self.window = None
        self.session_active = False


    def _create_persistent_plots(self):
        self.plot_manager.create_persistent_plots(self.window)


    def capture_current_layout(self):
        self.plot_manager.capture_current_layout(self.window)


    def _position_windows(self):
        self.plot_manager.position_windows(self.window)


    def _resolve_panels_for_mode(self):
        """
        Return (left_panel, right_panel) for current mode.
        Each panel is a dict:
            { "plot_family": ..., "result_source": ... }
        """

        if self.mode == SCENARIO_MODE_SCENARIO_VIEW:
            return (
                {"plot_family": PLOT_FAMILY_CASHFLOW, "result_source": RESULT_SOURCE_SCENARIO},
                {"plot_family": PLOT_FAMILY_PORTFOLIO, "result_source": RESULT_SOURCE_SCENARIO},
            )

        elif self.mode == SCENARIO_MODE_INCOME_COMPARE:
            return (
                {"plot_family": PLOT_FAMILY_INCOME, "result_source": RESULT_SOURCE_BASELINE},
                {"plot_family": PLOT_FAMILY_INCOME, "result_source": RESULT_SOURCE_SCENARIO},
            )

        elif self.mode == SCENARIO_MODE_CASHFLOW_COMPARE:
            return (
                {"plot_family": PLOT_FAMILY_CASHFLOW, "result_source": RESULT_SOURCE_BASELINE},
                {"plot_family": PLOT_FAMILY_CASHFLOW, "result_source": RESULT_SOURCE_SCENARIO},
            )

        elif self.mode == SCENARIO_MODE_PORTFOLIO_COMPARE:
            return (
                {"plot_family": PLOT_FAMILY_PORTFOLIO, "result_source": RESULT_SOURCE_BASELINE},
                {"plot_family": PLOT_FAMILY_PORTFOLIO, "result_source": RESULT_SOURCE_SCENARIO},
            )

        # fallback safety
        return (
            {"plot_family": PLOT_FAMILY_CASHFLOW, "result_source": RESULT_SOURCE_SCENARIO},
            {"plot_family": PLOT_FAMILY_PORTFOLIO, "result_source": RESULT_SOURCE_SCENARIO},
        )


    def resync(self):
        """
        Discard current Scenario snapshots and rebuild from GUI truth.
        Reset slider values to match truth, recompute baseline/original results,
        and redraw using the scenario path so visible behavior stays unchanged.
        """
        if not self.session_active or self.window is None:
            return

        self._cancel_pending_update()
        self._needs_redraw = False

        self.mode = SCENARIO_MODE_SCENARIO_VIEW
        self.plot_style = SCENARIO_PLOT_STYLE_FILL

        self._build_snapshots_from_truth()
        self._build_controls_ui()

        # Synchronize initialized slider values back into scenario snapshots.
        self._apply_slider_values_to_snapshots()

        # Freeze the fully initialized scenario state as the session baseline.
        self.state_manager.capture_baseline_from_scenario()

        self._compute_baseline_results()
        self.run_and_redraw()


    def run_and_redraw(self):
        if not self.session_active:
            return

        # Prevent re-entrancy / overlapping redraws
        if self._is_redrawing:
            self._needs_redraw = True
            return

        self._is_redrawing = True

        try:
            # Cannot draw until plots exist
            if not self.plot_manager.has_plots():
                return

            self._apply_slider_values_to_snapshots()
            self._run_scenario_simulation()
        finally:
            self._is_redrawing = False
            if self._needs_redraw:
                self._needs_redraw = False
                self.schedule_update()
    # ----------------------------------------------------------
    # Debounced live updates
    # ----------------------------------------------------------
    def _cancel_pending_update(self):
        """
        Cancel any scheduled debounced run_and_redraw callback.
        Safe to call multiple times.
        """
        if self._pending_job_id is None:
            return

        try:
            if self.window is not None:
                self.window.after_cancel(self._pending_job_id)
        except Exception:
            pass
        finally:
            self._pending_job_id = None


    def schedule_update(self):
        """
        Debounce updates: schedule run_and_redraw in ~self._debounce_ms.
        If another change happens before it fires, reschedule.
        """
        if not self.session_active or self.window is None:
            return

        # If we're already running a redraw, don't queue another immediate job.
        # Just record that we need one more run after the current one finishes.
        if self._is_redrawing:
            self._needs_redraw = True
            return

        # Cancel prior job if any
        self._cancel_pending_update()

        def _run():
            # job is now executing; clear id first
            self._pending_job_id = None
            self.run_and_redraw()

        try:
            self._pending_job_id = self.window.after(self._debounce_ms, _run)
        except Exception:
            self._pending_job_id = None


    def _wire_live_update_traces(self):
        """
        Attach Tk variable traces so any slider/checkbox change schedules
        a debounced run_and_redraw().
        """
        if self.sliders_frame is None:
            return

        # Any change to these variables should schedule an update.
        
        vars_to_trace = [
            self.sliders_frame.tmp_ret_age_h,
            self.sliders_frame.tmp_ss_age_h,
            self.sliders_frame.inflation_value,
            self.sliders_frame.fund_expense_value,
            self.sliders_frame.stocks_percent,
            self.sliders_frame.bonds_percent,
            self.sliders_frame.cash_percent,          # changes when stocks/bonds adjust cash
            self.sliders_frame.enable_annotations,    # checkbox affects plots
            self.sliders_frame.calculate_real_dollars, 
            self.sliders_frame.dynamic_value,
        ]

        # Wife retirement age is optional
        if getattr(self.sliders_frame, "tmp_ret_age_w", None) is not None:
            vars_to_trace.append(self.sliders_frame.tmp_ret_age_w)
        if getattr(self.sliders_frame, "tmp_ss_age_w", None) is not None:
            vars_to_trace.append(self.sliders_frame.tmp_ss_age_w)

        for v in vars_to_trace:
            if v is None:
                continue
            try:
                v.trace_add("write", lambda *args: self.schedule_update())
            except Exception:
                pass


    def _on_mode_dropdown_selected(self, event=None):
        self._on_mode_changed()
        self.mode_dropdown.selection_clear()
        self.window.focus_set()


    def _on_plot_style_dropdown_selected(self, event=None):
        if self.plot_style_var is None:
            return

        selected_label = self.plot_style_var.get()
        selected_plot_style = self.plot_style_label_to_value.get(selected_label)
        if selected_plot_style is None:
            return

        self.plot_style = selected_plot_style
        self.plot_style_dropdown.selection_clear()
        self.window.focus_set()

        if self.session_active:
            self._cancel_pending_update()
            self._needs_redraw = False
            self._compute_baseline_results()
            self.run_and_redraw()


    def _on_rebalancing_dropdown_selected(self, event=None):
        if self.rebalancing_var is None:
            return

        selected_label = self.rebalancing_var.get()
        selected_value = None

        for label, value in SCENARIO_REBALANCING_OPTIONS:
            if label == selected_label:
                selected_value = value
                break

        if selected_value is None:
            return

        self.session_state.retirement_snapshots.rebalance_every_year = selected_value
        self.rebalancing_dropdown.selection_clear()
        self.window.focus_set()

        if self.session_active:
            self._cancel_pending_update()
            self._needs_redraw = False
            self.run_and_redraw()


    def _on_mode_changed(self, *_args):
        if self.mode_var is None:
            return

        selected_label = self.mode_var.get()
        selected_mode = self.mode_label_to_value.get(selected_label)

        if selected_mode is None:
            return

        self.mode = selected_mode

        if self.session_active:
            self._cancel_pending_update()
            self._needs_redraw = False
            self._render_panels()


    def _build_snapshots_from_truth(self):
        self.state_manager.build_snapshots_from_truth()

    def _build_controls_ui(self):
        # Clear existing UI (if resync)
        for widget in self.window.winfo_children():
            widget.destroy()

        controls = self.main_gui.simulation_controls
        show_wife = bool(controls.get("second_person_enabled", False))

        # ---- Main 2-column layout ----
        self.window.rowconfigure(0, weight=1)
        self.window.columnconfigure(0, weight=1)

        main = ttk.Frame(self.window)
        main.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        main.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2, minsize=360)

        # ---- Sliders (left) ----
        self.sliders_frame = ScenarioSlidersFrame(
            main,
            main_gui=self.main_gui,
            persons=self.session_state.person_snapshots,
            portfolio=self.session_state.portfolio_snapshots,
            retirement_snapshots=self.session_state.retirement_snapshots,
            show_enable_overrides_checkbox=False,      # Scenario: no checkbox
            show_wife=show_wife                        # hide wife when not enabled
        )
        self.sliders_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        self._wire_live_update_traces()

        # ---- Scenario controls (left, below assumptions) ----
        controls_frame = ttk.LabelFrame(main, text="Scenario Controls", padding=8)
        controls_frame.grid(row=1, column=0, sticky="ew", padx=(0, 12), pady=(10, 0))
        controls_frame.columnconfigure(0, weight=1)

        current_mode_label = self.mode_value_to_label.get(
            self.mode, self.mode_value_to_label[SCENARIO_MODE_SCENARIO_VIEW]
        )
        self.mode_var = tk.StringVar(value=current_mode_label)

        style = ttk.Style(self.window)
        combo_foreground = style.lookup("TLabel", "foreground")
        combo_background = style.lookup("TCombobox", "fieldbackground")

        style.configure("Scenario.TCombobox", foreground=combo_foreground, fieldbackground=combo_background)
        style.map("Scenario.TCombobox", foreground=[("readonly", combo_foreground)],
                  fieldbackground=[("readonly", combo_background)])

        self.mode_dropdown = ttk.Combobox(
            controls_frame, textvariable=self.mode_var, values=[label for label, _value in SCENARIO_MODE_OPTIONS],
            state="readonly", width=20, style="Scenario.TCombobox"
        )
        self.mode_dropdown.grid(row=1, column=0, sticky="w", pady=(2, 6))
        self.mode_dropdown.bind("<<ComboboxSelected>>", self._on_mode_dropdown_selected)

        current_plot_style_label = self.plot_style_value_to_label.get(
            self.plot_style, self.plot_style_value_to_label[SCENARIO_PLOT_STYLE_FILL]
        )
        self.plot_style_var = tk.StringVar(value=current_plot_style_label)

        ttk.Label(controls_frame, text="Plot Style").grid(row=2, column=0, sticky="w", pady=(2, 0))

        self.plot_style_dropdown = ttk.Combobox(
            controls_frame, textvariable=self.plot_style_var,
            values=[label for label, _value in SCENARIO_PLOT_STYLE_OPTIONS],
            state="readonly", width=20, style="Scenario.TCombobox"
        )
        self.plot_style_dropdown.grid(row=3, column=0, sticky="w", pady=(2, 6))
        self.plot_style_dropdown.bind("<<ComboboxSelected>>", self._on_plot_style_dropdown_selected)

        ttk.Label(controls_frame, text="Rebalancing").grid(row=4, column=0, sticky="w", pady=(2, 0))

        current_rebalancing = bool(self.session_state.retirement_snapshots.rebalance_every_year)
        current_rebalancing_label = next(
            label for label, value in SCENARIO_REBALANCING_OPTIONS if value == current_rebalancing
        )
        self.rebalancing_var = tk.StringVar(value=current_rebalancing_label)

        self.rebalancing_dropdown = ttk.Combobox(
            controls_frame, textvariable=self.rebalancing_var,
            values=[label for label, _value in SCENARIO_REBALANCING_OPTIONS],
            state="readonly", width=20, style="Scenario.TCombobox"
        )
        self.rebalancing_dropdown.grid(row=5, column=0, sticky="w", pady=(2, 6))
        self.rebalancing_dropdown.bind("<<ComboboxSelected>>", self._on_rebalancing_dropdown_selected)

        self.include_realestate_var = tk.BooleanVar(value=bool(controls.get("include_realestate", False)))
        self.include_realestate_cb = ttk.Checkbutton(
            controls_frame, text="Include Real Estate", variable=self.include_realestate_var,
            command=self.schedule_update
        )
        self.include_realestate_cb.grid(row=6, column=0, sticky="w")

        self.adjust_infl_delta_cb = ttk.Checkbutton(
            controls_frame, text="Real Returns (Inflation Adjusted)",
            variable=self.sliders_frame.calculate_real_dollars
        )
        self.adjust_infl_delta_cb.grid(row=7, column=0, sticky="w")

        button_frame = ttk.Frame(controls_frame)
        button_frame.grid(row=8, column=0, sticky="w", pady=(8, 0))

        ttk.Button(button_frame, text="Restore Layout", width=20, command=self._position_windows).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Button(button_frame, text="Reset Scenario", width=20, command=self.resync).grid(
            row=1, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Button(button_frame, text="Close Explorer", width=20, command=self._stop_session).grid(
            row=2, column=0, sticky="w"
        )
        
        # ---- Results (right) ----
        self.results_frame = ScenarioResultsFrame(main)
        self.results_frame.grid(row=0, column=1, rowspan=2, sticky="nsew")


    def _apply_slider_values_to_snapshots(self):
        if self.sliders_frame is None:
            return

        values = self.sliders_frame.get_values()
        self.state_manager.apply_control_values(values)


    def _compute_baseline_results(self):
        include_realestate = bool(self.main_gui.simulation_controls.get("include_realestate", False))
        self.state_manager.compute_baseline_results(include_realestate, self.plot_style)


    def _compute_scenario_results(self):
        include_realestate = self.include_realestate_var.get()
        return self.state_manager.compute_scenario_results(include_realestate, self.plot_style)


    def _render_panels(self):
        """
        Render both panels according to the current mode.
        """
        left_panel, right_panel = self._resolve_panels_for_mode()
        sync_axes = self.mode in (
            SCENARIO_MODE_INCOME_COMPARE, SCENARIO_MODE_CASHFLOW_COMPARE, SCENARIO_MODE_PORTFOLIO_COMPARE
        )

        annotations_enabled = False
        if self.sliders_frame is not None:
            annotations_enabled = bool(self.sliders_frame.enable_annotations.get())

        self.plot_manager.render_panels(
            left_panel, right_panel, self.session_state.baseline_results, self.session_state.scenario_results,
            self.mode, annotations_enabled, sync_axes=sync_axes
        )


    def _run_scenario_simulation(self):
        self._compute_scenario_results()
        if self.results_frame is not None:
            self.results_frame.update_results(self.state_manager.build_results_view_model())
        self._render_panels()


