# gui_settings.py

import copy
import json
import os
import re
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


SETTINGS_VERSION = 1

MAIN_WINDOW_AUTOMATIC = "automatic"
MAIN_WINDOW_MAXIMIZED = "maximized"
MAIN_WINDOW_CUSTOM = "custom"

SCENARIO_LAYOUT_AUTOMATIC = "automatic"
SCENARIO_LAYOUT_REMEMBER = "remember"

GEOMETRY_PATTERN = re.compile(
    r"^(?P<width>\d+)x(?P<height>\d+)"
    r"(?P<x>[+-]\d+)(?P<y>[+-]\d+)$"
)


def get_default_settings():
    """
    Return a new dictionary containing the default display settings.
    """
    return {
        "version": SETTINGS_VERSION,
        "main_window": {
            "sizing_mode": MAIN_WINDOW_AUTOMATIC,
            "custom_width": 1200,
            "custom_height": 750,
            "remember_geometry": False,
            "last_geometry": None,
            "last_maximized": False,
        },
        "scenario_explorer": {
            "layout_mode": SCENARIO_LAYOUT_AUTOMATIC,
            "layout": None,
        },
    }


def get_settings_directory():
    """
    Return the WARPSimLab administration directory on the user's Desktop.
    """
    return (
        Path.home()
        / "Desktop"
        / "WARPSimLab"
        / "Administration"
    )


def get_settings_path():
    """
    Return the full path to the display settings JSON file.
    """
    settings_path = (
        get_settings_directory()
        / "display_settings.json"
    )

    return settings_path


def _merge_settings(defaults, loaded):
    """
    Recursively copy recognized loaded values into the defaults.

    Unknown keys are ignored so old or manually edited files cannot add
    unexpected settings to the active configuration.
    """
    merged = copy.deepcopy(defaults)

    if not isinstance(loaded, dict):
        return merged

    for key, default_value in defaults.items():
        if key not in loaded:
            continue

        loaded_value = loaded[key]

        if isinstance(default_value, dict):
            merged[key] = _merge_settings(
                default_value,
                loaded_value,
            )
        else:
            merged[key] = loaded_value

    return merged


def parse_geometry(geometry):
    """
    Parse a Tk geometry string.

    Returns:
        A dictionary containing width, height, x, and y, or None.
    """
    if not isinstance(geometry, str):
        return None

    match = GEOMETRY_PATTERN.fullmatch(geometry.strip())
    if match is None:
        return None

    values = {
        name: int(value)
        for name, value in match.groupdict().items()
    }

    if values["width"] <= 0 or values["height"] <= 0:
        return None

    return values


def geometry_is_visible(
    geometry,
    screen_width,
    screen_height,
    minimum_visible_width=100,
    minimum_visible_height=80,
):
    """
    Return True when a saved window geometry remains reachable.

    The entire window does not need to fit on the current screen. At least
    part of the window must remain visible so the user can move or resize it.
    """
    parsed = parse_geometry(geometry)
    if parsed is None:
        return False

    width = parsed["width"]
    height = parsed["height"]
    x = parsed["x"]
    y = parsed["y"]

    right = x + width
    bottom = y + height

    visible_width = min(right, screen_width) - max(x, 0)
    visible_height = min(bottom, screen_height) - max(y, 0)

    required_width = min(minimum_visible_width, width)
    required_height = min(minimum_visible_height, height)

    return (
        visible_width >= required_width
        and visible_height >= required_height
    )


