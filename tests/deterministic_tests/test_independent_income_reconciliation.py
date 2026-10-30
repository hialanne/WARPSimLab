"""Extend the existing spouse/household net-income contract to Roth conversions."""

import pytest


@pytest.mark.parametrize("expense_mode", [True, False], ids=["expenses", "retirement"])
def test_non_cash_conversion_does_not_inflate_sum_of_spouse_net_incomes(run_financial_case, expense_mode):
    result = run_financial_case(
        husband=dict(age=65, retire_age=65, pension=40_000, pension_age=65),
        wife=dict(age=65, retire_age=65, pension=20_000, pension_age=65),
        h_assets=dict(cash_pre=10_000), second_person_enabled=True,
        tax_filing_status="Married filing jointly", calculate_income_taxes=True,
        always_use_expense_mode=expense_mode,
        roth_flows=[dict(name="Noncash conversion", owner="husband", enabled=True,
                         type="roth_conversion", amount=10_000, start_age=66, end_age=66,
                         inflation_adjustment_pct=0)],
    )
    # 70k taxable ordinary receipts, 32,200 deduction: 24,800 at 10%,
    # remaining 13,000 at 12%. Cash is the 60k pensions, excluding conversion.
    federal = 2_480 + 13_000 * .12
    assert result["federal_ordinary_tax"][0, 1] == pytest.approx(federal, rel=0, abs=1e-7)
    assert result["gross_income"][0, 1] == 60_000
    assert result["net_income"][0, 1] == pytest.approx(60_000 - federal, rel=0, abs=1e-7)
    assert result["roth_assets"][0, 1] == 10_000
    person_sum = result["net_income_husband"][0, 1] + result["net_income_wife"][0, 1]
    assert person_sum == pytest.approx(60_000 - federal, rel=0, abs=1e-7)
