# gui_display.py

import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from src.warpsimlab.gui.gui_settings import (
    DisplaySettingsDialog,
    MAIN_WINDOW_AUTOMATIC,
    MAIN_WINDOW_CUSTOM,
    MAIN_WINDOW_MAXIMIZED,
    SCENARIO_LAYOUT_AUTOMATIC,
    SCENARIO_LAYOUT_REMEMBER,
    geometry_is_visible,
    save_display_settings,
)


class PortfolioSimulatorGUI_DisplayMixin:
    def _apply_dark_mode_diagnostic_theme(self):
        """
        TEMPORARY: Force TTK into a dark palette for GUI diagnostics.
        Remove or disable before production release.
        """
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(".", background="#2b2b2b", foreground="#f0f0f0", fieldbackground="#3a3a3a")
        style.configure("TFrame", background="#2b2b2b")
        style.configure("TLabel", background="#2b2b2b", foreground="#f0f0f0")
        style.configure("TLabelframe", background="#2b2b2b", foreground="#f0f0f0")
        style.configure("TLabelframe.Label", background="#2b2b2b", foreground="#f0f0f0")
        style.configure("TCheckbutton", background="#2b2b2b", foreground="#f0f0f0")
        style.configure("TRadiobutton", background="#2b2b2b", foreground="#f0f0f0")
        style.configure("TEntry", fieldbackground="#3a3a3a", foreground="#f0f0f0")
        style.configure("TCombobox", fieldbackground="#3a3a3a", foreground="#f0f0f0")

        style.map("TCheckbutton", background=[("active", "#2b2b2b")], foreground=[("active", "#f0f0f0")])
        style.map("TRadiobutton", background=[("active", "#2b2b2b")], foreground=[("active", "#f0f0f0")])
        style.map("TLabel", background=[("disabled", "#2b2b2b")], foreground=[("disabled", "#9a9a9a")])
        style.map("TEntry", fieldbackground=[("disabled", "#333333")], foreground=[("disabled", "#9a9a9a")])
        style.map("TMenubutton", background=[("disabled", "#333333")], foreground=[("disabled", "#9a9a9a")])

        style.configure("TButton", background="#3a3a3a", foreground="#f0f0f0")
        style.map(
            "TButton",
            background=[("disabled", "#333333"), ("active", "#4a4a4a")],
            foreground=[("disabled", "#9a9a9a"), ("active", "#f0f0f0")],
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
            monitor = user32.MonitorFromPoint(point, MONITOR_DEFAULTTONEAREST)

            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD),
                ]

            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            user32.GetMonitorInfoW(monitor, ctypes.byref(info))

            return info.rcWork.left, info.rcWork.top, info.rcWork.right, info.rcWork.bottom

        return 0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def _center_main_window(self, width, height):
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            cursor = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(cursor))
            work_left, work_top, work_right, work_bottom = self._get_monitor_work_area(cursor.x, cursor.y)
        else:
            work_left, work_top, work_right, work_bottom = self._get_monitor_work_area(0, 0)

        work_width = work_right - work_left
        work_height = work_bottom - work_top

        x = work_left + (work_width - width) // 2
        y = work_top + (work_height - height) // 2

        self.root.geometry(f"{width}x{height}+{x}+{y}")

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

        font_14 = tkfont.Font(root=self.root, family="Arial", size=14)
        font_16 = tkfont.Font(root=self.root, family="Arial", size=16)

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
        print(f"TkDefaultFont linespace: {default_font.metrics('linespace')}")

        test_label = ttk.Label(self.root, text="WARPSimLab", font=("Arial", 16))
        test_button = ttk.Button(self.root, text="Test Button")

        test_label.update_idletasks()
        test_button.update_idletasks()

        print(f"Arial 16 label requested size: {test_label.winfo_reqwidth()}x{test_label.winfo_reqheight()}")
        print(f"TTK button requested size: {test_button.winfo_reqwidth()}x{test_button.winfo_reqheight()}")

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

            def monitor_enum_proc(monitor, hdc, rect_pointer, data):
                info = MONITORINFO()
                info.cbSize = ctypes.sizeof(MONITORINFO)
                user32.GetMonitorInfoW(monitor, ctypes.byref(info))

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
            user32.EnumDisplayMonitors(None, None, callback, 0)

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

        print(f"root requested size: {self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")
        print(f"root actual size: {self.root.winfo_width()}x{self.root.winfo_height()}")
        print(f"main frame requested size: {self.frame.winfo_reqwidth()}x{self.frame.winfo_reqheight()}")
        print(f"main frame actual size: {self.frame.winfo_width()}x{self.frame.winfo_height()}")
        print(f"top frame requested size: {self.top_frame.winfo_reqwidth()}x{self.top_frame.winfo_reqheight()}")
        print(f"top frame actual size: {self.top_frame.winfo_width()}x{self.top_frame.winfo_height()}")
        print(f"button frame requested size: {self.button_frame.winfo_reqwidth()}x{self.button_frame.winfo_reqheight()}")
        print(f"button frame actual size: {self.button_frame.winfo_width()}x{self.button_frame.winfo_height()}")
        print(
            f"editor container requested size: "
            f"{self.edit_frame_container.winfo_reqwidth()}x{self.edit_frame_container.winfo_reqheight()}"
        )
        print(
            f"editor container actual size: "
            f"{self.edit_frame_container.winfo_width()}x{self.edit_frame_container.winfo_height()}"
        )

        if hasattr(self, "home_frame"):
            print(f"home frame requested size: {self.home_frame.winfo_reqwidth()}x{self.home_frame.winfo_reqheight()}")
            print(f"home frame actual size: {self.home_frame.winfo_width()}x{self.home_frame.winfo_height()}")

            if hasattr(self.home_frame, "intro_label"):
                intro_label = self.home_frame.intro_label

                print(
                    f"intro label requested size: "
                    f"{intro_label.winfo_reqwidth()}x{intro_label.winfo_reqheight()}"
                )
                print(f"intro label actual size: {intro_label.winfo_width()}x{intro_label.winfo_height()}")
                print(f"intro label wraplength: {intro_label.cget('wraplength')}")

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
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")

    def _main_window_is_maximized(self):
        """
        Return True when the main window is currently maximized.
        """
        try:
            if sys.platform.startswith("linux"):
                return bool(self.root.attributes("-zoomed"))

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

        reference_font = tkfont.Font(family="Arial", size=16)
        current_font_linespace = reference_font.metrics("linespace")

        gui_scale = current_font_linespace / development_font_linespace

        effective_screen_width = screen_width / gui_scale
        effective_screen_height = screen_height / gui_scale

        width_scale = effective_screen_width / development_screen_width
        height_scale = effective_screen_height / development_screen_height

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
        self._center_main_window(window_width, window_height)

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

            if geometry_is_visible(saved_geometry, screen_width, screen_height):
                self._set_main_window_normal()
                self.root.geometry(saved_geometry)
                return

        self._apply_selected_main_window_mode()

    def _apply_selected_main_window_mode(self):
        """
        Apply the selected Automatic, Maximized, or Custom policy.
        """
        main_settings = self.display_settings["main_window"]
        sizing_mode = main_settings.get("sizing_mode", MAIN_WINDOW_AUTOMATIC)

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
        DisplaySettingsDialog(self.root, self.display_settings, self._apply_display_settings)

    def _apply_display_settings(self, updated_settings):
        """
        Store and immediately apply settings returned by the dialog.
        """
        self.display_settings = updated_settings

        self._apply_selected_main_window_mode()

        scenario_controller = getattr(self, "scenario_controller", None)

        if scenario_controller is not None and scenario_controller.session_active:
            scenario_mode = self.display_settings["scenario_explorer"]["layout_mode"]

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
            main_settings["last_geometry"] = self.root.winfo_geometry()