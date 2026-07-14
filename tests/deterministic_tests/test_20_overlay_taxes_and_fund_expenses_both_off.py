import numpy as np

from src.warpsimlab.sim import simulation


def test_overlay_taxes_and_fund_expenses_both_off_attaches_combined_and_combined_is_highest(monkeypatch):
    years_to_simulate = 3
    baseline_total_assets = np.array([[100.0, 90.0, 80.0, 70.0]])
    no_taxes_assets = np.array([[100.0, 95.0, 89.0, 84.0]])
    no_fees_assets = np.array([[100.0, 93.0, 86.0, 79.0]])
    no_taxes_no_fees_assets = np.array([[100.0, 98.0, 94.0, 91.0]])

    def fake_simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
        num_sims,
    ):
        total_assets = baseline_total_assets.copy()

        if num_sims == 1 and (sim_config.calculate_income_taxes is False) and (sim_config.use_fund_expenses is False):
            total_assets = no_taxes_no_fees_assets.copy()
        elif num_sims == 1 and sim_config.calculate_income_taxes is False:
            total_assets = no_taxes_assets.copy()
        elif num_sims == 1 and sim_config.use_fund_expenses is False:
            total_assets = no_fees_assets.copy()

        zeros = np.zeros((1, years_to_simulate + 1))

        return {
            "year": np.array([[2040.0, 2041.0, 2042.0, 2043.0]]),
            "total_assets": total_assets,
            "pre_tax_assets": np.array([[60.0, 55.0, 50.0, 45.0]]),
            "post_tax_assets": np.array([[40.0, 35.0, 30.0, 25.0]]),
            "roth_assets": zeros.copy(),
            "hsa_assets": zeros.copy(),
            "cash": np.array([[10.0, 9.0, 8.0, 7.0]]),
            "bonds": np.array([[20.0, 18.0, 16.0, 14.0]]),
            "real_estate": zeros.copy(),
            "gross_income": np.array([[60.0, 60.0, 60.0, 60.0]]),
            "net_income": np.array([[48.0, 48.0, 48.0, 48.0]]),
            "net_profit": np.array([[8.0, 7.0, 6.0, 5.0]]),
            "taxes": np.array([[12.0, 12.0, 12.0, 12.0]]),
            "payroll_tax": zeros.copy(),
            "social_security_payroll_tax": zeros.copy(),
            "medicare_tax": zeros.copy(),
            "additional_medicare_tax": zeros.copy(),
            "tax_bracket": np.array([[0.24, 0.24, 0.24, 0.24]]),
            "federal_ordinary_tax": zeros.copy(),
            "federal_qualified_dividend_tax": zeros.copy(),
            "state_income_tax": zeros.copy(),
            "emergency_pre_tax_used": zeros.copy(),
            "final_tax_delta": zeros.copy(),
            "final_tax_delta_deducted": zeros.copy(),
            "final_tax_delta_uncovered": zeros.copy(),
            "roth_withdrawals": zeros.copy(),
            "hsa_withdrawals": zeros.copy(),
            "expense_amt": np.array([[40.0, 41.0, 42.0, 43.0]]),
            "ira_401k": zeros.copy(),
            "roth_ira_contributions": zeros.copy(),
            "roth_workplace_contributions": zeros.copy(),
            "roth_conversions": zeros.copy(),
            "roth_total_flows": zeros.copy(),
            "fund_expenses": np.array([[1.0, 1.0, 1.0, 1.0]]),
            "breakdown_by_class": {
                "work": np.array([[60.0, 60.0, 60.0, 60.0]]),
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

    monkeypatch.setattr(simulation, "simulate_yearly_portfolios", fake_simulate_yearly_portfolios)

    class SimConfig:
        pass

    sim_config = SimConfig()
    sim_config.years_to_simulate = years_to_simulate
    sim_config.inflation_rate = 0.0
    sim_config.num_sims = 50
    sim_config.subplot_mode = "default"
    sim_config.include_realestate = False
    sim_config.overlay_tax_impacts = True
    sim_config.overlay_fund_expense_impacts = True
    sim_config.calculate_income_taxes = True
    sim_config.use_fund_expenses = True

    # REQUIRED (same fix as tests 18 & 19)
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

    assert plot_data.median_without_taxes is not None
    assert plot_data.median_without_fund_expenses is not None
    assert plot_data.median_without_taxes_or_fund_expenses is not None

    np.testing.assert_allclose(plot_data.median_without_taxes, no_taxes_assets[0])
    np.testing.assert_allclose(plot_data.median_without_fund_expenses, no_fees_assets[0])
    np.testing.assert_allclose(plot_data.median_without_taxes_or_fund_expenses, no_taxes_no_fees_assets[0])

    assert np.all(plot_data.median_without_taxes_or_fund_expenses >= plot_data.median_without_taxes)
    assert np.all(plot_data.median_without_taxes_or_fund_expenses >= plot_data.median_without_fund_expenses)

    assert sim_config.calculate_income_taxes is True
    assert sim_config.use_fund_expenses is True