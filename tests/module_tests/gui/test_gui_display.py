# test_gui_display.py

from src.warpsimlab.gui import gui_display


class DummyRoot:
    def __init__(self, width=1707, height=1067):
        self.screen_width = width
        self.screen_height = height
        self.geometry_calls = []
        self.state_calls = []
        self.attribute_calls = []
        self.current_state = "normal"
        self.current_geometry = "1200x750+100+100"
        self.update_calls = 0

    def winfo_screenwidth(self):
        return self.screen_width

    def winfo_screenheight(self):
        return self.screen_height

    def geometry(self, value=None):
        if value is None:
            return self.current_geometry
        self.geometry_calls.append(value)
        self.current_geometry = value

    def state(self, value=None):
        if value is None:
            return self.current_state
        self.state_calls.append(value)
        self.current_state = value

    def attributes(self, name, value=None):
        if value is None:
            return False
        self.attribute_calls.append((name, value))

    def update_idletasks(self):
        self.update_calls += 1

    def winfo_geometry(self):
        return self.current_geometry


class DummyScenarioController:
    def __init__(self, active=True):
        self.session_active = active
        self.position_calls = 0
        self.capture_calls = 0

    def _position_windows(self):
        self.position_calls += 1

    def capture_current_layout(self):
        self.capture_calls += 1


def _make_gui():
    gui = gui_display.PortfolioSimulatorGUI_DisplayMixin()
    gui.root = DummyRoot()
    return gui


def test_get_monitor_work_area_non_windows_uses_tk_screen(monkeypatch):
    gui = _make_gui()
    monkeypatch.setattr(gui_display.sys, "platform", "linux")

    assert gui._get_monitor_work_area(100, 200) == (0, 0, 1707, 1067)


def test_center_main_window_centers_in_work_area():
    gui = _make_gui()
    gui._get_monitor_work_area = lambda x, y: (100, 50, 1700, 950)

    gui._center_main_window(1200, 700)

    assert gui.root.geometry_calls == ["1200x700+300+150"]


def test_set_main_window_normal_windows(monkeypatch):
    gui = _make_gui()
    monkeypatch.setattr(gui_display.sys, "platform", "win32")

    gui._set_main_window_normal()

    assert gui.root.state_calls == ["normal"]


def test_set_main_window_normal_linux(monkeypatch):
    gui = _make_gui()
    monkeypatch.setattr(gui_display.sys, "platform", "linux")

    gui._set_main_window_normal()

    assert gui.root.attribute_calls == [("-zoomed", False)]


def test_set_main_window_maximized_windows(monkeypatch):
    gui = _make_gui()
    monkeypatch.setattr(gui_display.sys, "platform", "win32")

    gui._set_main_window_maximized()

    assert gui.root.state_calls == ["zoomed"]


def test_set_main_window_maximized_linux(monkeypatch):
    gui = _make_gui()
    monkeypatch.setattr(gui_display.sys, "platform", "linux")

    gui._set_main_window_maximized()

    assert gui.root.attribute_calls == [("-zoomed", True)]


def test_main_window_is_maximized_non_linux(monkeypatch):
    gui = _make_gui()
    gui.root.current_state = "zoomed"
    monkeypatch.setattr(gui_display.sys, "platform", "win32")

    assert gui._main_window_is_maximized() is True


def test_apply_automatic_main_window_size_at_reference_scale(monkeypatch):
    gui = _make_gui()
    calls = []

    class DummyFont:
        def __init__(self, *args, **kwargs):
            pass

        def metrics(self, name):
            assert name == "linespace"
            return 24

    monkeypatch.setattr(gui_display.tkfont, "Font", DummyFont)

    gui._set_main_window_normal = lambda: calls.append(("normal",))
    gui._center_main_window = lambda width, height: calls.append(("center", width, height))

    gui._apply_automatic_main_window_size()

    assert calls == [("normal",), ("center", 1200, 750)]


def test_startup_settings_restore_remembered_geometry(monkeypatch):
    gui = _make_gui()
    gui.display_settings = {
        "main_window": {
            "remember_geometry": True,
            "last_maximized": False,
            "last_geometry": "1300x800+50+60",
        }
    }

    calls = []
    gui._set_main_window_normal = lambda: calls.append("normal")
    gui._apply_selected_main_window_mode = lambda: calls.append("selected")

    monkeypatch.setattr(gui_display, "geometry_is_visible", lambda geometry, width, height: True)

    gui._apply_main_window_startup_settings()

    assert calls == ["normal"]
    assert gui.root.geometry_calls == ["1300x800+50+60"]


