from __future__ import annotations

import tkinter as tk
from types import SimpleNamespace

import pytest


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk not available: {e}")

    root.withdraw()
    yield root
    root.destroy()


def make_portfolio(
    *,
    equity=0.0,
    bonds=0.0,
    cash=0.0,
):
    return SimpleNamespace(
        equity_pre=equity,
        equity_post=0.0,
        equity_roth=0.0,
        hsa_equity=0.0,
        bond_pre=bonds,
        bond_post=0.0,
        bond_roth=0.0,
        hsa_bond=0.0,
        cash_pre=cash,
        cash_post=0.0,
        cash_roth=0.0,
        hsa_cash=0.0,
    )


@pytest.fixture
def parent_gui():
    calls = []

    def edit_blank():
        calls.append(("edit_blank", None))

    def run_simulation_from_gui(*, sim_type):
        calls.append(("run_simulation_from_gui", sim_type))

    return SimpleNamespace(
        calls=calls,
        edit_blank=edit_blank,
        run_simulation_from_gui=run_simulation_from_gui,
        husband_portfolio=make_portfolio(
            equity=60.0,
            bonds=30.0,
            cash=10.0,
        ),
        wife_portfolio=make_portfolio(),
        simulation_controls={
            "second_person_enabled": False,
        },
    )


@pytest.fixture
def mod():
    from src.warpsimlab.gui.reports import gui_reportAssetAllocationComparison as mod

    return mod


def test_normalize_options_uses_defaults(tk_root, parent_gui, mod):
    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame.working_options["equity_percentages"] == [
        0,
        20,
        40,
        60,
        80,
        100,
    ]
    assert frame.working_options["output"]["generate_html"] is True
    assert frame.working_options["output"]["open_report_in_browser"] is False


def test_normalize_options_preserves_supplied_values(tk_root, parent_gui, mod):
    options = {
        "equity_percentages": [40, 60, 80],
        "output": {
            "open_report_in_browser": True,
        },
    }

    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    assert frame.working_options["equity_percentages"] == [40, 60, 80]
    assert frame.working_options["output"]["generate_html"] is True
    assert frame.working_options["output"]["open_report_in_browser"] is True


def test_portfolio_components_combines_all_account_types(tk_root, parent_gui, mod):
    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    portfolio = SimpleNamespace(
        equity_pre=10.0,
        equity_post=20.0,
        equity_roth=30.0,
        hsa_equity=40.0,
        bond_pre=1.0,
        bond_post=2.0,
        bond_roth=3.0,
        hsa_bond=4.0,
        cash_pre=5.0,
        cash_post=6.0,
        cash_roth=7.0,
        hsa_cash=8.0,
    )

    equity, bonds, cash = frame._portfolio_components(portfolio)

    assert equity == pytest.approx(100.0)
    assert bonds == pytest.approx(10.0)
    assert cash == pytest.approx(26.0)


def test_compute_current_allocation_single_person(tk_root, parent_gui, mod):
    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame.current_equity_percent == pytest.approx(60.0)
    assert frame.current_bonds_percent == pytest.approx(30.0)
    assert frame.current_cash_percent == pytest.approx(10.0)


def test_compute_current_allocation_combines_couple(tk_root, parent_gui, mod):
    parent_gui.simulation_controls["second_person_enabled"] = True
    parent_gui.wife_portfolio = make_portfolio(
        equity=40.0,
        bonds=30.0,
        cash=30.0,
    )

    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame.current_equity_percent == pytest.approx(50.0)
    assert frame.current_bonds_percent == pytest.approx(30.0)
    assert frame.current_cash_percent == pytest.approx(20.0)


def test_compute_current_allocation_empty_portfolio_defaults_to_cash(tk_root, parent_gui, mod):
    parent_gui.husband_portfolio = make_portfolio()

    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame.current_equity_percent == pytest.approx(0.0)
    assert frame.current_bonds_percent == pytest.approx(0.0)
    assert frame.current_cash_percent == pytest.approx(100.0)


