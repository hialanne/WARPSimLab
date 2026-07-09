# test_gui_main.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk

import pytest


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    root.withdraw()
    yield root
    root.destroy()


class DummyBtn:
    def __init__(self):
        self.last_state = None
        self.calls = []

    def config(self, **kwargs):
        self.calls.append(kwargs)
        if "state" in kwargs:
            self.last_state = kwargs["state"]


@dataclass
class DummyParentGUI:
    # run buttons
    income_btn: DummyBtn
    operating_balance_btn: DummyBtn
    portfolio_balance_btn: DummyBtn
    summary_btn: DummyBtn
    temp_overrides_btn: DummyBtn
    # nav buttons
    edit_person_data_button: DummyBtn
    edit_expenses_taxes_button: DummyBtn
    edit_portfolio_button: DummyBtn
    edit_market_sim_button: DummyBtn
    edit_retirement_button: DummyBtn
    edit_simulation_controls_button: DummyBtn
    edit_tutorial_button: DummyBtn

    apply_temp_called: int = 0
    apply_opbal_called: int = 0
    legal_accepted: bool = False

    def _apply_mode_to_temp_overrides_button(self):
        self.apply_temp_called += 1

    def _apply_mode_to_operating_balance_button(self):
        self.apply_opbal_called += 1

    def _apply_mode_to_results_button(self):
        state = "normal" if self.legal_accepted else "disabled"
        for btn in [
            self.income_btn,
            self.operating_balance_btn,
            self.portfolio_balance_btn,
            self.summary_btn,
            self.temp_overrides_btn,
        ]:
            btn.config(state=state)

    def _apply_mode_to_top_buttons(self):
        state = "normal" if self.legal_accepted else "disabled"
        for btn in [
            self.edit_person_data_button,
            self.edit_expenses_taxes_button,
            self.edit_portfolio_button,
            self.edit_market_sim_button,
            self.edit_retirement_button,
            self.edit_simulation_controls_button,
            self.edit_tutorial_button,
        ]:
            btn.config(state=state)


@pytest.fixture
def parent_gui():
    return DummyParentGUI(
        income_btn=DummyBtn(),
        operating_balance_btn=DummyBtn(),
        portfolio_balance_btn=DummyBtn(),
        summary_btn=DummyBtn(),
        temp_overrides_btn=DummyBtn(),
        edit_person_data_button=DummyBtn(),
        edit_expenses_taxes_button=DummyBtn(),
        edit_portfolio_button=DummyBtn(),
        edit_market_sim_button=DummyBtn(),
        edit_retirement_button=DummyBtn(),
        edit_simulation_controls_button=DummyBtn(),
        edit_tutorial_button=DummyBtn(),
    )


def test_init_disables_buttons_when_parent_gui_present(tk_root, parent_gui, monkeypatch):
    from src.warpsimlab.gui import gui_main as mod

    # Ensure init does not immediately "restore acceptance"
    monkeypatch.setattr(mod.MainHomeFrame, "_legal_acceptance_exists", lambda self: False, raising=True)

    frame = mod.MainHomeFrame(tk_root, parent_gui=parent_gui)
    frame.pack()

    # Disabled at build-time
    for btn in [
        parent_gui.income_btn,
        parent_gui.operating_balance_btn,
        parent_gui.portfolio_balance_btn,
        parent_gui.summary_btn,
        parent_gui.temp_overrides_btn,
        parent_gui.edit_person_data_button,
        parent_gui.edit_expenses_taxes_button,
        parent_gui.edit_portfolio_button,
        parent_gui.edit_market_sim_button,
        parent_gui.edit_retirement_button,
        parent_gui.edit_simulation_controls_button,
        parent_gui.edit_tutorial_button,
    ]:
        assert btn.last_state == "disabled"


