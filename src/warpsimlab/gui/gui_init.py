# gui_init.py

#
# Version string is defined after imports.
#

import tkinter.font as tkfont

import tkinter as tk
from tkinter import ttk
from datetime import datetime
import os
import sys
from pathlib import Path
import traceback

from src.warpsimlab.utils.constants import *
from src.warpsimlab.gui.gui_run import PortfolioSimulatorGUI_RunMixin
from src.warpsimlab.gui.gui_normalIncome import *
from src.warpsimlab.gui.gui_specialIncome import SpecialIncomeEditFrame
from src.warpsimlab.utils.io_utils import *
from src.warpsimlab.gui.gui_portfolio import *
from src.warpsimlab.dataClasses.portfolio import Portfolio 
from src.warpsimlab.gui.gui_historicalData import *
from src.warpsimlab.gui.gui_portfolioSimulation import *
from src.warpsimlab.gui.gui_simulationControls import *
from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.gui.gui_retirement import *
from src.warpsimlab.gui.gui_main import MainHomeFrame
from src.warpsimlab.gui.gui_tutorial import TutorialFrame
from src.warpsimlab.gui.gui_scenarioSnapshots import *
from src.warpsimlab.gui.gui_io import *
from src.warpsimlab.gui.gui_io import PortfolioSimulatorGUI_IOMixin
from src.warpsimlab.gui.gui_scenarioController import ScenarioController
from src.warpsimlab.gui.gui_utils import (noop,set_tk_button_soft_disabled,create_dropdown_button, create_top_button)
from .gui_notes import NotesFrame
from src.warpsimlab.gui.gui_expenses import ExpensesEditFrame
from src.warpsimlab.gui.gui_taxes import TaxesEditFrame
from src.warpsimlab.gui.gui_roth import RothEditFrame
from src.warpsimlab.gui.gui_reportExecutiveSummary import ExecutiveSummaryReportFrame
from src.warpsimlab.gui.gui_reportYearByYearDetails import YearByYearDetailsReportFrame
from src.warpsimlab.gui.gui_reportHistoricalWindowRisk import HistoricalWindowRiskReportFrame
from src.warpsimlab.gui.gui_reportMonteCarloRisk import MonteCarloRiskReportFrame
from src.warpsimlab.gui.gui_realEstate import RealEstateEditFrame
from src.warpsimlab.gui.gui_derivedStatistics import DerivedStatisticsFrame
from src.warpsimlab.gui.gui_reportTaxes import TaxReportFrame
from src.warpsimlab.gui.gui_guidedtutorial import GuidedTutorialController
from src.warpsimlab.gui.gui_tutorial_definitions import (
    build_basic_tutorial_steps,
    build_advanced_building_tutorial_steps,
    build_advanced_analysis_tutorial_steps,
)

from src.warpsimlab.gui.gui_settings import (
    DisplaySettingsDialog,
    MAIN_WINDOW_AUTOMATIC,
    MAIN_WINDOW_CUSTOM,
    MAIN_WINDOW_MAXIMIZED,
    SCENARIO_LAYOUT_AUTOMATIC,
    SCENARIO_LAYOUT_REMEMBER,
    geometry_is_visible,
    load_display_settings,
    save_display_settings,
)
from src.warpsimlab.gui.gui_reportSpendingComparison import SpendingComparisonReportFrame
from src.warpsimlab.gui.gui_reportAssetAllocationComparison import (AssetAllocationComparisonReportFrame,)
from src.warpsimlab.gui.gui_reportRetirementSSComparison import (RetirementSSComparisonReportFrame,)


WARPSIMLAB_VERSION = "4.2.2"
WARPSIMLAB_TITLE = f"WARPSimLab version {WARPSIMLAB_VERSION}"

MODE_DEBUG  = False
SCREEN_DEBUG  = False

