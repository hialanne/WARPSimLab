# test_gui_editors.py

import pytest

from src.warpsimlab.gui import gui_editors


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class DummyChild:
    def __init__(self):
        self.destroyed = False

    def destroy(self):
        self.destroyed = True


class DummyContainer:
    def __init__(self):
        self.children = [DummyChild()]

    def winfo_children(self):
        return [child for child in self.children if not child.destroyed]


class DummyFrame:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.pack_calls = []

    def pack(self, **kwargs):
        self.pack_calls.append(kwargs)


class FrameFactory:
    def __init__(self):
        self.instances = []

    def __call__(self, *args, **kwargs):
        frame = DummyFrame(*args, **kwargs)
        self.instances.append(frame)
        return frame


class DummyTutorialController:
    def __init__(self):
        self.calls = []

    def start(self, **kwargs):
        self.calls.append(kwargs)


def _make_gui(advanced=True, second_person=True):
    gui = gui_editors.PortfolioSimulatorGUI_EditorsMixin()
    gui.edit_frame_container = DummyContainer()
    gui.mode_var = DummyVar("Advanced" if advanced else "Basic")
    gui._advanced_only = lambda: advanced

    gui.husband = object()
    gui.wife = object()
    gui.husband_portfolio = object()
    gui.wife_portfolio = object()

    gui.simulation_controls = {"second_person_enabled": second_person}
    gui.simulation_settings = {"test": True, "start_year": 2025}
    gui.special_income_streams = [{"test": 1}]
    gui.roth_flows = [{"test": 2}]
    gui.expensesDict = object()
    gui._on_second_person_changed = lambda: None

    return gui


def test_edit_main_home(monkeypatch):
    gui = _make_gui()
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "MainHomeFrame", factory)

    gui.edit_main_home()

    assert gui.edit_frame_container.winfo_children() == []
    assert len(factory.instances) == 1
    assert factory.instances[0].kwargs["title"] == "Home"
    assert factory.instances[0].kwargs["parent_gui"] is gui
    assert gui.home_frame is factory.instances[0]


def test_edit_blank_clears_editor():
    gui = _make_gui()

    gui.edit_blank()

    assert gui.edit_frame_container.winfo_children() == []


def test_edit_tutorial_blank_calls_edit_blank():
    gui = _make_gui()
    calls = []
    gui.edit_blank = lambda: calls.append(True)

    gui.edit_tutorial_blank()

    assert calls == [True]


def test_tutorial_start_methods(monkeypatch):
    gui = _make_gui()
    gui.guided_tutorial_controller = DummyTutorialController()

    monkeypatch.setattr(gui_editors, "build_basic_tutorial_steps", lambda parent: ["basic"])
    monkeypatch.setattr(gui_editors, "build_advanced_building_tutorial_steps", lambda parent: ["building"])
    monkeypatch.setattr(gui_editors, "build_advanced_analysis_tutorial_steps", lambda parent: ["analysis"])

    gui.start_basic_tutorial()
    gui.start_advanced_building_tutorial()
    gui.start_advanced_analysis_tutorial()

    assert gui.guided_tutorial_controller.calls == [
        {"tutorial_title": "Basic Tutorial", "steps": ["basic"]},
        {"tutorial_title": "Advanced Tutorial 1: Building the Simulation", "steps": ["building"]},
        {"tutorial_title": "Advanced Tutorial 2: Analyzing Results", "steps": ["analysis"]},
    ]


def test_edit_tutorial(monkeypatch):
    gui = _make_gui()
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "TutorialFrame", factory)

    gui.edit_tutorial()

    frame = factory.instances[0]
    assert frame.kwargs["title"] == "Tutorials"
    assert frame.kwargs["start_basic_tutorial_callback"] == gui.start_basic_tutorial
    assert frame.kwargs["start_advanced_building_tutorial_callback"] == gui.start_advanced_building_tutorial
    assert frame.kwargs["start_advanced_analysis_tutorial_callback"] == gui.start_advanced_analysis_tutorial


def test_edit_notes(monkeypatch):
    gui = _make_gui()
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "NotesFrame", factory)

    gui.edit_notes()

    assert factory.instances[0].kwargs["title"] == "Notes"


@pytest.mark.parametrize("second_person", [False, True])
def test_edit_person_data(monkeypatch, second_person):
    gui = _make_gui(second_person=second_person)
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "NormalIncomeEditFrame", factory)

    gui.edit_person_data()

    frame = factory.instances[0]
    persons = frame.args[1]

    assert persons["husband"] is gui.husband
    assert ("wife" in persons) is second_person
    if second_person:
        assert persons["wife"] is gui.wife

    assert frame.kwargs["simulation_controls"] is gui.simulation_controls
    assert frame.kwargs["mode"] == "Advanced"


