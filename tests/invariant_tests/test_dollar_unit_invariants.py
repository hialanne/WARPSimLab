"""Currency-unit changes preserve path economics, metadata and lagged tax history."""

import copy
import csv
from pathlib import Path

import numpy as np
import pytest

from src.warpsimlab.sim.simulation import run_pipeline
from tests.invariant_helpers import ACCOUNT_COMPONENTS, accounting_case, assert_money_equal


MONEY_FIELDS = (
    "total_assets", "cash", "bonds", "real_estate", "gross_income", "net_income", "net_profit",
    "net_income_husband", "net_income_wife", "expense_amt", "taxes", "taxable_ordinary_income",
    "federal_ordinary_tax", "federal_qualified_dividend_tax", "state_income_tax", "payroll_tax",
    "social_security_payroll_tax", "medicare_tax", "additional_medicare_tax", "fund_expenses",
    "employee_401k_contributions", "ira_401k", "hsa_employee_contributions", "hsa_employer_contributions",
    "hsa_total_contributions", "roth_ira_contributions", "roth_workplace_contributions",
    "roth_conversions", "roth_total_flows", "rmd_husband", "rmd_wife", "pre_tax_withdrawals",
    "emergency_pre_tax_used", "roth_withdrawals", "hsa_withdrawals", "hsa_qualified_withdrawals",
    "hsa_taxable_withdrawals", "cash_flow_shortfall", "funding_gap", "uncovered_expense",
    "final_tax_delta", "final_tax_delta_deducted", "final_tax_delta_uncovered",
    "medicare_cost", "medicare_cost_husband", "medicare_cost_wife", "magi",
    "irmaa", "irmaa_husband", "irmaa_wife", "irmaa_lookback_magi",
    "qualified_equity_distributions", "bond_interest", "cash_interest",
)


def discount_factors(case, core, market):
    """Derive currency factors from public inputs and raw CSV data, not engines."""
    config = case["sim_config"]
    years = core["total_assets"].shape[1]
    if market != "historical":
        row = (1 + config.inflation_rate + config.inflation_delta) ** np.arange(years)
        return np.broadcast_to(row, core["total_assets"].shape)
    filename = Path(__file__).resolve().parents[2] / "src/warpsimlab/dataFiles" / config.historical_inflation_file
    with filename.open(encoding="utf-8-sig", newline="") as source:
        rates = {int(row["Year"]): float(row["Inflation_Rate_Pct"]) / 100 for row in csv.DictReader(source)}
    factors = []
    for start in core["historical_window_start_year"]:
        steps = [1 + rates[int(start) + offset] + config.inflation_delta for offset in range(years - 1)]
        factors.append(np.r_[1.0, np.cumprod(steps)])
    return np.array(factors)


@pytest.mark.parametrize("market,inflation", [
    ("monte_carlo", -.02), ("monte_carlo", .03), ("historical", .99),
], ids=["deflation", "inflation", "historical-window-units"])
@pytest.mark.parametrize("expense_mode", [False, True])
def test_real_and_nominal_are_same_financial_paths_in_different_currency_units(market, inflation, expense_mode):
    nominal_case = accounting_case(market=market, expense_mode=expense_mode,
                                   inflation_rate=inflation, inflation_delta=.005)
    real_case = copy.deepcopy(nominal_case)
    real_case["sim_config"].inflation_mode = "real"
    nominal = run_pipeline(**nominal_case)["core"]
    real = run_pipeline(**real_case)["core"]
    factors = discount_factors(nominal_case, nominal, market)
    fields = [*MONEY_FIELDS, *ACCOUNT_COMPONENTS,
              *(field for components in ACCOUNT_COMPONENTS.values() for field in components)]
    for field in fields:
        assert_money_equal(real[field], nominal[field] / factors, field)
    for field, value in nominal["breakdown_by_class"].items():
        assert_money_equal(real["breakdown_by_class"][field], value / factors, field)
    for field in ("year", "tax_bracket", "husband_alive", "wife_alive", "husband_death_event", "wife_death_event",
                  "survivor_state", "survivor_expense_factor", "filing_status_single", "irmaa_level",
                  "irmaa_lookback_available", "irmaa_filing_status_single", "terminal_year", "effective_end_index",
                  "historical_window_start_year", "historical_window_end_year"):
        np.testing.assert_array_equal(real[field], nominal[field], err_msg=field)
    for field in ("federal_bracket_lower_threshold", "federal_bracket_upper_threshold",
                  "irmaa_lower_threshold", "irmaa_upper_threshold"):
        monetary = nominal[field] >= 0
        assert_money_equal(real[field][monetary], (nominal[field] / factors)[monetary], field)
        if field.startswith("federal"):
            # Federal unavailable/unbounded sentinels are explicitly preserved.
            np.testing.assert_array_equal(real[field][~monetary], nominal[field][~monetary])
    # Real-dollar lookback MAGI is expressed in the assessment year's dollars;
    # translate both sides back to nominal before comparing two-year history.
    available = real["irmaa_lookback_available"][:, 3:]
    assert np.any(available)
    assert_money_equal((real["irmaa_lookback_magi"] * factors)[:, 3:][available],
                       (real["magi"] * factors)[:, 1:-2][available], "IRMAA lag across dollar units")
    if market == "historical":
        assert not np.array_equal(factors[0], factors[1])
