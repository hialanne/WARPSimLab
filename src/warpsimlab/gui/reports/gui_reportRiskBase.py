# gui_reportRiskBase.py

import copy
import tkinter as tk
from tkinter import ttk

from src.warpsimlab.utils.tooltip import Tooltip

class RiskReportBaseFrame(ttk.Frame):
    REPORT_NAME = "Risk Report"
    RUN_SIM_TYPE = "risk_report"
    DESCRIPTION = "Select the sections and outputs to include in the risk report."
    METHOD_NOTE = ""
    DEFAULT_OPTIONS = {}

    def __init__(self, parent, report_options, parent_gui, title=None):
        super().__init__(parent, padding=10)

        self.options = report_options
        self.parent_gui = parent_gui
        self.working_options = self._normalize_options(report_options)
        self.vars = {}

        if title is None:
            title = self.REPORT_NAME

        ttk.Label(self, text=title, font=("Arial", 14, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        ttk.Label(
            self,
            text=self.DESCRIPTION,
            font=("Arial", 11),
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))

        row = 2

        if self.METHOD_NOTE:
            ttk.Label(
                self,
                text=self.METHOD_NOTE,
                font=("Arial", 10, "italic"),
                wraplength=900,
                justify="left",
            ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 12))
            row += 1

        note_frame = ttk.Frame(self)
        note_frame.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(
            note_frame,
            text=f"NOTE: {self.REPORT_NAME}s are written to: ",
            font=("Arial", 11, "italic"),
        ).pack(side="left")

        ttk.Label(
            note_frame,
            text="Desktop \\ WARPSimLab \\ Reports",
            font=("Arial", 11, "bold"),
        ).pack(side="left")

        row += 1

        content_frame = ttk.Frame(self)
        content_frame.grid(row=row, column=0, sticky="nw")

        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nw", padx=(0, 60))

        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nw")

        left_row = 0
        right_row = 0

        left_row = self._add_section_label_to_frame(left_frame, "General", left_row)

        left_row = self._add_check_path_to_frame(
            left_frame,
            "Include executive summary",
            ["general", "include_executive_summary"],
            left_row,
            (
                "Include a concise summary of the report's main simulated "
                "outcomes and observations."
            )
        )

        left_row = self._add_check_path_to_frame(
            left_frame,
            "Include method explanation",
            ["general", "include_method_explanation"],
            left_row,
            (
                "Include an explanation of the simulation method used to "
                "produce this risk report."
            )
        )

        left_row += 1
        left_row = self._add_section_label_to_frame(left_frame, "Analysis", left_row)

        left_row = self._add_check_path_to_frame(
            left_frame,
            "Include Portfolio Projection",
            ["analysis", "include_portfolio_projection"],
            left_row,
            (
                "Include portfolio values over time across the simulated "
                "or historical result set."
            )
        )

        left_row = self._add_check_path_to_frame(
            left_frame,
            "Include Portfolio Sustainability Analysis",
            ["analysis", "include_portfolio_sustainability"],
            left_row,
            (
                "Include analysis of how often the modeled portfolio remains "
                "above zero through the simulation period."
            )
        )

        left_row = self._build_method_specific_analysis_options(left_frame, left_row)

        left_row = self._add_check_path_to_frame(
            left_frame,
            "Include Percentile Portfolio Table",
            ["analysis", "include_percentile_table"],
            left_row,
            (
                "Include portfolio values at selected percentiles across the "
                "Monte Carlo runs or historical windows."
            )
        )

        left_row += 1
        left_row = self._add_section_label_to_frame(left_frame, "Output", left_row)

        left_row = self._add_check_path_to_frame(
            left_frame,
            "Generate HTML report",
            ["output", "generate_html"],
            left_row,
            "Generate the risk report as a formatted HTML file."
        )

        left_row = self._add_check_path_to_frame(
            left_frame,
            "Generate CSV export",
            ["output", "generate_csv"],
            left_row,
            (
                "Generate a CSV file containing the report's underlying "
                "risk-analysis data."
            )
        )

        left_row = self._add_check_path_to_frame(
            left_frame,
            "Open HTML report in web browser when complete",
            ["output", "open_report_in_browser"],
            left_row,
            (
                "Open the generated HTML report in the default web browser "
                "when report generation is complete."
            )
        )

        right_row = self._build_method_specific_options(right_frame, right_row)

        row += 1

        button_frame = ttk.Frame(self)
        button_frame.grid(row=row, column=0, sticky="w", pady=(18, 0))

        ttk.Button(button_frame, text="Apply", command=self.apply_changes).pack(
            side="left", padx=(0, 8)
        )

        ttk.Button(button_frame, text="Cancel", command=self.cancel_changes).pack(
            side="left"
        )


    def _build_method_specific_options(self, parent, row):
        return row


    def _build_method_specific_analysis_options(self, parent, row):
        return row


    def _normalize_options(self, report_options):
        normalized = copy.deepcopy(self.DEFAULT_OPTIONS)

        if isinstance(report_options, dict):
            self._deep_update(normalized, report_options)

        return normalized

    def _deep_update(self, target, source):
        for key, value in source.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value

    def _set_option_path_in_dict(self, options_dict, path, value):
        target = options_dict

        for key in path[:-1]:
            target = target.setdefault(key, {})

        target[path[-1]] = value

    def _get_option_path(self, path, default=False):
        target = self.working_options

        for key in path:
            if not isinstance(target, dict) or key not in target:
                return default
            target = target[key]

        return target

    def _set_option_path(self, path, value):
        self._set_option_path_in_dict(self.working_options, path, value)

    def _path_key(self, path):
        return ".".join(path)

    def _add_section_label_to_frame(self, parent, text, row):
        ttk.Label(parent, text=text, font=("Arial", 12, "bold")).grid(
            row=row, column=0, sticky="w", pady=(10, 4)
        )
        return row + 1


    def _add_check_path_to_frame(
        self,
        parent,
        label,
        path,
        row,
        tooltip_text=None
    ):
        var = tk.BooleanVar(value=self._get_option_path(path, False))
        self.vars[self._path_key(path)] = var

        cb = ttk.Checkbutton(
            parent,
            text=label,
            variable=var
        )
        cb.grid(row=row, column=0, sticky="w", pady=2)

        if tooltip_text:
            Tooltip(cb, tooltip_text, font=("Arial", 11))

        var.trace_add(
            "write",
            lambda *_args, p=path, v=var: self._set_option_path(p, v.get()),
        )

        return row + 1


    def apply_changes(self):
        self.options.clear()
        self.options.update(copy.deepcopy(self.working_options))

        self.parent_gui.edit_blank()
        self.parent_gui.run_simulation_from_gui(sim_type=self.RUN_SIM_TYPE)


    def cancel_changes(self):
        self.working_options = self._normalize_options(self.options)

        for path_key, var in self.vars.items():
            path = path_key.split(".")

            if isinstance(var, tk.BooleanVar):
                var.set(self._get_option_path(path, False))

        self.parent_gui.edit_blank()