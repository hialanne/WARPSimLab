"""Account composition and flow conservation across populated and depleted cases."""

import copy

import numpy as np
import pytest

from src.warpsimlab.sim.simulation import run_pipeline
from tests.invariant_helpers import ACCOUNT_COMPONENTS, accounting_case, assert_money_equal


@pytest.mark.parametrize("market", ["fixed", "monte_carlo", "historical"])
@pytest.mark.parametrize("expense_mode", [False, True])
@pytest.mark.parametrize("balance_scale", [0.01, 1.0], ids=["stressed", "funded"])
def test_all_account_components_and_flow_partitions_reconcile_on_every_path(
    market, expense_mode, balance_scale,
):
    case = accounting_case(market=market, expense_mode=expense_mode, balance_scale=balance_scale)
    core = run_pipeline(**case)["core"]
    for account, components in ACCOUNT_COMPONENTS.items():
        assert_money_equal(core[account], sum(core[key] for key in components), account)
        for key in (account, *components):
            assert np.all(np.isfinite(core[key])), key
            assert np.all(core[key] >= -1e-8), key
    assert_money_equal(core["total_assets"], sum(core[key] for key in ACCOUNT_COMPONENTS) + core["real_estate"])
    assert_money_equal(core["cash"], sum(core[components[2]] for components in ACCOUNT_COMPONENTS.values()))
    assert_money_equal(core["bonds"], sum(core[components[1]] for components in ACCOUNT_COMPONENTS.values()))
    for total, parts in {
        "taxes": ("federal_ordinary_tax", "federal_qualified_dividend_tax", "state_income_tax", "payroll_tax"),
        "payroll_tax": ("social_security_payroll_tax", "medicare_tax", "additional_medicare_tax"),
        "medicare_cost": ("medicare_cost_husband", "medicare_cost_wife"),
        "irmaa": ("irmaa_husband", "irmaa_wife"),
        "hsa_withdrawals": ("hsa_qualified_withdrawals", "hsa_taxable_withdrawals"),
        "hsa_total_contributions": ("hsa_employee_contributions", "hsa_employer_contributions"),
        "roth_total_flows": ("roth_ira_contributions", "roth_workplace_contributions", "roth_conversions"),
        "final_tax_delta": ("final_tax_delta_deducted", "final_tax_delta_uncovered"),
    }.items():
        assert_money_equal(core[total], sum(core[key] for key in parts), total)
    assert_money_equal(core["breakdown_by_class"]["rmd"], core["rmd_husband"] + core["rmd_wife"])
    if expense_mode:
        assert_money_equal(core["funding_gap"], core["uncovered_expense"] + core["final_tax_delta_uncovered"])
    else:
        # Retirement mode can additionally have unfunded baseline tax cash.
        assert np.all(core["funding_gap"] + 1e-8 >= core["uncovered_expense"] + core["final_tax_delta_uncovered"])
    assert np.any(core["taxes"] > 0)
    assert np.any(core["hsa_total_contributions"] > 0)
    assert np.any(core["survivor_state"])
    assert core["total_assets"].shape[0] == (1 if market == "fixed" else 3)


