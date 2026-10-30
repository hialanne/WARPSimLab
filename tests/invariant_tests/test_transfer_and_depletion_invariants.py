"""Transfers cannot create wealth; discretionary spending respects account priority."""

import copy

import numpy as np
import pytest

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.simulation import run_pipeline
from tests.architectural_helpers import make_person, make_portfolio, make_simulation
from tests.invariant_helpers import assert_money_equal


@pytest.mark.parametrize("expense_mode", [False, True])
@pytest.mark.parametrize("annual_return", [-.25, 0, .08])
@pytest.mark.parametrize("requested", [5_000, 100_000], ids=["partial-conversions", "exhaust-convertible-assets"])
def test_conversion_only_redistributes_sheltered_wealth_after_returns_and_fees(
    expense_mode, annual_return, requested,
):
    case = dict(
        husband_portfolio=make_portfolio(equity_pre=30_000, bond_pre=10_000, cash_pre=5_000,
            equity_roth=5_000, bond_roth=2_000, cash_roth=1_000,
            hsa_equity=1_000, hsa_bond=2_000, hsa_cash=3_000, real_estate=20_000),
        wife_portfolio=make_portfolio(), husband=make_person(age=65, retire_age=65),
        wife=make_person(), expenses=DynamicExpenses(),
        sim_config=make_simulation(years_to_simulate=4, always_use_expense_mode=expense_mode,
            include_realestate=True, use_fund_expenses=True, fund_expense=.005,
            eq_mean=annual_return, bd_mean=annual_return, cs_mean=annual_return, re_mean=annual_return),
    )
    converted_case = copy.deepcopy(case)
    converted_case["sim_config"].roth_flows = [dict(name="Internal transfer", owner="husband",
        type="roth_conversion", enabled=True, amount=requested, start_age=66, end_age=69,
        inflation_adjustment_pct=0)]
    baseline = run_pipeline(**case)["core"]
    converted = run_pipeline(**converted_case)["core"]
    for field in ("total_assets", "hsa_assets", "real_estate"):
        assert_money_equal(converted[field], baseline[field], field)
    assert_money_equal(baseline["pre_tax_assets"] - converted["pre_tax_assets"],
                       converted["roth_assets"] - baseline["roth_assets"], "balanced transfer")
    sheltered = converted["pre_tax_assets"] + converted["roth_assets"] + converted["hsa_assets"]
    assert_money_equal(sheltered[:, 1:], sheltered[:, :-1] * (1 + annual_return) * .995)
    assert_money_equal(converted["real_estate"][:, 1:], converted["real_estate"][:, :-1] * (1 + annual_return))
    assert_money_equal(converted["magi"], converted["roth_conversions"])
    assert_money_equal(converted["gross_income"], np.zeros((1, 5)))
    assert_money_equal(converted["net_income"], np.zeros((1, 5)))
    assert np.any(converted["roth_conversions"] > 0)
    assert np.all(converted["roth_conversions"][:, 1:] <= converted["pre_tax_assets"][:, :-1] + 1e-8)


@pytest.mark.parametrize("expense_mode", [False, True])
@pytest.mark.parametrize("second_person", [False, True])
@pytest.mark.parametrize("spending", [0, 500, 7_000, 100_000], ids=["rmd-only", "partial", "multiple-buckets", "depletion"])
def test_discretionary_lower_priority_draws_require_higher_priority_accounts_exhausted(
    expense_mode, second_person, spending,
):
    expenses = DynamicExpenses()
    expenses.add_expense(2027, spending)
    core = run_pipeline(
        make_portfolio(cash_post=1_000, cash_pre=2_000, cash_roth=3_000,
                       hsa_cash=4_000, real_estate=5_000),
        make_portfolio(cash_post=2_000, cash_pre=3_000, cash_roth=4_000,
                       hsa_cash=5_000, real_estate=6_000),
        make_person(age=72, retire_age=65), make_person(age=72, retire_age=65), expenses,
        make_simulation(years_to_simulate=4, always_use_expense_mode=expense_mode,
            include_rmd=True, include_realestate=True, second_person_enabled=second_person,
            retirement_withdraw_mode="Fixed Dollar Amount", retirement_withdraw_dollars=spending),
    )["core"]
    # Emergency pre-tax cash is already included in pre_tax_withdrawals.
    discretionary_pre = core["pre_tax_withdrawals"]
    for use, higher_accounts in [
        (discretionary_pre, ("post_tax_assets",)),
        (core["roth_withdrawals"], ("post_tax_assets", "pre_tax_assets")),
        (core["hsa_taxable_withdrawals"], ("post_tax_assets", "pre_tax_assets", "roth_assets")),
    ]:
        used = use > 1e-8
        for field in higher_accounts:
            assert_money_equal(core[field][used], np.zeros(np.count_nonzero(used)), field)
    estate_used = np.diff(core["real_estate"], axis=1) < -1e-8
    for field in ("post_tax_assets", "pre_tax_assets", "roth_assets", "hsa_assets"):
        assert_money_equal(core[field][:, 1:][estate_used], np.zeros(np.count_nonzero(estate_used)), field)
    # Mandatory RMDs are allowed ahead of taxable spending and are accounted
    # separately from the discretionary pre-tax draw above.
    assert_money_equal(-np.diff(core["pre_tax_assets"], axis=1), (
        discretionary_pre + core["rmd_husband"] + core["rmd_wife"])[:, 1:])
    assert_money_equal(-np.diff(core["roth_assets"], axis=1), core["roth_withdrawals"][:, 1:])
    assert_money_equal(-np.diff(core["hsa_assets"], axis=1), core["hsa_withdrawals"][:, 1:])
    if spending == 100_000:
        assert_money_equal(core["total_assets"][:, 1:], np.zeros((1, 4)))
        assert np.all(core["funding_gap"][:, 1:] > 0)
