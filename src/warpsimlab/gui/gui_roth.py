import tkinter as tk
from tkinter import ttk

from src.warpsimlab.utils.tooltip import Tooltip


class RothEditFrame(ttk.Frame):
    """
    Advanced-mode editor for scheduled Roth flows.

    Writes directly into roth_flows, which is a list of dicts:

    {
        "owner": "husband" or "wife",
        "type": (
            "roth_ira_contribution"
            or "roth_workplace_contribution"
            or "roth_conversion"
        ),
        "name": str,
        "amount": float,
        "start_age": int,
        "end_age": int,
        "enabled": bool,
        "inflation_adjustment_pct": float,
    }
    """

    ROTH_FLOW_TYPES = (
        "roth_ira_contribution",
        "roth_workplace_contribution",
        "roth_conversion",
    )

    TYPE_LABELS = {
        "roth_ira_contribution": "Roth IRA Contribution",
        "roth_workplace_contribution": (
            "Roth Workplace-Plan Contribution"
        ),
        "roth_conversion": "Roth Conversion",
    }

    LABEL_TO_TYPE = {
        label: flow_type
        for flow_type, label in TYPE_LABELS.items()
    }

    TYPE_TOOLTIPS = {
        "roth_ira_contribution": (
            "After-tax contribution to a Roth IRA."
        ),
        "roth_workplace_contribution": (
            "After-tax employee contribution to the Roth side of a "
            "workplace retirement plan, such as a Roth 401(k), "
            "Roth 403(b), or Roth 457(b). This is not an employer match."
        ),
        "roth_conversion": (
            "Conversion of pre-tax retirement assets to Roth assets. "
            "Simulator tax behavior will be implemented separately."
        ),
    }

    def __init__(
        self,
        parent,
        roth_flows,
        enable_second_person=True,
        title="Roth Contributions / Conversions",
        **kwargs
    ):
        super().__init__(parent, padding=10, **kwargs)

        # gui_init.py owns this list. This frame mutates it directly.
        self.roth_flows = roth_flows
        self.enable_second_person = enable_second_person
        self.title = title

        self.row_vars = []
        self.next_row = 0

        ttk.Label(
            self,
            text=(
                "Roth flows define scheduled Roth IRA contributions, "
                "Roth workplace-plan contributions, and Roth conversions. "
                "This screen stores user-supplied Roth flow data for the "
                "simulation engine; simulator behavior is implemented "
                "separately."
            ),
            font=("Arial", 11),
            wraplength=1050,
            justify="left",
        ).grid(
            row=self.next_row,
            column=0,
            columnspan=9,
            sticky="w",
            pady=(0, 10),
        )

        self.next_row += 1

        headers = [
            "Owner",
            "Type",
            "Name / Comment",
            "Amount ($/yr)",
            "Start Age",
            "End Age",
            "Enabled",
            "Inflation Adj. (%)",
            "Delete",
        ]

        for col, header in enumerate(headers):
            ttk.Label(
                self,
                text=header,
                font=("Arial", 10, "bold"),
            ).grid(
                row=self.next_row,
                column=col,
                padx=5,
                pady=5,
                sticky="w",
            )

        self.next_row += 1

        self.add_button = ttk.Button(
            self,
            text="Add Roth Flow",
            command=self._add_new_flow,
        )
        self.add_button.grid(
            row=self.next_row,
            column=0,
            pady=(6, 2),
            sticky="w",
        )

        for flow in self.roth_flows:
            self._normalize_flow(flow)
            self._add_flow_row(flow)

        self._update_add_button_position()


    def _default_owner(self):
        return "husband"


    def _owner_values(self):
        if self.enable_second_person:
            return ["husband", "wife"]

        return ["husband"]


    def _normalize_flow(self, flow):
        flow.setdefault("owner", self._default_owner())
        flow.setdefault("type", "roth_ira_contribution")
        flow.setdefault("name", "")
        flow.setdefault("amount", 0.0)
        flow.setdefault("start_age", 0)
        flow.setdefault("end_age", 120)
        flow.setdefault("enabled", True)
        flow.setdefault("inflation_adjustment_pct", 0.0)

        if flow["owner"] not in self._owner_values():
            flow["owner"] = self._default_owner()

        if flow["type"] not in self.ROTH_FLOW_TYPES:
            flow["type"] = "roth_ira_contribution"


    def _add_new_flow(self):
        flow = {
            "owner": self._default_owner(),
            "type": "roth_ira_contribution",
            "name": "",
            "amount": 0.0,
            "start_age": 0,
            "end_age": 120,
            "enabled": True,
            "inflation_adjustment_pct": 0.0,
        }

        self.roth_flows.append(flow)
        self._add_flow_row(flow)


    def _add_flow_row(self, flow):
        self._normalize_flow(flow)

        row = self.next_row

        owner_var = tk.StringVar(
            value=flow["owner"]
        )

        type_var = tk.StringVar(
            value=self.TYPE_LABELS[flow["type"]]
        )

        name_var = tk.StringVar(
            value=str(flow["name"])
        )

        amount_var = tk.StringVar(
            value=str(flow["amount"])
        )

        start_age_var = tk.StringVar(
            value=str(flow["start_age"])
        )

        end_age_var = tk.StringVar(
            value=str(flow["end_age"])
        )

        enabled_var = tk.BooleanVar(
            value=bool(flow["enabled"])
        )

        inflation_var = tk.StringVar(
            value=str(flow["inflation_adjustment_pct"])
        )

        owner_combo = ttk.Combobox(
            self,
            textvariable=owner_var,
            values=self._owner_values(),
            width=10,
            state="readonly",
        )
        owner_combo.grid(
            row=row,
            column=0,
            padx=5,
            pady=2,
            sticky="w",
        )
        Tooltip(
            owner_combo,
            "Person whose age controls this Roth flow.",
            font=("Arial", 11),
        )

        type_combo = ttk.Combobox(
            self,
            textvariable=type_var,
            values=[
                self.TYPE_LABELS[flow_type]
                for flow_type in self.ROTH_FLOW_TYPES
            ],
            width=32,
            state="readonly",
        )
        type_combo.grid(
            row=row,
            column=1,
            padx=5,
            pady=2,
            sticky="w",
        )
        Tooltip(
            type_combo,
            (
                "Choose a Roth IRA contribution, an employee Roth "
                "workplace-plan contribution, or a Roth conversion."
            ),
            font=("Arial", 11),
        )

        name_entry = ttk.Entry(
            self,
            textvariable=name_var,
            width=20,
        )
        name_entry.grid(
            row=row,
            column=2,
            padx=5,
            pady=2,
            sticky="w",
        )
        Tooltip(
            name_entry,
            "Optional description or comment for this Roth flow.",
            font=("Arial", 11),
        )

        amount_entry = ttk.Entry(
            self,
            textvariable=amount_var,
            width=14,
            validate="focusout",
            validatecommand=(
                self.register(
                    lambda proposed_value, f=flow, v=amount_var:
                        self._validate_float_field(
                            proposed_value,
                            f,
                            "amount",
                            v,
                            0.0,
                            allow_negative=False,
                        )
                ),
                "%P",
            ),
        )
        amount_entry.grid(
            row=row,
            column=3,
            padx=5,
            pady=2,
            sticky="w",
        )
        Tooltip(
            amount_entry,
            "Annual Roth contribution or conversion amount.",
            font=("Arial", 11),
        )

        start_age_entry = ttk.Entry(
            self,
            textvariable=start_age_var,
            width=10,
            validate="focusout",
            validatecommand=(
                self.register(
                    lambda proposed_value, f=flow, v=start_age_var:
                        self._validate_int_field(
                            proposed_value,
                            f,
                            "start_age",
                            v,
                            0,
                        )
                ),
                "%P",
            ),
        )
        start_age_entry.grid(
            row=row,
            column=4,
            padx=5,
            pady=2,
            sticky="w",
        )
        Tooltip(
            start_age_entry,
            "Age when this Roth flow starts.",
            font=("Arial", 11),
        )

        end_age_entry = ttk.Entry(
            self,
            textvariable=end_age_var,
            width=10,
            validate="focusout",
            validatecommand=(
                self.register(
                    lambda proposed_value, f=flow, v=end_age_var:
                        self._validate_int_field(
                            proposed_value,
                            f,
                            "end_age",
                            v,
                            120,
                        )
                ),
                "%P",
            ),
        )
        end_age_entry.grid(
            row=row,
            column=5,
            padx=5,
            pady=2,
            sticky="w",
        )
        Tooltip(
            end_age_entry,
            "Age when this Roth flow stops.",
            font=("Arial", 11),
        )

        enabled_check = ttk.Checkbutton(
            self,
            variable=enabled_var,
        )
        enabled_check.grid(
            row=row,
            column=6,
            padx=5,
            pady=2,
            sticky="w",
        )
        Tooltip(
            enabled_check,
            "Temporarily enable or disable this Roth flow.",
            font=("Arial", 11),
        )

        inflation_entry = ttk.Entry(
            self,
            textvariable=inflation_var,
            width=12,
            validate="focusout",
            validatecommand=(
                self.register(
                    lambda proposed_value, f=flow, v=inflation_var:
                        self._validate_float_field(
                            proposed_value,
                            f,
                            "inflation_adjustment_pct",
                            v,
                            0.0,
                            allow_negative=True,
                        )
                ),
                "%P",
            ),
        )
        inflation_entry.grid(
            row=row,
            column=7,
            padx=5,
            pady=2,
            sticky="w",
        )
        Tooltip(
            inflation_entry,
            (
                "Percent of inflation adjustment. "
                "100 = full inflation, 0 = no adjustment."
            ),
            font=("Arial", 11),
        )

        delete_button = ttk.Button(
            self,
            text="Delete",
            command=lambda f=flow: self._delete_flow(f),
        )
        delete_button.grid(
            row=row,
            column=8,
            padx=5,
            pady=2,
            sticky="w",
        )

        owner_var.trace_add(
            "write",
            lambda *_: flow.__setitem__(
                "owner",
                owner_var.get(),
            ),
        )

        type_var.trace_add(
            "write",
            lambda *_: self._set_flow_type(
                flow,
                type_var.get(),
            ),
        )

        name_var.trace_add(
            "write",
            lambda *_: flow.__setitem__(
                "name",
                name_var.get(),
            ),
        )

        enabled_var.trace_add(
            "write",
            lambda *_: flow.__setitem__(
                "enabled",
                bool(enabled_var.get()),
            ),
        )

        self.row_vars.append({
            "flow": flow,
            "vars": {
                "owner": owner_var,
                "type": type_var,
                "name": name_var,
                "amount": amount_var,
                "start_age": start_age_var,
                "end_age": end_age_var,
                "enabled": enabled_var,
                "inflation_adjustment_pct": inflation_var,
            },
            "widgets": [
                owner_combo,
                type_combo,
                name_entry,
                amount_entry,
                start_age_entry,
                end_age_entry,
                enabled_check,
                inflation_entry,
                delete_button,
            ],
        })

        self.next_row += 1
        self._update_add_button_position()


    def _set_flow_type(self, flow, display_label):
        flow_type = self.LABEL_TO_TYPE.get(
            display_label,
            "roth_ira_contribution",
        )
        flow["type"] = flow_type


    def _clean_number_text(self, raw_value):
        return raw_value.strip().replace(",", "")


    def _validate_float_field(
        self,
        proposed_value,
        flow,
        field_key,
        var,
        default_value,
        allow_negative,
    ):
        text = self._clean_number_text(proposed_value)

        try:
            if text == "" or text in {
                "-",
                "+",
                ".",
                "-.",
                "+.",
            }:
                raise ValueError("Invalid number.")

            if "e" in text.lower():
                raise ValueError(
                    "Scientific notation not allowed."
                )

            value = float(text)

            if not allow_negative and value < 0.0:
                raise ValueError(
                    "Negative value not allowed."
                )

            flow[field_key] = value
            self.after_idle(
                lambda: var.set(str(value))
            )
            return True

        except ValueError:
            current_value = flow.get(
                field_key,
                float(default_value),
            )
            self.after_idle(
                lambda: var.set(str(current_value))
            )
            self.bell()
            return True


    def _validate_int_field(
        self,
        proposed_value,
        flow,
        field_key,
        var,
        default_value,
    ):
        text = self._clean_number_text(proposed_value)

        try:
            if text == "" or text in {"-", "+"}:
                raise ValueError("Invalid integer.")

            value = int(text)

            if value < 0 or value > 120:
                raise ValueError("Invalid age.")

            flow[field_key] = value
            self.after_idle(
                lambda: var.set(str(value))
            )
            return True

        except ValueError:
            current_value = flow.get(
                field_key,
                int(default_value),
            )
            self.after_idle(
                lambda: var.set(str(current_value))
            )
            self.bell()
            return True


    def _delete_flow(self, flow):
        for item in list(self.row_vars):
            if item["flow"] is flow:
                for widget in item["widgets"]:
                    widget.destroy()

                self.row_vars.remove(item)
                break

        if flow in self.roth_flows:
            self.roth_flows.remove(flow)

        self._regrid_rows()


    def _regrid_rows(self):
        start_row = 2

        for index, item in enumerate(self.row_vars):
            row_index = start_row + index

            for col, widget in enumerate(item["widgets"]):
                widget.grid_configure(
                    row=row_index,
                    column=col,
                )

        self.next_row = start_row + len(self.row_vars)
        self._update_add_button_position()


    def _update_add_button_position(self):
        self.add_button.grid_configure(
            row=self.next_row,
            column=0,
            sticky="w",
        )