
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox

from src.warpsimlab.gui.gui_validation import mark_validation_failed, parse_finite_float
from src.warpsimlab.utils.tooltip import Tooltip
from src.warpsimlab.gui.gui_utils import bind_entry_commit_on_return
from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin


class RmdQcdEditFrame(ScalableFrameMixin, ttk.Frame):
    def __init__(self, parent, control_vars, qcd_settings, second_person_enabled=False, title="RMDs & QCDs", **kwargs):
        super().__init__(parent, padding=10, **kwargs)

        self.controls = control_vars["_controls_dict"]
        self.qcd_settings = qcd_settings
        self._body_font = tkfont.nametofont("TkDefaultFont").copy()
        self._header_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._tooltip_font = tkfont.Font(root=self, family="Arial", size=11)

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._header_font)
        self._register_scalable_font(self._tooltip_font)
        self._apply_gui_scale()

        ttk.Label(self, text=f"Retirement > {title}", font=self._header_font).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 10)
        )
        self._add_include_rmd()
        ttk.Separator(self, orient="horizontal").grid(row=2, column=0, columnspan=4, sticky="ew", pady=12)
        ttk.Label(self, text="Qualified Charitable Distributions", font=self._header_font).grid(
            row=3, column=0, columnspan=4, sticky="w", pady=(0, 5)
        )
        ttk.Label(self, text="Annual charitable distributions from tax-deferred assets; separate from household spending.").grid(
            row=4, column=0, columnspan=4, sticky="w", pady=(0, 10)
        )

        self.qcd_vars = {}
        persons = ["husband"]
        if second_person_enabled:
            persons.append("wife")

        for col, person in enumerate(persons):
            self._add_person_qcd(person, col * 2)


    def _apply_scaled_styles(self):
        ttk.Style(self).configure("Retirement.TCheckbutton", font=self._body_font)


    def _add_include_rmd(self):
        self.rmd_var = tk.BooleanVar(value=self.controls.get("include_rmd", True))
        self.rmd_var.trace_add("write", lambda *args: self.controls.__setitem__("include_rmd", self.rmd_var.get()))
        self.rmd_cb = ttk.Checkbutton(
            self, text="Include RMDs", variable=self.rmd_var, style="Retirement.TCheckbutton"
        )
        self.rmd_cb.grid(row=1, column=0, columnspan=4, sticky="w")
        Tooltip(self.rmd_cb, "Include required minimum distributions in the simulation.", font=self._tooltip_font)


    def _add_person_qcd(self, person, col):
        settings = self.qcd_settings[person]
        vars_for_person = {
            "enabled": tk.BooleanVar(value=settings["enabled"]),
            "mode": tk.StringVar(value=settings["mode"]),
            "amount": tk.StringVar(value=f'{settings["amount"]:,.0f}'),
            "percent": tk.StringVar(value=f'{settings["percent"]:g}'),
            "start_age": tk.StringVar(value=f'{settings["start_age"]:g}'),
            "end_age": tk.StringVar(value="" if settings["end_age"] is None else f'{settings["end_age"]:g}'),
        }
        self.qcd_vars[person] = vars_for_person

        ttk.Label(self, text=person.capitalize(), font=self._header_font).grid(
            row=5, column=col, columnspan=2, sticky="w", pady=(0, 6)
        )
        enabled_cb = ttk.Checkbutton(
            self, text="Enable QCDs", variable=vars_for_person["enabled"], style="Retirement.TCheckbutton"
        )
        enabled_cb.grid(row=6, column=col, columnspan=2, sticky="w", pady=3)

        ttk.Label(self, text="Calculation:").grid(row=7, column=col, sticky="w", pady=3)
        mode_menu = ttk.OptionMenu(
            self, vars_for_person["mode"], vars_for_person["mode"].get(), "Fixed Amount", "Percent of RMD"
        )
        mode_menu.grid(row=7, column=col + 1, sticky="w", padx=5)
        mode_menu["menu"].configure(font=self._body_font)

        entries = {}
        labels = {
            "amount": "Annual QCD ($):", "percent": "RMD Percentage (%):",
            "start_age": "Starting Age:", "end_age": "Ending Age (blank = lifetime):"
        }
        for row, field in enumerate(("amount", "percent", "start_age", "end_age"), start=8):
            ttk.Label(self, text=labels[field]).grid(row=row, column=col, sticky="w", pady=3)
            command = (self.register(lambda value, p=person, f=field: self._validate_qcd_field(p, f, value)), "%P")
            entry = ttk.Entry(
                self, textvariable=vars_for_person[field], width=13, font=self._body_font,
                validate="focusout", validatecommand=command
            )
            entry.grid(row=row, column=col + 1, sticky="w", padx=5)
            bind_entry_commit_on_return(entry)
            entries[field] = entry


        def update_controls(*args):
            settings["enabled"] = vars_for_person["enabled"].get()
            settings["mode"] = vars_for_person["mode"].get()
            state = "normal" if settings["enabled"] else "disabled"
            mode_menu.configure(state=state)
            for field, entry in entries.items():
                active = (field not in ("amount", "percent") or
                          (field == "amount" and settings["mode"] == "Fixed Amount") or
                          (field == "percent" and settings["mode"] == "Percent of RMD"))
                entry.configure(state=state if active else "disabled")


        vars_for_person["enabled"].trace_add("write", update_controls)
        vars_for_person["mode"].trace_add("write", update_controls)
        update_controls()


    def _validate_qcd_field(self, person, field, text):
        settings = self.qcd_settings[person]
        var = self.qcd_vars[person][field]
        previous = settings[field]
        try:
            if field == "end_age" and not text.strip():
                value = None
            else:
                minimum = 70.5 if field == "start_age" else 0
                maximum = 100 if field == "percent" else 120 if field in ("start_age", "end_age") else None
                value = parse_finite_float(
                    text, allow_commas=True, allow_scientific=False, minimum=minimum, maximum=maximum
                )
            start_age = value if field == "start_age" else settings["start_age"]
            end_age = value if field == "end_age" else settings["end_age"]
            if end_age is not None and end_age < start_age:
                raise ValueError("Ending age must not precede starting age.")
            settings[field] = value
            formatted = "" if value is None else f"{value:,.0f}" if field == "amount" else f"{value:g}"
            self.after_idle(lambda: var.set(formatted))
        except ValueError as exc:
            formatted = "" if previous is None else f"{previous:,.0f}" if field == "amount" else f"{previous:g}"
            self.after_idle(lambda: var.set(formatted))
            mark_validation_failed(self)
            messagebox.showerror("Invalid QCD Input", f"{person.capitalize()} / {field}: {exc}", parent=self.winfo_toplevel())
        return True
