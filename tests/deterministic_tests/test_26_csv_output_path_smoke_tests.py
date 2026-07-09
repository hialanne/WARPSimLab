import numpy as np

from src.warpsimlab.sim import run_sim_income
from src.warpsimlab.sim import run_sim_operating_balance
from src.warpsimlab.sim import run_sim_summary
from src.warpsimlab.sim import run_sim_portfolio


def test_run_sim_income_calls_expected_csv_writer(monkeypatch):
    pipeline_payload = {
        "years": 2,
        "years_list": np.array([0, 1, 2]),
        "net_income": np.array([0.0, 10.0, 20.0]),
        "net_profit": np.array([0.0, 1.0, 2.0]),
        "taxes": np.array([0.0, 3.0, 4.0]),
        "expense_amt": np.array([0.0, 9.0, 18.0]),
            "breakdown_by_class": {
                "work": np.array([0.0, 10.0, 20.0]),
                "pension": np.array([0.0, 0.0, 0.0]),
                "annuity": np.array([0.0, 0.0, 0.0]),
                "ss": np.array([0.0, 0.0, 0.0]),
                "special_income": np.array([0.0, 0.0, 0.0]),
                "rmd": np.array([0.0, 0.0, 0.0]),
                "withdrawal": np.array([0.0, 0.0, 0.0]),
                "bond_interest": np.array([0.0, 0.0, 0.0]),
                "cash_interest": np.array([0.0, 0.0, 0.0]),
                "qualified_dividends": np.array([0.0, 0.0, 0.0]),
            },
    }
    captured = {}

    monkeypatch.setattr(run_sim_income, "run_pipeline", lambda *args, **kwargs: pipeline_payload)
    monkeypatch.setattr(run_sim_income, "plot_yearly_income", lambda *args, **kwargs: None)

    def fake_writer(years, net_income, net_profit, yearly_taxes, breakdown, sim_config, prefix):
        captured["args"] = (years, net_income, net_profit, yearly_taxes, breakdown, sim_config, prefix)
        return "/tmp/income.csv"

    monkeypatch.setattr(run_sim_income.io, "write_income_results_csv", fake_writer)

    sim_config = type(
        "SimConfig",
        (),
        {
            "output_csv": "Output",
            "sim_type": "income_sim",
        },
    )()

    run_sim_income.run_sim_income(None, None, None, None, None, sim_config)

    years, net_income, net_profit, yearly_taxes, breakdown, cfg, prefix = captured["args"]
    np.testing.assert_array_equal(years, pipeline_payload["years_list"])
    np.testing.assert_array_equal(net_income, pipeline_payload["net_income"])
    np.testing.assert_array_equal(net_profit, pipeline_payload["net_profit"])
    np.testing.assert_array_equal(yearly_taxes, pipeline_payload["taxes"])
    assert breakdown is pipeline_payload["breakdown_by_class"]
    assert cfg is sim_config
    assert prefix == "income_simulation"


def test_run_sim_operating_balance_calls_expected_csv_writer_when_available(monkeypatch):
    pipeline_payload = {
        "net_profit": np.array([0.0, 5.0, -2.0]),
        "years": 2,
        "years_list": np.array([0, 1, 2]),
        "portfolio_plot_data": type(
            "PortfolioPlotDataStub",
            (),
            {"percentiles": {"median": np.array([100.0, 101.0, 102.0])}},
        )(),
    }
    captured = {}

    monkeypatch.setattr(run_sim_operating_balance, "run_pipeline", lambda *args, **kwargs: pipeline_payload)
    monkeypatch.setattr(run_sim_operating_balance, "plot_operating_balance", lambda *args, **kwargs: None)

    def fake_writer(years_list, net_profit, operating_balance, sim_config, prefix):
        captured["args"] = (years_list, net_profit, operating_balance, sim_config, prefix)
        return "/tmp/operating_balance.csv"

    monkeypatch.setattr(run_sim_operating_balance.io, "write_operating_balance_results_csv", fake_writer, raising=False)

    sim_config = type("SimConfig", (), {"output_csv": "Output"})()

    run_sim_operating_balance.run_sim_operating_balance(None, None, None, None, None, sim_config)

    years_list, net_profit, operating_balance, cfg, prefix = captured["args"]
    np.testing.assert_array_equal(years_list, pipeline_payload["years_list"])
    np.testing.assert_array_equal(net_profit, pipeline_payload["net_profit"])
    np.testing.assert_array_equal(operating_balance, np.array([0.0, 5.0, 3.0]))
    assert cfg is sim_config
    assert prefix == "operating_balance_simulation"


