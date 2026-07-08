# run_sim_income.py

from .simulation import run_pipeline
from src.warpsimlab.plots.plotYearlyIncome import plot_yearly_income
from src.warpsimlab.plots import io  # ensure io.py is imported


def run_sim_income(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config):
    """
    Run a yearly income-focused simulation using the canonical pipeline.
    """

    # Income mode is deterministic
    p = run_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        force_num_sims=1
    )

    breakdown = p["breakdown_by_class"]

    income_keys = [
        "work",
        "pension",
        "annuity",
        "ss",
        "special_income",
    ]

    cashflow_extra_keys = [
        "rmd",
        "withdrawal",
        "bond_interest",
        "cash_interest",
        "qualified_dividends",
    ]

    if sim_config.sim_type == "income_sim":
        plot_breakdown = {
            key: breakdown[key].copy()
            for key in income_keys
        }

    elif sim_config.sim_type == "cashflow_sim":
        plot_breakdown = {
            "income": sum(breakdown[key] for key in income_keys)
        }

        for key in cashflow_extra_keys:
            plot_breakdown[key] = breakdown[key].copy()

    else:
        raise ValueError(f"Unsupported income runner sim_type: {sim_config.sim_type}")

    plot_total = sum(plot_breakdown[key] for key in plot_breakdown)

    '''
    print("YEAR | NET | WORK | PENSION | ANNUITY | SS | RMD | SPECIAL | TAXES | EXPENSES")
    for i in range(len(p["years_list"])):
        print(
            int(p["years_list"][i]),
            round(p["net_income"][i], 2),
            round(p["breakdown_by_class"]["work"][i], 2),
            round(p["breakdown_by_class"]["pension"][i], 2),
            round(p["breakdown_by_class"]["annuity"][i], 2),
            round(p["breakdown_by_class"]["ss"][i], 2),
            round(p["breakdown_by_class"]["rmd"][i], 2),
            round(p["breakdown_by_class"]["special_income"][i], 2),
            round(p["taxes"][i], 2),
            round(p["expense_amt"][i], 2),
        )

    print("YEAR | NET | WORK | BOND_INT | CASH_INT | QDIV | EXPENSES | NET_PROFIT")
    for i in range(len(p["years_list"])):
        print(
            int(p["years_list"][i]),
            round(p["net_income"][i], 2),
            round(p["breakdown_by_class"]["work"][i], 2),
            round(p["breakdown_by_class"]["bond_interest"][i], 2),
            round(p["breakdown_by_class"]["cash_interest"][i], 2),
            round(p["breakdown_by_class"]["qualified_dividends"][i], 2),
            round(p["expense_amt"][i], 2),
            round(p["net_profit"][i], 2),
        )
    '''

    # Plot
    plot_yearly_income(
        p["years"],
        net_profit=p["net_profit"],
        net_income=plot_total,
        breakdown=plot_breakdown,
        taxes=p["taxes"],
        expenses=p["expense_amt"],
        husband=husband,
        wife=wife,
        sim_config=sim_config
    )

    # Optional CSV output
    if sim_config.output_csv == "Output":
        csv_file = io.write_income_results_csv(
            p["years_list"],
            p["net_income"],
            p["net_profit"],
            p["taxes"],
            p["breakdown_by_class"],
            sim_config,
            prefix="income_simulation"
        )
        if csv_file:
            print(f"Income simulation results written to: {csv_file}")