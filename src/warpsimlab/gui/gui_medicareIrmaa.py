# gui_medicareIrmaa.py

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox

from src.warpsimlab.gui.gui_validation import mark_validation_failed, parse_finite_float, parse_integer
from src.warpsimlab.gui.gui_utils import bind_entry_commit_on_return
from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin
from src.warpsimlab.utils.tooltip import Tooltip


class MedicareIrmaaEditFrame(ScalableFrameMixin, ttk.Frame):
    """Edit per-person Medicare assumptions and household IRMAA inputs."""

    def __init__(self, parent, persons, simulation_controls, historical_magi, **kwargs):
        super().__init__(parent, padding=10, **kwargs)

        self.persons = persons
        self.simulation_controls = simulation_controls
        self.historical_magi = historical_magi

        self._body_font = tkfont.nametofont("TkDefaultFont").copy()
        self._header_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._header_text_font = tkfont.Font(root=self, family="Arial", size=11)
        self._section_font = tkfont.Font(root=self, family="Arial", size=12, weight="bold")
        self._person_header_font = tkfont.Font(root=self, family="Arial", size=12, weight="bold")
        self._tooltip_font = tkfont.Font(root=self, family="Arial", size=11)

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._header_font)
        self._register_scalable_font(self._header_text_font)
        self._register_scalable_font(self._section_font)
        self._register_scalable_font(self._person_header_font)
        self._register_scalable_font(self._tooltip_font)
        self._apply_gui_scale()

        self.vars = {}
        for key, person in persons.items():
            self.vars[key] = {
                "medicare_start_age": tk.StringVar(value=str(person.medicare_start_age)),
                "medicare_annual_cost": tk.StringVar(value=self._format_money(person.medicare_annual_cost)),
            }

        self.irmaa_enabled_var = tk.BooleanVar(value=simulation_controls["irmaa_enabled"])
        self.magi_vars = {
            "two_years_prior": tk.StringVar(value=self._format_optional_money(historical_magi["two_years_prior"])),
            "one_year_prior": tk.StringVar(value=self._format_optional_money(historical_magi["one_year_prior"])),
        }
        self.magi_warning_var = tk.StringVar()

        self.irmaa_enabled_var.trace_add("write", self._on_irmaa_enabled_changed)
        self._build_fields()


    def _apply_scaled_styles(self):
        ttk.Style(self).configure("MedicareIrmaa.TCheckbutton", font=self._body_font)


    def _format_money(self, value):
        return f"{float(value):,.0f}"


    def _format_optional_money(self, value):
        if value is None:
            return ""

        return self._format_money(value)


    def _build_fields(self):
        row = 0

        header_frame = ttk.Frame(self)
        header_frame.grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Label(header_frame, text="Household > Medicare & IRMAA", font=self._header_font).pack(side="left")
        ttk.Label(
            header_frame, text=" - Defines Medicare costs and optional IRMAA historical MAGI.",
            font=self._header_text_font
        ).pack(side="left")

        row += 1
        ttk.Label(self, text="Medicare", font=self._section_font).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(5, 4)
        )

        row += 1
        ttk.Label(self, text="", font=self._body_font).grid(row=row, column=0, sticky="w")
        ttk.Label(self, text="Husband", font=self._person_header_font).grid(
            row=row, column=1, sticky="w", padx=(5, 0)
        )

        if "wife" in self.persons:
            ttk.Label(self, text="Wife", font=self._person_header_font).grid(
                row=row, column=2, sticky="w", padx=(5, 0)
            )

        row += 1
        row = self._add_person_row(
            row, "Medicare Start Age", "medicare_start_age",
            "Age when Medicare-related costs begin."
        )
        row = self._add_person_row(
            row, "Annual Medicare Cost ($)", "medicare_annual_cost",
            "Annual year-0 Medicare-related cost. The simulation will apply inflation."
        )

        ttk.Separator(self, orient="horizontal").grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=8
        )

        row += 1
        ttk.Label(self, text="IRMAA", font=self._section_font).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )

        row += 1
        ttk.Checkbutton(
            self, text="Enable IRMAA", variable=self.irmaa_enabled_var, style="MedicareIrmaa.TCheckbutton"
        ).grid(row=row, column=0, columnspan=3, sticky="w")

        if not self.irmaa_enabled_var.get():
            return

        required_keys = self._required_historical_magi_keys()

        if not required_keys:
            row += 1
            ttk.Label(
                self,
                text="Historical MAGI is not needed before Medicare begins for the current ages and start ages.",
                font=self._body_font
            ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(6, 0))
            self._update_magi_warning()
            return

        row += 1
        ttk.Label(self, text="Historical Household MAGI", font=self._section_font).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(10, 4)
        )

        if "two_years_prior" in required_keys:
            row += 1
            row = self._add_magi_row(row, "2 Years Before Simulation", "two_years_prior")

        if "one_year_prior" in required_keys:
            row += 1
            row = self._add_magi_row(row, "1 Year Before Simulation", "one_year_prior")

        self._update_magi_warning()

        ttk.Label(
            self, textvariable=self.magi_warning_var, font=self._body_font, wraplength=700,
            justify="left"
        ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(8, 0))

    def _add_person_row(self, row, label, field, tooltip_text):
        ttk.Label(self, text=f"{label}:", font=self._body_font).grid(
            row=row, column=0, sticky="w", pady=2
        )

        for column, person_key in enumerate(("husband", "wife"), start=1):
            if person_key not in self.persons:
                continue

            vcmd = self.register(self._validate_person_field), "%P", person_key, field
            entry = ttk.Entry(
                self, textvariable=self.vars[person_key][field], width=14, font=self._body_font,
                validate="focusout", validatecommand=vcmd
            )
            entry.grid(row=row, column=column, sticky="w", padx=5)
            bind_entry_commit_on_return(entry)

            Tooltip(entry, tooltip_text, font=self._tooltip_font)

        return row + 1


    def _add_magi_row(self, row, label, key):
        ttk.Label(self, text=f"{label} ($):", font=self._body_font).grid(
            row=row, column=0, sticky="w", pady=2
        )

        vcmd = self.register(self._validate_magi), "%P", key
        entry = ttk.Entry(
            self, textvariable=self.magi_vars[key], width=14, font=self._body_font,
            validate="focusout", validatecommand=vcmd
        )
        entry.grid(row=row, column=1, sticky="w", padx=5)
        bind_entry_commit_on_return(entry)
        Tooltip(
            entry, "Optional household MAGI used for initial IRMAA lookback years.",
            font=self._tooltip_font
        )

        return row + 1


    def _required_historical_magi_keys(self):
        required = 0

        for person in self.persons.values():
            years_until_medicare = person.medicare_start_age - person.age

            if years_until_medicare <= 1:
                required = max(required, 2)
            elif years_until_medicare == 2:
                required = max(required, 1)

        if required == 2:
            return ("two_years_prior", "one_year_prior")

        if required == 1:
            return ("one_year_prior",)

        return ()


    def _update_magi_warning(self):
        if not self.irmaa_enabled_var.get():
            self.magi_warning_var.set("")
            return

        required_keys = self._required_historical_magi_keys()
        missing_count = 0

        for key in required_keys:
            if self.historical_magi[key] is None:
                missing_count += 1

        if missing_count == 0:
            self.magi_warning_var.set("")
            return

        noun = "value is" if missing_count == 1 else "values are"
        self.magi_warning_var.set(
            f"Warning: {missing_count} required historical MAGI {noun} missing. "
            "Initial IRMAA years cannot be modeled until sufficient MAGI history is available."
        )


    def _rebuild_fields(self):
        for widget in self.winfo_children():
            widget.destroy()

        self._build_fields()


    def _on_irmaa_enabled_changed(self, *_):
        self.simulation_controls["irmaa_enabled"] = self.irmaa_enabled_var.get()
        self.after_idle(self._rebuild_fields)


    def _validate_person_field(self, proposed_value, person_key, field):
        person = self.persons[person_key]
        var = self.vars[person_key][field]
        person_label = "Husband" if person_key == "husband" else "Wife"
        field_label = "Medicare Start Age" if field == "medicare_start_age" else "Annual Medicare Cost"

        try:
            if field == "medicare_start_age":
                value = parse_integer(proposed_value, allow_commas=True, minimum=0, maximum=120)
            else:
                value = parse_finite_float(
                    proposed_value, allow_commas=True, allow_scientific=False, minimum=0
                )

            setattr(person, field, value)

            if field == "medicare_start_age":
                self.after_idle(lambda: var.set(str(value)))
                self.after_idle(self._rebuild_fields)
            else:
                self.after_idle(lambda: var.set(self._format_money(value)))

            return True

        except ValueError as exc:
            current_value = getattr(person, field)
            formatted = str(current_value) if field == "medicare_start_age" else self._format_money(current_value)
            self.after_idle(lambda: var.set(formatted))
            mark_validation_failed(self)
            messagebox.showerror(
                "Invalid Input", f"Medicare & IRMAA / {person_label} / {field_label}: {exc}",
                parent=self.winfo_toplevel()
            )
            return True


    def _validate_magi(self, proposed_value, key):
        current_value = self.historical_magi[key]

        try:
            raw_value = proposed_value.strip()
            value = None if not raw_value else parse_finite_float(
                raw_value, allow_commas=True, allow_scientific=False, minimum=0
            )

            self.historical_magi[key] = value
            self.after_idle(lambda: self.magi_vars[key].set(self._format_optional_money(value)))
            self.after_idle(self._update_magi_warning)
            return True

        except ValueError as exc:
            self.after_idle(
                lambda: self.magi_vars[key].set(self._format_optional_money(current_value))
            )
            mark_validation_failed(self)
            messagebox.showerror(
                "Invalid Input", f"Medicare & IRMAA / Historical Household MAGI: {exc}",
                parent=self.winfo_toplevel()
            )
            return True