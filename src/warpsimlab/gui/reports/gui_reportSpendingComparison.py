# gui_reportSpendingComparison.py

import copy
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk

from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin
from src.warpsimlab.gui.gui_validation import parse_finite_float


class SpendingComparisonReportFrame(ScalableFrameMixin, ttk.Frame):

    DEFAULT_OPTIONS = {
        "spending_percentages": [70, 80, 90, 100, 110, 120, 130],
        "output": {
            "generate_html": True,
            "open_report_in_browser": False,
        },
    }


    def __init__(self, parent, report_options, parent_gui, title="Spending Comparison Report"):
        super().__init__(parent, padding=10)

        self.options = report_options
        self.parent_gui = parent_gui
        self.working_options = self._normalize_options(report_options)

        self._body_font = tkfont.nametofont("TkDefaultFont").copy()
        self._title_font = tkfont.Font(root=self, family="Arial", size=14, weight="bold")
        self._text_font = tkfont.Font(root=self, family="Arial", size=11)
        self._text_bold_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._text_italic_font = tkfont.Font(root=self, family="Arial", size=11, slant="italic")
        self._section_font = tkfont.Font(root=self, family="Arial", size=12, weight="bold")

        self._spending_entries = []

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._title_font)
        self._register_scalable_font(self._text_font)
        self._register_scalable_font(self._text_bold_font)
        self._register_scalable_font(self._text_italic_font)
        self._register_scalable_font(self._section_font)
        self._apply_gui_scale()

        self._build_header(title)
        self._build_spending_levels()
        self._build_output_options()
        self._build_buttons()


    def _apply_scaled_styles(self):
        style = ttk.Style(self)
        style.configure("SpendingComparison.TEntry", font=self._body_font)
        style.configure("SpendingComparison.TCheckbutton", font=self._body_font)
        style.configure("SpendingComparison.TButton", font=self._body_font)

        for entry in self._spending_entries:
            entry.configure(width=7)


    def _build_header(self, title):
        ttk.Label(self, text=title, font=self._title_font).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        ttk.Label(
            self,
            text="Compare how different household spending levels affect modeled financial outcomes.",
            font=self._text_font,
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        note_frame = ttk.Frame(self)
        note_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(
            note_frame,
            text="NOTE: Spending Comparison Reports are written to: ",
            font=self._text_italic_font,
        ).pack(side="left")

        ttk.Label(
            note_frame,
            text="Desktop \\ WARPSimLab \\ Reports",
            font=self._text_bold_font,
        ).pack(side="left")


    def _build_spending_levels(self):
        ttk.Label(self, text="Spending Levels", font=self._section_font).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(4, 4)
        )

        ttk.Label(
            self,
            text=(
                "Enter spending levels as percentages of current modeled household spending. "
                "Leave unused fields blank."
            ),
            font=self._text_font,
            wraplength=900,
            justify="left",
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 8))

        values_frame = ttk.Frame(self)
        values_frame.grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self.spending_vars = []
        percentages = self.working_options["spending_percentages"]

        for index in range(7):
            value = ""

            if index < len(percentages):
                value = percentages[index]

            text = ""

            if value != "":
                text = self._format_percentage(value)

            var = tk.StringVar(value=text)
            self.spending_vars.append(var)

            entry = ttk.Entry(
                values_frame,
                textvariable=var,
                width=7,
                justify="right",
                font=self._body_font,
                style="SpendingComparison.TEntry",
            )
            entry.grid(row=0, column=index * 2, padx=(0, 2))
            self._spending_entries.append(entry)

            ttk.Label(values_frame, text="%", font=self._body_font).grid(
                row=0, column=(index * 2) + 1, sticky="w", padx=(0, 10)
            )

        baseline_frame = ttk.Frame(self)
        baseline_frame.grid(row=6, column=0, columnspan=2, sticky="w", pady=(2, 12))

        ttk.Label(
            baseline_frame,
            text="100% = Current Spending",
            font=self._text_bold_font,
        ).pack(side="left")

        ttk.Label(
            baseline_frame,
            text="   All other values scale your existing year-by-year expense schedule relative to this baseline.",
            font=self._text_font,
        ).pack(side="left")


    def _build_output_options(self):
        self.open_browser_var = tk.BooleanVar(
            value=self.working_options["output"].get("open_report_in_browser", False)
        )

        ttk.Checkbutton(
            self,
            text="Open HTML report in web browser when complete",
            variable=self.open_browser_var,
            style="SpendingComparison.TCheckbutton",
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=2)


    def _build_buttons(self):
        button_frame = ttk.Frame(self)
        button_frame.grid(row=8, column=0, columnspan=2, sticky="w", pady=(18, 0))

        ttk.Button(
            button_frame,
            text="Apply",
            command=self.apply_changes,
            style="SpendingComparison.TButton",
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_changes,
            style="SpendingComparison.TButton",
        ).pack(side="left")


    def _normalize_options(self, report_options):
        normalized = copy.deepcopy(self.DEFAULT_OPTIONS)

        if not isinstance(report_options, dict):
            return normalized

        percentages = report_options.get("spending_percentages")

        if isinstance(percentages, list):
            normalized["spending_percentages"] = list(percentages)

        output = report_options.get("output")

        if isinstance(output, dict):
            normalized["output"].update(output)

        return normalized


    def _format_percentage(self, value):
        value = float(value)

        if value.is_integer():
            return str(int(value))

        return f"{value:.2f}".rstrip("0").rstrip(".")


    def _parse_spending_percentages(self):
        values = []

        for var in self.spending_vars:
            text = var.get().strip()

            if text == "":
                continue

            try:
                value = parse_finite_float(text)
            except ValueError as exc:
                raise ValueError(f"'{text}' is not a valid spending percentage: {exc}") from exc

            if value <= 0:
                raise ValueError("Spending percentages must be greater than zero.")

            values.append(value)

        if len(values) < 2:
            raise ValueError("Enter at least two spending percentages.")

        if len(set(values)) != len(values):
            raise ValueError("Duplicate spending percentages are not allowed.")

        if 100.0 not in values:
            raise ValueError("100% Current Spending must always be included.")

        values.sort()
        return values


    def apply_changes(self):
        try:
            percentages = self._parse_spending_percentages()
        except ValueError as exc:
            messagebox.showerror("Invalid Spending Comparison", str(exc), parent=self)
            return

        self.working_options["spending_percentages"] = percentages
        self.working_options["output"]["open_report_in_browser"] = self.open_browser_var.get()

        self.options.clear()
        self.options.update(copy.deepcopy(self.working_options))

        self.parent_gui.edit_blank()
        self.parent_gui.run_simulation_from_gui(sim_type="spending_comparison_report")


    def cancel_changes(self):
        self.working_options = self._normalize_options(self.options)
        self.parent_gui.edit_blank()