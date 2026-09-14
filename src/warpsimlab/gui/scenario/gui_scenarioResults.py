# gui_scenarioResults.py

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk


class ScenarioResultsFrame(ttk.LabelFrame):
    def __init__(self, parent):
        style = ttk.Style(parent)
        style.configure("ScenarioResults.TLabelframe.Label", font=("Arial", 10, "bold"))

        super().__init__(parent, text="Results", padding=10, style="ScenarioResults.TLabelframe")

        self.columnconfigure(0, weight=1)

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        self.metric_rows = {}
        self.normal_label_font = tkfont.nametofont("TkDefaultFont").copy()
        self.changed_label_font = self.normal_label_font.copy()
        self.changed_label_font.configure(weight="bold")

        label_background = style.lookup("TLabel", "background")
        try:
            red, green, blue = (value // 256 for value in parent.winfo_rgb(label_background))
            dark_background = 0.2126 * red + 0.7152 * green + 0.0722 * blue < 128
        except tk.TclError:
            dark_background = False

        if dark_background:
            changed_result_color = "#ff6b6b"
        else:
            changed_result_color = "#c62828"

        style.configure("ScenarioChangedResult.TLabel", foreground=changed_result_color, font=self.changed_label_font)

        results_frame = ttk.Frame(self)
        results_frame.grid(row=0, column=0, sticky="ew")
        results_frame.columnconfigure(0, weight=1)

        self.results_table = results_frame
        self._build_results_table()

        assumptions_group = ttk.Frame(self)
        assumptions_group.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        assumptions_group.columnconfigure(0, weight=1)

        ttk.Separator(assumptions_group, orient="horizontal").grid(row=0, column=0, sticky="ew", pady=(0, 5))
        ttk.Label(assumptions_group, text="Assumptions", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w")

        self.assumptions_frame = ttk.Frame(assumptions_group)
        self.assumptions_frame.grid(row=2, column=0, sticky="nsew", pady=(4, 0))

        ttk.Label(self, text="Changed assumptions are shown in red.").grid(row=2, column=0, sticky="w", pady=(8, 0))


    def _build_results_table(self):
        table = self.results_table
        table.columnconfigure(0, weight=1)

        ttk.Label(table, text="Metric", font=self.changed_label_font).grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        ttk.Label(table, text="Original", font=self.changed_label_font).grid(
            row=0, column=1, sticky="e", padx=4
        )
        ttk.Label(table, text="Changed", font=self.changed_label_font).grid(
            row=0, column=2, sticky="e", padx=(4, 0)
        )

        row = 1
        row = self._add_section(table, row, "Key Results")
        row = self._add_metric_row(table, row, "ending_portfolio", "Ending Portfolio")
        row = self._add_metric_row(table, row, "depletion_rate", "Portfolio Depletion Rate")

        row = self._add_section(table, row, "Cash Flow Results")
        row = self._add_metric_row(table, row, "ending_cash_flow", "Ending Net Cash Flow")
        row = self._add_metric_row(table, row, "lifetime_funding_gap", "Lifetime Funding Gap")
        row = self._add_metric_row(table, row, "lifetime_taxes", "Lifetime Taxes")

        row = self._add_section(table, row, "Ending Assets")
        row = self._add_metric_row(table, row, "ending_pre_tax", "Tax-Deferred Assets")
        row = self._add_metric_row(table, row, "ending_after_tax", "Taxable Assets")
        row = self._add_metric_row(table, row, "ending_roth", "Roth Assets")
        self._add_metric_row(table, row, "ending_hsa", "HSA Assets")


    def _add_section(self, parent, row, label):
        ttk.Separator(parent, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=(8, 5))
        ttk.Label(parent, text=label, font=("Arial", 10, "bold")).grid(
            row=row + 1, column=0, columnspan=3, sticky="w"
        )
        return row + 2


    def _add_metric_row(self, parent, row, key, label):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=2)

        original = ttk.Label(parent, text="-", anchor="e")
        changed = ttk.Label(parent, text="-", anchor="e")

        original.grid(row=row, column=1, sticky="e", padx=4, pady=2)
        changed.grid(row=row, column=2, sticky="e", padx=(4, 0), pady=2)

        self.metric_rows[key] = {"original": original, "changed": changed}
        return row + 1


    def update_results(self, view_model):
        if view_model is None:
            return

        original = view_model.original_metrics
        changed = view_model.changed_metrics

        self._set_currency_row("ending_portfolio", original.ending_portfolio, changed.ending_portfolio)
        self._set_percent_row("depletion_rate", original.depletion_rate, changed.depletion_rate)

        self._set_currency_row("ending_cash_flow", original.ending_cash_flow, changed.ending_cash_flow)
        self._set_currency_row(
            "lifetime_funding_gap", original.lifetime_funding_gap, changed.lifetime_funding_gap, positive_red=True
        )
        self._set_currency_row("lifetime_taxes", original.lifetime_taxes, changed.lifetime_taxes)

        self._set_currency_row("ending_pre_tax", original.ending_pre_tax, changed.ending_pre_tax)
        self._set_currency_row("ending_after_tax", original.ending_after_tax, changed.ending_after_tax)
        self._set_currency_row("ending_roth", original.ending_roth, changed.ending_roth)
        self._set_currency_row("ending_hsa", original.ending_hsa, changed.ending_hsa)

        self._rebuild_assumptions(view_model)


    def _rebuild_assumptions(self, view_model):
        for widget in self.assumptions_frame.winfo_children():
            widget.destroy()

        frame = self.assumptions_frame
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Assumption", font=self.changed_label_font).grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        ttk.Label(frame, text="Original", font=self.changed_label_font).grid(
            row=0, column=1, sticky="e", padx=4
        )
        ttk.Label(frame, text="Changed", font=self.changed_label_font).grid(
            row=0, column=2, sticky="e", padx=(4, 0)
        )

        original = view_model.original_assumptions
        changed = view_model.changed_assumptions

        row = 1
        row = self._add_assumption_section(frame, row, "Husband")
        row = self._add_assumption_original_only_row(frame, row, "Age", original.husband_age)
        row = self._add_assumption_row(
            frame, row, "Retirement Age", original.husband_retire_age, changed.husband_retire_age, "age"
        )
        row = self._add_assumption_row(
            frame, row, "Social Security Age", original.husband_ss_age, changed.husband_ss_age, "age"
        )

        if original.wife_age is not None and changed.wife_age is not None:
            row = self._add_assumption_section(frame, row, "Wife")
            row = self._add_assumption_original_only_row(frame, row, "Age", original.wife_age)
            row = self._add_assumption_row(
                frame, row, "Retirement Age", original.wife_retire_age, changed.wife_retire_age, "age"
            )
            row = self._add_assumption_row(
                frame, row, "Social Security Age", original.wife_ss_age, changed.wife_ss_age, "age"
            )

        row = self._add_assumption_row(
            frame, row, "Inflation Rate", original.inflation_rate, changed.inflation_rate, "percent", indent=0
        )
        row = self._add_assumption_row(
            frame, row, "Fund Expenses", original.fund_expense, changed.fund_expense, "percent", indent=0
        )
        row = self._add_assumption_row(
            frame, row, "Market Adjustment", original.market_adjustment, changed.market_adjustment, "percent", indent=0
        )
        row = self._add_assumption_row(
            frame, row, original.dynamic_label, original.dynamic_value, changed.dynamic_value, "percent", indent=0
        )
        row = self._add_assumption_row(frame, row, "Stock", original.stock, changed.stock, "percent", indent=0)
        row = self._add_assumption_row(frame, row, "Bonds", original.bonds, changed.bonds, "percent", indent=0)
        self._add_assumption_row(frame, row, "Cash", original.cash, changed.cash, "percent", indent=0)


    def _add_assumption_section(self, parent, row, label):
        ttk.Label(parent, text=label, font=("Arial", 10, "bold")).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(7, 2)
        )
        return row + 1


    def _add_assumption_original_only_row(self, parent, row, label, value):
        ttk.Label(parent, text=label, font=self.normal_label_font).grid(
            row=row, column=0, sticky="w", padx=(12, 10), pady=2
        )
        ttk.Label(parent, text=f"{value:g}", anchor="e").grid(
            row=row, column=1, sticky="e", padx=4, pady=2
        )
        return row + 1


    def _add_assumption_row(self, parent, row, label, original, changed, value_type, indent=12):
        is_changed = abs(float(changed) - float(original)) > 1e-9
        changed_style = "ScenarioChangedResult.TLabel"
        if not is_changed:
            changed_style = "TLabel"

        ttk.Label(parent, text=label, font=self.normal_label_font).grid(
            row=row, column=0, sticky="w", padx=(indent, 10), pady=2
        )

        if value_type == "age":
            original_text = f"{original:g}"
            changed_text = f"{changed:g}"
        else:
            original_text = f"{original:.2f}%"
            changed_text = f"{changed:.2f}%"

        ttk.Label(parent, text=original_text, anchor="e", font=self.normal_label_font).grid(
            row=row, column=1, sticky="e", padx=4, pady=2
        )

        if is_changed:
            changed_font = self.changed_label_font
        else:
            changed_font = self.normal_label_font

        ttk.Label(parent, text=changed_text, anchor="e", font=changed_font, style=changed_style).grid(
            row=row, column=2, sticky="e", padx=(4, 0), pady=2
        )

        return row + 1


    def _set_currency_row(self, key, original, changed, negative_red=False, positive_red=False):
        if abs(original) < 0.5:
            original = 0.0

        if abs(changed) < 0.5:
            changed = 0.0

        is_changed = abs(float(changed) - float(original)) > 1e-9
        original_style = "TLabel"
        changed_style = "TLabel"

        if (negative_red and original < 0) or (positive_red and original > 0):
            original_style = "ScenarioChangedResult.TLabel"

        if is_changed:
            changed_style = "ScenarioChangedResult.TLabel"
        elif (negative_red and changed < 0) or (positive_red and changed > 0):
            changed_style = "ScenarioChangedResult.TLabel"

        self.metric_rows[key]["original"].configure(text=f"${original:,.0f}", style=original_style)
        self.metric_rows[key]["changed"].configure(text=f"${changed:,.0f}", style=changed_style)

    def _set_percent_row(self, key, original, changed):
        if original is None or changed is None:
            self.metric_rows[key]["original"].configure(text="-", style="TLabel")
            self.metric_rows[key]["changed"].configure(text="-", style="TLabel")
            return

        is_changed = abs(float(changed) - float(original)) > 1e-9
        changed_style = "TLabel"

        if is_changed:
            changed_style = "ScenarioChangedResult.TLabel"

        self.metric_rows[key]["original"].configure(text=f"{original:.1f}%", style="TLabel")
        self.metric_rows[key]["changed"].configure(text=f"{changed:.1f}%", style=changed_style)
