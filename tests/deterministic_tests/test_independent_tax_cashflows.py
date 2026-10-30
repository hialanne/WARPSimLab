"""Dollar oracles for WARPSimLab's documented planning-grade tax model.

Constants below deliberately stand apart from production tax functions/tables.
These are simulator regression expectations, not a claim of full tax-law fidelity.
"""

import numpy as np
import pytest


@pytest.mark.parametrize("pension,dividend,federal,qualified", [
    # Unused ordinary deduction shelters dividends before the 0% band.
    (0, 70_000, 0, (70_000 - 16_100 - 48_350) * .15),
    # Ordinary taxable income 43,900 leaves 4,450 of the 0% dividend band.
    (60_000, 10_000, 1_240 + 31_500 * .12, (10_000 - 4_450) * .15),
    # Ordinary taxable income is above the top qualified-dividend threshold.
    (600_000, 20_000,
     1_240 + 4_560 + 12_166 + 23_058 + 17_424 + 327_675 * .35, 20_000 * .20),
])
def test_dividend_stacking_state_tax_and_cash_deposit_have_independent_dollar_oracles(
    run_financial_case, pension, dividend, federal, qualified,
):
    # A 2% total equity return equals the dividend yield: price return is zero.
    starting_equity = dividend / .02
    result = run_financial_case(
        husband=dict(age=65, retire_age=65, pension=pension, pension_age=65),
        h_assets=dict(equity_post=starting_equity), eq_mean=.02,
        post_tax_equity_dividend_yield=.02, calculate_income_taxes=True,
        calculate_state_taxes=True, state_of_residence="CO",
    )
    state_tax = (pension + dividend) * .044
    total_tax = federal + qualified + state_tax
    assert result["qualified_equity_distributions"][0, 1] == pytest.approx(dividend, rel=0, abs=1e-7)
    assert result["federal_ordinary_tax"][0, 1] == pytest.approx(federal, rel=0, abs=1e-7)
    assert result["federal_qualified_dividend_tax"][0, 1] == pytest.approx(qualified, rel=0, abs=1e-7)
    assert result["state_income_tax"][0, 1] == pytest.approx(state_tax, rel=0, abs=1e-7)
    assert result["taxes"][0, 1] == pytest.approx(total_tax, rel=0, abs=1e-7)
    assert result["magi"][0, 1] == pytest.approx(pension + dividend, rel=0, abs=1e-7)
    assert result["net_income"][0, 1] == pytest.approx(pension + dividend - total_tax, rel=0, abs=1e-7)
    assert result["post_tax_assets"][0, 1] == pytest.approx(starting_equity + pension + dividend - total_tax, rel=0, abs=1e-7)
    assert result["payroll_tax"][0, 1] == 0


# Tax due exactly at each upper taxable-income boundary, independently summed.
@pytest.mark.parametrize("status,deduction,boundary,tax_at_boundary,rate_below,rate_above", [
    ("Single", 16_100, 105_700, 17_966, .22, .24),
    ("Single", 16_100, 201_775, 41_024, .24, .32),
    ("Single", 16_100, 256_225, 58_448, .32, .35),
    ("Single", 16_100, 640_600, 192_979.25, .35, .37),
    ("Married filing jointly", 32_200, 211_400, 35_932, .22, .24),
    ("Married filing jointly", 32_200, 403_550, 82_048, .24, .32),
    ("Married filing jointly", 32_200, 512_450, 116_896, .32, .35),
    ("Married filing jointly", 32_200, 768_700, 206_583.5, .35, .37),
])
@pytest.mark.parametrize("offset", [0, .01], ids=["at-boundary", "one-cent-over"])
def test_conversion_crosses_high_federal_brackets_without_creating_spendable_cash(
    run_financial_case, status, deduction, boundary, tax_at_boundary, rate_below, rate_above, offset,
):
    ordinary = deduction + boundary + offset
    pension = ordinary - 1_000
    federal = tax_at_boundary + offset * rate_above
    result = run_financial_case(
        husband=dict(age=65, retire_age=65, pension=pension, pension_age=65),
        h_assets=dict(cash_pre=1_000), second_person_enabled=status != "Single",
        tax_filing_status=status, calculate_income_taxes=True,
        roth_flows=[dict(name="Bracket crossing", owner="husband", enabled=True, type="roth_conversion", amount=1_000,
                         start_age=66, end_age=66, inflation_adjustment_pct=0)],
    )
    assert result["federal_ordinary_tax"][0, 1] == pytest.approx(federal, rel=0, abs=1e-7)
    assert result["tax_bracket"][0, 1] == (rate_above if offset else rate_below)
    assert result["magi"][0, 1] == pytest.approx(ordinary, rel=0, abs=1e-7)
    assert result["gross_income"][0, 1] == pytest.approx(pension, rel=0, abs=1e-7)
    assert result["pre_tax_assets"][0, 1] == 0
    assert result["roth_assets"][0, 1] == 1_000
    assert result["post_tax_assets"][0, 1] == pytest.approx(pension - federal, rel=0, abs=1e-7)
    assert result["total_assets"][0, 1] == pytest.approx(1_000 + pension - federal, rel=0, abs=1e-7)


