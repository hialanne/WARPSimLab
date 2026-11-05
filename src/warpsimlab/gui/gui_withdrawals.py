
# gui_withdrawals.py

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox

from src.warpsimlab.gui.gui_validation import mark_validation_failed, parse_finite_float
from src.warpsimlab.utils.tooltip import Tooltip
from src.warpsimlab.gui.gui_utils import bind_entry_commit_on_return
from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin


class WithdrawalsEditFrame(ScalableFrameMixin, ttk.Frame):
    def __init__(self, parent, control_vars, title="Withdrawal Strategies", **kwargs):
        super().__init__(parent, padding=10, **kwargs)

        self.controls = control_vars["_controls_dict"]
        self.title = title

        self._body_font = tkfont.nametofont("TkDefaultFont").copy()
        self._header_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._header_text_font = tkfont.Font(root=self, family="Arial", size=11)
        self._intro_font = tkfont.Font(root=self, family="Arial", size=11, slant="italic")
        self._tooltip_font = tkfont.Font(root=self, family="Arial", size=11)

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._header_font)
        self._register_scalable_font(self._header_text_font)
        self._register_scalable_font(self._intro_font)
        self._register_scalable_font(self._tooltip_font)
        self._apply_gui_scale()

        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(header_frame, text=f"Retirement > {title}", font=self._header_font).pack(side="left")

        content_frame = ttk.Frame(self)
        content_frame.grid(row=1, column=0, sticky="nw")
        self._row = 0
        self._add_use_mode_checkboxes(content_frame)
        self._add_withdrawal_controls(content_frame)


    def _apply_scaled_styles(self):
        style = ttk.Style(self)
        style.configure("Retirement.TCheckbutton", font=self._body_font)
        style.configure("Retirement.TMenubutton", font=self._body_font)

    def _next_row(self, which="left"):
        r = self._row
        self._row += 1
        return r

    def _add_use_mode_checkboxes(self, parent):
        INTRO_TEXT = (
            "Choose how to calculate withdrawals:\n"
            "- Use manually entered expenses\n"
            "- Use automatic retirement withdrawal rules"
        )

        ttk.Label(
            parent, text=INTRO_TEXT, justify="left", wraplength=400,
            font=self._intro_font
        ).grid(row=self._next_row("left"), column=0, sticky="w", pady=(0, 8))

        if "use_mode" not in self.controls:
            self.controls["use_mode"] = "expenses"

        self.use_expenses_var = tk.BooleanVar(value=(self.controls["use_mode"] == "expenses"))
        self.use_retirement_var = tk.BooleanVar(value=(self.controls["use_mode"] == "retirement"))

        def on_use_expenses_changed():
            if self.use_expenses_var.get():
                self.use_retirement_var.set(False)
                self.controls["use_mode"] = "expenses"
                self.controls["always_use_expense_mode"] = True
            else:
                if not self.use_retirement_var.get():
                    self.use_expenses_var.set(True)

            self._update_withdrawal_visibility()

        def on_use_retirement_changed():
            if self.use_retirement_var.get():
                self.use_expenses_var.set(False)
                self.controls["use_mode"] = "retirement"
                self.controls["always_use_expense_mode"] = False
            else:
                if not self.use_expenses_var.get():
                    self.use_retirement_var.set(True)

            self._update_withdrawal_visibility()

        self.use_expenses_cb = ttk.Checkbutton(
            parent, text="Use Manually Entered Expenses", variable=self.use_expenses_var,
            command=on_use_expenses_changed, style="Retirement.TCheckbutton"
        )
        self.use_expenses_cb.grid(row=self._next_row("left"), column=0, sticky="w", pady=2)

        Tooltip(
            self.use_expenses_cb,
            "If selected, withdrawals are taken from the amounts you manually entered in the Expenses tab.\n"
            "This mode uses income and expenses for the simulation.",
            font=self._tooltip_font
        )

        self.use_retirement_cb = ttk.Checkbutton(
            parent, text="Use Automatically Calculated Withdrawals", variable=self.use_retirement_var,
            command=on_use_retirement_changed, style="Retirement.TCheckbutton"
        )
        self.use_retirement_cb.grid(row=self._next_row("left"), column=0, sticky="w", pady=2)

        Tooltip(
            self.use_retirement_cb,
            "If selected, this mode withdraws money from your portfolio at a specified rate. "
            "This money is then spent.\n"
            "This simulates different withdrawal rates from a portfolio.",
            font=self._tooltip_font
        )

    def _add_withdrawal_controls(self, parent):
        if "retirement_withdraw_mode" not in self.controls:
            self.controls["retirement_withdraw_mode"] = "Percentage + Inflation"

        self.ret_mode_var = tk.StringVar(value=self.controls["retirement_withdraw_mode"])
        mode_options = [
            "Off",
            "Percentage",
            "Percentage + Inflation",
            "Fixed Dollar Amount",
            "Fixed Dollar Amount + Inflation"
        ]

        self.ret_mode_frame = ttk.Frame(parent)
        self.ret_mode_frame.grid(row=self._next_row("left"), column=0, columnspan=2, sticky="w", pady=5)

        ttk.Label(
            self.ret_mode_frame, text="Retirement Withdrawals Mode:", font=self._body_font
        ).pack(side="left")

        self.ret_mode_menu = ttk.OptionMenu(
            self.ret_mode_frame, self.ret_mode_var, self.ret_mode_var.get(), *mode_options,
            style="Retirement.TMenubutton"
        )
        self.ret_mode_menu.pack(side="left", padx=5)
        self.ret_mode_menu["menu"].configure(font=self._body_font)

        Tooltip(
            self.ret_mode_menu,
            "Percentage: withdraw a fixed % of portfolio per year\n"
            "Fixed Amount: withdraw a fixed dollar amount per year\n"
            "+ Inflation: adjusts the withdrawal for inflation\n"
            "Includes RMDs if enabled; uses after-tax funds if possible.",
            font=self._tooltip_font
        )

        def on_mode_change(*args):
            self.controls["retirement_withdraw_mode"] = self.ret_mode_var.get()

            if self.ret_mode_var.get() != "Off":
                state = "normal"
            else:
                state = "disabled"

            self.pct_entry.config(state=state)
            self.dollars_entry.config(state=state)

        self.ret_mode_var.trace_add("write", on_mode_change)

        if "retirement_withdraw_pct" not in self.controls:
            self.controls["retirement_withdraw_pct"] = 4.0

        self.pct_var = tk.StringVar(
            value=self._format_retirement_field(self.controls["retirement_withdraw_pct"])
        )

        self.pct_frame = ttk.Frame(parent)
        self.pct_frame.grid(row=self._next_row("left"), column=0, columnspan=2, sticky="w", pady=2)

        ttk.Label(
            self.pct_frame, text="Total Annual Withdrawal %:", font=self._body_font
        ).pack(side="left")

        vcmd = self.register(self._validate_retirement_field), "%P", "retirement_withdraw_pct"

        self.pct_entry = ttk.Entry(
            self.pct_frame, textvariable=self.pct_var, width=6, font=self._body_font,
            validate="focusout", validatecommand=vcmd
        )
        self.pct_entry.pack(side="left", padx=5)
        bind_entry_commit_on_return(self.pct_entry)

        Tooltip(
            self.pct_entry,
            "Enter the total annual withdrawal as a percentage of your portfolio.\n"
            "Used only if 'Use Manually Entered Expenses' is selected.",
            font=self._tooltip_font
        )

        if "retirement_withdraw_dollars" not in self.controls:
            self.controls["retirement_withdraw_dollars"] = 0.0

        self.dollars_var = tk.StringVar(
            value=self._format_retirement_dollars(self.controls["retirement_withdraw_dollars"])
        )

        self.dollars_frame = ttk.Frame(parent)
        self.dollars_frame.grid(row=self._next_row("left"), column=0, columnspan=2, sticky="w", pady=2)

        ttk.Label(
            self.dollars_frame, text="Total Annual Withdrawal $:", font=self._body_font
        ).pack(side="left")

        vcmd = self.register(self._validate_retirement_field), "%P", "retirement_withdraw_dollars"

        self.dollars_entry = ttk.Entry(
            self.dollars_frame, textvariable=self.dollars_var, width=10, font=self._body_font,
            validate="focusout", validatecommand=vcmd
        )
        self.dollars_entry.pack(side="left", padx=5)
        bind_entry_commit_on_return(self.dollars_entry)

        Tooltip(
            self.dollars_entry,
            "Enter the total annual withdrawal as a fixed dollar amount.\n"
            "Used only if 'Use Manually Entered Expenses' is selected.",
            font=self._tooltip_font
        )

        self._update_withdrawal_visibility()

    def _update_withdrawal_visibility(self):
        use_retirement = self.controls.get("use_mode", "expenses") == "retirement"

        if use_retirement:
            state = "normal"
        else:
            state = "disabled"

        for widget in self.ret_mode_frame.winfo_children():
            widget.configure(state=state)

        for widget in self.pct_frame.winfo_children():
            widget.configure(state=state)

        for widget in self.dollars_frame.winfo_children():
            widget.configure(state=state)

    def _parse_retirement_field(self, field, value):
        if field == "retirement_withdraw_pct":
            return parse_finite_float(value, minimum=0)

        if field == "retirement_withdraw_dollars":
            return parse_finite_float(value, allow_commas=True, allow_scientific=False, minimum=0)

        raise ValueError(f"Unknown retirement field: {field}")

    def _retirement_field_label(self, field):
        labels = {
            "retirement_withdraw_pct": "Total Annual Withdrawal %",
            "retirement_withdraw_dollars": "Total Annual Withdrawal $",
        }
        return labels.get(field, field)

    def _format_retirement_field(self, value):
        return f"{value:.2f}".rstrip("0").rstrip(".")

    def _format_retirement_dollars(self, value):
        return f"{float(value):,.0f}"

    def _validate_retirement_field(self, proposed_value, field):
        if field == "retirement_withdraw_pct":
            var = self.pct_var
            formatter = self._format_retirement_field
        else:
            var = self.dollars_var
            formatter = self._format_retirement_dollars

        current_value = self.controls[field]

        try:
            parsed = self._parse_retirement_field(field, proposed_value)
            self.controls[field] = parsed
            self.after_idle(lambda: var.set(formatter(parsed)))
            return True

        except ValueError as exc:
            self.after_idle(lambda: var.set(formatter(current_value)))
            mark_validation_failed(self)
            messagebox.showerror(
                "Invalid Input",
                f"Retirement / {self._retirement_field_label(field)}: {exc}",
                parent=self.winfo_toplevel(),
            )
            return True
