# gui_specialIncome.py

import tkinter as tk
from tkinter import ttk, messagebox

from src.warpsimlab.gui.gui_validation import mark_validation_failed, parse_finite_float, parse_integer
from src.warpsimlab.utils.tooltip import Tooltip


class SpecialIncomeEditFrame(ttk.Frame):
    """
    Advanced-mode editor for special income streams.

    Writes directly into special_income_streams, which is a list of dicts:

    {
        "owner": "husband" or "wife",
        "name": str,
        "amount": float,
        "start_age": int,
        "end_age": int,
        "taxable": bool,
        "adjustment_mode": "inflation", "fixed", or "none",
        "adjustment_pct": float,
    }
    """

    ADJUSTMENT_MODE_LABELS = {"inflation": "Inflation", "fixed": "Fixed Annual", "none": "None"}
    ADJUSTMENT_MODE_VALUES = {"Inflation": "inflation", "Fixed Annual": "fixed", "None": "none"}
    ADJUSTMENT_MODE_DEFAULTS = {"inflation": 100.0, "fixed": 5.0, "none": 0.0}

    def __init__(
        self,
        parent,
        special_income_streams,
        second_person_enabled=True,
        title="Special Income",
        **kwargs
    ):
        super().__init__(parent, padding=10, **kwargs)

        self.special_income_streams = special_income_streams
        self.second_person_enabled = second_person_enabled
        self.title = title

        style = ttk.Style(self)
        combo_foreground = style.lookup("TLabel", "foreground")
        combo_background = style.lookup("TCombobox", "fieldbackground")

        style.configure(
            "SpecialIncome.TCombobox",
            foreground=combo_foreground,
            fieldbackground=combo_background,
        )

        style.map(
            "SpecialIncome.TCombobox",
            foreground=[
                ("readonly", combo_foreground),
            ],
            fieldbackground=[
                ("readonly", combo_background),
            ],
        )

        self.row_vars = []
        self.next_row = 0

        header_frame = ttk.Frame(self)
        header_frame.grid(
            row=self.next_row,
            column=0,
            columnspan=10,
            sticky="w",
            pady=(0, 10),
        )

        ttk.Label(
            header_frame,
            text="Cash Flow > Special Income",
            font=("Arial", 11, "bold"),
        ).pack(side="left")

        ttk.Label(
            header_frame,
            text=(
                " - Special income streams include income items "
                "such as alimony, inheritance payments, consulting income, or "
                "other non-standard income. "
            ),
            font=("Arial", 11),
        ).pack(side="left")

        self.next_row += 1

        headers = [
            "Owner",
            "Name / Comment",
            "Amount ($/yr)",
            "Start Age",
            "End Age",
            "Enabled",
            "Taxable",
            "Annual Increase",
            "Adjustment (%)",
            "Delete",
        ]

        for col, header in enumerate(headers):
            ttk.Label(self, text=header, font=("Arial", 10, "bold")).grid(
                row=self.next_row,
                column=col,
                padx=5,
                pady=5,
                sticky="w",
            )

        self.next_row += 1

        self.add_button = ttk.Button(
            self,
            text="Add Special Income",
            command=self._add_new_stream,
        )
        self.add_button.grid(row=self.next_row, column=0, pady=(6, 2), sticky="w")

        for stream in self.special_income_streams:
            self._normalize_stream(stream)
            self._add_stream_row(stream)

        self._update_add_button_position()


    def _on_combobox_selected(self, event=None):
        event.widget.selection_clear()
        self.focus_set()


    def _default_owner(self):
        return "husband"


    def _owner_values(self):
        if self.second_person_enabled:
            return ["husband", "wife"]
        return ["husband"]


    def _normalize_stream(self, stream):
        stream.setdefault("owner", self._default_owner())
        stream.setdefault("name", "")
        stream.setdefault("amount", 0.0)
        stream.setdefault("start_age", 0)
        stream.setdefault("end_age", 120)
        stream.setdefault("taxable", True)
        stream.setdefault("enabled", True)
        stream.setdefault("adjustment_mode", "inflation")
        stream.setdefault("adjustment_pct", float(stream.get("inflation_adjustment_pct", 100.0)))

        if stream["adjustment_mode"] not in self.ADJUSTMENT_MODE_LABELS:
            stream["adjustment_mode"] = "inflation"

        if stream["owner"] not in self._owner_values():
            stream["owner"] = self._default_owner()


    def _add_new_stream(self):
        stream = {
            "owner": self._default_owner(),
            "name": "",
            "amount": 0.0,
            "start_age": 0,
            "end_age": 120,
            "taxable": True,
            "enabled": True,
            "adjustment_mode": "inflation",
            "adjustment_pct": 100.0,
        }
        self.special_income_streams.append(stream)
        self._add_stream_row(stream)


    def _set_adjustment_mode(self, stream, mode_var, pct_var, pct_entry, reset_rate=False):
        mode = self.ADJUSTMENT_MODE_VALUES.get(mode_var.get(), "inflation")
        stream["adjustment_mode"] = mode

        if reset_rate:
            pct = self.ADJUSTMENT_MODE_DEFAULTS[mode]
            stream["adjustment_pct"] = pct
            pct_var.set(str(pct))

        pct_entry.configure(state="disabled" if mode == "none" else "normal")


    def _add_stream_row(self, stream):
        self._normalize_stream(stream)

        row = self.next_row

        owner_var = tk.StringVar(value=stream["owner"])
        name_var = tk.StringVar(value=str(stream["name"]))
        amount_var = tk.StringVar(value=str(stream["amount"]))
        start_age_var = tk.StringVar(value=str(stream["start_age"]))
        end_age_var = tk.StringVar(value=str(stream["end_age"]))
        taxable_var = tk.BooleanVar(value=bool(stream["taxable"]))
        enabled_var = tk.BooleanVar(value=bool(stream["enabled"]))
        adjustment_mode_var = tk.StringVar(value=self.ADJUSTMENT_MODE_LABELS[stream["adjustment_mode"]])
        adjustment_pct_var = tk.StringVar(value=str(stream["adjustment_pct"]))

        owner_combo = ttk.Combobox(
            self,
            textvariable=owner_var,
            values=self._owner_values(),
            width=10,
            state="readonly",
            style="SpecialIncome.TCombobox",
        )
        owner_combo.grid(row=row, column=0, padx=5, pady=2, sticky="w")
        owner_combo.bind("<<ComboboxSelected>>", self._on_combobox_selected)
        Tooltip(owner_combo, "Person whose age controls this income stream", font=("Arial", 11))

        name_entry = ttk.Entry(self, textvariable=name_var, width=24)
        name_entry.grid(row=row, column=1, padx=5, pady=2, sticky="w")
        Tooltip(name_entry, "Description such as Alimony, Inheritance, Consulting, etc.", font=("Arial", 11))

        amount_entry = ttk.Entry(
            self,
            textvariable=amount_var,
            width=14,
            validate="focusout",
            validatecommand=(
                self.register(
                    lambda proposed_value, s=stream, v=amount_var:
                        self._validate_float_field(
                            proposed_value,
                            s,
                            "amount",
                            v,
                            "0.0",
                            "False",
                        )
                ),
                "%P",
            ),        )
        amount_entry.grid(row=row, column=2, padx=5, pady=2, sticky="w")
        Tooltip(amount_entry, "Annual dollar amount before tax treatment", font=("Arial", 11))

        start_age_entry = ttk.Entry(
            self,
            textvariable=start_age_var,
            width=10,
            validate="focusout",
            validatecommand=(
                self.register(
                    lambda proposed_value, s=stream, v=start_age_var:
                        self._validate_int_field(
                            proposed_value,
                            s,
                            "start_age",
                            v,
                            "0",
                        )
                ),
                "%P",
            ),
        )
        start_age_entry.grid(row=row, column=3, padx=5, pady=2, sticky="w")
        Tooltip(start_age_entry, "Age when this income starts", font=("Arial", 11))

        end_age_entry = ttk.Entry(
            self,
            textvariable=end_age_var,
            width=10,
            validate="focusout",
            validatecommand=(
                self.register(
                    lambda proposed_value, s=stream, v=end_age_var:
                        self._validate_int_field(
                            proposed_value,
                            s,
                            "end_age",
                            v,
                            "120",
                        )
                ),
                "%P",
            ),
        )
        end_age_entry.grid(row=row, column=4, padx=5, pady=2, sticky="w")
        Tooltip(end_age_entry, "Age when this income stops", font=("Arial", 11))

        enabled_check = ttk.Checkbutton(
            self,
            variable=enabled_var
        )
        enabled_check.grid(
            row=row,
            column=5,
            padx=5,
            pady=2,
            sticky="w"
        )

        Tooltip(
            enabled_check,
            "Temporarily enable or disable this income stream",
            font=("Arial", 11)
        )

        taxable_check = ttk.Checkbutton(self, variable=taxable_var)
        taxable_check.grid(row=row, column=6, padx=5, pady=2, sticky="w")
        Tooltip(taxable_check, "Checked means taxable ordinary income; unchecked means non-taxable", font=("Arial", 11))

        adjustment_mode_combo = ttk.Combobox(
            self, textvariable=adjustment_mode_var, values=list(self.ADJUSTMENT_MODE_VALUES), width=12,
            state="readonly", style="SpecialIncome.TCombobox"
        )
        adjustment_mode_combo.grid(row=row, column=7, padx=5, pady=2, sticky="w")
        adjustment_mode_combo.bind("<<ComboboxSelected>>", self._on_combobox_selected)
        Tooltip(adjustment_mode_combo, "How this income changes over time", font=("Arial", 11))

        adjustment_mode_combo = ttk.Combobox(
            self, textvariable=adjustment_mode_var, values=list(self.ADJUSTMENT_MODE_VALUES), width=12,
            state="readonly", style="SpecialIncome.TCombobox"
        )
        adjustment_mode_combo.grid(row=row, column=7, padx=5, pady=2, sticky="w")
        adjustment_mode_combo.bind("<<ComboboxSelected>>", self._on_combobox_selected)
        Tooltip(
            adjustment_mode_combo,
            "Inflation adjusts by a percentage of inflation. Fixed Annual increases by a fixed percentage each year. "
            "None applies no annual increase.",
            font=("Arial", 11)
        )

        adjustment_pct_entry = ttk.Entry(
            self, textvariable=adjustment_pct_var, width=12, validate="focusout",
            validatecommand=(
                self.register(
                    lambda proposed_value, s=stream, v=adjustment_pct_var:
                        self._validate_float_field(proposed_value, s, "adjustment_pct", v, "100.0", "True")
                ),
                "%P",
            ),
        )
        adjustment_pct_entry.grid(row=row, column=8, padx=5, pady=2, sticky="w")
        Tooltip(
            adjustment_pct_entry,
            "Inflation: percent of inflation adjustment; 100 = full inflation, 0 = none. "
            "Fixed Annual: annual percentage increase; 5 = 5% per year.",
            font=("Arial", 11)
        )

        adjustment_mode_var.trace_add(
            "write",
            lambda *_: self._set_adjustment_mode(
                stream, adjustment_mode_var, adjustment_pct_var, adjustment_pct_entry, reset_rate=True
            )
        )
        self._set_adjustment_mode(stream, adjustment_mode_var, adjustment_pct_var, adjustment_pct_entry)

        delete_button = ttk.Button(
            self,
            text="Delete",
            command=lambda s=stream: self._delete_stream(s),
        )
        delete_button.grid(row=row, column=9, padx=5, pady=2, sticky="w")

        owner_var.trace_add("write", lambda *_: stream.__setitem__("owner", owner_var.get()))
        name_var.trace_add("write", lambda *_: stream.__setitem__("name", name_var.get()))
        taxable_var.trace_add("write", lambda *_: stream.__setitem__("taxable", bool(taxable_var.get())))
        enabled_var.trace_add("write", lambda *_: stream.__setitem__("enabled",bool(enabled_var.get())))

        self.row_vars.append({
            "stream": stream,
            "vars": {
                "owner": owner_var,
                "name": name_var,
                "amount": amount_var,
                "start_age": start_age_var,
                "end_age": end_age_var,
                "taxable": taxable_var,
                "enabled": enabled_var,
                "adjustment_mode": adjustment_mode_var,
                "adjustment_pct": adjustment_pct_var,
            },
            "widgets": [
                owner_combo,
                name_entry,
                amount_entry,
                start_age_entry,
                end_age_entry,
                enabled_check,
                taxable_check,
                adjustment_mode_combo,
                adjustment_pct_entry,
                delete_button,
            ],
        })

        self.next_row += 1
        self._update_add_button_position()


    def _validate_float_field(
        self,
        proposed_value,
        stream,
        field_key,
        var,
        default_value,
        allow_negative_text,
    ):
        allow_negative = allow_negative_text == "True"
        field_label = "Amount" if field_key == "amount" else "Annual Increase Adjustment"

        try:
            parsed = parse_finite_float(
                proposed_value,
                allow_commas=True,
                allow_scientific=False,
                minimum=None if allow_negative else 0,
            )

            stream[field_key] = parsed
            self.after_idle(lambda: var.set(str(parsed)))
            return True

        except ValueError as exc:
            current_value = stream.get(field_key, float(default_value))
            self.after_idle(lambda: var.set(str(current_value)))
            mark_validation_failed(self)
            messagebox.showerror(
                "Invalid Input",
                f"Special Income / {field_label}: {exc}",
                parent=self.winfo_toplevel(),
            )
            return True


    def _validate_int_field(self, proposed_value, stream, field_key, var, default_value):
        field_label = "Start Age" if field_key == "start_age" else "End Age"

        try:
            parsed = parse_integer(proposed_value, allow_commas=True, minimum=0, maximum=120)

            stream[field_key] = parsed
            self.after_idle(lambda: var.set(str(parsed)))
            return True

        except ValueError as exc:
            current_value = stream.get(field_key, int(default_value))
            self.after_idle(lambda: var.set(str(current_value)))
            mark_validation_failed(self)
            messagebox.showerror(
                "Invalid Input",
                f"Special Income / {field_label}: {exc}",
                parent=self.winfo_toplevel(),
            )
            return True


    def _delete_stream(self, stream):
        for item in list(self.row_vars):
            if item["stream"] is stream:
                for widget in item["widgets"]:
                    widget.destroy()
                self.row_vars.remove(item)
                break

        if stream in self.special_income_streams:
            self.special_income_streams.remove(stream)

        self._regrid_rows()


    def _regrid_rows(self):
        start_row = 2

        for i, item in enumerate(self.row_vars):
            row_index = start_row + i

            for col, widget in enumerate(item["widgets"]):
                widget.grid_configure(row=row_index, column=col)

        self.next_row = start_row + len(self.row_vars)
        self._update_add_button_position()


    def _update_add_button_position(self):
        self.add_button.grid_configure(row=self.next_row, column=0, sticky="w")