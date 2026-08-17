import tkinter as tk


def center_plot_window_on_main(fig, sim_config):
    """
    Center a standalone Matplotlib window over the main WARPSimLab window.
    """
    root = getattr(sim_config, "root", None)
    manager = getattr(fig.canvas, "manager", None)
    window = getattr(manager, "window", None)

    if root is None or window is None:
        return

    try:
        root.update_idletasks()
        window.update_idletasks()

        width = window.winfo_width()
        height = window.winfo_height()

        x = (
            root.winfo_rootx()
            + (root.winfo_width() - width) // 2
        )
        y = (
            root.winfo_rooty()
            + (root.winfo_height() - height) // 2
        )

        window.geometry(
            f"+{x}+{y}"
        )
    except (tk.TclError, AttributeError):
        pass