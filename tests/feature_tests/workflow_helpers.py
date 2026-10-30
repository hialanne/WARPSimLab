"""Headless GUI state with real configuration, persistence and finance methods."""

import copy
from types import SimpleNamespace

from src.warpsimlab.gui.gui_io import PortfolioSimulatorGUI_IOMixin
from src.warpsimlab.gui.gui_navigation import PortfolioSimulatorGUI_NavigationMixin
from src.warpsimlab.gui.gui_run import PortfolioSimulatorGUI_RunMixin
from tests.architectural_helpers import make_execution_case


class WorkflowGUI(PortfolioSimulatorGUI_RunMixin, PortfolioSimulatorGUI_IOMixin,
                  PortfolioSimulatorGUI_NavigationMixin):
    pass


def make_gui(tmp_path, **overrides):
    case = make_execution_case(**overrides)
    config = case["sim_config"]
    gui = WorkflowGUI()
    for name in ("husband", "wife", "husband_portfolio", "wife_portfolio"):
        setattr(gui, name, case[name])
    gui.expensesDict = case["expenses"]
    gui.simulation_controls = {k: copy.deepcopy(v) for k, v in vars(config).items()
                               if not k.startswith("_")}
    gui.simulation_settings = dict(start_year=config.start_year,
        years_to_simulate=config.years_to_simulate, num_sims=config.num_sims,
        fund_expense=config.fund_expense * 100, use_fund_expenses=config.use_fund_expenses,
        longevity_mode="custom_death_age", fixed_years_to_simulate=8,
        initial_allocation_mode=config.sim_initial_allocation_mode)
    gui.inflation = config.inflation_rate * 100
    for name in ("eq_mean", "bd_mean", "cs_mean", "re_mean", "eq_std", "bd_std", "cs_std", "re_std"):
        setattr(gui, name, getattr(config, name) * 100)
    for name in ("historical_magi", "special_income_streams", "roth_flows"):
        setattr(gui, name, copy.deepcopy(getattr(config, name)))
    # Only the event loop and file pickers are replaced; domain objects and
    # all GUI-to-simulation conversion methods remain production implementations.
    gui.root = SimpleNamespace(focus_get=lambda: None, update_idletasks=lambda: None)
    gui.edit_frame_container = None
    gui.mode_var = SimpleNamespace(get=lambda: "Advanced")
    gui.warpsimlab_version = "feature-test"
    gui.loaded_data_file = None
    gui.get_default_warpsimlab_dir = lambda: tmp_path
    gui._get_recent_data_dirs_file = lambda: tmp_path / "recent.json"
    output = dict(generate_html=True, generate_csv=True, open_report_in_browser=False)
    gui.report_options = {
        "executive_summary": dict(include_simulation_summary=True,
            include_assumptions_appendix=True, output_format="HTML"),
        "year_by_year_details": dict(output, table_detail="Detailed"),
        "tax_report": dict(output=output, sections=dict(include_roth_analysis=True,
            include_hsa_analysis=True, include_rmd_analysis=True)),
        "monte_carlo_risk": dict(output=output, analysis=dict(include_percentile_table=True)),
        "historical_window_risk": dict(output=output, analysis=dict(include_percentile_table=True)),
        "asset_allocation_comparison": dict(output=output, equity_percentages=[20, 80]),
        "spending_comparison": dict(output=output, spending_percentages=[80, 120]),
        "retirement_ss_comparison": dict(output=output, retirement_ages=[68, 70],
                                         social_security_ages=[68, 70]),
    }
    return gui


def inputs_from_gui(gui, sim_type="portfolio_sim"):
    couple = gui.simulation_controls["second_person_enabled"]
    return dict(husband=gui._person_for_sim(gui.husband),
        wife=gui._person_for_sim(gui.wife) if couple else None,
        husband_portfolio=gui._portfolio_for_sim(gui.husband_portfolio),
        wife_portfolio=gui._portfolio_for_sim(gui.wife_portfolio) if couple else None,
        expenses=gui.expensesDict, sim_config=gui.build_simulation_from_gui(sim_type))
