# gui_scenarioState.py

import copy

from src.warpsimlab.gui.scenario.gui_scenarioSnapshots import ScenarioSnapshots
from src.warpsimlab.sim.simulation import run_pipeline
from src.warpsimlab.gui.gui_annotations import build_scenario_explorer_annotations
from dataclasses import dataclass


@dataclass
class ScenarioResultMetrics:
    ending_portfolio: float
    depletion_rate: float | None
    ending_cash_flow: float
    lifetime_funding_gap: float
    lifetime_taxes: float
    ending_pre_tax: float
    ending_after_tax: float
    ending_roth: float
    ending_hsa: float


@dataclass
class ScenarioAssumptions:
    husband_age: float
    husband_retire_age: float
    husband_ss_age: float
    wife_age: float | None
    wife_retire_age: float | None
    wife_ss_age: float | None
    inflation_rate: float
    fund_expense: float
    market_adjustment: float
    dynamic_label: str
    dynamic_value: float
    stock: float
    bonds: float
    cash: float


@dataclass
class ScenarioResultsViewModel:
    original_metrics: ScenarioResultMetrics
    changed_metrics: ScenarioResultMetrics
    original_assumptions: ScenarioAssumptions
    changed_assumptions: ScenarioAssumptions


def compute_portfolio_percentages(portfolio):
    husband = portfolio["husband"]
    wife = portfolio.get("wife")

    if wife:
        wife_equity_pre = wife.equity_pre
        wife_equity_post = wife.equity_post
        wife_bond_pre = wife.bond_pre
        wife_bond_post = wife.bond_post
        wife_cash_pre = wife.cash_pre
        wife_cash_post = wife.cash_post
    else:
        wife_equity_pre = 0
        wife_equity_post = 0
        wife_bond_pre = 0
        wife_bond_post = 0
        wife_cash_pre = 0
        wife_cash_post = 0

    total_equity = husband.equity_pre + husband.equity_post + wife_equity_pre + wife_equity_post
    total_bonds = husband.bond_pre + husband.bond_post + wife_bond_pre + wife_bond_post
    total_cash = husband.cash_pre + husband.cash_post + wife_cash_pre + wife_cash_post
    total_portfolio = total_equity + total_bonds + total_cash

    if total_portfolio > 0:
        stocks_pct = total_equity / total_portfolio * 100
        bonds_pct = total_bonds / total_portfolio * 100
        cash_pct = 100 - stocks_pct - bonds_pct
    else:
        stocks_pct, bonds_pct, cash_pct = 0, 0, 100

    return round(stocks_pct), round(bonds_pct), round(cash_pct)


class ScenarioSessionState:
    """Owns mutable simulation state for one Scenario Explorer session."""

    def __init__(self):
        self.baseline_person_snapshots = None
        self.baseline_portfolio_snapshots = None
        self.baseline_retirement_snapshots = None
        self.person_snapshots = None
        self.portfolio_snapshots = None
        self.retirement_snapshots = None
        self.baseline_results = None
        self.scenario_results = None

