# gui_utils.py

import tkinter as tk


def noop():
    return


def set_tk_button_soft_disabled(btn: tk.Button, enabled: bool, real_command, noop_command=noop):
    """
    Keep tk.Button appearance while simulating a disabled state.

    Why this exists:
    - tk.Button with state='disabled' often does not render the exact look desired
    - this keeps the widget visually present while neutralizing clicks

    Parameters
    ----------
    btn : tk.Button
        The button to update.
    enabled : bool
        True to enable the real command, False to gray it out and disable behavior.
    real_command : callable
        The command to run when enabled.
    noop_command : callable
        Fallback command when disabled.
    """
    if enabled:
        btn.configure(
            state="normal",
            fg="black",
            activeforeground="black",
            cursor="",
            command=real_command,
            relief="raised",
        )
    else:
        btn.configure(
            state="normal",
            fg="gray60",
            activeforeground="gray60",
            cursor="arrow",
            command=noop_command,
            relief="flat",
        )


def popup_menu_below_widget(widget, menu: tk.Menu):
    """
    Popup a tk.Menu directly below a widget.
    """
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

