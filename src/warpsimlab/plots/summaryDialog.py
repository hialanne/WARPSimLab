import numpy as np
import tkinter as tk
from tkinter import ttk


class SummaryDialog(tk.Toplevel):
    def __init__(
        self,
        results,
        husband,
        wife,
        sim_config,
        title="Simulation Summary"
    ):
        super().__init__(sim_config.root)

        self.results = results
        self.husband = husband
        self.wife = wife
        self.sim_config = sim_config

        width = 1100
        height = 800
        self.geometry(f"{width}x{height}")

        self.title(title)
        self._build_ui()

    def _build_ui(self):
        title_font = ("Arial", 17, "bold")
        tab_font_bold = ("Arial", 14, "bold")
        tab_font_reg = ("Arial", 14, "normal")

        style = ttk.Style(self)

        style.configure(
            "TNotebook.Tab",
            font=tab_font_reg,
            padding=[20, 5],
            background="#f0f0f0"
        )
        style.configure(
            "TNotebook",
            tabposition="n"
        )
        style.map(
            "TNotebook.Tab",
            font=[("selected", tab_font_bold)],
            padding=[("selected", [40, 0])],
            foreground=[("selected", "darkblue")],
            background=[("selected", "white")]
        )

        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Simulation Summary",
            font=title_font,
            anchor="center",
            justify="center"
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, 15)
        )

        notebook = ttk.Notebook(container)
        notebook.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="nsew"
        )

        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(1, weight=1)

        self._build_portfolio_tab(notebook)
        self._build_income_tab(notebook)
        self._build_cash_flow_tab(notebook)
        self._build_summary_tab(notebook)

        ttk.Button(
            container,
            text="Close",
            command=self.destroy
        ).grid(
            row=2,
            column=0,
            columnspan=2,
            pady=(20, 0)
        )

    def _get_display_indices(self):
        r = self.results

        year_start_index = 1
        year_end_index = len(r["year"]) - 1

        if self.sim_config.second_person_enabled:
            last_retirement_index = max(
                self.husband.retire_age - self.husband.age,
                self.wife.retire_age - self.wife.age
            )
        else:
            last_retirement_index = (
                self.husband.retire_age - self.husband.age
            )

        last_retirement_index = min(
            max(last_retirement_index, 1),
            year_end_index
        )

        before_retirement_index = max(
            last_retirement_index - 1,
            1
        )

        after_retirement_index = min(
            last_retirement_index + 1,
            year_end_index
        )

        return [
            year_start_index,
            before_retirement_index,
            after_retirement_index,
            year_end_index
        ]

    def _add_year_headers(
        self,
        tab,
        column_indices,
        header_font
    ):
        r = self.results

        start_year = int(r["year"][column_indices[0]])
        before_year = int(r["year"][column_indices[1]])
        after_year = int(r["year"][column_indices[2]])
        end_year = int(r["year"][column_indices[3]])

        column_headers = [
            "",
            f"Start\nSimulation\n({start_year})",
            f"Year Before\nRetirement\n({before_year})",
            f"Year After\nRetirement\n({after_year})",
            f"End\nSimulation\n({end_year})"
        ]

        for col, header in enumerate(column_headers):
            ttk.Label(
                tab,
                text=header,
                font=header_font,
                anchor="center"
            ).grid(
                row=0,
                column=col,
                padx=20,
                pady=5,
                sticky="nsew"
            )

            tab.columnconfigure(col, weight=0)

    def _build_portfolio_tab(self, notebook):
        portfolio_tab = ttk.Frame(notebook, padding=15)
        notebook.add(portfolio_tab, text="Portfolio")

        header_font = ("Arial", 14, "bold")
        body_font = ("Courier New", 12)
        body_total_font = ("Courier New", 12, "bold")

        fmt = lambda x: f"${x:,.0f}"
        r = self.results

        if self.sim_config.second_person_enabled:
            last_retirement_index = max(
                self.husband.retire_age - self.husband.age,
                self.wife.retire_age - self.wife.age
            )
        else:
            last_retirement_index = (
                self.husband.retire_age - self.husband.age
            )

        last_retirement_index = min(
            max(last_retirement_index, 0),
            len(r["year"]) - 1
        )

        p_left = ttk.Frame(portfolio_tab, padding=10)
        p_left.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        p_middle = ttk.Frame(portfolio_tab, padding=10)
        p_middle.grid(
            row=1,
            column=1,
            sticky="nsew"
        )

        p_right = ttk.Frame(portfolio_tab, padding=10)
        p_right.grid(
            row=1,
            column=2,
            sticky="nsew"
        )

        portfolio_tab.columnconfigure(0, weight=1)
        portfolio_tab.columnconfigure(1, weight=1)
        portfolio_tab.columnconfigure(2, weight=1)

        def add_portfolio_section(
            frame,
            year_idx,
            title=None
        ):
            if title:
                ttk.Label(
                    frame,
                    text=title,
                    font=header_font
                ).pack(
                    anchor="w",
                    pady=(0, 8)
                )

            year = int(r["year"][year_idx])

            ttk.Label(
                frame,
                text=f"Portfolio Value in {year}",
                font=header_font
            ).pack(anchor="w")

            ttk.Label(
                frame,
                text="",
                font=body_font
            ).pack(anchor="w")

            ttk.Label(
                frame,
                text=(
                    f"Pre-Tax Assets:   "
                    f"{fmt(r['pre_tax_assets'][year_idx])}"
                ),
                font=body_font
            ).pack(anchor="w")

            ttk.Label(
                frame,
                text=(
                    f"Post-Tax Assets:  "
                    f"{fmt(r['post_tax_assets'][year_idx])}"
                ),
                font=body_font
            ).pack(anchor="w")

            roth_assets = r.get(
                "roth_assets",
                np.zeros_like(r["pre_tax_assets"])
            )

            hsa_assets = r.get(
                "hsa_assets",
                np.zeros_like(r["pre_tax_assets"])
            )

            ttk.Label(
                frame,
                text=(
                    f"Roth Assets:      "
                    f"{fmt(roth_assets[year_idx])}"
                ),
                font=body_font
            ).pack(anchor="w")

            ttk.Label(
                frame,
                text=(
                    f"HSA Assets:       "
                    f"{fmt(hsa_assets[year_idx])}"
                ),
                font=body_font
            ).pack(anchor="w")

            ttk.Separator(
                frame,
                orient="horizontal"
            ).pack(
                fill="x",
                pady=4
            )

            total_portfolio = (
                r["pre_tax_assets"][year_idx]
                + r["post_tax_assets"][year_idx]
                + roth_assets[year_idx]
                + hsa_assets[year_idx]
            )

            color = (
                "red"
                if total_portfolio == 0
                else "black"
            )

            ttk.Label(
                frame,
                text=(
                    f"Total Portfolio:  "
                    f"{fmt(total_portfolio)}"
                ),
                font=body_total_font,
                foreground=color
            ).pack(anchor="w")

            ttk.Label(
                frame,
                text="",
                font=body_font
            ).pack(anchor="w")

            ttk.Label(
                frame,
                text=(
                    f"Real Estate:      "
                    f"{fmt(r['real_estate'][year_idx])}"
                ),
                font=body_font
            ).pack(anchor="w")

            ttk.Separator(
                frame,
                orient="horizontal"
            ).pack(
                fill="x",
                pady=4
            )

            color = (
                "red"
                if r["total_assets"][year_idx] == 0
                else "black"
            )

            ttk.Label(
                frame,
                text=(
                    f"Total Assets:     "
                    f"{fmt(r['total_assets'][year_idx])}"
                ),
                font=body_total_font,
                foreground=color
            ).pack(anchor="w")

            ttk.Separator(
                frame,
                orient="horizontal"
            ).pack(
                fill="x",
                pady=4
            )

        add_portfolio_section(
            p_left,
            0,
            "Start of Simulation"
        )

        if 0 <= last_retirement_index < len(r["year"]):
            add_portfolio_section(
                p_middle,
                last_retirement_index,
                "Retirement"
            )

        add_portfolio_section(
            p_right,
            -1,
            "End of Simulation"
        )

        summary_frame = ttk.Frame(portfolio_tab)
        summary_frame.grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(40, 0)
        )

        ttk.Label(
            summary_frame,
            text=(
                "There are four tabs: Portfolio, Income, Cash Flow, "
                "and Summary.\n\n"
                "If enabled, the portfolio sustained fund expenses "
                "throughout the full simulation period.\n"
                "Assets are shown in real (inflation-adjusted) or "
                "nominal terms,\n"
                "depending on the simulation settings.\n"
                "Retirement year is the later of the husband's or "
                "wife's, if applicable."
            ),
            font=body_font,
            foreground="darkblue",
            justify="left"
        ).pack(anchor="w")

        return portfolio_tab

    def _build_income_tab(self, notebook):
        income_tab = ttk.Frame(notebook, padding=15)
        notebook.add(income_tab, text="Income")

        header_font = ("Arial", 14, "bold")
        body_font = ("Courier New", 12)
        body_font_bold = ("Courier New", 12, "bold")
        column_label_font = ("Courier New", 14)
        column_label_bold_font = ("Courier New", 14, "bold")

        r = self.results
        column_indices = self._get_display_indices()

        self._add_year_headers(
            income_tab,
            column_indices,
            header_font
        )

        fmt = lambda x: f"${x:,.0f}"
        row_idx = 1

        def add_row(
            label,
            key,
            bold=False,
            color_fn=None
        ):
            nonlocal row_idx

            ttk.Label(
                income_tab,
                text=label,
                font=(
                    column_label_bold_font
                    if bold
                    else column_label_font
                ),
                anchor="w"
            ).grid(
                row=row_idx,
                column=0,
                padx=20,
                pady=0,
                sticky="w"
            )

            value_font = (
                body_font_bold
                if bold
                else body_font
            )

            for col_offset, idx in enumerate(
                column_indices,
                start=1
            ):
                value = r[key][idx]

                color = (
                    color_fn(value)
                    if color_fn
                    else "black"
                )

                ttk.Label(
                    income_tab,
                    text=fmt(value),
                    font=value_font,
                    foreground=color
                ).grid(
                    row=row_idx,
                    column=col_offset,
                    padx=20,
                    pady=0,
                    sticky="w"
                )

            row_idx += 1

        def add_combined_row(
            label,
            keys,
            bold=False
        ):
            nonlocal row_idx

            ttk.Label(
                income_tab,
                text=label,
                font=(
                    column_label_bold_font
                    if bold
                    else column_label_font
                ),
                anchor="w"
            ).grid(
                row=row_idx,
                column=0,
                padx=20,
                pady=0,
                sticky="w"
            )

            value_font = (
                body_font_bold
                if bold
                else body_font
            )

            for col_offset, idx in enumerate(
                column_indices,
                start=1
            ):
                value = sum(
                    r[key][idx]
                    for key in keys
                )

                ttk.Label(
                    income_tab,
                    text=fmt(value),
                    font=value_font
                ).grid(
                    row=row_idx,
                    column=col_offset,
                    padx=20,
                    pady=0,
                    sticky="w"
                )

            row_idx += 1

        def add_separator():
            nonlocal row_idx

            ttk.Separator(
                income_tab,
                orient="horizontal"
            ).grid(
                row=row_idx,
                column=0,
                columnspan=5,
                sticky="ew",
                pady=6
            )

            row_idx += 1

        add_row("Wages", "wages")
        add_row("RMD", "rmd")
        add_row("Social Security", "social_security")

        add_combined_row(
            "Pensions and Annuities",
            (
                "pensions",
                "annuities"
            )
        )

        add_row(
            "Special Income",
            "special_income"
        )

        add_separator()

        add_row(
            "Bond Interest",
            "bond_interest"
        )

        add_row(
            "Cash Interest",
            "cash_interest"
        )

        add_row(
            "Qualified Dividends",
            "qualified_dividends"
        )

        add_row(
            "Portfolio Withdrawals",
            "withdrawal"
        )

        add_row(
            "Emergency Pre-Tax Withdrawal",
            "emergency_pre_tax_used"
        )

        add_separator()

        add_row(
            "Gross Income",
            "gross_income",
            bold=True
        )

        note_text = (
            "Gross Income includes all modeled income and spendable "
            "withdrawal cash before taxes.\n"
            "Employee traditional 401k contributions are added back "
            "when calculating Gross Income.\n"
            "Amounts are shown in real or nominal terms according to "
            "the simulation settings."
        )

        ttk.Label(
            income_tab,
            text=note_text,
            font=body_font,
            foreground="darkblue",
            justify="left"
        ).grid(
            row=row_idx,
            column=0,
            columnspan=5,
            sticky="w",
            pady=(15, 10)
        )

        return income_tab

    def _build_cash_flow_tab(self, notebook):
        cash_flow_tab = ttk.Frame(notebook, padding=15)
        notebook.add(cash_flow_tab, text="Cash Flow")

        header_font = ("Arial", 14, "bold")
        body_font = ("Courier New", 12)
        body_font_bold = ("Courier New", 12, "bold")
        column_label_font = ("Courier New", 14)
        column_label_bold_font = ("Courier New", 14, "bold")

        r = self.results
        column_indices = self._get_display_indices()

        self._add_year_headers(
            cash_flow_tab,
            column_indices,
            header_font
        )

        fmt = lambda x: f"${x:,.0f}"

        fmt_pct = (
            lambda x: "N/A"
            if x is None
            else f"{x * 100:.0f}%"
        )

        row_idx = 1

        def add_row(
            label,
            key,
            bold=False,
            color_fn=None
        ):
            nonlocal row_idx

            ttk.Label(
                cash_flow_tab,
                text=label,
                font=(
                    column_label_bold_font
                    if bold
                    else column_label_font
                ),
                anchor="w"
            ).grid(
                row=row_idx,
                column=0,
                padx=20,
                pady=0,
                sticky="w"
            )

            value_font = (
                body_font_bold
                if bold
                else body_font
            )

            for col_offset, idx in enumerate(
                column_indices,
                start=1
            ):
                value = r[key][idx]

                color = (
                    color_fn(value)
                    if color_fn
                    else "black"
                )

                ttk.Label(
                    cash_flow_tab,
                    text=fmt(value),
                    font=value_font,
                    foreground=color
                ).grid(
                    row=row_idx,
                    column=col_offset,
                    padx=20,
                    pady=0,
                    sticky="w"
                )

            row_idx += 1

        def add_separator():
            nonlocal row_idx

            ttk.Separator(
                cash_flow_tab,
                orient="horizontal"
            ).grid(
                row=row_idx,
                column=0,
                columnspan=5,
                sticky="ew",
                pady=6
            )

            row_idx += 1

        add_row(
            "Gross Income",
            "gross_income",
            bold=True
        )

        add_row(
            "Employee Traditional 401k ",
            "employee_401k_contributions"
        )

        add_row(
            "Taxes",
            "taxes"
        )

        ttk.Label(
            cash_flow_tab,
            text="Tax Bracket",
            font=column_label_font,
            anchor="w"
        ).grid(
            row=row_idx,
            column=0,
            padx=20,
            pady=0,
            sticky="w"
        )

        for col_offset, idx in enumerate(
            column_indices,
            start=1
        ):
            value = r["tax_bracket"][idx]

            ttk.Label(
                cash_flow_tab,
                text=fmt_pct(value),
                font=body_font
            ).grid(
                row=row_idx,
                column=col_offset,
                padx=20,
                pady=0,
                sticky="w"
            )

        row_idx += 1

        add_separator()

        add_row(
            "Net Income",
            "net_income",
            bold=True
        )

        add_row(
            "Roth IRA Contributions",
            "roth_ira_contributions"
        )

        add_row(
            "Workplace Roth Contributions",
            "roth_workplace_contributions"
        )

        if self.sim_config.always_use_expense_mode:
            add_row(
                "Household Expenses",
                "expenses"
            )

            add_separator()

            add_row(
                "Net Cash Flow",
                "net_cash_flow",
                bold=True,
                color_fn=(
                    lambda x: "red"
                    if x < 0
                    else "black"
                )
            )

        ttk.Label(
            cash_flow_tab,
            text=""
        ).grid(
            row=row_idx,
            column=0,
            columnspan=5,
            pady=6
        )

        row_idx += 1

        add_row(
            "Fund Expenses",
            "fund_expenses",
            bold=True
        )

        if self.sim_config.always_use_expense_mode:
            note_text = (
                "Net Income is Gross Income after modeled taxes and "
                "employee traditional 401k contributions.\n"
                "Net Cash Flow also reflects household expenses, Roth IRA "
                "contributions, and workplace Roth contributions.\n"
                "Fund expenses are removed directly from the portfolio "
                "and are shown for reference."
            )
        else:
            note_text = (
                "Gross Income and Net Income include modeled retirement "
                "withdrawal cash where applicable.\n"
                "Roth IRA and workplace Roth contributions are shown as "
                "after-tax cash uses.\n"
                "Fund expenses are removed directly from the portfolio "
                "and are shown for reference."
            )

        ttk.Label(
            cash_flow_tab,
            text=note_text,
            font=body_font,
            foreground="darkblue",
            justify="left"
        ).grid(
            row=row_idx,
            column=0,
            columnspan=5,
            sticky="w",
            pady=(15, 10)
        )

        return cash_flow_tab

    def _build_summary_tab(self, notebook):
        header_font = ("Arial", 14, "bold")
        body_font = ("Courier New", 12)

        fmt = lambda x: f"${x:,.0f}"

        fmt_pct = (
            lambda x: "N/A"
            if x is None
            else f"{x:.0f}%"
        )

        r = self.results

        summary_tab = ttk.Frame(
            notebook,
            padding=15
        )

        notebook.add(
            summary_tab,
            text="Summary"
        )

        totals_frame = ttk.Frame(
            summary_tab,
            padding=10
        )

        totals_frame.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        ttk.Label(
            totals_frame,
            text="Results / Simulation Sums",
            font=header_font
        ).pack(
            anchor="w",
            pady=(0, 8)
        )

        roth_assets = np.array(
            r.get(
                "roth_assets",
                np.zeros_like(r["pre_tax_assets"])
            )
        )

        hsa_assets = np.array(
            r.get(
                "hsa_assets",
                np.zeros_like(r["pre_tax_assets"])
            )
        )

        total_portfolio = (
            np.array(r["pre_tax_assets"])
            + np.array(r["post_tax_assets"])
            + roth_assets
            + hsa_assets
        )

        def add_total_label(
            label,
            value,
            color_fn=None,
            bold=False
        ):
            value_font = (
                ("Courier New", 12, "bold")
                if bold
                else body_font
            )

            color = (
                color_fn(value)
                if color_fn
                else "black"
            )

            ttk.Label(
                totals_frame,
                text=f"{label}{fmt(value)}",
                font=value_font,
                foreground=color
            ).pack(
                anchor="w",
                pady=2
            )

        add_total_label(
            "Portfolio Start:          ",
            total_portfolio[0]
        )

        add_total_label(
            "Portfolio End:            ",
            total_portfolio[-1]
        )

        add_total_label(
            "Maximum Portfolio:        ",
            np.max(total_portfolio)
        )

        add_total_label(
            "Minimum Portfolio:        ",
            np.min(total_portfolio)
        )

        ttk.Separator(
            totals_frame,
            orient="horizontal"
        ).pack(
            fill="x",
            pady=4
        )

        ttk.Label(
            totals_frame,
            text=""
        ).pack(pady=6)

        add_total_label(
            "Taxes Paid (sum):         ",
            np.sum(r["taxes"])
        )

        add_total_label(
            "Household Expenses (sum): ",
            np.sum(r["expenses"])
        )

        add_total_label(
            "Net Cash Flow (sum):      ",
            np.sum(r["net_cash_flow"]),
            color_fn=(
                lambda x: "red"
                if x < 0
                else "black"
            )
        )

        ttk.Separator(
            totals_frame,
            orient="horizontal"
        ).pack(
            fill="x",
            pady=4
        )

        ttk.Label(
            totals_frame,
            text=""
        ).pack(pady=6)

        ttk.Label(
            totals_frame,
            text=(
                f"{fmt_pct(r.get('simulated_shortfall_rate'))} "
                "of modeled scenarios resulted\n"
                "    in the portfolio falling to $0."
            ),
            font=body_font,
            foreground="black",
            justify="left"
        ).pack(
            anchor="w",
            pady=2
        )

        ttk.Label(
            totals_frame,
            text=""
        ).pack(pady=4)

        add_total_label(
            "Fund Expenses (sum):      ",
            np.sum(r["fund_expenses"])
        )

        inputs_frame = ttk.Frame(
            summary_tab,
            padding=10
        )

        inputs_frame.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        ttk.Label(
            inputs_frame,
            text="Simulation Inputs / Assumptions",
            font=header_font
        ).pack(
            anchor="w",
            pady=(0, 8)
        )

        def add_input_label(label, value):
            ttk.Label(
                inputs_frame,
                text=f"{label}{value}",
                font=body_font
            ).pack(
                anchor="w",
                pady=2
            )

        def add_empty_space(label):
            ttk.Label(
                inputs_frame,
                text=label,
                font=body_font
            ).pack(
                anchor="w",
                pady=2
            )

        add_input_label(
            "Husband Age:            ",
            self.husband.age
        )

        add_input_label(
            "Husband Retirement Age: ",
            self.husband.retire_age
        )

        if self.sim_config.second_person_enabled:
            add_input_label(
                "Wife Age:               ",
                self.wife.age
            )

            add_input_label(
                "Wife Retirement Age:    ",
                self.wife.retire_age
            )
        else:
            add_empty_space("                ")
            add_empty_space("    ")

        ttk.Separator(
            inputs_frame,
            orient="horizontal"
        ).pack(
            fill="x",
            pady=4
        )

        ttk.Label(
            inputs_frame,
            text=""
        ).pack(pady=6)

        add_input_label(
            "Stocks Yearly Gains:    ",
            f"{self.sim_config.eq_mean * 100:.2f}%"
        )

        add_input_label(
            "Bonds Yearly Gains:     ",
            f"{self.sim_config.bd_mean * 100:.2f}%"
        )

        add_input_label(
            "Cash Yearly Gains:      ",
            f"{self.sim_config.cs_mean * 100:.2f}%"
        )

        add_input_label(
            "Inflation Rate:         ",
            f"{self.sim_config.inflation_rate * 100:.2f}%"
        )

        ttk.Separator(
            inputs_frame,
            orient="horizontal"
        ).pack(
            fill="x",
            pady=4
        )

        add_input_label(
            "Fund Expense Rate:      ",
            f"{self.sim_config.fund_expense * 100:.2f}%"
        )

        ttk.Label(
            summary_tab,
            text=(
                "Values shown are outputs of the simulation based on "
                "the user's inputs and assumptions.\n"
                "All amounts are displayed in real "
                "(inflation-adjusted) or nominal terms as selected.\n"
                "Totals represent the sum of the item across the "
                "simulation period.\n\n"
            ),
            font=body_font,
            foreground="darkblue",
            justify="left"
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(20, 0)
        )

        summary_tab.columnconfigure(0, weight=1)
        summary_tab.columnconfigure(1, weight=1)

        return summary_tab