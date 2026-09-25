# gui_realEstate.py

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox

from src.warpsimlab.gui.gui_validation import mark_validation_failed, parse_finite_float
from src.warpsimlab.utils.tooltip import Tooltip
from src.warpsimlab.gui.gui_utils import bind_entry_commit_on_return
from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin


class RealEstateEditFrame(ScalableFrameMixin, ttk.Frame):
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

        self._body_font = tkfont.nametofont("TkDefaultFont").copy()
        self._header_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._header_text_font = tkfont.Font(root=self, family="Arial", size=11)
        self._major_header_font = tkfont.Font(root=self, family="Arial", size=12, weight="bold")
        self._tooltip_font = tkfont.Font(root=self, family="Arial", size=11)

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._header_font)
        self._register_scalable_font(self._header_text_font)
        self._register_scalable_font(self._major_header_font)
        self._register_scalable_font(self._tooltip_font)
        self._apply_gui_scale()

        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        ttk.Label(
            header_frame, text="Balance Sheet > Real Estate", font=self._header_font
        ).pack(side="left")

        ttk.Label(
            header_frame,
            text=(
                " - Defines real estate value used by the simulation and balance "
                "sheet calculations. Represents actual worth after loans."
            ),
            font=self._header_text_font,
        ).pack(side="left")

        self._init_vars()
        self._build_fields()
        self._update_totals()

    def _format_money(self, value):
        return f"{float(value):,.0f}"

    def _parse_money(self, raw_value):
        return parse_finite_float(raw_value, allow_commas=True, allow_scientific=False, minimum=0)

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

        ttk.Label(self, text="Husband", font=self._major_header_font).grid(
            row=row, column=1, sticky="w", padx=(30, 0), pady=(10, 5)
        )

        if self.wife_portfolio:
            ttk.Label(self, text="Wife", font=self._major_header_font).grid(
                row=row, column=2, sticky="w", padx=(30, 0), pady=(10, 5)
            )

        ttk.Label(self, text="Total", font=self._major_header_font).grid(
            row=row, column=3, sticky="w", padx=(30, 0), pady=(10, 5)
        )

        row += 1

        ttk.Label(self, text="Real Estate", font=self._body_font).grid(
            row=row, column=0, sticky="w", padx=5, pady=2
        )

        vcmd_h = self.register(self._validate_real_estate_on_focusout), "%P", "husband"

        tooltip_text = (
            "Current net real estate value after subtracting mortgages "
            "and other property loans"
        )

        entry_h = ttk.Entry(
            self, textvariable=self.h_real_estate_var, width=14, font=self._body_font,
            validate="focusout", validatecommand=vcmd_h
        )
        entry_h.grid(row=row, column=1, sticky="w", padx=5)
        bind_entry_commit_on_return(entry_h)
        Tooltip(entry_h, tooltip_text, font=self._tooltip_font)

        if self.wife_portfolio:
            vcmd_w = self.register(self._validate_real_estate_on_focusout), "%P", "wife"

            entry_w = ttk.Entry(
                self, textvariable=self.w_real_estate_var, width=14, font=self._body_font,
                validate="focusout", validatecommand=vcmd_w
            )
            entry_w.grid(row=row, column=2, sticky="w", padx=5)
            bind_entry_commit_on_return(entry_w)
            Tooltip(entry_w, tooltip_text, font=self._tooltip_font)

        ttk.Entry(
            self, textvariable=self.total_real_estate_var, width=14, font=self._body_font,
            state="readonly"
        ).grid(row=row, column=3, sticky="w", padx=5)

    def _validate_real_estate_on_focusout(self, proposed_value, person_key):
        if person_key == "husband":
            portfolio = self.husband_portfolio
            var = self.h_real_estate_var
            person_label = "Husband"
        else:
            portfolio = self.wife_portfolio
            var = self.w_real_estate_var
            person_label = "Wife"

        try:
            parsed = self._parse_money(proposed_value)
            portfolio.real_estate = parsed

            self.after_idle(lambda: var.set(self._format_money(parsed)))
            self.after_idle(self._update_totals)
            return True

        except ValueError as exc:
            current_value = portfolio.real_estate

            self.after_idle(lambda: var.set(self._format_money(current_value)))
            self.after_idle(self._update_totals)
            mark_validation_failed(self)
            messagebox.showerror(
                "Invalid Input", f"Real Estate / {person_label}: {exc}", parent=self.winfo_toplevel()
            )
            return True

    def _update_totals(self):
        husband_value = self.husband_portfolio.real_estate

        if self.wife_portfolio:
            wife_value = self.wife_portfolio.real_estate
        else:
            wife_value = 0.0

        self.total_real_estate_var.set(self._format_money(husband_value + wife_value))