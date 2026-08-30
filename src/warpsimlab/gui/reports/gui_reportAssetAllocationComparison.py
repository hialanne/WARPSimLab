# gui_reportAssetAllocationComparison.py

import copy
import tkinter as tk
from tkinter import ttk, messagebox

from src.warpsimlab.gui.gui_validation import parse_finite_float


class AssetAllocationComparisonReportFrame(ttk.Frame):

    DEFAULT_OPTIONS = {
        "equity_percentages": [
            0,
            20,
            40,
            60,
            80,
            100,
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
        title="Asset Allocation Comparison Report",
    ):
        super().__init__(
            parent,
            padding=10,
        )

        self.options = report_options
        self.parent_gui = parent_gui

        self.working_options = self._normalize_options(
            report_options
        )

        (
            self.current_equity_percent,
            self.current_bonds_percent,
            self.current_cash_percent,
        ) = self._compute_current_allocation()

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
                "Compare how different household equity allocations "
                "affect modeled financial outcomes."
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
            text=(
                "NOTE: Asset Allocation Comparison Reports "
                "are written to: "
            ),
            font=("Arial", 11, "italic"),
        ).pack(
            side="left",
        )

        ttk.Label(
            note_frame,
            text="Desktop \\ WARPSimLab \\ Reports",
            font=("Arial", 11, "bold"),
        ).pack(
            side="left",
        )

        row = 3

        ttk.Label(
            self,
            text="Current Allocation",
            font=("Arial", 12, "bold"),
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(4, 4),
        )
        row += 1

        current_frame = ttk.Frame(self)
        current_frame.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 12),
        )

        ttk.Label(
            current_frame,
            text=(
                f"Equity: "
                f"{self._format_percentage(self.current_equity_percent)}%"
            ),
            font=("Arial", 11, "bold"),
        ).pack(
            side="left",
            padx=(0, 22),
        )

        ttk.Label(
            current_frame,
            text=(
                f"Bonds: "
                f"{self._format_percentage(self.current_bonds_percent)}%"
            ),
            font=("Arial", 11),
        ).pack(
            side="left",
            padx=(0, 22),
        )

        ttk.Label(
            current_frame,
            text=(
                f"Cash: "
                f"{self._format_percentage(self.current_cash_percent)}%"
            ),
            font=("Arial", 11),
        ).pack(
            side="left",
        )

        row += 1

        ttk.Label(
            self,
            text="Equity Allocation Cases",
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
                "Enter household equity percentages to compare. "
                "Leave unused fields blank. The actual current "
                "allocation is included automatically."
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
            pady=(0, 8),
        )

        self.equity_vars = []

        percentages = self.working_options[
            "equity_percentages"
        ]

        for index in range(6):
            value = (
                percentages[index]
                if index < len(percentages)
                else ""
            )

            var = tk.StringVar(
                value=(
                    self._format_percentage(value)
                    if value != ""
                    else ""
                )
            )

            self.equity_vars.append(var)

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

        ttk.Label(
            self,
            text=(
                "For each comparison case, the remaining non-equity "
                "allocation is divided between bonds and cash using "
                "the current household bond-to-cash ratio."
            ),
            font=("Arial", 11),
            wraplength=900,
            justify="left",
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(2, 12),
        )

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
        ).pack(
            side="left",
        )

    def _normalize_options(self, report_options):
        normalized = copy.deepcopy(
            self.DEFAULT_OPTIONS
        )

        if not isinstance(report_options, dict):
            return normalized

        percentages = report_options.get(
            "equity_percentages"
        )

        if isinstance(percentages, list):
            normalized["equity_percentages"] = list(
                percentages
            )

        output = report_options.get("output")

        if isinstance(output, dict):
            normalized["output"].update(output)

        return normalized

    def _portfolio_components(self, portfolio):
        if portfolio is None:
            return 0.0, 0.0, 0.0

        equity = (
            float(getattr(portfolio, "equity_pre", 0.0))
            + float(getattr(portfolio, "equity_post", 0.0))
            + float(getattr(portfolio, "equity_roth", 0.0))
            + float(getattr(portfolio, "hsa_equity", 0.0))
        )

        bonds = (
            float(getattr(portfolio, "bond_pre", 0.0))
            + float(getattr(portfolio, "bond_post", 0.0))
            + float(getattr(portfolio, "bond_roth", 0.0))
            + float(getattr(portfolio, "hsa_bond", 0.0))
        )

        cash = (
            float(getattr(portfolio, "cash_pre", 0.0))
            + float(getattr(portfolio, "cash_post", 0.0))
            + float(getattr(portfolio, "cash_roth", 0.0))
            + float(getattr(portfolio, "hsa_cash", 0.0))
        )

        return equity, bonds, cash

    def _compute_current_allocation(self):
        h_equity, h_bonds, h_cash = (
            self._portfolio_components(
                self.parent_gui.husband_portfolio
            )
        )

        w_equity = 0.0
        w_bonds = 0.0
        w_cash = 0.0

        if self.parent_gui.simulation_controls.get(
            "second_person_enabled",
            False,
        ):
            w_equity, w_bonds, w_cash = (
                self._portfolio_components(
                    self.parent_gui.wife_portfolio
                )
            )

        equity = h_equity + w_equity
        bonds = h_bonds + w_bonds
        cash = h_cash + w_cash

        total = equity + bonds + cash

        if total <= 0.0:
            return 0.0, 0.0, 100.0

        return (
            100.0 * equity / total,
            100.0 * bonds / total,
            100.0 * cash / total,
        )

    def _format_percentage(self, value):
        value = float(value)

        if value.is_integer():
            return str(int(value))

        return f"{value:.2f}".rstrip(
            "0"
        ).rstrip(
            "."
        )

    def _parse_equity_percentages(self):
        values = []

        for var in self.equity_vars:
            text = var.get().strip()

            if text == "":
                continue

            try:
                value = parse_finite_float(text)
            except ValueError as exc:
                raise ValueError(f"'{text}' is not a valid equity percentage: {exc}") from exc

            if value < 0.0 or value > 100.0:
                raise ValueError(
                    "Equity percentages must be between "
                    "0 and 100."
                )

            values.append(value)

        if len(values) < 2:
            raise ValueError(
                "Enter at least two equity percentages."
            )

        if len(set(values)) != len(values):
            raise ValueError(
                "Duplicate equity percentages are not allowed."
            )

        non_equity = (
            self.current_bonds_percent
            + self.current_cash_percent
        )

        if (
            non_equity <= 0.0
            and any(value < 100.0 for value in values)
        ):
            raise ValueError(
                "The current portfolio contains no bonds or cash. "
                "WARPSimLab therefore has no current bond-to-cash "
                "ratio to preserve for lower-equity comparison cases."
            )

        values.sort()

        return values

    def apply_changes(self):
        try:
            percentages = (
                self._parse_equity_percentages()
            )
        except ValueError as exc:
            messagebox.showerror(
                "Invalid Asset Allocation Comparison",
                str(exc),
                parent=self,
            )
            return

        self.working_options[
            "equity_percentages"
        ] = percentages

        self.working_options["output"][
            "open_report_in_browser"
        ] = self.open_browser_var.get()

        self.options.clear()

        self.options.update(
            copy.deepcopy(
                self.working_options
            )
        )

        self.parent_gui.edit_blank()

        self.parent_gui.run_simulation_from_gui(
             sim_type="asset_allocation_comparison_report"
        )

    def cancel_changes(self):
        self.working_options = (
            self._normalize_options(
                self.options
            )
        )

        self.parent_gui.edit_blank()