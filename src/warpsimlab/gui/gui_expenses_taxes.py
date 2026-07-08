# gui_expenses_taxes.py

from tkinter import ttk

from src.warpsimlab.gui.gui_expenses import ExpensesEditFrame
from src.warpsimlab.gui.gui_taxes import TaxesEditFrame

class _StrCgetSeparator(ttk.Separator):
    def cget(self, key):
        return str(super().cget(key))

class ExpensesTaxesFrame(ttk.Frame):
    """
    Combined screen:
      - Expenses on the left
      - Taxes on the right
    """
    '''
    Basic mode banner (Expenses-only view)

    Household spending inputs. Add recurring or time-bounded expenses that the simulator subtracts each year during the run.

    Advanced mode banner (Expenses + Taxes split view)

    Household spending and tax assumptions. Expenses define annual cash outflows. Taxes configure how the simulator estimates income taxes during the run.

    These are descriptive, non-advisory, and explain purpose.


    Best so far:
    Defines household expenses and tax assumptions used in the simulation.
    '''

    def __init__(self, parent, expensesDict, control_vars, title="Expenses & Taxes", mode="Basic", **kwargs):
        super().__init__(parent, padding=10, **kwargs)

        self.mode = mode

        ttk.Label(
            self,
            text="Defines household expenses and tax assumptions used in the simulation.",
            font=("Arial", 11),
            wraplength=600,
            justify="left",
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        if self.mode == "Basic":
            left_container = ttk.Frame(self)
            left_container.grid(row=1, column=0, sticky="nsew")

            # Make it resize properly
            self.grid_rowconfigure(1, weight=1)
            self.grid_columnconfigure(0, weight=1)

            expenses_frame = ExpensesEditFrame(
                left_container,
                expensesDict=expensesDict,
                title="Expenses"
            )
            expenses_frame.grid(row=0, column=0, sticky="nsew")

            left_container.grid_rowconfigure(0, weight=1)
            left_container.grid_columnconfigure(0, weight=1)
            return
    


        # Layout: left | separator | right
        left_container = ttk.Frame(self)
        sep = _StrCgetSeparator(self, orient="vertical")
        right_container = ttk.Frame(self)

        left_container.grid(row=1, column=0, sticky="nsew")
        sep.grid(row=1, column=1, sticky="ns", padx=10)
        right_container.grid(row=1, column=2, sticky="nsew")

        # Make both sides resize reasonably
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=3)  # Expenses typically wider
        self.grid_columnconfigure(2, weight=2)  # Taxes typically narrower

        # Instantiate existing frames largely unchanged
        expenses_frame = ExpensesEditFrame(
            left_container,
            expensesDict=expensesDict,
            title="Expenses"
        )
        expenses_frame.grid(row=0, column=0, sticky="nsew")

        taxes_frame = TaxesEditFrame(
            right_container,
            control_vars=control_vars,
            title="Taxes"
        )
        taxes_frame.grid(row=0, column=0, sticky="nsew")

        # Let child containers expand
        left_container.grid_rowconfigure(0, weight=1)
        left_container.grid_columnconfigure(0, weight=1)

        right_container.grid_rowconfigure(0, weight=1)
        right_container.grid_columnconfigure(0, weight=1)