# gui_portfolio.py

import tkinter as tk
from tkinter import ttk, messagebox

from src.warpsimlab.gui.gui_validation import mark_validation_failed, parse_finite_float
from src.warpsimlab.utils.tooltip import Tooltip


class PortfolioEditFrame(ttk.Frame):
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

        header_frame = ttk.Frame(self)
        header_frame.grid(
            row=0,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(0, 8),
        )

        ttk.Label(
            header_frame,
            text="Balance Sheet > Portfolio",
            font=("Arial", 11, "bold"),
        ).pack(side="left")

        ttk.Label(
            header_frame,
            text=(
                " - Defines investable portfolio balances used by the simulation. "
                "Real estate is entered separately."
            ),
            font=("Arial", 11),
        ).pack(side="left")

        self._init_vars()
        self._build_fields()
        self._update_totals()

    def _format_money(self, value):
        return f"{float(value):,.0f}"


    def _parse_money(self, raw_value):
        return parse_finite_float(
            raw_value, allow_commas=True, allow_scientific=False, minimum=0
        )


    def _portfolio_field_label(self, field_key):
        labels = {
            "equity_pre": "Stocks Pre-Tax",
            "equity_post": "Stocks After-Tax",
            "equity_roth": "Stocks Roth",
            "bond_pre": "Bonds Pre-Tax",
            "bond_post": "Bonds After-Tax",
            "bond_roth": "Bonds Roth",
            "cash_pre": "Cash Pre-Tax",
            "cash_post": "Cash After-Tax",
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

        ttk.Label(self, text="Husband", font=("Arial", 12, "bold")).grid(
            row=row, column=1, sticky="w", padx=(30, 0), pady=(10, 5)
        )

        if self.w_vars:
            ttk.Label(self, text="Wife", font=("Arial", 12, "bold")).grid(
                row=row, column=2, sticky="w", padx=(30, 0), pady=(10, 5)
            )

        ttk.Label(self, text="Total", font=("Arial", 12, "bold")).grid(
            row=row, column=3, sticky="w", padx=(30, 0), pady=(10, 5)
        )

        row += 1

        if self.mode == "Basic":
            fields = [
                (
                    "Savings",
                    "cash_post",
                    "Cash and savings held outside retirement accounts",
                ),
            ]
        else:
            fields = [
                (
                    "Stocks Pre-Tax",
                    "equity_pre",
                    "Stock investments held in tax-deferred retirement accounts",
                ),
                (
                    "Stocks After-Tax",
                    "equity_post",
                    "Stock investments held in taxable accounts",
                ),
                (
                    "Stocks Roth",
                    "equity_roth",
                    "Stock investments held in Roth retirement accounts",
                ),
                (
                    "Stocks HSA",
                    "hsa_equity",
                    "Stock investments held in HSA accounts",
                ),
                ("", None, None),

                (
                    "Bonds Pre-Tax",
                    "bond_pre",
                    "Bond investments held in tax-deferred retirement accounts",
                ),
                (
                    "Bonds After-Tax",
                    "bond_post",
                    "Bond investments held in taxable accounts",
                ),
                (
                    "Bonds Roth",
                    "bond_roth",
                    "Bond investments held in Roth retirement accounts",
                ),
                (
                    "Bonds HSA",
                    "hsa_bond",
                    "Bond investments held in HSA accounts",
                ),
                ("", None, None),

                (
                    "Cash Pre-Tax",
                    "cash_pre",
                    "Cash held in tax-deferred retirement accounts",
                ),
                (
                    "Cash After-Tax",
                    "cash_post",
                    "Cash and savings held in taxable accounts",
                ),
                (
                    "Cash Roth",
                    "cash_roth",
                    "Cash held in Roth retirement accounts",
                ),
                (
                    "Cash HSA",
                    "hsa_cash",
                    "Cash held in HSA accounts",
                ),
            ]

        for label_text, key, tooltip_text in fields:
            if key is None:
                ttk.Label(self, text="").grid(row=row, column=0, pady=3)
                row += 1
                continue

            self._add_money_row(row, label_text, key, tooltip_text)

            row += 1

        ttk.Separator(self, orient="horizontal").grid(
            row=row,
            column=0,
            columnspan=4,
            sticky="ew",
            pady=(8, 6)
        )
        row += 1

        ttk.Label(self, text="TOTAL", font=("Arial", 12, "bold")).grid(
            row=row, column=0, sticky="w", padx=5, pady=2
        )

        ttk.Entry(
            self,
            textvariable=self.column_total_vars["husband"],
            width=14,
            state="readonly",
        ).grid(row=row, column=1, sticky="w", padx=5)

        if self.w_vars:
            ttk.Entry(
                self,
                textvariable=self.column_total_vars["wife"],
                width=14,
                state="readonly",
                style="Derived.TEntry",
            ).grid(row=row, column=2, sticky="w", padx=5)

        ttk.Entry(
            self,
            textvariable=self.column_total_vars["total"],
            width=14,
            state="readonly",
            style="Derived.TEntry",
        ).grid(row=row, column=3, sticky="w", padx=5)


    def _add_money_row(self, row, label_text, key, tooltip_text):
        ttk.Label(self, text=label_text).grid(
            row=row, column=0, sticky="w", padx=5, pady=2
        )

        vcmd_h = (
            self.register(self._validate_portfolio_field_on_focusout),
            "%P",
            "husband",
            key,
        )

        entry_h = ttk.Entry(
            self,
            textvariable=self.h_vars[key],
            width=14,
            validate="focusout",
            validatecommand=vcmd_h,
        )
        entry_h.grid(row=row, column=1, sticky="w", padx=5)
        Tooltip(entry_h, tooltip_text, font=("Arial", 11))

        if self.w_vars:
            vcmd_w = (
                self.register(self._validate_portfolio_field_on_focusout),
                "%P",
                "wife",
                key,
            )

            entry_w = ttk.Entry(
                self,
                textvariable=self.w_vars[key],
                width=14,
                validate="focusout",
                validatecommand=vcmd_w,
            )
            entry_w.grid(row=row, column=2, sticky="w", padx=5)
            Tooltip(entry_w, tooltip_text, font=("Arial", 11))

        total_var = tk.StringVar(value="--")
        self.row_total_vars[key] = total_var

        ttk.Entry(
            self,
            textvariable=total_var,
            width=14,
            state="readonly",
            style="Derived.TEntry",
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

        household_total = husband_total + wife_total

        self.column_total_vars["husband"].set(self._format_money(husband_total))
        self.column_total_vars["wife"].set(self._format_money(wife_total) if self.w_vars else "--")
        self.column_total_vars["total"].set(self._format_money(household_total))