def _validated_settings(settings):
    """
    Validate loaded settings and replace invalid values with defaults.
    """
    defaults = get_default_settings()
    validated = _merge_settings(defaults, settings)

    main_settings = validated["main_window"]

    valid_main_modes = {
        MAIN_WINDOW_AUTOMATIC,
        MAIN_WINDOW_MAXIMIZED,
        MAIN_WINDOW_CUSTOM,
    }

    if main_settings["sizing_mode"] not in valid_main_modes:
        main_settings["sizing_mode"] = MAIN_WINDOW_AUTOMATIC

    try:
        main_settings["custom_width"] = int(
            main_settings["custom_width"]
        )
    except (TypeError, ValueError):
        main_settings["custom_width"] = 1200

    try:
        main_settings["custom_height"] = int(
            main_settings["custom_height"]
        )
    except (TypeError, ValueError):
        main_settings["custom_height"] = 750

    if main_settings["custom_width"] <= 0:
        main_settings["custom_width"] = 1200

    if main_settings["custom_height"] <= 0:
        main_settings["custom_height"] = 750

    main_settings["remember_geometry"] = bool(
        main_settings["remember_geometry"]
    )
    main_settings["last_maximized"] = bool(
        main_settings["last_maximized"]
    )

    if parse_geometry(main_settings["last_geometry"]) is None:
        main_settings["last_geometry"] = None

    scenario_settings = validated["scenario_explorer"]

    valid_scenario_modes = {
        SCENARIO_LAYOUT_AUTOMATIC,
        SCENARIO_LAYOUT_REMEMBER,
    }

    if scenario_settings["layout_mode"] not in valid_scenario_modes:
        scenario_settings["layout_mode"] = (
            SCENARIO_LAYOUT_AUTOMATIC
        )

    layout = scenario_settings.get("layout")
    if not isinstance(layout, dict):
        scenario_settings["layout"] = None
    else:
        expected_names = {
            "income_plot",
            "portfolio_plot",
            "dashboard",
        }

        if set(layout.keys()) != expected_names:
            scenario_settings["layout"] = None
        elif any(
            parse_geometry(layout[name]) is None
            for name in expected_names
        ):
            scenario_settings["layout"] = None

    validated["version"] = SETTINGS_VERSION

    return validated


def load_display_settings():
    """
    Load display settings.

    Missing, unreadable, or invalid files silently fall back to defaults.
    """
    settings_path = get_settings_path()

    try:
        with settings_path.open(
            "r",
            encoding="utf-8",
        ) as settings_file:
            loaded = json.load(settings_file)
    except (
        FileNotFoundError,
        PermissionError,
        OSError,
        json.JSONDecodeError,
    ):
        return get_default_settings()

    return _validated_settings(loaded)


def save_display_settings(settings):
    """
    Validate and save display settings.

    Returns:
        True when the settings were saved successfully.
        False when the settings could not be saved.
    """
    validated = _validated_settings(settings)
    settings_path = get_settings_path()

    try:
        settings_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = settings_path.with_suffix(".tmp")

        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as settings_file:
            json.dump(
                validated,
                settings_file,
                indent=4,
            )
            settings_file.write("\n")

        temporary_path.replace(settings_path)
    except (PermissionError, OSError):
        return False

    return True


