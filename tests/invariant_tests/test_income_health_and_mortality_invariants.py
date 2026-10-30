"""Taxable-income partitions, inheritance neutrality and mortality state contracts."""

import copy

import numpy as np
import pytest

from src.warpsimlab.sim.simulation import run_pipeline
from tests.architectural_helpers import assert_tree_equal
from tests.invariant_helpers import ACCOUNT_COMPONENTS, accounting_case, assert_money_equal


@pytest.mark.parametrize("market", ["fixed", "monte_carlo", "historical"])
@pytest.mark.parametrize("expense_mode", [False, True])
def test_gross_income_and_magi_partition_cash_transfers_and_non_taxable_income(market, expense_mode):
    case = accounting_case(market=market, expense_mode=expense_mode)
    case["sim_config"].special_income_streams.append(dict(
        name="Tax-free payment", owner="husband", enabled=True, taxable=False,
        amount=1_234, start_age=0, end_age=120, adjustment_mode="none", adjustment_pct=0))
    core = run_pipeline(**case)["core"]
    income = core["breakdown_by_class"]
    # Every special stream except the added fixed payment is taxable. A stream
    # that started before the projection with no escalation stays at its amount.
    non_taxable = 1_234 * core["husband_alive"].copy()
    non_taxable[:, 0] = 0
    operating = sum(income[key] for key in (
        "work", "ss", "pension", "annuity", "rmd", "special_income",
        "bond_interest", "cash_interest", "qualified_equity_distributions"))
    taxable_income = (operating - non_taxable + core["pre_tax_withdrawals"]
                      + core["hsa_taxable_withdrawals"] + core["roth_conversions"])
    assert_money_equal(core["magi"], taxable_income, "MAGI counts taxable transfers once")
    config = case["sim_config"]
    offset = core["year"] - config.start_year
    expense_year = (core["husband_alive"] & (case["husband"].age + offset < case["husband"].retire_age))
    expense_year |= core["wife_alive"] & (case["wife"].age + offset < case["wife"].retire_age)
    expense_year |= config.always_use_expense_mode
    cash_receipts = (operating + income["withdrawal"] + income["tax_funding_withdrawal"]
                     + core["employee_401k_contributions"] + core["hsa_employee_contributions"])
    # Expense-mode emergency taxable draws have separate reporting fields;
    # retirement draws are already in withdrawal/tax-funding cash receipts.
    cash_receipts += expense_year * (core["emergency_pre_tax_used"] + core["hsa_taxable_withdrawals"])
    assert_money_equal(core["gross_income"], cash_receipts, "gross cash receipts")
    assert np.any(non_taxable > 0)
    assert np.any(core["roth_conversions"] > 0)
    assert np.any(core["irmaa"] > 0)


@pytest.mark.parametrize("market", ["monte_carlo", "historical"])
@pytest.mark.parametrize("expense_mode", [False, True])
@pytest.mark.parametrize("deceased", ["husband", "wife"])
def test_inheritance_matches_assets_already_owned_by_survivor(market, expense_mode, deceased):
    case = accounting_case(market=market, expense_mode=expense_mode)
    survivor = "wife" if deceased == "husband" else "husband"
    case[deceased].modeled_death_age = case[deceased].age + 1
    combined = {field: getattr(case["husband_portfolio"], field) + getattr(case["wife_portfolio"], field)
                for field in vars(case["husband_portfolio"])}
    for owner in ("husband", "wife"):
        for field, amount in combined.items():
            setattr(case[f"{owner}_portfolio"], field, amount if owner == deceased else 0)
    already_owned = copy.deepcopy(case)
    for field, amount in combined.items():
        setattr(already_owned[f"{deceased}_portfolio"], field, 0)
        setattr(already_owned[f"{survivor}_portfolio"], field, amount)
    inherited = run_pipeline(**case)["core"]
    direct = run_pipeline(**already_owned)["core"]
    # Death occurs before the first year's financial flows. Initial household
    # wealth and every later household result must be independent of the old owner.
    assert_tree_equal(inherited, direct)
    assert np.all(inherited[f"{deceased}_death_event"][:, 1])
    assert np.all(inherited[f"rmd_{deceased}"] == 0)


@pytest.mark.parametrize("market", ["monte_carlo", "historical"])
@pytest.mark.parametrize("deaths", ["first-year", "simultaneous", "sequential"])
def test_terminal_state_and_zero_terminal_flows_are_consistent_across_paths(market, deaths):
    case = accounting_case(market=market, expense_mode=deaths != "first-year")
    h_offset, w_offset = {"first-year": (1, 1), "simultaneous": (2, 2), "sequential": (2, 4)}[deaths]
    case["husband"].modeled_death_age = case["husband"].age + h_offset
    case["wife"].modeled_death_age = case["wife"].age + w_offset
    core = run_pipeline(**case)["core"]
    end = max(h_offset, w_offset)
    assert np.all(core["effective_end_index"] == end)
    assert np.all(core["terminal_year"] == case["sim_config"].start_year + end)
    assert core["total_assets"].shape == (3, end + 1)
    for person in ("husband", "wife"):
        alive = core[f"{person}_alive"]
        assert not np.any(np.diff(alive.astype(int), axis=1) > 0)
        np.testing.assert_array_equal(core[f"{person}_death_event"][:, 1:], alive[:, :-1] & ~alive[:, 1:])
        assert not np.any(alive[:, -1])
        assert np.all(core[f"medicare_cost_{person}"][~alive] == 0)
        assert np.all(core[f"irmaa_{person}"][~alive] == 0)
        assert np.all(core[f"rmd_{person}"][~alive] == 0)
    count = core["husband_alive"].astype(int) + core["wife_alive"].astype(int)
    np.testing.assert_array_equal(core["survivor_state"], count == 1)
    assert_money_equal(core["survivor_expense_factor"], np.where(count == 2, 1, np.where(count == 1, .75, 0)))
    for field in ("gross_income", "net_income", "taxes", "expense_amt", "fund_expenses", "medicare_cost",
                  "irmaa", "roth_conversions", "hsa_withdrawals", "pre_tax_withdrawals",
                  "ira_401k", "hsa_total_contributions", "funding_gap"):
        assert np.all(core[field][:, -1] == 0), field
    if end:
        for field in (*ACCOUNT_COMPONENTS, "real_estate", "total_assets"):
            assert_money_equal(core[field][:, -1], core[field][:, -2], field)
