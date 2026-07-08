import tkinter as tk
from tkinter import ttk


class DerivedStatisticsFrame(ttk.Frame):
    """
    Read-only balance sheet and portfolio statistics.
    """

    def __init__(
        self,
        parent,
        husband_portfolio,
        wife_portfolio=None,
        title="Derived Statistics",
        mode="Advanced",
        **kwargs
    ):
        super().__init__(parent, padding=10, **kwargs)

        self.husband_portfolio = husband_portfolio
        self.wife_portfolio = wife_portfolio
        self.mode = mode

        style = ttk.Style()
        style.configure("Derived.TEntry", foreground="#555555")

        ttk.Label(
            self,
            text="Read-only derived statistics calculated from portfolio and real estate values.",
            font=("Arial", 11),
            wraplength=700,
            justify="left",
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self.vars = {}
        self._build_fields()
        self._update_statistics()

    def _format_money(self, value):
        return f"{float(value):,.0f}"

    def _format_pct(self, value):
        return f"{float(value):5.1f}%"

    def _portfolio_value(self, portfolio, key):
        if portfolio is None:
            return 0.0
        return float(getattr(portfolio, key, 0.0))

    def _hsa_total(self, portfolio):
        if portfolio is None:
            return 0.0

        return (
            self._portfolio_value(portfolio, "hsa_cash") +
            self._portfolio_value(portfolio, "hsa_equity") +
            self._portfolio_value(portfolio, "hsa_bond")
        )

    def _combined(self, key):
        return (
            self._portfolio_value(self.husband_portfolio, key) +
            self._portfolio_value(self.wife_portfolio, key)
        )

    def _combined_hsa(self):
        return self._hsa_total(self.husband_portfolio) + self._hsa_total(self.wife_portfolio)

    def _build_fields(self):
        row = 1

        ttk.Label(self, text="Balance Sheet Summary", font=("Arial", 12, "bold")).grid(
            row=row, column=0, sticky="w", pady=(10, 5)
        )
        row += 1

        for label, key in [
            ("Investable Assets", "investable_assets"),
            ("Real Estate", "real_estate"),
            ("Total Wealth", "total_wealth"),
        ]:
            self._add_readonly_row(row, label, key)
            row += 1

        row += 1

        ttk.Label(self, text="Tax Bucket Percentages", font=("Arial", 12, "bold")).grid(
            row=row, column=0, sticky="w", pady=(10, 5)
        )
        row += 1

        for label, key in [
            ("Pre-Tax", "pct_pre"),
            ("After-Tax", "pct_post"),
            ("Roth", "pct_roth"),
            ("HSA", "pct_hsa"),
        ]:
            self._add_readonly_row(row, label, key)
            row += 1

        row += 1

        ttk.Label(self, text="Asset Class Percentages", font=("Arial", 12, "bold")).grid(
            row=row, column=0, sticky="w", pady=(10, 5)
        )
        row += 1

        for label, key in [
            ("Stocks", "pct_equity"),
            ("Bonds", "pct_bonds"),
            ("Cash", "pct_cash"),
        ]:
            self._add_readonly_row(row, label, key)
            row += 1

    def _add_readonly_row(self, row, label_text, key):
        ttk.Label(self, text=label_text).grid(
            row=row, column=0, sticky="w", padx=5, pady=2
        )

        var = tk.StringVar(value="--")
        self.vars[key] = var

        ttk.Entry(
            self,
            textvariable=var,
            width=18,
            state="readonly",
            style="Derived.TEntry",
        ).grid(row=row, column=1, sticky="w", padx=10)

    def _safe_pct(self, numerator, denominator):
        if denominator <= 0:
            return "--"
        return self._format_pct(numerator / denominator * 100.0)

    def _update_statistics(self):
        equity_total = (
            self._combined("equity_pre") +
            self._combined("equity_post") +
            self._combined("equity_roth") +
            self._combined("hsa_equity")
        )

        bond_total = (
            self._combined("bond_pre") +
            self._combined("bond_post") +
            self._combined("bond_roth") +
            self._combined("hsa_bond")
        )

        cash_total = (
            self._combined("cash_pre") +
            self._combined("cash_post") +
            self._combined("cash_roth") +
            self._combined("hsa_cash")
        )

        pre_total = (
            self._combined("equity_pre") +
            self._combined("bond_pre") +
            self._combined("cash_pre")
        )

        post_total = (
            self._combined("equity_post") +
            self._combined("bond_post") +
            self._combined("cash_post")
        )

        roth_total = (
            self._combined("equity_roth") +
            self._combined("bond_roth") +
            self._combined("cash_roth")
        )

        hsa_total = self._combined_hsa()

        investable_assets = equity_total + bond_total + cash_total
        real_estate = self._combined("real_estate")
        total_wealth = investable_assets + real_estate

        self.vars["investable_assets"].set(self._format_money(investable_assets))
        self.vars["real_estate"].set(self._format_money(real_estate))
        self.vars["total_wealth"].set(self._format_money(total_wealth))

        self.vars["pct_pre"].set(self._safe_pct(pre_total, investable_assets))
        self.vars["pct_post"].set(self._safe_pct(post_total, investable_assets))
        self.vars["pct_roth"].set(self._safe_pct(roth_total, investable_assets))
        self.vars["pct_hsa"].set(self._safe_pct(hsa_total, investable_assets))

        self.vars["pct_equity"].set(self._safe_pct(equity_total, investable_assets))
        self.vars["pct_bonds"].set(self._safe_pct(bond_total, investable_assets))
        self.vars["pct_cash"].set(self._safe_pct(cash_total, investable_assets))