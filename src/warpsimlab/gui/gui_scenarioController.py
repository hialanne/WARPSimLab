# gui_scenarioController.py

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import copy

SCENARIO_MODE_SCENARIO_VIEW = "scenario_view"
SCENARIO_MODE_CASHFLOW_COMPARE = "cashflow_compare"
SCENARIO_MODE_PORTFOLIO_COMPARE = "portfolio_compare"

SCENARIO_MODE_OPTIONS = [
    ("Scenario View", SCENARIO_MODE_SCENARIO_VIEW),
    ("Compare Cashflow", SCENARIO_MODE_CASHFLOW_COMPARE),
    ("Compare Portfolio", SCENARIO_MODE_PORTFOLIO_COMPARE),
]

PLOT_FAMILY_CASHFLOW = "cashflow"
PLOT_FAMILY_PORTFOLIO = "portfolio"

RESULT_SOURCE_BASELINE = "baseline"
RESULT_SOURCE_SCENARIO = "scenario"

from src.warpsimlab.plots.plotYearlyIncome import draw_yearly_income
from src.warpsimlab.plots.plotPortfolioProjection import draw_portfolio_projection

from src.warpsimlab.gui.gui_scenarioSliders import ScenarioSlidersFrame
from src.warpsimlab.gui.gui_scenarioSnapshots import ScenarioSnapshots

from src.warpsimlab.sim.simulation import run_pipeline
from src.warpsimlab.gui.gui_utils import set_tk_button_soft_disabled, noop

from src.warpsimlab.gui.gui_annotations import build_scenario_explorer_annotations


