# run_sim_portfolio.py

from tkinter import messagebox

from .simulation import run_pipeline
from src.warpsimlab.plots.plotPortfolioProjection import plot_portfolio_projection
from src.warpsimlab.plots import io  # ensure io.py is imported


def run_sim_portfolio(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config):

    # --------------------------
    # Simulation count limits (preserve existing behavior)
    # --------------------------
    if sim_config.num_sims > 100000:
        sim_config.num_sims = 100000
        messagebox.showinfo("Simulation Limit", "Number of simulations limited to 100000.")

    # --------------------------
    # Canonical pipeline
    # --------------------------
    p = run_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        force_num_sims=None,  # pipeline enforces subplot_mode != monte_carlo -> num_sims=1
    )

    simulation_data = p["portfolio_plot_data"]
    years_list = p["years_list"]

    # --------------------------
    # Plot
    # --------------------------
    plot_portfolio_projection(
        years_list,
        simulation_data,
        sim_config=sim_config,
        annotate_plots=sim_config.annotate_plots,
        sim_rebalance_string=sim_config.sim_initial_allocation_mode,
        husband=husband,
        wife=wife,
    )

    # --------------------------
    # Optional CSV output
    # --------------------------
    if sim_config.output_csv == "Output":
        csv_file = io.write_portfolio_results_csv(
            years_list,
            simulation_data,
            sim_config,
            prefix="portfolio_simulation"
        )
        if csv_file:
            print(f"Portfolio simulation results written to: {csv_file}")