def test_run_sim_summary_calls_expected_csv_writer(monkeypatch):
    summary_results = {
        "year": np.array([2025.0, 2026.0]),
        "total_assets": np.array([100.0, 120.0]),
        "pre_tax_assets": np.array([60.0, 70.0]),
        "post_tax_assets": np.array([40.0, 50.0]),
        "real_estate": np.array([0.0, 0.0]),
        "gross_income": np.array([50.0, 55.0]),
        "net_income": np.array([40.0, 44.0]),
        "taxes": np.array([10.0, 11.0]),
        "tax_bracket": np.array([0.22, 0.22]),
        "expenses": np.array([35.0, 36.0]),
        "net_cash_flow": np.array([5.0, 8.0]),
        "wages": np.array([45.0, 46.0]),
        "rmd": np.array([0.0, 0.0]),
        "ira_401k": np.array([2.0, 2.0]),
        "social_security": np.array([0.0, 0.0]),
        "pensions": np.array([0.0, 0.0]),
        "annuities": np.array([0.0, 0.0]),
        "withdrawal": np.array([0.0, 0.0]),
        "fund_expenses": np.array([1.0, 1.0]),
        "bond_interest": np.array([0.0, 0.0]),
        "cash_interest": np.array([0.0, 0.0]),
        "qualified_dividends": np.array([0.0, 0.0]),
    }
    captured = {}

    monkeypatch.setattr(run_sim_summary, "run_pipeline", lambda *args, **kwargs: {"summary_results": summary_results})
    monkeypatch.setattr(run_sim_summary, "SummaryDialog", lambda *args, **kwargs: object())

    def fake_writer(results, sim_config, prefix):
        captured["args"] = (results, sim_config, prefix)
        return "/tmp/summary.csv"

    monkeypatch.setattr(run_sim_summary.io, "write_summary_results_csv", fake_writer)

    sim_config = type("SimConfig", (), {"output_csv": "Output"})()

    run_sim_summary.run_sim_summary(None, None, None, None, None, sim_config)

    results, cfg, prefix = captured["args"]
    assert results is summary_results
    assert cfg is sim_config
    assert prefix == "summary_simulation"


def test_run_sim_portfolio_calls_expected_csv_writer(monkeypatch):
    simulation_data = type(
        "PortfolioPlotDataStub",
        (),
        {
            "percentiles": {"median": np.array([100.0, 110.0, 120.0])},
            "baseline": np.array([100.0, 110.0, 120.0]),
            "cash": np.array([10.0, 10.0, 10.0]),
            "bonds": np.array([20.0, 20.0, 20.0]),
            "realestate": np.array([0.0, 0.0, 0.0]),
            "pre_tax_assets": np.array([60.0, 65.0, 70.0]),
            "post_tax_assets": np.array([40.0, 45.0, 50.0]),
        },
    )()
    years_list = np.array([0, 1, 2])
    captured = {}

    monkeypatch.setattr(
        run_sim_portfolio,
        "run_pipeline",
        lambda *args, **kwargs: {
            "portfolio_plot_data": simulation_data,
            "years_list": years_list,
        },
    )
    monkeypatch.setattr(run_sim_portfolio, "plot_portfolio_projection", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_sim_portfolio.messagebox, "showinfo", lambda *args, **kwargs: None)

    def fake_writer(years, sim_data, sim_config, prefix):
        captured["args"] = (years, sim_data, sim_config, prefix)
        return "/tmp/portfolio.csv"

    monkeypatch.setattr(run_sim_portfolio.io, "write_portfolio_results_csv", fake_writer)

    sim_config = type(
        "SimConfig",
        (),
        {
            "output_csv": "Output",
            "num_sims": 100,
            "annotate_plots": False,
            "sim_rebalance": "none",
        },
    )()

    run_sim_portfolio.run_sim_portfolio(None, None, None, None, None, sim_config)

    years, sim_data, cfg, prefix = captured["args"]
    np.testing.assert_array_equal(years, years_list)
    assert sim_data is simulation_data
    assert cfg is sim_config
    assert prefix == "portfolio_simulation"