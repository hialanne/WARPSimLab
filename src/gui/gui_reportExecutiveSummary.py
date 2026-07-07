import copy
import tkinter as tk
from tkinter import ttk


class ExecutiveSummaryReportFrame(ttk.Frame):
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
    }

    OLD_TO_NEW_OPTION_PATHS = {
        "include_portfolio_plot": (
            ["portfolio_visuals", "include_normal_projection"],
            True,
        ),
        "include_income_plot": (
            ["income_visuals", "include_normal_income"],
            True,
        ),
        "include_operating_balance_plot": (
            ["cash_flow_visuals", "include_cumulative_operating_balance"],
            False,
        ),
        "include_historical_windows": (
            ["portfolio_visuals", "include_historical_windows_analysis"],
            False,
        ),
        "include_monte_carlo": (
            ["portfolio_visuals", "include_monte_carlo_analysis"],
            False,
        ),
        "include_simulation_summary": (
            ["include_simulation_summary"],
            True,
        ),
        "include_assumptions_appendix": (
            ["include_assumptions_appendix"],
            True,
        ),
        "output_format": (
            ["output_format"],
            "HTML",
        ),
    }

    def __init__(self, parent, report_options, parent_gui, title="Executive Summary"):
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
            text="Select the sections and outputs to include in the Executive Summary report.",
            font=("Arial", 11),
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        note_frame = ttk.Frame(self)
        note_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(
            note_frame,
            text="NOTE: Executive Summary Reports are written to: ",
            font=("Arial", 11, "italic")
        ).pack(side="left")

        ttk.Label(
            note_frame,
            text="Desktop \\ WARPSimLab \\ Reports",
            font=("Arial", 11, "bold")
        ).pack(side="left")

        row = 3

        content_frame = ttk.Frame(self)
        content_frame.grid(row=row, column=0, sticky="nw")

        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nw", padx=(0, 60))

        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nw")

        left_row = 0
        right_row = 0

        left_row = self._add_section_label_to_frame(left_frame, "Simulation Summary", left_row)
        left_row = self._add_check_path_to_frame(
            left_frame,
            "Include Simulation Summary",
            ["include_simulation_summary"],
            left_row
        )

        left_row += 1
        left_row = self._add_section_label_to_frame(left_frame, "Appendices", left_row)
        left_row = self._add_check_path_to_frame(
            left_frame,
            "Include assumptions appendix",
            ["include_assumptions_appendix"],
            left_row
        )

        left_row += 1
        left_row = self._add_section_label_to_frame(left_frame, "Output Format", left_row)

        output_format_var = tk.StringVar(
            value=self._get_option_path(["output_format"], "HTML")
        )
        self.vars["output_format"] = output_format_var

        output_frame = ttk.Frame(left_frame)
        output_frame.grid(row=left_row, column=0, sticky="w", pady=2)

        ttk.Radiobutton(
            output_frame,
            text="HTML",
            variable=output_format_var,
            value="HTML"
        ).pack(side="left", padx=(0, 20))

        ttk.Radiobutton(
            output_frame,
            text="PDF (future)",
            variable=output_format_var,
            value="PDF"
        ).pack(side="left")

        output_format_var.trace_add(
            "write",
            lambda *_: self._set_option_path(
                ["output_format"],
                output_format_var.get()
            )
        )

        right_row = self._add_section_label_to_frame(right_frame, "Portfolio Visuals", right_row)
        right_row = self._add_check_path_to_frame(
            right_frame,
            "Include normal projection",
            ["portfolio_visuals", "include_normal_projection"],
            right_row
        )
        right_row = self._add_check_path_to_frame(
            right_frame,
            "Include sub-categories projection",
            ["portfolio_visuals", "include_subcategories_projection"],
            right_row
        )
        right_row = self._add_check_path_to_frame(
            right_frame,
            "Include Historical Windows analysis",
            ["portfolio_visuals", "include_historical_windows_analysis"],
            right_row
        )
        right_row = self._add_check_path_to_frame(
            right_frame,
            "Include Monte Carlo analysis",
            ["portfolio_visuals", "include_monte_carlo_analysis"],
            right_row
        )

        right_row += 1
        right_row = self._add_section_label_to_frame(right_frame, "Income Visuals", right_row)
        right_row = self._add_check_path_to_frame(
            right_frame,
            "Include normal income",
            ["income_visuals", "include_normal_income"],
            right_row
        )
        right_row = self._add_check_path_to_frame(
            right_frame,
            "Include sub-categories income",
            ["income_visuals", "include_subcategories_income"],
            right_row
        )

        right_row += 1
        right_row = self._add_section_label_to_frame(
            right_frame,
            "Cashflow Visuals",
            right_row
        )

        right_row = self._add_check_path_to_frame(
            right_frame,
            "Include normal cashflow",
            ["cashflow_visuals", "include_normal_cashflow"],
            right_row
        )

        right_row = self._add_check_path_to_frame(
            right_frame,
            "Include sub-categories cashflow",
            ["cashflow_visuals", "include_subcategories_cashflow"],
            right_row
        )

        right_row += 1
        right_row = self._add_section_label_to_frame(
            right_frame,
            "Operating Balance Visuals",
            right_row
        )

        right_row = self._add_check_path_to_frame(
            right_frame,
            "Include cumulative operating balance",
            ["operating_balance_visuals", "include_cumulative_operating_balance"],
            right_row
        )

        row += 1

        button_frame = ttk.Frame(self)
        button_frame.grid(row=row, column=0, sticky="w", pady=(18, 0))

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

        for key, value in report_options.items():
            if key in {
                "portfolio_visuals",
                "income_visuals",
                "cashflow_visuals",
                "operating_balance_visuals",
            }:
                if isinstance(value, dict):
                    normalized.setdefault(key, {})
                    normalized[key].update(value)
            elif key in {
                "include_simulation_summary",
                "include_assumptions_appendix",
                "output_format",
            }:
                normalized[key] = value

        for old_key, (new_path, _default_value) in self.OLD_TO_NEW_OPTION_PATHS.items():
            if old_key in report_options:
                self._set_option_path_in_dict(
                    normalized,
                    new_path,
                    report_options[old_key]
                )

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

    def _add_section_label(self, text, row):
        ttk.Label(
            self,
            text=text,
            font=("Arial", 12, "bold")
        ).grid(row=row, column=0, sticky="w", pady=(10, 4))
        return row + 1

    def _add_check_path(self, label, path, row):
        var = tk.BooleanVar(value=self._get_option_path(path, False))
        self.vars[self._path_key(path)] = var

        cb = ttk.Checkbutton(
            self,
            text=label,
            variable=var
        )
        cb.grid(row=row, column=0, sticky="w", pady=2)

        var.trace_add(
            "write",
            lambda *_args, p=path, v=var: self._set_option_path(p, v.get())
        )

        return row + 1

    def apply_changes(self):
        self.options.clear()
        self.options.update(copy.deepcopy(self.working_options))

        self.parent_gui.edit_main_home()
        self.parent_gui.run_simulation_from_gui(sim_type="summary_report")

    def cancel_changes(self):
        self.working_options = self._normalize_options(self.options)

        for path_key, var in self.vars.items():
            path = path_key.split(".")

            if isinstance(var, tk.BooleanVar):
                var.set(self._get_option_path(path, False))
            elif isinstance(var, tk.StringVar):
                var.set(self._get_option_path(path, "HTML"))

        self.parent_gui.edit_main_home()

    def _add_section_label_to_frame(self, parent, text, row):
        ttk.Label(
            parent,
            text=text,
            font=("Arial", 12, "bold")
        ).grid(row=row, column=0, sticky="w", pady=(10, 4))
        return row + 1

    def _add_check_path_to_frame(self, parent, label, path, row):
        var = tk.BooleanVar(value=self._get_option_path(path, False))
        self.vars[self._path_key(path)] = var

        cb = ttk.Checkbutton(
            parent,
            text=label,
            variable=var
        )
        cb.grid(row=row, column=0, sticky="w", pady=2)

        var.trace_add(
            "write",
            lambda *_args, p=path, v=var: self._set_option_path(p, v.get())
        )

        return row + 1