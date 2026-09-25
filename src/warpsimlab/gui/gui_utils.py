# gui_utils.py

import tkinter as tk


def noop():
    return


def bind_entry_commit_on_return(entry):
    """
    Make Enter run an Entry's configured validation without moving focus.
    """
    def _commit(_event):
        entry.tk.call(entry._w, "validate")
        return "break"

    entry.bind("<Return>", _commit)


def set_tk_button_soft_disabled(btn: tk.Button, enabled: bool, real_command, noop_command=noop):
    def command_after_dismiss(command):
        def wrapped_command():
            dismiss_active_popup(btn)
            return command()

        return wrapped_command

    default_fg = btn.option_get("foreground", "Foreground")
    default_active_fg = btn.option_get("activeForeground", "Foreground")

    if not hasattr(btn, "_warpsimlab_default_fg"):
        btn._warpsimlab_default_fg = btn.cget("fg")
        btn._warpsimlab_default_active_fg = btn.cget("activeforeground")

    if enabled:
        btn.configure(
            state="normal",
            fg=btn._warpsimlab_default_fg,
            activeforeground=btn._warpsimlab_default_active_fg,
            cursor="",
            command=command_after_dismiss(real_command),
            relief="raised",
        )
    else:
        btn.configure(
            state="normal",
            fg="gray60",
            activeforeground="gray60",
            cursor="arrow",
            command=command_after_dismiss(noop_command),
            relief="flat",
        )


def dismiss_active_popup(widget):
    toplevel = widget.winfo_toplevel()
    menu = getattr(toplevel, "_warpsimlab_active_popup_menu", None)

    if menu is None:
        return

    try:
        menu.unpost()
    except tk.TclError:
        pass

    toplevel._warpsimlab_active_popup_menu = None


def popup_menu_below_widget(widget, menu: tk.Menu):
    """
    Popup a tk.Menu directly below a widget.
    """
    dismiss_active_popup(widget)

    toplevel = widget.winfo_toplevel()
    toplevel._warpsimlab_active_popup_menu = menu

    x = widget.winfo_rootx()
    y = widget.winfo_rooty() + widget.winfo_height()

    try:
        menu.tk_popup(x, y)
    finally:
        menu.grab_release()


def create_dropdown_button(parent, text: str, menu_labels_and_commands, command=None, **grid_kwargs):
    """
    Create a tk.Button that opens a dropdown tk.Menu.

    Parameters
    ----------
    parent : widget
        Parent container.
    text : str
        Button label.
    menu_labels_and_commands : iterable[tuple[str, callable]]
        Sequence of (menu_label, callback).
    command : callable | None
        Optional explicit button command. If omitted, a default popup command is created.
    **grid_kwargs
        Passed to .grid() if provided.

    Returns
    -------
    (button, menu, popup_command)
        button : tk.Button
        menu : tk.Menu
        popup_command : callable
            The command used to show the popup menu.
    """
    button = tk.Button(parent, text=text)
    menu = tk.Menu(button, tearoff=0)

    for label, callback in menu_labels_and_commands:
        menu.add_command(label=label, command=callback)

    def popup_command():
        popup_menu_below_widget(button, menu)

    button.configure(command=command or popup_command)

    if grid_kwargs:
        button.grid(**grid_kwargs)

    return button, menu, popup_command


def create_top_button(parent, text: str, command, grid_kwargs=None, **button_kwargs):
    """
    Create a standard top navigation tk.Button and optionally grid it.

    Parameters
    ----------
    parent : widget
        Parent container.
    text : str
        Button label.
    command : callable
        Button callback.
    grid_kwargs : dict | None
        Optional keyword arguments passed to .grid().
    **button_kwargs
        Additional keyword arguments passed to tk.Button.

    Returns
    -------
    button : tk.Button
    """
    button = tk.Button(parent, text=text, command=command, **button_kwargs)

    if grid_kwargs:
        button.grid(**grid_kwargs)

    return button

