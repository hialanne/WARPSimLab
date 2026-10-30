"""Hand-calculated expense-mode Roth reporting through the real pipeline."""

import numpy as np
import pytest

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.simulation import run_pipeline
from tests.architectural_helpers import make_person, make_portfolio, make_simulation


@pytest.mark.parametrize("married", [False, True], ids=["single", "married"])
@pytest.mark.parametrize(
    "annual_expense,withdrawals,roth,taxable,total,gap",
    [
        (0, [0, 0, 0, 0], [9000, 9000, 9000, 9000],
         [2000, 2000, 2000, 2000], [11000, 11000, 11000, 11000], [0, 0, 0, 0]),
        (4000, [0, 2000, 4000, 3000], [9000, 7000, 3000, 0],
         [2000, 0, 0, 0], [11000, 7000, 3000, 0], [0, 0, 0, 1000]),
        (15000, [0, 9000, 0, 0], [9000, 0, 0, 0],
         [2000, 0, 0, 0], [11000, 0, 0, 0], [0, 4000, 15000, 15000]),
    ],
    ids=["no-shortfall", "partial-then-exhausted", "immediate-exhaustion"],
)
def test_expense_roth_reporting_matches_actual_funding(
    married, annual_expense, withdrawals, roth, taxable, total, gap,
):
    # Taxable cash funds expenses first. Only actual Roth cash spent is reported;
    # unfunded expenses after exhaustion must not create fictitious withdrawals.
    husband_assets = make_portfolio(cash_post=2000, cash_roth=6000 if married else 9000)
    wife_assets = make_portfolio(cash_roth=3000 if married else 0)
    expenses = DynamicExpenses()
    expenses.add_expense(2027, annual_expense)
    config = make_simulation(
        years_to_simulate=3, second_person_enabled=married,
        tax_filing_status="Married filing jointly" if married else "Single",
        calculate_income_taxes=True, calculate_payroll_taxes=True,
        calculate_state_taxes=True, state_of_residence="CO",
        husband_portfolio=husband_assets, wife_portfolio=wife_assets,
        always_use_expense_mode=True, retirement_withdraw_mode="Off",
    )
    core = run_pipeline(
        husband_assets, wife_assets, make_person(age=70, retire_age=70),
        make_person(age=70, retire_age=70), expenses, config,
    )["core"]

    for field, expected in [
        ("year", [2026, 2027, 2028, 2029]),
        ("roth_withdrawals", withdrawals), ("roth_assets", roth),
        ("post_tax_assets", taxable), ("total_assets", total), ("funding_gap", gap),
    ]:
        assert core[field].shape == (1, 4), field
        # Proportional spouse funding can leave sub-picodollar roundoff.
        np.testing.assert_allclose(core[field], [expected], rtol=0, atol=1e-9, err_msg=field)
    # Zero growth/contributions make the Roth balance reduction an independent
    # reconciliation of the reporting array, including year zero and later years.
    np.testing.assert_allclose(core["roth_withdrawals"][:, 1:],
                               -np.diff(core["roth_assets"], axis=1), rtol=0, atol=1e-9)
    for field in ["taxes", "federal_ordinary_tax", "state_income_tax", "magi",
                  "pre_tax_withdrawals", "emergency_pre_tax_used", "hsa_withdrawals"]:
        np.testing.assert_array_equal(core[field], np.zeros((1, 4)), err_msg=field)
