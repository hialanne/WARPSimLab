# gui_scenarioPlots.py

# gui_scenarioPlots.py

import tkinter as tk
import matplotlib.pyplot as plt
import copy

from src.warpsimlab.plots.plotYearlyIncome import draw_yearly_income
from src.warpsimlab.plots.plotPortfolioProjection import draw_portfolio_projection
from src.warpsimlab.gui.gui_settings import SCENARIO_LAYOUT_REMEMBER, geometry_is_visible, save_display_settings


PLOT_FAMILY_INCOME = "income"
PLOT_FAMILY_CASHFLOW = "cashflow"
PLOT_FAMILY_PORTFOLIO = "portfolio"

RESULT_SOURCE_BASELINE = "baseline"
RESULT_SOURCE_SCENARIO = "scenario"

class ScenarioPlotManager:
    """
    Owns Scenario Explorer Matplotlib figure creation and plot-window layout.
    """

    def __init__(self, main_gui, close_callback):
        self.main_gui = main_gui
        self.close_callback = close_callback
        self.income_fig = None
        self.income_ax = None
        self.portfolio_fig = None
        self.portfolio_ax = None


    def create_persistent_plots(self, dashboard_window):
        """
        Create the two persistent Scenario Explorer Matplotlib figures.
        """
        self.income_fig, self.income_ax = plt.subplots(figsize=(8, 5))
        self.income_fig.canvas.manager.set_window_title("Scenario Explorer")

        self.portfolio_fig, self.portfolio_ax = plt.subplots(figsize=(8, 5))
        self.portfolio_fig.canvas.manager.set_window_title("Scenario Explorer")

        self.income_fig.canvas.mpl_connect("close_event", lambda event: self.close_callback())
        self.portfolio_fig.canvas.mpl_connect("close_event", lambda event: self.close_callback())

        if not self.restore_saved_layout(dashboard_window):
            self.position_windows(dashboard_window)

        try:
            plt.show(block=False)
        except Exception:
            pass


    def has_plots(self):
        return self.income_ax is not None and self.portfolio_ax is not None


    def close_plots(self):
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


    def capture_current_layout(self, dashboard_window):
        """
        Save the three Scenario Explorer window geometries when enabled.
        """
        scenario_settings = self.main_gui.display_settings["scenario_explorer"]

        if scenario_settings.get("layout_mode") != SCENARIO_LAYOUT_REMEMBER:
            return

        income_window = self.get_plot_window(self.income_fig)
        portfolio_window = self.get_plot_window(self.portfolio_fig)

        if income_window is None or portfolio_window is None or dashboard_window is None:
            return

        try:
            income_window.update_idletasks()
            portfolio_window.update_idletasks()
            dashboard_window.update_idletasks()

            scenario_settings["layout"] = {
                "income_plot": income_window.winfo_geometry(),
                "portfolio_plot": portfolio_window.winfo_geometry(),
                "dashboard": dashboard_window.winfo_geometry(),
            }
        except tk.TclError:
            return

        save_display_settings(self.main_gui.display_settings)


    def restore_saved_layout(self, dashboard_window):
        """
        Restore the three saved Scenario Explorer geometries.

        Returns True only when all three saved windows are valid and visible.
        """
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

        income_window = self.get_plot_window(self.income_fig)
        portfolio_window = self.get_plot_window(self.portfolio_fig)

        if income_window is None or portfolio_window is None or dashboard_window is None:
            return False

        try:
            income_window.geometry(income_geometry)
            portfolio_window.geometry(portfolio_geometry)
            dashboard_window.geometry(dashboard_geometry)
        except tk.TclError:
            return False

        return True


    def position_windows(self, dashboard_window):
        """
        Position the Scenario Dashboard on the left, with Cash Flow above Portfolio on the right.
        """

        try:
            root = self.main_gui.root
            root.update_idletasks()

            root_center_x = root.winfo_rootx() + root.winfo_width() // 2
            root_center_y = root.winfo_rooty() + root.winfo_height() // 2
            work_left, work_top, work_right, work_bottom = self.main_gui._get_monitor_work_area(root_center_x, root_center_y)

            screen_width = work_right - work_left
            screen_height = work_bottom - work_top

            development_screen_width = 1707
            development_screen_height = 1067
            scale = min(screen_width / development_screen_width, screen_height / development_screen_height)

            gap = max(10, int(20 * scale))
            usable_width = screen_width - gap * 3
            usable_height = screen_height - gap * 3

            dashboard_width = int(usable_width * 0.43)
            plot_width = usable_width - dashboard_width
            plot_height = usable_height // 2
            dashboard_height = plot_height * 2 + gap

            dashboard_x = work_left + gap
            plot_x = dashboard_x + dashboard_width + gap
            top_y = work_top + gap
            portfolio_y = top_y + plot_height + gap

            if dashboard_window is not None:
                dashboard_window.geometry(f"{dashboard_width}x{dashboard_height}+{dashboard_x}+{top_y}")

            self.income_fig.canvas.manager.window.geometry(f"{plot_width}x{plot_height}+{plot_x}+{top_y}")
            self.portfolio_fig.canvas.manager.window.geometry(f"{plot_width}x{plot_height}+{plot_x}+{portfolio_y}")

        except Exception:
            pass


    def panel_role_label(self, panel, mode):
        """
        Human-readable label for the current panel.
        """
        if panel["result_source"] == RESULT_SOURCE_BASELINE:
            return "Original"

        if panel["result_source"] == RESULT_SOURCE_SCENARIO:
            if mode != "scenario_view":
                return "Changed"
            return "Scenario"

        return "Scenario"


    def panel_window_title(self, panel, mode):
        """
        Human-readable figure window title for the current panel.
        """
        role = self.panel_role_label(panel, mode)

        if panel["plot_family"] == PLOT_FAMILY_INCOME:
            family = "Income"
        elif panel["plot_family"] == PLOT_FAMILY_CASHFLOW:
            family = "Cash Flow"
        else:
            family = "Portfolio"

        return f"{role} {family}"


    def apply_panel_window_title(self, fig, panel, mode):
        try:
            manager = getattr(fig.canvas, "manager", None)
            if manager is not None:
                manager.set_window_title(self.panel_window_title(panel, mode))
        except Exception:
            pass


    def display_sim_config(self, result, panel, annotations_enabled):
        """
        Return a display-only sim_config copy for plot rendering tweaks.
        """
        sim_config = copy.copy(result["sim_config"])
        sim_config.use_snapshot_annotations = bool(annotations_enabled)
        sim_config.scenario_explorer_annotations = []

        if panel["plot_family"] == PLOT_FAMILY_INCOME:
            sim_config.sim_type = "income_sim"
        elif panel["plot_family"] == PLOT_FAMILY_CASHFLOW:
            sim_config.sim_type = "cashflow_sim"

        return sim_config


    def sync_compare_axes(self, left_panel, right_panel):
        """
        In compare modes, keep x/y scales identical across both windows.
        """
        if left_panel["plot_family"] != right_panel["plot_family"]:
            return

        left_xlim = self.income_ax.get_xlim()
        right_xlim = self.portfolio_ax.get_xlim()
        left_ylim = self.income_ax.get_ylim()
        right_ylim = self.portfolio_ax.get_ylim()

        shared_xlim = (min(left_xlim[0], right_xlim[0]), max(left_xlim[1], right_xlim[1]))
        shared_ylim = (min(left_ylim[0], right_ylim[0]), max(left_ylim[1], right_ylim[1]))

        self.income_ax.set_xlim(shared_xlim)
        self.portfolio_ax.set_xlim(shared_xlim)
        self.income_ax.set_ylim(shared_ylim)
        self.portfolio_ax.set_ylim(shared_ylim)

        self.income_fig.canvas.draw_idle()
        self.portfolio_fig.canvas.draw_idle()


    def draw_panel(self, ax, fig, panel, baseline_results, scenario_results, mode, annotations_enabled):
        """
        Draw a panel based on plot family and result source.
        """
        if panel["result_source"] == RESULT_SOURCE_BASELINE:
            result = baseline_results
        else:
            result = scenario_results

        if result is None:
            return

        p = result["p"]
        sim_config = self.display_sim_config(result, panel, annotations_enabled)
        husband = result["husband"]
        wife = result["wife"]

        ax.clear()

        if panel["plot_family"] == PLOT_FAMILY_INCOME:
            breakdown = dict(p["breakdown_by_class"])
            income_keys = ["work", "pension", "annuity", "ss", "special_income"]
            income_total = sum(breakdown[key] for key in income_keys)

            draw_yearly_income(ax, p["years"], p["net_profit"], income_total, breakdown, p["taxes"], p["expense_amt"],
                               husband, wife, sim_config)

        elif panel["plot_family"] == PLOT_FAMILY_CASHFLOW:
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

        role = self.panel_role_label(panel, mode)
        current_title = ax.get_title()
        if current_title:
            ax.set_title(f"{role} {current_title}")
        else:
            ax.set_title(role)

        self.apply_panel_window_title(fig, panel, mode)
        fig.canvas.draw_idle()


    def render_panels(
        self, left_panel, right_panel, baseline_results, scenario_results, mode, annotations_enabled, sync_axes=False
    ):
        """
        Render both Scenario Explorer panels.
        """
        self.draw_panel(
            self.income_ax, self.income_fig, left_panel, baseline_results, scenario_results, mode, annotations_enabled
        )
        self.draw_panel(
            self.portfolio_ax, self.portfolio_fig, right_panel, baseline_results, scenario_results, mode,
            annotations_enabled
        )

        if sync_axes:
            self.sync_compare_axes(left_panel, right_panel)
