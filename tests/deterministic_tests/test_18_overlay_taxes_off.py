import numpy as np

from src.warpsimlab.sim import simulation


def test_overlay_taxes_off_attaches_median_without_taxes_and_exceeds_taxed_baseline(monkeypatch):
    years_to_simulate = 3
    baseline_total_assets = np.array([[100.0, 95.0, 90.0, 85.0]])
    overlay_total_assets = np.array([[100.0, 101.0, 103.0, 106.0]])

    def fake_simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        num_sims,
    ):
        zeros = np.zeros((1, years_to_simulate + 1))

        results = {
            "year": np.array([[2025.0, 2026.0, 2027.0, 2028.0]]),
            "total_assets": baseline_total_assets.copy(),
            "pre_tax_assets": np.array([[60.0, 57.0, 54.0, 51.0]]),
            "post_tax_assets": np.array([[40.0, 38.0, 36.0, 34.0]]),
            "roth_assets": zeros.copy(),
            "hsa_assets": zeros.copy(),
            "cash": np.array([[10.0, 10.0, 10.0, 10.0]]),
            "bonds": np.array([[20.0, 19.0, 18.0, 17.0]]),
            "real_estate": zeros.copy(),
            "gross_income": np.array([[50.0, 50.0, 50.0, 50.0]]),
            "net_income": np.array([[40.0, 40.0, 40.0, 40.0]]),
            "net_profit": np.array([[5.0, 4.0, 3.0, 2.0]]),
            "taxes": np.array([[10.0, 11.0, 12.0, 13.0]]),
            "payroll_tax": zeros.copy(),
            "social_security_payroll_tax": zeros.copy(),
            "medicare_tax": zeros.copy(),
            "additional_medicare_tax": zeros.copy(),
            "tax_bracket": np.array([[0.22, 0.22, 0.22, 0.22]]),
            "federal_ordinary_tax": zeros.copy(),
            "federal_qualified_dividend_tax": zeros.copy(),
            "state_income_tax": zeros.copy(),
            "emergency_pre_tax_used": zeros.copy(),
            "final_tax_delta": zeros.copy(),
            "final_tax_delta_deducted": zeros.copy(),
            "final_tax_delta_uncovered": zeros.copy(),
            "roth_withdrawals": zeros.copy(),
            "hsa_withdrawals": zeros.copy(),
            "expense_amt": np.array([[35.0, 36.0, 37.0, 38.0]]),
            "ira_401k": zeros.copy(),
            "roth_ira_contributions": zeros.copy(),
            "roth_workplace_contributions": zeros.copy(),
            "roth_conversions": zeros.copy(),
            "roth_total_flows": zeros.copy(),
            "fund_expenses": np.array([[1.0, 1.0, 1.0, 1.0]]),
            "breakdown_by_class": {
                "work": np.array([[50.0, 50.0, 50.0, 50.0]]),
                "pension": zeros.copy(),
                "annuity": zeros.copy(),
                "ss": zeros.copy(),
                "rmd": zeros.copy(),
                "withdrawal": zeros.copy(),
                "bond_interest": zeros.copy(),
                "cash_interest": zeros.copy(),
                "qualified_dividends": zeros.copy(),
                "special_income": zeros.copy(),
            },
        }

        if num_sims == 1 and sim_config.calculate_income_taxes is False:
            results["total_assets"] = overlay_total_assets.copy()

        return results

    monkeypatch.setattr(simulation, "simulate_yearly_portfolios", fake_simulate_yearly_portfolios)

    class SimConfig:
        pass

    sim_config = SimConfig()
    sim_config.years_to_simulate = years_to_simulate
    sim_config.inflation_rate = 0.0
    sim_config.num_sims = 25
    sim_config.subplot_mode = "default"
    sim_config.include_realestate = False
    sim_config.overlay_tax_impacts = True
    sim_config.overlay_fund_expense_impacts = False
    sim_config.calculate_income_taxes = True
    sim_config.use_fund_expenses = True
    sim_config.show_simulated_shortfall_rate = False

    result = simulation.run_pipeline(
        husband_portfolio=None,
        wife_portfolio=None,
        husband=None,
        wife=None,
        expenses=None,
        sim_config=sim_config,
    )

    plot_data = result["portfolio_plot_data"]
    baseline = plot_data.percentiles["median"]

    assert hasattr(plot_data, "median_without_taxes")
    assert plot_data.median_without_taxes is not None
    np.testing.assert_allclose(plot_data.median_without_taxes, overlay_total_assets[0])
    assert np.all(plot_data.median_without_taxes >= baseline)
    assert np.any(plot_data.median_without_taxes > baseline)

    assert sim_config.calculate_income_taxes is True
    assert sim_config.use_fund_expenses is True