def test_on_agree_changed_enables_then_disables_buttons(tk_root, parent_gui, monkeypatch):
    from src.warpsimlab.gui import gui_main as mod

    monkeypatch.setattr(mod.MainHomeFrame, "_legal_acceptance_exists", lambda self: False, raising=True)

    # Don’t touch filesystem in this test
    recorded = {"called": 0}
    monkeypatch.setattr(
        mod.MainHomeFrame,
        "_record_legal_acceptance_once",
        lambda self: recorded.__setitem__("called", recorded["called"] + 1),
        raising=True,
    )

    frame = mod.MainHomeFrame(tk_root, parent_gui=parent_gui)
    frame.pack()

    # Toggle to True
    frame.agree_var.set(True)
    frame._on_agree_changed()

    assert recorded["called"] == 1
    for btn in [
        parent_gui.income_btn,
        parent_gui.operating_balance_btn,
        parent_gui.portfolio_balance_btn,
        parent_gui.summary_btn,
        parent_gui.temp_overrides_btn,
        parent_gui.edit_person_data_button,
        parent_gui.edit_expenses_taxes_button,
        parent_gui.edit_portfolio_button,
        parent_gui.edit_market_sim_button,
        parent_gui.edit_retirement_button,
        parent_gui.edit_simulation_controls_button,
        parent_gui.edit_tutorial_button,
    ]:
        assert btn.last_state == "normal"


    # Toggle to False
    frame.agree_var.set(False)
    frame._on_agree_changed()

    for btn in [
        parent_gui.income_btn,
        parent_gui.operating_balance_btn,
        parent_gui.portfolio_balance_btn,
        parent_gui.summary_btn,
        parent_gui.temp_overrides_btn,
        parent_gui.edit_person_data_button,
        parent_gui.edit_expenses_taxes_button,
        parent_gui.edit_portfolio_button,
        parent_gui.edit_market_sim_button,
        parent_gui.edit_retirement_button,
        parent_gui.edit_simulation_controls_button,
        parent_gui.edit_tutorial_button,
    ]:
        assert btn.last_state == "disabled"


def test_init_restores_prior_acceptance_if_log_exists(tk_root, parent_gui, monkeypatch):
    from src.warpsimlab.gui import gui_main as mod

    monkeypatch.setattr(mod.MainHomeFrame, "_legal_acceptance_exists", lambda self: True, raising=True)

    frame = mod.MainHomeFrame(tk_root, parent_gui=parent_gui)
    frame.pack()

    assert frame.agree_var.get() is True

    # Should have enabled buttons due to restore path
    assert parent_gui.income_btn.last_state == "normal"
    assert parent_gui.edit_person_data_button.last_state == "normal"


def test_record_legal_acceptance_once_writes_file(tmp_path, monkeypatch):
    from src.warpsimlab.gui import gui_main as mod

    # Patch Path.home() -> tmp_path, so it writes under tmp_path/Desktop/WARPSimLab
    monkeypatch.setattr(mod.Path, "home", lambda: tmp_path, raising=True)

    # Make timestamp deterministic
    class DummyDT:
        @staticmethod
        def now():
            class _X:
                def strftime(self, fmt):
                    return "2000-01-02 03:04:05"
            return _X()

    monkeypatch.setattr(mod, "datetime", DummyDT, raising=True)
    monkeypatch.setattr(mod.getpass, "getuser", lambda: "tester", raising=True)

    # Construct a frame without building widgets; we only need the method
    inst = mod.MainHomeFrame.__new__(mod.MainHomeFrame)

    inst._record_legal_acceptance_once()

    log_file = tmp_path / "Desktop" / "WARPSimLab Data" / "legal_acceptance.log"
    assert log_file.exists()

    content = log_file.read_text(encoding="utf-8")
    assert "WARPSimLab Legal Acceptance Record" in content
    assert "Accepted on: 2000-01-02 03:04:05" in content
    assert "OS User: tester" in content


def test_record_legal_acceptance_once_does_not_overwrite_if_exists(tmp_path, monkeypatch):
    from src.warpsimlab.gui import gui_main as mod

    monkeypatch.setattr(mod.Path, "home", lambda: tmp_path, raising=True)

    log_file = tmp_path / "Desktop" / "WARPSimLab Data" / "legal_acceptance.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("PREEXISTING", encoding="utf-8")

    inst = mod.MainHomeFrame.__new__(mod.MainHomeFrame)
    inst._record_legal_acceptance_once()

    assert log_file.read_text(encoding="utf-8") == "PREEXISTING"


def test_record_legal_acceptance_once_swallows_exceptions(monkeypatch):
    from src.warpsimlab.gui import gui_main as mod

    # Force Path.home() to raise, which should be swallowed
    monkeypatch.setattr(mod.Path, "home", lambda: (_ for _ in ()).throw(RuntimeError("boom")), raising=True)

    inst = mod.MainHomeFrame.__new__(mod.MainHomeFrame)

    # Should not raise
    inst._record_legal_acceptance_once()


def test_legal_acceptance_exists_true_false(tmp_path, monkeypatch):
    from src.warpsimlab.gui import gui_main as mod

    monkeypatch.setattr(mod.Path, "home", lambda: tmp_path, raising=True)

    inst = mod.MainHomeFrame.__new__(mod.MainHomeFrame)

    # No file yet
    assert inst._legal_acceptance_exists() is False

    # Create file
    log_file = tmp_path / "Desktop" / "WARPSimLab Data" / "legal_acceptance.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("x", encoding="utf-8")

    assert inst._legal_acceptance_exists() is True