# gui_annotations.py

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from src.warpsimlab.utils.tooltip import Tooltip
from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin


class AnnotationsEditFrame(ScalableFrameMixin, ttk.Frame):
    def __init__(self, parent, annotation_strings, title="Plot Annotations"):
        super().__init__(parent, padding=2)
        self.annotation_strings = annotation_strings  # reference
        self.row_vars = []  # store each row's vars to prevent GC

        self._body_font = tkfont.nametofont("TkDefaultFont").copy()
        self._tooltip_font = tkfont.Font(root=self, family="Arial", size=11)

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._tooltip_font)
        self._apply_gui_scale()

        # Headers
        for col, header in enumerate(["Annotation Text", "Delete"]):
            ttk.Label(self, text=header, font=self._body_font).grid(row=1, column=col, padx=5, pady=5)

        self.next_row = 2

        # Add button
        self.add_button = ttk.Button(
            self, text="Add Annotation", style="Annotations.TButton",
            command=self._add_new_annotation
        )
        self.add_button.grid(row=self.next_row, column=0, pady=(2, 2), sticky="w")

        # Populate existing
        for line in self.annotation_strings:
            self._add_annotation_row(line)


    def _add_new_annotation(self):
        line = [{"text":"", "color":None}]
        self.annotation_strings.append(line)
        self._add_annotation_row(line)


    def _apply_scaled_styles(self):
        # File: gui_userAnnotations.py; Function: _apply_scaled_styles
        # Action: Scale annotation editor buttons.
        style = ttk.Style(self)
        style.configure("Annotations.TButton", font=self._body_font)


    def _add_annotation_row(self, line):
        row = self.next_row
        text_var = tk.StringVar(value=line[0]["text"])

        # bind text_var to model
        text_var.trace_add("write", lambda *_: line[0].__setitem__("text", text_var.get()))

        # Entry
        entry = ttk.Entry(self, textvariable=text_var, width=40, font=self._body_font)
        entry.grid(row=row, column=0, padx=5, pady=2)
        Tooltip(entry, "Text displayed as a plot annotation", font=self._tooltip_font)

        # Delete
        del_btn = ttk.Button(
            self, text="Delete", style="Annotations.TButton",
            command=lambda l=line: self._delete_row(l)
        )
        del_btn.grid(row=row, column=1, padx=5, pady=2)
        Tooltip(del_btn, "Delete this annotation row", font=self._tooltip_font)

        # Save row info and var to prevent GC
        self.row_vars.append({
            "row": row,
            "annotation_line": line,
            "text_var": text_var,
            "widgets": [entry, del_btn]
        })

        self.next_row += 1
        self._update_add_button_position()

    def _delete_row(self, line):
        for item in self.row_vars:
            if item["annotation_line"] == line:
                for w in item["widgets"]:
                    w.destroy()
                self.row_vars.remove(item)
                break
        if line in self.annotation_strings:
            self.annotation_strings.remove(line)
        self._regrid_rows()

    def _regrid_rows(self):
        for i, item in enumerate(self.row_vars):
            row_index = 2 + i
            for col, w in enumerate(item["widgets"]):
                w.grid_configure(row=row_index, column=col)
            item["row"] = row_index
        self.next_row = 2 + len(self.row_vars)
        self._update_add_button_position()

    def _update_add_button_position(self):
        self.add_button.grid_configure(row=self.next_row, column=0, sticky="w")
