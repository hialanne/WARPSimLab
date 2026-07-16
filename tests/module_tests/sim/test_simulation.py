from __future__ import annotations

from dataclasses import dataclass
from types import ModuleType
from typing import Any
import sys

import numpy as np
import pytest


@dataclass
class DummySimConfig:
    years_to_simulate: int = 3
    num_sims: int = 25
    subplot_mode: str = "monte_carlo"
    inflation_rate: float = 0.0
    include_realestate: bool = True

    overlay_tax_impacts: bool = False
    overlay_fund_expense_impacts: bool = False
    calculate_income_taxes: bool = True
    use_fund_expenses: bool = True

    show_simulated_shortfall_rate: bool = False
    sim_type: str = "portfolio_sim"


class DummyPerson:
    pass


class DummyPortfolio:
    pass


class DummyExpenses:
    pass


@dataclass
class FakePortfolioPlotData:
    years: Any
    percentiles: Any
    cash: Any = None
    bonds: Any = None
    realestate: Any = None
    pre_tax_assets: Any = None
    post_tax_assets: Any = None
    roth_assets: Any = None
    hsa_assets: Any = None
    raw_total_assets: Any = None
    simulated_shortfall_rate: Any = None


def _core_for_extracts() -> dict:
    return {
        "net_income": np.array([[100.0, 101.0, 102.0, 103.0]]),
        "net_profit": np.array([[1.0, 2.0, 3.0, 4.0]]),
        "breakdown_by_class": {
            "work": np.array([[10.0, 11.0, 12.0, 13.0]]),
            "pension": np.array([[0.0, 0.0, 0.0, 0.0]]),
            "annuity": np.array([[0.0, 0.0, 0.0, 0.0]]),
            "ss": np.array([[5.0, 5.0, 5.0, 5.0]]),
            "rmd": np.array([[0.0, 0.0, 0.0, 0.0]]),
            "special_income": np.array([[4.0, 4.0, 4.0, 4.0]]),
            "withdrawal": np.array([[1.0, 1.0, 1.0, 1.0]]),
            "bond_interest": np.array([[2.0, 2.0, 2.0, 2.0]]),
            "cash_interest": np.array([[3.0, 3.0, 3.0, 3.0]]),
            "qualified_dividends": np.array([[4.0, 4.0, 4.0, 4.0]]),
        },
        "taxes": np.array([[7.0, 7.0, 8.0, 9.0]]),
        "payroll_tax": np.array([[2.0, 2.0, 2.0, 2.0]]),
        "social_security_payroll_tax": np.array([[1.0, 1.0, 1.0, 1.0]]),
        "medicare_tax": np.array([[0.8, 0.8, 0.8, 0.8]]),
        "additional_medicare_tax": np.array([[0.2, 0.2, 0.2, 0.2]]),
        "expense_amt": np.array([[50.0, 51.0, 52.0, 53.0]]),
        "year": np.array([[0.0, 1.0, 2.0, 3.0]]),
        "total_assets": np.array([[1000.0, 1100.0, 1200.0, 1300.0]]),
        "pre_tax_assets": np.array([[600.0, 650.0, 700.0, 750.0]]),
        "post_tax_assets": np.array([[400.0, 450.0, 500.0, 550.0]]),
        "roth_assets": np.array([[100.0, 105.0, 110.0, 115.0]]),
        "hsa_assets": np.array([[50.0, 55.0, 60.0, 65.0]]),

        "federal_ordinary_tax": np.array([[4.0, 4.0, 5.0, 5.0]]),
        "federal_qualified_dividend_tax": np.array([[0.5, 0.5, 0.6, 0.6]]),
        "state_income_tax": np.array([[1.0, 1.0, 1.2, 1.2]]),

        "emergency_pre_tax_used": np.array([[0.0, 0.0, 0.0, 0.0]]),

        "final_tax_delta": np.array([[0.0, 0.0, 0.0, 0.0]]),
        "final_tax_delta_deducted": np.array([[0.0, 0.0, 0.0, 0.0]]),
        "final_tax_delta_uncovered": np.array([[0.0, 0.0, 0.0, 0.0]]),

        "roth_withdrawals": np.array([[0.0, 0.0, 0.0, 0.0]]),
        "hsa_withdrawals": np.array([[0.0, 0.0, 0.0, 0.0]]),
        "real_estate": np.array([[0.0, 10.0, 20.0, 30.0]]),
        "gross_income": np.array([[120.0, 121.0, 122.0, 123.0]]),
        "tax_bracket": np.array([[0.10, 0.10, 0.12, 0.12]]),
        "ira_401k": np.array([[0.0, 0.0, 0.0, 0.0]]),
        "employee_401k_contributions": np.array(
            [[0.0, 10.0, 20.0, 30.0]]
        ),

        "roth_ira_contributions": np.array(
            [[0.0, 1.0, 2.0, 3.0]]
        ),
        "roth_workplace_contributions": np.array(
            [[0.0, 4.0, 5.0, 6.0]]
        ),
        "roth_conversions": np.array(
            [[0.0, 7.0, 8.0, 9.0]]
        ),
        "roth_total_flows": np.array(
            [[0.0, 12.0, 15.0, 18.0]]
        ),

        "fund_expenses": np.array([[0.0, 1.0, 1.0, 2.0]]),

        "cash": np.array([[100.0, 110.0, 120.0, 130.0]]),
        "bonds": np.array([[200.0, 210.0, 220.0, 230.0]]),
    }



