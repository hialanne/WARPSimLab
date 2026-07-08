# tooltip.py

import tkinter as tk

class Tooltip:
    _current_tip = None  # class-level reference

    def __init__(self, widget, text, font=None, delay=500, lifetime=6000):
        self.widget = widget
        self.text = text
        self.font = font or ("TkDefaultFont", 10)
        self.delay = delay
        self.tipwindow = None
        self.id = None
        self.lifetime = lifetime
        self._auto_close_id = None

        self.widget.bind("<Enter>", self.schedule)
        self.widget.bind("<Leave>", self.hide)
        self.widget.bind("<FocusIn>", self.schedule)
        self.widget.bind("<FocusOut>", self.hide)

        self.widget.bind("<Destroy>", self.hide)

    def schedule(self, event=None):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show(self, event=None):
        if Tooltip._current_tip:
            Tooltip._current_tip.hide()
        if self.tipwindow or not self.text:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=self.font,
            wraplength=400
        )
        label.pack(ipadx=4, ipady=2)
        
        Tooltip._current_tip = self

        # Auto-close after lifetime (milliseconds)
        if self.lifetime:
            self._auto_close_id = self.widget.after(self.lifetime, self.hide)

        # bind tooltip window to hide when mouse leaves
        tw.bind("<Leave>", self.hide)


    def hide(self, event=None):
        # Cancel scheduled show
        self.unschedule()

        # Cancel auto-close timer
        if self._auto_close_id:
            try:
                self.widget.after_cancel(self._auto_close_id)
            except Exception:
                pass
            self._auto_close_id = None

        if self.tipwindow:
            try:
                self.tipwindow.destroy()
            except Exception:
                pass
            self.tipwindow = None

        if Tooltip._current_tip is self:
            Tooltip._current_tip = None