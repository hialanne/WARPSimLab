# summaryDialog.py

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from src.warpsimlab.gui.gui_display import set_window_maximized, set_window_normal, window_is_maximized
from src.warpsimlab.gui.gui_scaling import ScalableClientMixin
from src.warpsimlab.gui.gui_settings import (
    SUMMARY_DIALOG_AUTOMATIC,
    SUMMARY_DIALOG_MAXIMIZED,
    geometry_is_visible,
    save_display_settings,
)

from .summaryPortfolio import build_portfolio_tab
from .summaryIncome import build_income_tab
from .summaryCashFlow import build_cash_flow_tab
from .summaryOverview import build_summary_tab


class SummaryDialog(ScalableClientMixin, tk.Toplevel):

    def __init__(self, results, husband, wife, sim_config, title="Simulation Summary"):
        super().__init__(sim_config.root)

        self.results = results
        self.husband = husband
        self.wife = wife
        self.sim_config = sim_config

        parent = sim_config.root
        parent.update_idletasks()

        development_font_linespace = 24
        reference_font = tkfont.Font(root=self, family="Arial", size=16)
        gui_scale = reference_font.metrics("linespace") / development_font_linespace

        width = int(1100 * gui_scale)

        # Making the dialog slightly shorter vertically to keep the dialog close to the same height as the main window.
        # height = int(800 * gui_scale)
        height = int(750 * gui_scale)

        self._summary_reference_width = width
        self._summary_reference_height = height
        self._warpsimlab_gui_scale = 1.0
        self._summary_scale_after_id = None

        self._apply_summary_startup_settings(width, height)

        self._title_font = tkfont.Font(root=self, family="Arial", size=17, weight="bold")
        self._tab_font = tkfont.Font(root=self, family="Arial", size=14)
        self._tab_bold_font = tkfont.Font(root=self, family="Arial", size=14, weight="bold")
        self._report_header_font = tkfont.Font(root=self, family="Arial", size=14, weight="bold")
        self._report_body_font = tkfont.Font(root=self, family="Courier New", size=12)
        self._report_body_bold_font = tkfont.Font(root=self, family="Courier New", size=12, weight="bold")
        self._button_font = tkfont.nametofont("TkDefaultFont").copy()

        self._initialize_scaling(self)
        self._register_scalable_font(self._title_font)
        self._register_scalable_font(self._tab_font)
        self._register_scalable_font(self._tab_bold_font)
        self._register_scalable_font(self._report_header_font)
        self._register_scalable_font(self._report_body_font)
        self._register_scalable_font(self._report_body_bold_font)
        self._register_scalable_font(self._button_font)
        self._apply_gui_scale()

        if self.sim_config.inflation_mode == "real":
            value_basis = "Real"
        else:
            value_basis = "Nominal"

        self.display_title = f"{title} ({value_basis})"

        self.title(self.display_title)
        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self._close_dialog)
        self.bind("<Configure>", self._on_summary_configure, add="+")


    def _apply_summary_startup_settings(self, width, height):
        settings = self.sim_config.root._warpsimlab_display_settings["summary_dialog"]

        if settings.get("remember_geometry", False):
            if settings.get("last_maximized", False):
                set_window_maximized(self)
                return

            saved_geometry = settings.get("last_geometry")
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            if geometry_is_visible(saved_geometry, screen_width, screen_height):
                set_window_normal(self)
                self.geometry(saved_geometry)
                return

        sizing_mode = settings.get("sizing_mode", SUMMARY_DIALOG_AUTOMATIC)

        if sizing_mode == SUMMARY_DIALOG_MAXIMIZED:
            set_window_maximized(self)
            return

        set_window_normal(self)

        parent = self.sim_config.root
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")


    def _save_summary_geometry(self):
        display_settings = self.sim_config.root._warpsimlab_display_settings
        settings = display_settings["summary_dialog"]

        if not settings.get("remember_geometry", False):
            return

        self.update_idletasks()

        maximized = window_is_maximized(self)
        settings["last_maximized"] = maximized

        if not maximized:
            settings["last_geometry"] = self.winfo_geometry()

        save_display_settings(display_settings)


    def _close_dialog(self):
        self._save_summary_geometry()
        self.destroy()


    def _on_summary_configure(self, event):
        if event.widget is not self:
            return

        if self._summary_scale_after_id is not None:
            self.after_cancel(self._summary_scale_after_id)

        self._summary_scale_after_id = self.after(50, self._update_summary_scale)


    def _update_summary_scale(self):
        self._summary_scale_after_id = None

        width = self.winfo_width()
        height = self.winfo_height()

        if width <= 1 or height <= 1:
            return

        scale = min(width / self._summary_reference_width, height / self._summary_reference_height)

        if abs(scale - self._get_gui_scale()) < 0.01:
            return

        self._warpsimlab_gui_scale = scale
        self.event_generate("<<WARPSimLabScaleChanged>>", when="tail")


    def _apply_scaled_styles(self):
        style = ttk.Style(self)
        scale = self._get_gui_scale()

        tab_padx = max(1, round(20 * scale))
        tab_pady = max(1, round(5 * scale))
        selected_tab_padx = max(1, round(40 * scale))

        style.configure("Summary.TNotebook", tabposition="n")
        style.configure("Summary.TNotebook.Tab", font=self._tab_font, padding=[tab_padx, tab_pady])
        style.map(
            "Summary.TNotebook.Tab",
            font=[("selected", self._tab_bold_font)],
            padding=[("selected", [selected_tab_padx, 0])]
        )
        style.configure("Summary.TButton", font=self._button_font)


    def _build_ui(self):
        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container, text=self.display_title, font=self._title_font, anchor="center", justify="center"
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        notebook = ttk.Notebook(container, style="Summary.TNotebook")
        notebook.grid(row=1, column=0, columnspan=2, sticky="nsew")

        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(1, weight=1)

        build_portfolio_tab(self, notebook)
        build_income_tab(self, notebook)
        build_cash_flow_tab(self, notebook)
        build_summary_tab(self, notebook)

        ttk.Button(container, text="Close", command=self._close_dialog, style="Summary.TButton").grid(
            row=2, column=0, columnspan=2, pady=(20, 0)
        )


    def _get_display_indices(self):
        r = self.results

        year_start_index = 1
        year_end_index = len(r["year"]) - 1

        if self.sim_config.second_person_enabled:
            last_retirement_index = max(
                self.husband.retire_age - self.husband.age,
                self.wife.retire_age - self.wife.age
            )
        else:
            last_retirement_index = self.husband.retire_age - self.husband.age

        last_retirement_index = min(max(last_retirement_index, 1), year_end_index)
        before_retirement_index = max(last_retirement_index - 1, 1)
        after_retirement_index = min(last_retirement_index + 1, year_end_index)

        return [year_start_index, before_retirement_index, after_retirement_index, year_end_index]


    def _add_year_headers(self, tab, column_indices, header_font):
        r = self.results

        start_year = int(r["year"][column_indices[0]])
        before_year = int(r["year"][column_indices[1]])
        after_year = int(r["year"][column_indices[2]])
        end_year = int(r["year"][column_indices[3]])

        column_headers = [
            "",
            f"Start\nSimulation\n({start_year})",
            f"Year Before\nRetirement\n({before_year})",
            f"Year After\nRetirement\n({after_year})",
            f"End\nSimulation\n({end_year})"
        ]

        for col, header in enumerate(column_headers):
            ttk.Label(tab, text=header, font=header_font, anchor="center").grid(
                row=0, column=col, padx=20, pady=5, sticky="nsew"
            )
            tab.columnconfigure(col, weight=0)