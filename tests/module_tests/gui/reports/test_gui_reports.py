# test_gui_reports.py

import pytest

from src.warpsimlab.gui.reports import gui_reports


class DummyChild:
    def __init__(self):
        self.destroyed = False

    def destroy(self):
        self.destroyed = True


class DummyContainer:
    def __init__(self):
        self.children = [DummyChild()]

    def winfo_children(self):
        return [child for child in self.children if not child.destroyed]


class DummyMenu:
    def __init__(self):
        self.commands = []
        self.separator_count = 0
        self.delete_calls = []

    def delete(self, *args):
        self.delete_calls.append(args)
        self.commands = []
        self.separator_count = 0

    def add_command(self, **kwargs):
        self.commands.append(kwargs)

    def add_separator(self):
        self.separator_count += 1


class DummyFrame:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.pack_calls = []

    def pack(self, **kwargs):
        self.pack_calls.append(kwargs)


class FrameFactory:
    def __init__(self):
        self.instances = []

    def __call__(self, *args, **kwargs):
        frame = DummyFrame(*args, **kwargs)
        self.instances.append(frame)
        return frame


def _make_gui(advanced=True, use_mode="expenses"):
    gui = gui_reports.PortfolioSimulatorGUI_ReportsMixin()
    gui._advanced_only = lambda: advanced
    gui.edit_frame_container = DummyContainer()
    gui.simulation_controls = {"use_mode": use_mode}

    gui.report_options = {
        "executive_summary": {"name": "executive"},
        "year_by_year_details": {"name": "year"},
        "tax_report": {"name": "tax"},
        "historical_window_risk": {"name": "historical"},
        "monte_carlo_risk": {"name": "monte"},
        "spending_comparison": {"name": "spending"},
        "asset_allocation_comparison": {"name": "allocation"},
        "retirement_ss_comparison": {"name": "retirement"},
    }

    return gui


def test_rebuild_reports_menu_expense_mode():
    gui = _make_gui(use_mode="expenses")
    gui.reports_menu = DummyMenu()

    gui._rebuild_reports_menu()

    labels = [item["label"] for item in gui.reports_menu.commands]

    assert labels == [
        "Executive Summary",
        "Year-by-Year Details",
        "Tax Report",
        "Historical Window Risk Report",
        "Monte Carlo Risk Report",
        "Spending Comparison Report",
        "Asset Allocation Comparison Report",
        "Retirement & Social Security Comparison Report",
    ]
    assert gui.reports_menu.separator_count == 2

    spending = next(item for item in gui.reports_menu.commands if item["label"] == "Spending Comparison Report")
    assert spending["state"] == "normal"


def test_rebuild_reports_menu_disables_spending_when_not_expense_mode():
    gui = _make_gui(use_mode="percentage")
    gui.reports_menu = DummyMenu()

    gui._rebuild_reports_menu()

    spending = next(item for item in gui.reports_menu.commands if item["label"] == "Spending Comparison Report")
    assert spending["state"] == "disabled"


def test_rebuild_reports_menu_without_menu_returns():
    gui = _make_gui()

    gui._rebuild_reports_menu()


