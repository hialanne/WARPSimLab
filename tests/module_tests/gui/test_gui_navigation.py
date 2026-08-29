# test_gui_navigation.py

from src.warpsimlab.gui import gui_navigation


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyChild:
    def __init__(self):
        self.destroyed = False

    def destroy(self):
        self.destroyed = True


class DummyContainer:
    def __init__(self, count=1):
        self.children = [DummyChild() for _ in range(count)]

    def winfo_children(self):
        return [child for child in self.children if not child.destroyed]


class DummyMenu:
    def __init__(self):
        self.commands = []
        self.entry_calls = []
        self.separator_count = 0
        self.delete_calls = []

    def delete(self, *args):
        self.delete_calls.append(args)
        self.commands = []
        self.separator_count = 0

    def add_command(self, **kwargs):
        self.commands.append(kwargs)

    def add_separator(self):
        self.separator_count += 1

    def entryconfig(self, index, **kwargs):
        self.entry_calls.append((index, kwargs))


class DummyButton:
    def __init__(self):
        self.values = {}

    def configure(self, **kwargs):
        self.values.update(kwargs)


class DummyTutorialController:
    def __init__(self, active=False):
        self.active = active
        self.refresh_calls = 0

    def refresh_current_step(self):
        self.refresh_calls += 1


class DummyScenarioController:
    def start_or_focus(self):
        pass


def _make_gui(mode="Basic"):
    gui = gui_navigation.PortfolioSimulatorGUI_NavigationMixin()
    gui.mode_var = DummyVar(mode)
    gui.simulation_controls = {"enable_second_person": True}
    return gui


def test_advanced_only():
    gui = _make_gui("Basic")
    assert gui._advanced_only() is False

    gui.mode_var.set("Advanced")
    assert gui._advanced_only() is True


def test_sync_tax_status_from_second_person():
    gui = _make_gui()

    gui.simulation_controls["enable_second_person"] = True
    gui._sync_tax_status_from_second_person()
    assert gui.simulation_controls["tax_filing_status"] == "Married filing jointly"

    gui.simulation_controls["enable_second_person"] = False
    gui._sync_tax_status_from_second_person()
    assert gui.simulation_controls["tax_filing_status"] == "Single"


def test_load_user_mode_defaults_to_basic_when_file_missing(monkeypatch, tmp_path):
    gui = _make_gui()
    monkeypatch.setattr(gui_navigation.Path, "home", lambda: tmp_path)

    assert gui._load_user_mode() == "Basic"


def test_load_user_mode_reads_saved_advanced(monkeypatch, tmp_path):
    target = tmp_path / "Desktop" / "WARPSimLab" / "Administration"
    target.mkdir(parents=True)
    (target / "user_mode.txt").write_text("Advanced", encoding="utf-8")

    gui = _make_gui()
    monkeypatch.setattr(gui_navigation.Path, "home", lambda: tmp_path)

    assert gui._load_user_mode() == "Advanced"


def test_load_user_mode_rejects_invalid_value(monkeypatch, tmp_path):
    target = tmp_path / "Desktop" / "WARPSimLab" / "Administration"
    target.mkdir(parents=True)
    (target / "user_mode.txt").write_text("Invalid", encoding="utf-8")

    gui = _make_gui()
    monkeypatch.setattr(gui_navigation.Path, "home", lambda: tmp_path)

    assert gui._load_user_mode() == "Basic"


def test_save_user_mode(monkeypatch, tmp_path):
    gui = _make_gui("Advanced")
    monkeypatch.setattr(gui_navigation.Path, "home", lambda: tmp_path)

    gui._save_user_mode()

    mode_file = tmp_path / "Desktop" / "WARPSimLab" / "Administration" / "user_mode.txt"
    assert mode_file.read_text(encoding="utf-8") == "Advanced"


def test_save_user_mode_ignores_invalid_mode(monkeypatch, tmp_path):
    gui = _make_gui("Invalid")
    monkeypatch.setattr(gui_navigation.Path, "home", lambda: tmp_path)

    gui._save_user_mode()

    mode_file = tmp_path / "Desktop" / "WARPSimLab" / "Administration" / "user_mode.txt"
    assert not mode_file.exists()


