# test_simulationObject.py

from __future__ import annotations

import pytest

from src.warpsimlab.sim.simulationObject import Simulation


def _base_args():
    """Return a minimal argument set required to construct Simulation."""
    return dict(
        start_year=2025,
        years_to_simulate=5,
        inflation_rate=0.03,
        num_sims=100,
        fund_expense=0.01,
        use_fund_expenses=True,
        plot_mode="raw",
        subplot_mode="monte_carlo",
        include_rmd=True,
        calculate_income_taxes=True,
        calculate_payroll_taxes=True,  
        tax_filing_status="married",
        calculate_state_taxes=False,
        state_of_residence="CA",
        second_person_enabled=True,
        eq_mean=7,
        bd_mean=3,
        cs_mean=1,
        eq_std=15,
        bd_std=5,
        cs_std=1,
    )


def test_simulation_assigns_core_attributes():
    args = _base_args()
    sim = Simulation(**args)

    assert sim.start_year == 2025
    assert sim.years_to_simulate == 5
    assert sim.inflation_rate == 0.03
    assert sim.num_sims == 100
    assert sim.fund_expense == 0.01
    assert sim.use_fund_expenses is True


def test_simulation_assigns_plot_configuration():
    args = _base_args()
    sim = Simulation(**args)

    assert sim.plot_mode == "raw"
    assert sim.subplot_mode == "monte_carlo"
    assert sim.annotate_plots is False
    assert sim.constant_y_plots is False


def test_simulation_assigns_tax_settings():
    args = _base_args()
    sim = Simulation(**args)

    assert sim.calculate_income_taxes is True
    assert sim.tax_filing_status == "married"
    assert sim.calculate_state_taxes is False
    assert sim.state_of_residence == "CA"
    assert sim.calculate_payroll_taxes is True


def test_simulation_assigns_asset_parameters():
    args = _base_args()
    sim = Simulation(**args)

    assert sim.eq_mean == 7
    assert sim.bd_mean == 3
    assert sim.cs_mean == 1

    assert sim.eq_std == 15
    assert sim.bd_std == 5
    assert sim.cs_std == 1


def test_simulation_overlay_flags_defaults():
    args = _base_args()
    sim = Simulation(**args)

    assert sim.overlay_tax_impacts is False
    assert sim.overlay_fund_expense_impacts is False
    assert sim.overlay_household_expenses is False
    assert sim.overlay_profit_loss is True
    assert sim.overlay_retirement_age is False


def test_simulation_annotation_defaults():
    args = _base_args()
    sim = Simulation(**args)

    assert sim.use_snapshot_annotations is False
    assert isinstance(sim.user_annotation_strings, list)


def test_simulation_custom_asset_mix():
    args = _base_args()

    sim = Simulation(
        **args,
        custom_stock=60,
        custom_bonds=30,
        custom_cash=10
    )

    assert sim.custom_stock == 60
    assert sim.custom_bonds == 30
    assert sim.custom_cash == 10


def test_simulation_real_estate_settings():
    args = _base_args()

    sim = Simulation(
        **args,
        include_realestate=True,
        re_mean=4,
        re_std=6
    )

    assert sim.include_realestate is True
    assert sim.re_mean == 4
    assert sim.re_std == 6


def test_simulation_output_csv_configuration():
    args = _base_args()

    sim = Simulation(
        **args,
        output_csv="Output",
        csv_output_dir="/tmp"
    )

    assert sim.output_csv == "Output"
    assert sim.csv_output_dir == "/tmp"