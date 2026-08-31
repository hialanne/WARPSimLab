# gui_scenarioController.py

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt

SCENARIO_MODE_SCENARIO_VIEW = "scenario_view"
SCENARIO_MODE_CASHFLOW_COMPARE = "cashflow_compare"
SCENARIO_MODE_PORTFOLIO_COMPARE = "portfolio_compare"

SCENARIO_MODE_OPTIONS = [
    ("Scenario View", SCENARIO_MODE_SCENARIO_VIEW),
    ("Compare Cashflow", SCENARIO_MODE_CASHFLOW_COMPARE),
    ("Compare Portfolio", SCENARIO_MODE_PORTFOLIO_COMPARE),
]

from src.warpsimlab.gui.scenario.gui_scenarioSliders import ScenarioSlidersFrame
from src.warpsimlab.gui.scenario.gui_scenarioPlots import (
    ScenarioPlotManager, PLOT_FAMILY_CASHFLOW, PLOT_FAMILY_PORTFOLIO, RESULT_SOURCE_BASELINE, RESULT_SOURCE_SCENARIO
)

from src.warpsimlab.gui.gui_utils import set_tk_button_soft_disabled, noop
from src.warpsimlab.gui.scenario.gui_scenarioState import ScenarioStateManager

class ScenarioController:
    """
    Controls lifecycle of the Scenario Dashboard (Scenario mode).
    """

    def __init__(self, main_gui):
        self.main_gui = main_gui
        self.plot_manager = ScenarioPlotManager(self)
        self.state_manager = ScenarioStateManager(self)
        self.session_active = False
        self.window = None

        self.income_fig = None
        self.income_ax = None

        self.portfolio_fig = None
        self.portfolio_ax = None

        self.person_snapshots = None          # dict: "husband", optional "wife"
        self.portfolio_snapshots = None       # dict: "husband", optional "wife"
        self.retirement_snapshots = None      # RetirementSnapshots container
        self.sliders_frame = None             # RetirementSlidersFrame widget

        # Epic 2 caches
        self.baseline_results = None          # original/truth results; recomputed on start/resync
        self.scenario_results = None          # changed/slider results; recomputed on slider change

        self._pending_job_id = None
        self._debounce_ms = 150  # adjust if desired (200-400)

        self._is_redrawing = False
        self._needs_redraw = False

        self.mode = SCENARIO_MODE_SCENARIO_VIEW
        self.mode_var = None
        self.mode_label_to_value = {
            label: value for label, value in SCENARIO_MODE_OPTIONS
        }
        self.mode_value_to_label = {
            value: label for label, value in SCENARIO_MODE_OPTIONS
        }

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

        # Close plot figures if they exist
        for fig in [self.income_fig, self.portfolio_fig]:
            if fig is not None:
                try:
                    plt.close(fig)
                except Exception:
                    pass

        self.income_fig = None
        self.income_ax = None
        self.portfolio_fig = None
        self.portfolio_ax = None
        self.baseline_results = None
        self.scenario_results = None

        self.window = None
        self.session_active = False


    def _create_persistent_plots(self):
        self.plot_manager.create_persistent_plots()


    def _get_plot_window(self, figure):
        return self.plot_manager.get_plot_window(figure)


    def capture_current_layout(self):
        self.plot_manager.capture_current_layout()


    def _restore_saved_layout(self):
        return self.plot_manager.restore_saved_layout()


    def _position_windows(self):
        self.plot_manager.position_windows()


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


    def _panel_role_label(self, panel):
        return self.plot_manager.panel_role_label(panel)


    def _panel_window_title(self, panel):
        return self.plot_manager.panel_window_title(panel)


    def _apply_panel_window_title(self, fig, panel):
        self.plot_manager.apply_panel_window_title(fig, panel)


    def _draw_panel_role_label(self, ax, panel):
        self.plot_manager.draw_panel_role_label(ax, panel)


    def _display_sim_config(self, result, panel):
        return self.plot_manager.display_sim_config(result, panel)


    def _sync_compare_axes(self, left_panel, right_panel):
        self.plot_manager.sync_compare_axes(left_panel, right_panel)


    def _draw_panel(self, ax, fig, panel):
        self.plot_manager.draw_panel(ax, fig, panel)


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

        self._build_snapshots_from_truth()
        self._build_controls_ui()

        # Synchronize initialized slider values back into snapshots
        self._apply_slider_values_to_snapshots()

        # Compute baseline only after snapshots fully reflect the UI defaults
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
            if self.income_ax is None or self.portfolio_ax is None:
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
            self.sliders_frame.inflation_value,
            self.sliders_frame.fund_expense_value,
            self.sliders_frame.market_adjustment_percent,
            self.sliders_frame.stocks_percent,
            self.sliders_frame.bonds_percent,
            self.sliders_frame.cash_percent,          # changes when stocks/bonds adjust cash
            self.sliders_frame.enable_annotations,    # checkbox affects plots
            self.sliders_frame.adjust_hist_for_infl_delta, 
            self.sliders_frame.dynamic_value,
        ]

        # Wife retirement age is optional
        if getattr(self.sliders_frame, "tmp_ret_age_w", None) is not None:
            vars_to_trace.append(self.sliders_frame.tmp_ret_age_w)

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
        main.columnconfigure(0, weight=1)  # sliders expand
        main.columnconfigure(1, weight=0)  # controls fixed width

        # ---- Sliders (left) ----
        self.sliders_frame = ScenarioSlidersFrame(
            main,
            main_gui=self.main_gui,
            persons=self.person_snapshots,
            portfolio=self.portfolio_snapshots,
            retirement_snapshots=self.retirement_snapshots,
            show_enable_overrides_checkbox=False,      # Scenario: no checkbox
            allow_main_gui_override_flag=False,        # Scenario: never toggle main_gui flags
            show_wife=show_wife,                       # hide wife when not enabled
            baseline_persons={
                "husband": self.main_gui.husband,
                "wife": self.main_gui.wife if show_wife else None
            }
        )
        self.sliders_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        self._wire_live_update_traces()

        # ---- Controls stack (right) ----
        right_stack = ttk.Frame(main)
        right_stack.grid(row=0, column=1, sticky="ne")

        ttk.Label(right_stack, text="Mode").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )

        current_mode_label = self.mode_value_to_label.get(
            self.mode,
            self.mode_value_to_label[SCENARIO_MODE_SCENARIO_VIEW]
        )
        self.mode_var = tk.StringVar(value=current_mode_label)

        style = ttk.Style(self.window)

        combo_foreground = style.lookup("TLabel", "foreground")
        combo_background = style.lookup("TCombobox", "fieldbackground")

        style.configure(
            "Scenario.TCombobox",
            foreground=combo_foreground,
            fieldbackground=combo_background,
        )

        style.map(
            "Scenario.TCombobox",
            foreground=[
                ("readonly", combo_foreground),
            ],
            fieldbackground=[
                ("readonly", combo_background),
            ],
        )

        self.mode_dropdown = ttk.Combobox(
            right_stack,
            textvariable=self.mode_var,
            values=[label for label, _value in SCENARIO_MODE_OPTIONS],
            state="readonly",
            width=20,
            style="Scenario.TCombobox"
        )

        self.mode_dropdown.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.mode_dropdown.bind("<<ComboboxSelected>>", self._on_mode_dropdown_selected)

        self.annotate_cb = ttk.Checkbutton(
            right_stack,
            text="Annotate Plots",
            variable=self.sliders_frame.enable_annotations
        )
        self.annotate_cb.grid(row=2, column=0, sticky="e", pady=(0, 10))

        self.adjust_infl_delta_cb = ttk.Checkbutton(
            right_stack,
            text="Adjust returns\nfor local\ninflation change",
            variable=self.sliders_frame.adjust_hist_for_infl_delta
        )
        self.adjust_infl_delta_cb.grid(row=3, column=0, sticky="e", pady=(0, 10))

        ttk.Button(right_stack, text="Resync", command=self.resync).grid(
            row=4, column=0, sticky="ew"
        )
        ttk.Button(right_stack, text="Stop", command=self._stop_session).grid(
            row=5, column=0, sticky="ew", pady=(0, 8)
        )

        # Disable annotate checkbox when overrides are disabled (for non-scenario uses)
        try:
            if not bool(self.sliders_frame.enable_overrides.get()):
                self.annotate_cb.state(["disabled"])
        except Exception:
            pass


    def _apply_slider_values_to_snapshots(self):
        self.state_manager.apply_slider_values_to_snapshots()


    def _clone_result_inputs(self, persons, portfolios, retirement_snapshots):
        return self.state_manager.clone_result_inputs(persons, portfolios, retirement_snapshots)


    def _compute_results_from_inputs(self, persons, portfolios, retirement_snapshots):
        return self.state_manager.compute_results_from_inputs(persons, portfolios, retirement_snapshots)


    def _compute_baseline_results(self):
        self.state_manager.compute_baseline_results()


    def _compute_scenario_results(self):
        return self.state_manager.compute_scenario_results()

    def _render_panels(self):
        """
        Render both panels according to the current mode.
        """
        left_panel, right_panel = self._resolve_panels_for_mode()
        sync_axes = self.mode in (SCENARIO_MODE_CASHFLOW_COMPARE, SCENARIO_MODE_PORTFOLIO_COMPARE)
        self.plot_manager.render_panels(left_panel, right_panel, sync_axes=sync_axes)


    def _run_scenario_simulation(self):
        self._compute_scenario_results()
        #self._debug_compare_baseline_vs_scenario("after scenario recompute")
        self._render_panels()



