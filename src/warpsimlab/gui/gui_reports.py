# gui_reports.py

from src.warpsimlab.gui.gui_utils import noop, set_tk_button_soft_disabled
from src.warpsimlab.gui.gui_reportExecutiveSummary import ExecutiveSummaryReportFrame
from src.warpsimlab.gui.gui_reportYearByYearDetails import YearByYearDetailsReportFrame
from src.warpsimlab.gui.gui_reportHistoricalWindowRisk import HistoricalWindowRiskReportFrame
from src.warpsimlab.gui.gui_reportMonteCarloRisk import MonteCarloRiskReportFrame
from src.warpsimlab.gui.gui_reportTaxes import TaxReportFrame
from src.warpsimlab.gui.gui_reportSpendingComparison import SpendingComparisonReportFrame
from src.warpsimlab.gui.gui_reportAssetAllocationComparison import AssetAllocationComparisonReportFrame
from src.warpsimlab.gui.gui_reportRetirementSSComparison import RetirementSSComparisonReportFrame


class PortfolioSimulatorGUI_ReportsMixin:
    def _rebuild_reports_menu(self):
        if not hasattr(self, "reports_menu"):
            return

        self.reports_menu.delete(0, "end")

        self.reports_menu.add_command(
            label="Executive Summary", command=self.edit_report_executive_summary
        )
        self.reports_menu.add_command(
            label="Year-by-Year Details", command=self.edit_report_year_by_year_details
        )
        self.reports_menu.add_command(label="Tax Report", command=self.edit_report_taxes)

        self.reports_menu.add_separator()

        self.reports_menu.add_command(
            label="Historical Window Risk Report", command=self.edit_report_historical_window_risk
        )
        self.reports_menu.add_command(
            label="Monte Carlo Risk Report", command=self.edit_report_monte_carlo_risk
        )

        self.reports_menu.add_separator()

        spending_state = (
            "normal" if self.simulation_controls.get("use_mode", "expenses") == "expenses" else "disabled"
        )

        self.reports_menu.add_command(
            label="Spending Comparison Report",
            command=self.edit_report_spending_comparison,
            state=spending_state,
        )
        self.reports_menu.add_command(
            label="Asset Allocation Comparison Report",
            command=self.edit_report_asset_allocation_comparison,
        )
        self.reports_menu.add_command(
            label="Retirement & Social Security Comparison Report",
            command=self.edit_report_retirement_ss_comparison,
        )

    def edit_report_executive_summary(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = ExecutiveSummaryReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["executive_summary"],
            parent_gui=self,
            title="Executive Summary",
        )
        frame.pack(padx=10, pady=5, fill="x")

    def edit_report_year_by_year_details(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = YearByYearDetailsReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["year_by_year_details"],
            parent_gui=self,
            title="Year-by-Year Details",
        )
        frame.pack(padx=10, pady=5, fill="x")

    def edit_report_taxes(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = TaxReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["tax_report"],
            parent_gui=self,
            title="Tax Report",
        )
        frame.pack(padx=10, pady=5, fill="x")

    def edit_report_historical_window_risk(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = HistoricalWindowRiskReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["historical_window_risk"],
            parent_gui=self,
            title="Historical Window Risk Report",
        )
        frame.pack(padx=10, pady=5, fill="x")

    def edit_report_monte_carlo_risk(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = MonteCarloRiskReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["monte_carlo_risk"],
            parent_gui=self,
            title="Monte Carlo Risk Report",
        )
        frame.pack(padx=10, pady=5, fill="x")

    def edit_report_spending_comparison(self):
        if not self._advanced_only():
            return

        if self.simulation_controls.get("use_mode", "expenses") != "expenses":
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = SpendingComparisonReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["spending_comparison"],
            parent_gui=self,
            title="Spending Comparison Report",
        )
        frame.pack(padx=10, pady=5, fill="x")

    def edit_report_asset_allocation_comparison(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = AssetAllocationComparisonReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["asset_allocation_comparison"],
            parent_gui=self,
            title="Asset Allocation Comparison Report",
        )
        frame.pack(padx=10, pady=5, fill="x")

    def edit_report_retirement_ss_comparison(self):
        if not self._advanced_only():
            return

        for widget in self.edit_frame_container.winfo_children():
            widget.destroy()

        frame = RetirementSSComparisonReportFrame(
            self.edit_frame_container,
            report_options=self.report_options["retirement_ss_comparison"],
            parent_gui=self,
            title="Retirement & Social Security Comparison Report",
        )
        frame.pack(padx=10, pady=5, fill="x")

    def _apply_mode_to_reports_button(self):
        if not hasattr(self, "reports_button"):
            return

        legal_enabled = getattr(self, "legal_accepted", False)
        advanced_enabled = self._advanced_only() and legal_enabled

        set_tk_button_soft_disabled(
            self.reports_button, advanced_enabled, self._show_reports_menu, noop_command=noop
        )

        self._rebuild_reports_menu()