
# gui_sequenceRisk.py

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox

from src.warpsimlab.gui.gui_validation import mark_validation_failed, parse_integer
from src.warpsimlab.utils.tooltip import Tooltip
from src.warpsimlab.gui.gui_utils import bind_entry_commit_on_return
from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin


class SequenceRiskEditFrame(ScalableFrameMixin, ttk.Frame):
    def __init__(self, parent, control_vars, title="Sequence-of-Returns Scenarios", **kwargs):
        super().__init__(parent, padding=10, **kwargs)

        self.controls = control_vars["_controls_dict"]
        self.title = title

        self._body_font = tkfont.nametofont("TkDefaultFont").copy()
        self._header_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._section_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._description_font = tkfont.Font(root=self, family="Arial", size=10, slant="italic")
        self._tooltip_font = tkfont.Font(root=self, family="Arial", size=11)

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._header_font)
        self._register_scalable_font(self._section_font)
        self._register_scalable_font(self._description_font)
        self._register_scalable_font(self._tooltip_font)
        self._apply_gui_scale()

        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(header_frame, text=f"Retirement > {title}", font=self._header_font).pack(side="left")

        content_frame = ttk.Frame(self)
        content_frame.grid(row=1, column=0, sticky="nw")
        self._row = 0
        self._add_sequence_risk_controls(content_frame)

    def _apply_scaled_styles(self):
        style = ttk.Style(self)
        style.configure("Retirement.TCheckbutton", font=self._body_font)
        style.configure("Retirement.TMenubutton", font=self._body_font)

    def _next_row(self):
        r = self._row
        self._row += 1
        return r

    def _validate_sequence_start_year_offset(self, proposed_value):
        current_value = self.controls.get("sequence_risk_start_year_offset", 0)

        try:
            parsed = parse_integer(proposed_value, minimum=0)
            self.controls["sequence_risk_start_year_offset"] = parsed
            self.after_idle(lambda: self.sequence_risk_start_year_offset_var.set(str(parsed)))
            return True

        except ValueError as exc:
            self.after_idle(lambda: self.sequence_risk_start_year_offset_var.set(str(current_value)))
            mark_validation_failed(self)
            messagebox.showerror(
                "Invalid Input",
                f"Retirement / Years From Simulation Start: {exc}",
                parent=self.winfo_toplevel()
            )
            return True

    def _add_sequence_risk_controls(self, parent):
        ttk.Label(
            parent, text="Sequence-of-Returns Scenarios (Optional)", font=self._section_font
        ).grid(row=self._next_row(), column=0, columnspan=2, sticky="w", pady=(0, 6))

        ttk.Label(
            parent,
            text=(
                "Use these controls to explore how a downturn at different points in retirement "
                "might affect withdrawal outcomes. These settings are educational scenario inputs only."
            ),
            justify="left", wraplength=360, font=self._description_font
        ).grid(row=self._next_row(), column=0, columnspan=2, sticky="w", pady=(0, 10))

        if "sequence_risk_enabled" not in self.controls:
            self.controls["sequence_risk_enabled"] = False

        if "sequence_risk_timing" not in self.controls:
            self.controls["sequence_risk_timing"] = "Early downturn"

        if "sequence_risk_start_year_offset" not in self.controls:
            self.controls["sequence_risk_start_year_offset"] = 0

        if "sequence_risk_length" not in self.controls:
            self.controls["sequence_risk_length"] = "Medium"

        if "sequence_risk_depth" not in self.controls:
            self.controls["sequence_risk_depth"] = "Moderate"

        self.sequence_risk_enabled_var = tk.BooleanVar(value=self.controls["sequence_risk_enabled"])
        self.sequence_risk_timing_var = tk.StringVar(value=self.controls["sequence_risk_timing"])
        self.sequence_risk_start_year_offset_var = tk.StringVar(
            value=str(self.controls["sequence_risk_start_year_offset"])
        )
        self.sequence_risk_length_var = tk.StringVar(value=self.controls["sequence_risk_length"])
        self.sequence_risk_depth_var = tk.StringVar(value=self.controls["sequence_risk_depth"])

        self.sequence_risk_enabled_var.trace_add(
            "write", lambda *args: self.controls.__setitem__(
                "sequence_risk_enabled", self.sequence_risk_enabled_var.get()
            )
        )

        def on_sequence_timing_changed(*args):
            self.controls["sequence_risk_timing"] = self.sequence_risk_timing_var.get()

            if hasattr(self, "sequence_start_year_frame"):
                self._update_sequence_risk_visibility()

        self.sequence_risk_timing_var.trace_add("write", on_sequence_timing_changed)

        self.sequence_risk_length_var.trace_add(
            "write", lambda *args: self.controls.__setitem__(
                "sequence_risk_length", self.sequence_risk_length_var.get()
            )
        )

        self.sequence_risk_depth_var.trace_add(
            "write", lambda *args: self.controls.__setitem__(
                "sequence_risk_depth", self.sequence_risk_depth_var.get()
            )
        )

        self.sequence_enabled_cb = ttk.Checkbutton(
            parent, text="Include Sequence-of-Returns Scenarios",
            variable=self.sequence_risk_enabled_var,
            command=self._update_sequence_risk_visibility, style="Retirement.TCheckbutton"
        )
        self.sequence_enabled_cb.grid(row=self._next_row(), column=0, columnspan=2, sticky="w", pady=2)

        Tooltip(
            self.sequence_enabled_cb,
            "Turns on optional sequence-of-returns scenario inputs for retirement modeling.",
            font=self._tooltip_font
        )

        self.sequence_timing_frame = ttk.Frame(parent)
        self.sequence_timing_frame.grid(row=self._next_row(), column=0, columnspan=2, sticky="w", pady=4)

        ttk.Label(
            self.sequence_timing_frame, text="Scenario Timing:", font=self._body_font
        ).pack(side="left")

        self.sequence_timing_menu = ttk.OptionMenu(
            self.sequence_timing_frame, self.sequence_risk_timing_var, self.sequence_risk_timing_var.get(),
            "Early downturn", "Mid-retirement downturn", "Late downturn", "Custom",
            style="Retirement.TMenubutton"
        )
        self.sequence_timing_menu.pack(side="left", padx=5)
        self.sequence_timing_menu["menu"].configure(font=self._body_font)

        Tooltip(
            self.sequence_timing_menu,
            "Choose when the downturn occurs. Select Custom to enter a year offset from simulation start.",
            font=self._tooltip_font
        )

        self.sequence_start_year_frame = ttk.Frame(parent)
        self.sequence_start_year_frame.grid(row=self._next_row(), column=0, columnspan=2, sticky="w", pady=4)

        ttk.Label(
            self.sequence_start_year_frame, text="Years From Simulation Start:", font=self._body_font
        ).pack(side="left")

        vcmd = self.register(self._validate_sequence_start_year_offset), "%P"

        self.sequence_start_year_entry = ttk.Entry(
            self.sequence_start_year_frame, textvariable=self.sequence_risk_start_year_offset_var,
            width=6, font=self._body_font, validate="focusout", validatecommand=vcmd
        )
        self.sequence_start_year_entry.pack(side="left", padx=5)
        bind_entry_commit_on_return(self.sequence_start_year_entry)

        Tooltip(
            self.sequence_start_year_entry,
            "Used only when Scenario Timing is Custom.\n"
            "Enter the number of years after simulation start when the downturn begins.\n"
            "Example: 5 means the downturn begins 5 years into the simulation.",
            font=self._tooltip_font
        )

        self.sequence_length_frame = ttk.Frame(parent)
        self.sequence_length_frame.grid(row=self._next_row(), column=0, columnspan=2, sticky="w", pady=4)

        ttk.Label(
            self.sequence_length_frame, text="Scenario Length:", font=self._body_font
        ).pack(side="left")

        self.sequence_length_menu = ttk.OptionMenu(
            self.sequence_length_frame, self.sequence_risk_length_var, self.sequence_risk_length_var.get(),
            "Short", "Medium", "Long", style="Retirement.TMenubutton"
        )
        self.sequence_length_menu.pack(side="left", padx=5)
        self.sequence_length_menu["menu"].configure(font=self._body_font)

        Tooltip(
            self.sequence_length_menu,
            "Controls the duration category of the downturn scenario.",
            font=self._tooltip_font
        )

        self.sequence_depth_frame = ttk.Frame(parent)
        self.sequence_depth_frame.grid(row=self._next_row(), column=0, columnspan=2, sticky="w", pady=4)

        ttk.Label(
            self.sequence_depth_frame, text="Scenario Depth:", font=self._body_font
        ).pack(side="left")

        self.sequence_depth_menu = ttk.OptionMenu(
            self.sequence_depth_frame, self.sequence_risk_depth_var, self.sequence_risk_depth_var.get(),
            "Mild", "Moderate", "Severe", style="Retirement.TMenubutton"
        )
        self.sequence_depth_menu.pack(side="left", padx=5)
        self.sequence_depth_menu["menu"].configure(font=self._body_font)

        Tooltip(
            self.sequence_depth_menu,
            "Controls the severity category of the downturn scenario.",
            font=self._tooltip_font
        )

        self._update_sequence_risk_visibility()

    def _update_sequence_risk_visibility(self):
        required_attrs = (
            "sequence_timing_frame", "sequence_start_year_frame", "sequence_length_frame",
            "sequence_depth_frame", "sequence_risk_enabled_var", "sequence_risk_timing_var"
        )

        if not all(hasattr(self, attr) for attr in required_attrs):
            return

        enabled = self.sequence_risk_enabled_var.get()
        base_state = "normal" if enabled else "disabled"

        for frame in (self.sequence_timing_frame, self.sequence_length_frame, self.sequence_depth_frame):
            for widget in frame.winfo_children():
                try:
                    widget.configure(state=base_state)
                except tk.TclError:
                    pass

        custom_state = "normal" if enabled and self.sequence_risk_timing_var.get() == "Custom" else "disabled"

        for widget in self.sequence_start_year_frame.winfo_children():
            try:
                widget.configure(state=custom_state)
            except tk.TclError:
                pass
