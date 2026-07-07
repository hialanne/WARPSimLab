# gui_notes.py

import tkinter as tk
from tkinter import ttk

import os
import sys
import subprocess


# ------------------------------------------------------------------
# Notes tab
# ------------------------------------------------------------------

class NotesFrame(ttk.Frame):

    BTN_WIDTH = 26

    def __init__(self, parent, title="Notes", **kwargs):
        super().__init__(parent, padding=10, **kwargs)
        self.title = title
        self._build_fields()

    def _build_fields(self):
        style = ttk.Style()

        style.configure("TutorialHeader.TLabel", font=("Arial", 12, "bold"))
        style.configure("TutorialButton.TButton", font=("Arial", 13, "bold"), padding=(12, 10))
        style.configure("TutorialBorder.TLabelframe", borderwidth=4, relief="solid")

        ttk.Label(
            self,
            text="Provides notes and technical documentation describing the model.",
            font=("Arial", 11),
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        # ---- Bordered container ----
        border = ttk.LabelFrame(self, style="TutorialBorder.TLabelframe")
        border.pack(fill="both", expand=True)

        # 2-column layout
        main = ttk.Frame(border, padding=8)
        main.pack(fill="both", expand=True)

        main.columnconfigure(0, weight=1)

        # ---- Right column: Technical Notes ----
        ttk.Label(
            main,
            text="Technical Notes",
            style="TutorialHeader.TLabel"
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

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
                btn_grid,
                text=label,
                style="TutorialButton.TButton",
                width=self.BTN_WIDTH,
                command=lambda fn=filename: self._open_pdf(fn),
            ).grid(row=r, column=c, sticky="w", padx=(0, 14) if c == 0 else 0, pady=6)

    def _open_pdf(self, pdf_filename: str):
        """
        Opens a PDF from the bundled docs/ directory when frozen,
        or from the source docs/ directory when running normally.
        """
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        pdf_path = os.path.join(base_dir, "docs", pdf_filename)

        if sys.platform.startswith("win"):
            os.startfile(pdf_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", pdf_path], check=False)
        else:
            subprocess.run(["xdg-open", pdf_path], check=False)