def test_startup_settings_restore_maximized_window():
    gui = _make_gui()
    gui.display_settings = {
        "main_window": {
            "remember_geometry": True,
            "last_maximized": True,
        }
    }

    calls = []
    gui._set_main_window_maximized = lambda: calls.append("maximized")
    gui._apply_selected_main_window_mode = lambda: calls.append("selected")

    gui._apply_main_window_startup_settings()

    assert calls == ["maximized"]


def test_startup_settings_fall_back_when_saved_geometry_not_visible(monkeypatch):
    gui = _make_gui()
    gui.display_settings = {
        "main_window": {
            "remember_geometry": True,
            "last_maximized": False,
            "last_geometry": "1300x800+9999+9999",
        }
    }

    calls = []
    gui._apply_selected_main_window_mode = lambda: calls.append("selected")

    monkeypatch.setattr(gui_display, "geometry_is_visible", lambda geometry, width, height: False)

    gui._apply_main_window_startup_settings()

    assert calls == ["selected"]


def test_selected_main_window_mode_maximized():
    gui = _make_gui()
    gui.display_settings = {
        "main_window": {
            "sizing_mode": gui_display.MAIN_WINDOW_MAXIMIZED,
        }
    }

    calls = []
    gui._set_main_window_maximized = lambda: calls.append("maximized")
    gui._apply_automatic_main_window_size = lambda: calls.append("automatic")

    gui._apply_selected_main_window_mode()

    assert calls == ["maximized"]


def test_selected_main_window_mode_custom():
    gui = _make_gui()
    gui.display_settings = {
        "main_window": {
            "sizing_mode": gui_display.MAIN_WINDOW_CUSTOM,
            "custom_width": 1450,
            "custom_height": 900,
        }
    }

    calls = []
    gui._set_main_window_normal = lambda: calls.append(("normal",))
    gui._center_main_window = lambda width, height: calls.append(("center", width, height))

    gui._apply_selected_main_window_mode()

    assert calls == [("normal",), ("center", 1450, 900)]


def test_selected_main_window_mode_automatic():
    gui = _make_gui()
    gui.display_settings = {
        "main_window": {
            "sizing_mode": gui_display.MAIN_WINDOW_AUTOMATIC,
        }
    }

    calls = []
    gui._apply_automatic_main_window_size = lambda: calls.append("automatic")

    gui._apply_selected_main_window_mode()

    assert calls == ["automatic"]


def test_apply_display_settings_repositions_active_scenario():
    gui = _make_gui()
    gui.scenario_controller = DummyScenarioController(active=True)
    gui._apply_selected_main_window_mode = lambda: None

    gui._apply_display_settings(
        {
            "main_window": {},
            "scenario_explorer": {"layout_mode": gui_display.SCENARIO_LAYOUT_AUTOMATIC},
        }
    )

    assert gui.scenario_controller.position_calls == 1
    assert gui.scenario_controller.capture_calls == 0


def test_apply_display_settings_remember_captures_and_saves(monkeypatch):
    gui = _make_gui()
    gui.scenario_controller = DummyScenarioController(active=True)
    gui._apply_selected_main_window_mode = lambda: None

    saved = []
    monkeypatch.setattr(gui_display, "save_display_settings", lambda settings: saved.append(settings))

    settings = {
        "main_window": {},
        "scenario_explorer": {"layout_mode": gui_display.SCENARIO_LAYOUT_REMEMBER},
    }

    gui._apply_display_settings(settings)

    assert gui.scenario_controller.capture_calls == 1
    assert saved == [settings]


def test_save_main_window_geometry_when_remember_enabled():
    gui = _make_gui()
    gui.display_settings = {
        "main_window": {
            "remember_geometry": True,
            "last_maximized": False,
            "last_geometry": None,
        }
    }

    gui.root.current_geometry = "1400x850+100+120"
    gui._main_window_is_maximized = lambda: False

    gui._save_main_window_geometry()

    settings = gui.display_settings["main_window"]
    assert settings["last_maximized"] is False
    assert settings["last_geometry"] == "1400x850+100+120"


def test_save_main_window_geometry_does_nothing_when_disabled():
    gui = _make_gui()
    gui.display_settings = {
        "main_window": {
            "remember_geometry": False,
            "last_geometry": "unchanged",
        }
    }

    gui._save_main_window_geometry()

    assert gui.display_settings["main_window"]["last_geometry"] == "unchanged"
    assert gui.root.update_calls == 0