import numpy as np

from src.warpsimlab.sim import run_sim_income


def test_run_sim_income_plots_pipeline_outputs_exactly(monkeypatch):
    years = 4
    years_list = np.arange(0, years + 1)
    net_profit = np.array([0.0, 10.0, 20.0, 30.0, 40.0])
    net_income = np.array([0.0, 100.0, 110.0, 120.0, 130.0])
    taxes = np.array([0.0, 15.0, 16.0, 17.0, 18.0])
    expense_amt = np.array([0.0, 80.0, 82.0, 84.0, 86.0])

    breakdown = {
        "work": np.array([0.0, 90.0, 95.0, 100.0, 105.0]),
        "pension": np.array([0.0, 5.0, 5.0, 5.0, 5.0]),
        "annuity": np.array([0.0, 2.0, 2.0, 2.0, 2.0]),
        "ss": np.array([0.0, 1.0, 2.0, 3.0, 4.0]),
        "special_income": np.array([0.0, 4.0, 4.0, 4.0, 4.0]),
        "rmd": np.array([0.0, 0.0, 1.0, 1.0, 1.0]),
        "withdrawal": np.array([0.0, 7.0, 8.0, 9.0, 10.0]),
        "bond_interest": np.array([0.0, 0.5, 0.5, 0.5, 0.5]),
        "cash_interest": np.array([0.0, 0.2, 0.2, 0.2, 0.2]),
        "qualified_dividends": np.array([0.0, 0.3, 0.3, 0.3, 0.3]),
    }

    pipeline_payload = {
        "years": years,
        "years_list": years_list,
        "net_profit": net_profit,
        "net_income": net_income,
        "breakdown_by_class": breakdown,
        "taxes": taxes,
        "expense_amt": expense_amt,
    }

    captured = {}

    def fake_run_pipeline(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config, force_num_sims):
        assert force_num_sims == 1
        return pipeline_payload

    def fake_plot_yearly_income(
        years_to_simulate,
        net_profit,
        net_income,
        breakdown,
        taxes,
        expenses,
        husband,
        wife,
        sim_config,
    ):
        captured["years_to_simulate"] = years_to_simulate
        captured["net_profit"] = net_profit
        captured["net_income"] = net_income
        captured["breakdown"] = breakdown
        captured["taxes"] = taxes
        captured["expenses"] = expenses
        captured["husband"] = husband
        captured["wife"] = wife
        captured["sim_config"] = sim_config

    monkeypatch.setattr(run_sim_income, "run_pipeline", fake_run_pipeline)
    monkeypatch.setattr(run_sim_income, "plot_yearly_income", fake_plot_yearly_income)

    husband = object()
    wife = object()
    sim_config = type(
        "SimConfig",
        (),
        {
            "output_csv": "Do Not Output",
            "sim_type": "cashflow_sim",
        },
    )()

    run_sim_income.run_sim_income(
        husband_portfolio=None,
        wife_portfolio=None,
        husband=husband,
        wife=wife,
        expenses=None,
        sim_config=sim_config,
    )

    assert captured["years_to_simulate"] == pipeline_payload["years"]
    np.testing.assert_array_equal(captured["net_profit"], pipeline_payload["net_profit"])

    expected_plot_income = (
        breakdown["work"]
        + breakdown["pension"]
        + breakdown["annuity"]
        + breakdown["ss"]
        + breakdown["special_income"]
        + breakdown["rmd"]
        + breakdown["withdrawal"]
        + breakdown["bond_interest"]
        + breakdown["cash_interest"]
        + breakdown["qualified_dividends"]
    )

    np.testing.assert_array_equal(captured["net_income"], expected_plot_income)    
    np.testing.assert_array_equal(captured["taxes"], pipeline_payload["taxes"])
    np.testing.assert_array_equal(captured["expenses"], pipeline_payload["expense_amt"])

    expected_plot_breakdown = {
        "income": (
            breakdown["work"]
            + breakdown["pension"]
            + breakdown["annuity"]
            + breakdown["ss"]
            + breakdown["special_income"]
        ),
        "rmd": breakdown["rmd"],
        "withdrawal": breakdown["withdrawal"],
        "bond_interest": breakdown["bond_interest"],
        "cash_interest": breakdown["cash_interest"],
        "qualified_dividends": breakdown["qualified_dividends"],
    }

    assert set(captured["breakdown"]) == set(expected_plot_breakdown)

    for key, expected in expected_plot_breakdown.items():
        np.testing.assert_array_equal(captured["breakdown"][key], expected)

    assert captured["husband"] is husband
    assert captured["wife"] is wife
    assert captured["sim_config"] is sim_config