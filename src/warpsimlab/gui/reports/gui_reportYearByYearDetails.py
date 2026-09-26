# gui_reportYearByYearDetails.py

import copy
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin
from src.warpsimlab.utils.tooltip import Tooltip


class YearByYearDetailsReportFrame(ScalableFrameMixin, ttk.Frame):

    DEFAULT_OPTIONS = {
        "generate_html": True,
        "generate_csv": True,
        "table_detail": "Compact",
        "insert_5_year_breaks": True,
        "open_report_in_browser": False,
    }


    def __init__(self, parent, report_options, parent_gui, title="Year-by-Year Details"):
        super().__init__(parent, padding=10)

        self.options = report_options
        self.parent_gui = parent_gui
        self.working_options = self._normalize_options(report_options)
        self.vars = {}

        self._body_font = tkfont.nametofont("TkDefaultFont").copy()
        self._title_font = tkfont.Font(root=self, family="Arial", size=14, weight="bold")
        self._text_font = tkfont.Font(root=self, family="Arial", size=11)
        self._text_bold_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._text_italic_font = tkfont.Font(root=self, family="Arial", size=11, slant="italic")
        self._section_font = tkfont.Font(root=self, family="Arial", size=12, weight="bold")
        self._detail_font = tkfont.Font(root=self, family="Arial", size=10)
        self._tooltip_font = tkfont.Font(root=self, family="Arial", size=11)

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._title_font)
        self._register_scalable_font(self._text_font)
        self._register_scalable_font(self._text_bold_font)
        self._register_scalable_font(self._text_italic_font)
        self._register_scalable_font(self._section_font)
        self._register_scalable_font(self._detail_font)
        self._register_scalable_font(self._tooltip_font)
        self._apply_gui_scale()

        self._build_header(title)
        self._build_content()
        self._build_buttons()


    def _apply_scaled_styles(self):
        style = ttk.Style(self)
        style.configure("YearByYear.TCheckbutton", font=self._body_font)
        style.configure("YearByYear.TRadiobutton", font=self._body_font)
        style.configure("YearByYear.TButton", font=self._body_font)


    def _build_header(self, title):
        ttk.Label(self, text=title, font=self._title_font).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        ttk.Label(
            self,
            text="Select the outputs and table detail level for the Year-by-Year Details report.",
            font=self._text_font,
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        note_frame = ttk.Frame(self)
        note_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(
            note_frame,
            text="NOTE: Year-by-Year Reports are written to: ",
            font=self._text_italic_font,
        ).pack(side="left")

        ttk.Label(
            note_frame,
            text="Desktop \\ WARPSimLab \\ Reports",
            font=self._text_bold_font,
        ).pack(side="left")


    def _build_content(self):
        content_frame = ttk.Frame(self)
        content_frame.grid(row=3, column=0, sticky="nw")

        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nw", padx=(0, 60))

        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nw")

        self._build_output_options(left_frame)
        self._build_table_detail(right_frame)


    def _build_output_options(self, parent):
        row = 0

        row = self._add_section_label_to_frame(parent, "Output", row)
        row = self._add_check_path_to_frame(
            parent,
            "Generate HTML report",
            ["generate_html"],
            row,
            "Generate a formatted HTML version of the Year-by-Year Details report.",
        )
        row = self._add_check_path_to_frame(
            parent,
            "Open HTML report in web browser when complete",
            ["open_report_in_browser"],
            row,
            "Open the generated HTML report in the default web browser when report generation is complete.",
        )
        row = self._add_check_path_to_frame(
            parent,
            "Generate CSV export",
            ["generate_csv"],
            row,
            "Generate a CSV file containing the year-by-year report data.",
        )

        row += 1
        row = self._add_section_label_to_frame(parent, "Layout", row)

        self._add_check_path_to_frame(
            parent,
            "Insert visual break every 5 years",
            ["insert_5_year_breaks"],
            row,
            "Add a visual separator after every five simulation years in the HTML table.",
        )


    def _build_table_detail(self, parent):
        row = 0

        row = self._add_section_label_to_frame(parent, "Table Detail", row)

        table_detail_var = tk.StringVar(value=self._get_option_path(["table_detail"], "Compact"))
        self.vars["table_detail"] = table_detail_var

        detail_frame = ttk.Frame(parent)
        detail_frame.grid(row=row, column=0, sticky="w", pady=2)

        compact_rb = ttk.Radiobutton(
            detail_frame,
            text="Compact",
            variable=table_detail_var,
            value="Compact",
            style="YearByYear.TRadiobutton",
        )
        compact_rb.pack(anchor="w", pady=2)
        Tooltip(
            compact_rb,
            "Show a smaller set of high-level year-by-year columns.",
            font=self._tooltip_font,
        )

        detailed_rb = ttk.Radiobutton(
            detail_frame,
            text="Detailed",
            variable=table_detail_var,
            value="Detailed",
            style="YearByYear.TRadiobutton",
        )
        detailed_rb.pack(anchor="w", pady=2)
        Tooltip(
            detailed_rb,
            "Show expanded income, tax, cash flow, and portfolio columns for each simulation year.",
            font=self._tooltip_font,
        )

        table_detail_var.trace_add(
            "write", lambda *_: self._set_option_path(["table_detail"], table_detail_var.get())
        )

        ttk.Label(
            parent,
            text=(
                "Compact: fewer high-level columns.\n"
                "Detailed: expanded income, tax, cash-flow, and portfolio columns."
            ),
            font=self._detail_font,
            wraplength=360,
            justify="left",
        ).grid(row=row + 1, column=0, sticky="w", pady=(8, 0))


    def _build_buttons(self):
        button_frame = ttk.Frame(self)
        button_frame.grid(row=4, column=0, sticky="w", pady=(18, 0))

        ttk.Button(
            button_frame,
            text="Apply",
            command=self.apply_changes,
            style="YearByYear.TButton",
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_changes,
            style="YearByYear.TButton",
        ).pack(side="left")


    def _normalize_options(self, report_options):
        normalized = copy.deepcopy(self.DEFAULT_OPTIONS)

        if not isinstance(report_options, dict):
            return normalized

        for key, value in report_options.items():
            if key in normalized:
                normalized[key] = value

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
        self._set_option_path_in_dict(self.working_options, path, value)


    def _path_key(self, path):
        return ".".join(path)


    def _add_section_label_to_frame(self, parent, text, row):
        ttk.Label(parent, text=text, font=self._section_font).grid(
            row=row, column=0, sticky="w", pady=(10, 4)
        )

        return row + 1


    def _add_check_path_to_frame(self, parent, label, path, row, tooltip_text=None):
        var = tk.BooleanVar(value=self._get_option_path(path, False))
        self.vars[self._path_key(path)] = var

        checkbutton = ttk.Checkbutton(
            parent,
            text=label,
            variable=var,
            style="YearByYear.TCheckbutton",
        )
        checkbutton.grid(row=row, column=0, sticky="w", pady=2)

        if tooltip_text:
            Tooltip(checkbutton, tooltip_text, font=self._tooltip_font)

        var.trace_add(
            "write", lambda *_args, p=path, v=var: self._set_option_path(p, v.get())
        )

        return row + 1


    def apply_changes(self):
        self.options.clear()
        self.options.update(copy.deepcopy(self.working_options))

        self.parent_gui.edit_blank()
        self.parent_gui.run_simulation_from_gui(sim_type="year_by_year_report")


    def cancel_changes(self):
        self.working_options = self._normalize_options(self.options)

        for path_key, var in self.vars.items():
            path = path_key.split(".")

            if isinstance(var, tk.BooleanVar):
                var.set(self._get_option_path(path, False))
                continue

            if isinstance(var, tk.StringVar):
                var.set(self._get_option_path(path, "Compact"))

        self.parent_gui.edit_blank()