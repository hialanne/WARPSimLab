import tkinter as tk
from tkinter import messagebox

import pytest


@pytest.fixture
def tk_root():
    """Use real Tk widgets, keeping the test window hidden."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk unavailable: {exc}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def validation_errors(monkeypatch):
    errors = []
    monkeypatch.setattr(messagebox, "showerror", lambda *args, **kwargs: errors.append(args))
    return errors
