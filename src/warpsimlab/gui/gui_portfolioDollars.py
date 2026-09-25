# gui_portfolioDollars.py

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox

from src.warpsimlab.gui.gui_validation import mark_validation_failed, parse_finite_float
from src.warpsimlab.utils.tooltip import Tooltip
from src.warpsimlab.gui.gui_utils import bind_entry_commit_on_return
from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin


class PortfolioDollarsEditFrame(ScalableFrameMixin, ttk.Frame):
    """
    Edit investable portfolio balances for Husband and optional Wife.

    This screen intentionally excludes real estate and derived statistics.
    Real estate is edited in gui_realEstate.py.
    Derived statistics are displayed read-only in gui_derivedStatistics.py.
    """


    def __init__(
        self,
        parent,
        husband_portfolio,
        wife_portfolio=None,
        title="Portfolio Data",
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
        self._column_header_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._major_header_font = tkfont.Font(root=self, family="Arial", size=12, weight="bold")
        self._tooltip_font = tkfont.Font(root=self, family="Arial", size=11)

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._header_font)
        self._register_scalable_font(self._header_text_font)
        self._register_scalable_font(self._column_header_font)
        self._register_scalable_font(self._major_header_font)
        self._register_scalable_font(self._tooltip_font)
        self._bucket_padding = (14, 10)
        self._bucket_horizontal_gap = 25
        self._bucket_vertical_gap = 18
        self._bucket_label_minsize = 75
        self._footer_label_minsize = 140
        self._bucket_cell_padx = 8
        self._apply_gui_scale()

        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        ttk.Label(
            header_frame, text="Balance Sheet > Portfolio Amounts", font=self._header_font
        ).pack(side="left")

        ttk.Label(
            header_frame,
            text=(
                " - Defines investable portfolio balances used by the simulation. "
                "Real estate is entered separately."
            ),
            font=self._header_text_font,
        ).pack(side="left")

        self._init_vars()
        self._build_fields()
        self._update_totals()


    def _apply_scaled_styles(self):
        style = ttk.Style(self)
        style.configure("PortfolioDollars.TLabelframe.Label", font=self._column_header_font)

        scale = self._get_gui_scale()
        self._scaled_bucket_padding = (
            max(1, round(self._bucket_padding[0] * scale)),
            max(1, round(self._bucket_padding[1] * scale)),
        )
        self._scaled_bucket_horizontal_gap = max(1, round(self._bucket_horizontal_gap * scale))
        self._scaled_bucket_vertical_gap = max(1, round(self._bucket_vertical_gap * scale))
        self._scaled_bucket_label_minsize = max(1, round(self._bucket_label_minsize * scale))
        self._scaled_footer_label_minsize = max(1, round(self._footer_label_minsize * scale))
        self._scaled_bucket_cell_padx = max(1, round(self._bucket_cell_padx * scale))


    def _format_money(self, value):
        return f"{float(value):,.0f}"


    def _parse_money(self, raw_value):
        return parse_finite_float(raw_value, allow_commas=True, allow_scientific=False, minimum=0)


    def _portfolio_field_label(self, field_key):
        labels = {
            "equity_pre": "Stocks Tax-Deferred",
            "equity_post": "Stocks Taxable",
            "equity_roth": "Stocks Roth",
            "bond_pre": "Bonds Tax-Deferred",
            "bond_post": "Bonds Taxable",
            "bond_roth": "Bonds Roth",
            "cash_pre": "Cash Tax-Deferred",
            "cash_post": "Cash Taxable",
            "cash_roth": "Cash Roth",
            "hsa_equity": "Stocks HSA",
            "hsa_bond": "Bonds HSA",
            "hsa_cash": "Cash HSA",
        }
        return labels.get(field_key, field_key)


    def _init_vars(self):
        self.h_vars = {
            "equity_pre": tk.StringVar(value=self._format_money(self.husband_portfolio.equity_pre)),
            "equity_post": tk.StringVar(value=self._format_money(self.husband_portfolio.equity_post)),
            "equity_roth": tk.StringVar(value=self._format_money(self.husband_portfolio.equity_roth)),
            "bond_pre": tk.StringVar(value=self._format_money(self.husband_portfolio.bond_pre)),
            "bond_post": tk.StringVar(value=self._format_money(self.husband_portfolio.bond_post)),
            "bond_roth": tk.StringVar(value=self._format_money(self.husband_portfolio.bond_roth)),
            "cash_pre": tk.StringVar(value=self._format_money(self.husband_portfolio.cash_pre)),
            "cash_post": tk.StringVar(value=self._format_money(self.husband_portfolio.cash_post)),
            "cash_roth": tk.StringVar(value=self._format_money(self.husband_portfolio.cash_roth)),
            "hsa_equity": tk.StringVar(value=self._format_money(self.husband_portfolio.hsa_equity)),
            "hsa_bond": tk.StringVar(value=self._format_money(self.husband_portfolio.hsa_bond)),
            "hsa_cash": tk.StringVar(value=self._format_money(self.husband_portfolio.hsa_cash)),
        }

        self.w_vars = None
        if self.wife_portfolio:
            self.w_vars = {
                "equity_pre": tk.StringVar(value=self._format_money(self.wife_portfolio.equity_pre)),
                "equity_post": tk.StringVar(value=self._format_money(self.wife_portfolio.equity_post)),
                "equity_roth": tk.StringVar(value=self._format_money(self.wife_portfolio.equity_roth)),
                "bond_pre": tk.StringVar(value=self._format_money(self.wife_portfolio.bond_pre)),
                "bond_post": tk.StringVar(value=self._format_money(self.wife_portfolio.bond_post)),
                "bond_roth": tk.StringVar(value=self._format_money(self.wife_portfolio.bond_roth)),
                "cash_pre": tk.StringVar(value=self._format_money(self.wife_portfolio.cash_pre)),
                "cash_post": tk.StringVar(value=self._format_money(self.wife_portfolio.cash_post)),
                "cash_roth": tk.StringVar(value=self._format_money(self.wife_portfolio.cash_roth)),
                "hsa_equity": tk.StringVar(value=self._format_money(self.wife_portfolio.hsa_equity)),
                "hsa_bond": tk.StringVar(value=self._format_money(self.wife_portfolio.hsa_bond)),
                "hsa_cash": tk.StringVar(value=self._format_money(self.wife_portfolio.hsa_cash)),
            }

        self.bucket_total_vars = {}
        self.row_total_vars = {}
        self.column_total_vars = {
            "husband": tk.StringVar(value="--"),
            "wife": tk.StringVar(value="--"),
            "total": tk.StringVar(value="--"),
        }


    def _set_hsa_as_cash_only(self, portfolio, value):
        portfolio.hsa_cash = value
        portfolio.hsa_equity = 0.0
        portfolio.hsa_bond = 0.0


    def _build_fields(self):
        row = 1

        if self.mode == "Basic":
            ttk.Label(self, text="Husband", font=self._major_header_font).grid(
                row=row, column=1, sticky="w", padx=(30, 0), pady=(10, 5)
            )

            if self.w_vars:
                ttk.Label(self, text="Wife", font=self._major_header_font).grid(
                    row=row, column=2, sticky="w", padx=(30, 0), pady=(10, 5)
                )

            ttk.Label(self, text="Household", font=self._major_header_font).grid(
                row=row, column=3, sticky="w", padx=(30, 0), pady=(10, 5)
            )

            row += 1
            self._add_money_row(row, "Savings", "cash_post", "Cash and savings held outside retirement accounts")
            row += 1

            ttk.Separator(self, orient="horizontal").grid(
                row=row, column=0, columnspan=4, sticky="ew", pady=(8, 6)
            )
            row += 1

            ttk.Label(self, text="TOTAL", font=self._major_header_font).grid(
                row=row, column=0, sticky="w", padx=5, pady=2
            )

            ttk.Entry(
                self, textvariable=self.column_total_vars["husband"], width=12, font=self._body_font,
                state="readonly", style="Derived.TEntry"
            ).grid(row=row, column=1, sticky="w", padx=5)

            if self.w_vars:
                ttk.Entry(
                    self, textvariable=self.column_total_vars["wife"], width=12, font=self._body_font,
                    state="readonly", style="Derived.TEntry"
                ).grid(row=row, column=2, sticky="w", padx=5)

            ttk.Entry(
                self, textvariable=self.column_total_vars["total"], width=12, font=self._body_font,
                state="readonly", style="Derived.TEntry"
            ).grid(row=row, column=3, sticky="w", padx=5)

            return

        buckets = {
            "pre": (
                "Tax-Deferred",
                [
                    ("Stocks", "equity_pre", "Stock investments held in tax-deferred retirement accounts"),
                    ("Bonds", "bond_pre", "Bond investments held in tax-deferred retirement accounts"),
                    ("Cash", "cash_pre", "Cash held in tax-deferred retirement accounts"),
                ],
            ),
            "post": (
                "Taxable",
                [
                    ("Stocks", "equity_post", "Stock investments held in taxable accounts"),
                    ("Bonds", "bond_post", "Bond investments held in taxable accounts"),
                    ("Cash", "cash_post", "Cash and savings held in taxable accounts"),
                ],
            ),
            "roth": (
                "Roth",
                [
                    ("Stocks", "equity_roth", "Stock investments held in Roth retirement accounts"),
                    ("Bonds", "bond_roth", "Bond investments held in Roth retirement accounts"),
                    ("Cash", "cash_roth", "Cash held in Roth retirement accounts"),
                ],
            ),
            "hsa": (
                "HSA",
                [
                    ("Stocks", "hsa_equity", "Stock investments held in HSA accounts"),
                    ("Bonds", "hsa_bond", "Bond investments held in HSA accounts"),
                    ("Cash", "hsa_cash", "Cash held in HSA accounts"),
                ],
            ),
        }

        blocks = (
            ("pre", 0, 0),
            ("post", 0, 1),
            ("roth", 1, 0),
            ("hsa", 1, 1),
        )

        self.columnconfigure(0, weight=1)

        portfolio_grid = ttk.Frame(self)
        portfolio_grid.grid(row=row, column=0, columnspan=4, sticky="ew", padx=(5, 20), pady=(10, 0))
        portfolio_grid.columnconfigure(0, weight=1, uniform="portfolio_bucket")
        portfolio_grid.columnconfigure(1, weight=1, uniform="portfolio_bucket")

        for bucket_key, grid_row, grid_column in blocks:
            bucket_label, fields = buckets[bucket_key]

            if grid_column == 0:
                bucket_padx = (0, self._scaled_bucket_horizontal_gap)
            else:
                bucket_padx = (self._scaled_bucket_horizontal_gap, 0)

            if grid_row == 0:
                bucket_pady = (0, self._scaled_bucket_vertical_gap)
            else:
                bucket_pady = (0, 0)

            bucket_frame = ttk.LabelFrame(
                portfolio_grid, text=bucket_label, padding=self._scaled_bucket_padding,
                style="PortfolioDollars.TLabelframe"
            )
            bucket_frame.grid(
                row=grid_row, column=grid_column, sticky="nsew",
                padx=bucket_padx, pady=bucket_pady
            )

            bucket_frame.columnconfigure(0, minsize=self._scaled_bucket_label_minsize)
            bucket_frame.columnconfigure(1, weight=1, uniform=f"{bucket_key}_person")
            bucket_frame.columnconfigure(2, weight=1, uniform=f"{bucket_key}_person")
            bucket_frame.columnconfigure(3, weight=1, uniform=f"{bucket_key}_person")

            ttk.Label(bucket_frame, text="Husband", font=self._column_header_font).grid(
                row=0, column=1, sticky="w", padx=self._scaled_bucket_cell_padx, pady=(0, 5)

            )

            if self.w_vars:
                ttk.Label(bucket_frame, text="Wife", font=self._column_header_font).grid(
                    row=0, column=2, sticky="w", padx=self._scaled_bucket_cell_padx, pady=(0, 5)
                )

            ttk.Label(bucket_frame, text="Household", font=self._column_header_font).grid(
                row=0, column=3, sticky="w", padx=self._scaled_bucket_cell_padx, pady=(0, 5)
            )

            for field_row, (label_text, key, tooltip_text) in enumerate(fields, start=1):
                ttk.Label(bucket_frame, text=label_text, font=self._body_font).grid(
                    row=field_row, column=0, sticky="w", padx=(0, 10), pady=3
                )

                vcmd_h = self.register(self._validate_portfolio_field_on_focusout), "%P", "husband", key
                entry_h = ttk.Entry(
                    bucket_frame, textvariable=self.h_vars[key], width=12, font=self._body_font,
                    validate="focusout", validatecommand=vcmd_h
                )
                entry_h.grid(row=field_row, column=1, sticky="ew", padx=self._scaled_bucket_cell_padx)
                bind_entry_commit_on_return(entry_h)
                Tooltip(entry_h, tooltip_text, font=self._tooltip_font)

                if self.w_vars:
                    vcmd_w = self.register(self._validate_portfolio_field_on_focusout), "%P", "wife", key
                    entry_w = ttk.Entry(
                        bucket_frame, textvariable=self.w_vars[key], width=12, font=self._body_font,
                        validate="focusout", validatecommand=vcmd_w
                    )
                    entry_w.grid(row=field_row, column=2, sticky="ew", padx=self._scaled_bucket_cell_padx)
                    bind_entry_commit_on_return(entry_w)
                    Tooltip(entry_w, tooltip_text, font=self._tooltip_font)

                total_var = tk.StringVar(value="--")
                self.row_total_vars[key] = total_var
                ttk.Entry(
                    bucket_frame, textvariable=total_var, width=12, font=self._column_header_font,
                    state="readonly", style="Derived.TEntry"
                ).grid(row=field_row, column=3, sticky="ew", padx=self._scaled_bucket_cell_padx)

            bucket_vars = {
                "husband": tk.StringVar(value="--"),
                "wife": tk.StringVar(value="--"),
                "total": tk.StringVar(value="--"),
            }
            self.bucket_total_vars[bucket_key] = bucket_vars

            ttk.Label(bucket_frame, text="Total", font=self._column_header_font).grid(
                row=4, column=0, sticky="w", padx=(0, 10), pady=(5, 0)
            )

            ttk.Entry(
                bucket_frame, textvariable=bucket_vars["husband"], width=12, font=self._body_font,
                state="readonly", style="Derived.TEntry"
            ).grid(row=4, column=1, sticky="ew", padx=self._scaled_bucket_cell_padx, pady=(5, 0))

            if self.w_vars:
                ttk.Entry(
                    bucket_frame, textvariable=bucket_vars["wife"], width=12, font=self._body_font,
                    state="readonly", style="Derived.TEntry"
                ).grid(row=4, column=2, sticky="ew", padx=self._scaled_bucket_cell_padx, pady=(5, 0))

            ttk.Entry(
                bucket_frame, textvariable=bucket_vars["total"], width=12, font=self._column_header_font,
                state="readonly", style="Derived.TEntry"
            ).grid(row=4, column=3, sticky="ew", padx=self._scaled_bucket_cell_padx, pady=(5, 0))

        footer_frame = ttk.Frame(portfolio_grid)
        footer_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        footer_frame.columnconfigure(0, minsize=self._scaled_footer_label_minsize)
        footer_frame.columnconfigure(1, weight=1, uniform="portfolio_total")
        footer_frame.columnconfigure(2, weight=1, uniform="portfolio_total")
        footer_frame.columnconfigure(3, weight=1, uniform="portfolio_total")

        ttk.Separator(footer_frame, orient="horizontal").grid(
            row=0, column=0, columnspan=4, sticky="ew", pady=(0, 10)
        )

        ttk.Label(footer_frame, text="Portfolio Total", font=self._major_header_font).grid(
            row=1, column=0, sticky="w", padx=(5, 15)
        )
        ttk.Label(footer_frame, text="Husband", font=self._column_header_font).grid(
            row=1, column=1, sticky="w", padx=15
        )

        if self.w_vars:
            ttk.Label(footer_frame, text="Wife", font=self._column_header_font).grid(
                row=1, column=2, sticky="w", padx=15
            )

        ttk.Label(footer_frame, text="Household", font=self._column_header_font).grid(
            row=1, column=3, sticky="w", padx=15
        )

        ttk.Entry(
            footer_frame, textvariable=self.column_total_vars["husband"], width=12, font=self._body_font,
            state="readonly", style="Derived.TEntry"
        ).grid(row=2, column=1, sticky="ew", padx=15, pady=(5, 0))

        if self.w_vars:
            ttk.Entry(
                footer_frame, textvariable=self.column_total_vars["wife"], width=12, font=self._body_font,
                state="readonly", style="Derived.TEntry"
            ).grid(row=2, column=2, sticky="ew", padx=15, pady=(5, 0))

        ttk.Entry(
            footer_frame, textvariable=self.column_total_vars["total"], width=12, font=self._body_font,
            state="readonly", style="Derived.TEntry"
        ).grid(row=2, column=3, sticky="ew", padx=15, pady=(5, 0))


    def _add_money_row(self, row, label_text, key, tooltip_text):
        ttk.Label(self, text=label_text, font=self._body_font).grid(
            row=row, column=0, sticky="w", padx=5, pady=2
        )

        vcmd_h = self.register(self._validate_portfolio_field_on_focusout), "%P", "husband", key
        entry_h = ttk.Entry(
            self, textvariable=self.h_vars[key], width=14, font=self._body_font,
            validate="focusout", validatecommand=vcmd_h
        )
        entry_h.grid(row=row, column=1, sticky="w", padx=5)
        bind_entry_commit_on_return(entry_h)
        Tooltip(entry_h, tooltip_text, font=self._tooltip_font)

        if self.w_vars:
            vcmd_w = self.register(self._validate_portfolio_field_on_focusout), "%P", "wife", key
            entry_w = ttk.Entry(
                self, textvariable=self.w_vars[key], width=14, font=self._body_font,
                validate="focusout", validatecommand=vcmd_w
            )
            entry_w.grid(row=row, column=2, sticky="w", padx=5)
            bind_entry_commit_on_return(entry_w)
            Tooltip(entry_w, tooltip_text, font=self._tooltip_font)

        total_var = tk.StringVar(value="--")
        self.row_total_vars[key] = total_var

        ttk.Entry(
            self, textvariable=total_var, width=14, font=self._body_font,
            state="readonly", style="Derived.TEntry"
        ).grid(row=row, column=3, sticky="w", padx=5)


    def _validate_portfolio_field_on_focusout(self, proposed_value, person_key, field_key):
        portfolio = self.husband_portfolio if person_key == "husband" else self.wife_portfolio
        vars_dict = self.h_vars if person_key == "husband" else self.w_vars
        var = vars_dict[field_key]
        person_label = "Husband" if person_key == "husband" else "Wife"
        field_label = self._portfolio_field_label(field_key)

        try:
            parsed = self._parse_money(proposed_value)

            setattr(portfolio, field_key, parsed)
            self.after_idle(lambda: var.set(self._format_money(parsed)))
            self.after_idle(self._update_totals)
            return True

        except ValueError as exc:
            current_value = getattr(portfolio, field_key)

            self.after_idle(lambda: var.set(self._format_money(current_value)))
            self.after_idle(self._update_totals)
            mark_validation_failed(self)
            messagebox.showerror(
                "Invalid Input",
                f"Portfolio / {person_label} / {field_label}: {exc}",
                parent=self.winfo_toplevel(),
            )
            return True


    def _get_var_value(self, vars_dict, key):
        if vars_dict is None:
            return 0.0

        try:
            return self._parse_money(vars_dict[key].get())
        except Exception:
            return 0.0


    def _update_totals(self):
        husband_total = 0.0
        wife_total = 0.0

        for key, total_var in self.row_total_vars.items():
            h_value = self._get_var_value(self.h_vars, key)
            w_value = self._get_var_value(self.w_vars, key) if self.w_vars else 0.0

            husband_total += h_value
            wife_total += w_value
            total_var.set(self._format_money(h_value + w_value))

        bucket_fields = {
            "pre": ("equity_pre", "bond_pre", "cash_pre"),
            "post": ("equity_post", "bond_post", "cash_post"),
            "roth": ("equity_roth", "bond_roth", "cash_roth"),
            "hsa": ("hsa_equity", "hsa_bond", "hsa_cash"),
        }

        for bucket_key, bucket_vars in self.bucket_total_vars.items():
            keys = bucket_fields[bucket_key]
            h_value = sum(self._get_var_value(self.h_vars, key) for key in keys)
            w_value = sum(self._get_var_value(self.w_vars, key) for key in keys) if self.w_vars else 0.0

            bucket_vars["husband"].set(self._format_money(h_value))
            bucket_vars["wife"].set(self._format_money(w_value) if self.w_vars else "--")
            bucket_vars["total"].set(self._format_money(h_value + w_value))

        household_total = husband_total + wife_total

        self.column_total_vars["husband"].set(self._format_money(husband_total))
        self.column_total_vars["wife"].set(self._format_money(wife_total) if self.w_vars else "--")
        self.column_total_vars["total"].set(self._format_money(household_total))