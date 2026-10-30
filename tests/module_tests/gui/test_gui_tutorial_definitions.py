from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.warpsimlab.gui import gui_tutorial_definitions as mod


@pytest.mark.parametrize("builder", [mod.build_basic_tutorial_steps, mod.build_advanced_building_tutorial_steps, mod.build_advanced_analysis_tutorial_steps])
def test_tutorial_steps_have_callable_navigation_and_live_mode_gate(builder):
    # Restrict the stand-in to actual GUI methods used by these definitions.
    from src.warpsimlab.gui.gui_init import PortfolioSimulatorGUI
    gui = Mock(spec=PortfolioSimulatorGUI)
    mode = ["Basic"]
    gui.mode_var = SimpleNamespace(get=lambda: mode[0])
    steps = builder(gui)
    assert steps
    for step in steps:
        assert step["title"] and step["text"]
        assert callable(step["screen_callback"])
        if "can_advance" in step:
            assert step["can_advance"]() is False
            mode[0] = "Advanced"
            assert step["can_advance"]() is True
            mode[0] = "Basic"
    # Builders must return fresh mutable step dictionaries.
    again = builder(gui)
    assert all(a is not b for a, b in zip(steps, again))
