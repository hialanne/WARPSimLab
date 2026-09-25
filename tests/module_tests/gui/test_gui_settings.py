from __future__ import annotations

import json
import tkinter as tk

import pytest

from src.warpsimlab.gui import gui_settings as mod


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")

    root.withdraw()
    yield root
    root.destroy()


def test_default_settings_include_main_summary_and_scenario_sections():
    settings = mod.get_default_settings()

    assert settings["version"] == mod.SETTINGS_VERSION

    assert settings["main_window"]["sizing_mode"] == mod.MAIN_WINDOW_AUTOMATIC
    assert settings["main_window"]["remember_geometry"] is False
    assert settings["main_window"]["last_geometry"] is None
    assert settings["main_window"]["last_maximized"] is False

    assert settings["summary_dialog"]["sizing_mode"] == mod.SUMMARY_DIALOG_AUTOMATIC
    assert settings["summary_dialog"]["remember_geometry"] is False
    assert settings["summary_dialog"]["last_geometry"] is None
    assert settings["summary_dialog"]["last_maximized"] is False

    assert settings["scenario_explorer"]["layout_mode"] == mod.SCENARIO_LAYOUT_AUTOMATIC
    assert settings["scenario_explorer"]["layout"] is None


def test_merge_settings_preserves_new_defaults_for_old_settings_file():
    defaults = mod.get_default_settings()

    old_settings = {
        "version": 1,
        "main_window": {
            "sizing_mode": mod.MAIN_WINDOW_MAXIMIZED,
            "custom_width": 1400,
            "custom_height": 900,
            "remember_geometry": True,
            "last_geometry": "1400x900+20+30",
            "last_maximized": False,
        },
        "scenario_explorer": {
            "layout_mode": mod.SCENARIO_LAYOUT_REMEMBER,
            "layout": None,
        },
    }

    merged = mod._merge_settings(defaults, old_settings)

    assert merged["main_window"]["sizing_mode"] == mod.MAIN_WINDOW_MAXIMIZED
    assert merged["summary_dialog"] == defaults["summary_dialog"]
    assert merged["scenario_explorer"]["layout_mode"] == mod.SCENARIO_LAYOUT_REMEMBER


def test_merge_settings_ignores_unknown_keys():
    defaults = mod.get_default_settings()

    loaded = {
        "unknown_section": {"bad": True},
        "main_window": {
            "unknown_setting": 123,
        },
    }

    merged = mod._merge_settings(defaults, loaded)

    assert "unknown_section" not in merged
    assert "unknown_setting" not in merged["main_window"]


def test_parse_geometry_accepts_valid_geometry():
    assert mod.parse_geometry("1200x750+100+200") == {
        "width": 1200,
        "height": 750,
        "x": 100,
        "y": 200,
    }

    assert mod.parse_geometry("800x600-50+20") == {
        "width": 800,
        "height": 600,
        "x": -50,
        "y": 20,
    }


@pytest.mark.parametrize(
    "geometry",
    [
        None,
        "",
        "1200x750",
        "1200x750+10",
        "0x750+0+0",
        "1200x0+0+0",
        "invalid",
    ],
)
def test_parse_geometry_rejects_invalid_geometry(geometry):
    assert mod.parse_geometry(geometry) is None


def test_geometry_is_visible_when_window_overlaps_screen():
    assert mod.geometry_is_visible("1200x750+100+100", 1920, 1080) is True
    assert mod.geometry_is_visible("1200x750+1800+100", 1920, 1080) is True


def test_geometry_is_not_visible_when_window_is_off_screen():
    assert mod.geometry_is_visible("1200x750+2000+100", 1920, 1080) is False
    assert mod.geometry_is_visible("1200x750+100+1200", 1920, 1080) is False


def test_validated_settings_rejects_invalid_summary_values():
    settings = mod.get_default_settings()

    settings["summary_dialog"]["sizing_mode"] = "nonsense"
    settings["summary_dialog"]["last_geometry"] = "bad geometry"
    settings["summary_dialog"]["remember_geometry"] = 1
    settings["summary_dialog"]["last_maximized"] = 0

    validated = mod._validated_settings(settings)

    assert validated["summary_dialog"]["sizing_mode"] == mod.SUMMARY_DIALOG_AUTOMATIC
    assert validated["summary_dialog"]["last_geometry"] is None
    assert validated["summary_dialog"]["remember_geometry"] is True
    assert validated["summary_dialog"]["last_maximized"] is False


