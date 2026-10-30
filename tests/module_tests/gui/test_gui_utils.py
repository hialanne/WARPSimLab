from types import SimpleNamespace
from unittest.mock import Mock

import tkinter as tk

from src.warpsimlab.gui import gui_utils as mod


def test_return_commits_validation_without_moving_focus():
    entry = Mock()
    entry._w = ".entry"
    mod.bind_entry_commit_on_return(entry)
    event, callback = entry.bind.call_args.args
    assert event == "<Return>"
    assert callback(None) == "break"
    entry.tk.call.assert_called_once_with(".entry", "validate")


def test_popup_position_replaces_previous_and_handles_destroyed_menu():
    previous = Mock()
    previous.unpost.side_effect = tk.TclError("destroyed")
    root = SimpleNamespace(_warpsimlab_active_popup_menu=previous)
    widget = Mock()
    widget.winfo_toplevel.return_value = root
    widget.winfo_rootx.return_value = 10
    widget.winfo_rooty.return_value = 20
    widget.winfo_height.return_value = 30
    menu = Mock()
    mod.popup_menu_below_widget(widget, menu)
    previous.unpost.assert_called_once()
    menu.tk_popup.assert_called_once_with(10, 50)
    assert root._warpsimlab_active_popup_menu is menu
    mod.dismiss_active_popup(widget)
    menu.unpost.assert_called_once()
    assert root._warpsimlab_active_popup_menu is None
    mod.dismiss_active_popup(widget)


def test_soft_disable_and_reenable_preserve_colors_and_dismiss_popup(tk_root):
    button = tk.Button(tk_root, fg="navy", activeforeground="blue")
    real, noop = Mock(), Mock()
    menu = Mock()
    tk_root._warpsimlab_active_popup_menu = menu
    mod.set_tk_button_soft_disabled(button, False, real, noop)
    button.invoke()
    noop.assert_called_once()
    real.assert_not_called()
    menu.unpost.assert_called_once()
    assert button.cget("fg") == "gray60"
    mod.set_tk_button_soft_disabled(button, True, real)
    button.invoke()
    real.assert_called_once()
    assert button.cget("fg") == "navy"
    assert button.cget("activeforeground") == "blue"


def test_button_factories_wire_commands_and_grid(tk_root):
    action = Mock()
    button, menu, popup = mod.create_dropdown_button(tk_root, "Menu", [("Run", action)], command=action, row=2)
    assert int(button.grid_info()["row"]) == 2
    assert menu.entrycget(0, "label") == "Run"
    button.invoke()
    menu.invoke(0)
    assert action.call_count == 2
    assert callable(popup)
    top = mod.create_top_button(tk_root, "Run", action, grid_kwargs={"row": 3})
    top.invoke()
    assert action.call_count == 3
    assert int(top.grid_info()["row"]) == 3
