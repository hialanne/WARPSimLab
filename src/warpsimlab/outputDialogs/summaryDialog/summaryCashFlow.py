# summaryCashFlow.py

from tkinter import ttk


def build_cash_flow_tab(dialog, notebook):
    cash_flow_tab = ttk.Frame(notebook, padding=15)
    notebook.add(cash_flow_tab, text="Cash Flow")

    header_font = dialog._report_header_font
    body_font = dialog._report_body_font
    body_font_bold = dialog._report_body_bold_font
    column_label_font = dialog._report_body_font
    column_label_bold_font = dialog._report_body_bold_font

    r = dialog.results
    column_indices = dialog._get_display_indices()
    dialog._add_year_headers(cash_flow_tab, column_indices, header_font)


    def fmt(value):
        return f"${value:,.0f}"


    def fmt_pct(value):
        if value is None:
            return "N/A"
        return f"{value * 100:.0f}%"


    def negative_color(value):
        if value < 0:
            return "red"
        return None

    row_idx = 1


    def add_row(label, key, bold=False, color_fn=None):
        nonlocal row_idx

        if bold:
            label_font = column_label_bold_font
            value_font = body_font_bold
        else:
            label_font = column_label_font
            value_font = body_font

        ttk.Label(cash_flow_tab, text=label, font=label_font, anchor="w").grid(
            row=row_idx, column=0, padx=20, pady=1, sticky="w"
        )

        for col_offset, idx in enumerate(column_indices, start=1):
            value = r[key][idx]
            label_args = {"text": fmt(value), "font": value_font}

            if color_fn:
                color = color_fn(value)
                if color:
                    label_args["foreground"] = color

            ttk.Label(cash_flow_tab, **label_args).grid(
                row=row_idx, column=col_offset, padx=20, pady=1, sticky="w"
            )

        row_idx += 1


    def add_separator():
        nonlocal row_idx

        ttk.Separator(cash_flow_tab, orient="horizontal").grid(
            row=row_idx, column=0, columnspan=5, sticky="ew", pady=3
        )
        row_idx += 1


    add_row("Gross Income", "gross_income", bold=True)
    add_row("Employee 401(k) / IRA", "employee_401k_contributions")
    add_row("Employee HSA Contribution", "hsa_employee_contributions")
    add_row("Taxes", "taxes")

    ttk.Label(cash_flow_tab, text="Tax Bracket", font=column_label_font, anchor="w").grid(
        row=row_idx, column=0, padx=20, pady=1, sticky="w"
    )

    for col_offset, idx in enumerate(column_indices, start=1):
        value = r["tax_bracket"][idx]
        ttk.Label(cash_flow_tab, text=fmt_pct(value), font=body_font).grid(
            row=row_idx, column=col_offset, padx=20, pady=1, sticky="w"
        )

    row_idx += 1
    add_separator()

    add_row("Net Income", "net_income", bold=True)
    add_row("Employer HSA Contribution", "hsa_employer_contributions")
    add_row("Roth IRA Contributions", "roth_ira_contributions")
    add_row("Workplace Roth Contributions", "roth_workplace_contributions")
    add_row("Qualified HSA Withdrawal", "hsa_qualified_withdrawals")
    add_row("Taxable HSA Withdrawal", "hsa_taxable_withdrawals")

    if dialog.sim_config.always_use_expense_mode:
        add_row("Household Expenses", "expenses")
        add_separator()
        add_row("Net Cash Flow", "net_cash_flow", bold=True, color_fn=negative_color)

    add_row("Fund Expenses", "fund_expenses", bold=True)

    if dialog.sim_config.always_use_expense_mode:
        note_text = (
            "Net Income is Gross Income after modeled taxes and employee traditional 401k and HSA contributions.\n"
            "Net Cash Flow also reflects household expenses, Roth contributions, and HSA funding flows.\n"
            "Fund expenses are removed directly from the portfolio and are shown for reference."
        )
    else:
        note_text = (
            "Gross Income and Net Income include modeled retirement withdrawal cash and taxable HSA withdrawals "
            "where applicable.\n"
            "Roth contributions are after-tax cash uses; qualified HSA withdrawals are tax-free funding for "
            "modeled eligible expenses.\n"
            "Fund expenses are removed directly from the portfolio and are shown for reference."
        )

    ttk.Label(cash_flow_tab, text=note_text, font=body_font, justify="left").grid(
        row=row_idx, column=0, columnspan=5, sticky="w", pady=(15, 10)
    )

    return cash_flow_tab