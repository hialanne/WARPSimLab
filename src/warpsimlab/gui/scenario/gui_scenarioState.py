# gui_scenarioState.py

import copy

from src.warpsimlab.gui.scenario.gui_scenarioSnapshots import ScenarioSnapshots
from src.warpsimlab.sim.simulation import run_pipeline
from src.warpsimlab.gui.gui_annotations import build_scenario_explorer_annotations


class ScenarioStateManager:
    """
    Owns Scenario Explorer snapshots and baseline/scenario simulation results.
    """

    def __init__(self, controller):
        self.controller = controller
        self.main_gui = controller.main_gui


    def build_snapshots_from_truth(self):
        c = self.controller
        controls = self.main_gui.simulation_controls

        c.baseline_person_snapshots = {"husband": copy.deepcopy(self.main_gui.husband)}
        if controls.get("second_person_enabled", False):
            c.baseline_person_snapshots["wife"] = copy.deepcopy(self.main_gui.wife)

        c.baseline_portfolio_snapshots = {"husband": copy.deepcopy(self.main_gui.husband_portfolio)}
        if controls.get("second_person_enabled", False):
            c.baseline_portfolio_snapshots["wife"] = copy.deepcopy(self.main_gui.wife_portfolio)

        c.baseline_retirement_snapshots = ScenarioSnapshots()
        c.baseline_retirement_snapshots.fund_expense = self.main_gui.simulation_settings.get("fund_expense")
        c.baseline_retirement_snapshots.historical_data_multiplier = 100.0

        c.person_snapshots = copy.deepcopy(c.baseline_person_snapshots)
        c.portfolio_snapshots = copy.deepcopy(c.baseline_portfolio_snapshots)
        c.retirement_snapshots = copy.deepcopy(c.baseline_retirement_snapshots)


    def capture_baseline_from_scenario(self):
        c = self.controller
        c.baseline_person_snapshots = copy.deepcopy(c.person_snapshots)
        c.baseline_portfolio_snapshots = copy.deepcopy(c.portfolio_snapshots)
        c.baseline_retirement_snapshots = copy.deepcopy(c.retirement_snapshots)


    def apply_slider_values_to_snapshots(self):
        c = self.controller

        if c.sliders_frame is None:
            return

        controls = self.main_gui.simulation_controls

        inflation = c.sliders_frame.inflation_value.get()
        fund_expense = c.sliders_frame.fund_expense_value.get()
        historical_data_multiplier = c.sliders_frame.market_adjustment_percent.get()

        stocks = c.sliders_frame.stocks_percent.get()
        bonds = c.sliders_frame.bonds_percent.get()
        cash = c.sliders_frame.cash_percent.get()

        c.retirement_snapshots.calculate_real_dollars = c.sliders_frame.calculate_real_dollars.get()
        c.retirement_snapshots.delta_inflation = float(inflation) - float(self.main_gui.inflation)
        c.retirement_snapshots.fund_expense = fund_expense
        c.retirement_snapshots.historical_data_multiplier = historical_data_multiplier

        c.retirement_snapshots.custom_stock_percent = stocks
        c.retirement_snapshots.custom_bonds_percent = bonds
        c.retirement_snapshots.custom_cash_percent = cash

        husband_snapshot = c.person_snapshots.get("husband")
        tmp_ret_age_h = c.sliders_frame.tmp_ret_age_h.get()
        tmp_ss_age_h = c.sliders_frame.tmp_ss_age_h.get()
        husband_snapshot.retire_age = tmp_ret_age_h
        husband_snapshot.ss_age = tmp_ss_age_h

        wife_snapshot = None
        tmp_ret_age_w = None
        if controls.get("second_person_enabled", False):
            wife_snapshot = c.person_snapshots.get("wife")
            if wife_snapshot is not None and c.sliders_frame.tmp_ret_age_w is not None:
                tmp_ret_age_w = c.sliders_frame.tmp_ret_age_w.get()
                wife_snapshot.retire_age = tmp_ret_age_w
                wife_snapshot.ss_age = c.sliders_frame.tmp_ss_age_w.get()

        c.retirement_snapshots.use_snapshot_annotations = c.sliders_frame.enable_annotations.get()

        baseline_stocks, baseline_bonds, baseline_cash = c.sliders_frame._compute_initial_portfolio_percents()

        c.retirement_snapshots.annotation_strings = build_scenario_explorer_annotations(
            main_gui=self.main_gui, tmp_ret_age_h=tmp_ret_age_h, tmp_ret_age_w=tmp_ret_age_w, inflation=inflation,
            fund_expense=fund_expense, historical_data_multiplier=historical_data_multiplier, stocks=stocks,
            bonds=bonds, cash=cash, baseline_stocks=baseline_stocks, baseline_bonds=baseline_bonds,
            baseline_cash=baseline_cash, wife_snapshot=wife_snapshot,
            scenario_expense_multiplier=c.retirement_snapshots.scenario_expense_multiplier,
            scenario_withdraw_pct=c.retirement_snapshots.scenario_withdraw_pct,
        )


    def clone_result_inputs(self, persons, portfolios, retirement_snapshots):
        persons_copy = copy.deepcopy(persons)
        portfolios_copy = copy.deepcopy(portfolios)
        retirement_copy = copy.deepcopy(retirement_snapshots)
        return persons_copy, portfolios_copy, retirement_copy


    def compute_results_from_inputs(self, persons, portfolios, retirement_snapshots, include_realestate):
        persons_copy, portfolios_copy, retirement_copy = self.clone_result_inputs(
            persons, portfolios, retirement_snapshots
        )

        sim_config = self.main_gui.build_simulation_from_gui(
            sim_type="portfolio_sim", use_snapshots=True, retirement_snapshots=retirement_copy
        )

        plot_style = self.controller.plot_style

        if plot_style == "historical_risk":
            sim_config.results_mode = "risk_analysis"
            sim_config.risk_analysis_mode = "historical_windows"
            sim_config.risk_analysis_plot_style = "fill"
        else:
            sim_config.results_mode = plot_style

        sim_config.include_realestate = bool(include_realestate)

        husband = persons_copy["husband"]
        wife = persons_copy.get("wife") if sim_config.second_person_enabled else None
        husband_portfolio = portfolios_copy["husband"]
        wife_portfolio = portfolios_copy.get("wife") if wife else None

        p = run_pipeline(husband_portfolio, wife_portfolio, husband, wife, self.main_gui.expensesDict, sim_config)

        return {
            "p": p, "sim_config": sim_config, "husband": husband, "wife": wife,
            "retirement_snapshots": retirement_copy,
        }


    def compute_baseline_results(self):
        c = self.controller
        include_realestate = bool(self.main_gui.simulation_controls.get("include_realestate", False))

        c.baseline_results = self.compute_results_from_inputs(
            c.baseline_person_snapshots, c.baseline_portfolio_snapshots,
            c.baseline_retirement_snapshots, include_realestate
        )


    def compute_scenario_results(self):
        c = self.controller
        include_realestate = c.include_realestate_var.get()
        c.scenario_results = self.compute_results_from_inputs(
            c.person_snapshots, c.portfolio_snapshots, c.retirement_snapshots, include_realestate
        )
        return c.scenario_results