def test_on_mode_changed_destroys_editor_children_and_calls_home():
    gui = _make_gui()
    gui.edit_frame_container = DummyContainer()
    gui.guided_tutorial_controller = DummyTutorialController(active=False)

    calls = []
    gui._save_user_mode = lambda: calls.append("save")
    gui._apply_mode_to_top_buttons = lambda: calls.append("buttons")
    gui.edit_main_home = lambda: calls.append("home")

    gui._on_mode_changed()

    assert gui.edit_frame_container.winfo_children() == []
    assert calls == ["save", "buttons", "home"]


def test_on_mode_changed_refreshes_active_tutorial_instead_of_home():
    gui = _make_gui()
    gui.edit_frame_container = DummyContainer()
    gui.guided_tutorial_controller = DummyTutorialController(active=True)

    home_calls = []
    gui._save_user_mode = lambda: None
    gui._apply_mode_to_top_buttons = lambda: None
    gui.edit_main_home = lambda: home_calls.append(True)

    gui._on_mode_changed()

    assert gui.guided_tutorial_controller.refresh_calls == 1
    assert home_calls == []


def test_on_second_person_changed_syncs_tax_and_rebuilds_person_editor():
    gui = _make_gui()
    gui.edit_frame_container = DummyContainer()
    gui.guided_tutorial_controller = DummyTutorialController(active=False)

    calls = []
    gui._sync_tax_status_from_second_person = lambda: calls.append("sync")
    gui.edit_person_data = lambda: calls.append("person")

    gui._on_second_person_changed()

    assert gui.edit_frame_container.winfo_children() == []
    assert calls == ["sync", "person"]


def test_on_second_person_changed_refreshes_active_tutorial():
    gui = _make_gui()
    gui.edit_frame_container = DummyContainer()
    gui.guided_tutorial_controller = DummyTutorialController(active=True)

    calls = []
    gui._sync_tax_status_from_second_person = lambda: calls.append("sync")
    gui.edit_person_data = lambda: calls.append("person")

    gui._on_second_person_changed()

    assert calls == ["sync"]
    assert gui.guided_tutorial_controller.refresh_calls == 1


def test_rebuild_results_menu_basic():
    gui = _make_gui("Basic")
    gui.results_menu = DummyMenu()
    gui.run_simulation_from_gui = lambda sim_type=None: None

    gui._rebuild_results_menu()

    labels = [item["label"] for item in gui.results_menu.commands]

    assert labels == [
        "Income Plots",
        "Portfolio Plots",
        "Simulation Summary",
    ]
    assert gui.results_menu.separator_count == 0


def test_rebuild_results_menu_advanced():
    gui = _make_gui("Advanced")
    gui.results_menu = DummyMenu()
    gui.run_simulation_from_gui = lambda sim_type=None: None
    gui.scenario_controller = DummyScenarioController()

    gui._rebuild_results_menu()

    labels = [item["label"] for item in gui.results_menu.commands]

    assert labels == [
        "Income Plots",
        "Cash Flow Plots",
        "Portfolio Plots",
        "Simulation Summary",
        "Scenario Explorer",
        "Cumulative Operating Balance",
    ]
    assert gui.results_menu.separator_count == 1


def test_apply_mode_to_results_button(monkeypatch):
    gui = _make_gui()
    gui.legal_accepted = True
    gui.results_button = DummyButton()
    gui.results_menu = DummyMenu()
    gui._show_results_menu = lambda: None
    gui.run_simulation_from_gui = lambda sim_type=None: None

    calls = []

    def fake_soft_disable(button, enabled, real_command, noop_command=None):
        calls.append((button, enabled, real_command, noop_command))

    monkeypatch.setattr(gui_navigation, "set_tk_button_soft_disabled", fake_soft_disable)

    gui._apply_mode_to_results_button()

    assert len(calls) == 1
    assert calls[0][0] is gui.results_button
    assert calls[0][1] is True