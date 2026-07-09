
import tkinter as tk

from src.warpsimlab.gui.gui_init import PortfolioSimulatorGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = PortfolioSimulatorGUI(root)
    root.mainloop()