class PortfolioSimulatorGUI(PortfolioSimulatorGUI_RunMixin, PortfolioSimulatorGUI_IOMixin):
    def __init__(self, root):
        self.root = root

        self.legal_accepted = False

        root.title(WARPSIMLAB_TITLE)

        # Diagnostic code to replicate a Mac's dark mode.
        # self._apply_dark_mode_diagnostic_theme()

        self.display_settings = load_display_settings()
        self._apply_main_window_startup_settings()

        # Diagnostic prints for dialog and subdialog diagnostics.  Comment out in production.
        if SCREEN_DEBUG:
            self._print_display_diagnostics()

        ttk.Label(root, text=WARPSIMLAB_TITLE, font=("Arial", 16), ).pack(pady=10)

        self.frame = ttk.Frame(root)
        self.frame.pack(pady=5, padx=10, fill="both", expand=True)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)

        self.husband = Person(
            age=DEFAULT_HUSBAND_AGE,
            retire_age=DEFAULT_HUSBAND_RETIRE,
            income=DEFAULT_HUSBAND_INCOME,
            ss=DEFAULT_HUSBAND_SOC,
            ss_age=DEFAULT_HUSBAND_SOC_AGE,
            pension=DEFAULT_HUSBAND_PENSION,
            pension_age=DEFAULT_HUSBAND_PENSION_AGE,
            annuity=DEFAULT_HUSBAND_ANNUITY,
            annuity_age=DEFAULT_HUSBAND_ANNUITY_AGE,
            annual_401k_contribution=DEFAULT_HUSBAND_401K_CONTRIB,
            annual_employer_match=DEFAULT_HUSBAND_401K_MATCH,
            pension_inflation_adjustment_pct=DEFAULT_HUSBAND_PENSION_INFLATION_ADJ,
        )

        self.wife = Person(
            age=DEFAULT_WIFE_AGE,
            retire_age=DEFAULT_WIFE_RETIRE,
            income=DEFAULT_WIFE_INCOME,
            ss=DEFAULT_WIFE_SOC,
            ss_age=DEFAULT_WIFE_SOC_AGE,
            pension=DEFAULT_WIFE_PENSION,
            pension_age=DEFAULT_WIFE_PENSION_AGE,
            annuity=DEFAULT_WIFE_ANNUITY,
            annuity_age=DEFAULT_WIFE_ANNUITY_AGE,
            annual_401k_contribution=DEFAULT_WIFE_401K_CONTRIB,
            annual_employer_match=DEFAULT_WIFE_401K_MATCH,
            pension_inflation_adjustment_pct=DEFAULT_WIFE_PENSION_INFLATION_ADJ,
        )

        self.husband_portfolio = Portfolio(
            equity_pre=DEFAULT_EQUITY_PRE_H,
            equity_post=DEFAULT_EQUITY_POST_H,
            equity_roth=DEFAULT_EQUITY_ROTH_H,
            bond_pre=DEFAULT_BOND_PRE_H,
            bond_post=DEFAULT_BOND_POST_H,
            bond_roth=DEFAULT_BOND_ROTH_H,
            cash_pre=DEFAULT_CASH_PRE_H,
            cash_post=DEFAULT_CASH_POST_H,
            cash_roth=DEFAULT_CASH_ROTH_H,
            hsa_cash=DEFAULT_HSA_CASH_H,
            hsa_equity=DEFAULT_HSA_EQUITY_H,
            hsa_bond=DEFAULT_HSA_BOND_H,
            real_estate=DEFAULT_REAL_ESTATE_H
        )

        self.wife_portfolio = Portfolio(
            equity_pre=DEFAULT_EQUITY_PRE_W,
            equity_post=DEFAULT_EQUITY_POST_W,
            equity_roth=DEFAULT_EQUITY_ROTH_W,
            bond_pre=DEFAULT_BOND_PRE_W,
            bond_post=DEFAULT_BOND_POST_W,
            bond_roth=DEFAULT_BOND_ROTH_W,
            cash_pre=DEFAULT_CASH_PRE_W,
            cash_post=DEFAULT_CASH_POST_W,
            cash_roth=DEFAULT_CASH_ROTH_W,
            hsa_cash=DEFAULT_HSA_CASH_W,
            hsa_equity=DEFAULT_HSA_EQUITY_W,
            hsa_bond=DEFAULT_HSA_BOND_W,
            real_estate=DEFAULT_REAL_ESTATE_W
        )

        self._init_vars()

        self._build_fields()

        # Guided tutorial controller
        self.guided_tutorial_controller = GuidedTutorialController(self)

        self.scenario_controller = ScenarioController(self)

        # Rebuild now that the Scenario Explorer controller exists.
        self._rebuild_results_menu()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self._close_application,
        )

        self._build_run_button()

        self.edit_main_home()

        # This should be commented out in production.
        # self._print_content_geometry_diagnostics()


    def _apply_dark_mode_diagnostic_theme(self):
        """
        TEMPORARY: Force TTK into a dark palette for GUI diagnostics.
        Remove or disable before production release.
        """
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(
            ".",
            background="#2b2b2b",
            foreground="#f0f0f0",
            fieldbackground="#3a3a3a",
        )

        style.configure(
            "TFrame",
            background="#2b2b2b",
        )

        style.configure(
            "TLabel",
            background="#2b2b2b",
            foreground="#f0f0f0",
        )

        style.configure(
            "TLabelframe",
            background="#2b2b2b",
            foreground="#f0f0f0",
        )

        style.configure(
            "TLabelframe.Label",
            background="#2b2b2b",
            foreground="#f0f0f0",
        )

        style.configure(
            "TCheckbutton",
            background="#2b2b2b",
            foreground="#f0f0f0",
        )

        style.configure(
            "TRadiobutton",
            background="#2b2b2b",
            foreground="#f0f0f0",
        )

        style.configure(
            "TEntry",
            fieldbackground="#3a3a3a",
            foreground="#f0f0f0",
        )

        style.configure(
            "TCombobox",
            fieldbackground="#3a3a3a",
            foreground="#f0f0f0",
        )

        style.map(
            "TCheckbutton",
            background=[
                ("active", "#2b2b2b"),
            ],
            foreground=[
                ("active", "#f0f0f0"),
            ],
        )

        style.map(
            "TRadiobutton",
            background=[
                ("active", "#2b2b2b"),
            ],
            foreground=[
                ("active", "#f0f0f0"),
            ],
        )

        style.map(
            "TLabel",
            background=[
                ("disabled", "#2b2b2b"),
            ],
            foreground=[
                ("disabled", "#9a9a9a"),
            ],
        )

        style.map(
            "TEntry",
            fieldbackground=[
                ("disabled", "#333333"),
            ],
            foreground=[
                ("disabled", "#9a9a9a"),
            ],
        )

        style.map(
            "TMenubutton",
            background=[
                ("disabled", "#333333"),
            ],
            foreground=[
                ("disabled", "#9a9a9a"),
            ],
        )
        style.configure(
            "TButton",
            background="#3a3a3a",
            foreground="#f0f0f0",
        )
        style.map(
            "TButton",
            background=[
                ("disabled", "#333333"),
                ("active", "#4a4a4a"),
            ],
            foreground=[
                ("disabled", "#9a9a9a"),
                ("active", "#f0f0f0"),
            ],
        )

        self.root.option_add("*Button.background", "#3a3a3a")
        self.root.option_add("*Button.foreground", "#f0f0f0")
        self.root.option_add("*Button.activeBackground", "#4a4a4a")
        self.root.option_add("*Button.activeForeground", "#f0f0f0")

        self.root.option_add("*Menubutton.background", "#3a3a3a")
        self.root.option_add("*Menubutton.foreground", "#f0f0f0")
        self.root.option_add("*Menubutton.activeBackground", "#4a4a4a")
        self.root.option_add("*Menubutton.activeForeground", "#f0f0f0")

        self.root.option_add("*Menu.background", "#3a3a3a")
        self.root.option_add("*Menu.foreground", "#f0f0f0")
        self.root.option_add("*Menu.activeBackground", "#4a4a4a")
        self.root.option_add("*Menu.activeForeground", "#f0f0f0")

        self.root.option_add("*Menu.selectColor", "#f0f0f0")



    def _get_monitor_work_area(self, x, y):
        """
        Return the usable monitor rectangle containing the supplied point.

        Returns:
            (left, top, right, bottom)

        On Windows, this uses the native monitor work area so taskbars are
        excluded and secondary-monitor coordinates are handled correctly.

        Other platforms currently fall back to Tk's reported screen.
        """
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            MONITOR_DEFAULTTONEAREST = 2

            point = wintypes.POINT(x, y)

            monitor = user32.MonitorFromPoint(
                point,
                MONITOR_DEFAULTTONEAREST,
            )

            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD),
                ]

            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)

            user32.GetMonitorInfoW(
                monitor,
                ctypes.byref(info),
            )

            return (
                info.rcWork.left,
                info.rcWork.top,
                info.rcWork.right,
                info.rcWork.bottom,
            )

        return (
            0,
            0,
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
        )


    def _center_main_window(self, width, height):
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            cursor = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(
                ctypes.byref(cursor)
            )

            work_left, work_top, work_right, work_bottom = (
                self._get_monitor_work_area(
                    cursor.x,
                    cursor.y,
                )
            )
        else:
            work_left, work_top, work_right, work_bottom = (
                self._get_monitor_work_area(0, 0)
            )

        work_width = work_right - work_left
        work_height = work_bottom - work_top

        x = work_left + (work_width - width) // 2
        y = work_top + (work_height - height) // 2

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )


    def _print_display_diagnostics(self):
        """
        Print Tk display and geometry information for debugging.
        """
        self.root.update_idletasks()

        print("")
        print("WARPSimLab display diagnostics")
        print("------------------------------")
        print(f"platform: {sys.platform}")
        print(f"screen width: {self.root.winfo_screenwidth()}")
        print(f"screen height: {self.root.winfo_screenheight()}")
        print(f"screen width mm: {self.root.winfo_screenmmwidth()}")
        print(f"screen height mm: {self.root.winfo_screenmmheight()}")
        print(f"pixels per inch: {self.root.winfo_fpixels('1i')}")
        print(f"tk scaling: {self.root.tk.call('tk', 'scaling')}")
        print(f"root width: {self.root.winfo_width()}")
        print(f"root height: {self.root.winfo_height()}")
        print(f"root x: {self.root.winfo_x()}")
        print(f"root y: {self.root.winfo_y()}")
        print(f"root geometry: {self.root.winfo_geometry()}")

        font_14 = tkfont.Font(
            root=self.root,
            family="Arial",
            size=14,
        )

        font_16 = tkfont.Font(
            root=self.root,
            family="Arial",
            size=16,
        )

        print("")
        print("Font diagnostics")
        print("----------------")
        print(f"Arial 14 linespace: {font_14.metrics('linespace')}")
        print(f"Arial 14 ascent: {font_14.metrics('ascent')}")
        print(f"Arial 14 descent: {font_14.metrics('descent')}")
        print(f"Arial 14 width of 'WARPSimLab': {font_14.measure('WARPSimLab')}")
        print(f"Arial 16 linespace: {font_16.metrics('linespace')}")
        print(f"Arial 16 ascent: {font_16.metrics('ascent')}")
        print(f"Arial 16 descent: {font_16.metrics('descent')}")
        print(f"Arial 16 width of 'WARPSimLab': {font_16.measure('WARPSimLab')}")
        print("")
        print("Additional Tk diagnostics")
        print("-------------------------")

        print(f"Arial 14 actual: {font_14.actual()}")
        print(f"Arial 16 actual: {font_16.actual()}")

        default_font = tkfont.nametofont("TkDefaultFont")
        print(f"TkDefaultFont actual: {default_font.actual()}")
        print(
            f"TkDefaultFont linespace: "
            f"{default_font.metrics('linespace')}"
        )

        test_label = ttk.Label(
            self.root,
            text="WARPSimLab",
            font=("Arial", 16),
        )

        test_button = ttk.Button(
            self.root,
            text="Test Button",
        )

        test_label.update_idletasks()
        test_button.update_idletasks()

        print(
            f"Arial 16 label requested size: "
            f"{test_label.winfo_reqwidth()}x"
            f"{test_label.winfo_reqheight()}"
        )
        print(
            f"TTK button requested size: "
            f"{test_button.winfo_reqwidth()}x"
            f"{test_button.winfo_reqheight()}"
        )

        test_label.destroy()
        test_button.destroy()
        print("")
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32

            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD),
                ]

            monitor_data = []

            MONITORENUMPROC = ctypes.WINFUNCTYPE(
                ctypes.c_int,
                wintypes.HMONITOR,
                wintypes.HDC,
                ctypes.POINTER(wintypes.RECT),
                wintypes.LPARAM,
            )

            def monitor_enum_proc(
                monitor,
                hdc,
                rect_pointer,
                data,
            ):
                info = MONITORINFO()
                info.cbSize = ctypes.sizeof(MONITORINFO)

                user32.GetMonitorInfoW(
                    monitor,
                    ctypes.byref(info),
                )

                monitor_data.append(
                    (
                        info.rcMonitor.left,
                        info.rcMonitor.top,
                        info.rcMonitor.right,
                        info.rcMonitor.bottom,
                        info.rcWork.left,
                        info.rcWork.top,
                        info.rcWork.right,
                        info.rcWork.bottom,
                        info.dwFlags,
                    )
                )

                return 1

            callback = MONITORENUMPROC(monitor_enum_proc)

            user32.EnumDisplayMonitors(
                None,
                None,
                callback,
                0,
            )

            cursor = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(cursor))

            print("\nWindows monitor diagnostics")
            print("---------------------------")
            print(f"cursor: {cursor.x}, {cursor.y}")

            for index, monitor in enumerate(monitor_data):
                print(f"monitor {index}: {monitor}")


    def _print_content_geometry_diagnostics(self):
        """
        Print requested and actual GUI geometry after the GUI is built.
        """
        self.root.update_idletasks()

        print("")
        print("WARPSimLab content geometry diagnostics")
        print("---------------------------------------")

        print(
            f"root requested size: "
            f"{self.root.winfo_reqwidth()}x"
            f"{self.root.winfo_reqheight()}"
        )
        print(
            f"root actual size: "
            f"{self.root.winfo_width()}x"
            f"{self.root.winfo_height()}"
        )

        print(
            f"main frame requested size: "
            f"{self.frame.winfo_reqwidth()}x"
            f"{self.frame.winfo_reqheight()}"
        )
        print(
            f"main frame actual size: "
            f"{self.frame.winfo_width()}x"
            f"{self.frame.winfo_height()}"
        )

        print(
            f"top frame requested size: "
            f"{self.top_frame.winfo_reqwidth()}x"
            f"{self.top_frame.winfo_reqheight()}"
        )
        print(
            f"top frame actual size: "
            f"{self.top_frame.winfo_width()}x"
            f"{self.top_frame.winfo_height()}"
        )

        print(
            f"button frame requested size: "
            f"{self.button_frame.winfo_reqwidth()}x"
            f"{self.button_frame.winfo_reqheight()}"
        )
        print(
            f"button frame actual size: "
            f"{self.button_frame.winfo_width()}x"
            f"{self.button_frame.winfo_height()}"
        )

        print(
            f"editor container requested size: "
            f"{self.edit_frame_container.winfo_reqwidth()}x"
            f"{self.edit_frame_container.winfo_reqheight()}"
        )
        print(
            f"editor container actual size: "
            f"{self.edit_frame_container.winfo_width()}x"
            f"{self.edit_frame_container.winfo_height()}"
        )

        if hasattr(self, "home_frame"):
            print(
                f"home frame requested size: "
                f"{self.home_frame.winfo_reqwidth()}x"
                f"{self.home_frame.winfo_reqheight()}"
            )
            print(
                f"home frame actual size: "
                f"{self.home_frame.winfo_width()}x"
                f"{self.home_frame.winfo_height()}"
            )
            if hasattr(self.home_frame, "intro_label"):
                intro_label = self.home_frame.intro_label

                print(
                    f"intro label requested size: "
                    f"{intro_label.winfo_reqwidth()}x"
                    f"{intro_label.winfo_reqheight()}"
                )
                print(
                    f"intro label actual size: "
                    f"{intro_label.winfo_width()}x"
                    f"{intro_label.winfo_height()}"
                )
                print(
                    f"intro label wraplength: "
                    f"{intro_label.cget('wraplength')}"
                )

        print("")


    def _set_main_window_normal(self):
        """
        Leave the maximized state before applying normal geometry.
        """
        try:
            if sys.platform.startswith("win"):
                self.root.state("normal")
            elif sys.platform.startswith("linux"):
                self.root.attributes("-zoomed", False)
            else:
                self.root.state("normal")
        except tk.TclError:
            pass


    def _set_main_window_maximized(self):
        """
        Maximize the main window using the platform-supported operation.
        """
        try:
            if sys.platform.startswith("win"):
                self.root.state("zoomed")
            elif sys.platform.startswith("linux"):
                self.root.attributes("-zoomed", True)
            else:
                self.root.state("zoomed")
        except tk.TclError:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            self.root.geometry(
                f"{screen_width}x{screen_height}+0+0"
            )


    def _main_window_is_maximized(self):
        """
        Return True when the main window is currently maximized.
        """
        try:
            if sys.platform.startswith("linux"):
                return bool(
                    self.root.attributes("-zoomed")
                )

            return self.root.state() == "zoomed"
        except tk.TclError:
            return False


    def _apply_automatic_main_window_size(self):
        """
        Scale the main window from the original Windows development layout.
        """
        development_screen_width = 1707
        development_screen_height = 1067

        development_window_width = 1200
        development_window_height = 750

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        width_scale = screen_width / development_screen_width
        height_scale = screen_height / development_screen_height

        # bad scale = min(width_scale, height_scale)


        # good development_font_linespace = 24

        #reference_font = tkfont.Font(
        #    family="Arial",
        #    size=16,
        #)
        #current_font_linespace = reference_font.metrics("linespace")

        #scale = current_font_linespace / development_font_linespace

        # diagnostic print.  Turn off for production.
        # print(f"automatic main-window scale: {scale}")

        #window_width = int(development_window_width * scale)
        #window_height = int(development_window_height * scale)

        development_screen_width = 1707
        development_screen_height = 1067

        development_window_width = 1200
        development_window_height = 750

        development_font_linespace = 24

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        reference_font = tkfont.Font(
            family="Arial",
            size=16,
        )
        current_font_linespace = reference_font.metrics("linespace")

        gui_scale = (
            current_font_linespace
            / development_font_linespace
        )

        effective_screen_width = screen_width / gui_scale
        effective_screen_height = screen_height / gui_scale

        width_scale = (
            effective_screen_width
            / development_screen_width
        )
        height_scale = (
            effective_screen_height
            / development_screen_height
        )

        desktop_scale = min(width_scale, height_scale)

        if desktop_scale > 1.0:
            #large_display_factor = 1.0 / (desktop_scale ** 0.5)
            large_display_factor = 1.0 / (desktop_scale ** 0.5)
        else:
            large_display_factor = 1.0

        scale = gui_scale * large_display_factor

        window_width = int(development_window_width * scale)
        window_height = int(development_window_height * scale)

        minimum_window_width = 1200
        minimum_window_height = 750

        window_width = max(window_width, minimum_window_width)
        window_height = max(window_height, minimum_window_height)

        # Diagnostic code.  Comment out in production.
        '''
        print(f"automatic GUI scale: {gui_scale}")
        print(f"effective desktop scale: {desktop_scale}")
        print(f"large display factor: {large_display_factor}")
        print(f"automatic main-window scale: {scale}")
        '''

        self._set_main_window_normal()
        self._center_main_window(
            window_width,
            window_height,
        )


    def _apply_main_window_startup_settings(self):
        """
        Apply remembered geometry or the selected sizing policy at startup.
        """
        main_settings = self.display_settings["main_window"]

        if main_settings.get("remember_geometry", False):
            if main_settings.get("last_maximized", False):
                self._set_main_window_maximized()
                return

            saved_geometry = main_settings.get("last_geometry")
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            if geometry_is_visible(
                saved_geometry,
                screen_width,
                screen_height,
            ):
                self._set_main_window_normal()
                self.root.geometry(saved_geometry)
                return

        self._apply_selected_main_window_mode()


    def _apply_selected_main_window_mode(self):
        """
        Apply the selected Automatic, Maximized, or Custom policy.
        """
        main_settings = self.display_settings["main_window"]
        sizing_mode = main_settings.get(
            "sizing_mode",
            MAIN_WINDOW_AUTOMATIC,
        )

        if sizing_mode == MAIN_WINDOW_MAXIMIZED:
            self._set_main_window_maximized()
            return

        if sizing_mode == MAIN_WINDOW_CUSTOM:
            width = main_settings["custom_width"]
            height = main_settings["custom_height"]

            self._set_main_window_normal()
            self._center_main_window(width, height)
            return

        self._apply_automatic_main_window_size()


    def edit_display_settings(self):
        """
        Open the application display settings dialog.
        """
        DisplaySettingsDialog(
            self.root,
            self.display_settings,
            self._apply_display_settings,
        )


    def _apply_display_settings(self, updated_settings):
        """
        Store and immediately apply settings returned by the dialog.
        """
        self.display_settings = updated_settings

        self._apply_selected_main_window_mode()

        scenario_controller = getattr(
            self,
            "scenario_controller",
            None,
        )

        if (
            scenario_controller is not None
            and scenario_controller.session_active
        ):
            scenario_mode = self.display_settings[
                "scenario_explorer"
            ]["layout_mode"]

            if scenario_mode == SCENARIO_LAYOUT_AUTOMATIC:
                scenario_controller._position_windows()
            elif scenario_mode == SCENARIO_LAYOUT_REMEMBER:
                scenario_controller.capture_current_layout()
                save_display_settings(self.display_settings)


    def _save_main_window_geometry(self):
        """
        Save the current main-window layout when remembering is enabled.
        """
        main_settings = self.display_settings["main_window"]

        if not main_settings.get("remember_geometry", False):
            return

        self.root.update_idletasks()

        maximized = self._main_window_is_maximized()
        main_settings["last_maximized"] = maximized

        if not maximized:
            main_settings["last_geometry"] = (
                self.root.winfo_geometry()
            )


    def _close_application(self):
        """
        Save remembered display layouts and close WARPSimLab.
        """
        scenario_controller = getattr(
            self,
            "scenario_controller",
            None,
        )

        if (
            scenario_controller is not None
            and scenario_controller.session_active
        ):
            scenario_controller.capture_current_layout()

        self._save_main_window_geometry()
        save_display_settings(self.display_settings)

        self.root.destroy()

    # ------------------------
    # Initialize Variables
    # ------------------------
    def _init_vars(self):
        # Load market data
        market_values = load_market_data()  # defaults to "25_year_data"

        self.eq_mean = market_values["eq_mean"]
        self.bd_mean = market_values["bd_mean"]
        self.cs_mean = market_values["cs_mean"]
        self.re_mean = market_values["re_mean"]

        self.eq_std = market_values["eq_std"]
        self.bd_std = market_values["bd_std"]
        self.cs_std = market_values["cs_std"]
        self.re_std = market_values["re_std"]

        self.inflation = market_values["inflation"]
        self.historical_market = "25_year_data"

        # Default simulation settings
        self.simulation_settings = {
            "start_year": datetime.now().year,
            "years_to_simulate": DEFAULT_YEARS,
            "num_sims": DEFAULT_SIMULATIONS,
            "fund_expense": DEFAULT_FUND_EXPENSE,
            "use_fund_expenses": True,
            "initial_allocation_mode": "maintain-current-allocation",
            "custom_stock": 0.0,
            "custom_bonds": 0.0,
            "custom_cash": 100.0
        }

        default_csv_dir = os.path.join(os.path.expanduser("~"), "Desktop", "WARPSimLab")

        self.simulation_controls = {
            "enable_second_person": bool(DEFAULT_ENABLE_SECOND_PERSON),
            "include_realestate": False,
            "plot_mode": "real",
            "subplot_mode": "fill",
            "monte_carlo_plot_style": "fill",
            "use_correlated_returns": True,
            #"monte_carlo_mode": "pathBasedAnnualSampling",
            "monte_carlo_mode": "rollingHistoricalWindows",
            "historical_asset_returns_file": "us_asset_returns_1876_2025.csv",
            "historical_inflation_file": "us_inflation_1876_2025_real.csv",
            "historical_window_mode": "rolling_overlapping_all",
            "disable_sequence_risk_for_historical": True,
            "show_simulated_shortfall_rate": True,
            "include_rmd": True,
            "calculate_income_taxes": True,
            "calculate_payroll_taxes": True,
            "tax_filing_status": "Married filing jointly",
            "calculate_state_taxes": True,
            "state_of_residence": DEFAULT_STATE_OF_RESIDENCE,
            "constant_y_plots": False,
            "rebalance_every_year": True,
            "output_csv": "None",
            "csv_output_dir": default_csv_dir,
            "overlay_tax_impacts": False,
            "overlay_fund_expense_impacts": False,
            "overlay_household_expenses": False,
            "overlay_profit_loss": True,
            "overlay_retirement_age": False,
            "retirement_withdraw_mode": "Percentage + Inflation",
            "retirement_withdraw_pct": 4.0,
            "retirement_withdraw_dollars": 0.0,
            "sequence_risk_enabled": False,
            "sequence_risk_timing": "Early downturn",
            "sequence_risk_length": "Medium",
            "sequence_risk_depth": "Moderate",
            "sequence_risk_start_year_offset": 0,
            "always_use_expense_mode": True,
            "annotate_plots": False,
            "user_annotation_strings": []
        }

        self.report_options = {
            "executive_summary": {
                "include_simulation_summary": True,

                "portfolio_visuals": {
                    "include_normal_projection": True,
                    "include_subcategories_projection": False,
                    "include_monte_carlo_analysis": False,
                    "include_historical_windows_analysis": False,
                },

                "income_visuals": {
                    "include_normal_income": True,
                    "include_subcategories_income": False,
                },

                "cashflow_visuals": {
                    "include_normal_cashflow": True,
                    "include_subcategories_cashflow": False,
                },

                "operating_balance_visuals": {
                    "include_cumulative_operating_balance": True,
                },

                "include_assumptions_appendix": True,

                "output_format": "HTML",
                "open_report_in_browser": False,
            },
            "year_by_year_details": {
                "generate_html": True,
                "generate_csv": True,
                "table_detail": "Compact",
                "insert_5_year_breaks": True,
                "open_report_in_browser": False,
            },
            "historical_window_risk": {
                "general": {
                    "include_executive_summary": True,
                    "include_method_explanation": True,
                },
                "analysis": {
                    "include_portfolio_projection": True,
                    "include_portfolio_sustainability": True,
                    "include_historical_window_insights": True,
                    "include_percentile_table": True,
                },
                "output": {
                    "generate_html": True,
                    "generate_csv": False,
                    "open_report_in_browser": False,
                },
            },
            "monte_carlo_risk": {
                "general": {
                    "include_executive_summary": True,
                    "include_method_explanation": True,
                },
                "analysis": {
                    "include_portfolio_projection": True,
                    "include_portfolio_sustainability": True,
                    "include_monte_carlo_insights": True,
                    "include_percentile_table": True,
                },
                "output": {
                    "generate_html": True,
                    "generate_csv": False,
                    "open_report_in_browser": False,
                },
            },
            "tax_report": {
                "output": {
                    "generate_html": True,
                    "generate_csv": False,
                    "open_report_in_browser": False,
                },
                "sections": {
                    "include_roth_analysis": True,
                    "include_hsa_analysis": True,
                    "include_rmd_analysis": True,
                    "include_educational_commentary": True,
                },
            },
            "spending_comparison": {
                "spending_percentages": [
                    70,
                    80,
                    90,
                    100,
                    110,
                    120,
                    130,
                ],
                "output": {
                    "generate_html": True,
                    "open_report_in_browser": False,
                },
            },
            "asset_allocation_comparison": {
                "equity_percentages": [
                    0,
                    20,
                    40,
                    60,
                    80,
                    100,
                ],
                "output": {
                    "generate_html": True,
                    "open_report_in_browser": False,
                },
            },
            "retirement_ss_comparison": {
                "retirement_ages": [
                    62,
                    64,
                    66,
                    68,
                    70,
                ],
                "social_security_ages": [
                    62,
                    64,
                    66,
                    68,
                    70,
                ],
                "output": {
                    "generate_html": True,
                    "open_report_in_browser": False,
                },
            },
        }

        # Dynamic expenses
        self.expensesDict = DynamicExpenses()
        for expense in DEFAULT_EXPENSE_ENTRIES:
            self.expensesDict.add_expense(
                expense["start_year"], expense["cost"], expense["end_year"], expense["comment"]
            )

        # Special income streams
        self.special_income_streams = [dict(stream) for stream in DEFAULT_SPECIAL_INCOME_STREAMS]

        # Scheduled Roth contributions and conversions
        self.roth_flows = [dict(flow) for flow in DEFAULT_ROTH_FLOWS]


    def _sync_tax_status_from_second_person(self):
        if self.simulation_controls["enable_second_person"]:
            self.simulation_controls["tax_filing_status"] = "Married filing jointly"
        else:
            self.simulation_controls["tax_filing_status"] = "Single"

    def _advanced_only(self) -> bool:
        return self.mode_var.get() == "Advanced"


    def _apply_mode_to_top_buttons(self):
        is_basic = (self.mode_var.get() == "Basic")
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
            self.mode_button.configure(
                state="normal" if legal_enabled else "disabled"
            )

        basic_enabled = legal_enabled
        advanced_enabled = (not is_basic) and legal_enabled

        set_tk_button_soft_disabled(
            self.home_button,
            basic_enabled,
            self._show_home_menu,
            noop_command=noop
        )

        set_tk_button_soft_disabled(
            self.cashflow_button,
            basic_enabled,
            self._show_cashflow_menu,
            noop_command=noop
        )

        if hasattr(self, "balance_sheet_menu") and hasattr(self, "_balance_sheet_real_estate_index"):
            state = "normal" if advanced_enabled else "disabled"
            self.balance_sheet_menu.entryconfig(self._balance_sheet_real_estate_index, state=state)

        if hasattr(self, "balance_sheet_menu") and hasattr(self, "_balance_sheet_derived_statistics_index"):
            state = "normal" if advanced_enabled else "disabled"
            self.balance_sheet_menu.entryconfig(self._balance_sheet_derived_statistics_index, state=state)

        set_tk_button_soft_disabled(
            self.balance_sheet_button,
            basic_enabled,
            self._show_balance_sheet_menu,
            noop_command=noop
        )

        set_tk_button_soft_disabled(
            self.edit_retirement_button,
            advanced_enabled,
            self._cmd_edit_retirement_controls,
            noop_command=noop
        )

        set_tk_button_soft_disabled(
            self.simulation_button,
            advanced_enabled,
            self._show_simulation_menu,
            noop_command=noop
        )

        set_tk_button_soft_disabled(
            self.results_button,
            basic_enabled,
            self._show_results_menu,
            noop_command=noop
        )

        self._apply_mode_to_reports_button()

        if (
            hasattr(self, "cashflow_menu")
            and hasattr(self, "_cashflow_special_income_index")
        ):
            state = "normal" if advanced_enabled else "disabled"
            self.cashflow_menu.entryconfig(
                self._cashflow_special_income_index,
                state=state,
            )

        if (
            hasattr(self, "cashflow_menu")
            and hasattr(self, "_cashflow_roth_index")
        ):
            state = "normal" if advanced_enabled else "disabled"
            self.cashflow_menu.entryconfig(
                self._cashflow_roth_index,
                state=state,
            )

        if (
            hasattr(self, "cashflow_menu")
            and hasattr(self, "_cashflow_taxes_index")
        ):
            state = "normal" if advanced_enabled else "disabled"
            self.cashflow_menu.entryconfig(
                self._cashflow_taxes_index,
                state=state,
            )

        self._apply_mode_to_results_button()

    def _rebuild_results_menu(self):
        if not hasattr(self, "results_menu"):
            return

        self.results_menu.delete(0, "end")

        is_advanced = (self.mode_var.get() == "Advanced")

        # Always available
        self.results_menu.add_command(
            label="Income Plots",
            command=lambda: self.run_simulation_from_gui(sim_type="income_sim")
        )

        if is_advanced:
            self.results_menu.add_command(
                label="Cash Flow Plots",
                command=lambda: self.run_simulation_from_gui(sim_type="cashflow_sim")
            )

        self.results_menu.add_command(
            label="Portfolio Plots",
            command=lambda: self.run_simulation_from_gui(sim_type="portfolio_sim")
        )

        self.results_menu.add_command(
            label="Simulation Summary",
            command=lambda: self.run_simulation_from_gui(sim_type="summary_sim")
        )

        if is_advanced:
            self.results_menu.add_separator()

            if hasattr(self, "scenario_controller"):
                self.results_menu.add_command(
                    label="Scenario Explorer",
                    command=self.scenario_controller.start_or_focus
                )

            self.results_menu.add_command(
                label="Cumulative Operating Balance",
                command=lambda: self.run_simulation_from_gui(
                    sim_type="operating_balance_sim"
                )
            )

    def _apply_mode_to_results_button(self):
        if not hasattr(self, "results_button"):
            return

        legal_enabled = getattr(self, "legal_accepted", False)

        set_tk_button_soft_disabled(
            self.results_button,
            legal_enabled,
            self._show_results_menu,
            noop_command=noop
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

            if MODE_DEBUG :
                print("MODE LOAD FILE:", mode_file)

            if not mode_file.exists():
                if MODE_DEBUG :
                    print("MODE LOAD: file does not exist - using Basic")
                return "Basic"

            mode = mode_file.read_text(encoding="utf-8").strip()

            if MODE_DEBUG :
                print("MODE LOAD VALUE:", repr(mode))

            if mode in ("Basic", "Advanced"):
                return mode

            if MODE_DEBUG :
                print("MODE LOAD: invalid value - using Basic")

        except Exception as e:
            if MODE_DEBUG :
                print("MODE LOAD ERROR:", repr(e))

        return "Basic"


    def _save_user_mode(self):
        """
        Save the user's current Basic/Advanced mode.

        Fail silently if the preference cannot be written.
        """
        try:
            target_dir = (
                Path.home()
                / "Desktop"
                / "WARPSimLab"
                / "Administration"
            )
            target_dir.mkdir(parents=True, exist_ok=True)

            mode_file = target_dir / "user_mode.txt"

            mode = self.mode_var.get()
            if mode not in ("Basic", "Advanced"):
                return

            if MODE_DEBUG :
                print("MODE SAVE:", repr(mode), "->", mode_file)

            mode_file.write_text(mode, encoding="utf-8")

        except Exception:
            # A preference-file failure must never prevent WARPSimLab
            # from operating normally.
            pass


    def _on_mode_changed(self):
        if MODE_DEBUG :
            print("MODE MENU CALLBACK:", self.mode_var.get())

        self._save_user_mode()

        container = getattr(self, "edit_frame_container", None)
        if container is not None:
            for widget in container.winfo_children():
                widget.destroy()

        self._apply_mode_to_top_buttons()

        tutorial_controller = getattr(
            self,
            "guided_tutorial_controller",
            None,
        )

        if (
            tutorial_controller is not None
            and tutorial_controller.active
        ):
            tutorial_controller.refresh_current_step()
            return

        self.edit_main_home()


    def _on_second_person_changed(self):
        # one-way sync
        self._sync_tax_status_from_second_person()

        tutorial_controller = getattr(
            self,
            "guided_tutorial_controller",
            None,
        )

        if (
            tutorial_controller is not None
            and tutorial_controller.active
        ):
            tutorial_controller.refresh_current_step()
            return

        # rebuild the person editor (existing behavior)
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        self.edit_person_data()


    def _debug_mode_change(self, *args):
        if not MODE_DEBUG :
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

        if MODE_DEBUG :
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
            padx=(0,10),
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
            padx=(0,15),
            pady=2,
        ) 

        self.cashflow_button, self.cashflow_menu, self._show_cashflow_menu = create_dropdown_button(
            self.button_frame,
            text="Cash Flow \u25BE",
            menu_labels_and_commands=[],  # empty
            row=0,
            column=2,
            padx=(25,10),
            pady=2,
        )

        self.cashflow_menu.add_command(
            label="Normal Income",
            command=self.edit_person_data
        )

        self.cashflow_menu.add_command(
            label="Special Income",
            command=self.edit_special_income
        )
        self._cashflow_special_income_index = self.cashflow_menu.index("end")

        self.cashflow_menu.add_command(
            label="Roth Contributions / Conversions",
            command=self.edit_roth
        )
        self._cashflow_roth_index = self.cashflow_menu.index("end")

        self.cashflow_menu.add_command(
            label="Expenses",
            command=self.edit_expenses
        )

        self.cashflow_menu.add_command(
            label="Taxes",
            command=self.edit_taxes
        )
        self._cashflow_taxes_index = self.cashflow_menu.index("end")

        self.balance_sheet_button, self.balance_sheet_menu, self._show_balance_sheet_menu = create_dropdown_button(
            self.button_frame,
            text="Balance Sheet \u25BE",
            menu_labels_and_commands=[],
            row=0,
            column=3,
            padx=(0,15),
            pady=2,
        )

        self.balance_sheet_menu.add_command(
            label="Portfolio",
            command=self.edit_portfolio_data
        )

        self.balance_sheet_menu.add_command(
            label="Real Estate",
            command=self.edit_real_estate
        )
        self._balance_sheet_real_estate_index = self.balance_sheet_menu.index("end")

        self.balance_sheet_menu.add_command(
            label="Derived Statistics",
            command=self.edit_derived_statistics
        )
        self._balance_sheet_derived_statistics_index = self.balance_sheet_menu.index("end")

        self.edit_retirement_button = create_top_button(
            self.button_frame,
            text="Retirement",
            command=self.edit_retirement_controls,
            grid_kwargs={"row": 0, "column": 4, "padx": (25,10), "pady": 2}
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
            padx=(0,15),
            pady=2,
        )

        self.results_button, self.results_menu, self._show_results_menu = create_dropdown_button(
            self.button_frame,
            text="Results \u25BE",
            menu_labels_and_commands=[],
            row=0,
            column=6,
            padx=(25,15),
            pady=2,
        )

        self.reports_button, self.reports_menu, self._show_reports_menu = create_dropdown_button(
            self.button_frame,
            text="Reports \u25BE",
            menu_labels_and_commands=[],
            row=0,
            column=7,
            padx=(0, 15),
            pady=2,
        )

        # --- MODE BUTTON WITH DROPDOWN (reliable tk.Menubutton wiring) ---
        self.button_frame.grid_columnconfigure(8, weight=1)
        
        # Create the menubutton (button look)
        self.mode_button = tk.Menubutton(
            self.button_frame,
            text="Mode \u25BE",   # small down triangle
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
            label="Basic",
            variable=self.mode_var,
            value="Basic",
            command=self._on_mode_changed
        )
        self.mode_menu.add_radiobutton(
            label="Advanced",
            variable=self.mode_var,
            value="Advanced",
            command=self._on_mode_changed
        )

        self.mode_button["menu"] = self.mode_menu

        # --- EDIT FRAME CONTAINER ---
        self.edit_frame_container = ttk.Frame(parent)
        self.edit_frame_container.grid(row=1, column=0, columnspan=4, sticky="nsew", pady=(5,0))

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


    def edit_main_home(self):
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        home_frame = MainHomeFrame(
            self.edit_frame_container,
            title="Home",
            parent_gui=self  # important!
        )
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
            tutorial_title="Basic Tutorial",
            steps=build_basic_tutorial_steps(self),
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
            start_advanced_building_tutorial_callback=(
                self.start_advanced_building_tutorial
            ),
            start_advanced_analysis_tutorial_callback=(
                self.start_advanced_analysis_tutorial
            ),
            title="Tutorials",
        )

        tutorial_frame.pack(padx=10, pady=5, fill="x")


    def edit_notes(self):
        # Clear any existing editor frame
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        notes_frame = NotesFrame(
            self.edit_frame_container,
            title="Notes"
        )
        notes_frame.pack(padx=10, pady=5, fill="x")


    def edit_person_data(self):
        # Remove previous edit frames
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        persons = {"husband": self.husband}

        if self.simulation_controls["enable_second_person"]:
            persons["wife"] = self.wife

        person_frame = NormalIncomeEditFrame(
            self.edit_frame_container,
            persons,
            simulation_controls=self.simulation_controls,
            refresh_callback=self._on_second_person_changed,
            title="Personal Data",
            mode=self.mode_var.get()
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
            enable_second_person=self.simulation_controls.get("enable_second_person", False),
            title="Special Income"
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
            enable_second_person=self.simulation_controls.get(
                "enable_second_person",
                False,
            ),
            title="Roth Contributions / Conversions",
        )

        roth_frame.pack(
            padx=10,
            pady=5,
            fill="x",
        )


    def edit_expenses(self):
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        expenses_frame = ExpensesEditFrame(
            self.edit_frame_container,
            expensesDict=self.expensesDict,
            title="Expenses"
        )
        expenses_frame.pack(padx=10, pady=5, fill="x")


    def edit_taxes(self):
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        control_vars = {
            "_controls_dict": self.simulation_controls
        }

        taxes_frame = TaxesEditFrame(
            self.edit_frame_container,
            control_vars=control_vars,
            title="Taxes"
        )
        taxes_frame.pack(padx=10, pady=5, fill="x")


    def edit_expenses_taxes(self):
        # Clear any existing editor frame
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        control_vars = {
            "_controls_dict": self.simulation_controls
        }

        self.expenses_taxes_editor_frame = ExpensesTaxesFrame(
            self.edit_frame_container,
            expensesDict=self.expensesDict,
            control_vars=control_vars,
            title="Expenses & Taxes",
            mode=self.mode_var.get()
        )

        # Use pack like your other editors for consistency
        self.expenses_taxes_editor_frame.pack(anchor="w", pady=(20, 10), fill="both", expand=True)
    
    
    def edit_portfolio_data(self):
        # Remove previous edit frames
        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        husband_portfolio = self.husband_portfolio
        wife_portfolio = self.wife_portfolio if self.simulation_controls["enable_second_person"] else None

        portfolio_frame = PortfolioEditFrame(
            self.edit_frame_container,
            husband_portfolio=husband_portfolio,
            wife_portfolio=wife_portfolio,
            title="Portfolio Data",
            mode=self.mode_var.get()
        )
        portfolio_frame.pack(padx=10, pady=5, fill="x")


    def edit_real_estate(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        husband_portfolio = self.husband_portfolio
        wife_portfolio = self.wife_portfolio if self.simulation_controls["enable_second_person"] else None

        real_estate_frame = RealEstateEditFrame(
            self.edit_frame_container,
            husband_portfolio=husband_portfolio,
            wife_portfolio=wife_portfolio,
            title="Real Estate",
            mode=self.mode_var.get()
        )

        real_estate_frame.pack(padx=10, pady=5, fill="x")


    def edit_derived_statistics(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        husband_portfolio = self.husband_portfolio
        wife_portfolio = self.wife_portfolio if self.simulation_controls["enable_second_person"] else None

        derived_statistics_frame = DerivedStatisticsFrame(
            self.edit_frame_container,
            husband_portfolio=husband_portfolio,
            wife_portfolio=wife_portfolio,
            title="Derived Statistics",
            mode=self.mode_var.get()
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
        if self.simulation_controls["enable_second_person"]:
            persons["wife"] = self.wife

        portfolio = {"husband": self.husband_portfolio}
        if self.simulation_controls["enable_second_person"]:
            portfolio["wife"] = self.wife_portfolio

        self.retirement_editor_frame = RetirementEditFrame(
            self.edit_frame_container,
            main_gui=self, 
            control_vars=control_vars,
            persons=persons,
            portfolio=portfolio,
            title="Retirement"
        )
        self.retirement_editor_frame.pack(anchor="w", pady=(20, 10))


    def edit_simulation_assumptions(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        historical_frame = HistoricalEditFrame(
            self.edit_frame_container,
            historical_data=self,
            title="Assumptions"
        )
        historical_frame.pack(padx=10, pady=5, fill="x")


    def edit_simulation_settings(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        sim_vars = {
            "_settings_dict": self.simulation_settings
        }

        simulation_frame = PortfolioSimulationEditFrame(
            self.edit_frame_container,
            sim_vars=sim_vars,
            title="Settings"
        )
        simulation_frame.pack(padx=10, pady=5, fill="x")
        

    def edit_simulation_controls(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        control_vars = {"_controls_dict": self.simulation_controls}

        self.simulation_controls_editor_frame = SimulationControlsEditFrame(
            self.edit_frame_container,
            control_vars=control_vars,
            title="Controls"
        )
        self.simulation_controls_editor_frame.pack(
            padx=10,
            pady=5,
            fill="x",
        )


    def _rebuild_reports_menu(self):
        if not hasattr(self, "reports_menu"):
            return

        self.reports_menu.delete(0, "end")

        self.reports_menu.add_command(
            label="Executive Summary",
            command=self.edit_report_executive_summary
        )

        self.reports_menu.add_command(
            label="Year-by-Year Details",
            command=self.edit_report_year_by_year_details
        )

        self.reports_menu.add_command(
            label="Tax Report",
            command=self.edit_report_taxes
        )

        self.reports_menu.add_separator()

        self.reports_menu.add_command(
            label="Historical Window Risk Report",
            command=self.edit_report_historical_window_risk
        )

        self.reports_menu.add_command(
            label="Monte Carlo Risk Report",
            command=self.edit_report_monte_carlo_risk
        )

        self.reports_menu.add_separator()

        spending_state = (
            "normal"
            if self.simulation_controls.get("use_mode", "expenses") == "expenses"
            else "disabled"
        )

        self.reports_menu.add_command(
            label="Spending Comparison Report",
            command=self.edit_report_spending_comparison,
            state=spending_state,
        )

        self.reports_menu.add_command(
            label="Asset Allocation Comparison Report",
            command=self.edit_report_asset_allocation_comparison,
        )

        self.reports_menu.add_command(
            label="Retirement & Social Security Comparison Report",
            command=self.edit_report_retirement_ss_comparison,
        )
        

    def edit_report_executive_summary(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = ExecutiveSummaryReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["executive_summary"],
            parent_gui=self,
            title="Executive Summary"
        )
        frame.pack(padx=10, pady=5, fill="x")


    def edit_report_year_by_year_details(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = YearByYearDetailsReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["year_by_year_details"],
            parent_gui=self,
            title="Year-by-Year Details"
        )
        frame.pack(padx=10, pady=5, fill="x")


    def edit_report_taxes(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = TaxReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["tax_report"],
            parent_gui=self,
            title="Tax Report"
        )
        frame.pack(padx=10, pady=5, fill="x")


    def edit_report_historical_window_risk(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = HistoricalWindowRiskReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["historical_window_risk"],
            parent_gui=self,
            title="Historical Window Risk Report"
        )
        frame.pack(padx=10, pady=5, fill="x")


    def edit_report_monte_carlo_risk(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = MonteCarloRiskReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["monte_carlo_risk"],
            parent_gui=self,
            title="Monte Carlo Risk Report"
        )
        frame.pack(padx=10, pady=5, fill="x")


    def edit_report_spending_comparison(self):
        if not self._advanced_only():
            return

        if self.simulation_controls.get("use_mode", "expenses") != "expenses":
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = SpendingComparisonReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["spending_comparison"],
            parent_gui=self,
            title="Spending Comparison Report",
        )
        frame.pack(padx=10, pady=5, fill="x")


    def edit_report_asset_allocation_comparison(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = AssetAllocationComparisonReportFrame(
            self.edit_frame_container,
            report_options=self.report_options[
                "asset_allocation_comparison"
            ],
            parent_gui=self,
            title="Asset Allocation Comparison Report",
        )

        frame.pack(
            padx=10,
            pady=5,
            fill="x",
        )


    def edit_report_retirement_ss_comparison(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = RetirementSSComparisonReportFrame(
            self.edit_frame_container,
            report_options=self.report_options[
                "retirement_ss_comparison"
            ],
            parent_gui=self,
            title=(
                "Retirement & Social Security Comparison Report"
            ),
        )

        frame.pack(
            padx=10,
            pady=5,
            fill="x",
        )


    def _apply_mode_to_reports_button(self):
        if not hasattr(self, "reports_button"):
            return

        legal_enabled = getattr(self, "legal_accepted", False)
        advanced_enabled = self._advanced_only() and legal_enabled

        set_tk_button_soft_disabled(
            self.reports_button,
            advanced_enabled,
            self._show_reports_menu,
            noop_command=noop
        )

        self._rebuild_reports_menu()


    def _build_run_button(self):
        style = ttk.Style()
        style.configure("Big.TButton", font=("Arial", 14, "bold"), padding=(10, 10))
        style.configure("BigFaded.TButton", font=("Arial", 14, "bold"), padding=(10, 10))
        style.map(
            "BigFaded.TButton",
            foreground=[
                ("disabled", "gray60"),
                ("!disabled", "black"),
            ],
        )