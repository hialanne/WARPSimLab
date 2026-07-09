# test_tooltip.py

from __future__ import annotations

import tkinter as tk
import pytest

from src.warpsimlab.utils.tooltip import Tooltip


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk not available")
    root.withdraw()
    yield root
    root.destroy()


def test_tooltip_initialization(tk_root):
    btn = tk.Button(tk_root)

    tip = Tooltip(btn, "test text")

    assert tip.widget is btn
    assert tip.text == "test text"
    assert tip.tipwindow is None


def test_tooltip_show_and_hide(tk_root):
    btn = tk.Button(tk_root)

    tip = Tooltip(btn, "text", delay=0)

    tip.show()

    assert tip.tipwindow is not None

    tip.hide()

    assert tip.tipwindow is None