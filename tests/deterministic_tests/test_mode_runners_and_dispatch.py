from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.plots.portfolioPlotData import PortfolioPlotData
from src.warpsimlab.sim.run_sim_income import run_sim_income
from src.warpsimlab.sim.run_sim_operating_balance import run_sim_operating_balance
from src.warpsimlab.sim.run_sim_portfolio import run_sim_portfolio
from src.warpsimlab.sim.run_sim_summary import run_sim_summary
from src.warpsimlab.sim.simulation import run_simulation


def _fake_pipeline_output():
    return {
        "years": 2,
        "years_list": np.array([0, 1, 2]),
        "net_income": np.array([0.0, 100.0, 90.0]),
        "net_profit": np.array([0.0, 30.0, -10.0]),
        "breakdown_by_class": {
            "work": np.array([0.0, 100.0, 0.0]),
            "pension": np.array([0.0, 0.0, 0.0]),
            "annuity": np.array([0.0, 0.0, 0.0]),
            "ss": np.array([0.0, 0.0, 0.0]),
            "special_income": np.array([0.0, 0.0, 0.0]),
            "rmd": np.array([0.0, 0.0, 0.0]),
            "withdrawal": np.array([0.0, 0.0, 20.0]),
            "bond_interest": np.array([0.0, 0.0, 0.0]),
            "cash_interest": np.array([0.0, 0.0, 0.0]),
            "qualified_dividends": np.array([0.0, 0.0, 0.0]),
        },
        "taxes": np.array([0.0, 10.0, 5.0]),
        "expense_amt": np.array([0.0, 60.0, 0.0]),
        "summary_results": {"hello": "world"},
        "portfolio_plot_data": PortfolioPlotData(
            years=np.array([0, 1, 2]),
            percentiles={"median": np.array([100.0, 130.0, 120.0])},
        ),
    }


def test_run_simulation_dispatches_to_correct_runner(monkeypatch, scenario_builders):
    Portfolio = scenario_builders.Portfolio
    Person = scenario_builders.Person
    DynamicExpenses = scenario_builders.DynamicExpenses
    make_config = scenario_builders.make_config

    husband_portfolio = Portfolio()
    wife_portfolio = Portfolio()
    husband = Person(age=40, retire_age=65)
    wife = Person(age=40, retire_age=65)
    expenses = DynamicExpenses()

    seen = {}

    def make_runner(name):
        def _runner(*args, **kwargs):
            seen["name"] = name
            return name
        return _runner

    monkeypatch.setattr("src.warpsimlab.sim.run_sim_income.run_sim_income", make_runner("cashflow"))
    monkeypatch.setattr("src.warpsimlab.sim.run_sim_operating_balance.run_sim_operating_balance", make_runner("operating"))
    monkeypatch.setattr("src.warpsimlab.sim.run_sim_portfolio.run_sim_portfolio", make_runner("portfolio"))
    monkeypatch.setattr("src.warpsimlab.sim.run_sim_summary.run_sim_summary", make_runner("summary"))

    cfg = make_config(sim_type="cashflow_sim")
    assert run_simulation(husband_portfolio, wife_portfolio, husband, wife, expenses, cfg) == "cashflow"

    cfg = make_config(sim_type="operating_balance_sim")
    assert run_simulation(husband_portfolio, wife_portfolio, husband, wife, expenses, cfg) == "operating"

    cfg = make_config(sim_type="portfolio_sim")
    assert run_simulation(husband_portfolio, wife_portfolio, husband, wife, expenses, cfg) == "portfolio"

    cfg = make_config(sim_type="summary_sim")
    assert run_simulation(husband_portfolio, wife_portfolio, husband, wife, expenses, cfg) == "summary"


def test_run_sim_income_calls_plotter(monkeypatch, scenario_builders):
    Portfolio = scenario_builders.Portfolio
    Person = scenario_builders.Person
    DynamicExpenses = scenario_builders.DynamicExpenses
    make_config = scenario_builders.make_config

    captured = {}

    monkeypatch.setattr("src.warpsimlab.sim.run_sim_income.run_pipeline", lambda *a, **k: _fake_pipeline_output())

    def fake_plot(years, net_profit, net_income, breakdown, taxes, expenses, husband, wife, sim_config):
        captured["years"] = years
        captured["net_profit"] = net_profit
        captured["net_income"] = net_income
        captured["breakdown"] = breakdown
        captured["taxes"] = taxes
        captured["expenses"] = expenses

    monkeypatch.setattr("src.warpsimlab.sim.run_sim_income.plot_yearly_income", fake_plot)

    run_sim_income(
        Portfolio(),
        Portfolio(),
        Person(age=40, retire_age=65),
        Person(age=40, retire_age=65),
        DynamicExpenses(),
        make_config(sim_type="cashflow_sim"),
    )

    assert captured["years"] == 2
    assert np.allclose(captured["net_profit"], [0.0, 30.0, -10.0])
    assert np.allclose(captured["net_income"], [0.0, 100.0, 20.0])
    assert np.allclose(captured["taxes"], [0.0, 10.0, 5.0])
    assert np.allclose(captured["expenses"], [0.0, 60.0, 0.0])