class ScenarioStateManager:
    """
    Owns Scenario Explorer snapshots and baseline/scenario simulation results.
    """

    def __init__(self, main_gui, session_state):
        self.main_gui = main_gui
        self.session_state = session_state


    def build_snapshots_from_truth(self):
        s = self.session_state
        controls = self.main_gui.simulation_controls

        s.baseline_person_snapshots = {"husband": copy.deepcopy(self.main_gui.husband)}
        if controls.get("second_person_enabled", False):
            s.baseline_person_snapshots["wife"] = copy.deepcopy(self.main_gui.wife)

        s.baseline_portfolio_snapshots = {"husband": copy.deepcopy(self.main_gui.husband_portfolio)}
        if controls.get("second_person_enabled", False):
            s.baseline_portfolio_snapshots["wife"] = copy.deepcopy(self.main_gui.wife_portfolio)

        s.baseline_retirement_snapshots = ScenarioSnapshots()
        s.baseline_retirement_snapshots.fund_expense = self.main_gui.simulation_settings.get("fund_expense")
        s.baseline_retirement_snapshots.historical_data_multiplier = 100.0

        s.person_snapshots = copy.deepcopy(s.baseline_person_snapshots)
        s.portfolio_snapshots = copy.deepcopy(s.baseline_portfolio_snapshots)
        s.retirement_snapshots = copy.deepcopy(s.baseline_retirement_snapshots)


    def capture_baseline_from_scenario(self):
        s = self.session_state
        s.baseline_person_snapshots = copy.deepcopy(s.person_snapshots)
        s.baseline_portfolio_snapshots = copy.deepcopy(s.portfolio_snapshots)
        s.baseline_retirement_snapshots = copy.deepcopy(s.retirement_snapshots)


    def _adjust_retirement_benefits_year_by_year(self, snapshot, baseline):
        ss_factors = {62: 0.70, 63: 0.75, 64: 0.80, 65: 0.867, 66: 0.933, 67: 1.0, 68: 1.08, 69: 1.16, 70: 1.24}

        baseline_ss_age = min(max(baseline.ss_age, 62), 70)
        new_ss_age = min(max(snapshot.ss_age, 62), 70)
        baseline_factor = ss_factors[baseline_ss_age]
        new_factor = ss_factors[new_ss_age]

        if baseline_factor > 0:
            baseline_pia = baseline.ss / baseline_factor
        else:
            baseline_pia = baseline.ss

        snapshot.ss = round(baseline_pia * new_factor, 2)
        snapshot.pension = baseline.pension
        snapshot.annuity = baseline.annuity
        snapshot.pension_age = snapshot.retire_age
        snapshot.annuity_age = snapshot.retire_age


    def apply_control_values(self, values):
        s = self.session_state
        controls = self.main_gui.simulation_controls
        expense_mode = controls.get("always_use_expense_mode", False)

        s.retirement_snapshots.calculate_real_dollars = values.calculate_real_dollars
        s.retirement_snapshots.delta_inflation = float(values.inflation) - float(self.main_gui.inflation)
        s.retirement_snapshots.fund_expense = values.fund_expense
        s.retirement_snapshots.historical_data_multiplier = values.market_adjustment
        s.retirement_snapshots.custom_stock_percent = values.stocks
        s.retirement_snapshots.custom_bonds_percent = values.bonds
        s.retirement_snapshots.custom_cash_percent = values.cash

        if expense_mode:
            s.retirement_snapshots.scenario_expense_multiplier = values.dynamic_value / 100.0
        else:
            s.retirement_snapshots.scenario_withdraw_pct = values.dynamic_value

        husband_snapshot = s.person_snapshots.get("husband")
        husband_baseline = s.baseline_person_snapshots.get("husband")
        husband_snapshot.retire_age = values.husband_ret_age
        husband_snapshot.ss_age = values.husband_ss_age
        self._adjust_retirement_benefits_year_by_year(husband_snapshot, husband_baseline)

        wife_snapshot = None
        if controls.get("second_person_enabled", False):
            wife_snapshot = s.person_snapshots.get("wife")
            wife_baseline = s.baseline_person_snapshots.get("wife")
            if wife_snapshot is not None and values.wife_ret_age is not None:
                wife_snapshot.retire_age = values.wife_ret_age
                wife_snapshot.ss_age = values.wife_ss_age
                self._adjust_retirement_benefits_year_by_year(wife_snapshot, wife_baseline)

        s.retirement_snapshots.use_snapshot_annotations = values.enable_annotations

        baseline_stocks, baseline_bonds, baseline_cash = compute_portfolio_percentages(s.baseline_portfolio_snapshots)
        s.retirement_snapshots.annotation_strings = build_scenario_explorer_annotations(
            main_gui=self.main_gui, tmp_ret_age_h=values.husband_ret_age, tmp_ret_age_w=values.wife_ret_age,
            inflation=values.inflation, fund_expense=values.fund_expense,
            historical_data_multiplier=values.market_adjustment, stocks=values.stocks, bonds=values.bonds,
            cash=values.cash, baseline_stocks=baseline_stocks, baseline_bonds=baseline_bonds,
            baseline_cash=baseline_cash, wife_snapshot=wife_snapshot,
            scenario_expense_multiplier=s.retirement_snapshots.scenario_expense_multiplier,
            scenario_withdraw_pct=s.retirement_snapshots.scenario_withdraw_pct
        )


    def clone_result_inputs(self, persons, portfolios, retirement_snapshots):
        persons_copy = copy.deepcopy(persons)
        portfolios_copy = copy.deepcopy(portfolios)
        retirement_copy = copy.deepcopy(retirement_snapshots)
        return persons_copy, portfolios_copy, retirement_copy


    def compute_results_from_inputs(self, persons, portfolios, retirement_snapshots, include_realestate, plot_style):
        persons_copy, portfolios_copy, retirement_copy = self.clone_result_inputs(
            persons, portfolios, retirement_snapshots
        )

        sim_config = self.main_gui.build_simulation_from_gui(
            sim_type="portfolio_sim", use_snapshots=True, retirement_snapshots=retirement_copy
        )

        if plot_style == "historical_risk":
            sim_config.results_mode = "risk_analysis"
            sim_config.risk_analysis_mode = "historical_windows"
            sim_config.risk_analysis_plot_style = "fill"
        else:
            sim_config.results_mode = plot_style

        sim_config.include_realestate = bool(include_realestate)

        husband = persons_copy["husband"]
        if sim_config.second_person_enabled:
            wife = persons_copy.get("wife")
        else:
            wife = None

        husband_portfolio = portfolios_copy["husband"]
        if wife:
            wife_portfolio = portfolios_copy.get("wife")
        else:
            wife_portfolio = None

        p = run_pipeline(husband_portfolio, wife_portfolio, husband, wife, self.main_gui.expensesDict, sim_config)

        return {
            "p": p, "sim_config": sim_config, "husband": husband, "wife": wife,
            "retirement_snapshots": retirement_copy,
        }


    def compute_baseline_results(self, include_realestate, plot_style):
        s = self.session_state
        s.baseline_results = self.compute_results_from_inputs(
            s.baseline_person_snapshots, s.baseline_portfolio_snapshots, s.baseline_retirement_snapshots,
            include_realestate, plot_style
        )


    def compute_scenario_results(self, include_realestate, plot_style):
        s = self.session_state
        s.scenario_results = self.compute_results_from_inputs(
            s.person_snapshots, s.portfolio_snapshots, s.retirement_snapshots, include_realestate, plot_style
        )
        return s.scenario_results


    def _build_result_metrics(self, result):
        summary = result["p"]["summary_results"]

        return ScenarioResultMetrics(
            ending_portfolio=summary["total_assets"][-1],
            depletion_rate=summary["simulated_shortfall_rate"],
            ending_cash_flow=summary["net_cash_flow"][-1],
            lifetime_funding_gap=sum(summary["funding_gap"]),
            lifetime_taxes=sum(summary["taxes"]),
            ending_pre_tax=summary["pre_tax_assets"][-1],
            ending_after_tax=summary["post_tax_assets"][-1],
            ending_roth=summary["roth_assets"][-1],
            ending_hsa=summary["hsa_assets"][-1]
        )

    def _build_result_assumptions(self, result):
        sim = result["sim_config"]
        snapshot = result["retirement_snapshots"]
        husband = result["husband"]
        wife = result["wife"]

        if sim.always_use_expense_mode:
            dynamic_label = "Expense Multiplier"
            dynamic_value = sim.scenario_expense_multiplier * 100
        else:
            dynamic_label = "Withdrawal Rate"
            dynamic_value = sim.retirement_withdraw_pct

        if wife is not None:
            wife_age = wife.age
            wife_retire_age = wife.retire_age
            wife_ss_age = wife.ss_age
        else:
            wife_age = None
            wife_retire_age = None
            wife_ss_age = None

        return ScenarioAssumptions(
            husband_age=husband.age, 
            husband_retire_age=husband.retire_age, 
            husband_ss_age=husband.ss_age,
            wife_age=wife_age,
            wife_retire_age=wife_retire_age,
            wife_ss_age=wife_ss_age,
            inflation_rate=sim.inflation_rate * 100,
            fund_expense=sim.fund_expense * 100,
            market_adjustment=snapshot.historical_data_multiplier,
            dynamic_label=dynamic_label,
            dynamic_value=dynamic_value, 
            stock=sim.custom_stock * 100, 
            bonds=sim.custom_bonds * 100,
            cash=sim.custom_cash * 100,
        )


    def build_results_view_model(self):
        s = self.session_state

        if s.baseline_results is None or s.scenario_results is None:
            return None

        return ScenarioResultsViewModel(
            original_metrics=self._build_result_metrics(s.baseline_results),
            changed_metrics=self._build_result_metrics(s.scenario_results),
            original_assumptions=self._build_result_assumptions(s.baseline_results),
            changed_assumptions=self._build_result_assumptions(s.scenario_results)
        )