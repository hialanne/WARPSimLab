"""Read-only financial captures for the final migration; never writes approved references."""

from copy import deepcopy
from dataclasses import asdict, fields, is_dataclass
import importlib
from pathlib import Path

import pytest

from src.warpsimlab.sim import simulation
from src.warpsimlab.sim.simulationObject import SimulationConfig
from tests.architectural_helpers import make_execution_case
from tests.feature_tests.workflow_helpers import inputs_from_gui, make_gui
from tests.numerical_reference_scenarios import CASES, run_case


def financial_pipeline(result):
    if isinstance(result, tuple):
        result = result[0]
    captured = deepcopy({key: value for key, value in result.items() if key != "portfolio_plot_data"})
    captured["portfolio_plot_data"] = deepcopy(vars(result["portfolio_plot_data"]))
    return captured


def capture_financial_execution():
    captured = {"core": {name: run_case(name)[0] for name in CASES}, "secondary": {}, "reports": {}}
    for mode in ("fill", "risk_analysis"):
        case = make_execution_case(results_mode=mode, show_simulated_shortfall_rate=True,
            calculate_simulated_shortfall_rate=True, overlay_tax_impacts=True, overlay_fund_expense_impacts=True)
        captured["secondary"][mode] = financial_pipeline(simulation.run_pipeline(**case))
    modules = ["summary", "year_by_year", "tax", "risk", "asset_allocation_comparison",
        "spending_comparison", "retirement_ss_comparison"]
    original = simulation.run_pipeline
    current = []

    def record(*args, **kwargs):
        config = kwargs.get("sim_config")
        if config is None:
            config = args[5]
        settings = {field.name: deepcopy(getattr(config, field.name)) for field in fields(SimulationConfig)}
        result = original(*args, **kwargs)
        current.append(dict(config=settings, financial=financial_pipeline(result)))
        return result

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(simulation, "run_pipeline", record)
        folder = Path("codex_reports/sprint_4_capture_home").resolve()
        patch.setenv("USERPROFILE", str(folder))
        patch.setenv("HOME", str(folder))
        for name in modules:
            module = importlib.import_module(f"src.warpsimlab.sim.run_sim_{name}_report" if name != "risk"
                else "src.warpsimlab.sim.run_sim_risk_reports")
            if hasattr(module, "run_pipeline"):
                patch.setattr(module, "run_pipeline", record)
            for key in vars(module).copy():
                if key.startswith("save_") and key.endswith("_report_plot"):
                    patch.setattr(module, key, lambda *args, **kwargs: "verification-plot.png")
                if key.startswith("generate_") and key.endswith("report"):
                    patch.setattr(module, key, lambda data: data)
            if hasattr(module, "_generate_historical_allocation_plots"):
                patch.setattr(module, "_generate_historical_allocation_plots", lambda **kwargs: {})
        for mode in ["summary_report", "year_by_year_report", "tax_report", "monte_carlo_risk_report",
            "historical_window_risk_report", "asset_allocation_comparison_report", "spending_comparison_report",
            "retirement_ss_comparison_report"]:
            current = []
            gui = make_gui(folder)
            result = simulation.run_simulation(**inputs_from_gui(gui, mode))
            report = result
            if is_dataclass(result):
                report = asdict(result)
                for key in ("report_metadata", "plot_assets", "historical_plot_assets"):
                    report.pop(key, None)
            captured["reports"][mode] = dict(executions=current, report=report)
    return captured
