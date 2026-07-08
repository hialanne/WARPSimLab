# gui_annotations.py

def _multi_path_mode_label(simulation_controls):
    subplot_mode = simulation_controls.get("subplot_mode", "")
    if subplot_mode != "monte_carlo":
        return None

    monte_carlo_mode = simulation_controls.get(
        "monte_carlo_mode",
        "pathBasedAnnualSampling"
    )

    if monte_carlo_mode == "rollingHistoricalWindows":
        return "Historical Windows"

    return "Monte Carlo"


def build_scenario_explorer_annotations(
    *,
    main_gui,
    tmp_ret_age_h,
    tmp_ret_age_w,
    inflation,
    fund_expense,
    historical_data_multiplier,
    stocks,
    bonds,
    cash,
    baseline_stocks,
    baseline_bonds,
    baseline_cash,
    wife_snapshot,
    scenario_expense_multiplier,
    scenario_withdraw_pct,
):
    annotation_list = []
    annotation_list.append([{"text": "Scenario Dashboard (Temporary)", "color": "black"}])

    husband_changed = tmp_ret_age_h != main_gui.husband.retire_age
    husband_color = "red" if husband_changed else "black"

    if wife_snapshot is not None and tmp_ret_age_w is not None:
        wife_changed = tmp_ret_age_w != main_gui.wife.retire_age
        wife_color = "red" if wife_changed else "black"
        annotation_list.append([
            {"text": "Retirement Age: ", "color": "black"},
            {"text": f"Husband {tmp_ret_age_h}", "color": husband_color},
            {"text": f", Wife {tmp_ret_age_w}", "color": wife_color},
        ])
    else:
        annotation_list.append([
            {"text": f"Retirement Age: Husband {tmp_ret_age_h}", "color": husband_color}
        ])

    inflation_changed = inflation != main_gui.inflation
    fund_expense_changed = fund_expense != main_gui.simulation_settings.get("fund_expense")
    inflation_color = "red" if inflation_changed else "black"
    fund_expense_color = "red" if fund_expense_changed else "black"

    market_changed = historical_data_multiplier != 100.0
    market_color = "red" if market_changed else "black"

    stocks_changed = stocks != baseline_stocks
    bonds_changed = bonds != baseline_bonds
    cash_changed = cash != baseline_cash
    stocks_color = "red" if stocks_changed else "black"
    bonds_color = "red" if bonds_changed else "black"
    cash_color = "red" if cash_changed else "black"

    annotation_list.append([
        {"text": f"Inflation rate: {inflation:.1f}%", "color": inflation_color},
        {"text": f", Fund Expenses: {fund_expense:.2f}%", "color": fund_expense_color},
    ])

    annotation_list.append([
        {"text": f"Hypothetical Market Multiplier: {historical_data_multiplier:.0f}%", "color": market_color}
    ])

    annotation_list.append([
        {"text": f"Stock {stocks:.0f}%", "color": stocks_color},
        {"text": f", Bond {bonds:.0f}%", "color": bonds_color},
        {"text": f", Cash {cash:.0f}%", "color": cash_color},
    ])

    manual = bool(main_gui.simulation_controls.get("manual_expenses", True))

    if manual:
        exp_mult = scenario_expense_multiplier
        if exp_mult is None:
            exp_mult = 1.0

        exp_pct = exp_mult * 100.0
        exp_changed = abs(exp_mult - 1.0) > 1e-9
        exp_color = "red" if exp_changed else "black"

        annotation_list.append([
            {"text": f"Expense Multiplier: {exp_pct:.0f}%", "color": exp_color}
        ])
    else:
        withdraw_pct = scenario_withdraw_pct
        if withdraw_pct is None:
            withdraw_pct = float(main_gui.simulation_controls.get("retirement_withdraw_pct", 4.0))

        baseline_withdraw = float(main_gui.simulation_controls.get("retirement_withdraw_pct", 4.0))
        wd_changed = abs(withdraw_pct - baseline_withdraw) > 1e-9
        wd_color = "red" if wd_changed else "black"

        annotation_list.append([
            {"text": f"Withdrawal %: {withdraw_pct:.2f}%", "color": wd_color}
        ])

    multi_path_label = _multi_path_mode_label(main_gui.simulation_controls)
    if multi_path_label is not None:

        annotation_list.append([{"text": "", "color": "black"}])

        annotation_list.append([{"text": f"Percentile Bands ({multi_path_label})", "color": "black"}])

    return annotation_list

def build_normal_run_annotations(simulation_controls):
    annotation_list = []

    multi_path_label = _multi_path_mode_label(simulation_controls)
    if multi_path_label is not None:
        annotation_list.append([{"text": f"Percentile Bands ({multi_path_label})", "color": "black"}])

    return annotation_list