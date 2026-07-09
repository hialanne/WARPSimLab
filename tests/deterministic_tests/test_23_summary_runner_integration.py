import numpy as np

from src.warpsimlab.sim import run_sim_summary


def test_run_sim_summary_sends_exact_summary_payload_to_ui_layer(monkeypatch):
    summary_results = {
        "year": np.array([2025.0, 2026.0, 2027.0]),
        "total_assets": np.array([100.0, 110.0, 120.0]),
        "pre_tax_assets": np.array([60.0, 65.0, 70.0]),
        "post_tax_assets": np.array([40.0, 45.0, 50.0]),
        "real_estate": np.array([5.0, 5.0, 5.0]),
        "gross_income": np.array([50.0, 51.0, 52.0]),
        "net_income": np.array([40.0, 41.0, 42.0]),
        "taxes": np.array([10.0, 10.0, 10.0]),
        "tax_bracket": np.array([0.22, 0.22, 0.22]),
        "expenses": np.array([35.0, 36.0, 37.0]),
        "net_cash_flow": np.array([5.0, 5.0, 5.0]),
        "wages": np.array([45.0, 46.0, 47.0]),
        "rmd": np.array([0.0, 0.0, 1.0]),
        "ira_401k": np.array([2.0, 2.0, 2.0]),
        "social_security": np.array([0.0, 0.0, 0.0]),
        "pensions": np.array([0.0, 0.0, 0.0]),
        "annuities": np.array([0.0, 0.0, 0.0]),
        "withdrawal": np.array([0.0, 0.0, 0.0]),
        "fund_expenses": np.array([1.0, 1.0, 1.0]),
        "bond_interest": np.array([0.5, 0.5, 0.5]),
        "cash_interest": np.array([0.2, 0.2, 0.2]),
        "qualified_dividends": np.array([0.3, 0.3, 0.3]),
    }

    pipeline_payload = {"summary_results": summary_results}
    captured = {}

    def fake_run_pipeline(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config, force_num_sims):
        assert force_num_sims == 1
        return pipeline_payload

    class FakeSummaryDialog:
        def __init__(self, results, husband, wife, sim_config, title="Summary"):
            captured["results"] = results
            captured["husband"] = husband
            captured["wife"] = wife
            captured["sim_config"] = sim_config
            captured["title"] = title

    monkeypatch.setattr(run_sim_summary, "run_pipeline", fake_run_pipeline)
    monkeypatch.setattr(run_sim_summary, "SummaryDialog", FakeSummaryDialog)

    husband = object()
    wife = object()
    sim_config = type("SimConfig", (), {"output_csv": "Do Not Output"})()

    returned = run_sim_summary.run_sim_summary(
        husband_portfolio=None,
        wife_portfolio=None,
        husband=husband,
        wife=wife,
        expenses=None,
        sim_config=sim_config,
    )

    assert captured["results"] is summary_results
    assert captured["husband"] is husband
    assert captured["wife"] is wife
    assert captured["sim_config"] is sim_config
    assert captured["title"] == "Simulation Summary"
    assert returned is summary_results