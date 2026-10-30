from __future__ import annotations

import pytest


class _ModeVar:
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value


@pytest.fixture
def dummy_gui():
    from src.warpsimlab.gui import gui_run as mod

    class DummyGUI(mod.PortfolioSimulatorGUI_RunMixin):
        pass

    inst = DummyGUI()

    inst.husband = object()
    inst.wife = object()
    inst.husband_portfolio = object()
    inst.wife_portfolio = object()
    inst.expensesDict = object()
    inst.simulation_controls = {"second_person_enabled": True}
    inst.mode_var = type("_ModeVar", (), {"get": lambda self: "Advanced"})()

    return inst


@pytest.mark.parametrize(
    "sim_type",
    [
        "cashflow_sim",
        "operating_balance_sim",
        "portfolio_sim",
        "summary_sim",
    ],
)
def test_run_simulation_from_gui(monkeypatch, dummy_gui, sim_type):
    from src.warpsimlab.gui import gui_run as mod

    called = {}

    def fake_run_simulation(**kwargs):
        called["kwargs"] = kwargs

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "commit_pending_gui_edits",
        lambda self: True,
    )

    monkeypatch.setattr(mod, "run_simulation", fake_run_simulation)

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "_person_for_sim",
        lambda self, p: f"PERSON_{id(p)}",
    )

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "_portfolio_for_sim",
        lambda self, p: f"PORT_{id(p)}",
    )

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "build_simulation_from_gui",
        lambda self, sim_type=None: f"SIMCFG_{sim_type}",
    )

    mod.PortfolioSimulatorGUI_RunMixin.run_simulation_from_gui(dummy_gui, sim_type=sim_type)

    assert "kwargs" in called
    assert called["kwargs"]["sim_config"] == f"SIMCFG_{sim_type}"
    assert called["kwargs"]["expenses"] is dummy_gui.expensesDict
    assert called["kwargs"]["husband"] == f"PERSON_{id(dummy_gui.husband)}"
    assert called["kwargs"]["wife"] == f"PERSON_{id(dummy_gui.wife)}"


def test_run_simulation_without_second_person(monkeypatch, dummy_gui):
    from src.warpsimlab.gui import gui_run as mod

    dummy_gui.simulation_controls["second_person_enabled"] = False

    called = {}

    def fake_run_simulation(**kwargs):
        called["kwargs"] = kwargs

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "commit_pending_gui_edits",
        lambda self: True,
    )

    monkeypatch.setattr(mod, "run_simulation", fake_run_simulation)

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "_person_for_sim",
        lambda self, p: f"PERSON_{id(p)}",
    )

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "_portfolio_for_sim",
        lambda self, p: f"PORT_{id(p)}",
    )

    monkeypatch.setattr(
        mod.PortfolioSimulatorGUI_RunMixin,
        "build_simulation_from_gui",
        lambda self, sim_type=None: f"SIMCFG_{sim_type}",
    )

    mod.PortfolioSimulatorGUI_RunMixin.run_simulation_from_gui(dummy_gui, sim_type="cashflow_sim")

    assert called["kwargs"]["wife"] is None
    assert called["kwargs"]["wife_portfolio"] is None


@pytest.mark.parametrize("mode", ["Basic", "Advanced"])
def test_person_and_portfolio_conversion_isolated_and_honors_visible_fields(dummy_gui, scenario_builders, mode):
    dummy_gui.mode_var = _ModeVar(mode)
    person = scenario_builders.Person(age=60, retire_age=65, income=100000, ss=24000, ss_age=70,
        pension=2000, annuity=3000, annual_401k_contribution=10000, annual_hsa_contribution=4000,
        medicare_annual_cost=3000, modeled_death_age=90)
    portfolio = scenario_builders.Portfolio(equity_pre=100, equity_post=200, cash_post=300,
        equity_roth=400, hsa_equity=500, real_estate=1000)
    before_person, before_portfolio = vars(person).copy(), vars(portfolio).copy()
    converted_person = dummy_gui._person_for_sim(person)
    converted_portfolio = dummy_gui._portfolio_for_sim(portfolio)
    assert converted_person is not person and converted_portfolio is not portfolio
    assert vars(person) == before_person and vars(portfolio) == before_portfolio
    assert converted_person.income == 100000
    assert converted_person.modeled_death_age == 90
    assert converted_person.medicare_annual_cost == 3000
    assert converted_portfolio.cash_post == 300
    if mode == "Basic":
        assert converted_person.ss_age == 65
        assert converted_person.pension == converted_person.annuity == 0
        assert converted_person.annual_401k_contribution == converted_person.annual_hsa_contribution == 0
        assert sum(vars(converted_portfolio).values()) == 300
    else:
        assert converted_person.ss_age == 70
        assert converted_person.pension == 2000
        assert converted_person.annual_hsa_contribution == 4000
        assert vars(converted_portfolio) == before_portfolio


@pytest.mark.parametrize("sim_type,key", [("summary_report", "executive_summary"), ("year_by_year_report", "year_by_year_details"),
    ("tax_report", "tax_report"), ("monte_carlo_risk_report", "monte_carlo_risk"),
    ("historical_window_risk_report", "historical_window_risk"), ("spending_comparison_report", "spending_comparison"),
    ("asset_allocation_comparison_report", "asset_allocation_comparison"), ("retirement_ss_comparison_report", "retirement_ss_comparison")])
def test_report_options_are_independent_copies(dummy_gui, sim_type, key):
    dummy_gui.report_options = {key: {"sections": ["summary"]}}
    options = dummy_gui._build_report_options(sim_type)
    options["sections"].append("details")
    assert dummy_gui.report_options[key]["sections"] == ["summary"]
    assert dummy_gui._build_report_options("portfolio_sim") == {}
