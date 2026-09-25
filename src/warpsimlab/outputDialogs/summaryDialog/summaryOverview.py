# summaryOverview.py

import numpy as np
from tkinter import ttk


def build_summary_tab(dialog, notebook):
    header_font = dialog._report_header_font
    body_font = dialog._report_body_font
    body_font_bold = dialog._report_body_bold_font

    r = dialog.results


    def fmt(value):
        return f"${value:,.0f}"


    def fmt_pct(value):
        if value is None:
            return "N/A"
        return f"{value:.0f}%"


    def funding_gap_color(value):
        if value > 0:
            return "red"
        return None


    summary_tab = ttk.Frame(notebook, padding=15)
    notebook.add(summary_tab, text="Summary")

    totals_frame = ttk.Frame(summary_tab, padding=10)
    totals_frame.grid(row=0, column=0, sticky="nsew")

    ttk.Label(totals_frame, text="Simulation Results", font=header_font).pack(anchor="w", pady=(0, 8))

    roth_assets = np.array(r.get("roth_assets", np.zeros_like(r["pre_tax_assets"])))
    hsa_assets = np.array(r.get("hsa_assets", np.zeros_like(r["pre_tax_assets"])))

    total_portfolio = (
        np.array(r["pre_tax_assets"])
        + np.array(r["post_tax_assets"])
        + roth_assets
        + hsa_assets
    )


    def add_total_label(label, value, color_fn=None, bold=False):
        if bold:
            value_font = body_font_bold
        else:
            value_font = body_font

        label_args = {"text": f"{label}{fmt(value)}", "font": value_font}

        if color_fn:
            color = color_fn(value)
            if color:
                label_args["foreground"] = color

        ttk.Label(totals_frame, **label_args).pack(anchor="w", pady=2)


    add_total_label("Portfolio Start:          ", total_portfolio[0])
    add_total_label("Portfolio End:            ", total_portfolio[-1])
    add_total_label("Maximum Portfolio:        ", np.max(total_portfolio))
    add_total_label("Minimum Portfolio:        ", np.min(total_portfolio))

    ttk.Separator(totals_frame, orient="horizontal").pack(fill="x", pady=4)
    ttk.Label(totals_frame, text="", font=body_font).pack(pady=6)

    add_total_label("Taxes Paid (sum):         ", np.sum(r["taxes"]))
    add_total_label("Household Expenses (sum): ", np.sum(r["expenses"]))
    add_total_label(
        "Lifetime Funding Gap:     ",
        np.sum(r["funding_gap"]),
        color_fn=funding_gap_color,
        bold=True
    )

    ttk.Separator(totals_frame, orient="horizontal").pack(fill="x", pady=4)
    ttk.Label(totals_frame, text="", font=body_font).pack(pady=6)

    ttk.Label(
        totals_frame,
        text=(
            f"{fmt_pct(r.get('simulated_shortfall_rate'))} of modeled scenarios resulted\n"
            "    in the portfolio falling to $0."
        ),
        font=body_font,
        justify="left"
    ).pack(anchor="w", pady=2)

    ttk.Label(totals_frame, text="", font=body_font).pack(pady=4)
    add_total_label("Fund Expenses (sum):      ", np.sum(r["fund_expenses"]))

    inputs_frame = ttk.Frame(summary_tab, padding=10)
    inputs_frame.grid(row=0, column=1, sticky="nsew")

    ttk.Label(inputs_frame, text="Simulation Inputs / Assumptions", font=header_font).pack(
        anchor="w", pady=(0, 8)
    )


    def add_input_label(label, value):
        ttk.Label(inputs_frame, text=f"{label}{value}", font=body_font).pack(anchor="w", pady=2)


    def add_empty_space(label):
        ttk.Label(inputs_frame, text=label, font=body_font).pack(anchor="w", pady=2)


    add_input_label("Husband Age:            ", dialog.husband.age)
    add_input_label("Husband Retirement Age: ", dialog.husband.retire_age)

    if dialog.sim_config.second_person_enabled:
        add_input_label("Wife Age:               ", dialog.wife.age)
        add_input_label("Wife Retirement Age:    ", dialog.wife.retire_age)
    else:
        add_empty_space("                ")
        add_empty_space("    ")

    ttk.Separator(inputs_frame, orient="horizontal").pack(fill="x", pady=4)
    ttk.Label(inputs_frame, text="", font=body_font).pack(pady=6)

    add_input_label("Expected Annual Stock Return:    ", f"{dialog.sim_config.eq_mean * 100:.2f}%")
    add_input_label("Expected Annual Bond Return:     ", f"{dialog.sim_config.bd_mean * 100:.2f}%")
    add_input_label("Expected Annual Cash Return:     ", f"{dialog.sim_config.cs_mean * 100:.2f}%")
    add_input_label("Expected Inflation Rate:         ", f"{dialog.sim_config.inflation_rate * 100:.2f}%")

    ttk.Separator(inputs_frame, orient="horizontal").pack(fill="x", pady=4)

    add_input_label("Fund Expense Rate:               ", f"{dialog.sim_config.fund_expense * 100:.2f}%")

    summary_text = (
        "Values shown are outputs of the simulation based on the user's inputs and assumptions.\n"
        "All amounts are displayed in real (inflation-adjusted) or nominal terms as selected.\n"
        "Totals represent the sum of the item across the simulation period.\n\n"
    )

    ttk.Label(summary_tab, text=summary_text, font=body_font, justify="left").grid(
        row=1, column=0, columnspan=2, sticky="w", pady=(20, 0)
    )

    summary_tab.columnconfigure(0, weight=1)
    summary_tab.columnconfigure(1, weight=1)

    return summary_tab