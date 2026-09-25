# gui_derivedStatistics.py

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin


class DerivedStatisticsFrame(ScalableFrameMixin, ttk.Frame):
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

        self._body_font = tkfont.nametofont("TkDefaultFont").copy()
        self._header_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._header_text_font = tkfont.Font(root=self, family="Arial", size=11)
        self._section_font = tkfont.Font(root=self, family="Arial", size=10, weight="bold")
        self._total_font = tkfont.Font(root=self, family="Arial", size=10, weight="bold")

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._header_font)
        self._register_scalable_font(self._header_text_font)
        self._register_scalable_font(self._section_font)
        self._register_scalable_font(self._total_font)
        self._apply_gui_scale()

        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Label(
            header_frame, text="Balance Sheet > Derived Statistics", font=self._header_font
        ).pack(side="left")

        ttk.Label(
            header_frame,
            text=(
                " - Displays read-only statistics calculated from portfolio "
                "and real estate values."
            ),
            font=self._header_text_font,
        ).pack(side="left")

        self.vars = {}
        self._build_fields()
        self._update_statistics()

    def _apply_scaled_styles(self):
        style = ttk.Style(self)
        style.configure("DerivedStatistics.TLabelframe.Label", font=self._section_font)
        style.configure("DerivedStatisticsTotal.TEntry", font=self._total_font)

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
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        summary_frame = ttk.LabelFrame(
            self, text="Balance Sheet Summary", padding=6,
            style="DerivedStatistics.TLabelframe"
        )
        summary_frame.grid(row=1, column=0, sticky="nsew", padx=(5, 20), pady=(10, 8))

        owners = [("Husband", "husband")]
        if self.wife_portfolio is not None:
            owners.append(("Wife", "wife"))
        owners.append(("Household", "household"))

        for col, (text, owner) in enumerate(owners, start=1):
            ttk.Label(summary_frame, text=text, font=self._section_font).grid(
                row=0, column=col, sticky="w", padx=8, pady=(0, 5)
            )

        pct_col = len(owners) + 1
        ttk.Label(summary_frame, text="% Wealth", font=self._section_font).grid(
            row=0, column=pct_col, sticky="w", padx=8, pady=(0, 5)
        )

        for row, (label, key, bold) in enumerate([
            ("Investable Assets", "investable", False),
            ("Real Estate", "real_estate", False),
            ("Total Wealth", "wealth", True),
        ], start=1):
            if bold:
                label_font = self._section_font
            else:
                label_font = self._body_font

            ttk.Label(summary_frame, text=label, font=label_font).grid(
                row=row, column=0, sticky="w", padx=8, pady=2
            )

            for col, (text, owner) in enumerate(owners, start=1):
                self._add_value_entry(summary_frame, row, col, f"summary_{key}_{owner}", bold=bold)

            self._add_value_entry(summary_frame, row, pct_col, f"summary_{key}_pct", width=10, bold=bold)

        overall_frame = ttk.LabelFrame(
            self, text="Overall Asset Allocation", padding=6,
            style="DerivedStatistics.TLabelframe"
        )
        overall_frame.grid(row=1, column=1, sticky="nsew", padx=(20, 5), pady=(10, 8))

        ttk.Label(overall_frame, text="Dollars", font=self._section_font).grid(
            row=0, column=1, sticky="w", padx=8, pady=(0, 5)
        )
        ttk.Label(overall_frame, text="% Portfolio", font=self._section_font).grid(
            row=0, column=2, sticky="w", padx=8, pady=(0, 5)
        )

        for row, (label, key, bold) in enumerate([
            ("Stocks", "stocks", False),
            ("Bonds", "bonds", False),
            ("Cash", "cash", False),
            ("Total", "total", True),
        ], start=1):
            if bold:
                label_font = self._section_font
            else:
                label_font = self._body_font

            ttk.Label(overall_frame, text=label, font=label_font).grid(
                row=row, column=0, sticky="w", padx=8, pady=2
            )
            self._add_value_entry(overall_frame, row, 1, f"overall_{key}_dollars", bold=bold)
            self._add_value_entry(overall_frame, row, 2, f"overall_{key}_pct", width=10, bold=bold)

        bucket_frame = ttk.LabelFrame(
            self, text="Portfolio by Tax Bucket", padding=6,
            style="DerivedStatistics.TLabelframe"
        )
        bucket_frame.grid(row=2, column=0, columnspan=2, sticky="nw", padx=5, pady=8)

        for col, text in enumerate(["", "Dollars", "% Portfolio", "Stocks", "Bonds", "Cash"]):
            if text:
                ttk.Label(bucket_frame, text=text, font=self._section_font).grid(
                    row=0, column=col, sticky="w", padx=8, pady=(0, 5)
                )

        for row, (label, key, bold) in enumerate([
            ("Tax-Deferred", "pre", False),
            ("Taxable", "post", False),
            ("Roth", "roth", False),
            ("HSA", "hsa", False),
            ("Total", "total", True),
        ], start=1):
            if bold:
                label_font = self._section_font
            else:
                label_font = self._body_font

            ttk.Label(bucket_frame, text=label, font=label_font).grid(
                row=row, column=0, sticky="w", padx=8, pady=2
            )
            self._add_value_entry(bucket_frame, row, 1, f"bucket_{key}_dollars", bold=bold)
            self._add_value_entry(bucket_frame, row, 2, f"bucket_{key}_portfolio_pct", width=10, bold=bold)
            self._add_value_entry(bucket_frame, row, 3, f"bucket_{key}_stocks_pct", width=10, bold=bold)
            self._add_value_entry(bucket_frame, row, 4, f"bucket_{key}_bonds_pct", width=10, bold=bold)
            self._add_value_entry(bucket_frame, row, 5, f"bucket_{key}_cash_pct", width=10, bold=bold)

    def _add_value_entry(self, parent, row, column, key, width=14, bold=False):
        var = tk.StringVar(value="--")
        self.vars[key] = var

        if bold:
            entry = ttk.Entry(
                parent, textvariable=var, width=width, font=self._total_font,
                state="readonly", style="DerivedStatisticsTotal.TEntry"
            )
        else:
            entry = ttk.Entry(
                parent, textvariable=var, width=width, font=self._body_font,
                state="readonly"
            )

        entry.grid(row=row, column=column, sticky="w", padx=8, pady=2)

    def _bucket_components(self, portfolio, bucket):
        fields = {
            "pre": ("equity_pre", "bond_pre", "cash_pre"),
            "post": ("equity_post", "bond_post", "cash_post"),
            "roth": ("equity_roth", "bond_roth", "cash_roth"),
            "hsa": ("hsa_equity", "hsa_bond", "hsa_cash"),
        }
        return tuple(self._portfolio_value(portfolio, key) for key in fields[bucket])

    def _person_statistics(self, portfolio):
        buckets = {
            bucket: self._bucket_components(portfolio, bucket)
            for bucket in ("pre", "post", "roth", "hsa")
        }
        stocks = sum(values[0] for values in buckets.values())
        bonds = sum(values[1] for values in buckets.values())
        cash = sum(values[2] for values in buckets.values())
        investable = stocks + bonds + cash
        real_estate = self._portfolio_value(portfolio, "real_estate")

        return {
            "buckets": buckets,
            "stocks": stocks,
            "bonds": bonds,
            "cash": cash,
            "investable": investable,
            "real_estate": real_estate,
            "wealth": investable + real_estate,
        }

    def _safe_pct(self, numerator, denominator):
        if denominator <= 0:
            return "--"

        return self._format_pct(numerator / denominator * 100.0)

    def _update_statistics(self):
        husband = self._person_statistics(self.husband_portfolio)
        wife = self._person_statistics(self.wife_portfolio)
        household = {}

        for key in ("stocks", "bonds", "cash", "investable", "real_estate", "wealth"):
            household[key] = husband[key] + wife[key]

        household["buckets"] = {
            bucket: tuple(
                husband["buckets"][bucket][i] + wife["buckets"][bucket][i]
                for i in range(3)
            )
            for bucket in ("pre", "post", "roth", "hsa")
        }

        for key in ("investable", "real_estate", "wealth"):
            self.vars[f"summary_{key}_husband"].set(self._format_money(husband[key]))

            if self.wife_portfolio is not None:
                self.vars[f"summary_{key}_wife"].set(self._format_money(wife[key]))

            self.vars[f"summary_{key}_household"].set(self._format_money(household[key]))
            self.vars[f"summary_{key}_pct"].set(
                self._safe_pct(household[key], household["wealth"])
            )

        for key in ("stocks", "bonds", "cash"):
            self.vars[f"overall_{key}_dollars"].set(self._format_money(household[key]))
            self.vars[f"overall_{key}_pct"].set(
                self._safe_pct(household[key], household["investable"])
            )

        self.vars["overall_total_dollars"].set(self._format_money(household["investable"]))
        self.vars["overall_total_pct"].set(
            self._safe_pct(household["investable"], household["investable"])
        )

        for bucket in ("pre", "post", "roth", "hsa"):
            stocks, bonds, cash = household["buckets"][bucket]
            bucket_total = stocks + bonds + cash

            self.vars[f"bucket_{bucket}_dollars"].set(self._format_money(bucket_total))
            self.vars[f"bucket_{bucket}_portfolio_pct"].set(
                self._safe_pct(bucket_total, household["investable"])
            )

            if bucket_total > 0:
                self.vars[f"bucket_{bucket}_stocks_pct"].set(
                    self._safe_pct(stocks, bucket_total)
                )
                self.vars[f"bucket_{bucket}_bonds_pct"].set(
                    self._safe_pct(bonds, bucket_total)
                )
                self.vars[f"bucket_{bucket}_cash_pct"].set(
                    self._safe_pct(cash, bucket_total)
                )
            else:
                self.vars[f"bucket_{bucket}_stocks_pct"].set("--")
                self.vars[f"bucket_{bucket}_bonds_pct"].set("--")
                self.vars[f"bucket_{bucket}_cash_pct"].set("--")

        self.vars["bucket_total_dollars"].set(self._format_money(household["investable"]))
        self.vars["bucket_total_portfolio_pct"].set(
            self._safe_pct(household["investable"], household["investable"])
        )
        self.vars["bucket_total_stocks_pct"].set(
            self._safe_pct(household["stocks"], household["investable"])
        )
        self.vars["bucket_total_bonds_pct"].set(
            self._safe_pct(household["bonds"], household["investable"])
        )
        self.vars["bucket_total_cash_pct"].set(
            self._safe_pct(household["cash"], household["investable"])
        )