@pytest.mark.parametrize("deceased", ["husband", "wife"])
@pytest.mark.parametrize("dollar_mode", ["nominal", "real"])
def test_survivor_progressive_state_brackets_change_after_death_year_with_inflation(
    run_financial_case, deceased, dollar_mode,
):
    survivor = "wife" if deceased == "husband" else "husband"
    people = {deceased: dict(age=70, modeled_death_age=72),
              survivor: dict(age=70, pension=10_000, pension_age=70)}
    result = run_financial_case(
        **people, years_to_simulate=3, inflation_rate=.10, inflation_mode=dollar_mode,
        second_person_enabled=True, tax_filing_status="Married filing jointly",
        calculate_income_taxes=True, calculate_state_taxes=True, state_of_residence="AL",
    )
    # Joint brackets at 1.1 and 1.21 times (1,000, 6,000); then single
    # brackets at 1.331 times (500, 3,000). Pension has no COLA.
    state = np.array([0, 22 + 220 + 3_400 * .05,
                      24.2 + 242 + 2_740 * .05,
                      13.31 + 133.1 + 6_007 * .05])
    factors = np.array([1, 1.1, 1.21, 1.331]) if dollar_mode == "real" else np.ones(4)
    income = np.array([0, 10_000, 10_000, 10_000])
    assert result["filing_status_single"][0].tolist() == [False, False, False, True]
    assert result["state_income_tax"][0] == pytest.approx(state / factors, rel=0, abs=1e-7)
    assert result["federal_ordinary_tax"][0] == pytest.approx(np.zeros(4), rel=0, abs=1e-7)
    assert result["total_assets"][0] == pytest.approx(np.cumsum(income - state) / factors, rel=0, abs=1e-7)
    assert result[f"net_income_{deceased}"][0] == pytest.approx(np.zeros(4), rel=0, abs=1e-7)


def test_survivor_additional_medicare_threshold_uses_hsa_adjusted_wages(run_financial_case):
    result = run_financial_case(
        husband=dict(age=40, modeled_death_age=42),
        wife=dict(age=40, retire_age=65, income=225_000, annual_hsa_contribution=5_000),
        second_person_enabled=True, tax_filing_status="Married filing jointly",
        calculate_payroll_taxes=True, years_to_simulate=3,
    )
    # HSA salary reduction gives 220,000 payroll wages. The 184,500 wage
    # base is per worker; Additional Medicare switches from 250k to 200k.
    payroll = np.array([0, 184_500 * .062 + 220_000 * .0145,
                        184_500 * .062 + 220_000 * .0145,
                        184_500 * .062 + 220_000 * .0145 + 20_000 * .009])
    assert result["additional_medicare_tax"][0] == pytest.approx([0, 0, 0, 180], rel=0, abs=1e-7)
    assert result["payroll_tax"][0] == pytest.approx(payroll, rel=0, abs=1e-7)
    assert result["hsa_assets"][0] == pytest.approx([0, 5_000, 10_000, 15_000], rel=0, abs=1e-7)
    assert result["magi"][0] == pytest.approx([0, 220_000, 220_000, 220_000], rel=0, abs=1e-7)
    assert result["post_tax_assets"][0] == pytest.approx(np.cumsum([0, 220_000, 220_000, 220_000]) - np.cumsum(payroll), rel=0, abs=1e-7)
    assert result["total_assets"][0] == pytest.approx(np.cumsum([0, 225_000, 225_000, 225_000]) - np.cumsum(payroll), rel=0, abs=1e-7)
