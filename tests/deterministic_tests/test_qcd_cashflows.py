"""Charity leaves the portfolio but never funds household consumption."""

import copy

import numpy as np
import pytest

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.simulation import run_pipeline
from src.warpsimlab.sim import run_sim_summary_report, run_sim_tax_report, run_sim_year_by_year_report
from tests.architectural_helpers import assert_tree_equal, make_person, make_portfolio, make_simulation


@pytest.mark.parametrize("expense_mode", [True, False])
@pytest.mark.parametrize("include_rmd,qcd", [(False, 0), (False, 5_000), (True, 0),
    (True, 5_000), (True, 10_000), (True, 15_000)])
def test_qcd_cash_tax_rmd_and_portfolio_reconciliation(expense_mode, include_rmd, qcd):
    config = make_simulation(always_use_expense_mode=expense_mode, include_rmd=include_rmd,
                             retirement_withdraw_mode="Fixed Dollar Amount", retirement_withdraw_dollars=20_000)
    config.qcd_settings["husband"].update(enabled=qcd > 0, amount=qcd)
    before = copy.deepcopy(vars(config))
    expenses = DynamicExpenses()
    expenses.add_expense(2027, 20_000)
    husband = make_person(age=74, retire_age=60)
    pipeline = run_pipeline(make_portfolio(equity_pre=246_000, cash_post=100_000), make_portfolio(),
                            husband, make_person(), expenses, config)
    core, summary = pipeline["core"], pipeline["summary_results"]
    required_rmd = 0
    if include_rmd:
        # At age 75 the uniform lifetime divisor is 24.6.
        required_rmd = 10_000

    taxable_rmd = max(0, required_rmd - qcd)
    spendable = 20_000 - qcd
    ordinary_draw = spendable - taxable_rmd
    if expense_mode:
        spendable = taxable_rmd
        ordinary_draw = 20_000 - taxable_rmd

    assert core["qcd_husband"][0, 1] == qcd
    assert core["qcd_wife"][0, 1] == 0
    assert core["rmd_husband"][0, 1] == required_rmd
    assert core["qcd_rmd_offset_husband"][0, 1] == min(qcd, required_rmd)
    assert core["taxable_rmd_husband"][0, 1] == taxable_rmd
    assert core["breakdown_by_class"]["rmd"][0, 1] == taxable_rmd
    assert core["magi"][0, 1] == taxable_rmd
    assert core["gross_income"][0, 1] == spendable
    assert core["net_income"][0, 1] == spendable
    assert core["pre_tax_assets"][0, 1] == 246_000 - max(qcd, required_rmd)
    assert core["post_tax_assets"][0, 1] == 100_000 - ordinary_draw
    assert core["total_assets"][0, 1] == 346_000 - max(qcd, required_rmd) - ordinary_draw
    assert core["funding_gap"][0, 1] == 0
    for key in ("qcd_husband", "qcd_wife", "qcd_rmd_offset_husband", "qcd_rmd_offset_wife",
                "taxable_rmd_husband", "taxable_rmd_wife"):
        np.testing.assert_array_equal(summary[key], core[key][0])

    assert_tree_equal(vars(config), before)


def test_disabled_qcd_matches_defaults_for_every_result(run_financial_case):
    baseline = run_financial_case(husband=dict(age=74, retire_age=60), h_assets=dict(equity_pre=246_000),
                                  include_rmd=True, years_to_simulate=3)
    settings = make_simulation().qcd_settings
    for owner in ("husband", "wife"):
        settings[owner].update(amount=100_000, percent=100, mode="Percent of RMD")

    disabled = run_financial_case(husband=dict(age=74, retire_age=60), h_assets=dict(equity_pre=246_000),
                                  include_rmd=True, years_to_simulate=3, qcd_settings=settings)
    assert_tree_equal(disabled, baseline)


def test_qcd_is_excluded_from_tax_and_magi_with_taxes_enabled(run_financial_case):
    settings = make_simulation().qcd_settings
    settings["husband"].update(enabled=True, amount=10_000)
    core = run_financial_case(husband=dict(age=74, retire_age=60), h_assets=dict(equity_pre=246_000),
                              include_rmd=True, calculate_income_taxes=True, qcd_settings=settings)
    assert core["qcd_husband"][0, 1] == 10_000
    assert core["taxable_rmd_husband"][0, 1] == 0
    assert core["magi"][0, 1] == 0
    assert core["taxes"][0, 1] == 0
    assert core["total_assets"][0, 1] == 236_000


