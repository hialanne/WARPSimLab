import numpy as np

from src.warpsimlab.sim import run_sim_portfolio


def test_run_sim_portfolio_caps_num_sims_at_40000_and_sends_correct_plot_payload(monkeypatch):
    simulation_data = type(
        "PortfolioPlotDataStub",
        (),
        {"percentiles": {"median": np.array([100.0, 105.0, 110.0])}},
    )()
    years_list = np.array([0, 1, 2])

    pipeline_payload = {
        "portfolio_plot_data": simulation_data,
        "years_list": years_list,
    }

    captured = {
        "messagebox_calls": [],
    }

    def fake_run_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        force_num_sims,
    ):
        captured["run_pipeline_force_num_sims"] = force_num_sims
        captured["run_pipeline_sim_config_num_sims"] = sim_config.num_sims
        return pipeline_payload

    def fake_plot_portfolio_projection(
        years_list,
        simulation_data,
        sim_config,
        annotate_plots,
        sim_rebalance_string,
        husband,
        wife,
    ):
        captured["years_list"] = years_list
        captured["simulation_data"] = simulation_data
        captured["sim_config"] = sim_config
        captured["annotate_plots"] = annotate_plots
        captured["sim_rebalance_string"] = sim_rebalance_string
        captured["husband"] = husband
        captured["wife"] = wife

    def fake_showinfo(title, message):
        captured["messagebox_calls"].append((title, message))

    monkeypatch.setattr(run_sim_portfolio, "run_pipeline", fake_run_pipeline)
    monkeypatch.setattr(run_sim_portfolio, "plot_portfolio_projection", fake_plot_portfolio_projection)
    monkeypatch.setattr(run_sim_portfolio.messagebox, "showinfo", fake_showinfo)

    husband = object()
    wife = object()

    sim_config = type(
        "SimConfig",
        (),
        {
            "num_sims": 50000,
            "annotate_plots": True,
            "sim_initial_allocation_mode": "annual",
            "output_csv": "Do Not Output",
        },
    )()

    run_sim_portfolio.run_sim_portfolio(
        husband_portfolio=None,
        wife_portfolio=None,
        husband=husband,
        wife=wife,
        expenses=None,
        sim_config=sim_config,
    )

    assert sim_config.num_sims == 50000

    assert captured["run_pipeline_force_num_sims"] is None
    assert captured["run_pipeline_sim_config_num_sims"] == 50000

    np.testing.assert_array_equal(captured["years_list"], years_list)
    assert captured["simulation_data"] is simulation_data
    assert captured["sim_config"] is sim_config
    assert captured["annotate_plots"] is True
    assert captured["sim_rebalance_string"] == "annual"
    assert captured["husband"] is husband
    assert captured["wife"] is wife