def test_extract_income_single_run_shapes_and_values():
    from src.warpsimlab.sim import simulation as mod

    core = _core_for_extracts()
    net_income, net_profit, breakdown, taxes, expense_amt = mod._extract_income_single_run(core)

    np.testing.assert_allclose(net_income, core["net_income"][0])
    np.testing.assert_allclose(net_profit, core["net_profit"][0])
    np.testing.assert_allclose(taxes, core["taxes"][0])
    np.testing.assert_allclose(expense_amt, core["expense_amt"][0])

    assert set(breakdown.keys()) == set(core["breakdown_by_class"].keys())
    for key, value in breakdown.items():
        np.testing.assert_allclose(value, core["breakdown_by_class"][key][0])



def test_extract_summary_single_run_builds_expected_keys():
    from src.warpsimlab.sim import simulation as mod

    core = _core_for_extracts()
    summary = mod._extract_summary_single_run(core, simulated_shortfall_rate=12.5)

    np.testing.assert_allclose(summary["year"], core["year"][0])
    np.testing.assert_allclose(summary["total_assets"], core["total_assets"][0])
    np.testing.assert_allclose(summary["pre_tax_assets"], core["pre_tax_assets"][0])
    np.testing.assert_allclose(summary["post_tax_assets"], core["post_tax_assets"][0])
    np.testing.assert_allclose(summary["real_estate"], core["real_estate"][0])
    np.testing.assert_allclose(summary["gross_income"], core["gross_income"][0])
    np.testing.assert_allclose(summary["net_income"], core["net_income"][0])
    np.testing.assert_allclose(summary["taxes"], core["taxes"][0])
    np.testing.assert_allclose(summary["tax_bracket"], core["tax_bracket"][0])
    np.testing.assert_allclose(summary["expenses"], core["expense_amt"][0])
    np.testing.assert_allclose(summary["net_cash_flow"], core["net_profit"][0])
    np.testing.assert_allclose(summary["wages"], core["breakdown_by_class"]["work"][0])
    np.testing.assert_allclose(summary["rmd"], core["breakdown_by_class"]["rmd"][0])
    np.testing.assert_allclose(
        summary["special_income"],
        core["breakdown_by_class"]["special_income"][0],
    )
    np.testing.assert_allclose(
        summary["employee_401k_contributions"],
        core["employee_401k_contributions"][0],
    )
    np.testing.assert_allclose(
        summary["roth_ira_contributions"],
        core["roth_ira_contributions"][0],
    )
    np.testing.assert_allclose(
        summary["roth_workplace_contributions"],
        core["roth_workplace_contributions"][0],
    )
    np.testing.assert_allclose(
        summary["roth_conversions"],
        core["roth_conversions"][0],
    )
    np.testing.assert_allclose(
        summary["roth_total_flows"],
        core["roth_total_flows"][0],
    )
    np.testing.assert_allclose(summary["ira_401k"], core["ira_401k"][0])
    np.testing.assert_allclose(summary["social_security"], core["breakdown_by_class"]["ss"][0])
    np.testing.assert_allclose(summary["pensions"], core["breakdown_by_class"]["pension"][0])
    np.testing.assert_allclose(summary["annuities"], core["breakdown_by_class"]["annuity"][0])
    np.testing.assert_allclose(summary["withdrawal"], core["breakdown_by_class"]["withdrawal"][0])
    np.testing.assert_allclose(summary["fund_expenses"], core["fund_expenses"][0])
    np.testing.assert_allclose(summary["bond_interest"], core["breakdown_by_class"]["bond_interest"][0])
    np.testing.assert_allclose(summary["cash_interest"], core["breakdown_by_class"]["cash_interest"][0])
    np.testing.assert_allclose(summary["qualified_dividends"], core["breakdown_by_class"]["qualified_dividends"][0])
    np.testing.assert_allclose(summary["payroll_tax"],core["payroll_tax"][0])
    np.testing.assert_allclose(summary["social_security_payroll_tax"],core["social_security_payroll_tax"][0])
    np.testing.assert_allclose(summary["medicare_tax"],core["medicare_tax"][0])
    np.testing.assert_allclose(summary["additional_medicare_tax"],core["additional_medicare_tax"][0])
    np.testing.assert_allclose(summary["roth_assets"], core["roth_assets"][0])
    np.testing.assert_allclose(summary["hsa_assets"], core["hsa_assets"][0])

    np.testing.assert_allclose(summary["federal_ordinary_tax"], core["federal_ordinary_tax"][0])
    np.testing.assert_allclose(
        summary["federal_qualified_dividend_tax"],
        core["federal_qualified_dividend_tax"][0],
    )
    np.testing.assert_allclose(summary["state_income_tax"], core["state_income_tax"][0])

    np.testing.assert_allclose(summary["emergency_pre_tax_used"], core["emergency_pre_tax_used"][0])

    np.testing.assert_allclose(summary["final_tax_delta"], core["final_tax_delta"][0])
    np.testing.assert_allclose(summary["final_tax_delta_deducted"], core["final_tax_delta_deducted"][0])
    np.testing.assert_allclose(summary["final_tax_delta_uncovered"], core["final_tax_delta_uncovered"][0])

    np.testing.assert_allclose(summary["roth_withdrawals"], core["roth_withdrawals"][0])
    np.testing.assert_allclose(summary["hsa_withdrawals"], core["hsa_withdrawals"][0])

    assert summary["simulated_shortfall_rate"] == 12.5



