# gui_portfolioPercentages.py

import tkinter as tk
from tkinter import ttk, messagebox

from src.warpsimlab.gui.gui_validation import parse_finite_float


class PortfolioPercentagesEditFrame(ttk.Frame):
    """
    Edit investable portfolio balances using total assets and percentage allocations.

    Percentages are temporary GUI state until Apply Percentages is pressed.
    The Portfolio objects remain the source of truth and continue storing dollar amounts.
    """

    TAX_BUCKETS = ("pre", "post", "roth", "hsa")
    ASSET_CLASSES = ("stocks", "bonds", "cash")

    TAX_LABELS = {
        "pre": "Pre-Tax",
        "post": "After-Tax",
        "roth": "Roth",
        "hsa": "HSA",
    }

    FIELD_MAP = {
        "pre": {"stocks": "equity_pre", "bonds": "bond_pre", "cash": "cash_pre"},
        "post": {"stocks": "equity_post", "bonds": "bond_post", "cash": "cash_post"},
        "roth": {"stocks": "equity_roth", "bonds": "bond_roth", "cash": "cash_roth"},
        "hsa": {"stocks": "hsa_equity", "bonds": "hsa_bond", "cash": "hsa_cash"},
    }

    def __init__(self, parent, husband_portfolio, wife_portfolio=None, title="Portfolio Percentages", mode="Advanced",
                 **kwargs):
        super().__init__(parent, padding=10, **kwargs)

        self.husband_portfolio = husband_portfolio
        self.wife_portfolio = wife_portfolio
        self.mode = mode

        self.total_vars = {}
        self.tax_vars = {}
        self.asset_vars = {}
        self.tax_total_vars = {}
        self.asset_total_vars = {}
        self.status_var = tk.StringVar(value="")

        self._build_fields()
        self._load_from_portfolios()
        self._attach_traces()
        self._update_display_totals()

    def _format_money(self, value):
        return f"{float(value):,.0f}"

    def _format_pct(self, value):
        return f"{float(value):.1f}"

    def _parse_money(self, value):
        return parse_finite_float(value, allow_commas=True, allow_scientific=False, minimum=0)

    def _parse_pct(self, value):
        parsed = parse_finite_float(value, allow_commas=False, allow_scientific=False, minimum=0)
        if parsed > 100.0:
            raise ValueError("percentage must be between 0 and 100")
        return parsed

    def _portfolio_value(self, portfolio, field):
        return float(getattr(portfolio, field, 0.0))

    def _bucket_values(self, portfolio, bucket):
        fields = self.FIELD_MAP[bucket]
        return [self._portfolio_value(portfolio, fields[asset]) for asset in self.ASSET_CLASSES]

    def _bucket_total(self, portfolio, bucket):
        return sum(self._bucket_values(portfolio, bucket))

    def _portfolio_total(self, portfolio):
        return sum(self._bucket_total(portfolio, bucket) for bucket in self.TAX_BUCKETS)

    def _split_percentages(self, values):
        total = sum(values)
        if total <= 0:
            return None

        percentages = [round(value / total * 100.0, 1) for value in values]
        difference = round(100.0 - sum(percentages), 1)

        if difference:
            largest_index = max(range(len(values)), key=lambda index: values[index])
            percentages[largest_index] = round(percentages[largest_index] + difference, 1)

        return percentages

    def _build_fields(self):
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, columnspan=7, sticky="w", pady=(0, 8))

        ttk.Label(header_frame, text="Balance Sheet > Portfolio - Percentages",
                  font=("Arial", 11, "bold")).pack(side="left")
        ttk.Label(header_frame,
                  text=" - Enter total investable assets, tax-bucket percentages, and asset allocation within each bucket.",
                  font=("Arial", 11)).pack(side="left")

        row = 1
        ttk.Label(self, text="Total Investable Assets", font=("Arial", 12, "bold")).grid(
            row=row, column=0, sticky="w", padx=5, pady=(10, 5)
        )

        self.total_vars["husband"] = tk.StringVar()
        ttk.Label(self, text="Husband", font=("Arial", 12, "bold")).grid(row=row, column=1, sticky="w", padx=5)
        ttk.Entry(self, textvariable=self.total_vars["husband"], width=14).grid(row=row + 1, column=1, sticky="w", padx=5)

        if self.wife_portfolio is not None:
            self.total_vars["wife"] = tk.StringVar()
            ttk.Label(self, text="Wife", font=("Arial", 12, "bold")).grid(row=row, column=2, sticky="w", padx=5)
            ttk.Entry(self, textvariable=self.total_vars["wife"], width=14).grid(row=row + 1, column=2, sticky="w", padx=5)

        row += 3
        ttk.Separator(self, orient="horizontal").grid(row=row, column=0, columnspan=7, sticky="ew", pady=(5, 8))
        row += 1

        ttk.Label(self, text="Tax Bucket Allocation", font=("Arial", 12, "bold")).grid(
            row=row, column=0, sticky="w", padx=5, pady=(5, 5)
        )
        row += 1

        ttk.Label(self, text="Tax Bucket").grid(row=row, column=0, sticky="w", padx=5)
        ttk.Label(self, text="Husband", font=("Arial", 11, "bold")).grid(row=row, column=1, sticky="w", padx=5)
        if self.wife_portfolio is not None:
            ttk.Label(self, text="Wife", font=("Arial", 11, "bold")).grid(row=row, column=2, sticky="w", padx=5)
        row += 1

        for bucket in self.TAX_BUCKETS:
            ttk.Label(self, text=self.TAX_LABELS[bucket]).grid(row=row, column=0, sticky="w", padx=5, pady=2)

            self.tax_vars[("husband", bucket)] = tk.StringVar()
            ttk.Entry(self, textvariable=self.tax_vars[("husband", bucket)], width=10).grid(
                row=row, column=1, sticky="w", padx=5
            )
            ttk.Label(self, text="%").grid(row=row, column=1, sticky="w", padx=(88, 0))

            if self.wife_portfolio is not None:
                self.tax_vars[("wife", bucket)] = tk.StringVar()
                ttk.Entry(self, textvariable=self.tax_vars[("wife", bucket)], width=10).grid(
                    row=row, column=2, sticky="w", padx=5
                )
                ttk.Label(self, text="%").grid(row=row, column=2, sticky="w", padx=(88, 0))

            row += 1

        ttk.Label(self, text="TOTAL", font=("Arial", 11, "bold")).grid(row=row, column=0, sticky="w", padx=5, pady=(4, 2))

        self.tax_total_vars["husband"] = tk.StringVar(value="--")
        ttk.Label(self, textvariable=self.tax_total_vars["husband"], font=("Arial", 11, "bold")).grid(
            row=row, column=1, sticky="w", padx=5
        )

        if self.wife_portfolio is not None:
            self.tax_total_vars["wife"] = tk.StringVar(value="--")
            ttk.Label(self, textvariable=self.tax_total_vars["wife"], font=("Arial", 11, "bold")).grid(
                row=row, column=2, sticky="w", padx=5
            )

        row += 2
        ttk.Separator(self, orient="horizontal").grid(row=row, column=0, columnspan=7, sticky="ew", pady=(5, 8))
        row += 1

        ttk.Label(self, text="Asset Allocation Within Each Tax Bucket", font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=7, sticky="w", padx=5, pady=(5, 5)
        )
        row += 1

        allocation_frame = ttk.Frame(self)
        allocation_frame.grid(row=row, column=0, columnspan=7, sticky="w", padx=5)

        husband_frame = ttk.LabelFrame(allocation_frame, text="Husband", padding=(10, 6))
        husband_frame.grid(row=0, column=0, sticky="nw")

        if self.wife_portfolio is not None:
            wife_frame = ttk.LabelFrame(allocation_frame, text="Wife", padding=(10, 6))
            wife_frame.grid(row=0, column=1, sticky="nw", padx=(40, 0))
        else:
            wife_frame = None

        for frame in (husband_frame, wife_frame):
            if frame is None:
                continue

            ttk.Label(frame, text="").grid(row=0, column=0, padx=5)
            for column, text in ((1, "Stocks"), (2, "Bonds"), (3, "Cash"), (4, "Total")):
                ttk.Label(frame, text=text).grid(row=0, column=column, sticky="w", padx=5)

        for bucket_row, bucket in enumerate(self.TAX_BUCKETS, start=1):
            ttk.Label(husband_frame, text=self.TAX_LABELS[bucket]).grid(
                row=bucket_row, column=0, sticky="w", padx=(5, 12), pady=3
            )

            for column, asset in enumerate(self.ASSET_CLASSES, start=1):
                self.asset_vars[("husband", bucket, asset)] = tk.StringVar()
                ttk.Entry(husband_frame, textvariable=self.asset_vars[("husband", bucket, asset)], width=8).grid(
                    row=bucket_row, column=column, sticky="w", padx=5
                )

            self.asset_total_vars[("husband", bucket)] = tk.StringVar(value="--")
            ttk.Label(husband_frame, textvariable=self.asset_total_vars[("husband", bucket)],
                      font=("Arial", 11, "bold")).grid(row=bucket_row, column=4, sticky="w", padx=5)

            if wife_frame is not None:
                ttk.Label(wife_frame, text=self.TAX_LABELS[bucket]).grid(
                    row=bucket_row, column=0, sticky="w", padx=(5, 12), pady=3
                )

                for column, asset in enumerate(self.ASSET_CLASSES, start=1):
                    self.asset_vars[("wife", bucket, asset)] = tk.StringVar()
                    ttk.Entry(wife_frame, textvariable=self.asset_vars[("wife", bucket, asset)], width=8).grid(
                        row=bucket_row, column=column, sticky="w", padx=5
                    )

                self.asset_total_vars[("wife", bucket)] = tk.StringVar(value="--")
                ttk.Label(wife_frame, textvariable=self.asset_total_vars[("wife", bucket)],
                          font=("Arial", 11, "bold")).grid(row=bucket_row, column=4, sticky="w", padx=5)

        row += 1

        ttk.Button(self, text="Apply Percentages", command=self._apply_percentages).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(12, 5)
        )
        ttk.Label(self, textvariable=self.status_var, font=("Arial", 11, "bold")).grid(
            row=row, column=2, columnspan=5, sticky="w", padx=5
        )

    def _load_from_portfolios(self):
        self._load_person_from_portfolio("husband", self.husband_portfolio)
        if self.wife_portfolio is not None:
            self._load_person_from_portfolio("wife", self.wife_portfolio)


    def _load_person_from_portfolio(self, person_key, portfolio):
        total = self._portfolio_total(portfolio)
        self.total_vars[person_key].set(self._format_money(total))

        bucket_totals = [self._bucket_total(portfolio, bucket) for bucket in self.TAX_BUCKETS]
        tax_percentages = self._split_percentages(bucket_totals)

        if tax_percentages is None:
            tax_percentages = [0.0, 0.0, 0.0, 0.0]

        for bucket, percentage in zip(self.TAX_BUCKETS, tax_percentages):
            self.tax_vars[(person_key, bucket)].set(self._format_pct(percentage))

            asset_percentages = self._split_percentages(self._bucket_values(portfolio, bucket))
            if asset_percentages is None:
                asset_percentages = [100.0, 0.0, 0.0]

            for asset, asset_percentage in zip(self.ASSET_CLASSES, asset_percentages):
                self.asset_vars[(person_key, bucket, asset)].set(self._format_pct(asset_percentage))


    def _attach_traces(self):
        for var in self.tax_vars.values():
            var.trace_add("write", self._on_percentage_changed)

        for var in self.asset_vars.values():
            var.trace_add("write", self._on_percentage_changed)


    def _on_percentage_changed(self, *_args):
        self.status_var.set("")
        self._update_display_totals()


    def _safe_percentage_total(self, variables):
        try:
            return sum(self._parse_pct(var.get()) for var in variables)
        except ValueError:
            return None


    def _update_display_totals(self):
        for person_key in self.total_vars:
            tax_total = self._safe_percentage_total([self.tax_vars[(person_key, bucket)] for bucket in self.TAX_BUCKETS])
            self.tax_total_vars[person_key].set("--" if tax_total is None else f"{tax_total:.1f}%")

            for bucket in self.TAX_BUCKETS:
                asset_total = self._safe_percentage_total(
                    [self.asset_vars[(person_key, bucket, asset)] for asset in self.ASSET_CLASSES]
                )
                self.asset_total_vars[(person_key, bucket)].set("--" if asset_total is None else f"{asset_total:.1f}%")


    def _validated_person_values(self, person_key):
        person_label = "Husband" if person_key == "husband" else "Wife"
        total = self._parse_money(self.total_vars[person_key].get())

        tax_percentages = {}
        for bucket in self.TAX_BUCKETS:
            tax_percentages[bucket] = self._parse_pct(self.tax_vars[(person_key, bucket)].get())

        tax_total = sum(tax_percentages.values())
        if abs(tax_total - 100.0) > 0.01:
            raise ValueError(f"{person_label} tax bucket percentages must total 100%. Current total: {tax_total:.1f}%")

        asset_percentages = {}
        for bucket in self.TAX_BUCKETS:
            asset_percentages[bucket] = {}
            for asset in self.ASSET_CLASSES:
                asset_percentages[bucket][asset] = self._parse_pct(self.asset_vars[(person_key, bucket, asset)].get())

            asset_total = sum(asset_percentages[bucket].values())
            if abs(asset_total - 100.0) > 0.01:
                bucket_label = self.TAX_LABELS[bucket]
                raise ValueError(
                    f"{person_label} {bucket_label} Stocks/Bonds/Cash percentages must total 100%. "
                    f"Current total: {asset_total:.1f}%"
                )

        updates = {}
        for bucket in self.TAX_BUCKETS:
            bucket_dollars = total * tax_percentages[bucket] / 100.0

            for asset in self.ASSET_CLASSES:
                field = self.FIELD_MAP[bucket][asset]
                updates[field] = bucket_dollars * asset_percentages[bucket][asset] / 100.0

        return updates


    def _apply_percentages(self):
        try:
            husband_updates = self._validated_person_values("husband")
            wife_updates = self._validated_person_values("wife") if self.wife_portfolio is not None else None

        except ValueError as exc:
            self.status_var.set("")
            messagebox.showerror("Invalid Portfolio Percentages", str(exc), parent=self.winfo_toplevel())
            return

        for field, value in husband_updates.items():
            setattr(self.husband_portfolio, field, value)

        if wife_updates is not None:
            for field, value in wife_updates.items():
                setattr(self.wife_portfolio, field, value)

        self._load_from_portfolios()
        self._update_display_totals()
        self.status_var.set("Portfolio updated.")