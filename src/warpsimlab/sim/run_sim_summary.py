# run_sim_summary.py

from .simulation import run_pipeline
from src.warpsimlab.plots.summaryDialog import SummaryDialog
from src.warpsimlab.plots import io  # ensure io.py is imported


def run_sim_summary(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config):
    """
    Deterministic yearly financial summary simulation using the canonical pipeline.
    """

    p = run_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        force_num_sims=1
    )

    summary_results = p["summary_results"]

    # Display dialog
    dialog = SummaryDialog(summary_results, husband, wife, sim_config, title="Simulation Summary")

    # Optional CSV output
    if sim_config.output_csv == "Output":
        csv_file = io.write_summary_results_csv(
            summary_results,
            sim_config,
            prefix="summary_simulation"
        )
        if csv_file:
            print(f"Simulation results written to: {csv_file}")

    return summary_results