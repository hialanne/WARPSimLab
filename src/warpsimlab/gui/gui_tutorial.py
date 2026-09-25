# gui_tutorial.py

import os
import sys
import subprocess

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin


# ------------------------------------------------------------------
# Tutorialstab
# ------------------------------------------------------------------

class TutorialFrame(ScalableFrameMixin, ttk.Frame):
    """
    Tutorials tab:
    - Left column: Getting Started instructions
    - Right column: Getting started documents
    """

    BTN_WIDTH = 26

    def __init__(
        self,
        parent,
        start_basic_tutorial_callback=None,
        start_advanced_building_tutorial_callback=None,
        start_advanced_analysis_tutorial_callback=None,
        title="Tutorials",
        **kwargs
    ):
        super().__init__(parent, padding=10, **kwargs)
        self._body_font = tkfont.Font(root=self, family="Arial", size=11)
        self._header_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._button_font = tkfont.Font(root=self, family="Arial", size=13, weight="bold")
        self._section_title_font = tkfont.Font(root=self, family="Arial", size=13, weight="bold")
        self._card_font = tkfont.nametofont("TkDefaultFont").copy()

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._header_font)
        self._register_scalable_font(self._button_font)
        self._register_scalable_font(self._section_title_font)
        self._register_scalable_font(self._card_font)
        self._apply_gui_scale()

        self.start_basic_tutorial_callback = (
            start_basic_tutorial_callback
        )
        self.start_advanced_building_tutorial_callback = (
            start_advanced_building_tutorial_callback
        )
        self.start_advanced_analysis_tutorial_callback = (
            start_advanced_analysis_tutorial_callback
        )
        self.title = title

        self._build_fields()


    def _apply_scaled_styles(self):
        style = ttk.Style(self)
        style.configure("TutorialSectionTitle.TLabel", font=self._section_title_font)
        style.configure("TutorialButton.TButton", font=self._button_font, padding=(12, 10))
        style.configure("TutorialCard.TLabelframe", borderwidth=2, relief="solid")
        style.configure("TutorialCard.TLabelframe.Label", font=self._card_font)


    def _build_fields(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(
            anchor="w",
            fill="x",
            pady=(0, 14),
        )

        ttk.Label(header_frame, text="Home > Tutorials", font=self._header_font).pack(side="left")

        ttk.Label(
            header_frame,
            text=(
                " - Choose a guided tutorial based on what you want to learn. "
                "Tutorials use the financial data currently loaded and do not "
                "reset your scenario."
            ),
            font=self._body_font,
        ).pack(side="left")

        tutorials_container = ttk.Frame(self)
        tutorials_container.pack(fill="x", expand=False)

        # Basic Tutorial
        basic_frame = ttk.LabelFrame(
            tutorials_container,
            text="Basic Tutorial",
            style="TutorialCard.TLabelframe",
            padding=12,
        )
        basic_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            basic_frame,
            text=(
                "Learn the primary income, expense, and portfolio inputs. "
                "Run a simulation, review the Simulation Summary, change an input, "
                "compare results, and save your work.  This tutorial assums that "
                "Mode is set to Basic."
            ),
            font=self._body_font,
            wraplength=850,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        if self.start_basic_tutorial_callback is not None:
            ttk.Button(
                basic_frame,
                text="Start Basic Tutorial",
                style="TutorialButton.TButton",
                width=self.BTN_WIDTH,
                command=self.start_basic_tutorial_callback,
            ).pack(anchor="w")

        # Advanced Tutorial 1
        advanced_build_frame = ttk.LabelFrame(
            tutorials_container,
            text="Advanced Tutorial 1: Build the Simulation",
            style="TutorialCard.TLabelframe",
            padding=12,
        )
        advanced_build_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            advanced_build_frame,
            text=(
                "Configure detailed income, assets, real estate, retirement "
                "spending, market assumptions, simulation settings, and "
                "display controls."
            ),
            font=self._body_font,
            wraplength=850,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        if self.start_advanced_building_tutorial_callback is not None:
            ttk.Button(
                advanced_build_frame,
                text="Start Building Tutorial",
                style="TutorialButton.TButton",
                width=self.BTN_WIDTH,
                command=self.start_advanced_building_tutorial_callback,
            ).pack(anchor="w")

        # Advanced Tutorial 2
        advanced_analysis_frame = ttk.LabelFrame(
            tutorials_container,
            text="Advanced Tutorial 2: Analyze Results",
            style="TutorialCard.TLabelframe",
            padding=12,
        )
        advanced_analysis_frame.pack(fill="x", pady=(0, 14))

        ttk.Label(
            advanced_analysis_frame,
            text=(
                "Review result plots, experiment with Scenario Explorer, "
                "generate reports, and examine tax and portfolio-risk results."
            ),
            font=self._body_font,
            wraplength=850,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        if self.start_advanced_analysis_tutorial_callback is not None:
            ttk.Button(
                advanced_analysis_frame,
                text="Start Analysis Tutorial",
                style="TutorialButton.TButton",
                width=self.BTN_WIDTH,
                command=self.start_advanced_analysis_tutorial_callback,
            ).pack(anchor="w")

        # Reference Guides
        reference_frame = ttk.LabelFrame(
            self,
            text="Reference Guides",
            style="TutorialCard.TLabelframe",
            padding=12,
        )
        reference_frame.pack(fill="x", pady=(0, 4))

        ttk.Label(
            reference_frame,
            text=(
                "These PDF guides provide additional written reference material."
            ),
            font=self._body_font,
            wraplength=850,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        button_frame = ttk.Frame(reference_frame)
        button_frame.pack(anchor="w")

        reference_buttons = [
            ("Getting Started Guide", "getting_started.pdf"),
            ("Advanced Guide", "getting_started_advanced.pdf"),
        ]

        for label, filename in reference_buttons:
            ttk.Button(
                button_frame,
                text=label,
                style="TutorialButton.TButton",
                width=self.BTN_WIDTH,
                command=lambda fn=filename: self._open_pdf(fn),
            ).pack(side="left", padx=(0, 12))


    def _open_pdf(self, pdf_filename: str):
        """
        Opens a PDF from the bundled docs/ directory when frozen,
        or from the source docs/ directory when running normally.
        """
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )

        pdf_path = os.path.join(base_dir, "docs", pdf_filename)

        #print(f"DEBUG _open_pdf base_dir = {base_dir}")
        #print(f"DEBUG _open_pdf pdf_path = {pdf_path}")
        #print(f"DEBUG _open_pdf exists   = {os.path.exists(pdf_path)}")

        #if not os.path.exists(pdf_path):
        #    print(f"PDF not found: {pdf_path}")
        #    return

        if sys.platform.startswith("win"):
            os.startfile(pdf_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", pdf_path], check=False)
        else:
            subprocess.run(["xdg-open", pdf_path], check=False)

