# summaryIncome.py

from tkinter import ttk


def build_income_tab(dialog, notebook):
    income_tab = ttk.Frame(notebook, padding=15)
    notebook.add(income_tab, text="Income")

    header_font = dialog._report_header_font
    body_font = dialog._report_body_font
    body_font_bold = dialog._report_body_bold_font
    column_label_font = dialog._report_body_font
    column_label_bold_font = dialog._report_body_bold_font

    r = dialog.results
    column_indices = dialog._get_display_indices()
    dialog._add_year_headers(income_tab, column_indices, header_font)

    def fmt(value):
        return f"${value:,.0f}"

    row_idx = 1

    def add_row(label, key, bold=False, color_fn=None):
        nonlocal row_idx

        if bold:
            label_font = column_label_bold_font
            value_font = body_font_bold
        else:
            label_font = column_label_font
            value_font = body_font

        ttk.Label(income_tab, text=label, font=label_font, anchor="w").grid(
            row=row_idx, column=0, padx=20, pady=1, sticky="w"
        )

        for col_offset, idx in enumerate(column_indices, start=1):
            value = r[key][idx]
            label_args = {"text": fmt(value), "font": value_font}

            if color_fn:
                color = color_fn(value)
                if color:
                    label_args["foreground"] = color

            ttk.Label(income_tab, **label_args).grid(
                row=row_idx, column=col_offset, padx=20, pady=1, sticky="w"
            )

        row_idx += 1

    def add_combined_row(label, keys, bold=False):
        nonlocal row_idx

        if bold:
            label_font = column_label_bold_font
            value_font = body_font_bold
        else:
            label_font = column_label_font
            value_font = body_font

        ttk.Label(income_tab, text=label, font=label_font, anchor="w").grid(
            row=row_idx, column=0, padx=20, pady=1, sticky="w"
        )

        for col_offset, idx in enumerate(column_indices, start=1):
            value = sum(r[key][idx] for key in keys)

            ttk.Label(income_tab, text=fmt(value), font=value_font).grid(
                row=row_idx, column=col_offset, padx=20, pady=1, sticky="w"
            )

        row_idx += 1

    def add_separator():
        nonlocal row_idx

        ttk.Separator(income_tab, orient="horizontal").grid(
            row=row_idx, column=0, columnspan=5, sticky="ew", pady=6
        )
        row_idx += 1

    add_combined_row("Gross Wages", ("wages", "employee_401k_contributions", "hsa_employee_contributions"))

    add_row("RMD", "rmd")
    add_row("Social Security", "social_security")
    add_combined_row("Pensions and Annuities", ("pensions", "annuities"))
    add_row("Special Income", "special_income")

    add_separator()

    add_row("Bond Interest", "bond_interest")
    add_row("Cash Interest", "cash_interest")
    add_row("Qualified Equity Distributions", "qualified_equity_distributions")
    add_row("Portfolio Withdrawals", "withdrawal")
    add_row("Emergency Pre-Tax Withdrawal", "emergency_pre_tax_used")

    add_separator()

    add_row("Gross Income", "gross_income", bold=True)

    note_text = (
        "Gross Income includes all modeled income and spendable withdrawal cash before taxes.\n"
        "Employee traditional 401k and HSA contributions are added back when calculating Gross Income.\n"
        "Amounts are shown in real or nominal terms according to the simulation settings."
    )

    ttk.Label(income_tab, text=note_text, font=body_font, justify="left").grid(
        row=row_idx, column=0, columnspan=5, sticky="w", pady=(15, 10)
    )

    return income_tab