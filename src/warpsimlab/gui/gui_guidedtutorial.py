import tkinter as tk
from tkinter import ttk


class GuidedTutorialController:
    """
    Controls a guided sequence of existing simulator screens.

    Each tutorial step is a dictionary containing:
        title
        text
        screen_callback

    The controller does not copy, reset, or restore financial data.
    """

    INSTRUCTION_PANEL_WIDTH = 330
    INSTRUCTION_WRAP_LENGTH = 280

    def __init__(self, parent_gui):
        self.parent_gui = parent_gui

        self.tutorial_title = ""
        self.steps = []
        self.current_step_index = 0
        self.active = False

        self.control_bar = None
        self.instruction_panel = None
        self.instructions_visible = True
        self.validation_message = ""

    def start(self, tutorial_title, steps):
        """
        Start a tutorial at its first step.
        """
        if not steps:
            return

        self.tutorial_title = tutorial_title
        self.steps = list(steps)

        self.current_step_index = 0
        self.active = True
        self.instructions_visible = True
        self.validation_message = ""

        self._show_current_step()

    def next_step(self):
        """
        Move to the next tutorial step.

        A step may provide an optional can_advance callback. If it returns
        False, remain on the current step and display its validation message.
        """
        if not self.active:
            return

        step = self.steps[self.current_step_index]
        can_advance = step.get("can_advance")

        if can_advance is not None and not can_advance():
            self.validation_message = step.get(
                "validation_message",
                "Complete the required action before continuing.",
            )
            self._show_current_step()
            return

        self.validation_message = ""

        if self.current_step_index >= len(self.steps) - 1:
            self.exit_tutorial()
            return

        self.current_step_index += 1
        self._show_current_step()


    def previous_step(self):
        """
        Move to the previous tutorial step.
        """
        if not self.active:
            return

        if self.current_step_index <= 0:
            return

        self.validation_message = ""
        self.current_step_index -= 1
        self._show_current_step()


    def refresh_current_step(self):
        """
        Rebuild the current tutorial step.

        This is used when an existing simulator screen rebuilds itself,
        such as when the mode or second-person setting changes.
        """
        if not self.active:
            return

        step = self.steps[self.current_step_index]
        can_advance = step.get("can_advance")

        if can_advance is not None and can_advance():
            self.validation_message = ""

        self._show_current_step()


    def toggle_instructions(self):
        """
        Show or hide the right-side tutorial instruction panel.

        The compact navigation bar remains visible in both states.
        """
        if not self.active:
            return

        self.instructions_visible = not self.instructions_visible
        self._show_current_step()


    def exit_tutorial(self):
        """
        End the tutorial and return to the Tutorials screen.
        """
        self.active = False
        self.tutorial_title = ""
        self.steps = []
        self.current_step_index = 0

        self.control_bar = None
        self.instruction_panel = None
        self.instructions_visible = True
        self.validation_message = ""

        self.parent_gui.edit_tutorial()


    def _show_current_step(self):
        """
        Open the normal simulator screen for the current step and then
        arrange the tutorial controls around that screen.
        """
        if not self.active:
            return

        if (
            self.control_bar is not None
            and self.control_bar.winfo_exists()
        ):
            self.control_bar.destroy()

        if (
            self.instruction_panel is not None
            and self.instruction_panel.winfo_exists()
        ):
            self.instruction_panel.destroy()

        self.control_bar = None
        self.instruction_panel = None

        step = self.steps[self.current_step_index]
        screen_callback = step["screen_callback"]

        screen_callback()
        self._build_tutorial_layout(step)


    def _build_tutorial_layout(self, step):
        """
        Build a compact control bar and an optional fixed-width
        instruction panel over the right side of the simulator screen.

        The simulator screen keeps the full available width. Hiding the
        instructions reveals the portion covered by the overlay.
        """
        container = self.parent_gui.edit_frame_container
        screen_widgets = list(container.winfo_children())

        for widget in screen_widgets:
            widget.pack_forget()
            widget.grid_forget()
            widget.place_forget()

        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=0)
        container.rowconfigure(0, weight=0)
        container.rowconfigure(1, weight=1, minsize=500)

        self._build_control_bar(container)

        for widget in screen_widgets:
            widget.grid(
                row=1,
                column=0,
                columnspan=2,
                sticky="nsew",
                padx=10,
                pady=5,
            )

        if self.instructions_visible:
            self._build_instruction_panel(container, step)


    def _build_control_bar(self, container):
        """
        Build the compact tutorial navigation bar.

        Grid is used inside the bar so the title remains fixed on the left
        while the button group remains fixed on the right.
        """
        step_number = self.current_step_index + 1
        step_count = len(self.steps)

        self.control_bar = tk.Frame(
            container,
            background="#dbeaf5",
            borderwidth=1,
            relief="solid",
        )

        self.control_bar.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=10,
            pady=(5, 3),
        )

        self.control_bar.columnconfigure(0, weight=1)
        self.control_bar.columnconfigure(1, weight=0)

        title_text = (
            f"{self.tutorial_title} - "
            f"Step {step_number} of {step_count}"
        )

        tk.Label(
            self.control_bar,
            text=title_text,
            font=("Arial", 13, "bold"),
            background="#dbeaf5",
            anchor="w",
            justify="left",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=10,
            pady=6,
        )

        button_frame = tk.Frame(
            self.control_bar,
            background="#dbeaf5",
        )
        button_frame.grid(
            row=0,
            column=1,
            sticky="e",
            padx=8,
            pady=4,
        )

        back_button = ttk.Button(
            button_frame,
            text="Back",
            command=self.previous_step,
        )
        back_button.pack(side="left", padx=(0, 6))

        if self.current_step_index == 0:
            back_button.state(["disabled"])

        if self.current_step_index == len(self.steps) - 1:
            next_button_text = "Finish"
        else:
            next_button_text = "Next"

        ttk.Button(
            button_frame,
            text=next_button_text,
            command=self.next_step,
        ).pack(side="left", padx=(0, 6))

        if self.instructions_visible:
            instruction_button_text = "Hide Instructions"
        else:
            instruction_button_text = "Show Instructions"

        ttk.Button(
            button_frame,
            text=instruction_button_text,
            command=self.toggle_instructions,
            width=17,
        ).pack(side="left", padx=(0, 6))

        ttk.Button(
            button_frame,
            text="Exit Tutorial",
            command=self.exit_tutorial,
        ).pack(side="left")


    def _build_instruction_panel(self, container, step):
        """
        Build a fixed-width instruction panel over the right side of the
        simulator screen.
        """
        container.update_idletasks()

        control_bar_height = self.control_bar.winfo_reqheight()
        top_offset = control_bar_height + 8
        bottom_margin = 10

        self.instruction_panel = tk.Frame(
            container,
            background="#f4f7f9",
            borderwidth=1,
            relief="solid",
        )

        self.instruction_panel.place(
            relx=1.0,
            x=-10,
            y=top_offset,
            anchor="ne",
            width=self.INSTRUCTION_PANEL_WIDTH,
            relheight=1.0,
            height=-(top_offset + bottom_margin),
        )

        tk.Label(
            self.instruction_panel,
            text=step["title"],
            font=("Arial", 16, "bold"),
            background="#f4f7f9",
            justify="left",
            anchor="w",
            wraplength=self.INSTRUCTION_WRAP_LENGTH,
        ).pack(
            anchor="w",
            fill="x",
            padx=14,
            pady=(14, 8),
        )

        tk.Label(
            self.instruction_panel,
            text=step.get("section_title", "What to do"),
            font=("Arial", 12, "bold"),
            background="#f4f7f9",
            justify="left",
            anchor="w",
        ).pack(
            anchor="w",
            fill="x",
            padx=14,
            pady=(4, 6),
        )

        tk.Label(
            self.instruction_panel,
            text=step["text"],
            font=("Arial", 12),
            background="#f4f7f9",
            justify="left",
            anchor="nw",
            wraplength=self.INSTRUCTION_WRAP_LENGTH,
        ).pack(
            anchor="nw",
            fill="x",
            padx=14,
            pady=(0, 10),
        )

        if self.validation_message:
            tk.Label(
                self.instruction_panel,
                text=self.validation_message,
                font=("Arial", 12, "bold"),
                background="#f4f7f9",
                foreground="#8b0000",
                justify="left",
                anchor="w",
                wraplength=self.INSTRUCTION_WRAP_LENGTH,
            ).pack(
                anchor="w",
                fill="x",
                padx=14,
                pady=(2, 14),
            )

        self.instruction_panel.lift()