class DisplaySettingsDialog(tk.Toplevel):
    """
    Edit WARPSimLab display preferences.
    """

    def __init__(
        self,
        parent,
        settings,
        apply_callback,
    ):
        super().__init__(parent)

        self.parent = parent
        self.apply_callback = apply_callback
        self.original_settings = copy.deepcopy(settings)

        self.title("Settings")
        self.resizable(False, False)
        self.transient(parent)

        self.main_sizing_mode = tk.StringVar(
            value=settings["main_window"]["sizing_mode"]
        )
        self.custom_width = tk.StringVar(
            value=str(
                settings["main_window"]["custom_width"]
            )
        )
        self.custom_height = tk.StringVar(
            value=str(
                settings["main_window"]["custom_height"]
            )
        )
        self.remember_main_geometry = tk.BooleanVar(
            value=settings["main_window"]["remember_geometry"]
        )
        self.scenario_layout_mode = tk.StringVar(
            value=settings["scenario_explorer"]["layout_mode"]
        )

        self._build_fields()
        self._update_custom_field_state()

        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.update_idletasks()
        self._center_over_parent()

        self.grab_set()
        self.custom_width_entry.focus_set()

    def _build_fields(self):
        """
        Build the dialog controls.
        """
        outer_frame = ttk.Frame(
            self,
            padding=12,
        )
        outer_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        main_frame = ttk.LabelFrame(
            outer_frame,
            text="Main Window",
            padding=10,
        )
        main_frame.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        main_frame.columnconfigure(1, weight=1)

        ttk.Radiobutton(
            main_frame,
            text="Automatic - 80% of reported screen size",
            variable=self.main_sizing_mode,
            value=MAIN_WINDOW_AUTOMATIC,
            command=self._update_custom_field_state,
        ).grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 6),
        )

        ttk.Radiobutton(
            main_frame,
            text="Maximized",
            variable=self.main_sizing_mode,
            value=MAIN_WINDOW_MAXIMIZED,
            command=self._update_custom_field_state,
        ).grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 6),
        )

        ttk.Radiobutton(
            main_frame,
            text="Custom size",
            variable=self.main_sizing_mode,
            value=MAIN_WINDOW_CUSTOM,
            command=self._update_custom_field_state,
        ).grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 6),
        )

        ttk.Label(
            main_frame,
            text="Width:",
        ).grid(
            row=3,
            column=0,
            sticky="e",
            padx=(24, 6),
            pady=3,
        )

        self.custom_width_entry = ttk.Entry(
            main_frame,
            textvariable=self.custom_width,
            width=10,
        )
        self.custom_width_entry.grid(
            row=3,
            column=1,
            sticky="w",
            pady=3,
        )

        ttk.Label(
            main_frame,
            text="pixels",
        ).grid(
            row=3,
            column=2,
            sticky="w",
            padx=(6, 0),
            pady=3,
        )

        ttk.Label(
            main_frame,
            text="Height:",
        ).grid(
            row=4,
            column=0,
            sticky="e",
            padx=(24, 6),
            pady=3,
        )

        self.custom_height_entry = ttk.Entry(
            main_frame,
            textvariable=self.custom_height,
            width=10,
        )
        self.custom_height_entry.grid(
            row=4,
            column=1,
            sticky="w",
            pady=3,
        )

        ttk.Label(
            main_frame,
            text="pixels",
        ).grid(
            row=4,
            column=2,
            sticky="w",
            padx=(6, 0),
            pady=3,
        )

        ttk.Checkbutton(
            main_frame,
            text=(
                "Remember the last window size, position, "
                "and maximized state"
            ),
            variable=self.remember_main_geometry,
        ).grid(
            row=5,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(10, 0),
        )

        ttk.Label(
            main_frame,
            text=(
                "When enabled, the remembered window layout takes "
                "priority at the next startup."
            ),
            wraplength=430,
            justify="left",
        ).grid(
            row=6,
            column=0,
            columnspan=3,
            sticky="w",
            padx=(24, 0),
            pady=(3, 0),
        )

        scenario_frame = ttk.LabelFrame(
            outer_frame,
            text="Scenario Explorer",
            padding=10,
        )
        scenario_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(12, 0),
        )

        ttk.Radiobutton(
            scenario_frame,
            text="Automatic layout",
            variable=self.scenario_layout_mode,
            value=SCENARIO_LAYOUT_AUTOMATIC,
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 6),
        )

        ttk.Radiobutton(
            scenario_frame,
            text="Remember last window sizes and positions",
            variable=self.scenario_layout_mode,
            value=SCENARIO_LAYOUT_REMEMBER,
        ).grid(
            row=1,
            column=0,
            sticky="w",
        )

        button_frame = ttk.Frame(outer_frame)
        button_frame.grid(
            row=2,
            column=0,
            sticky="e",
            pady=(14, 0),
        )

        ttk.Button(
            button_frame,
            text="Restore Defaults",
            command=self._restore_defaults,
        ).pack(
            side="left",
            padx=(0, 20),
        )

        ttk.Button(
            button_frame,
            text="OK",
            command=self._apply,
        ).pack(
            side="left",
            padx=(0, 6),
        )

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy,
        ).pack(side="left")

    def _update_custom_field_state(self):
        """
        Enable custom dimensions only while Custom size is selected.
        """
        custom_selected = (
            self.main_sizing_mode.get()
            == MAIN_WINDOW_CUSTOM
        )

        state = "normal" if custom_selected else "disabled"

        self.custom_width_entry.configure(state=state)
        self.custom_height_entry.configure(state=state)

    def _restore_defaults(self):
        """
        Restore the controls to the automatic defaults.

        The defaults are not applied until the user presses OK.
        """
        defaults = get_default_settings()

        self.main_sizing_mode.set(
            defaults["main_window"]["sizing_mode"]
        )
        self.custom_width.set(
            str(defaults["main_window"]["custom_width"])
        )
        self.custom_height.set(
            str(defaults["main_window"]["custom_height"])
        )
        self.remember_main_geometry.set(
            defaults["main_window"]["remember_geometry"]
        )
        self.scenario_layout_mode.set(
            defaults["scenario_explorer"]["layout_mode"]
        )

        self._update_custom_field_state()

    def _read_positive_integer(self, value, field_name):
        """
        Convert an entry value to a positive integer.
        """
        try:
            parsed_value = int(value)
        except ValueError:
            messagebox.showerror(
                "Invalid Settings",
                f"{field_name} must be a whole number.",
                parent=self,
            )
            return None

        if parsed_value <= 0:
            messagebox.showerror(
                "Invalid Settings",
                f"{field_name} must be greater than zero.",
                parent=self,
            )
            return None

        return parsed_value

    def _apply(self):
        """
        Validate, save, and immediately apply the selected settings.
        """
        custom_width = self._read_positive_integer(
            self.custom_width.get().strip(),
            "Custom width",
        )
        if custom_width is None:
            return

        custom_height = self._read_positive_integer(
            self.custom_height.get().strip(),
            "Custom height",
        )
        if custom_height is None:
            return

        if (
            self.main_sizing_mode.get()
            == MAIN_WINDOW_CUSTOM
            and (
                custom_width < 1200
                or custom_height < 750
            )
        ):
            continue_with_small_size = messagebox.askyesno(
                "Small Custom Window",
                (
                    "WARPSimLab is designed for a minimum useful "
                    "window size of 1200 by 750 pixels.\n\n"
                    "Use the smaller custom size anyway?"
                ),
                parent=self,
            )

            if not continue_with_small_size:
                return

        updated_settings = copy.deepcopy(
            self.original_settings
        )

        updated_settings["main_window"]["sizing_mode"] = (
            self.main_sizing_mode.get()
        )
        updated_settings["main_window"]["custom_width"] = (
            custom_width
        )
        updated_settings["main_window"]["custom_height"] = (
            custom_height
        )
        updated_settings["main_window"]["remember_geometry"] = (
            bool(self.remember_main_geometry.get())
        )

        updated_settings["scenario_explorer"]["layout_mode"] = (
            self.scenario_layout_mode.get()
        )

        if (
            self.scenario_layout_mode.get()
            == SCENARIO_LAYOUT_AUTOMATIC
        ):
            updated_settings["scenario_explorer"]["layout"] = None

        if not save_display_settings(updated_settings):
            messagebox.showerror(
                "Settings Not Saved",
                (
                    "WARPSimLab could not save the display settings "
                    "in the user configuration directory."
                ),
                parent=self,
            )
            return

        self.apply_callback(updated_settings)
        self.destroy()

    def _center_over_parent(self):
        """
        Center the dialog over the parent window.
        """
        width = self.winfo_width()
        height = self.winfo_height()

        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        x = parent_x + max((parent_width - width) // 2, 0)
        y = parent_y + max((parent_height - height) // 2, 0)

        self.geometry(f"+{x}+{y}")