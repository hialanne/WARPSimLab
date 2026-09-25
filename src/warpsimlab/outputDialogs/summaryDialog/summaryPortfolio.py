# summaryPortfolio.py

import numpy as np
from tkinter import ttk


def build_portfolio_tab(dialog, notebook):
    portfolio_tab = ttk.Frame(notebook, padding=15)
    notebook.add(portfolio_tab, text="Portfolio")

    header_font = dialog._report_header_font
    body_font = dialog._report_body_font
    body_total_font = dialog._report_body_bold_font

    r = dialog.results

    def fmt(value):
        return f"${value:,.0f}"

    if dialog.sim_config.second_person_enabled:
        last_retirement_index = max(
            dialog.husband.retire_age - dialog.husband.age,
            dialog.wife.retire_age - dialog.wife.age
        )
    else:
        last_retirement_index = dialog.husband.retire_age - dialog.husband.age

    last_retirement_index = min(max(last_retirement_index, 0), len(r["year"]) - 1)

    p_left = ttk.Frame(portfolio_tab, padding=10)
    p_left.grid(row=1, column=0, sticky="nsew")

    p_middle = ttk.Frame(portfolio_tab, padding=10)
    p_middle.grid(row=1, column=1, sticky="nsew")

    p_right = ttk.Frame(portfolio_tab, padding=10)
    p_right.grid(row=1, column=2, sticky="nsew")

    portfolio_tab.columnconfigure(0, weight=1)
    portfolio_tab.columnconfigure(1, weight=1)
    portfolio_tab.columnconfigure(2, weight=1)

    def add_portfolio_section(frame, year_idx, title=None):
        if title:
            ttk.Label(frame, text=title, font=header_font).pack(anchor="w", pady=(0, 8))

        year = int(r["year"][year_idx])

        ttk.Label(frame, text=f"Portfolio Value in {year}", font=header_font).pack(anchor="w")
        ttk.Label(frame, text="", font=body_font).pack(anchor="w")

        ttk.Label(
            frame,
            text=f"{'Tax-Deferred Assets:':<21}{fmt(r['pre_tax_assets'][year_idx])}",
            font=body_font
        ).pack(anchor="w", pady=1)

        ttk.Label(
            frame,
            text=f"{'Taxable Assets:':<21}{fmt(r['post_tax_assets'][year_idx])}",
            font=body_font
        ).pack(anchor="w", pady=1)

        roth_assets = r.get("roth_assets", np.zeros_like(r["pre_tax_assets"]))
        hsa_assets = r.get("hsa_assets", np.zeros_like(r["pre_tax_assets"]))

        ttk.Label(frame, text=f"{'Roth Assets:':<21}{fmt(roth_assets[year_idx])}", font=body_font).pack(
            anchor="w", pady=1
        )
        ttk.Label(frame, text=f"{'HSA Assets:':<21}{fmt(hsa_assets[year_idx])}", font=body_font).pack(
            anchor="w", pady=1
        )

        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=4)

        total_portfolio = (
            r["pre_tax_assets"][year_idx]
            + r["post_tax_assets"][year_idx]
            + roth_assets[year_idx]
            + hsa_assets[year_idx]
        )

        label_args = {"text": f"{'Total Portfolio:':<21}{fmt(total_portfolio)}", "font": body_total_font}

        if total_portfolio == 0:
            label_args["foreground"] = "red"

        ttk.Label(frame, **label_args).pack(anchor="w", pady=1)
        ttk.Label(frame, text="", font=body_font).pack(anchor="w")

        ttk.Label(
            frame,
            text=f"{'Real Estate:':<21}{fmt(r['real_estate'][year_idx])}",
            font=body_font
        ).pack(anchor="w", pady=1)

        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=4)

        label_args = {"text": f"{'Total Assets:':<21}{fmt(r['total_assets'][year_idx])}", "font": body_total_font}

        if r["total_assets"][year_idx] == 0:
            label_args["foreground"] = "red"

        ttk.Label(frame, **label_args).pack(anchor="w", pady=1)
        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=4)

    add_portfolio_section(p_left, 0, "Start of Simulation")

    if 0 <= last_retirement_index < len(r["year"]):
        add_portfolio_section(p_middle, last_retirement_index, "Retirement")

    add_portfolio_section(p_right, -1, "End of Simulation")

    summary_frame = ttk.Frame(portfolio_tab)
    summary_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(40, 0))

    summary_text = (
        "There are four tabs: Portfolio, Income, Cash Flow, and Summary.\n\n"
        "If enabled, the portfolio sustained fund expenses throughout the full simulation period.\n"
        "Assets are shown in real (inflation-adjusted) or nominal terms,\n"
        "depending on the simulation settings.\n"
        "Retirement year is the later of the husband's or wife's, if applicable."
    )

    ttk.Label(summary_frame, text=summary_text, font=body_font, justify="left").pack(anchor="w")

    return portfolio_tab