def test_format_percentage(tk_root, parent_gui, mod):
    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    assert frame._format_percentage(60.0) == "60"
    assert frame._format_percentage(62.5) == "62.5"
    assert frame._format_percentage(62.25) == "62.25"


def test_parse_equity_percentages_sorts_and_ignores_blanks(tk_root, parent_gui, mod):
    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    values = ["80", "", "40", "60", "", ""]

    for var, value in zip(frame.equity_vars, values):
        var.set(value)

    assert frame._parse_equity_percentages() == [40.0, 60.0, 80.0]


def test_parse_equity_percentages_rejects_invalid_value(tk_root, parent_gui, mod):
    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    frame.equity_vars[0].set("bad")

    with pytest.raises(ValueError, match="not a valid equity percentage"):
        frame._parse_equity_percentages()


def test_parse_equity_percentages_rejects_out_of_range(tk_root, parent_gui, mod):
    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    frame.equity_vars[0].set("101")

    with pytest.raises(ValueError, match="between 0 and 100"):
        frame._parse_equity_percentages()


def test_parse_equity_percentages_rejects_duplicates(tk_root, parent_gui, mod):
    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    for var in frame.equity_vars:
        var.set("")

    frame.equity_vars[0].set("60")
    frame.equity_vars[1].set("60")

    with pytest.raises(ValueError, match="Duplicate equity percentages"):
        frame._parse_equity_percentages()


def test_parse_equity_percentages_requires_two_values(tk_root, parent_gui, mod):
    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    for var in frame.equity_vars:
        var.set("")

    frame.equity_vars[0].set("60")

    with pytest.raises(ValueError, match="at least two"):
        frame._parse_equity_percentages()


def test_parse_equity_percentages_rejects_lower_equity_when_no_bonds_or_cash(
    tk_root,
    parent_gui,
    mod,
):
    parent_gui.husband_portfolio = make_portfolio(
        equity=100.0,
    )

    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options={},
        parent_gui=parent_gui,
    )

    for var in frame.equity_vars:
        var.set("")

    frame.equity_vars[0].set("80")
    frame.equity_vars[1].set("100")

    with pytest.raises(ValueError, match="contains no bonds or cash"):
        frame._parse_equity_percentages()


def test_apply_changes_updates_options_and_runs_report(tk_root, parent_gui, mod):
    options = {}

    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    values = ["80", "40", "60", "", "", ""]

    for var, value in zip(frame.equity_vars, values):
        var.set(value)

    frame.open_browser_var.set(True)

    frame.apply_changes()

    assert options["equity_percentages"] == [40.0, 60.0, 80.0]
    assert options["output"]["open_report_in_browser"] is True
    assert parent_gui.calls == [
        ("edit_blank", None),
        ("run_simulation_from_gui", "asset_allocation_comparison_report"),
    ]


def test_apply_changes_invalid_input_does_not_run_report(tk_root, parent_gui, mod, monkeypatch):
    options = {}
    errors = []

    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    monkeypatch.setattr(
        mod.messagebox,
        "showerror",
        lambda title, message, parent=None: errors.append((title, message)),
    )

    for var in frame.equity_vars:
        var.set("")

    frame.equity_vars[0].set("60")

    frame.apply_changes()

    assert len(errors) == 1
    assert "at least two" in errors[0][1]
    assert parent_gui.calls == []


def test_cancel_changes_restores_working_options_and_closes(tk_root, parent_gui, mod):
    options = {
        "equity_percentages": [40, 60, 80],
        "output": {
            "open_report_in_browser": True,
        },
    }

    frame = mod.AssetAllocationComparisonReportFrame(
        tk_root,
        report_options=options,
        parent_gui=parent_gui,
    )

    frame.working_options["equity_percentages"] = [0, 100]

    frame.cancel_changes()

    assert frame.working_options["equity_percentages"] == [40, 60, 80]
    assert frame.working_options["output"]["open_report_in_browser"] is True
    assert parent_gui.calls == [("edit_blank", None)]