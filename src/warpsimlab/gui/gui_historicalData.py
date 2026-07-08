# gui_historicalData.py

import tkinter as tk
from tkinter import ttk

from src.warpsimlab.utils.tooltip import Tooltip

def load_market_data(selection):
    # Lazy import to avoid circular import at module load time
    from src.warpsimlab.gui.gui_init import load_market_data as _load_market_data
    return _load_market_data(selection)

class HistoricalEditFrame(ttk.Frame):
    """
    Frame to edit historical market assumptions
    (mean returns, standard deviations, inflation, and selected dataset).

    Numeric fields are backed by StringVars that immediately update the
    provided historical_data object via trace bindings. There is no
    separate save step - changes propagate in real time.

    The layout displays:
        - Numeric assumption inputs on the left
        - Historical dataset selection on the right
    """
    def __init__(self, parent, historical_data, title="Historical Data"):
        super().__init__(parent, padding=10)
        self.data = historical_data

        # --- Top title ---
        if title:
            ttk.Label(self, text=title, font=("Arial", 12, "bold")).grid(
                row=0, column=0, columnspan=2, sticky="w", pady=(0, 10)
            )

        # --- Frames for side-by-side layout ---
        self.left_frame = ttk.Frame(self)
        self.left_frame.grid(row=1, column=0, sticky="nw", padx=(0, 20))

        # Vertical separator
        sep = ttk.Separator(self, orient="vertical")
        sep.grid(row=1, column=1, sticky="ns", padx=5, pady=0)

        self.right_frame = ttk.Frame(self)
        self.right_frame.grid(row=1, column=2, sticky="nw")

        # --- Initialize StringVars ---
        self._init_vars()

        self.entry_tooltips = {
            "eq_mean_var": "Historical average yearly return for stocks over the chosen timespan",
            "bd_mean_var": "Historical average yearly return for bonds over the chosen timespan",
            "cs_mean_var": "Historical average yearly return for cash over the chosen timespan",
            "re_mean_var": "Historical average yearly return for real estate over the chosen timespan",
            "eq_std_var": "Historical standard deviation (volatility) for stocks over the chosen timespan",
            "bd_std_var": "Historical standard deviation (volatility) for bonds over the chosen timespan",
            "cs_std_var": "Historical standard deviation (volatility) for cash over the chosen timespan",
            "re_std_var": "Historical standard deviation (volatility) for real estate over the chosen timespan",
            "inflation_var": "Historical average yearly inflation rate over the chosen timespan",
        }

        # --- Build left side: numeric inputs ---
        self._build_numeric_fields()

        # --- Build right side: Historical Market Data ---
        self._build_market_data_selection()



    # ------------------------------------------------
    # Initialize temporary StringVars
    # ------------------------------------------------
    def _init_vars(self):
        d = self.data
        # Numeric variables
        self.eq_mean_var = tk.StringVar(value=str(d.eq_mean))
        self.bd_mean_var = tk.StringVar(value=str(d.bd_mean))
        self.cs_mean_var = tk.StringVar(value=str(d.cs_mean))
        self.re_mean_var = tk.StringVar(value=str(d.re_mean))

        self.eq_std_var = tk.StringVar(value=str(d.eq_std))
        self.bd_std_var = tk.StringVar(value=str(d.bd_std))
        self.cs_std_var = tk.StringVar(value=str(d.cs_std))
        self.re_std_var = tk.StringVar(value=str(d.re_std))

        self.inflation_var = tk.StringVar(value=str(d.inflation))
        self.historical_market_var = tk.StringVar(value=d.historical_market)

        # Bind historical market selection
        self.historical_market_var.trace_add(
            "write",
            lambda *_: setattr(d, "historical_market", self.historical_market_var.get())
        )

    # ------------------------------------------------
    # Build numeric input fields (left frame)
    # ------------------------------------------------
    def _build_numeric_fields(self):
        for row, (label_text, var_name) in enumerate([
            ("Stock Yearly Gains %", "eq_mean_var"),
            ("Bond Yearly Gains %", "bd_mean_var"),
            ("Cash Yearly Gains %", "cs_mean_var"),
            ("Real Estate Yearly Gains %", "re_mean_var"),
            ("Stock STD %", "eq_std_var"),
            ("Bond STD %", "bd_std_var"),
            ("Cash STD %", "cs_std_var"),
            ("Real Estate STD %", "re_std_var"),
            ("Inflation Rate %", "inflation_var"),
        ]):
            var = getattr(self, var_name)
            ttk.Label(self.left_frame, text=label_text).grid(row=row, column=0, sticky="w", pady=2)

            vcmd = (
                self.register(self._validate_historical_field_on_focusout),
                "%P",
                var_name,
            )

            entry = ttk.Entry(
                self.left_frame,
                textvariable=var,
                width=14,
                validate="focusout",
                validatecommand=vcmd,
            )

            entry.grid(row=row, column=1, sticky="w", pady=2)

            # Add tooltip
            Tooltip(entry, self.entry_tooltips[var_name], 
                    font=("Arial", 11))


    # ------------------------------------------------
    # Build Historical Market Data selection (right frame)
    # ------------------------------------------------
    def _build_market_data_selection(self):
        ttk.Label(self.right_frame, text="Historical Market Data", font=("Arial", 12, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )

        datasets = [
            ("25 Year Data", "25_year_data"),
            ("50 Year Data", "50_year_data"),
            ("100 Year Data", "100_year_data"),
            ("Depression (1929-1940)", "depression"),
            ("Irrational Exuberance (1990-2000)", "irrational_exuberance")
        ]

        for row, (text, value) in enumerate(datasets, start=1):
            rb = ttk.Radiobutton(
                self.right_frame,
                text=text,
                variable=self.historical_market_var,
                value=value,
                command=self.update_market_fields
            )
            rb.grid(row=row, column=0, sticky="w", pady=2)

            Tooltip(rb, f"Select historical market dataset: {text}", 
                    font=("Arial", 11))


    def _parse_historical_field(self, raw_value):
        text = raw_value.strip()

        if text == "":
            raise ValueError("Blank value")

        if text in {"-", "+", ".", "-.", "+."}:
            raise ValueError("Invalid number")

        value = float(text)

        return value


    def _format_historical_field(self, value):
        return f"{value:.2f}".rstrip("0").rstrip(".")


    def _validate_historical_field_on_focusout(self, proposed_value, var_name):
        var = getattr(self, var_name)
        field_name = var_name.replace("_var", "")
        current_value = getattr(self.data, field_name)

        try:
            parsed = self._parse_historical_field(proposed_value)
            setattr(self.data, field_name, parsed)
            self.after_idle(lambda: var.set(self._format_historical_field(parsed)))
            return True
        except ValueError:
            self.after_idle(lambda: var.set(self._format_historical_field(current_value)))
            self.bell()
            return True


    def update_market_fields(self):
        selection = self.historical_market_var.get()
        market_values = load_market_data(selection)

        # Write to backing data model first
        self.data.eq_mean = market_values["eq_mean"]
        self.data.bd_mean = market_values["bd_mean"]
        self.data.cs_mean = market_values["cs_mean"]
        self.data.re_mean = market_values["re_mean"]

        self.data.eq_std = market_values["eq_std"]
        self.data.bd_std = market_values["bd_std"]
        self.data.cs_std = market_values["cs_std"]
        self.data.re_std = market_values["re_std"]

        self.data.inflation = market_values["inflation"]

        # Then refresh visible vars
        self.eq_mean_var.set(self._format_historical_field(self.data.eq_mean))
        self.bd_mean_var.set(self._format_historical_field(self.data.bd_mean))
        self.cs_mean_var.set(self._format_historical_field(self.data.cs_mean))
        self.re_mean_var.set(self._format_historical_field(self.data.re_mean))

        self.eq_std_var.set(self._format_historical_field(self.data.eq_std))
        self.bd_std_var.set(self._format_historical_field(self.data.bd_std))
        self.cs_std_var.set(self._format_historical_field(self.data.cs_std))
        self.re_std_var.set(self._format_historical_field(self.data.re_std))

        self.inflation_var.set(self._format_historical_field(self.data.inflation))
