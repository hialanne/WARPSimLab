# gui_editors.py

from src.warpsimlab.gui.gui_normalIncome import *
from src.warpsimlab.gui.gui_specialIncome import SpecialIncomeEditFrame
from src.warpsimlab.gui.gui_portfolio import *
from src.warpsimlab.gui.gui_historicalData import *
from src.warpsimlab.gui.gui_portfolioSimulation import *
from src.warpsimlab.gui.gui_simulationControls import *
from src.warpsimlab.gui.gui_retirement import *
from src.warpsimlab.gui.gui_main import MainHomeFrame
from src.warpsimlab.gui.gui_tutorial import TutorialFrame
from src.warpsimlab.gui.gui_expenses import ExpensesEditFrame
from src.warpsimlab.gui.gui_taxes import TaxesEditFrame
from src.warpsimlab.gui.gui_roth import RothEditFrame
from src.warpsimlab.gui.gui_realEstate import RealEstateEditFrame
from src.warpsimlab.gui.gui_derivedStatistics import DerivedStatisticsFrame
from src.warpsimlab.gui.gui_tutorial_definitions import (
    build_basic_tutorial_steps,
    build_advanced_building_tutorial_steps,
    build_advanced_analysis_tutorial_steps,
)
from .gui_notes import NotesFrame


