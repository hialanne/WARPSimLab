# gui_tutorial.py

import tkinter as tk
from tkinter import ttk

import os
import sys
import subprocess


# ------------------------------------------------------------------
# Tutorialstab
# ------------------------------------------------------------------

class TutorialFrame(ttk.Frame):
    """
    Tutorials tab:
    - Left column: Getting Started instructions
    - Right column: Getting started documents
    """

    BTN_WIDTH = 26

    def __init__(self, parent, title="Tutorials", **kwargs):
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
            text="Provides tutorials for using the simulator.",
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

        main.columnconfigure(0, weight=1, uniform="cols")
        main.columnconfigure(1, weight=1, uniform="cols")

        # ---- Left column: Getting Started ----
        ttk.Label(
            main,
            text="Getting Started",
            style="TutorialHeader.TLabel"
        ).grid(row=0, column=0, sticky="w", padx=(0, 30), pady=(0, 6))

        left_panel = ttk.Frame(main)
        left_panel.grid(row=1, column=0, sticky="nw", padx=(0, 30))

        ttk.Label(
            left_panel,
            text=(
                "1. Run Cashflow.\n"
                "2. Run Portfolio Balance.\n"
                "3. Run Summary.\n\n"
                "4. Change one input (e.g., retirement age or expenses).\n"
                "5. Run again and compare results.\n\n"
                "6. Customize Personal Data, Expenses, and Starting Assets.\n"
                "7. Run again and compare results.\n\n"
                "8. Click Mode (upper right) and select Advanced.\n"
                "9. Review tabs again - some tabs display additional options in Advanced mode.\n\n"
                "Make one change at a time to observe cause and effect."
            ),

            font=("Arial", 11),
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        # ---- Right column: Tutorials ----
        '''
        Getting Started (full story)

        Model Assumptions & Limitations

        Tax Modeling

        Portfolio Modeling

        Withdrawal Logic

        Monte Carlo & Uncertainty
        '''

        ttk.Label(
            main,
            text="Tutorial documents",
            style="TutorialHeader.TLabel"
        ).grid(row=0, column=1, sticky="w", pady=(0, 6))

        right_panel = ttk.Frame(main)
        right_panel.grid(row=1, column=1, sticky="nw")

        # ---- Two sub-columns for Technical Notes buttons ----
        btn_grid = ttk.Frame(right_panel)
        btn_grid.pack(anchor="nw")

        btn_grid.columnconfigure(0, weight=1, uniform="btncols")
        btn_grid.columnconfigure(1, weight=1, uniform="btncols")

        # (Button text, PDF filename) - filenames are best guesses; you can rename later.
        '''
        buttons = [
            ("Getting Started", "getting_started.pdf"),
            ("Getting Started - Advanced", "getting_started_advanced.pdf"),
            ("Beyond Getting Started", "beyond_getting_started.pdf"),
            ("Model Assumptions", "model_assumptions_limitations.pdf"),
            ("Tax Modeling", "tax_modeling.pdf"),
            ("Portfolio Modeling", "portfolio_modeling.pdf"),
            ("Withdrawal Logic", "withdrawal_logic.pdf"),
            ("Monte Carlo", "monte_carlo_uncertainty.pdf"),
        ]
        '''

        '''
        buttons = [
            ("Getting Started", "getting_started.pdf"),
            ("Getting Started - Advanced", "getting_started_advanced.pdf"),
            ("Users Manual", "users_manual.pdf"),
            ("Simulator Core", "sim_core.pdf"),
            ("Tax Modeling", "tax_modeling.pdf"),
            ("Scenario Explorer", "scenario_explorer.pdf"),
            ("Monte Carlo", "monte_carlo.pdf"),
            ("FAQ", "faq.pdf"),
        ]
        '''

        buttons = [
            ("Getting Started", "getting_started.pdf"),
            ("Getting Started - Advanced", "getting_started_advanced.pdf"),
        ]

        # Place buttons in 3 rows x 2 columns, reading top-to-bottom then left-to-right
        for i, (label, filename) in enumerate(buttons):
            r = i // 2   # 0..3
            c = i % 2    # 0..1
            ttk.Button(
                btn_grid,
                text=label,
                style="TutorialButton.TButton",
                width=self.BTN_WIDTH,
                command=lambda fn=filename: self._open_pdf(fn),
            ).grid(row=r, column=c, sticky="w", padx=(0, 14) if c == 0 else 0, pady=6)


    '''
    def _open_pdf(self, pdf_filename: str):
        """
        Opens a PDF from the docs/ directory.
        """
        pdf_path = os.path.join("src/docs", pdf_filename)

        if sys.platform.startswith("win"):
            os.startfile(pdf_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", pdf_path], check=False)
        else:
            subprocess.run(["xdg-open", pdf_path], check=False)
    '''

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

