from pathlib import Path
from unittest.mock import Mock

import pytest
import os

from src.warpsimlab.gui import gui_notes as mod


@pytest.mark.parametrize("platform,launcher", [("win32", "startfile"), ("darwin", "open"), ("linux", "xdg-open")])
@pytest.mark.parametrize("frozen", [False, True])
def test_pdf_path_and_platform_launcher(monkeypatch, tmp_path, platform, launcher, frozen):
    startfile = Mock()
    run = Mock()
    monkeypatch.setattr(mod.sys, "platform", platform)
    monkeypatch.setattr(mod.sys, "frozen", frozen, raising=False)
    if frozen:
        monkeypatch.setattr(mod.sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(mod.os, "startfile", startfile, raising=False)
    monkeypatch.setattr(mod.subprocess, "run", run)
    mod.NotesFrame._open_pdf(None, "faq.pdf")
    base = tmp_path if frozen else Path(mod.__file__).resolve().parent.parent

    expected = os.path.normcase(str(base / "docs" / "faq.pdf"))

    if launcher == "startfile":
        startfile.assert_called_once()
        actual = startfile.call_args.args[0]
        assert os.path.normcase(actual) == expected
        run.assert_not_called()
    else:
        run.assert_called_once()
        actual_command = run.call_args.args[0]
        assert actual_command[0] == launcher
        assert len(actual_command) == 2
        assert os.path.normcase(actual_command[1]) == expected
        assert run.call_args.kwargs == {"check": False}