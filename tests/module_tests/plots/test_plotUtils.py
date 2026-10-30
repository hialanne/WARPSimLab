from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import tkinter as tk

from src.warpsimlab.plots.plotUtils import center_plot_window_on_main


def test_center_uses_main_window_position_and_both_sizes():
    root, window = Mock(), Mock()
    root.winfo_rootx.return_value = 100
    root.winfo_rooty.return_value = 200
    root.winfo_width.return_value = 1000
    root.winfo_height.return_value = 800
    window.winfo_width.return_value = 400
    window.winfo_height.return_value = 300
    fig = SimpleNamespace(canvas=SimpleNamespace(manager=SimpleNamespace(window=window)))
    center_plot_window_on_main(fig, SimpleNamespace(root=root))
    window.geometry.assert_called_once_with("+400+450")


@pytest.mark.parametrize("error", [tk.TclError("closed"), AttributeError("no geometry")])
def test_missing_or_destroyed_window_is_safe(error):
    fig = SimpleNamespace(canvas=SimpleNamespace(manager=None))
    center_plot_window_on_main(fig, SimpleNamespace())
    root = Mock()
    root.update_idletasks.side_effect = error
    window = Mock()
    fig.canvas.manager = SimpleNamespace(window=window)
    center_plot_window_on_main(fig, SimpleNamespace(root=root))
    window.geometry.assert_not_called()
