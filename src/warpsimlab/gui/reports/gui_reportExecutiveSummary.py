# gui_reportExecutiveSummary.py

import copy
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin
from src.warpsimlab.utils.tooltip import Tooltip


class ExecutiveSummaryReportFrame(ScalableFrameMixin, ttk.Frame):

    DEFAULT_OPTIONS = {
        "include_simulation_summary": True,
        "portfolio_visuals": {
            "include_normal_projection": True,
            "include_subcategories_projection": False,
            "include_historical_windows_analysis": False,
            "include_monte_carlo_analysis": False,
        },
        "income_visuals": {
            "include_normal_income": True,
            "include_subcategories_income": False,
        },
        "cashflow_visuals": {
            "include_normal_cashflow": True,
            "include_subcategories_cashflow": False,
        },
        "operating_balance_visuals": {
            "include_cumulative_operating_balance": True,
        },
        "include_assumptions_appendix": True,
        "output_format": "HTML",
        "open_report_in_browser": False,
    }

    OLD_TO_NEW_OPTION_PATHS = {
        "include_portfolio_plot": (["portfolio_visuals", "include_normal_projection"], True),
        "include_income_plot": (["income_visuals", "include_normal_income"], True),
        "include_operating_balance_plot": (["cash_flow_visuals", "include_cumulative_operating_balance"], False),
        "include_historical_windows": (["portfolio_visuals", "include_historical_windows_analysis"], False),
        "include_monte_carlo": (["portfolio_visuals", "include_monte_carlo_analysis"], False),
        "include_simulation_summary": (["include_simulation_summary"], True),
        "include_assumptions_appendix": (["include_assumptions_appendix"], True),
        "output_format": (["output_format"], "HTML"),
    }


    def __init__(self, parent, report_options, parent_gui, title="Executive Summary"):
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
        self._tooltip_font = tkfont.Font(root=self, family="Arial", size=11)

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._title_font)
        self._register_scalable_font(self._text_font)
        self._register_scalable_font(self._text_bold_font)
        self._register_scalable_font(self._text_italic_font)
        self._register_scalable_font(self._section_font)
        self._register_scalable_font(self._tooltip_font)
        self._apply_gui_scale()

        self._build_header(title)
        self._build_content()
        self._build_buttons()


    def _apply_scaled_styles(self):
        style = ttk.Style(self)
        style.configure("ExecutiveSummary.TCheckbutton", font=self._body_font)
        style.configure("ExecutiveSummary.TRadiobutton", font=self._body_font)
        style.configure("ExecutiveSummary.TButton", font=self._body_font)


    def _build_header(self, title):
        ttk.Label(self, text=title, font=self._title_font).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        ttk.Label(
            self,
            text="Select the sections and outputs to include in the Executive Summary report.",
            font=self._text_font,
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        note_frame = ttk.Frame(self)
        note_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(
            note_frame,
            text="NOTE: Executive Summary Reports are written to: ",
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

        self._build_left_column(left_frame)
        self._build_right_column(right_frame)


    def _build_left_column(self, parent):
        row = 0

        row = self._add_section_label_to_frame(parent, "Simulation Summary", row)
        row = self._add_check_path_to_frame(
            parent,
            "Include Simulation Summary",
            ["include_simulation_summary"],
            row,
            "Include summary tables for portfolio, income, cash flow, and simulation results.",
        )

        row += 1
        row = self._add_check_path_to_frame(
            parent,
            "Include assumptions appendix",
            ["include_assumptions_appendix"],
            row,
            "Include the assumptions and configuration used to generate the report.",
        )

        row += 1
        row = self._add_section_label_to_frame(parent, "Output Format", row)
        row = self._build_output_format(parent, row)

        self._add_check_path_to_frame(
            parent,
            "Open HTML report in web browser when complete",
            ["open_report_in_browser"],
            row,
            "Open the generated HTML report in the default web browser when report generation is complete.",
        )


    def _build_output_format(self, parent, row):
        output_format_var = tk.StringVar(value=self._get_option_path(["output_format"], "HTML"))
        self.vars["output_format"] = output_format_var

        output_frame = ttk.Frame(parent)
        output_frame.grid(row=row, column=0, sticky="w", pady=2)

        html_rb = ttk.Radiobutton(
            output_frame,
            text="HTML",
            variable=output_format_var,
            value="HTML",
            style="ExecutiveSummary.TRadiobutton",
        )
        html_rb.pack(side="left", padx=(0, 20))
        Tooltip(html_rb, "Generate the report as an HTML file.", font=self._tooltip_font)

        pdf_rb = ttk.Radiobutton(
            output_frame,
            text="PDF (future)",
            variable=output_format_var,
            value="PDF",
            style="ExecutiveSummary.TRadiobutton",
        )
        pdf_rb.pack(side="left")
        Tooltip(pdf_rb, "PDF report output is not currently implemented.", font=self._tooltip_font)

        output_format_var.trace_add(
            "write", lambda *_: self._set_option_path(["output_format"], output_format_var.get())
        )

        return row + 1


    def _build_right_column(self, parent):
        row = 1

        row = self._add_section_label_to_frame(parent, "Income Visuals", row)
        row = self._add_check_path_to_frame(
            parent,
            "Include normal income",
            ["income_visuals", "include_normal_income"],
            row,
            "Include the primary net income visualization.",
        )
        row = self._add_check_path_to_frame(
            parent,
            "Include sub-categories income",
            ["income_visuals", "include_subcategories_income"],
            row,
            "Include income separated into its component sources.",
        )

        row += 2
        row = self._add_section_label_to_frame(parent, "Cash Flow Visuals", row)
        row = self._add_check_path_to_frame(
            parent,
            "Include normal cash flow",
            ["cashflow_visuals", "include_normal_cashflow"],
            row,
            "Include the primary cash flow visualization.",
        )
        row = self._add_check_path_to_frame(
            parent,
            "Include sub-categories cash flow",
            ["cashflow_visuals", "include_subcategories_cashflow"],
            row,
            "Include cash flow separated into its component sources.",
        )

        row += 1
        row = self._add_section_label_to_frame(parent, "Operating Balance Visuals", row)
        row = self._add_check_path_to_frame(
            parent,
            "Include cumulative operating balance",
            ["operating_balance_visuals", "include_cumulative_operating_balance"],
            row,
            "Include the accumulated difference between cash inflows and outflows over time.",
        )

        row += 1
        row = self._add_section_label_to_frame(parent, "Portfolio Visuals", row)
        row = self._add_check_path_to_frame(
            parent,
            "Include normal projection",
            ["portfolio_visuals", "include_normal_projection"],
            row,
            "Include the primary portfolio projection using the selected simulation assumptions.",
        )
        row = self._add_check_path_to_frame(
            parent,
            "Include sub-categories projection",
            ["portfolio_visuals", "include_subcategories_projection"],
            row,
            "Include portfolio results separated by asset and account categories.",
        )
        row = self._add_check_path_to_frame(
            parent,
            "Include Historical Windows analysis",
            ["portfolio_visuals", "include_historical_windows_analysis"],
            row,
            "Include results from overlapping historical market return windows.",
        )
        self._add_check_path_to_frame(
            parent,
            "Include Monte Carlo analysis",
            ["portfolio_visuals", "include_monte_carlo_analysis"],
            row,
            "Include results from simulated market return paths.",
        )


    def _build_buttons(self):
        button_frame = ttk.Frame(self)
        button_frame.grid(row=4, column=0, sticky="w", pady=(18, 0))

        ttk.Button(
            button_frame,
            text="Apply",
            command=self.apply_changes,
            style="ExecutiveSummary.TButton",
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_changes,
            style="ExecutiveSummary.TButton",
        ).pack(side="left")


    def _normalize_options(self, report_options):
        normalized = copy.deepcopy(self.DEFAULT_OPTIONS)

        if not isinstance(report_options, dict):
            return normalized

        nested_sections = {
            "portfolio_visuals",
            "income_visuals",
            "cashflow_visuals",
            "operating_balance_visuals",
        }

        scalar_options = {
            "include_simulation_summary",
            "include_assumptions_appendix",
            "output_format",
            "open_report_in_browser",
        }

        for key, value in report_options.items():
            if key in nested_sections and isinstance(value, dict):
                normalized[key].update(value)

            if key in scalar_options:
                normalized[key] = value

        for old_key, (new_path, _default_value) in self.OLD_TO_NEW_OPTION_PATHS.items():
            if old_key in report_options:
                self._set_option_path_in_dict(normalized, new_path, report_options[old_key])

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
            style="ExecutiveSummary.TCheckbutton",
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
        self.parent_gui.run_simulation_from_gui(sim_type="summary_report")


    def cancel_changes(self):
        self.working_options = self._normalize_options(self.options)

        for path_key, var in self.vars.items():
            path = path_key.split(".")

            if isinstance(var, tk.BooleanVar):
                var.set(self._get_option_path(path, False))

            if isinstance(var, tk.StringVar):
                var.set(self._get_option_path(path, "HTML"))

        self.parent_gui.edit_blank()