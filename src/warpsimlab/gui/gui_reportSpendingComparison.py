# gui_reportSpendingComparison.py

import copy
import tkinter as tk
from tkinter import ttk, messagebox


class SpendingComparisonReportFrame(ttk.Frame):

    DEFAULT_OPTIONS = {
        "spending_percentages": [
            70,
            80,
            90,
            100,
            110,
            120,
            130,
        ],
        "output": {
            "generate_html": True,
            "open_report_in_browser": False,
        },
    }

    def __init__(
        self,
        parent,
        report_options,
        parent_gui,
        title="Spending Comparison Report",
    ):
        super().__init__(parent, padding=10)

        self.options = report_options
        self.parent_gui = parent_gui
        self.working_options = self._normalize_options(report_options)

        ttk.Label(
            self,
            text=title,
            font=("Arial", 14, "bold"),
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 8),
        )

        ttk.Label(
            self,
            text=(
                "Compare how different household spending levels affect "
                "modeled financial outcomes."
            ),
            font=("Arial", 11),
            wraplength=900,
            justify="left",
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 12),
        )

        note_frame = ttk.Frame(self)
        note_frame.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 12),
        )

        ttk.Label(
            note_frame,
            text="NOTE: Spending Comparison Reports are written to: ",
            font=("Arial", 11, "italic"),
        ).pack(side="left")

        ttk.Label(
            note_frame,
            text="Desktop \\ WARPSimLab \\ Reports",
            font=("Arial", 11, "bold"),
        ).pack(side="left")

        row = 3

        ttk.Label(
            self,
            text="Spending Levels",
            font=("Arial", 12, "bold"),
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(4, 4),
        )
        row += 1

        ttk.Label(
            self,
            text=(
                "Enter spending levels as percentages of current modeled "
                "household spending. Leave unused fields blank."
            ),
            font=("Arial", 11),
            wraplength=900,
            justify="left",
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 8),
        )
        row += 1

        values_frame = ttk.Frame(self)
        values_frame.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 6),
        )

        self.spending_vars = []

        percentages = self.working_options["spending_percentages"]

        for index in range(7):
            value = percentages[index] if index < len(percentages) else ""

            var = tk.StringVar(
                value=self._format_percentage(value)
                if value != ""
                else ""
            )
            self.spending_vars.append(var)

            entry = ttk.Entry(
                values_frame,
                textvariable=var,
                width=7,
                justify="right",
            )
            entry.grid(
                row=0,
                column=index * 2,
                padx=(0, 2),
            )

            ttk.Label(
                values_frame,
                text="%",
            ).grid(
                row=0,
                column=(index * 2) + 1,
                sticky="w",
                padx=(0, 10),
            )

        row += 1

        baseline_frame = ttk.Frame(self)
        baseline_frame.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(2, 12),
        )

        ttk.Label(
            baseline_frame,
            text="100% = Current Spending",
            font=("Arial", 11, "bold"),
        ).pack(side="left")

        ttk.Label(
            baseline_frame,
            text=(
                "   All other values scale your existing year-by-year "
                "expense schedule relative to this baseline."
            ),
            font=("Arial", 11),
        ).pack(side="left")

        row += 1

        self.open_browser_var = tk.BooleanVar(
            value=self.working_options["output"].get(
                "open_report_in_browser",
                False,
            )
        )

        ttk.Checkbutton(
            self,
            text="Open HTML report in web browser when complete",
            variable=self.open_browser_var,
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=2,
        )
        row += 1

        button_frame = ttk.Frame(self)
        button_frame.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(18, 0),
        )

        ttk.Button(
            button_frame,
            text="Apply",
            command=self.apply_changes,
        ).pack(
            side="left",
            padx=(0, 8),
        )

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_changes,
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
                value = float(text)
            except ValueError:
                raise ValueError(
                    f"'{text}' is not a valid spending percentage."
                )

            if value <= 0:
                raise ValueError(
                    "Spending percentages must be greater than zero."
                )

            values.append(value)

        if len(values) < 2:
            raise ValueError(
                "Enter at least two spending percentages."
            )

        if len(set(values)) != len(values):
            raise ValueError(
                "Duplicate spending percentages are not allowed."
            )

        if 100.0 not in values:
            raise ValueError(
                "100% Current Spending must always be included."
            )

        values.sort()

        return values


    def apply_changes(self):
        try:
            percentages = self._parse_spending_percentages()
        except ValueError as exc:
            messagebox.showerror(
                "Invalid Spending Comparison",
                str(exc),
                parent=self,
            )
            return

        self.working_options["spending_percentages"] = percentages
        self.working_options["output"]["open_report_in_browser"] = (
            self.open_browser_var.get()
        )

        self.options.clear()
        self.options.update(
            copy.deepcopy(self.working_options)
        )

        self.parent_gui.edit_blank()
        self.parent_gui.run_simulation_from_gui(
            sim_type="spending_comparison_report"
        )

    def cancel_changes(self):
        self.working_options = self._normalize_options(self.options)
        self.parent_gui.edit_blank()