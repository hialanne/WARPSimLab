import tkinter as tk
from tkinter import ttk


class RealEstateEditFrame(ttk.Frame):
    """
    Edit real estate values for Husband and optional Wife.
    Real estate remains stored on the Portfolio object.
    """

    def __init__(
        self,
        parent,
        husband_portfolio,
        wife_portfolio=None,
        title="Real Estate",
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
            text="Defines real estate value used by the simulation and balance sheet calculations.  Represents actual worth after loans.",
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
        self.h_real_estate_var = tk.StringVar(
            value=self._format_money(self.husband_portfolio.real_estate)
        )

        self.w_real_estate_var = None
        if self.wife_portfolio:
            self.w_real_estate_var = tk.StringVar(
                value=self._format_money(self.wife_portfolio.real_estate)
            )

        self.total_real_estate_var = tk.StringVar(value="--")

    def _build_fields(self):
        row = 1

        ttk.Label(self, text="Husband", font=("Arial", 12, "bold")).grid(
            row=row, column=1, sticky="w", padx=(30, 0), pady=(10, 5)
        )

        if self.wife_portfolio:
            ttk.Label(self, text="Wife", font=("Arial", 12, "bold")).grid(
                row=row, column=2, sticky="w", padx=(30, 0), pady=(10, 5)
            )

        ttk.Label(self, text="Total", font=("Arial", 12, "bold")).grid(
            row=row, column=3, sticky="w", padx=(30, 0), pady=(10, 5)
        )

        row += 1

        ttk.Label(self, text="Real Estate").grid(
            row=row, column=0, sticky="w", padx=5, pady=2
        )

        vcmd_h = (
            self.register(self._validate_real_estate_on_focusout),
            "%P",
            "husband",
        )

        ttk.Entry(
            self,
            textvariable=self.h_real_estate_var,
            width=14,
            validate="focusout",
            validatecommand=vcmd_h,
        ).grid(row=row, column=1, sticky="w", padx=5)

        if self.wife_portfolio:
            vcmd_w = (
                self.register(self._validate_real_estate_on_focusout),
                "%P",
                "wife",
            )

            ttk.Entry(
                self,
                textvariable=self.w_real_estate_var,
                width=14,
                validate="focusout",
                validatecommand=vcmd_w,
            ).grid(row=row, column=2, sticky="w", padx=5)

        ttk.Entry(
            self,
            textvariable=self.total_real_estate_var,
            width=14,
            state="readonly",
            style="Derived.TEntry",
        ).grid(row=row, column=3, sticky="w", padx=5)

    def _validate_real_estate_on_focusout(self, proposed_value, person_key):
        portfolio = self.husband_portfolio if person_key == "husband" else self.wife_portfolio
        var = self.h_real_estate_var if person_key == "husband" else self.w_real_estate_var

        try:
            parsed = self._parse_money(proposed_value)
            portfolio.real_estate = parsed

            self.after_idle(lambda: var.set(self._format_money(parsed)))
            self.after_idle(self._update_totals)
            return True

        except ValueError:
            current_value = portfolio.real_estate

            self.after_idle(lambda: var.set(self._format_money(current_value)))
            self.after_idle(self._update_totals)
            self.bell()
            return True

    def _update_totals(self):
        husband_value = self.husband_portfolio.real_estate
        wife_value = self.wife_portfolio.real_estate if self.wife_portfolio else 0.0

        self.total_real_estate_var.set(
            self._format_money(husband_value + wife_value)
        )