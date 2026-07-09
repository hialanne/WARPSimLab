import numpy as np

from src.warpsimlab.sim import run_sim_operating_balance


def test_run_sim_operating_balance_computes_cumulative_balance_exactly(monkeypatch):
    net_profit = np.array([999.0, 10.0, -4.0, 7.0, -3.0])
    expected_operating_balance = np.array([0.0, 10.0, 6.0, 13.0, 10.0])
    median_portfolio = np.array([100.0, 101.0, 102.0, 103.0, 104.0])

    pipeline_payload = {
        "net_profit": net_profit,
        "years": 4,
        "years_list": np.arange(0, 5),
        "portfolio_plot_data": type(
            "PortfolioPlotDataStub",
            (),
            {"percentiles": {"median": median_portfolio}},
        )(),
    }

    captured = {}

    def fake_run_pipeline(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config, force_num_sims):
        assert force_num_sims == 1
        return pipeline_payload

    def fake_plot_operating_balance(
        years_to_simulate,
        net_profit,
        operating_balance,
        portfolio_value,
        husband,
        wife,
        sim_config,
    ):
        captured["years_to_simulate"] = years_to_simulate
        captured["net_profit"] = net_profit
        captured["operating_balance"] = operating_balance
        captured["portfolio_value"] = portfolio_value
        captured["husband"] = husband
        captured["wife"] = wife
        captured["sim_config"] = sim_config

    monkeypatch.setattr(run_sim_operating_balance, "run_pipeline", fake_run_pipeline)
    monkeypatch.setattr(run_sim_operating_balance, "plot_operating_balance", fake_plot_operating_balance)

    husband = object()
    wife = object()
    sim_config = type("SimConfig", (), {"output_csv": "Do Not Output"})()

    run_sim_operating_balance.run_sim_operating_balance(
        husband_portfolio=None,
        wife_portfolio=None,
        husband=husband,
        wife=wife,
        expenses=None,
        sim_config=sim_config,
    )

    assert captured["years_to_simulate"] == pipeline_payload["years"]
    np.testing.assert_array_equal(captured["net_profit"], net_profit)
    np.testing.assert_array_equal(captured["operating_balance"], expected_operating_balance)
    np.testing.assert_array_equal(captured["portfolio_value"], median_portfolio)
    assert captured["husband"] is husband
    assert captured["wife"] is wife
    assert captured["sim_config"] is sim_config