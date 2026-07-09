from __future__ import annotations

import pytest


class _ModeVar:
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value


@pytest.fixture
def dummy_gui():
    from src.warpsimlab.gui import gui_run as mod

    class DummyGUI(mod.PortfolioSimulatorGUI_RunMixin):
        pass

    inst = DummyGUI()

    inst.husband = object()
    inst.wife = object()
    inst.husband_portfolio = object()
    inst.wife_portfolio = object()
    inst.expensesDict = object()
    inst.simulation_controls = {"enable_second_person": True}
    inst.mode_var = type("_ModeVar", (), {"get": lambda self: "Advanced"})()

    return inst


@pytest.mark.parametrize(
    "sim_type",
    [
        "cashflow_sim",
        "operating_balance_sim",
        "portfolio_sim",
        "summary_sim",
    ],
)
def test_run_simulation_from_gui(monkeypatch, dummy_gui, sim_type):
    from src.warpsimlab.gui import gui_run as mod

    called = {}

    def fake_run_simulation(**kwargs):
        called["kwargs"] = kwargs

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "commit_pending_gui_edits",
        lambda self: None,
    )

    monkeypatch.setattr(mod, "run_simulation", fake_run_simulation)

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "_person_for_sim",
        lambda self, p: f"PERSON_{id(p)}",
    )

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "_portfolio_for_sim",
        lambda self, p: f"PORT_{id(p)}",
    )

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "build_simulation_from_gui",
        lambda self, sim_type=None: f"SIMCFG_{sim_type}",
    )

    mod.PortfolioSimulatorGUI_RunMixin.run_simulation_from_gui(dummy_gui, sim_type=sim_type)

    assert "kwargs" in called
    assert called["kwargs"]["sim_config"] == f"SIMCFG_{sim_type}"
    assert called["kwargs"]["expenses"] is dummy_gui.expensesDict
    assert called["kwargs"]["husband"] == f"PERSON_{id(dummy_gui.husband)}"
    assert called["kwargs"]["wife"] == f"PERSON_{id(dummy_gui.wife)}"


def test_run_simulation_without_second_person(monkeypatch, dummy_gui):
    from src.warpsimlab.gui import gui_run as mod

    dummy_gui.simulation_controls["enable_second_person"] = False

    called = {}

    def fake_run_simulation(**kwargs):
        called["kwargs"] = kwargs

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "commit_pending_gui_edits",
        lambda self: None,
    )

    monkeypatch.setattr(mod, "run_simulation", fake_run_simulation)

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "_person_for_sim",
        lambda self, p: f"PERSON_{id(p)}",
    )

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "_portfolio_for_sim",
        lambda self, p: f"PORT_{id(p)}",
    )

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "build_simulation_from_gui",
        lambda self, sim_type=None: f"SIMCFG_{sim_type}",
    )

    mod.PortfolioSimulatorGUI_RunMixin.run_simulation_from_gui(dummy_gui, sim_type="cashflow_sim")

    assert called["kwargs"]["wife"] is None
    assert called["kwargs"]["wife_portfolio"] is None