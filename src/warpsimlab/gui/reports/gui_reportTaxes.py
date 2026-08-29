# gui_reportTaxes.py

import copy
import tkinter as tk
from tkinter import ttk

from src.warpsimlab.utils.tooltip import Tooltip


class TaxReportFrame(ttk.Frame):
    DEFAULT_OPTIONS = {
        "output": {
            "generate_html": True,
            "generate_csv": False,
            "open_report_in_browser": False,
        },
        "sections": {
            "include_roth_analysis": True,
            "include_hsa_analysis": True,
            "include_rmd_analysis": True,
            "include_educational_commentary": True,
        },
    }

    def __init__(self, parent, report_options, parent_gui, title="Tax Report"):
        super().__init__(parent, padding=10)

        self.options = report_options
        self.parent_gui = parent_gui
        self.working_options = self._normalize_options(report_options)
        self.vars = {}

        ttk.Label(
            self,
            text=title,
            font=("Arial", 14, "bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        ttk.Label(
            self,
            text=(
                "Select the outputs and optional sections to include in the Tax Report. "
                "The report explains how taxes evolve over the simulation lifetime."
            ),
            font=("Arial", 11),
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(
            self,
            text=(
                "Tax calculation settings (Federal, State, Payroll, Filing Status, etc.) "
                "are configured under Cash Flow - Taxes."
            ),
            font=("Arial", 10, "italic"),
            wraplength=900,
            justify="left",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 12))

        note_frame = ttk.Frame(self)
        note_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(
            note_frame,
            text="NOTE: Tax Reports are written to: ",
            font=("Arial", 11, "italic")
        ).pack(side="left")

        ttk.Label(
            note_frame,
            text="Desktop \\ WARPSimLab \\ Reports",
            font=("Arial", 11, "bold")
        ).pack(side="left")

        content_frame = ttk.Frame(self)
        content_frame.grid(row=4, column=0, sticky="nw")

        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nw", padx=(0, 80))

        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nw")

        left_row = 0
        right_row = 0

        left_row = self._add_section_label_to_frame(left_frame, "Output", left_row)

        left_row = self._add_check_path_to_frame(
            left_frame,
            "HTML Report",
            ["output", "generate_html"],
            left_row,
            "Generate the Tax Report as a formatted HTML file."
        )

        left_row = self._add_check_path_to_frame(
            left_frame,
            "CSV Export",
            ["output", "generate_csv"],
            left_row,
            "Generate a CSV file containing the report's yearly tax data."
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

        right_row = self._add_section_label_to_frame(right_frame, "Sections", right_row)

        right_row = self._add_check_path_to_frame(
            right_frame,
            "Include Roth Analysis",
            ["sections", "include_roth_analysis"],
            right_row,
            (
                "Include educational analysis of Roth account balances, "
                "withdrawals, and their modeled tax treatment."
            )
        )

        right_row = self._add_check_path_to_frame(
            right_frame,
            "Include HSA Analysis",
            ["sections", "include_hsa_analysis"],
            right_row,
            (
                "Include educational analysis of HSA balances, withdrawals, "
                "and their modeled tax treatment."
            )
        )

        right_row = self._add_check_path_to_frame(
            right_frame,
            "Include RMD Analysis",
            ["sections", "include_rmd_analysis"],
            right_row,
            (
                "Include educational analysis of required minimum "
                "distributions modeled during the simulation."
            )
        )

        right_row = self._add_check_path_to_frame(
            right_frame,
            "Include Educational Commentary",
            ["sections", "include_educational_commentary"],
            right_row,
            (
                "Include explanatory commentary about the simulated tax "
                "results. The commentary is educational and is not tax advice."
            )
        )

        button_frame = ttk.Frame(self)
        button_frame.grid(row=5, column=0, sticky="w", pady=(18, 0))

        ttk.Button(
            button_frame,
            text="Apply",
            command=self.apply_changes
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_changes
        ).pack(side="left")

    def _normalize_options(self, report_options):
        normalized = copy.deepcopy(self.DEFAULT_OPTIONS)

        if not isinstance(report_options, dict):
            return normalized

        for key in {"output", "sections"}:
            if isinstance(report_options.get(key), dict):
                normalized[key].update(report_options[key])

        return normalized

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
        self._set_option_path_in_dict(
            self.working_options,
            path,
            value
        )

    def _path_key(self, path):
        return ".".join(path)

    def _add_section_label_to_frame(self, parent, text, row):
        ttk.Label(
            parent,
            text=text,
            font=("Arial", 12, "bold")
        ).grid(row=row, column=0, sticky="w", pady=(10, 4))
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
            lambda *_args, p=path, v=var: self._set_option_path(p, v.get())
        )

        return row + 1


    def apply_changes(self):
        self.options.clear()
        self.options.update(copy.deepcopy(self.working_options))

        self.parent_gui.edit_blank()
        self.parent_gui.run_simulation_from_gui(sim_type="tax_report")

    def cancel_changes(self):
        self.working_options = self._normalize_options(self.options)

        for path_key, var in self.vars.items():
            path = path_key.split(".")
            var.set(self._get_option_path(path, False))

        self.parent_gui.edit_blank()