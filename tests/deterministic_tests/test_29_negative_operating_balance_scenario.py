import numpy as np
from types import SimpleNamespace
import pytest

from src.warpsimlab.sim.run_sim_operating_balance import run_sim_operating_balance


def make_person(*, age=40, retire_age=100):
    return SimpleNamespace(
        age=age,
        retire_age=retire_age,
        income=0.0,
        ss=0.0,
        ss_age=99,
        pension=0.0,
        pension_age=99,
        annuity=0.0,
        annuity_age=99,
        annual_401k_contribution=0.0,
        annual_employer_match=0.0,
        pension_inflation_adjustment_pct=0.0,
    )


def make_portfolio():
    return SimpleNamespace(
        equity_pre=0.0,
        equity_post=0.0,
        bond_pre=0.0,
        bond_post=0.0,
        cash_pre=0.0,
        cash_post=0.0,
        real_estate=0.0,
    )


def make_expenses():
    return SimpleNamespace()


def make_sim_config():
    return SimpleNamespace(
        output_csv="No Output",
    )


def test_negative_operating_balance_scenario(monkeypatch):
    captured = {}

    class FakePortfolioPlotData:
        def __init__(self, median):
            self.percentiles = {"median": median}

    pipeline_payload = {
        "years": np.array([2026.0, 2027.0, 2028.0, 2029.0], dtype=float),
        "years_list": [2026, 2027, 2028, 2029],
        "net_profit": np.array([0.0, -15_000.0, -15_000.0, -15_000.0], dtype=float),
        "portfolio_plot_data": FakePortfolioPlotData(
            median=np.array([100_000.0, 85_000.0, 70_000.0, 55_000.0], dtype=float)
        ),
    }

    def fake_run_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        force_num_sims=None,
    ):
        captured["force_num_sims"] = force_num_sims
        captured["pipeline_args"] = {
            "husband_portfolio": husband_portfolio,
            "wife_portfolio": wife_portfolio,
            "husband": husband,
            "wife": wife,
            "expenses": expenses,
            "sim_config": sim_config,
        }
        return pipeline_payload

    def fake_plot_operating_balance(
        *,
        years_to_simulate,
        net_profit,
        operating_balance,
        portfolio_value,
        husband,
        wife,
        sim_config,
    ):
        captured["plot_call"] = {
            "years_to_simulate": np.array(years_to_simulate, dtype=float),
            "net_profit": np.array(net_profit, dtype=float),
            "operating_balance": np.array(operating_balance, dtype=float),
            "portfolio_value": np.array(portfolio_value, dtype=float),
            "husband": husband,
            "wife": wife,
            "sim_config": sim_config,
        }

    monkeypatch.setattr(
        "src.warpsimlab.sim.run_sim_operating_balance.run_pipeline",
        fake_run_pipeline,
    )
    monkeypatch.setattr(
        "src.warpsimlab.sim.run_sim_operating_balance.plot_operating_balance",
        fake_plot_operating_balance,
    )

    husband_portfolio = make_portfolio()
    wife_portfolio = make_portfolio()
    husband = make_person(age=40, retire_age=100)
    wife = make_person(age=38, retire_age=100)
    expenses = make_expenses()
    sim_config = make_sim_config()

    run_sim_operating_balance(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
    )

    assert captured["force_num_sims"] == 1

    expected_years = np.array([2026.0, 2027.0, 2028.0, 2029.0], dtype=float)
    expected_net_profit = np.array([0.0, -15_000.0, -15_000.0, -15_000.0], dtype=float)
    expected_operating_balance = np.array([0.0, -15_000.0, -30_000.0, -45_000.0], dtype=float)
    expected_portfolio_value = np.array([100_000.0, 85_000.0, 70_000.0, 55_000.0], dtype=float)

    plot_call = captured["plot_call"]

    assert plot_call["years_to_simulate"] == pytest.approx(expected_years)
    assert plot_call["net_profit"] == pytest.approx(expected_net_profit)
    assert plot_call["operating_balance"] == pytest.approx(expected_operating_balance)
    assert plot_call["portfolio_value"] == pytest.approx(expected_portfolio_value)

    assert plot_call["husband"] is husband
    assert plot_call["wife"] is wife
    assert plot_call["sim_config"] is sim_config