# gui_specialIncome.py

import tkinter as tk
from tkinter import ttk

from src.utils.tooltip import Tooltip


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
        "inflation_adjustment_pct": float,
    }
    """

    def __init__(
        self,
        parent,
        special_income_streams,
        enable_second_person=True,
        title="Special Income",
        **kwargs
    ):
        super().__init__(parent, padding=10, **kwargs)

        self.special_income_streams = special_income_streams
        self.enable_second_person = enable_second_person
        self.title = title
        self.row_vars = []
        self.next_row = 0

        ttk.Label(
            self,
            text=(
                "Special income streams are optional, age-based income items such as "
                "alimony, inheritance payments, consulting income, or other non-standard income. "
                "This screen stores the data for the simulation engine; it does not yet calculate income."
            ),
            font=("Arial", 11),
            wraplength=900,
            justify="left",
        ).grid(row=self.next_row, column=0, columnspan=8, sticky="w", pady=(0, 10))

        self.next_row += 1

        headers = [
            "Owner",
            "Name / Comment",
            "Amount ($/yr)",
            "Start Age",
            "End Age",
            "Enabled",
            "Taxable",
            "Inflation Adj. (%)",
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


    def _default_owner(self):
        return "husband"


    def _owner_values(self):
        if self.enable_second_person:
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
        stream.setdefault("inflation_adjustment_pct", 100.0)

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
            "inflation_adjustment_pct": 100.0,
        }
        self.special_income_streams.append(stream)
        self._add_stream_row(stream)


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
        inflation_var = tk.StringVar(value=str(stream["inflation_adjustment_pct"]))

        owner_combo = ttk.Combobox(
            self,
            textvariable=owner_var,
            values=self._owner_values(),
            width=10,
            state="readonly",
        )
        owner_combo.grid(row=row, column=0, padx=5, pady=2, sticky="w")
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

        inflation_entry = ttk.Entry(
            self,
            textvariable=inflation_var,
            width=12,
            validate="focusout",
            validatecommand=(
                self.register(
                    lambda proposed_value, s=stream, v=inflation_var:
                        self._validate_float_field(
                            proposed_value,
                            s,
                            "inflation_adjustment_pct",
                            v,
                            "100.0",
                            "True",
                        )
                ),
                "%P",
            ),
        )
        inflation_entry.grid(row=row, column=7, padx=5, pady=2, sticky="w")
        Tooltip(inflation_entry, "Percent of inflation adjustment. 100 = full inflation, 0 = none.", font=("Arial", 11))

        delete_button = ttk.Button(
            self,
            text="Delete",
            command=lambda s=stream: self._delete_stream(s),
        )
        delete_button.grid(row=row, column=8, padx=5, pady=2, sticky="w")

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
                "inflation_adjustment_pct": inflation_var,
            },
            "widgets": [
                owner_combo,
                name_entry,
                amount_entry,
                start_age_entry,
                end_age_entry,
                enabled_check,
                taxable_check,
                inflation_entry,
                delete_button,
            ],
        })

        self.next_row += 1
        self._update_add_button_position()


    def _clean_number_text(self, raw_value):
        return raw_value.strip().replace(",", "")


    def _validate_float_field(
        self,
        proposed_value,
        stream,
        field_key,
        var,
        default_value,
        allow_negative_text,
    ):
        text = self._clean_number_text(proposed_value)
        allow_negative = allow_negative_text == "True"

        try:
            if text == "" or text in {"-", "+", ".", "-.", "+."}:
                raise ValueError("Invalid number.")
            if "e" in text.lower():
                raise ValueError("Scientific notation not allowed.")

            value = float(text)

            if not allow_negative and value < 0.0:
                raise ValueError("Negative value not allowed.")

            stream[field_key] = value
            self.after_idle(lambda: var.set(str(value)))
            return True

        except ValueError:
            current_value = stream.get(field_key, float(default_value))
            self.after_idle(lambda: var.set(str(current_value)))
            self.bell()
            return True


    def _validate_int_field(self, proposed_value, stream, field_key, var, default_value):
        text = self._clean_number_text(proposed_value)

        try:
            if text == "" or text in {"-", "+"}:
                raise ValueError("Invalid integer.")

            value = int(text)

            if value < 0 or value > 120:
                raise ValueError("Invalid age.")

            stream[field_key] = value
            self.after_idle(lambda: var.set(str(value)))
            return True

        except ValueError:
            current_value = stream.get(field_key, int(default_value))
            self.after_idle(lambda: var.set(str(current_value)))
            self.bell()
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