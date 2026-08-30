# gui_navigation.py

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import traceback

from src.warpsimlab.gui.gui_utils import noop, set_tk_button_soft_disabled, create_dropdown_button, create_top_button


MODE_DEBUG = False


class PortfolioSimulatorGUI_NavigationMixin:
    def _sync_tax_status_from_second_person(self):
        if self.simulation_controls["second_person_enabled"]:
            self.simulation_controls["tax_filing_status"] = "Married filing jointly"
        else:
            self.simulation_controls["tax_filing_status"] = "Single"

    def _advanced_only(self) -> bool:
        return self.mode_var.get() == "Advanced"

    def _apply_mode_to_top_buttons(self):
        is_basic = self.mode_var.get() == "Basic"
        legal_enabled = getattr(self, "legal_accepted", False)

        # Before legal acceptance, File remains available only for Exit.
        if hasattr(self, "file_menu"):
            file_state = "normal" if legal_enabled else "disabled"

            self.file_menu.entryconfig(0, state=file_state)
            self.file_menu.entryconfig(1, state=file_state)
            self.file_menu.entryconfig(2, state=file_state)
            self.file_menu.entryconfig(3, state=file_state)

            # Exit must always remain available.
            self.file_menu.entryconfig(4, state="normal")

        # Prevent changing Basic/Advanced mode before legal acceptance.
        if hasattr(self, "mode_button"):
            self.mode_button.configure(state="normal" if legal_enabled else "disabled")

        basic_enabled = legal_enabled
        advanced_enabled = (not is_basic) and legal_enabled

        set_tk_button_soft_disabled(
            self.home_button, basic_enabled, self._show_home_menu, noop_command=noop
        )
        set_tk_button_soft_disabled(
            self.cashflow_button, basic_enabled, self._show_cashflow_menu, noop_command=noop
        )

        if hasattr(self, "balance_sheet_menu") and hasattr(self, "_balance_sheet_real_estate_index"):
            state = "normal" if advanced_enabled else "disabled"
            self.balance_sheet_menu.entryconfig(self._balance_sheet_real_estate_index, state=state)

        if hasattr(self, "balance_sheet_menu") and hasattr(self, "_balance_sheet_derived_statistics_index"):
            state = "normal" if advanced_enabled else "disabled"
            self.balance_sheet_menu.entryconfig(self._balance_sheet_derived_statistics_index, state=state)

        set_tk_button_soft_disabled(
            self.balance_sheet_button, basic_enabled, self._show_balance_sheet_menu, noop_command=noop
        )
        set_tk_button_soft_disabled(
            self.edit_retirement_button, advanced_enabled, self._cmd_edit_retirement_controls, noop_command=noop
        )
        set_tk_button_soft_disabled(
            self.simulation_button, advanced_enabled, self._show_simulation_menu, noop_command=noop
        )
        set_tk_button_soft_disabled(
            self.results_button, basic_enabled, self._show_results_menu, noop_command=noop
        )

        self._apply_mode_to_reports_button()

        if hasattr(self, "cashflow_menu") and hasattr(self, "_cashflow_special_income_index"):
            state = "normal" if advanced_enabled else "disabled"
            self.cashflow_menu.entryconfig(self._cashflow_special_income_index, state=state)

        if hasattr(self, "cashflow_menu") and hasattr(self, "_cashflow_roth_index"):
            state = "normal" if advanced_enabled else "disabled"
            self.cashflow_menu.entryconfig(self._cashflow_roth_index, state=state)

        if hasattr(self, "cashflow_menu") and hasattr(self, "_cashflow_taxes_index"):
            state = "normal" if advanced_enabled else "disabled"
            self.cashflow_menu.entryconfig(self._cashflow_taxes_index, state=state)

        self._apply_mode_to_results_button()

    def _rebuild_results_menu(self):
        if not hasattr(self, "results_menu"):
            return

        self.results_menu.delete(0, "end")
        is_advanced = self.mode_var.get() == "Advanced"

        # Always available
        self.results_menu.add_command(
            label="Income Plots", command=lambda: self.run_simulation_from_gui(sim_type="income_sim")
        )

        if is_advanced:
            self.results_menu.add_command(
                label="Cash Flow Plots", command=lambda: self.run_simulation_from_gui(sim_type="cashflow_sim")
            )

        self.results_menu.add_command(
            label="Portfolio Plots", command=lambda: self.run_simulation_from_gui(sim_type="portfolio_sim")
        )
        self.results_menu.add_command(
            label="Simulation Summary", command=lambda: self.run_simulation_from_gui(sim_type="summary_sim")
        )

        if is_advanced:
            self.results_menu.add_separator()

            if hasattr(self, "scenario_controller"):
                self.results_menu.add_command(
                    label="Scenario Explorer", command=self.scenario_controller.start_or_focus
                )

            self.results_menu.add_command(
                label="Cumulative Operating Balance",
                command=lambda: self.run_simulation_from_gui(sim_type="operating_balance_sim"),
            )

    def _apply_mode_to_results_button(self):
        if not hasattr(self, "results_button"):
            return

        legal_enabled = getattr(self, "legal_accepted", False)
        set_tk_button_soft_disabled(
            self.results_button, legal_enabled, self._show_results_menu, noop_command=noop
        )

        self._rebuild_results_menu()

    def _load_user_mode(self):
        """
        Load the user's last selected Basic/Advanced mode.

        Defaults to Basic when no saved preference exists or if the
        preference cannot be read.
        """
        try:
            mode_file = Path.home() / "Desktop" / "WARPSimLab" / "Administration" / "user_mode.txt"

            if MODE_DEBUG:
                print("MODE LOAD FILE:", mode_file)

            if not mode_file.exists():
                if MODE_DEBUG:
                    print("MODE LOAD: file does not exist - using Basic")
                return "Basic"

            mode = mode_file.read_text(encoding="utf-8").strip()

            if MODE_DEBUG:
                print("MODE LOAD VALUE:", repr(mode))

            if mode in ("Basic", "Advanced"):
                return mode

            if MODE_DEBUG:
                print("MODE LOAD: invalid value - using Basic")

        except Exception as e:
            if MODE_DEBUG:
                print("MODE LOAD ERROR:", repr(e))

        return "Basic"

    def _save_user_mode(self):
        """
        Save the user's current Basic/Advanced mode.

        Fail silently if the preference cannot be written.
        """
        try:
            target_dir = Path.home() / "Desktop" / "WARPSimLab" / "Administration"
            target_dir.mkdir(parents=True, exist_ok=True)

            mode_file = target_dir / "user_mode.txt"

            mode = self.mode_var.get()
            if mode not in ("Basic", "Advanced"):
                return

            if MODE_DEBUG:
                print("MODE SAVE:", repr(mode), "->", mode_file)

            mode_file.write_text(mode, encoding="utf-8")

        except Exception:
            # A preference-file failure must never prevent WARPSimLab
            # from operating normally.
            pass

    def _on_mode_changed(self):
        if MODE_DEBUG:
            print("MODE MENU CALLBACK:", self.mode_var.get())

        self._save_user_mode()

        container = getattr(self, "edit_frame_container", None)
        if container is not None:
            for widget in container.winfo_children():
                widget.destroy()

        self._apply_mode_to_top_buttons()

        tutorial_controller = getattr(self, "guided_tutorial_controller", None)

        if tutorial_controller is not None and tutorial_controller.active:
            tutorial_controller.refresh_current_step()
            return

        self.edit_main_home()

    def _on_second_person_changed(self):
        # one-way sync
        self._sync_tax_status_from_second_person()

        tutorial_controller = getattr(self, "guided_tutorial_controller", None)

        if tutorial_controller is not None and tutorial_controller.active:
            tutorial_controller.refresh_current_step()
            return

        # rebuild the person editor (existing behavior)
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        self.edit_person_data()

    def _debug_mode_change(self, *args):
        if not MODE_DEBUG:
            return

        print("")
        print("MODE CHANGED:", self.mode_var.get())
        traceback.print_stack(limit=12)
        print("")

    def _build_top_fields(self, parent):
        # --- BUTTON FRAME ---
        self.button_frame = ttk.Frame(parent)
        self.button_frame.grid(row=0, column=0, columnspan=3, sticky="w", pady=5)

        self.mode_var = tk.StringVar(value=self._load_user_mode())

        if MODE_DEBUG:
            self.mode_var.trace_add("write", self._debug_mode_change)

        # Store all buttons as instance variables
        self.file_button, self.file_menu, self._show_file_menu = create_dropdown_button(
            self.button_frame,
            text="File \u25BE",
            menu_labels_and_commands=[
                ("Load Examples", self.load_examples_from_json),
                ("Load Financial Data", self.load_values_from_json),
                ("Save Financial Data", self.save_values_to_json),
                ("Settings", self.edit_display_settings),
                ("Exit", self._close_application),
            ],
            row=0,
            column=0,
            padx=(0, 10),
            pady=2,
        )

        self.home_button, self.home_menu, self._show_home_menu = create_dropdown_button(
            self.button_frame,
            text="Home \u25BE",
            menu_labels_and_commands=[
                ("Start", self.edit_main_home),
                ("Tutorials", self.edit_tutorial),
                ("Notes", self.edit_notes),
            ],
            row=0,
            column=1,
            padx=(0, 15),
            pady=2,
        )

        self.cashflow_button, self.cashflow_menu, self._show_cashflow_menu = create_dropdown_button(
            self.button_frame, text="Cash Flow \u25BE", menu_labels_and_commands=[],
            row=0, column=2, padx=(25, 10), pady=2
        )

        self.cashflow_menu.add_command(label="Normal Income", command=self.edit_person_data)
        self.cashflow_menu.add_command(label="Special Income", command=self.edit_special_income)
        self._cashflow_special_income_index = self.cashflow_menu.index("end")

        self.cashflow_menu.add_command(label="Roth Contributions / Conversions", command=self.edit_roth)
        self._cashflow_roth_index = self.cashflow_menu.index("end")

        self.cashflow_menu.add_command(label="Expenses", command=self.edit_expenses)
        self.cashflow_menu.add_command(label="Taxes", command=self.edit_taxes)
        self._cashflow_taxes_index = self.cashflow_menu.index("end")

        self.balance_sheet_button, self.balance_sheet_menu, self._show_balance_sheet_menu = create_dropdown_button(
            self.button_frame, text="Balance Sheet \u25BE", menu_labels_and_commands=[],
            row=0, column=3, padx=(0, 15), pady=2
        )

        self.balance_sheet_menu.add_command(label="Portfolio", command=self.edit_portfolio_data)
        self.balance_sheet_menu.add_command(label="Real Estate", command=self.edit_real_estate)
        self._balance_sheet_real_estate_index = self.balance_sheet_menu.index("end")

        self.balance_sheet_menu.add_command(label="Derived Statistics", command=self.edit_derived_statistics)
        self._balance_sheet_derived_statistics_index = self.balance_sheet_menu.index("end")

        self.edit_retirement_button = create_top_button(
            self.button_frame,
            text="Retirement",
            command=self.edit_retirement_controls,
            grid_kwargs={"row": 0, "column": 4, "padx": (25, 10), "pady": 2},
        )
        self._cmd_edit_retirement_controls = self.edit_retirement_controls

        self.simulation_button, self.simulation_menu, self._show_simulation_menu = create_dropdown_button(
            self.button_frame,
            text="Simulation \u25BE",
            menu_labels_and_commands=[
                ("Assumptions", self.edit_simulation_assumptions),
                ("Settings", self.edit_simulation_settings),
                ("Controls", self.edit_simulation_controls),
            ],
            row=0,
            column=5,
            padx=(0, 15),
            pady=2,
        )

        self.results_button, self.results_menu, self._show_results_menu = create_dropdown_button(
            self.button_frame, text="Results \u25BE", menu_labels_and_commands=[],
            row=0, column=6, padx=(25, 15), pady=2
        )

        self.reports_button, self.reports_menu, self._show_reports_menu = create_dropdown_button(
            self.button_frame, text="Reports \u25BE", menu_labels_and_commands=[],
            row=0, column=7, padx=(0, 15), pady=2
        )

        # --- MODE BUTTON WITH DROPDOWN (reliable tk.Menubutton wiring) ---
        self.button_frame.grid_columnconfigure(8, weight=1)

        # Create the menubutton (button look)
        self.mode_button = tk.Menubutton(
            self.button_frame,
            text="Mode \u25BE",  # small down triangle
            relief="raised",
            borderwidth=2,
            font=("Arial", 14),
            indicatoron=True,
            direction="below",
        )
        self.mode_button.grid(row=0, column=8, padx=(30, 10), pady=2, sticky="e")

        # Create the menu and attach it explicitly
        self.mode_menu = tk.Menu(self.mode_button, tearoff=0)

        self.mode_menu.add_radiobutton(
            label="Basic", variable=self.mode_var, value="Basic", command=self._on_mode_changed
        )
        self.mode_menu.add_radiobutton(
            label="Advanced", variable=self.mode_var, value="Advanced", command=self._on_mode_changed
        )

        self.mode_button["menu"] = self.mode_menu

        # --- EDIT FRAME CONTAINER ---
        self.edit_frame_container = ttk.Frame(parent)
        self.edit_frame_container.grid(row=1, column=0, columnspan=4, sticky="nsew", pady=(5, 0))

        self._rebuild_results_menu()
        self._apply_mode_to_top_buttons()

    def _build_fields(self):
        top_frame = ttk.Frame(self.frame)
        top_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        self.top_frame = top_frame  # save as an instance variable

        # Make columns resize properly
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.columnconfigure(2, weight=1)
        self.frame.columnconfigure(3, weight=1)

        self._build_top_fields(top_frame)

    def _build_run_button(self):
        style = ttk.Style()
        style.configure("Big.TButton", font=("Arial", 14, "bold"), padding=(10, 10))
        style.configure("BigFaded.TButton", font=("Arial", 14, "bold"), padding=(10, 10))
        style.map("BigFaded.TButton", foreground=[("disabled", "gray60"), ("!disabled", "black")])