def test_run_sim_operating_balance_builds_cumulative_series(monkeypatch, scenario_builders):
    Portfolio = scenario_builders.Portfolio
    Person = scenario_builders.Person
    DynamicExpenses = scenario_builders.DynamicExpenses
    make_config = scenario_builders.make_config

    captured = {}

    monkeypatch.setattr("src.warpsimlab.sim.run_sim_operating_balance.run_pipeline", lambda *a, **k: _fake_pipeline_output())

    def fake_plot(years_to_simulate, net_profit, operating_balance, portfolio_value, husband, wife, sim_config):
        captured["years_to_simulate"] = years_to_simulate
        captured["net_profit"] = net_profit
        captured["operating_balance"] = operating_balance
        captured["portfolio_value"] = portfolio_value

    monkeypatch.setattr("src.warpsimlab.sim.run_sim_operating_balance.plot_operating_balance", fake_plot)

    run_sim_operating_balance(
        Portfolio(),
        Portfolio(),
        Person(age=40, retire_age=65),
        Person(age=40, retire_age=65),
        DynamicExpenses(),
        make_config(sim_type="operating_balance_sim"),
    )

    assert captured["years_to_simulate"] == 2
    assert np.allclose(captured["net_profit"], [0.0, 30.0, -10.0])
    assert np.allclose(captured["operating_balance"], [0.0, 30.0, 20.0])
    assert np.allclose(captured["portfolio_value"], [100.0, 130.0, 120.0])


def test_run_sim_summary_returns_summary_results_and_constructs_dialog(monkeypatch, scenario_builders):
    Portfolio = scenario_builders.Portfolio
    Person = scenario_builders.Person
    DynamicExpenses = scenario_builders.DynamicExpenses
    make_config = scenario_builders.make_config

    pipeline_output = _fake_pipeline_output()
    captured = {}

    monkeypatch.setattr("src.warpsimlab.sim.run_sim_summary.run_pipeline", lambda *a, **k: pipeline_output)

    class FakeDialog:
        def __init__(self, summary_results, husband, wife, sim_config, title="Simulation Summary"):
            captured["summary_results"] = summary_results
            captured["title"] = title

    monkeypatch.setattr("src.warpsimlab.sim.run_sim_summary.SummaryDialog", FakeDialog)

    result = run_sim_summary(
        Portfolio(),
        Portfolio(),
        Person(age=40, retire_age=65),
        Person(age=40, retire_age=65),
        DynamicExpenses(),
        make_config(sim_type="summary_sim"),
    )

    assert result == pipeline_output["summary_results"]
    assert captured["summary_results"] == pipeline_output["summary_results"]
    assert captured["title"] == "Simulation Summary"


def test_run_sim_portfolio_caps_num_sims_and_calls_plotter(monkeypatch, scenario_builders):
    Portfolio = scenario_builders.Portfolio
    Person = scenario_builders.Person
    DynamicExpenses = scenario_builders.DynamicExpenses
    make_config = scenario_builders.make_config

    captured = {}

    monkeypatch.setattr("src.warpsimlab.sim.run_sim_portfolio.run_pipeline", lambda *a, **k: _fake_pipeline_output())

    def fake_plot(years_list, simulation_data, sim_config, annotate_plots, sim_rebalance_string, husband, wife):
        captured["years_list"] = years_list
        captured["simulation_data"] = simulation_data
        captured["sim_rebalance_string"] = sim_rebalance_string

    monkeypatch.setattr("src.warpsimlab.sim.run_sim_portfolio.plot_portfolio_projection", fake_plot)

    messagebox_calls = []

    def fake_showinfo(title, message):
        messagebox_calls.append((title, message))

    monkeypatch.setattr("src.warpsimlab.sim.run_sim_portfolio.messagebox.showinfo", fake_showinfo)

    sim_config = make_config(sim_type="portfolio_sim", num_sims=50000)

    run_sim_portfolio(
        Portfolio(),
        Portfolio(),
        Person(age=40, retire_age=65),
        Person(age=40, retire_age=65),
        DynamicExpenses(),
        sim_config,
    )

    assert sim_config.num_sims == 50000
    assert np.array_equal(captured["years_list"], np.array([0, 1, 2]))
    assert captured["sim_rebalance_string"] == sim_config.sim_initial_allocation_mode