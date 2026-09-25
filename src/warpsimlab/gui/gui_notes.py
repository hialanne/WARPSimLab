# gui_notes.py

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

import os
import sys
import subprocess

from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin


# ------------------------------------------------------------------
# Notes tab
# ------------------------------------------------------------------

class NotesFrame(ScalableFrameMixin, ttk.Frame):

    BTN_WIDTH = 26

    def __init__(self, parent, title="Notes", **kwargs):
        super().__init__(parent, padding=10, **kwargs)
        self.title = title

        self._body_font = tkfont.Font(root=self, family="Arial", size=11)
        self._header_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._section_font = tkfont.Font(root=self, family="Arial", size=12, weight="bold")
        self._button_font = tkfont.Font(root=self, family="Arial", size=13, weight="bold")

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._header_font)
        self._register_scalable_font(self._section_font)
        self._register_scalable_font(self._button_font)
        self._apply_gui_scale()

        self._build_fields()

    def _apply_scaled_styles(self):
        style = ttk.Style(self)
        style.configure("NotesHeader.TLabel", font=self._section_font)
        style.configure("NotesButton.TButton", font=self._button_font, padding=(12, 10))
        style.configure("NotesBorder.TLabelframe", borderwidth=4, relief="solid")

    def _build_fields(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(anchor="w", fill="x", pady=(0, 8))

        ttk.Label(header_frame, text="Home > Notes", font=self._header_font).pack(side="left")

        ttk.Label(
            header_frame,
            text=" - Provides notes and technical documentation describing the model.",
            font=self._body_font,
        ).pack(side="left")

        # ---- Bordered container ----
        border = ttk.LabelFrame(self, style="NotesBorder.TLabelframe")
        border.pack(fill="both", expand=True)

        # 2-column layout
        main = ttk.Frame(border, padding=8)
        main.pack(fill="both", expand=True)

        main.columnconfigure(0, weight=1)

        # ---- Right column: Technical Notes ----
        ttk.Label(main, text="Technical Notes", style="NotesHeader.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )

        right_panel = ttk.Frame(main)
        right_panel.grid(row=1, column=0, sticky="nw")

        # ---- Two sub-columns for Technical Notes buttons ----
        btn_grid = ttk.Frame(right_panel)
        btn_grid.pack(anchor="nw")

        btn_grid.columnconfigure(0, weight=1, uniform="btncols")
        btn_grid.columnconfigure(1, weight=1, uniform="btncols")

        buttons = [
            ("FAQ", "faq.pdf"),
        ]

        for i, (label, filename) in enumerate(buttons):
            r = i // 2
            c = i % 2
            ttk.Button(
                btn_grid, text=label, style="NotesButton.TButton", width=self.BTN_WIDTH,
                command=lambda fn=filename: self._open_pdf(fn)
            ).grid(row=r, column=c, sticky="w", padx=(0, 14) if c == 0 else 0, pady=6)

    def _open_pdf(self, pdf_filename: str):
        """
        Opens a PDF from the bundled docs/ directory when frozen,
        or from the source docs/ directory when running normally.
        """
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        pdf_path = os.path.join(base_dir, "docs", pdf_filename)

        if sys.platform.startswith("win"):
            os.startfile(pdf_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", pdf_path], check=False)
        else:
            subprocess.run(["xdg-open", pdf_path], check=False)