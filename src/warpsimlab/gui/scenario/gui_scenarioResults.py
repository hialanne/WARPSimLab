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
        self.rowconfigure(1, weight=1, minsize=150)

        self.metric_rows = {}
        self.normal_label_font = tkfont.nametofont("TkDefaultFont").copy()
        self.changed_label_font = self.normal_label_font.copy()
        self.changed_label_font.configure(weight="bold")

        results_frame = ttk.Frame(self)
        results_frame.grid(row=0, column=0, sticky="ew")
        results_frame.columnconfigure(0, weight=1)

        self.results_table = results_frame
        self._build_results_table()

        assumptions_group = ttk.LabelFrame(
            self, text="Assumptions", padding=6, style="ScenarioResults.TLabelframe"
        )

        assumptions_group.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        assumptions_group.columnconfigure(0, weight=1)
        assumptions_group.rowconfigure(0, weight=1)

        self.assumptions_canvas = tk.Canvas(assumptions_group, highlightthickness=0, height=150)        
        assumptions_scrollbar = ttk.Scrollbar(assumptions_group, orient="vertical",
                                              command=self.assumptions_canvas.yview)
        self.assumptions_canvas.configure(yscrollcommand=assumptions_scrollbar.set)

        self.assumptions_canvas.grid(row=0, column=0, sticky="nsew")
        assumptions_scrollbar.grid(row=0, column=1, sticky="ns")

        self.assumptions_frame = ttk.Frame(self.assumptions_canvas)
        self.assumptions_window = self.assumptions_canvas.create_window(
            (0, 0), window=self.assumptions_frame, anchor="nw"
        )

        self.assumptions_frame.bind("<Configure>", self._on_assumptions_frame_configure)
        self.assumptions_canvas.bind("<Configure>", self._on_assumptions_canvas_configure)


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
        row = self._add_metric_row(table, row, "depletion_rate", "Depletion Rate")

        row = self._add_section(table, row, "Cash Flow Results")
        row = self._add_metric_row(table, row, "ending_cash_flow", "Ending Net Cash Flow")
        row = self._add_metric_row(table, row, "lifetime_shortfall", "Lifetime Shortfall")
        row = self._add_metric_row(table, row, "lifetime_taxes", "Lifetime Taxes")

        row = self._add_section(table, row, "Ending Assets")
        row = self._add_metric_row(table, row, "ending_pre_tax", "Pre-Tax Assets")
        row = self._add_metric_row(table, row, "ending_after_tax", "After-Tax Assets")
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


    def _on_assumptions_frame_configure(self, _event=None):
        self.assumptions_canvas.configure(scrollregion=self.assumptions_canvas.bbox("all"))


    def _on_assumptions_canvas_configure(self, event):
        self.assumptions_canvas.itemconfigure(self.assumptions_window, width=event.width)


    def update_results(self, baseline_results, scenario_results):
        if baseline_results is None or scenario_results is None:
            return

        baseline = baseline_results["p"]["summary_results"]
        scenario = scenario_results["p"]["summary_results"]

        self._set_currency_row("ending_portfolio", baseline["total_assets"][-1], scenario["total_assets"][-1])
        self._set_percent_row("depletion_rate", baseline["simulated_shortfall_rate"], scenario["simulated_shortfall_rate"])

        self._set_currency_row("ending_cash_flow", baseline["net_cash_flow"][-1], scenario["net_cash_flow"][-1])
        self._set_currency_row("lifetime_shortfall", sum(baseline["cash_flow_shortfall"]), sum(scenario["cash_flow_shortfall"]))
        self._set_currency_row("lifetime_taxes", sum(baseline["taxes"]), sum(scenario["taxes"]))

        self._set_currency_row("ending_pre_tax", baseline["pre_tax_assets"][-1], scenario["pre_tax_assets"][-1])
        self._set_currency_row("ending_after_tax", baseline["post_tax_assets"][-1], scenario["post_tax_assets"][-1])
        self._set_currency_row("ending_roth", baseline["roth_assets"][-1], scenario["roth_assets"][-1])
        self._set_currency_row("ending_hsa", baseline["hsa_assets"][-1], scenario["hsa_assets"][-1])

        self._rebuild_assumptions(baseline_results, scenario_results)


    def _rebuild_assumptions(self, baseline_results, scenario_results):
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

        baseline_sim = baseline_results["sim_config"]
        scenario_sim = scenario_results["sim_config"]
        baseline_snap = baseline_results["retirement_snapshots"]
        scenario_snap = scenario_results["retirement_snapshots"]
        baseline_husband = baseline_results["husband"]
        scenario_husband = scenario_results["husband"]
        baseline_wife = baseline_results["wife"]
        scenario_wife = scenario_results["wife"]

        row = 1
        row = self._add_assumption_section(frame, row, "Husband")
        row = self._add_assumption_row(frame, row, "Retirement Age", baseline_husband.retire_age,
                                       scenario_husband.retire_age, "age")
        row = self._add_assumption_row(frame, row, "Social Security Age", baseline_husband.ss_age,
                                       scenario_husband.ss_age, "age")

        if baseline_wife is not None and scenario_wife is not None:
            row = self._add_assumption_section(frame, row, "Wife")
            row = self._add_assumption_row(frame, row, "Retirement Age", baseline_wife.retire_age,
                                           scenario_wife.retire_age, "age")
            row = self._add_assumption_row(frame, row, "Social Security Age", baseline_wife.ss_age,
                                           scenario_wife.ss_age, "age")

        row = self._add_assumption_row(frame, row, "Inflation Rate", baseline_sim.inflation_rate * 100,
                                       scenario_sim.inflation_rate * 100, "percent")
        row = self._add_assumption_row(frame, row, "Fund Expenses", baseline_sim.fund_expense * 100,
                                       scenario_sim.fund_expense * 100, "percent")
        row = self._add_assumption_row(frame, row, "Market Adjustment", baseline_snap.historical_data_multiplier,
                                       scenario_snap.historical_data_multiplier, "percent")

        if baseline_sim.always_use_expense_mode:
            row = self._add_assumption_row(frame, row, "Expense Multiplier",
                                           baseline_sim.scenario_expense_multiplier * 100,
                                           scenario_sim.scenario_expense_multiplier * 100, "percent")
        else:
            row = self._add_assumption_row(frame, row, "Withdrawal Rate", baseline_sim.retirement_withdraw_pct,
                                           scenario_sim.retirement_withdraw_pct, "percent")

        row = self._add_assumption_row(frame, row, "Stock", baseline_sim.custom_stock * 100,
                                       scenario_sim.custom_stock * 100, "percent")
        row = self._add_assumption_row(frame, row, "Bonds", baseline_sim.custom_bonds * 100,
                                       scenario_sim.custom_bonds * 100, "percent")
        self._add_assumption_row(frame, row, "Cash", baseline_sim.custom_cash * 100,
                                 scenario_sim.custom_cash * 100, "percent")


    def _add_assumption_section(self, parent, row, label):
        ttk.Label(parent, text=label, font=("Arial", 10, "bold")).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(7, 2)
        )
        return row + 1


    def _add_assumption_row(self, parent, row, label, original, changed, value_type):
        is_changed = abs(float(changed) - float(original)) > 1e-9
        font = self.changed_label_font if is_changed else self.normal_label_font

        ttk.Label(parent, text=label, font=font).grid(row=row, column=0, sticky="w", padx=(12, 10), pady=2)

        if value_type == "age":
            original_text = f"{original:g}"
            changed_text = f"{changed:g}"
        else:
            original_text = f"{original:.2f}%"
            changed_text = f"{changed:.2f}%"

        ttk.Label(parent, text=original_text, anchor="e").grid(row=row, column=1, sticky="e", padx=4, pady=2)
        ttk.Label(parent, text=changed_text, anchor="e", font=font).grid(
            row=row, column=2, sticky="e", padx=(4, 0), pady=2
        )
        return row + 1


    def _set_currency_row(self, key, original, changed):
        self.metric_rows[key]["original"].configure(text=f"${original:,.0f}")
        self.metric_rows[key]["changed"].configure(text=f"${changed:,.0f}")


    def _set_percent_row(self, key, original, changed):
        if original is None or changed is None:
            self.metric_rows[key]["original"].configure(text="-")
            self.metric_rows[key]["changed"].configure(text="-")
            return

        self.metric_rows[key]["original"].configure(text=f"{original:.1f}%")
        self.metric_rows[key]["changed"].configure(text=f"{changed:.1f}%")
