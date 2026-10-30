from types import SimpleNamespace
from unittest.mock import Mock

import tkinter as tk

from src.warpsimlab.gui.gui_guidedTutorial import GuidedTutorialController


def test_tutorial_navigation_validation_toggle_and_exit(tk_root):
    parent = SimpleNamespace(root=tk_root, edit_tutorial=Mock(), edit_frame_container=tk.Frame(tk_root))
    controller = GuidedTutorialController(parent)
    first, second = Mock(), Mock()
    allowed = [False]
    steps = [{"title": "First", "text": "First instructions", "screen_callback": first,
              "can_advance": lambda: allowed[0], "validation_message": "Review inputs"},
             {"title": "Second", "text": "Second instructions", "screen_callback": second}]
    controller.start("Empty", [])
    assert controller.active is False
    controller.start("Guide", steps)
    assert controller.active
    assert controller.steps is not steps
    assert controller.instruction_panel.winfo_exists()
    controller.previous_step()
    assert controller.current_step_index == 0
    controller.next_step()
    assert controller.current_step_index == 0
    assert controller.validation_message == "Review inputs"
    allowed[0] = True
    controller.refresh_current_step()
    assert controller.validation_message == ""
    controller.next_step()
    assert controller.current_step_index == 1
    second.assert_called_once()
    controller.toggle_instructions()
    assert controller.instruction_panel is None
    assert controller.control_bar.winfo_exists()
    controller.toggle_instructions()
    assert controller.instruction_panel.winfo_exists()
    controller.previous_step()
    assert controller.current_step_index == 0
    controller.next_step()
    controller.next_step()
    assert controller.active is False
    assert controller.steps == []
    parent.edit_tutorial.assert_called_once()
    calls = first.call_count + second.call_count
    controller.next_step()
    controller.previous_step()
    controller.refresh_current_step()
    controller.toggle_instructions()
    assert first.call_count + second.call_count == calls
