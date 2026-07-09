# test_gui_tutorial.py

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk unavailable: {e}")
    root.withdraw()
    yield root
    root.destroy()


def _iter_descendants(widget):
    """Yield all descendants of a widget (depth-first)."""
    for child in widget.winfo_children():
        yield child
        yield from _iter_descendants(child)


def test_frame_builds_successfully(tk_root):
    from src.warpsimlab.gui import gui_tutorial as mod

    frame = mod.TutorialFrame(tk_root)
    frame.pack()

    assert frame.title == "Tutorials"
    assert len(frame.winfo_children()) > 0


def test_buttons_created(tk_root):
    """
    The TutorialFrame nests buttons several levels deep. The prior test only
    checked grandchildren, which misses the buttons.
    """
    from src.warpsimlab.gui import gui_tutorial as mod

    frame = mod.TutorialFrame(tk_root)
    frame.pack()

    # Robust: search the full widget tree and look specifically for ttk.Button.
    found_button = any(isinstance(w, ttk.Button) for w in _iter_descendants(frame))
    assert found_button


def test_open_pdf_windows(monkeypatch):
    from src.warpsimlab.gui import gui_tutorial as mod

    called = {}

    monkeypatch.setattr(mod.sys, "platform", "win32")

    def fake_startfile(path):
        called["path"] = path

    monkeypatch.setattr(mod.os, "startfile", fake_startfile, raising=False)

    frame = mod.TutorialFrame(None)
    frame._open_pdf("test.pdf")

    assert called["path"].endswith("docs\\test.pdf") or called["path"].endswith("docs/test.pdf")


def test_open_pdf_mac(monkeypatch):
    from src.warpsimlab.gui import gui_tutorial as mod

    called = {}

    monkeypatch.setattr(mod.sys, "platform", "darwin")

    def fake_run(cmd, check=False):
        called["cmd"] = cmd

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    frame = mod.TutorialFrame(None)
    frame._open_pdf("file.pdf")

    assert called["cmd"][0] == "open"


def test_open_pdf_linux(monkeypatch):
    from src.warpsimlab.gui import gui_tutorial as mod

    called = {}

    monkeypatch.setattr(mod.sys, "platform", "linux")

    def fake_run(cmd, check=False):
        called["cmd"] = cmd

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    frame = mod.TutorialFrame(None)
    frame._open_pdf("file.pdf")

    assert called["cmd"][0] == "xdg-open"