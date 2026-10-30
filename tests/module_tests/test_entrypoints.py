from pathlib import Path
import runpy
from unittest.mock import Mock

import pytest


ROOT = Path(__file__).resolve().parents[2]


def test_launcher_initializes_gui_and_enters_event_loop(monkeypatch):
    import tkinter
    from src.warpsimlab.gui import gui_init
    root = Mock()
    gui = Mock()
    monkeypatch.setattr(tkinter, "Tk", Mock(return_value=root))
    monkeypatch.setattr(gui_init, "PortfolioSimulatorGUI", gui)
    runpy.run_path(str(ROOT / "WARPSimLab.py"), run_name="__main__")
    gui.assert_called_once_with(root)
    root.mainloop.assert_called_once()


@pytest.mark.parametrize("content,expected", [("x = 1\n\t# comment\n", "No suspicious special characters found."),
    ("# caf\u00e9\n", "sample.py:1:6: U+00E9")])
def test_character_checker_scans_isolated_python_files(tmp_path, monkeypatch, capsys, content, expected):
    (tmp_path / "sample.py").write_text(content, encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("\u00e9", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    runpy.run_path(str(ROOT / "tools" / "checkForIllegalCharacters.py"), run_name="__main__")
    assert expected in capsys.readouterr().out
