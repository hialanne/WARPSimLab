# gui_scenarioPlots.py

# gui_scenarioPlots.py

import tkinter as tk
import matplotlib.pyplot as plt
import copy

from src.warpsimlab.plots.plotYearlyIncome import draw_yearly_income
from src.warpsimlab.plots.plotPortfolioProjection import draw_portfolio_projection
from src.warpsimlab.gui.gui_settings import SCENARIO_LAYOUT_REMEMBER, geometry_is_visible, save_display_settings


PLOT_FAMILY_CASHFLOW = "cashflow"
PLOT_FAMILY_PORTFOLIO = "portfolio"

RESULT_SOURCE_BASELINE = "baseline"
RESULT_SOURCE_SCENARIO = "scenario"

class ScenarioPlotManager:
    """
    Owns Scenario Explorer Matplotlib figure creation and plot-window layout.
    """

    def __init__(self, controller):
        self.controller = controller
        self.main_gui = controller.main_gui

    def create_persistent_plots(self):
        """
        Create two persistent Matplotlib figures and store references on the controller.
        """
        c = self.controller

        c.income_fig, c.income_ax = plt.subplots(figsize=(8, 5))
        c.income_fig.canvas.manager.set_window_title("Scenario Explorer")

        c.portfolio_fig, c.portfolio_ax = plt.subplots(figsize=(8, 5))
        c.portfolio_fig.canvas.manager.set_window_title("Scenario Explorer")

        c.income_fig.canvas.mpl_connect("close_event", lambda event: c._stop_session())
        c.portfolio_fig.canvas.mpl_connect("close_event", lambda event: c._stop_session())

        if not self.restore_saved_layout():
            self.position_windows()

        try:
            plt.show(block=False)
        except Exception:
            pass

    def get_plot_window(self, figure):
        """
        Return the native Tk window owned by a Matplotlib figure.
        """
        if figure is None:
            return None

        canvas = getattr(figure, "canvas", None)
        manager = getattr(canvas, "manager", None)

        if manager is None:
            return None

        return getattr(manager, "window", None)

    def capture_current_layout(self):
        """
        Save the three Scenario Explorer window geometries when enabled.
        """
        c = self.controller
        scenario_settings = self.main_gui.display_settings["scenario_explorer"]

        if scenario_settings.get("layout_mode") != SCENARIO_LAYOUT_REMEMBER:
            return

        income_window = self.get_plot_window(c.income_fig)
        portfolio_window = self.get_plot_window(c.portfolio_fig)

        if income_window is None or portfolio_window is None or c.window is None:
            return

        try:
            income_window.update_idletasks()
            portfolio_window.update_idletasks()
            c.window.update_idletasks()

            scenario_settings["layout"] = {
                "income_plot": income_window.winfo_geometry(),
                "portfolio_plot": portfolio_window.winfo_geometry(),
                "dashboard": c.window.winfo_geometry(),
            }
        except tk.TclError:
            return

        save_display_settings(self.main_gui.display_settings)

    def restore_saved_layout(self):
        """
        Restore the three saved Scenario Explorer geometries.

        Returns True only when all three saved windows are valid and visible.
        """
        c = self.controller
        scenario_settings = self.main_gui.display_settings["scenario_explorer"]

        if scenario_settings.get("layout_mode") != SCENARIO_LAYOUT_REMEMBER:
            return False

        layout = scenario_settings.get("layout")
        if not isinstance(layout, dict):
            return False

        income_geometry = layout.get("income_plot")
        portfolio_geometry = layout.get("portfolio_plot")
        dashboard_geometry = layout.get("dashboard")

        screen_width = self.main_gui.root.winfo_screenwidth()
        screen_height = self.main_gui.root.winfo_screenheight()
        geometries = (income_geometry, portfolio_geometry, dashboard_geometry)

        if not all(geometry_is_visible(geometry, screen_width, screen_height) for geometry in geometries):
            scenario_settings["layout"] = None
            save_display_settings(self.main_gui.display_settings)
            return False

        income_window = self.get_plot_window(c.income_fig)
        portfolio_window = self.get_plot_window(c.portfolio_fig)

        if income_window is None or portfolio_window is None or c.window is None:
            return False

        try:
            income_window.geometry(income_geometry)
            portfolio_window.geometry(portfolio_geometry)
            c.window.geometry(dashboard_geometry)
        except tk.TclError:
            return False

        return True

    def position_windows(self):
        """
        Position the two plot windows side-by-side and center the Scenario Dashboard below them.
        """
        c = self.controller

        try:
            root = self.main_gui.root
            root.update_idletasks()

            root_center_x = root.winfo_rootx() + root.winfo_width() // 2
            root_center_y = root.winfo_rooty() + root.winfo_height() // 2
            work_left, work_top, work_right, work_bottom = self.main_gui._get_monitor_work_area(
                root_center_x, root_center_y
            )

            screen_width = work_right - work_left
            screen_height = work_bottom - work_top

            development_screen_width = 1707
            development_screen_height = 1067

            width_scale = screen_width / development_screen_width
            height_scale = screen_height / development_screen_height
            scale = min(width_scale, height_scale)

            plot_width = int(850 * scale)
            plot_height = int(600 * scale)
            top_y = work_top + int(20 * scale)

            total_plots_width = plot_width * 2
            left_x = work_left + (screen_width - total_plots_width) // 2
            right_x = left_x + plot_width

            c.income_fig.canvas.manager.window.geometry(f"{plot_width}x{plot_height}+{left_x}+{top_y}")
            c.portfolio_fig.canvas.manager.window.geometry(f"{plot_width}x{plot_height}+{right_x}+{top_y}")

            if c.window is not None:
                control_width = int(1060 * scale)
                control_height = int(280 * scale)
                control_gap = int(40 * scale)

                control_y = top_y + plot_height + control_gap
                control_x = left_x + (total_plots_width - control_width) // 2

                c.window.geometry(f"{control_width}x{control_height}+{control_x}+{control_y}")

        except Exception:
            pass


    def panel_role_label(self, panel):
        """
        Human-readable label for the current panel.
        """
        c = self.controller

        if panel["result_source"] == RESULT_SOURCE_BASELINE:
            return "Original"
        if panel["result_source"] == RESULT_SOURCE_SCENARIO:
            return "Changed" if c.mode != "scenario_view" else "Scenario"

        return "Scenario"


    def panel_window_title(self, panel):
        """
        Human-readable figure window title for the current panel.
        """
        role = self.panel_role_label(panel)
        family = "Cashflow" if panel["plot_family"] == PLOT_FAMILY_CASHFLOW else "Portfolio"
        return f"{role} {family}"


    def apply_panel_window_title(self, fig, panel):
        try:
            manager = getattr(fig.canvas, "manager", None)
            if manager is not None:
                manager.set_window_title(self.panel_window_title(panel))
        except Exception:
            pass


    def draw_panel_role_label(self, ax, panel):
        """
        Draw a centered role label inside the plot area, just below the title.
        """
        label = self.panel_role_label(panel)

        ax.text(0.5, 0.985, label, transform=ax.transAxes, ha="center", va="top", fontsize=10, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.20", facecolor="white", edgecolor="none", alpha=0.75), zorder=20)


    def display_sim_config(self, result, panel):
        """
        Return a display-only sim_config copy for plot rendering tweaks.
        """
        c = self.controller
        sim_config = copy.copy(result["sim_config"])

        annotate_enabled = False
        if c.sliders_frame is not None and hasattr(c.sliders_frame, "enable_annotations"):
            try:
                annotate_enabled = bool(c.sliders_frame.enable_annotations.get())
            except Exception:
                annotate_enabled = False

        sim_config.use_snapshot_annotations = annotate_enabled

        if panel["plot_family"] == PLOT_FAMILY_CASHFLOW:
            sim_config.sim_type = "cashflow_sim"

        return sim_config


    def sync_compare_axes(self, left_panel, right_panel):
        """
        In compare modes, keep x/y scales identical across both windows.
        """
        c = self.controller

        if left_panel["plot_family"] != right_panel["plot_family"]:
            return

        left_xlim = c.income_ax.get_xlim()
        right_xlim = c.portfolio_ax.get_xlim()
        left_ylim = c.income_ax.get_ylim()
        right_ylim = c.portfolio_ax.get_ylim()

        shared_xlim = (min(left_xlim[0], right_xlim[0]), max(left_xlim[1], right_xlim[1]))
        shared_ylim = (min(left_ylim[0], right_ylim[0]), max(left_ylim[1], right_ylim[1]))

        c.income_ax.set_xlim(shared_xlim)
        c.portfolio_ax.set_xlim(shared_xlim)
        c.income_ax.set_ylim(shared_ylim)
        c.portfolio_ax.set_ylim(shared_ylim)

        c.income_fig.canvas.draw_idle()
        c.portfolio_fig.canvas.draw_idle()


    def draw_panel(self, ax, fig, panel):
        """
        Draw a panel based on plot family and result source.
        """
        c = self.controller
        result = c.baseline_results if panel["result_source"] == RESULT_SOURCE_BASELINE else c.scenario_results

        if result is None:
            return

        p = result["p"]
        sim_config = self.display_sim_config(result, panel)
        husband = result["husband"]
        wife = result["wife"]

        ax.clear()

        if panel["plot_family"] == PLOT_FAMILY_CASHFLOW:
            breakdown = dict(p["breakdown_by_class"])

            income_keys = ["work", "pension", "annuity", "ss", "special_income"]
            breakdown["income"] = sum(breakdown[key] for key in income_keys)

            cashflow_keys = [
                "income", "rmd", "withdrawal", "cash_interest", "bond_interest", "qualified_equity_distributions",
            ]
            cashflow_total = sum(breakdown[key] for key in cashflow_keys)

            draw_yearly_income(ax, p["years"], p["net_profit"], cashflow_total, breakdown, p["taxes"], p["expense_amt"],
                               husband, wife, sim_config)

        elif panel["plot_family"] == PLOT_FAMILY_PORTFOLIO:
            draw_portfolio_projection(ax, p["years_list"], p["portfolio_plot_data"], sim_config=sim_config,
                                      annotate_plots=sim_config.annotate_plots, husband=husband, wife=wife)

        role = self.panel_role_label(panel)
        current_title = ax.get_title()
        ax.set_title(f"{role} {current_title}" if current_title else role)

        self.apply_panel_window_title(fig, panel)
        fig.canvas.draw_idle()


    def render_panels(self, left_panel, right_panel, sync_axes=False):
        """
        Render both Scenario Explorer panels.
        """
        c = self.controller

        self.draw_panel(c.income_ax, c.income_fig, left_panel)
        self.draw_panel(c.portfolio_ax, c.portfolio_fig, right_panel)

        if sync_axes:
            self.sync_compare_axes(left_panel, right_panel)