@pytest.mark.parametrize("include_rmd,percent,qcd,taxable", [(False, 100, 0, 0),
    (True, 0, 0, 10_000), (True, 50, 5_000, 5_000), (True, 100, 10_000, 0)])
def test_percentage_qcd_with_rmd_calculation_enabled_or_disabled(run_financial_case, include_rmd, percent, qcd, taxable):
    settings = make_simulation().qcd_settings
    settings["husband"].update(enabled=True, mode="Percent of RMD", percent=percent)
    core = run_financial_case(husband=dict(age=74, retire_age=60), h_assets=dict(equity_pre=246_000),
                              include_rmd=include_rmd, qcd_settings=settings)
    assert core["qcd_husband"][0, 1] == qcd
    assert core["taxable_rmd_husband"][0, 1] == taxable
    assert core["magi"][0, 1] == taxable
    assert core["pre_tax_assets"][0, 1] == 246_000 - qcd - taxable
    assert core["post_tax_assets"][0, 1] == taxable
    assert core["total_assets"][0, 1] == 246_000 - qcd


@pytest.mark.parametrize("inflation_mode", ["nominal", "real"])
def test_qcd_inflation_and_age_window_propagate_to_every_year(run_financial_case, inflation_mode):
    settings = make_simulation().qcd_settings
    settings["husband"].update(enabled=True, amount=1_000, start_age=72, end_age=73)
    core = run_financial_case(husband=dict(age=70, retire_age=60), h_assets=dict(equity_pre=100_000),
                              years_to_simulate=4, inflation_rate=.02, inflation_mode=inflation_mode,
                              qcd_settings=settings)
    expected = np.array([[0, 0, 1_000 * 1.02 ** 2, 1_000 * 1.02 ** 3, 0]])
    if inflation_mode == "real":
        expected[0, 2:4] = 1_000

    np.testing.assert_allclose(core["qcd_husband"], expected, rtol=0, atol=1e-10)
    np.testing.assert_array_equal(core["magi"], np.zeros((1, 5)))


def test_spouses_qcd_and_report_fields_preserve_required_versus_taxable_rmd():
    config = make_simulation(second_person_enabled=True, include_rmd=True)
    config.qcd_settings["husband"].update(enabled=True, amount=5_000)
    config.qcd_settings["wife"].update(enabled=True, amount=15_000)
    husband = make_person(age=74, retire_age=60)
    wife = make_person(age=74, retire_age=60)
    pipeline = run_pipeline(make_portfolio(equity_pre=246_000), make_portfolio(equity_pre=246_000),
                            husband, wife, DynamicExpenses(), config)
    summary = pipeline["summary_results"]
    assert summary["qcd_husband"][1] == 5_000
    assert summary["qcd_wife"][1] == 15_000
    assert summary["taxable_rmd_husband"][1] == 5_000
    assert summary["taxable_rmd_wife"][1] == 0
    assert summary["magi"][1] == 5_000
    rows = run_sim_tax_report._build_yearly_tax_rows(summary, husband, wife, config)
    assert rows[0]["QCD"] == 20_000
    assert rows[0]["Husband QCD"] == 5_000
    assert rows[0]["Wife QCD"] == 15_000
    totals = run_sim_tax_report._build_rmd_summary(summary, True)
    assert totals["Lifetime Required RMD"] == 20_000
    assert totals["Lifetime QCD"] == 20_000
    assert totals["Lifetime Taxable RMD"] == 5_000
    year_row = run_sim_year_by_year_report._build_year_row(summary, 1, husband, wife, config)
    assert year_row["QCD"] == 20_000
    assert year_row["Taxable RMD"] == 5_000
    totals = run_sim_summary_report._build_simulation_totals(summary)
    assert totals["Total QCDs"] == 20_000
    assert totals["Total Taxable RMDs"] == 5_000
    milestone = run_sim_summary_report._build_income_milestone(summary, 1)
    assert milestone["Taxable RMD"] == 5_000
