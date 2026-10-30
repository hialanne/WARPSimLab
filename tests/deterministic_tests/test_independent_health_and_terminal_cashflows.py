"""HSA/IRMAA cliffs and final-year asset accounting with nonzero market flows."""

import numpy as np
import pytest


@pytest.mark.parametrize("qualified,taxable,irmaa", [
    (11_000, 109_000, 0), (10_999.99, 109_000.01, 1_147.92),
])
def test_hsa_qualified_split_controls_tax_and_two_year_irmaa_cliff(
    run_financial_case, qualified, taxable, irmaa,
):
    result = run_financial_case(
        husband=dict(age=65, retire_age=65), h_assets=dict(hsa_cash=200_000),
        years_to_simulate=3, calculate_income_taxes=True, irmaa_enabled=True,
        historical_magi=dict(two_years_prior=0, one_year_prior=0),
        expenses=[dict(start_year=2027, end_year=2027, cost=qualified, is_hsa_eligible=True),
                  dict(start_year=2027, end_year=2027, cost=120_000 - qualified)],
    )
    # Qualified spending is excluded from MAGI. The rest uses taxable HSA cash.
    # 2026 model: taxable ordinary income = MAGI - 16,100, in the 22% band.
    federal = 1_240 + 4_560 + (taxable - 16_100 - 50_400) * .22
    # No taxable cash remains to pay the one-pass additional tax in year 1.
    assert result["hsa_qualified_withdrawals"][0] == pytest.approx([0, qualified, 0, 0], rel=0, abs=1e-7)
    assert result["hsa_taxable_withdrawals"][0] == pytest.approx([0, taxable, 0, irmaa], rel=0, abs=1e-7)
    assert result["federal_ordinary_tax"][0] == pytest.approx([0, federal, 0, 0], rel=0, abs=1e-7)
    assert result["funding_gap"][0] == pytest.approx([0, federal, 0, 0], rel=0, abs=1e-7)
    assert result["magi"][0] == pytest.approx([0, taxable, 0, irmaa], rel=0, abs=1e-7)
    assert result["irmaa_lookback_magi"][0, 3] == pytest.approx(taxable, rel=0, abs=1e-7)
    assert result["irmaa"][0] == pytest.approx([0, 0, 0, irmaa], rel=0, abs=1e-7)
    assert result["hsa_assets"][0] == pytest.approx([200_000, 80_000, 80_000, 80_000 - irmaa], rel=0, abs=1e-7)