class PortfolioSimulatorGUI_EditorsMixin:
    def edit_main_home(self):
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        home_frame = MainHomeFrame(self.edit_frame_container, title="Home", parent_gui=self)
        home_frame.pack(padx=10, pady=5, fill="x")
        self.home_frame = home_frame


    def edit_blank(self):
        """
        Clear the main editor area without displaying another frame.
        """
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()


    def edit_tutorial_blank(self):
        """
        Clear the main editor area for a tutorial instruction-only step.
        """
        self.edit_blank()


    def start_basic_tutorial(self):
        """
        Start the Basic Tutorial.
        """
        self.guided_tutorial_controller.start(
            tutorial_title="Basic Tutorial", steps=build_basic_tutorial_steps(self)
        )


    def start_advanced_building_tutorial(self):
        """
        Start Advanced Tutorial 1: Building the Simulation.
        """
        self.guided_tutorial_controller.start(
            tutorial_title="Advanced Tutorial 1: Building the Simulation",
            steps=build_advanced_building_tutorial_steps(self),
        )


    def start_advanced_analysis_tutorial(self):
        """
        Start Advanced Tutorial 2: Analyzing Results.
        """
        self.guided_tutorial_controller.start(
            tutorial_title="Advanced Tutorial 2: Analyzing Results",
            steps=build_advanced_analysis_tutorial_steps(self),
        )


    def edit_tutorial(self):
        # Clear any existing editor frame
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        tutorial_frame = TutorialFrame(
            self.edit_frame_container,
            start_basic_tutorial_callback=self.start_basic_tutorial,
            start_advanced_building_tutorial_callback=self.start_advanced_building_tutorial,
            start_advanced_analysis_tutorial_callback=self.start_advanced_analysis_tutorial,
            title="Tutorials",
        )

        tutorial_frame.pack(padx=10, pady=5, fill="x")


    def edit_notes(self):
        # Clear any existing editor frame
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        notes_frame = NotesFrame(self.edit_frame_container, title="Notes")
        notes_frame.pack(padx=10, pady=5, fill="x")


    def edit_person_data(self):
        # Remove previous edit frames
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        persons = {"husband": self.husband}

        if self.simulation_controls["second_person_enabled"]:
            persons["wife"] = self.wife

        person_frame = NormalIncomeEditFrame(
            self.edit_frame_container,
            persons,
            simulation_controls=self.simulation_controls,
            refresh_callback=self._on_second_person_changed,
            title="Personal Data",
            mode=self.mode_var.get(),
        )

        person_frame.pack(padx=10, pady=5, fill="x")


    def edit_special_income(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        special_income_frame = SpecialIncomeEditFrame(
            self.edit_frame_container,
            special_income_streams=self.special_income_streams,
            second_person_enabled=self.simulation_controls.get("second_person_enabled", False),
            title="Special Income",
        )

        special_income_frame.pack(padx=10, pady=5, fill="x")


    def edit_roth(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        roth_frame = RothEditFrame(
            self.edit_frame_container,
            roth_flows=self.roth_flows,
            second_person_enabled=self.simulation_controls.get("second_person_enabled", False),
            title="Roth Contributions / Conversions",
        )

        roth_frame.pack(padx=10, pady=5, fill="x")


    def edit_expenses(self):
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        expenses_frame = ExpensesEditFrame(self.edit_frame_container, expensesDict=self.expensesDict, title="Expenses")
        expenses_frame.pack(padx=10, pady=5, fill="x")


    def edit_taxes(self):
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        control_vars = {"_controls_dict": self.simulation_controls}

        taxes_frame = TaxesEditFrame(self.edit_frame_container, control_vars=control_vars, title="Taxes")
        taxes_frame.pack(padx=10, pady=5, fill="x")


    def edit_portfolio_data(self):
        # Remove previous edit frames
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        husband_portfolio = self.husband_portfolio
        wife_portfolio = self.wife_portfolio if self.simulation_controls["second_person_enabled"] else None

        portfolio_frame = PortfolioEditFrame(
            self.edit_frame_container,
            husband_portfolio=husband_portfolio,
            wife_portfolio=wife_portfolio,
            title="Portfolio Data",
            mode=self.mode_var.get(),
        )
        portfolio_frame.pack(padx=10, pady=5, fill="x")


    def edit_real_estate(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        husband_portfolio = self.husband_portfolio
        wife_portfolio = self.wife_portfolio if self.simulation_controls["second_person_enabled"] else None

        real_estate_frame = RealEstateEditFrame(
            self.edit_frame_container,
            husband_portfolio=husband_portfolio,
            wife_portfolio=wife_portfolio,
            title="Real Estate",
            mode=self.mode_var.get(),
        )

        real_estate_frame.pack(padx=10, pady=5, fill="x")


    def edit_derived_statistics(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        husband_portfolio = self.husband_portfolio
        wife_portfolio = self.wife_portfolio if self.simulation_controls["second_person_enabled"] else None

        derived_statistics_frame = DerivedStatisticsFrame(
            self.edit_frame_container,
            husband_portfolio=husband_portfolio,
            wife_portfolio=wife_portfolio,
            title="Derived Statistics",
            mode=self.mode_var.get(),
        )

        derived_statistics_frame.pack(padx=10, pady=5, fill="x")

    # ------------------------
    # Build Retirement editor in edit_frame_container
    # ------------------------
    def edit_retirement_controls(self):
        if not self._advanced_only():
            return

        # existing code...        # Remove previous editor frame
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        control_vars = {"_controls_dict": self.simulation_controls}

        persons = {"husband": self.husband}
        if self.simulation_controls["second_person_enabled"]:
            persons["wife"] = self.wife

        portfolio = {"husband": self.husband_portfolio}
        if self.simulation_controls["second_person_enabled"]:
            portfolio["wife"] = self.wife_portfolio

        self.retirement_editor_frame = RetirementEditFrame(
            self.edit_frame_container,
            main_gui=self,
            control_vars=control_vars,
            persons=persons,
            portfolio=portfolio,
            title="Retirement",
        )
        self.retirement_editor_frame.pack(anchor="w", pady=(20, 10))


    def edit_simulation_assumptions(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        historical_frame = HistoricalEditFrame(
            self.edit_frame_container, historical_data=self, title="Assumptions"
        )
        historical_frame.pack(padx=10, pady=5, fill="x")


    def edit_simulation_settings(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        sim_vars = {"_settings_dict": self.simulation_settings}

        simulation_frame = PortfolioSimulationEditFrame(
            self.edit_frame_container, sim_vars=sim_vars, title="Settings"
        )
        simulation_frame.pack(padx=10, pady=5, fill="x")


    def edit_simulation_controls(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        control_vars = {"_controls_dict": self.simulation_controls}

        self.simulation_controls_editor_frame = SimulationControlsEditFrame(
            self.edit_frame_container, control_vars=control_vars, title="Controls"
        )
        self.simulation_controls_editor_frame.pack(padx=10, pady=5, fill="x")