@pytest.mark.parametrize("expense_mode", [False, True])
@pytest.mark.parametrize("second_person", [False, True])
@pytest.mark.parametrize("balance_scale", [0, 0.01, 1], ids=["initially-empty", "stressed", "funded"])
def test_zero_market_account_rollforwards_include_transfers_and_actual_funded_flows(
    expense_mode, second_person, balance_scale,
):
    case = accounting_case(
        expense_mode=expense_mode, second_person_enabled=second_person, balance_scale=balance_scale,
        eq_mean=0, bd_mean=0, cs_mean=0, re_mean=0, use_fund_expenses=False,
        post_tax_equity_dividend_yield=0, post_tax_bond_interest_yield=0, post_tax_cash_interest_yield=0,
    )
    core = run_pipeline(**case)["core"]
    rmd = core["rmd_husband"] + core["rmd_wife"]
    assert_money_equal(np.diff(core["pre_tax_assets"], axis=1), (
        core["ira_401k"] - rmd - core["roth_conversions"]
        - core["pre_tax_withdrawals"])[:, 1:], "pre-tax roll-forward")
    # Emergency pre-tax cash is reported in pre_tax_withdrawals too, not a
    # second withdrawal. Retirement mode may have other pre-tax withdrawals.
    assert np.all(core["pre_tax_withdrawals"] + 1e-8 >= core["emergency_pre_tax_used"])
    assert_money_equal(np.diff(core["roth_assets"], axis=1), (
        core["roth_conversions"] + core["roth_ira_contributions"]
        + core["roth_workplace_contributions"] - core["roth_withdrawals"])[:, 1:], "Roth roll-forward")
    assert_money_equal(np.diff(core["hsa_assets"], axis=1), (
        core["hsa_total_contributions"] - core["hsa_withdrawals"])[:, 1:], "HSA roll-forward")
    if expense_mode:
        income = core["breakdown_by_class"]
        # Work is already reduced by employee contributions. Restore those
        # and include employer contributions to measure outside wealth inflow.
        outside_inflow = (income["work"] + core["ira_401k"] + core["hsa_total_contributions"]
                          + income["ss"] + income["pension"] + income["annuity"] + income["special_income"])
        # RMDs, conversions and Roth contributions are internal transfers.
        # Funding gaps represent obligations that did not consume assets.
        net_external = (outside_inflow - core["expense_amt"] - core["medicare_cost"]
                        - core["irmaa"] - core["taxes"] + core["funding_gap"])
        assert_money_equal(np.diff(core["total_assets"], axis=1), net_external[:, 1:], "household cash conservation")


@pytest.mark.parametrize("market", ["fixed", "monte_carlo", "historical"])
@pytest.mark.parametrize("expense_mode", [False, True])
@pytest.mark.parametrize("balance_scale", [.01, 1], ids=["stressed", "funded"])
def test_fee_removes_exactly_its_share_of_post_flow_investments_without_changing_cash_flows(
    market, expense_mode, balance_scale,
):
    # At a single-year boundary, both counterfactuals see identical opening
    # wealth, market returns, contributions, conversions, withdrawals and taxes.
    # The documented final fee applies uniformly to investments, excluding RE.
    case = accounting_case(market=market, expense_mode=expense_mode, balance_scale=balance_scale,
                           years_to_simulate=1, use_fund_expenses=False)
    if not expense_mode:
        for owner in ("husband", "wife"):
            case[owner].retire_age = case[owner].age
    with_fee = copy.deepcopy(case)
    fee = .013
    with_fee["sim_config"].use_fund_expenses = True
    with_fee["sim_config"].fund_expense = fee
    baseline = run_pipeline(**case)["core"]
    charged = run_pipeline(**with_fee)["core"]
    before_fee = sum(baseline[key][:, 1] for key in ACCOUNT_COMPONENTS)
    for account in ACCOUNT_COMPONENTS:
        assert_money_equal(charged[account][:, 1], baseline[account][:, 1] * (1 - fee), account)
    assert_money_equal(charged["real_estate"], baseline["real_estate"])
    assert_money_equal(charged["fund_expenses"][:, 1], before_fee * fee)
    assert_money_equal(baseline["total_assets"][:, 1] - charged["total_assets"][:, 1], before_fee * fee)
    for field in ("gross_income", "net_income", "taxes", "magi", "expense_amt", "funding_gap",
                  "roth_conversions", "roth_withdrawals", "pre_tax_withdrawals", "hsa_withdrawals",
                  "ira_401k", "hsa_total_contributions", "medicare_cost", "irmaa"):
        assert_money_equal(charged[field], baseline[field], field)
    if balance_scale == .01 and not expense_mode:
        # Mandatory health/tax funding exhausts this small retirement account
        # before the fee stage. Unfunded obligations cannot generate a fee.
        assert_money_equal(before_fee, np.zeros_like(before_fee))
        assert np.all(charged["fund_expenses"] == 0)
        assert np.all(charged["funding_gap"][:, 1] > 0)
    else:
        assert np.any(charged["fund_expenses"] > 0)
