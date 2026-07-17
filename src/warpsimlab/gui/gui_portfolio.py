import tkinter as tk
from tkinter import ttk

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

        style = ttk.Style()
        style.configure("Derived.TEntry", foreground="#555555")

        ttk.Label(
            self,
            text="Defines investable portfolio balances used by the simulation. Real estate is entered separately.",
            font=("Arial", 11),
            wraplength=700,
            justify="left",
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        self._init_vars()
        self._build_fields()
        self._update_totals()

    def _format_money(self, value):
        return f"{float(value):,.0f}"

    def _parse_money(self, raw_value):
        text = str(raw_value).strip().replace(",", "")

        if text == "":
            raise ValueError("Blank value is not allowed.")

        if text in {"-", "+", ".", "-.", "+."}:
            raise ValueError("Invalid number.")

        if "e" in text.lower():
            raise ValueError("Scientific notation not allowed.")

        value = float(text)

        if value < 0:
            raise ValueError("Value cannot be negative.")

        return value

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

            "hsa": tk.StringVar(value=self._format_money(self._get_hsa_total(self.husband_portfolio))),
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

                "hsa": tk.StringVar(value=self._format_money(self._get_hsa_total(self.wife_portfolio))),
            }

        self.row_total_vars = {}
        self.column_total_vars = {
            "husband": tk.StringVar(value="--"),
            "wife": tk.StringVar(value="--"),
            "total": tk.StringVar(value="--"),
        }

    def _get_hsa_total(self, portfolio):
        return (
            float(getattr(portfolio, "hsa_cash", 0.0)) +
            float(getattr(portfolio, "hsa_equity", 0.0)) +
            float(getattr(portfolio, "hsa_bond", 0.0))
        )

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
                ("Savings", "cash_post"),
            ]
        else:
            fields = [
                ("Stocks Pre-Tax", "equity_pre"),
                ("Stocks After-Tax", "equity_post"),
                ("Stocks Roth", "equity_roth"),
                ("", None),

                ("Bonds Pre-Tax", "bond_pre"),
                ("Bonds After-Tax", "bond_post"),
                ("Bonds Roth", "bond_roth"),
                ("", None),

                ("Cash Pre-Tax", "cash_pre"),
                ("Cash After-Tax", "cash_post"),
                ("Cash Roth", "cash_roth"),
                ("", None),

                ("HSA", "hsa"),
            ]

        for label_text, key in fields:
            if key is None:
                ttk.Label(self, text="").grid(row=row, column=0, pady=3)
                row += 1
                continue

            self._add_money_row(row, label_text, key)
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
            style="Derived.TEntry",
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

        row += 1

        ttk.Label(
            self,
            text=(
                "Note: HSA is shown as one row. Internally, the edited HSA value is currently stored as HSA cash.\n\n"
                "HSA accounts are modeled as separate asset buckets. This release does not model new HSA\n"
                " contributions, qualified medical expenses, or detailed HSA tax treatment."
            ),
            font=("Arial", 12, "italic"),
            foreground="#555555",
        ).grid(row=row, column=0, columnspan=4, sticky="w", padx=10, pady=(12, 0))

    def _add_money_row(self, row, label_text, key):
        ttk.Label(self, text=label_text).grid(
            row=row, column=0, sticky="w", padx=5, pady=2
        )

        vcmd_h = (
            self.register(self._validate_portfolio_field_on_focusout),
            "%P",
            "husband",
            key,
        )

        ttk.Entry(
            self,
            textvariable=self.h_vars[key],
            width=14,
            validate="focusout",
            validatecommand=vcmd_h,
        ).grid(row=row, column=1, sticky="w", padx=5)

        if self.w_vars:
            vcmd_w = (
                self.register(self._validate_portfolio_field_on_focusout),
                "%P",
                "wife",
                key,
            )

            ttk.Entry(
                self,
                textvariable=self.w_vars[key],
                width=14,
                validate="focusout",
                validatecommand=vcmd_w,
            ).grid(row=row, column=2, sticky="w", padx=5)

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

        try:
            parsed = self._parse_money(proposed_value)

            if field_key == "hsa":
                self._set_hsa_as_cash_only(portfolio, parsed)
            else:
                setattr(portfolio, field_key, parsed)

            self.after_idle(lambda: var.set(self._format_money(parsed)))
            self.after_idle(self._update_totals)
            return True

        except ValueError:
            if field_key == "hsa":
                current_value = self._get_hsa_total(portfolio)
            else:
                current_value = getattr(portfolio, field_key)

            self.after_idle(lambda: var.set(self._format_money(current_value)))
            self.after_idle(self._update_totals)
            self.bell()
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