class ScenarioController:
    """
    Controls lifecycle of the Scenario Dashboard (Scenario mode).
    """

    def __init__(self, main_gui):
        self.main_gui = main_gui
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
        self.window.protocol("WM_DELETE_WINDOW", self._stop_session)

        # Create persistent plot windows FIRST (axes must exist before any run)
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
        """
        Create two persistent matplotlib figures and store references.
        """

        # Income figure
        self.income_fig, self.income_ax = plt.subplots(figsize=(8, 5))
        self.income_fig.canvas.manager.set_window_title("Scenario Explorer")

        # Portfolio figure
        self.portfolio_fig, self.portfolio_ax = plt.subplots(figsize=(8, 5))
        self.portfolio_fig.canvas.manager.set_window_title("Scenario Explorer")

        # Connect close handlers
        self.income_fig.canvas.mpl_connect("close_event", lambda event: self._stop_session())
        self.portfolio_fig.canvas.mpl_connect("close_event", lambda event: self._stop_session())

        # Position windows
        self._position_windows()

        try:
            plt.show(block=False)
        except Exception:
            pass


    def _position_windows(self):
        """
        Position income and portfolio windows side-by-side,
        and controls window below.
        """
        try:
            width = 850
            height = 600
            top_y = 20

            left_x = 0
            right_x = left_x + width + 0

            self.income_fig.canvas.manager.window.geometry(
                f"{width}x{height}+{left_x}+{top_y}"
            )

            self.portfolio_fig.canvas.manager.window.geometry(
                f"{width}x{height}+{right_x}+{top_y}"
            )

            if self.window is not None:
                control_w = 1060
                control_h = 280
                control_y = top_y + height + 40

                # Total width occupied by both plots
                total_plots_width = width * 2

                # Center control window under both plots
                control_x = left_x + (total_plots_width - control_w) // 2

                self.window.geometry(f"{control_w}x{control_h}+{control_x}+{control_y}")

        except Exception:
            pass


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
        """
        Human-readable label shown inside the plot, centered just below the title.
        """
        if panel["result_source"] == RESULT_SOURCE_BASELINE:
            return "Original"
        elif panel["result_source"] == RESULT_SOURCE_SCENARIO:
            return "Changed" if self.mode != SCENARIO_MODE_SCENARIO_VIEW else "Scenario"
        return "Scenario"


    def _panel_window_title(self, panel):
        """
        Human-readable figure window title for the current panel.
        """
        role = self._panel_role_label(panel)

        if panel["plot_family"] == PLOT_FAMILY_CASHFLOW:
            family = "Cashflow"
        else:
            family = "Portfolio"

        return f"{role} {family}"


    def _apply_panel_window_title(self, fig, panel):
        try:
            manager = getattr(fig.canvas, "manager", None)
            if manager is not None:
                manager.set_window_title(self._panel_window_title(panel))
        except Exception:
            pass


    def _draw_panel_role_label(self, ax, panel):
        """
        Draw a centered role label inside the plot area, just below the title.
        """
        label = self._panel_role_label(panel)

        ax.text(
            0.5,
            0.985,
            label,
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=10,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.20", facecolor="white", edgecolor="none", alpha=0.75),
            zorder=20
        )


    def _display_sim_config(self, result, panel):
        """
        Return a display-only sim_config copy for plot rendering tweaks.

        Important:
        - Do NOT deepcopy Simulation because it contains tkinter state (root),
          which is not deepcopy/pickle safe.
        - A shallow copy is sufficient here because we only override a simple
          display flag for the current render pass.
        """
        sim_config = copy.copy(result["sim_config"])

        annotate_enabled = False
        if self.sliders_frame is not None and hasattr(self.sliders_frame, "enable_annotations"):
            try:
                annotate_enabled = bool(self.sliders_frame.enable_annotations.get())
            except Exception:
                annotate_enabled = False

        sim_config.use_snapshot_annotations = annotate_enabled

        if panel["plot_family"] == PLOT_FAMILY_CASHFLOW:
            sim_config.sim_type = "cashflow_sim"

        return sim_config


    def _sync_compare_axes(self, left_panel, right_panel):
        """
        In compare modes, keep x/y scales identical across both windows.
        Scenario View is exempt by design.
        """
        if left_panel["plot_family"] != right_panel["plot_family"]:
            return

        left_ax = self.income_ax
        right_ax = self.portfolio_ax

        left_xlim = left_ax.get_xlim()
        right_xlim = right_ax.get_xlim()
        left_ylim = left_ax.get_ylim()
        right_ylim = right_ax.get_ylim()

        shared_xlim = (
            min(left_xlim[0], right_xlim[0]),
            max(left_xlim[1], right_xlim[1]),
        )
        shared_ylim = (
            min(left_ylim[0], right_ylim[0]),
            max(left_ylim[1], right_ylim[1]),
        )

        left_ax.set_xlim(shared_xlim)
        right_ax.set_xlim(shared_xlim)
        left_ax.set_ylim(shared_ylim)
        right_ax.set_ylim(shared_ylim)

        self.income_fig.canvas.draw_idle()
        self.portfolio_fig.canvas.draw_idle()


    def _draw_panel(self, ax, fig, panel):
        """
        Draw a panel based on plot family and result source.
        """

        if panel["result_source"] == RESULT_SOURCE_BASELINE:
            result = self.baseline_results
        else:
            result = self.scenario_results

        if result is None:
            return

        p = result["p"]
        sim_config = self._display_sim_config(result, panel)
        husband = result["husband"]
        wife = result["wife"]

        ax.clear()

        if panel["plot_family"] == PLOT_FAMILY_CASHFLOW:

            breakdown = dict(p["breakdown_by_class"])

            income_keys = [
                "work",
                "pension",
                "annuity",
                "ss",
                "special_income",
            ]

            breakdown["income"] = sum(
                breakdown[key]
                for key in income_keys
            )

            cashflow_keys = [
                "income",
                "rmd",
                "withdrawal",
                "cash_interest",
                "bond_interest",
                "qualified_dividends",
            ]

            cashflow_total = sum(
                breakdown[key]
                for key in cashflow_keys
            )

            draw_yearly_income(
                ax,
                p["years"],
                p["net_profit"],
                cashflow_total,
                breakdown,
                p["taxes"],
                p["expense_amt"],
                husband,
                wife,
                sim_config
            )
        elif panel["plot_family"] == PLOT_FAMILY_PORTFOLIO:
            draw_portfolio_projection(
                ax,
                p["years_list"],
                p["portfolio_plot_data"],
                sim_config=sim_config,
                annotate_plots=sim_config.annotate_plots,
                husband=husband,
                wife=wife
            )

        self._draw_panel_role_label(ax, panel)
        self._apply_panel_window_title(fig, panel)

        fig.canvas.draw_idle()


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
        controls = self.main_gui.simulation_controls

        # Persons
        self.person_snapshots = {"husband": copy.deepcopy(self.main_gui.husband)}
        if controls.get("enable_second_person", False):
            self.person_snapshots["wife"] = copy.deepcopy(self.main_gui.wife)

        # Portfolios
        self.portfolio_snapshots = {"husband": copy.deepcopy(self.main_gui.husband_portfolio)}
        if controls.get("enable_second_person", False):
            self.portfolio_snapshots["wife"] = copy.deepcopy(self.main_gui.wife_portfolio)

        # Scenario assumptions snapshots
        self.retirement_snapshots = ScenarioSnapshots()
        self.retirement_snapshots.inflation = self.main_gui.inflation
        self.retirement_snapshots.fund_expense = self.main_gui.simulation_settings.get("fund_expense")
        self.retirement_snapshots.historical_data_multiplier = 100.0  # baseline (percent)


    def _build_controls_ui(self):
        # Clear existing UI (if resync)
        for widget in self.window.winfo_children():
            widget.destroy()

        controls = self.main_gui.simulation_controls
        show_wife = bool(controls.get("enable_second_person", False))

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

        self.mode_dropdown = ttk.Combobox(
            right_stack,
            textvariable=self.mode_var,
            values=[label for label, _value in SCENARIO_MODE_OPTIONS],
            state="readonly",
            width=20
        )
        self.mode_dropdown.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.mode_dropdown.bind("<<ComboboxSelected>>", self._on_mode_changed)

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
        if self.sliders_frame is None:
            return

        controls = self.main_gui.simulation_controls

        # Read slider values -> scenario retirement_snapshots
        inflation = self.sliders_frame.inflation_value.get()
        fund_expense = self.sliders_frame.fund_expense_value.get()
        historical_data_multiplier = self.sliders_frame.market_adjustment_percent.get()

        stocks = self.sliders_frame.stocks_percent.get()
        bonds = self.sliders_frame.bonds_percent.get()
        cash = self.sliders_frame.cash_percent.get()

        self.retirement_snapshots.inflation = inflation
        self.retirement_snapshots.adjust_hist_for_infl_delta = (
            self.sliders_frame.adjust_hist_for_infl_delta.get()
        )

        # delta_inflation is in percent-points
        self.retirement_snapshots.delta_inflation = (
            float(self.retirement_snapshots.inflation) - float(self.main_gui.inflation)
        )
        self.retirement_snapshots.fund_expense = fund_expense
        self.retirement_snapshots.historical_data_multiplier = historical_data_multiplier

        self.retirement_snapshots.custom_stock_percent = stocks
        self.retirement_snapshots.custom_bonds_percent = bonds
        self.retirement_snapshots.custom_cash_percent = cash

        # Update person snapshot retirement ages (and related fields)
        husband_snapshot = self.person_snapshots.get("husband")
        tmp_ret_age_h = self.sliders_frame.tmp_ret_age_h.get()
        husband_snapshot.retire_age = tmp_ret_age_h
        husband_snapshot.ss_age = tmp_ret_age_h

        wife_snapshot = None
        tmp_ret_age_w = None
        if controls.get("enable_second_person", False):
            wife_snapshot = self.person_snapshots.get("wife")
            if wife_snapshot is not None and self.sliders_frame.tmp_ret_age_w is not None:
                tmp_ret_age_w = self.sliders_frame.tmp_ret_age_w.get()
                wife_snapshot.retire_age = tmp_ret_age_w
                wife_snapshot.ss_age = tmp_ret_age_w

        # Snapshot annotations
        self.retirement_snapshots.use_snapshot_annotations = self.sliders_frame.enable_annotations.get()

        baseline_stocks, baseline_bonds, baseline_cash = self.sliders_frame._compute_initial_portfolio_percents()

        self.retirement_snapshots.annotation_strings = build_scenario_explorer_annotations(
            main_gui=self.main_gui,
            tmp_ret_age_h=tmp_ret_age_h,
            tmp_ret_age_w=tmp_ret_age_w,
            inflation=inflation,
            fund_expense=fund_expense,
            historical_data_multiplier=historical_data_multiplier,
            stocks=stocks,
            bonds=bonds,
            cash=cash,
            baseline_stocks=baseline_stocks,
            baseline_bonds=baseline_bonds,
            baseline_cash=baseline_cash,
            wife_snapshot=wife_snapshot,
            scenario_expense_multiplier=self.retirement_snapshots.scenario_expense_multiplier,
            scenario_withdraw_pct=self.retirement_snapshots.scenario_withdraw_pct,
        )


    def _clone_result_inputs(self, persons, portfolios, retirement_snapshots):
        """
        Return fully detached copies of all simulation inputs so cached baseline
        and scenario results cannot be mutated later by sliders or redraw logic.
        """
        persons_copy = copy.deepcopy(persons)
        portfolios_copy = copy.deepcopy(portfolios)
        retirement_copy = copy.deepcopy(retirement_snapshots)
        return persons_copy, portfolios_copy, retirement_copy


    def _compute_results_from_inputs(self, persons, portfolios, retirement_snapshots):
        """
        Compute one result bundle from the supplied snapshots and return a cacheable dict.
        """
        persons_copy, portfolios_copy, retirement_copy = self._clone_result_inputs(
            persons, portfolios, retirement_snapshots
        )

        sim_config = self.main_gui.build_simulation_from_gui(
            sim_type="portfolio_sim",
            use_snapshots=True,
            retirement_snapshots=retirement_copy
        )

        husband = persons_copy["husband"]
        wife = persons_copy.get("wife") if sim_config.second_person_enabled else None

        husband_portfolio = portfolios_copy["husband"]
        wife_portfolio = portfolios_copy.get("wife") if wife else None

        expenses = self.main_gui.expensesDict

        p = run_pipeline(
            husband_portfolio, wife_portfolio,
            husband, wife,
            expenses, sim_config
        )

        return {
            "p": p,
            "sim_config": sim_config,
            "husband": husband,
            "wife": wife,
        }


    def _compute_baseline_results(self):
        """
        Baseline/original results are computed from GUI truth once when Scenario
        Explorer starts and whenever Resync is pressed.
        """
        baseline_persons = copy.deepcopy(self.person_snapshots)
        baseline_portfolios = copy.deepcopy(self.portfolio_snapshots)
        baseline_retirement = copy.deepcopy(self.retirement_snapshots)

        self.baseline_results = self._compute_results_from_inputs(
            baseline_persons,
            baseline_portfolios,
            baseline_retirement
        )


    def _compute_scenario_results(self):
        self.scenario_results = self._compute_results_from_inputs(
            self.person_snapshots,
            self.portfolio_snapshots,
            self.retirement_snapshots
        )
        return self.scenario_results


    def _render_panels(self):
        """
        Render both panels according to the current mode.
        """

        left_panel, right_panel = self._resolve_panels_for_mode()

        self._draw_panel(self.income_ax, self.income_fig, left_panel)
        self._draw_panel(self.portfolio_ax, self.portfolio_fig, right_panel)

        if self.mode in (
            SCENARIO_MODE_CASHFLOW_COMPARE,
            SCENARIO_MODE_PORTFOLIO_COMPARE,
        ):
            self._sync_compare_axes(left_panel, right_panel)


    def _run_scenario_simulation(self):
        self._compute_scenario_results()
        #self._debug_compare_baseline_vs_scenario("after scenario recompute")
        self._render_panels()



