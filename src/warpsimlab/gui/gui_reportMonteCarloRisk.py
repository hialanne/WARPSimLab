# gui_reportMonteCarloRisk.py

from src.warpsimlab.gui.gui_reportRiskBase import RiskReportBaseFrame


class MonteCarloRiskReportFrame(RiskReportBaseFrame):
    REPORT_NAME = "Monte Carlo Risk Report"
    RUN_SIM_TYPE = "monte_carlo_risk_report"

    DESCRIPTION = (
        "Select the Monte Carlo Risk Report sections and outputs to include. "
        "This dialog controls report contents only."
    )

    METHOD_NOTE = (
        "Simulation settings such as number of simulations, correlation, and sampling mode remain under Simulation. "
        "This dialog controls report contents only."
    )

    DEFAULT_OPTIONS = {
        "general": {
            "include_executive_summary": True,
            "include_method_explanation": True,
        },
        "analysis": {
            "include_portfolio_projection": True,
            "include_portfolio_sustainability": True,
            "include_monte_carlo_insights": True,
            "include_percentile_table": True,
        },
        "output": {
            "generate_html": True,
            "generate_csv": False,
        },
    }

    def _build_method_specific_analysis_options(self, parent, row):
        row = self._add_check_path_to_frame(
            parent,
            "Include Monte Carlo Insights",
            ["analysis", "include_monte_carlo_insights"],
            row,
        )

        return row