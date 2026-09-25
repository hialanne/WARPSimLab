# gui_historicalData.py

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox

from src.warpsimlab.gui.gui_validation import mark_validation_failed, parse_finite_float
from src.warpsimlab.utils.tooltip import Tooltip
from src.warpsimlab.gui.gui_scaling import ScalableFrameMixin


def load_market_data(selection):
    # Lazy import to avoid circular import at module load time
    from src.warpsimlab.gui.gui_init import load_market_data as _load_market_data
    return _load_market_data(selection)


class HistoricalEditFrame(ScalableFrameMixin, ttk.Frame):
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

        self._body_font = tkfont.nametofont("TkDefaultFont").copy()
        self._header_font = tkfont.Font(root=self, family="Arial", size=11, weight="bold")
        self._header_text_font = tkfont.Font(root=self, family="Arial", size=11)
        self._section_font = tkfont.Font(root=self, family="Arial", size=12, weight="bold")
        self._tooltip_font = tkfont.Font(root=self, family="Arial", size=11)

        self._initialize_frame_scaling()
        self._register_scalable_font(self._body_font)
        self._register_scalable_font(self._header_font)
        self._register_scalable_font(self._header_text_font)
        self._register_scalable_font(self._section_font)
        self._register_scalable_font(self._tooltip_font)
        self._apply_gui_scale()

        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        ttk.Label(
            header_frame, text="Simulation > Assumptions", font=self._header_font
        ).pack(side="left")

        ttk.Label(
            header_frame,
            text=(
                " - Configure historical return, volatility, inflation, "
                "and market dataset assumptions used by the simulation."
            ),
            font=self._header_text_font,
        ).pack(side="left")

        self.left_frame = ttk.Frame(self)
        self.left_frame.grid(row=1, column=0, sticky="nw", padx=(0, 20))

        sep = ttk.Separator(self, orient="vertical")
        sep.grid(row=1, column=1, sticky="ns", padx=5, pady=0)

        self.right_frame = ttk.Frame(self)
        self.right_frame.grid(row=1, column=2, sticky="nw")

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

        self._build_numeric_fields()
        self._build_market_data_selection()


    def _apply_scaled_styles(self):
        style = ttk.Style(self)
        style.configure("HistoricalData.TRadiobutton", font=self._body_font)


    # ------------------------------------------------
    # Initialize temporary StringVars
    # ------------------------------------------------
    def _init_vars(self):
        d = self.data

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

        self.historical_market_var.trace_add(
            "write",
            lambda *_: setattr(d, "historical_market", self.historical_market_var.get())
        )


    # ------------------------------------------------
    # Build numeric input fields (left frame)
    # ------------------------------------------------
    def _build_numeric_fields(self):
        fields = [
            ("Stock Yearly Gains %", "eq_mean_var"),
            ("Bond Yearly Gains %", "bd_mean_var"),
            ("Cash Yearly Gains %", "cs_mean_var"),
            ("Real Estate Yearly Gains %", "re_mean_var"),
            ("Stock STD %", "eq_std_var"),
            ("Bond STD %", "bd_std_var"),
            ("Cash STD %", "cs_std_var"),
            ("Real Estate STD %", "re_std_var"),
            ("Inflation Rate %", "inflation_var"),
        ]

        for row, (label_text, var_name) in enumerate(fields):
            var = getattr(self, var_name)

            ttk.Label(
                self.left_frame, text=label_text, font=self._body_font
            ).grid(row=row, column=0, sticky="w", pady=2)

            vcmd = (
                self.register(self._validate_historical_field_on_focusout),
                "%P",
                var_name,
            )

            entry = ttk.Entry(
                self.left_frame, textvariable=var, width=14, font=self._body_font,
                validate="focusout", validatecommand=vcmd
            )
            entry.grid(row=row, column=1, sticky="w", pady=2)

            Tooltip(entry, self.entry_tooltips[var_name], font=self._tooltip_font)


    # ------------------------------------------------
    # Build Historical Market Data selection (right frame)
    # ------------------------------------------------
    def _build_market_data_selection(self):
        ttk.Label(
            self.right_frame, text="Historical Market Data", font=self._section_font
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        datasets = [
            ("25 Year Data", "25_year_data"),
            ("50 Year Data", "50_year_data"),
            ("100 Year Data", "100_year_data"),
            ("Depression (1929-1940)", "depression"),
            ("Irrational Exuberance (1990-2000)", "irrational_exuberance"),
        ]

        for row, (text, value) in enumerate(datasets, start=1):
            rb = ttk.Radiobutton(
                self.right_frame,
                text=text,
                variable=self.historical_market_var,
                value=value,
                command=self.update_market_fields,
                style="HistoricalData.TRadiobutton"
            )
            rb.grid(row=row, column=0, sticky="w", pady=2)

            Tooltip(
                rb, f"Select historical market dataset: {text}",
                font=self._tooltip_font
            )


    def _parse_historical_field(self, field_name, raw_value):
        minimum = None

        if field_name in {"eq_std", "bd_std", "cs_std", "re_std"}:
            minimum = 0

        return parse_finite_float(raw_value, minimum=minimum)


    def _historical_field_label(self, field_name):
        labels = {
            "eq_mean": "Stock Yearly Gains",
            "bd_mean": "Bond Yearly Gains",
            "cs_mean": "Cash Yearly Gains",
            "re_mean": "Real Estate Yearly Gains",
            "eq_std": "Stock STD",
            "bd_std": "Bond STD",
            "cs_std": "Cash STD",
            "re_std": "Real Estate STD",
            "inflation": "Inflation Rate",
        }
        return labels.get(field_name, field_name)


    def _format_historical_field(self, value):
        return f"{value:.2f}".rstrip("0").rstrip(".")


    def _validate_historical_field_on_focusout(self, proposed_value, var_name):
        var = getattr(self, var_name)
        field_name = var_name.replace("_var", "")
        current_value = getattr(self.data, field_name)

        try:
            parsed = self._parse_historical_field(field_name, proposed_value)
            setattr(self.data, field_name, parsed)
            self.after_idle(lambda: var.set(self._format_historical_field(parsed)))
            return True

        except ValueError as exc:
            self.after_idle(lambda: var.set(self._format_historical_field(current_value)))
            mark_validation_failed(self)
            messagebox.showerror(
                "Invalid Input",
                f"Historical Data / {self._historical_field_label(field_name)}: {exc}",
                parent=self.winfo_toplevel(),
            )
            return True


    def update_market_fields(self):
        selection = self.historical_market_var.get()
        market_values = load_market_data(selection)

        self.data.eq_mean = market_values["eq_mean"]
        self.data.bd_mean = market_values["bd_mean"]
        self.data.cs_mean = market_values["cs_mean"]
        self.data.re_mean = market_values["re_mean"]

        self.data.eq_std = market_values["eq_std"]
        self.data.bd_std = market_values["bd_std"]
        self.data.cs_std = market_values["cs_std"]
        self.data.re_std = market_values["re_std"]

        self.data.inflation = market_values["inflation"]

        self.eq_mean_var.set(self._format_historical_field(self.data.eq_mean))
        self.bd_mean_var.set(self._format_historical_field(self.data.bd_mean))
        self.cs_mean_var.set(self._format_historical_field(self.data.cs_mean))
        self.re_mean_var.set(self._format_historical_field(self.data.re_mean))

        self.eq_std_var.set(self._format_historical_field(self.data.eq_std))
        self.bd_std_var.set(self._format_historical_field(self.data.bd_std))
        self.cs_std_var.set(self._format_historical_field(self.data.cs_std))
        self.re_std_var.set(self._format_historical_field(self.data.re_std))

        self.inflation_var.set(self._format_historical_field(self.data.inflation))