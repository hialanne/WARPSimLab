# gui_ageLongevity.py

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox

from src.warpsimlab.gui.gui_validation import mark_validation_failed, parse_integer
from src.warpsimlab.gui.gui_utils import bind_entry_commit_on_return
from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin
from src.warpsimlab.utils.tooltip import Tooltip


LONGEVITY_FIXED = "fixed_years"
LONGEVITY_CUSTOM = "custom_death_age"


class AgeLongevityEditFrame(ScalableFrameMixin, ttk.Frame):
    """Edit household ages, longevity mode, modeled death ages, and simulation horizon."""

    def __init__(self, parent, persons, simulation_controls, simulation_settings, refresh_callback=None, **kwargs):
        super().__init__(parent, padding=10, **kwargs)

        self.persons = persons
        self.simulation_controls = simulation_controls
        self.simulation_settings = simulation_settings
        self.refresh_callback = refresh_callback

        self._body_font = tkfont.nametofont("TkDefaultFont").copy()
        self._header_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._header_text_font = tkfont.Font(root=self, family="Arial", size=11)
        self._section_font = tkfont.Font(root=self, family="Arial", size=12, weight="bold")
        self._tooltip_font = tkfont.Font(root=self, family="Arial", size=11)

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._header_font)
        self._register_scalable_font(self._header_text_font)
        self._register_scalable_font(self._section_font)
        self._register_scalable_font(self._tooltip_font)
        self._apply_gui_scale()

        self.age_vars = {}
        self.death_age_vars = {}

        for key, person in persons.items():
            self.age_vars[key] = tk.StringVar(value=str(person.age))
            death_age = "" if person.modeled_death_age is None else str(person.modeled_death_age)
            self.death_age_vars[key] = tk.StringVar(value=death_age)

        self.second_person_var = tk.BooleanVar(value=simulation_controls["second_person_enabled"])
        self.longevity_mode_var = tk.StringVar(value=simulation_settings.get("longevity_mode", LONGEVITY_FIXED))
        self.years_var = tk.StringVar(value=str(simulation_settings["years_to_simulate"]))

        if self.longevity_mode_var.get() == LONGEVITY_CUSTOM:
            self._ensure_custom_death_ages()
            self._update_mortality_horizon()
        else:
            self._clear_modeled_death_ages()

        self.second_person_var.trace_add("write", self._on_second_person_changed)
        self.longevity_mode_var.trace_add("write", self._on_longevity_mode_changed)

        self._build_fields()


    def _apply_scaled_styles(self):
        style = ttk.Style(self)
        style.configure("AgeLongevity.TCheckbutton", font=self._body_font)
        style.configure("AgeLongevity.TRadiobutton", font=self._body_font)


    def _active_person_keys(self):
        keys = ["husband"]

        if self.simulation_controls["second_person_enabled"]:
            keys.append("wife")

        return keys


    def _build_fields(self):
        row = 0

        header_frame = ttk.Frame(self)
        header_frame.grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Label(header_frame, text="Household > Age & Longevity", font=self._header_font).pack(side="left")
        ttk.Label(
            header_frame, text=" - Defines household ages, longevity, and the simulation horizon.",
            font=self._header_text_font
        ).pack(side="left")

        row += 1
        ttk.Label(self, text="Household Ages", font=self._section_font).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(5, 4)
        )

        row += 1
        ttk.Checkbutton(
            self, text="Enable Second Person", variable=self.second_person_var, style="AgeLongevity.TCheckbutton"
        ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 6))

        row += 1
        row = self._add_age_row(row, "Husband", "husband")

        if self.simulation_controls["second_person_enabled"]:
            row = self._add_age_row(row, "Wife", "wife")

        ttk.Separator(self, orient="horizontal").grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=8
        )

        row += 1
        ttk.Label(self, text="Simulation Horizon", font=self._section_font).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )

        row += 1
        ttk.Radiobutton(
            self, text="Fixed simulation horizon", variable=self.longevity_mode_var,
            value=LONGEVITY_FIXED, style="AgeLongevity.TRadiobutton"
        ).grid(row=row, column=0, columnspan=3, sticky="w")

        row += 1
        ttk.Radiobutton(
            self, text="Custom modeled death age", variable=self.longevity_mode_var,
            value=LONGEVITY_CUSTOM, style="AgeLongevity.TRadiobutton"
        ).grid(row=row, column=0, columnspan=3, sticky="w")

        row += 1
        ttk.Label(self, text="Years to Simulate:", font=self._body_font).grid(
            row=row, column=0, sticky="w", pady=(6, 0)
        )

        vcmd = self.register(self._validate_years), "%P"
        self.years_entry = ttk.Entry(
            self, textvariable=self.years_var, width=14, font=self._body_font,
            validate="focusout", validatecommand=vcmd
        )
        self.years_entry.grid(row=row, column=1, sticky="w", padx=5, pady=(6, 0))
        bind_entry_commit_on_return(self.years_entry)

        if self.longevity_mode_var.get() == LONGEVITY_FIXED:
            Tooltip(self.years_entry, "Number of years to simulate.", font=self._tooltip_font)
        else:
            self.years_entry.configure(state="disabled")
            Tooltip(
                self.years_entry, "Derived from the last modeled death age.",
                font=self._tooltip_font
            )

        if self.longevity_mode_var.get() == LONGEVITY_CUSTOM:
            row += 1
            ttk.Label(self, text="Modeled Death Ages", font=self._section_font).grid(
                row=row, column=0, columnspan=3, sticky="w", pady=(10, 4)
            )

            row += 1
            row = self._add_death_age_row(row, "Husband", "husband")

            if self.simulation_controls["second_person_enabled"]:
                self._add_death_age_row(row, "Wife", "wife")


    def _add_age_row(self, row, label, person_key):
        ttk.Label(self, text=f"{label} Current Age:", font=self._body_font).grid(
            row=row, column=0, sticky="w"
        )

        vcmd = self.register(self._validate_age), "%P", person_key
        entry = ttk.Entry(
            self, textvariable=self.age_vars[person_key], width=14, font=self._body_font,
            validate="focusout", validatecommand=vcmd
        )
        entry.grid(row=row, column=1, sticky="w", padx=5)
        bind_entry_commit_on_return(entry)
        Tooltip(entry, "Current age in years.", font=self._tooltip_font)

        return row + 1


    def _add_death_age_row(self, row, label, person_key):
        ttk.Label(self, text=f"{label} Modeled Death Age:", font=self._body_font).grid(
            row=row, column=0, sticky="w"
        )

        vcmd = self.register(self._validate_death_age), "%P", person_key
        entry = ttk.Entry(
            self, textvariable=self.death_age_vars[person_key], width=14, font=self._body_font,
            validate="focusout", validatecommand=vcmd
        )
        entry.grid(row=row, column=1, sticky="w", padx=5)
        bind_entry_commit_on_return(entry)
        Tooltip(entry, "Age at which this person is modeled to die.", font=self._tooltip_font)

        return row + 1


    def _rebuild_fields(self):
        for widget in self.winfo_children():
            widget.destroy()

        self._build_fields()


    def _clear_modeled_death_ages(self):
        for key, person in self.persons.items():
            person.modeled_death_age = None
            self.death_age_vars[key].set("")


    def _ensure_custom_death_ages(self):
        years = self.simulation_settings["years_to_simulate"]

        for key in self._active_person_keys():
            person = self.persons[key]

            if person.modeled_death_age is None or person.modeled_death_age < person.age:
                person.modeled_death_age = person.age + years

            self.death_age_vars[key].set(str(person.modeled_death_age))


    def _update_mortality_horizon(self):
        if self.longevity_mode_var.get() != LONGEVITY_CUSTOM:
            return

        years = 1

        for key in self._active_person_keys():
            person = self.persons[key]

            if person.modeled_death_age is None:
                return

            years = max(years, person.modeled_death_age - person.age)

        self.simulation_settings["years_to_simulate"] = years
        self.years_var.set(str(years))


    def _on_second_person_changed(self, *_):
        self.simulation_controls["second_person_enabled"] = self.second_person_var.get()

        if self.longevity_mode_var.get() == LONGEVITY_CUSTOM:
            self._ensure_custom_death_ages()
            self._update_mortality_horizon()

        if self.refresh_callback:
            self.refresh_callback()


    def _on_longevity_mode_changed(self, *_):
        mode = self.longevity_mode_var.get()
        self.simulation_settings["longevity_mode"] = mode

        if mode == LONGEVITY_CUSTOM:
            self._ensure_custom_death_ages()
            self._update_mortality_horizon()
        else:
            self._clear_modeled_death_ages()

        self.after_idle(self._rebuild_fields)


    def _validate_age(self, proposed_value, person_key):
        person = self.persons[person_key]
        var = self.age_vars[person_key]
        person_label = "Husband" if person_key == "husband" else "Wife"

        try:
            value = parse_integer(proposed_value, allow_commas=True, minimum=0, maximum=120)

            if (
                self.longevity_mode_var.get() == LONGEVITY_CUSTOM
                and person.modeled_death_age is not None
                and value > person.modeled_death_age
            ):
                raise ValueError(f"must not exceed modeled death age {person.modeled_death_age}.")

            person.age = value
            self.after_idle(lambda: var.set(str(value)))
            self._update_mortality_horizon()
            return True
        except ValueError as exc:
            self.after_idle(lambda: var.set(str(person.age)))
            mark_validation_failed(self)
            messagebox.showerror(
                "Invalid Input", f"Age & Longevity / {person_label} / Current Age: {exc}",
                parent=self.winfo_toplevel()
            )
            return True


    def _validate_death_age(self, proposed_value, person_key):
        person = self.persons[person_key]
        var = self.death_age_vars[person_key]
        person_label = "Husband" if person_key == "husband" else "Wife"

        try:
            value = parse_integer(proposed_value, allow_commas=True, minimum=0, maximum=120)

            if value < person.age:
                raise ValueError(f"must be at least the current age of {person.age}.")

            person.modeled_death_age = value
            self.after_idle(lambda: var.set(str(value)))
            self._update_mortality_horizon()
            return True
        except ValueError as exc:
            current_value = "" if person.modeled_death_age is None else str(person.modeled_death_age)
            self.after_idle(lambda: var.set(current_value))
            mark_validation_failed(self)
            messagebox.showerror(
                "Invalid Input", f"Age & Longevity / {person_label} / Modeled Death Age: {exc}",
                parent=self.winfo_toplevel()
            )
            return True


    def _validate_years(self, proposed_value):
        current_value = self.simulation_settings["years_to_simulate"]

        try:
            value = parse_integer(proposed_value, allow_commas=True, minimum=1)
            self.simulation_settings["years_to_simulate"] = value
            self.after_idle(lambda: self.years_var.set(str(value)))
            return True
        except ValueError as exc:
            self.after_idle(lambda: self.years_var.set(str(current_value)))
            mark_validation_failed(self)
            messagebox.showerror(
                "Invalid Input", f"Age & Longevity / Years to Simulate: {exc}",
                parent=self.winfo_toplevel()
            )
            return True