def test_validated_settings_accepts_summary_maximized_mode():
    settings = mod.get_default_settings()
    settings["summary_dialog"]["sizing_mode"] = mod.SUMMARY_DIALOG_MAXIMIZED
    settings["summary_dialog"]["last_geometry"] = "1000x700+20+30"

    validated = mod._validated_settings(settings)

    assert validated["summary_dialog"]["sizing_mode"] == mod.SUMMARY_DIALOG_MAXIMIZED
    assert validated["summary_dialog"]["last_geometry"] == "1000x700+20+30"


def test_save_and_load_display_settings_round_trip(monkeypatch, tmp_path):
    settings_path = tmp_path / "display_settings.json"
    monkeypatch.setattr(mod, "get_settings_path", lambda: settings_path)

    settings = mod.get_default_settings()
    settings["main_window"]["sizing_mode"] = mod.MAIN_WINDOW_MAXIMIZED
    settings["summary_dialog"]["sizing_mode"] = mod.SUMMARY_DIALOG_MAXIMIZED
    settings["summary_dialog"]["remember_geometry"] = True
    settings["summary_dialog"]["last_geometry"] = "1100x750+10+20"

    assert mod.save_display_settings(settings) is True

    loaded = mod.load_display_settings()

    assert loaded["main_window"]["sizing_mode"] == mod.MAIN_WINDOW_MAXIMIZED
    assert loaded["summary_dialog"]["sizing_mode"] == mod.SUMMARY_DIALOG_MAXIMIZED
    assert loaded["summary_dialog"]["remember_geometry"] is True
    assert loaded["summary_dialog"]["last_geometry"] == "1100x750+10+20"


def test_load_display_settings_uses_defaults_for_bad_json(monkeypatch, tmp_path):
    settings_path = tmp_path / "display_settings.json"
    settings_path.write_text("{broken json", encoding="utf-8")
    monkeypatch.setattr(mod, "get_settings_path", lambda: settings_path)

    assert mod.load_display_settings() == mod.get_default_settings()


def test_display_settings_dialog_restore_defaults(tk_root):
    settings = mod.get_default_settings()
    settings["main_window"]["sizing_mode"] = mod.MAIN_WINDOW_MAXIMIZED
    settings["summary_dialog"]["sizing_mode"] = mod.SUMMARY_DIALOG_MAXIMIZED
    settings["summary_dialog"]["remember_geometry"] = True
    settings["scenario_explorer"]["layout_mode"] = mod.SCENARIO_LAYOUT_REMEMBER

    dialog = mod.DisplaySettingsDialog(tk_root, settings, lambda updated: None)

    dialog._restore_defaults()

    defaults = mod.get_default_settings()

    assert dialog.main_sizing_mode.get() == defaults["main_window"]["sizing_mode"]
    assert dialog.custom_width.get() == str(defaults["main_window"]["custom_width"])
    assert dialog.custom_height.get() == str(defaults["main_window"]["custom_height"])
    assert dialog.remember_main_geometry.get() == defaults["main_window"]["remember_geometry"]

    assert dialog.summary_sizing_mode.get() == defaults["summary_dialog"]["sizing_mode"]
    assert dialog.remember_summary_geometry.get() == defaults["summary_dialog"]["remember_geometry"]

    assert dialog.scenario_layout_mode.get() == defaults["scenario_explorer"]["layout_mode"]

    dialog.destroy()


def test_display_settings_dialog_apply_saves_summary_settings(monkeypatch, tk_root):
    settings = mod.get_default_settings()
    applied = []
    saved = []

    monkeypatch.setattr(mod, "save_display_settings", lambda updated: saved.append(updated) or True)

    dialog = mod.DisplaySettingsDialog(tk_root, settings, applied.append)

    dialog.summary_sizing_mode.set(mod.SUMMARY_DIALOG_MAXIMIZED)
    dialog.remember_summary_geometry.set(True)

    dialog._apply()

    assert len(saved) == 1
    assert saved[0]["summary_dialog"]["sizing_mode"] == mod.SUMMARY_DIALOG_MAXIMIZED
    assert saved[0]["summary_dialog"]["remember_geometry"] is True

    assert len(applied) == 1
    assert applied[0]["summary_dialog"]["sizing_mode"] == mod.SUMMARY_DIALOG_MAXIMIZED