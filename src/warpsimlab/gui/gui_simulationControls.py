# gui_simulationControls.py

import os
from tkinter import filedialog
import tkinter as tk
from tkinter import ttk

from src.warpsimlab.utils.tooltip import Tooltip
from .gui_userAnnotations import AnnotationsEditFrame


class SimulationControlsEditFrame(ttk.Frame):

    def __init__(self, parent, control_vars, title="Simulation Controls"):
        super().__init__(parent, padding=10)

        self.controls = control_vars["_controls_dict"]

        # Ensure defaults exist
        self.controls.setdefault("include_realestate", False)
        self.controls.setdefault("constant_y_plots", False)
        self.controls.setdefault("rebalance_every_year", False)

        self.controls.setdefault("overlay_tax_impacts", False)
        self.controls.setdefault("overlay_fund_expense_impacts", False)
        self.controls.setdefault("overlay_household_expenses", False)
        self.controls.setdefault("overlay_profit_loss", True)
        self.controls.setdefault("overlay_retirement_age", False)

        self.controls.setdefault("user_annotation_strings", [])
        self.controls.setdefault("annotate_plots", False)

        self.controls.setdefault("plot_mode", "real")
        self.controls.setdefault("subplot_mode", "fill")
        self.controls.setdefault("monte_carlo_plot_style", "fill")
        self.controls.setdefault("use_correlated_returns", True)
        self.controls.setdefault("show_simulated_shortfall_rate", True)
        self.controls.setdefault("monte_carlo_mode", "pathBasedAnnualSampling")
        self.controls.setdefault("historical_asset_returns_file", "us_asset_returns_1876_2025.csv")
        self.controls.setdefault("historical_inflation_file", "us_inflation_1876_2025_real.csv")
        self.controls.setdefault("historical_window_mode", "rolling_overlapping_all")
        self.controls.setdefault("disable_sequence_risk_for_historical", True)

        self.controls.setdefault("output_csv", "None")
        default_dir = os.path.join(os.path.expanduser("~"), "Desktop", "WARPSimLab")
        self.controls.setdefault("csv_output_dir", default_dir)

        # Outer grid config
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)

        # Description
        ttk.Label(
            self,
            text="Controls how simulation results are displayed, exported, and annotated.",
            font=("Arial", 11),
            wraplength=900,
            justify="left",
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        # Top-level layout:
        # left_panel spans outer columns 0-1
        # right_panel spans outer columns 2-3
        left_panel = ttk.Frame(self)
        left_panel.grid(row=1, column=0, columnspan=2, sticky="nw", padx=(0, 30))

        right_panel = ttk.Frame(self)
        right_panel.grid(row=1, column=2, columnspan=2, sticky="nw")

        # Internal column config for left panel
        left_panel.columnconfigure(0, weight=0, minsize=300)
        left_panel.columnconfigure(1, weight=0, minsize=300)

        # Two independent child columns inside right_panel
        right_panel.columnconfigure(0, weight=0)
        right_panel.columnconfigure(1, weight=0)

        right_left_col = ttk.Frame(right_panel)
        right_left_col.grid(row=0, column=0, sticky="nw")

        right_right_col = ttk.Frame(right_panel)
        right_right_col.grid(row=0, column=1, sticky="nw", padx=(30, 0))

        # -------------------------------------------------
        # LEFT PANEL, COLUMN 0: General checkboxes
        # -------------------------------------------------
        left_col0_row = 0

        def add_left_check(label, key, tooltip_text=None):
            nonlocal left_col0_row

            var = tk.BooleanVar(value=self.controls.get(key, False))
            var.trace_add(
                "write",
                lambda *_args, k=key, v=var: self.controls.__setitem__(k, v.get())
            )

            cb = ttk.Checkbutton(left_panel, text=label, variable=var)
            cb.grid(row=left_col0_row, column=0, sticky="w", pady=2, padx=(0, 20))
            Tooltip(cb, tooltip_text or f"{label}.", font=("Arial", 11))

            left_col0_row += 1

        add_left_check("Constant Y Plots", "constant_y_plots")
        add_left_check("Rebalance Every Year", "rebalance_every_year")

        # -------------------------------------------------
        # LEFT PANEL, COLUMN 1: Overlays
        # -------------------------------------------------
        left_col1_row = 0

        ttk.Label(left_panel, text="Overlays", font=("Arial", 12, "bold")).grid(
            row=left_col1_row, column=1, sticky="w", pady=(0, 5)
        )
        left_col1_row += 1

        def add_overlay_check(label, key, tooltip_text):
            nonlocal left_col1_row

            var = tk.BooleanVar(value=self.controls.get(key, False))
            var.trace_add(
                "write",
                lambda *_args, k=key, v=var: self.controls.__setitem__(k, v.get())
            )

            cb = ttk.Checkbutton(left_panel, text=label, variable=var)
            cb.grid(row=left_col1_row, column=1, sticky="w", pady=2)
            Tooltip(cb, tooltip_text, font=("Arial", 11))

            left_col1_row += 1

        add_overlay_check(
            "Tax Impacts",
            "overlay_tax_impacts",
            "Add overlay of tax impacts\nOnly used for Portfolio Plots"
        )
        add_overlay_check(
            "Fund Expense Impacts",
            "overlay_fund_expense_impacts",
            "Add overlay of fund expense impacts\nOnly used for Portfolio Plots"
        )
        add_overlay_check(
            "Household Expense Line Plot",
            "overlay_household_expenses",
            "Add overlay of household expenses\nOnly used for Income Plots"
        )
        add_overlay_check(
            "Household Profit/Loss Line Plot",
            "overlay_profit_loss",
            "Add overlay of profit/losses\nOnly used for Income Plots"
        )
        add_overlay_check(
            "Mark Last Retirement Age",
            "overlay_retirement_age",
            "Add a vertical line to mark last retirement age of husband or wife"
        )

        # -------------------------------------------------
        # LEFT PANEL BOTTOM: Annotations spanning both columns
        # -------------------------------------------------
        annotations_row = max(left_col0_row, left_col1_row) + 1

        annotations_section = ttk.Frame(left_panel)
        annotations_section.grid(
            row=annotations_row,
            column=0,
            columnspan=2,
            sticky="nw",
            pady=(8, 2)
        )

        annotations_header = ttk.Frame(annotations_section)
        annotations_header.pack(anchor="w", fill="x", pady=(0, 2))

        ttk.Label(
            annotations_header,
            text="Custom Annotations",
            font=("Arial", 12, "bold")
        ).pack(side="left")

        self.annotate_var = tk.BooleanVar(
            value=self.controls.get("annotate_plots", False)
        )

        annotate_cb = ttk.Checkbutton(
            annotations_header,
            text="Enable",
            variable=self.annotate_var
        )
        annotate_cb.pack(side="left", padx=(10, 0))
        Tooltip(
            annotate_cb,
            "Enable or disable custom plot annotations.",
            font=("Arial", 11)
        )

        self.annotate_var.trace_add(
            "write",
            lambda *_: self.controls.__setitem__("annotate_plots", self.annotate_var.get())
        )

        self.annotations_editor = AnnotationsEditFrame(
            parent=annotations_section,
            annotation_strings=self.controls["user_annotation_strings"],
            title=None
        )
        self.annotations_editor.pack(anchor="w", fill="x", pady=(0, 5))

        def _update_annotation_editor_state(*_):
            state = "normal" if self.annotate_var.get() else "disabled"
            for item in self.annotations_editor.row_vars:
                for widget in item["widgets"]:
                    widget.configure(state=state)
            self.annotations_editor.add_button.configure(state=state)

        _update_annotation_editor_state()
        self.annotate_var.trace_add("write", _update_annotation_editor_state)


        # -------------------------------------------------
        # RIGHT PANEL, COLUMN 0: Real/Nominal + Plot Style
        # RIGHT PANEL, COLUMN 1: reserved for Monte Carlo controls later
        # -------------------------------------------------
        right_col0_row = 0

        # Real/Nominal Mode
        ttk.Label(right_left_col, text="Real/Nominal Mode").grid(
            row=right_col0_row, column=0, sticky="w", pady=(0, 2)
        )
        right_col0_row += 1

        plot_mode_var = tk.StringVar(
            value="real" if self.controls.get("plot_mode") == "real" else "raw"
        )

        plot_mode_frame = ttk.Frame(right_left_col)
        plot_mode_frame.grid(row=right_col0_row, column=0, sticky="nw", pady=2)
        right_col0_row += 1

        real_rb = ttk.Radiobutton(
            plot_mode_frame,
            text="Real (inflation-adjusted)",
            variable=plot_mode_var,
            value="real"
        )
        real_rb.grid(row=0, column=0, sticky="w", pady=1)
        Tooltip(real_rb, "Show inflation-adjusted values.", font=("Arial", 11))

        raw_rb = ttk.Radiobutton(
            plot_mode_frame,
            text="Raw (nominal)",
            variable=plot_mode_var,
            value="raw"
        )
        raw_rb.grid(row=1, column=0, sticky="w", pady=1)
        Tooltip(raw_rb, "Show non-inflation-adjusted nominal values.", font=("Arial", 11))

        def on_plot_mode_changed(*_):
            self.controls["plot_mode"] = plot_mode_var.get()

        plot_mode_var.trace_add("write", on_plot_mode_changed)

        # Small spacer
        right_col0_row += 1

        # Plot Style
        ttk.Label(right_left_col, text="Plot Style").grid(
            row=right_col0_row, column=0, sticky="w", pady=(14, 2)
        )
        right_col0_row += 1

        subplot_mode_label_to_value = {
            "Fill": "fill",
            "Percentile Bands": "monte_carlo",
            "Sub Categories": "sub_categories",
            "Pre / Post Tax Savings": "pre_post_tax",
        }
        subplot_mode_value_to_label = {v: k for k, v in subplot_mode_label_to_value.items()}

        subplot_mode_var = tk.StringVar(
            value=subplot_mode_value_to_label.get(
                self.controls.get("subplot_mode", "fill"),
                "Fill"
            )
        )

        plot_style_frame = ttk.Frame(right_left_col)
        plot_style_frame.grid(row=right_col0_row, column=0, sticky="nw", pady=2)
        right_col0_row += 1

        plot_style_options = [
            "Fill",
            "Percentile Bands",
            "Sub Categories",
            "Pre / Post Tax Savings",
        ]

        for i, option in enumerate(plot_style_options):
            rb = ttk.Radiobutton(
                plot_style_frame,
                text=option,
                variable=subplot_mode_var,
                value=option
            )
            rb.grid(row=i, column=0, sticky="w", pady=1)
            Tooltip(rb, f"Use {option} plot style.", font=("Arial", 11))

        def on_subplot_mode_changed(*_):
            previous_mode = self.controls.get("subplot_mode", "fill")
            new_mode = subplot_mode_label_to_value[subplot_mode_var.get()]

            self.controls["subplot_mode"] = new_mode

            if previous_mode == "monte_carlo" and new_mode != "monte_carlo":
                self.controls["monte_carlo_mode"] = "rollingHistoricalWindows"
                monte_carlo_mode_var.set("rollingHistoricalWindows")

            update_include_realestate_visibility()

        subplot_mode_var.trace_add("write", on_subplot_mode_changed)

        # Simulated Shortfall Rate
        shortfall_var = tk.BooleanVar(
            value=self.controls.get("show_simulated_shortfall_rate", True)
        )

        shortfall_cb = ttk.Checkbutton(
            right_left_col,
            text="Show Simulated Shortfall Rate",
            variable=shortfall_var
        )
        shortfall_cb.grid(row=right_col0_row, column=0, sticky="w", pady=(10, 2))
        Tooltip(
            shortfall_cb,
            "Display the share of Monte Carlo runs that end in shortfall. "
            "This is a simulation outcome summary for educational use and is not financial advice.",
            font=("Arial", 11)
        )

        def on_shortfall_changed(*_):
            self.controls["show_simulated_shortfall_rate"] = shortfall_var.get()

        shortfall_var.trace_add("write", on_shortfall_changed)

        right_col0_row += 1

        # -------------------------------------------------
        # RIGHT PANEL, COLUMN 0: Real Estate visibility tied to Plot Style
        # hidden for Monte Carlo
        # -------------------------------------------------
        include_realestate_section = ttk.Frame(right_right_col)
        include_realestate_section.grid(
            row=0,
            column=0,
            sticky="nw"
        )

        include_realestate_var = tk.BooleanVar(
            value=self.controls.get("include_realestate", False)
        )

        include_realestate_cb = ttk.Checkbutton(
            include_realestate_section,
            text="Include Real Estate in Simulation",
            variable=include_realestate_var
        )
        include_realestate_cb.grid(row=0, column=0, sticky="w", pady=2)
        Tooltip(
            include_realestate_cb,
            "Include real estate in simulation results. Hidden when Plot Style is Monte Carlo.",
            font=("Arial", 11)
        )

        def on_include_realestate_changed(*_):
            self.controls["include_realestate"] = include_realestate_var.get()

        include_realestate_var.trace_add("write", on_include_realestate_changed)

        def update_include_realestate_visibility(*_):
            visible_plot_styles = {
                "Fill",
                "Sub Categories",
                "Pre / Post Tax Savings",
            }
            if subplot_mode_var.get() in visible_plot_styles:
                include_realestate_section.grid()
            else:
                include_realestate_section.grid_remove()

        update_include_realestate_visibility()


        # -------------------------------------------------
        # RIGHT PANEL, COLUMN 1: Monte Carlo options
        # hidden unless Plot Style = Monte Carlo
        # -------------------------------------------------
        monte_carlo_section = ttk.Frame(right_right_col)
        monte_carlo_section.grid(
            row=0,
            column=0,
            sticky="nw"
        )

        ttk.Label(
            monte_carlo_section,
            text="Percentile Bands Mode"
        ).grid(row=0, column=0, sticky="w", pady=(0, 2))

        monte_carlo_mode_var = tk.StringVar(
            value=self.controls.get("monte_carlo_mode", "pathBasedAnnualSampling")
        )

        monte_carlo_mode_frame = ttk.Frame(monte_carlo_section)
        monte_carlo_mode_frame.grid(row=1, column=0, sticky="nw", pady=2)

        mc_mode_path_rb = ttk.Radiobutton(
            monte_carlo_mode_frame,
            text="Monte Carlo",
            variable=monte_carlo_mode_var,
            value="pathBasedAnnualSampling"
        )
        mc_mode_path_rb.grid(row=0, column=0, sticky="w", pady=1)
        Tooltip(
            mc_mode_path_rb,
            "Sample one full annual return path using the configured return assumptions.",
            font=("Arial", 11)
        )

        mc_mode_historical_rb = ttk.Radiobutton(
            monte_carlo_mode_frame,
            text="Historical Windows",
            variable=monte_carlo_mode_var,
            value="rollingHistoricalWindows"
        )
        mc_mode_historical_rb.grid(row=2, column=0, sticky="w", pady=1)
        Tooltip(
            mc_mode_historical_rb,
            "Run all overlapping rolling historical return windows from the historical CSV file.",
            font=("Arial", 11)
        )

        def on_monte_carlo_mode_changed(*_):
            self.controls["monte_carlo_mode"] = monte_carlo_mode_var.get()
            update_monte_carlo_dependent_visibility()

        monte_carlo_mode_var.trace_add("write", on_monte_carlo_mode_changed)

        # Monte Carlo Plot Style
        ttk.Label(
            monte_carlo_section,
            text="Percentile Bands Plot Style"
        ).grid(row=3, column=0, sticky="w", pady=(20, 2))

        monte_carlo_plot_style_var = tk.StringVar(
            value=self.controls.get("monte_carlo_plot_style", "fill")
        )

        monte_carlo_plot_style_frame = ttk.Frame(monte_carlo_section)
        monte_carlo_plot_style_frame.grid(row=4, column=0, sticky="nw", pady=2)

        mc_plot_fill_rb = ttk.Radiobutton(
            monte_carlo_plot_style_frame,
            text="fill",
            variable=monte_carlo_plot_style_var,
            value="fill"
        )
        mc_plot_fill_rb.grid(row=0, column=0, sticky="w", pady=1)
        Tooltip(mc_plot_fill_rb, "Display Monte Carlo results using a filled band.", font=("Arial", 11))

        mc_plot_line_rb = ttk.Radiobutton(
            monte_carlo_plot_style_frame,
            text="line",
            variable=monte_carlo_plot_style_var,
            value="line"
        )
        mc_plot_line_rb.grid(row=1, column=0, sticky="w", pady=1)
        Tooltip(mc_plot_line_rb, "Display Monte Carlo results using summary lines.", font=("Arial", 11))

        mc_plot_all_lines_rb = ttk.Radiobutton(
            monte_carlo_plot_style_frame,
            text="all_lines",
            variable=monte_carlo_plot_style_var,
            value="all_lines"
        )
        mc_plot_all_lines_rb.grid(row=2, column=0, sticky="w", pady=1)
        Tooltip(mc_plot_all_lines_rb, "Display all Monte Carlo paths as lines.", font=("Arial", 11))

        def on_monte_carlo_plot_style_changed(*_):
            self.controls["monte_carlo_plot_style"] = monte_carlo_plot_style_var.get()

        monte_carlo_plot_style_var.trace_add("write", on_monte_carlo_plot_style_changed)

        correlated_returns_var = tk.BooleanVar(
            value=self.controls.get("use_correlated_returns", True)
        )

        correlated_returns_cb = ttk.Checkbutton(
            monte_carlo_section,
            text="Correlated Asset Returns",
            variable=correlated_returns_var
        )
        correlated_returns_cb.grid(row=5, column=0, sticky="w", pady=(8, 2))
        Tooltip(
            correlated_returns_cb,
            "Use correlated annual returns across asset classes in Monte Carlo mode.",
            font=("Arial", 11)
        )

        def on_correlated_returns_changed(*_):
            val = correlated_returns_var.get()
            self.controls["use_correlated_returns"] = val

        correlated_returns_var.trace_add("write", on_correlated_returns_changed)

        historical_note = ttk.Label(
            monte_carlo_section,
            text="Historical Windows uses annual returns from the historical CSV file.\n"
                 "Correlated returns do not apply in this mode.",
            justify="left"
        )
        historical_note.grid(row=6, column=0, sticky="w", pady=(8, 2))

        def update_monte_carlo_dependent_visibility(*_):
            is_historical = (monte_carlo_mode_var.get() == "rollingHistoricalWindows")

            if is_historical:
                correlated_returns_cb.state(["disabled"])
                historical_note.grid()
            else:
                correlated_returns_cb.state(["!disabled"])
                historical_note.grid_remove()

        def update_monte_carlo_visibility(*_):
            is_monte_carlo = (subplot_mode_label_to_value[subplot_mode_var.get()] == "monte_carlo")
            
            if is_monte_carlo:
                monte_carlo_section.grid()
            else:
                monte_carlo_section.grid_remove()

        subplot_mode_var.trace_add("write", update_monte_carlo_visibility)
        update_monte_carlo_visibility()
        update_monte_carlo_dependent_visibility()

        # -------------------------------------------------
        # RIGHT PANEL BOTTOM: CSV spanning both right columns
        # Mess with minsize to move the CSV block up or down.
        # -------------------------------------------------

        csv_spacer = ttk.Frame(right_right_col)
        csv_spacer.grid(row=1, column=0, sticky="nw")
        csv_spacer.configure(height=120)

        csv_section = ttk.Frame(right_right_col)
        csv_section.grid(
            row=2,
            column=0,
            sticky="nw",
            pady=(8, 2)
        )

        '''
        ttk.Label(
            csv_section,
            text="CSV Output",
            font=("Arial", 12, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        output_csv_var = tk.BooleanVar(
            value=(self.controls.get("output_csv", "None") != "None")
        )

        output_csv_cb = ttk.Checkbutton(
            csv_section,
            text="Write CSV Output",
            variable=output_csv_var
        )
        output_csv_cb.grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        Tooltip(
            output_csv_cb,
            "Enable CSV output for simulation data. Default directory is WARPSimLab on your desktop.",
            font=("Arial", 11)
        )

        csv_dir_var = tk.StringVar(value=self.controls["csv_output_dir"])

        csv_dir_frame = ttk.Frame(csv_section)
        csv_dir_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=2)

        csv_dir_entry = ttk.Entry(csv_dir_frame, textvariable=csv_dir_var, width=50)
        csv_dir_entry.pack(side="left", padx=(0, 5))
        Tooltip(
            csv_dir_entry,
            "Directory where CSV output files will be saved.",
            font=("Arial", 11)
        )

        def browse_directory():
            selected = filedialog.askdirectory(
                title="Select CSV Output Directory",
                initialdir=csv_dir_var.get()
            )
            if selected:
                csv_dir_var.set(selected)
                self.controls["csv_output_dir"] = selected
                os.makedirs(selected, exist_ok=True)

        browse_btn = ttk.Button(csv_dir_frame, text="Browse...", command=browse_directory)
        browse_btn.pack(side="left")
        Tooltip(
            browse_btn,
            "Browse to select CSV output directory.",
            font=("Arial", 11)
        )

        csv_dir_var.trace_add(
            "write",
            lambda *_: self.controls.__setitem__("csv_output_dir", csv_dir_var.get())
        )

        def update_csv_dir_visibility(*_):
            if output_csv_var.get():
                csv_dir_frame.grid()
            else:
                csv_dir_frame.grid_remove()

        def on_output_csv_changed(*_):
            self.controls["output_csv"] = "Output" if output_csv_var.get() else "None"

        output_csv_var.trace_add("write", update_csv_dir_visibility)
        output_csv_var.trace_add("write", on_output_csv_changed)

        update_csv_dir_visibility()
        '''