@pytest.mark.parametrize("annual_return,post,other,estate,fee", [
    (.10, 7_722, 1_089, 1_100, 111),
    (-.20, 6_098.4, 792, 800, 85.6),
])
@pytest.mark.parametrize("dollar_mode", ["nominal", "real"])
def test_terminal_year_freezes_all_buckets_before_returns_fees_and_scheduled_flows(
    run_financial_case, annual_return, post, other, estate, fee, dollar_mode,
):
    result = run_financial_case(
        husband=dict(age=60, retire_age=60, modeled_death_age=62, pension=10_000,
                     pension_age=60, medicare_start_age=60, medicare_annual_cost=1_000),
        h_assets=dict(cash_post=1_000, cash_pre=1_000, cash_roth=1_000,
                      hsa_cash=1_000, real_estate=1_000),
        years_to_simulate=4, inflation_rate=.10, inflation_mode=dollar_mode,
        cs_mean=annual_return, re_mean=annual_return,
        include_realestate=True, use_fund_expenses=True, fund_expense=.01,
        expenses=[dict(start_year=2027, cost=2_000)],
        roth_flows=[dict(name="Not after death", owner="husband", enabled=True,
                         type="roth_conversion", amount=500, start_age=62, end_age=62,
                         inflation_adjustment_pct=0)],
    )
    factors = np.array([1, 1.1, 1.21]) if dollar_mode == "real" else np.ones(3)
    # First year: expense 2,200 and Medicare 1,100. Positive taxable cash
    # returns are income on the opening 1,000; negative returns reduce the
    # post-flow cash balance. Fees cover all investment buckets, excluding RE.
    for key, expected in [("post_tax_assets", post), ("pre_tax_assets", other),
                          ("roth_assets", other), ("hsa_assets", other), ("real_estate", estate)]:
        assert result[key][0] == pytest.approx(np.array([1_000, expected, expected]) / factors, rel=0, abs=1e-7), key
    total = post + 3 * other + estate
    assert result["total_assets"][0] == pytest.approx(np.array([5_000, total, total]) / factors, rel=0, abs=1e-7)
    assert result["gross_income"][0] == pytest.approx(np.array([0, 10_100 if annual_return > 0 else 10_000, 0]) / factors, rel=0, abs=1e-7)
    assert result["medicare_cost"][0] == pytest.approx(np.array([0, 1_100, 0]) / factors, rel=0, abs=1e-7)
    assert result["expense_amt"][0] == pytest.approx(np.array([0, 2_200, 0]) / factors, rel=0, abs=1e-7)
    assert result["fund_expenses"][0] == pytest.approx(np.array([0, fee, 0]) / factors, rel=0, abs=1e-7)
    assert result["roth_conversions"][0] == pytest.approx([0, 0, 0], rel=0, abs=1e-7)
    assert result["terminal_year"].tolist() == [2028]
    assert result["year"].tolist() == [[2026, 2027, 2028]]


@pytest.mark.parametrize("premium,remaining_roth,roth_spent,gap", [
    (3_000, 49_832.08, 167.92, 0),
    (70_000, 0, 50_000, 17_167.92),
])
def test_retirement_conversion_tax_funding_competes_with_medicare_and_irmaa(
    run_financial_case, premium, remaining_roth, roth_spent, gap,
):
    result = run_financial_case(
        husband=dict(age=65, retire_age=65, medicare_annual_cost=premium),
        h_assets=dict(cash_pre=50_000, cash_post=10_000),
        always_use_expense_mode=False, retirement_withdraw_mode="Off",
        calculate_income_taxes=True, calculate_state_taxes=True, state_of_residence="CO",
        irmaa_enabled=True, historical_magi=dict(two_years_prior=110_000, one_year_prior=0),
        roth_flows=[dict(name="Conversion with health costs", owner="husband", enabled=True,
                         type="roth_conversion", amount=50_000, start_age=66, end_age=66,
                         inflation_adjustment_pct=0)],
    )
    # Conversion: 50k - 16,100 deduction; federal 1,240 + 21,500*.12 = 3,820,
    # state 50k*.044 = 2,200. Neither Roth nor taxable cash withdrawals add MAGI.
    # Health costs draw first. In the affordable case, 5,852.08 taxable cash
    # remains for 6,020 tax; the remaining 167.92 tax comes from Roth.
    # At 70k premium all 60k assets deplete, leaving 11,147.92 health costs
    # plus the 6,020 tax unpaid.
    assert result["medicare_cost"][0, 1] == premium
    assert result["irmaa"][0, 1] == pytest.approx(1_147.92, rel=0, abs=1e-7)
    assert result["federal_ordinary_tax"][0, 1] == 3_820
    assert result["state_income_tax"][0, 1] == 2_200
    assert result["magi"][0, 1] == 50_000
    assert result["roth_withdrawals"][0, 1] == pytest.approx(roth_spent, rel=0, abs=1e-7)
    assert result["roth_assets"][0, 1] == pytest.approx(remaining_roth, rel=0, abs=1e-7)
    assert result["pre_tax_assets"][0, 1] == 0
    assert result["post_tax_assets"][0, 1] == 0
    assert result["funding_gap"][0, 1] == pytest.approx(gap, rel=0, abs=1e-7)
    assert result["total_assets"][0, 1] == pytest.approx(remaining_roth, rel=0, abs=1e-7)