@pytest.mark.parametrize(
    "method_name,class_name",
    [
        ("edit_special_income", "SpecialIncomeEditFrame"),
        ("edit_roth", "RothEditFrame"),
        ("edit_real_estate", "RealEstateEditFrame"),
        ("edit_derived_statistics", "DerivedStatisticsFrame"),
        ("edit_simulation_assumptions", "HistoricalEditFrame"),
        ("edit_simulation_settings", "PortfolioSimulationEditFrame"),
        ("edit_simulation_controls", "SimulationControlsEditFrame"),
    ],
)
def test_advanced_editors_do_nothing_in_basic_mode(monkeypatch, method_name, class_name):
    gui = _make_gui(advanced=False)
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, class_name, factory)

    getattr(gui, method_name)()

    assert factory.instances == []
    assert len(gui.edit_frame_container.winfo_children()) == 1


def test_edit_special_income(monkeypatch):
    gui = _make_gui()
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "SpecialIncomeEditFrame", factory)

    gui.edit_special_income()

    frame = factory.instances[0]
    assert frame.kwargs["special_income_streams"] is gui.special_income_streams
    assert frame.kwargs["second_person_enabled"] is True
    assert frame.kwargs["title"] == "Special Income"


def test_edit_roth(monkeypatch):
    gui = _make_gui()
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "RothEditFrame", factory)

    gui.edit_roth()

    frame = factory.instances[0]
    assert frame.kwargs["roth_flows"] is gui.roth_flows
    assert frame.kwargs["second_person_enabled"] is True


def test_edit_expenses(monkeypatch):
    gui = _make_gui()
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "ExpensesEditFrame", factory)

    gui.edit_expenses()

    frame = factory.instances[0]
    assert frame.kwargs["expensesDict"] is gui.expensesDict
    assert frame.kwargs["title"] == "Expenses"


def test_edit_taxes(monkeypatch):
    gui = _make_gui()
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "TaxesEditFrame", factory)

    gui.edit_taxes()

    frame = factory.instances[0]
    assert frame.kwargs["control_vars"] == {"_controls_dict": gui.simulation_controls}
    assert frame.kwargs["title"] == "Taxes"


@pytest.mark.parametrize("second_person", [False, True])
def test_edit_portfolio_data(monkeypatch, second_person):
    gui = _make_gui(second_person=second_person)
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "PortfolioDollarsEditFrame", factory)

    gui.edit_portfolio_data()

    frame = factory.instances[0]
    assert frame.kwargs["husband_portfolio"] is gui.husband_portfolio
    assert frame.kwargs["wife_portfolio"] is (gui.wife_portfolio if second_person else None)
    assert frame.kwargs["mode"] == "Advanced"


def test_edit_real_estate(monkeypatch):
    gui = _make_gui()
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "RealEstateEditFrame", factory)

    gui.edit_real_estate()

    frame = factory.instances[0]
    assert frame.kwargs["husband_portfolio"] is gui.husband_portfolio
    assert frame.kwargs["wife_portfolio"] is gui.wife_portfolio


def test_edit_derived_statistics(monkeypatch):
    gui = _make_gui()
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "DerivedStatisticsFrame", factory)

    gui.edit_derived_statistics()

    frame = factory.instances[0]
    assert frame.kwargs["husband_portfolio"] is gui.husband_portfolio
    assert frame.kwargs["wife_portfolio"] is gui.wife_portfolio


def test_edit_retirement_controls(monkeypatch):
    gui = _make_gui()
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "RetirementEditFrame", factory)

    gui.edit_retirement_controls()

    frame = factory.instances[0]
    assert frame.kwargs["main_gui"] is gui
    assert frame.kwargs["control_vars"] == {"_controls_dict": gui.simulation_controls}
    assert frame.kwargs["persons"] == {"husband": gui.husband, "wife": gui.wife}
    assert frame.kwargs["portfolio"] == {
        "husband": gui.husband_portfolio,
        "wife": gui.wife_portfolio,
    }
    assert gui.retirement_editor_frame is frame


def test_edit_simulation_assumptions(monkeypatch):
    gui = _make_gui()
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "HistoricalEditFrame", factory)

    gui.edit_simulation_assumptions()

    frame = factory.instances[0]
    assert frame.kwargs["historical_data"] is gui
    assert frame.kwargs["title"] == "Assumptions"


def test_edit_simulation_settings(monkeypatch):
    gui = _make_gui()
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "PortfolioSimulationEditFrame", factory)

    gui.edit_simulation_settings()

    frame = factory.instances[0]
    assert frame.kwargs["sim_vars"] == {"_settings_dict": gui.simulation_settings}


def test_edit_simulation_controls(monkeypatch):
    gui = _make_gui()
    factory = FrameFactory()
    monkeypatch.setattr(gui_editors, "SimulationControlsEditFrame", factory)

    gui.edit_simulation_controls()

    frame = factory.instances[0]
    assert frame.kwargs["control_vars"] == {"_controls_dict": gui.simulation_controls}
    assert gui.simulation_controls_editor_frame is frame