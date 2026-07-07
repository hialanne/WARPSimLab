# gui_reportHistoricalWindowRisk.py

from src.gui.gui_reportRiskBase import RiskReportBaseFrame


class HistoricalWindowRiskReportFrame(RiskReportBaseFrame):
    REPORT_NAME = "Historical Window Risk Report"
    RUN_SIM_TYPE = "historical_window_risk_report"

    DESCRIPTION = (
        "Select the Historical Window Risk Report sections and outputs to include. "
        "This dialog controls report contents only."
    )

    METHOD_NOTE = (
        "Simulation settings such as historical data files and window mode remain under Simulation. "
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
            "include_historical_window_insights": True,
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
            "Include Historical Window Insights",
            ["analysis", "include_historical_window_insights"],
            row,
        )

        return row