@pytest.mark.parametrize(
    "method_name,class_name,option_key,title",
    [
        ("edit_report_executive_summary", "ExecutiveSummaryReportFrame", "executive_summary", "Executive Summary"),
        (
            "edit_report_year_by_year_details",
            "YearByYearDetailsReportFrame",
            "year_by_year_details",
            "Year-by-Year Details",
        ),
        ("edit_report_taxes", "TaxReportFrame", "tax_report", "Tax Report"),
        (
            "edit_report_historical_window_risk",
            "HistoricalWindowRiskReportFrame",
            "historical_window_risk",
            "Historical Window Risk Report",
        ),
        (
            "edit_report_monte_carlo_risk",
            "MonteCarloRiskReportFrame",
            "monte_carlo_risk",
            "Monte Carlo Risk Report",
        ),
        (
            "edit_report_spending_comparison",
            "SpendingComparisonReportFrame",
            "spending_comparison",
            "Spending Comparison Report",
        ),
        (
            "edit_report_asset_allocation_comparison",
            "AssetAllocationComparisonReportFrame",
            "asset_allocation_comparison",
            "Asset Allocation Comparison Report",
        ),
        (
            "edit_report_retirement_ss_comparison",
            "RetirementSSComparisonReportFrame",
            "retirement_ss_comparison",
            "Retirement & Social Security Comparison Report",
        ),
    ],
)
def test_report_editor_routes_to_correct_frame(monkeypatch, method_name, class_name, option_key, title):
    gui = _make_gui()
    factory = FrameFactory()
    monkeypatch.setattr(gui_reports, class_name, factory)

    getattr(gui, method_name)()

    assert gui.edit_frame_container.winfo_children() == []
    assert len(factory.instances) == 1

    frame = factory.instances[0]
    assert frame.args[0] is gui.edit_frame_container
    assert frame.kwargs["report_options"] is gui.report_options[option_key]
    assert frame.kwargs["parent_gui"] is gui
    assert frame.kwargs["title"] == title
    assert frame.pack_calls == [{"padx": 10, "pady": 5, "fill": "x"}]


@pytest.mark.parametrize(
    "method_name,class_name",
    [
        ("edit_report_executive_summary", "ExecutiveSummaryReportFrame"),
        ("edit_report_year_by_year_details", "YearByYearDetailsReportFrame"),
        ("edit_report_taxes", "TaxReportFrame"),
        ("edit_report_historical_window_risk", "HistoricalWindowRiskReportFrame"),
        ("edit_report_monte_carlo_risk", "MonteCarloRiskReportFrame"),
        ("edit_report_spending_comparison", "SpendingComparisonReportFrame"),
        ("edit_report_asset_allocation_comparison", "AssetAllocationComparisonReportFrame"),
        ("edit_report_retirement_ss_comparison", "RetirementSSComparisonReportFrame"),
    ],
)
def test_report_editors_do_nothing_in_basic_mode(monkeypatch, method_name, class_name):
    gui = _make_gui(advanced=False)
    factory = FrameFactory()
    monkeypatch.setattr(gui_reports, class_name, factory)

    getattr(gui, method_name)()

    assert factory.instances == []
    assert len(gui.edit_frame_container.winfo_children()) == 1


def test_spending_report_does_nothing_outside_expense_mode(monkeypatch):
    gui = _make_gui(use_mode="percentage")
    factory = FrameFactory()
    monkeypatch.setattr(gui_reports, "SpendingComparisonReportFrame", factory)

    gui.edit_report_spending_comparison()

    assert factory.instances == []
    assert len(gui.edit_frame_container.winfo_children()) == 1


def test_apply_mode_to_reports_button_enabled(monkeypatch):
    gui = _make_gui(advanced=True)
    gui.legal_accepted = True
    gui.reports_button = object()
    gui._show_reports_menu = lambda: None

    calls = []
    rebuild_calls = []

    def fake_soft_disable(button, enabled, real_command, noop_command=None):
        calls.append((button, enabled, real_command, noop_command))

    monkeypatch.setattr(gui_reports, "set_tk_button_soft_disabled", fake_soft_disable)
    gui._rebuild_reports_menu = lambda: rebuild_calls.append(True)

    gui._apply_mode_to_reports_button()

    assert len(calls) == 1
    assert calls[0][0] is gui.reports_button
    assert calls[0][1] is True
    assert rebuild_calls == [True]


def test_apply_mode_to_reports_button_disabled_without_legal_acceptance(monkeypatch):
    gui = _make_gui(advanced=True)
    gui.legal_accepted = False
    gui.reports_button = object()
    gui._show_reports_menu = lambda: None

    enabled_values = []

    def fake_soft_disable(button, enabled, real_command, noop_command=None):
        enabled_values.append(enabled)

    monkeypatch.setattr(gui_reports, "set_tk_button_soft_disabled", fake_soft_disable)
    gui._rebuild_reports_menu = lambda: None

    gui._apply_mode_to_reports_button()

    assert enabled_values == [False]