def test_build_portfolio_plot_data_sub_categories_include_realestate_true(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    core = _core_for_extracts()
    sim_config = DummySimConfig(years_to_simulate=3, subplot_mode="sub_categories", include_realestate=True)

    captured = {"percentiles_args": None, "optional_calls": [], "ppd_kwargs": None}

    def fake_compute_portfolio_statistics(total_assets, years, inflation_rate):
        captured["percentiles_args"] = (total_assets, years, inflation_rate)
        return {"median": [1, 2, 3, 4]}

    def fake_optional_stats(arr, years, inflation_rate, *, enabled):
        captured["optional_calls"].append((arr, years, inflation_rate, enabled))
        return {"median": [9, 9, 9, 9], "src": id(arr)}

    @dataclass
    class CapturingPortfolioPlotData(FakePortfolioPlotData):
        def __post_init__(self):
            captured["ppd_kwargs"] = {
                "years": self.years,
                "percentiles": self.percentiles,
                "cash": self.cash,
                "bonds": self.bonds,
                "realestate": self.realestate,
                "pre_tax_assets": self.pre_tax_assets,
                "post_tax_assets": self.post_tax_assets,
                "raw_total_assets": self.raw_total_assets,
            }

    monkeypatch.setattr(mod, "compute_portfolio_statistics", fake_compute_portfolio_statistics, raising=True)
    monkeypatch.setattr(mod, "optional_stats", fake_optional_stats, raising=True)
    monkeypatch.setattr(mod, "PortfolioPlotData", CapturingPortfolioPlotData, raising=True)

    ppd = mod._build_portfolio_plot_data(core, sim_config)

    assert np.all(ppd.years == np.arange(0, 4))
    assert captured["percentiles_args"][0] is core["total_assets"]
    assert captured["percentiles_args"][1] == 3
    assert captured["percentiles_args"][2] == sim_config.inflation_rate

    assert len(captured["optional_calls"]) == 3
    assert captured["optional_calls"][0][0] is core["cash"]
    assert captured["optional_calls"][1][0] is core["bonds"]
    assert captured["optional_calls"][2][0] is core["real_estate"]

    assert captured["ppd_kwargs"]["cash"] is not None
    assert captured["ppd_kwargs"]["bonds"] is not None
    assert captured["ppd_kwargs"]["realestate"] is not None
    assert captured["ppd_kwargs"]["pre_tax_assets"] is None
    assert captured["ppd_kwargs"]["post_tax_assets"] is None
    assert captured["ppd_kwargs"]["raw_total_assets"] is core["total_assets"]



def test_build_portfolio_plot_data_sub_categories_include_realestate_false_sets_zeros(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    core = _core_for_extracts()
    sim_config = DummySimConfig(years_to_simulate=3, subplot_mode="sub_categories", include_realestate=False)

    def fake_compute_portfolio_statistics(*args, **kwargs):
        return {"median": [0, 0, 0, 0]}

    def fake_optional_stats(arr, years, inflation_rate, *, enabled):
        return {"median": [1, 1, 1, 1]}

    monkeypatch.setattr(mod, "compute_portfolio_statistics", fake_compute_portfolio_statistics, raising=True)
    monkeypatch.setattr(mod, "optional_stats", fake_optional_stats, raising=True)
    monkeypatch.setattr(mod, "PortfolioPlotData", FakePortfolioPlotData, raising=True)

    ppd = mod._build_portfolio_plot_data(core, sim_config)

    assert isinstance(ppd.realestate, np.ndarray)
    np.testing.assert_allclose(ppd.realestate, np.zeros(4))
    assert ppd.raw_total_assets is core["total_assets"]



def test_build_portfolio_plot_data_pre_post_tax_realestate_optional(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    core = _core_for_extracts()
    sim_config = DummySimConfig(years_to_simulate=3, subplot_mode="pre_post_tax", include_realestate=False)

    def fake_compute_portfolio_statistics(*args, **kwargs):
        return {"median": [0, 0, 0, 0]}

    calls = []

    def fake_optional_stats(arr, years, inflation_rate, *, enabled):
        calls.append(arr)
        return {"median": [2, 2, 2, 2]}

    monkeypatch.setattr(mod, "compute_portfolio_statistics", fake_compute_portfolio_statistics, raising=True)
    monkeypatch.setattr(mod, "optional_stats", fake_optional_stats, raising=True)
    monkeypatch.setattr(mod, "PortfolioPlotData", FakePortfolioPlotData, raising=True)

    ppd = mod._build_portfolio_plot_data(core, sim_config)

    assert ppd.pre_tax_assets is not None
    assert ppd.post_tax_assets is not None
    assert ppd.realestate is None
    assert ppd.raw_total_assets is core["total_assets"]
    assert calls[0] is core["pre_tax_assets"]
    assert calls[1] is core["post_tax_assets"]



def test_run_overlay_total_assets_line_returns_first_sim_total_assets(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    overlay_core = _core_for_extracts()

    def fake_simulate_yearly_portfolios(*args, **kwargs):
        assert kwargs["num_sims"] == 1
        return overlay_core

    monkeypatch.setattr(mod, "simulate_yearly_portfolios", fake_simulate_yearly_portfolios, raising=True)

    out = mod._run_overlay_total_assets_line(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        DummySimConfig(),
    )

    np.testing.assert_allclose(out, overlay_core["total_assets"][0])



def test_calculate_shortfall_rate_from_total_assets_counts_any_non_positive_year():
    from src.warpsimlab.sim import simulation as mod

    total_assets = np.array(
        [
            [100.0, 50.0, 10.0, 1.0],
            [100.0, 0.0, 10.0, 1.0],
            [100.0, 50.0, -1.0, 1.0],
            [100.0, 50.0, 10.0, 1.0],
        ]
    )

    assert mod._calculate_shortfall_rate_from_total_assets(total_assets) == 50.0



def test_calculate_shortfall_rate_from_total_assets_requires_2d_input():
    from src.warpsimlab.sim import simulation as mod

    with pytest.raises(ValueError, match="Expected 2D total_assets array"):
        mod._calculate_shortfall_rate_from_total_assets(np.array([1.0, 2.0, 3.0]))



def test_compute_simulated_shortfall_rate_runs_monte_carlo_and_restores_subplot_mode(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    observed = {"subplot_mode_during_call": None, "num_sims": None}

    def fake_simulate_yearly_portfolios(*args, **kwargs):
        sim_config = args[5]
        observed["subplot_mode_during_call"] = sim_config.subplot_mode
        observed["num_sims"] = kwargs["num_sims"]
        return {
            "total_assets": np.array(
                [
                    [100.0, 50.0, 10.0, 1.0],
                    [100.0, 0.0, 10.0, 1.0],
                    [100.0, 50.0, -1.0, 1.0],
                    [100.0, 50.0, 10.0, 1.0],
                ]
            )
        }

    monkeypatch.setattr(mod, "simulate_yearly_portfolios", fake_simulate_yearly_portfolios, raising=True)

    sim_config = DummySimConfig(subplot_mode="pre_post_tax")
    rate = mod._compute_simulated_shortfall_rate(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
        num_sims=4,
    )

    assert rate == 50.0
    assert observed["subplot_mode_during_call"] == "monte_carlo"
    assert observed["num_sims"] == 4
    assert sim_config.subplot_mode == "pre_post_tax"



def test_compute_simulated_shortfall_rate_rejects_non_positive_num_sims():
    from src.warpsimlab.sim import simulation as mod

    with pytest.raises(ValueError, match="num_sims must be > 0"):
        mod._compute_simulated_shortfall_rate(
            DummyPortfolio(),
            DummyPortfolio(),
            DummyPerson(),
            DummyPerson(),
            DummyExpenses(),
            DummySimConfig(),
            num_sims=0,
        )



def test_run_pipeline_sim_count_policy_forces_one_when_not_monte_carlo(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    captured = {"num_sims": None}

    def fake_simulate_yearly_portfolios(*args, **kwargs):
        captured["num_sims"] = kwargs.get("num_sims")
        return _core_for_extracts()

    def fake_compute_portfolio_statistics(*args, **kwargs):
        return {"median": [0, 0, 0, 0]}

    monkeypatch.setattr(mod, "simulate_yearly_portfolios", fake_simulate_yearly_portfolios, raising=True)
    monkeypatch.setattr(mod, "compute_portfolio_statistics", fake_compute_portfolio_statistics, raising=True)
    monkeypatch.setattr(mod, "PortfolioPlotData", FakePortfolioPlotData, raising=True)

    sim_config = DummySimConfig(subplot_mode="pre_post_tax", num_sims=99)

    mod.run_pipeline(DummyPortfolio(), DummyPortfolio(), DummyPerson(), DummyPerson(), DummyExpenses(), sim_config)
    assert captured["num_sims"] == 1

    captured["num_sims"] = None
    mod.run_pipeline(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
        force_num_sims=7,
    )
    assert captured["num_sims"] == 1



def test_run_pipeline_uses_force_num_sims_when_monte_carlo(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    captured = {"num_sims": None}

    def fake_simulate_yearly_portfolios(*args, **kwargs):
        captured["num_sims"] = kwargs.get("num_sims")
        return _core_for_extracts()

    def fake_compute_portfolio_statistics(*args, **kwargs):
        return {"median": [0, 0, 0, 0]}

    monkeypatch.setattr(mod, "simulate_yearly_portfolios", fake_simulate_yearly_portfolios, raising=True)
    monkeypatch.setattr(mod, "compute_portfolio_statistics", fake_compute_portfolio_statistics, raising=True)
    monkeypatch.setattr(mod, "PortfolioPlotData", FakePortfolioPlotData, raising=True)

    sim_config = DummySimConfig(subplot_mode="monte_carlo", num_sims=123)

    mod.run_pipeline(DummyPortfolio(), DummyPortfolio(), DummyPerson(), DummyPerson(), DummyExpenses(), sim_config)
    assert captured["num_sims"] == 123

    mod.run_pipeline(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
        force_num_sims=7,
    )
    assert captured["num_sims"] == 7



def test_run_pipeline_returns_expected_top_level_views(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    def fake_simulate_yearly_portfolios(*args, **kwargs):
        return _core_for_extracts()

    def fake_compute_portfolio_statistics(*args, **kwargs):
        return {"median": [0, 0, 0, 0]}

    monkeypatch.setattr(mod, "simulate_yearly_portfolios", fake_simulate_yearly_portfolios, raising=True)
    monkeypatch.setattr(mod, "compute_portfolio_statistics", fake_compute_portfolio_statistics, raising=True)
    monkeypatch.setattr(mod, "PortfolioPlotData", FakePortfolioPlotData, raising=True)

    sim_config = DummySimConfig()

    result = mod.run_pipeline(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
    )

    assert result["years"] == 3
    np.testing.assert_allclose(result["years_list"], np.arange(0, 4))
    np.testing.assert_allclose(result["net_income"], _core_for_extracts()["net_income"][0])
    np.testing.assert_allclose(result["net_profit"], _core_for_extracts()["net_profit"][0])
    np.testing.assert_allclose(result["taxes"], _core_for_extracts()["taxes"][0])
    np.testing.assert_allclose(result["expense_amt"], _core_for_extracts()["expense_amt"][0])

    assert set(result["breakdown_by_class"].keys()) == set(_core_for_extracts()["breakdown_by_class"].keys())
    assert "summary_results" in result
    assert "portfolio_plot_data" in result
    assert "core" in result



def test_run_pipeline_monte_carlo_shortfall_rate_uses_existing_core(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    core = _core_for_extracts()
    core["total_assets"] = np.array(
        [
            [100.0, 50.0, 10.0, 1.0],
            [100.0, 0.0, 10.0, 1.0],
            [100.0, 50.0, -1.0, 1.0],
            [100.0, 50.0, 10.0, 1.0],
        ]
    )

    called = {"compute_simulated_shortfall_rate": 0}

    def fake_simulate_yearly_portfolios(*args, **kwargs):
        return core

    def fake_compute_portfolio_statistics(*args, **kwargs):
        return {"median": [0, 0, 0, 0]}

    def fake_compute_simulated_shortfall_rate(*args, **kwargs):
        called["compute_simulated_shortfall_rate"] += 1
        return 99.0

    monkeypatch.setattr(mod, "simulate_yearly_portfolios", fake_simulate_yearly_portfolios, raising=True)
    monkeypatch.setattr(mod, "compute_portfolio_statistics", fake_compute_portfolio_statistics, raising=True)
    monkeypatch.setattr(mod, "PortfolioPlotData", FakePortfolioPlotData, raising=True)
    monkeypatch.setattr(mod, "_compute_simulated_shortfall_rate", fake_compute_simulated_shortfall_rate, raising=True)

    sim_config = DummySimConfig(subplot_mode="monte_carlo", show_simulated_shortfall_rate=True, sim_type="portfolio_sim")

    result = mod.run_pipeline(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
    )

    assert called["compute_simulated_shortfall_rate"] == 0
    assert result["summary_results"]["simulated_shortfall_rate"] == 50.0
    assert result["portfolio_plot_data"].simulated_shortfall_rate == 50.0



def test_run_pipeline_non_monte_carlo_shortfall_rate_runs_secondary_sim_except_cashflow(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    called = {"compute_simulated_shortfall_rate": 0}

    def fake_simulate_yearly_portfolios(*args, **kwargs):
        return _core_for_extracts()

    def fake_compute_portfolio_statistics(*args, **kwargs):
        return {"median": [0, 0, 0, 0]}

    def fake_compute_simulated_shortfall_rate(*args, **kwargs):
        called["compute_simulated_shortfall_rate"] += 1
        assert kwargs["num_sims"] == 1000
        return 23.5

    monkeypatch.setattr(mod, "simulate_yearly_portfolios", fake_simulate_yearly_portfolios, raising=True)
    monkeypatch.setattr(mod, "compute_portfolio_statistics", fake_compute_portfolio_statistics, raising=True)
    monkeypatch.setattr(mod, "PortfolioPlotData", FakePortfolioPlotData, raising=True)
    monkeypatch.setattr(mod, "_compute_simulated_shortfall_rate", fake_compute_simulated_shortfall_rate, raising=True)

    sim_config = DummySimConfig(
        subplot_mode="pre_post_tax",
        show_simulated_shortfall_rate=True,
        sim_type="summary_sim",
    )

    result = mod.run_pipeline(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
    )

    assert called["compute_simulated_shortfall_rate"] == 1
    assert result["summary_results"]["simulated_shortfall_rate"] == 23.5
    assert result["portfolio_plot_data"].simulated_shortfall_rate == 23.5



def test_run_pipeline_cashflow_sim_does_not_compute_secondary_shortfall_rate(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    called = {"compute_simulated_shortfall_rate": 0}

    def fake_simulate_yearly_portfolios(*args, **kwargs):
        return _core_for_extracts()

    def fake_compute_portfolio_statistics(*args, **kwargs):
        return {"median": [0, 0, 0, 0]}

    def fake_compute_simulated_shortfall_rate(*args, **kwargs):
        called["compute_simulated_shortfall_rate"] += 1
        return 23.5

    monkeypatch.setattr(mod, "simulate_yearly_portfolios", fake_simulate_yearly_portfolios, raising=True)
    monkeypatch.setattr(mod, "compute_portfolio_statistics", fake_compute_portfolio_statistics, raising=True)
    monkeypatch.setattr(mod, "PortfolioPlotData", FakePortfolioPlotData, raising=True)
    monkeypatch.setattr(mod, "_compute_simulated_shortfall_rate", fake_compute_simulated_shortfall_rate, raising=True)

    sim_config = DummySimConfig(
        subplot_mode="pre_post_tax",
        show_simulated_shortfall_rate=True,
        sim_type="cashflow_sim",
    )

    result = mod.run_pipeline(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
    )

    assert called["compute_simulated_shortfall_rate"] == 0
    assert result["summary_results"]["simulated_shortfall_rate"] is None
    assert result["portfolio_plot_data"].simulated_shortfall_rate is None



def test_run_pipeline_overlay_tax_impacts_calls_overlay_with_flag_toggled_and_restored(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    observed = {"during": None}

    def fake_simulate_yearly_portfolios(*args, **kwargs):
        return _core_for_extracts()

    def fake_compute_portfolio_statistics(*args, **kwargs):
        return {"median": [0, 0, 0, 0]}

    def fake_run_overlay_total_assets_line(*args, **kwargs):
        sim_config = args[-1]
        observed["during"] = sim_config.calculate_income_taxes
        return np.array([111.0, 222.0, 333.0, 444.0])

    monkeypatch.setattr(mod, "simulate_yearly_portfolios", fake_simulate_yearly_portfolios, raising=True)
    monkeypatch.setattr(mod, "compute_portfolio_statistics", fake_compute_portfolio_statistics, raising=True)
    monkeypatch.setattr(mod, "PortfolioPlotData", FakePortfolioPlotData, raising=True)
    monkeypatch.setattr(mod, "_run_overlay_total_assets_line", fake_run_overlay_total_assets_line, raising=True)

    sim_config = DummySimConfig(subplot_mode="monte_carlo", overlay_tax_impacts=True, calculate_income_taxes=True)

    result = mod.run_pipeline(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
    )

    assert observed["during"] is False
    assert sim_config.calculate_income_taxes is True

    ppd = result["portfolio_plot_data"]
    assert hasattr(ppd, "median_without_taxes")
    np.testing.assert_allclose(ppd.median_without_taxes, np.array([111.0, 222.0, 333.0, 444.0]))



def test_run_pipeline_overlay_fund_expenses_impacts_calls_overlay_with_flag_toggled_and_restored(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    observed = {"during": None}

    def fake_simulate_yearly_portfolios(*args, **kwargs):
        return _core_for_extracts()

    def fake_compute_portfolio_statistics(*args, **kwargs):
        return {"median": [0, 0, 0, 0]}

    def fake_run_overlay_total_assets_line(*args, **kwargs):
        sim_config = args[-1]
        observed["during"] = sim_config.use_fund_expenses
        return np.array([9.0, 9.0, 9.0, 9.0])

    monkeypatch.setattr(mod, "simulate_yearly_portfolios", fake_simulate_yearly_portfolios, raising=True)
    monkeypatch.setattr(mod, "compute_portfolio_statistics", fake_compute_portfolio_statistics, raising=True)
    monkeypatch.setattr(mod, "PortfolioPlotData", FakePortfolioPlotData, raising=True)
    monkeypatch.setattr(mod, "_run_overlay_total_assets_line", fake_run_overlay_total_assets_line, raising=True)

    sim_config = DummySimConfig(subplot_mode="monte_carlo", overlay_fund_expense_impacts=True, use_fund_expenses=True)

    result = mod.run_pipeline(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
    )

    assert observed["during"] is False
    assert sim_config.use_fund_expenses is True

    ppd = result["portfolio_plot_data"]
    assert hasattr(ppd, "median_without_fund_expenses")
    np.testing.assert_allclose(ppd.median_without_fund_expenses, np.array([9.0, 9.0, 9.0, 9.0]))



def test_run_pipeline_overlay_combined_toggles_both_flags_and_restores(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    observed = {"tax": None, "fund": None}

    def fake_simulate_yearly_portfolios(*args, **kwargs):
        return _core_for_extracts()

    def fake_compute_portfolio_statistics(*args, **kwargs):
        return {"median": [0, 0, 0, 0]}

    def fake_run_overlay_total_assets_line(*args, **kwargs):
        sim_config = args[-1]
        observed["tax"] = sim_config.calculate_income_taxes
        observed["fund"] = sim_config.use_fund_expenses
        return np.array([1.0, 2.0, 3.0, 4.0])

    monkeypatch.setattr(mod, "simulate_yearly_portfolios", fake_simulate_yearly_portfolios, raising=True)
    monkeypatch.setattr(mod, "compute_portfolio_statistics", fake_compute_portfolio_statistics, raising=True)
    monkeypatch.setattr(mod, "PortfolioPlotData", FakePortfolioPlotData, raising=True)
    monkeypatch.setattr(mod, "_run_overlay_total_assets_line", fake_run_overlay_total_assets_line, raising=True)

    sim_config = DummySimConfig(
        subplot_mode="monte_carlo",
        overlay_tax_impacts=True,
        overlay_fund_expense_impacts=True,
        calculate_income_taxes=True,
        use_fund_expenses=True,
    )

    result = mod.run_pipeline(
        DummyPortfolio(),
        DummyPortfolio(),
        DummyPerson(),
        DummyPerson(),
        DummyExpenses(),
        sim_config,
    )

    assert observed["tax"] is False
    assert observed["fund"] is False
    assert sim_config.calculate_income_taxes is True
    assert sim_config.use_fund_expenses is True

    ppd = result["portfolio_plot_data"]
    assert hasattr(ppd, "median_without_taxes_or_fund_expenses")
    np.testing.assert_allclose(ppd.median_without_taxes_or_fund_expenses, np.array([1.0, 2.0, 3.0, 4.0]))



def test_run_simulation_dispatches_by_sim_type(monkeypatch):
    from src.warpsimlab.sim import simulation as mod

    pkg = "src.warpsimlab.sim"

    called = {"portfolio": 0, "income": 0, "summary": 0, "opbal": 0}

    def make_runner(name, ret):
        def runner(*args, **kwargs):
            called[name] += 1
            return ret
        return runner

    m_portfolio = ModuleType(f"{pkg}.run_sim_portfolio")
    m_portfolio.run_sim_portfolio = make_runner("portfolio", "P")

    m_income = ModuleType(f"{pkg}.run_sim_income")
    m_income.run_sim_income = make_runner("income", "I")

    m_summary = ModuleType(f"{pkg}.run_sim_summary")
    m_summary.run_sim_summary = make_runner("summary", "S")

    m_opbal = ModuleType(f"{pkg}.run_sim_operating_balance")
    m_opbal.run_sim_operating_balance = make_runner("opbal", "O")

    monkeypatch.setitem(sys.modules, f"{pkg}.run_sim_portfolio", m_portfolio)
    monkeypatch.setitem(sys.modules, f"{pkg}.run_sim_income", m_income)
    monkeypatch.setitem(sys.modules, f"{pkg}.run_sim_summary", m_summary)
    monkeypatch.setitem(sys.modules, f"{pkg}.run_sim_operating_balance", m_opbal)

    base_args = (DummyPortfolio(), DummyPortfolio(), DummyPerson(), DummyPerson(), DummyExpenses())

    cfg = DummySimConfig(sim_type="cashflow_sim")
    assert mod.run_simulation(*base_args, cfg) == "I"
    assert called["income"] == 1

    cfg = DummySimConfig(sim_type="operating_balance_sim")
    assert mod.run_simulation(*base_args, cfg) == "O"
    assert called["opbal"] == 1

    cfg = DummySimConfig(sim_type="portfolio_sim")
    assert mod.run_simulation(*base_args, cfg) == "P"
    assert called["portfolio"] == 1

    cfg = DummySimConfig(sim_type="summary_sim")
    assert mod.run_simulation(*base_args, cfg) == "S"
    assert called["summary"] == 1

    cfg = DummySimConfig(sim_type="unknown")
    assert mod.run_simulation(*base_args, cfg) is None
