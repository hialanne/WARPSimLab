"""Delayed special-income escalation, taxability, and purchasing-power oracles."""

import numpy as np
import pytest


@pytest.mark.parametrize("adjustment_mode,adjustment_pct,third_year", [
    ("none", 0, 12_100), ("fixed", 8, 13_068), ("inflation", 25, 12_402.5),
])
@pytest.mark.parametrize("taxable", [True, False], ids=["taxable", "non-taxable"])
@pytest.mark.parametrize("dollar_mode", ["nominal", "real"])
def test_delayed_special_income_escalation_and_tax_cashflow(
    run_financial_case, adjustment_mode, adjustment_pct, third_year, taxable, dollar_mode,
):
    result = run_financial_case(
        husband=dict(age=60, retire_age=60, pension=50_000, pension_age=60),
        years_to_simulate=4, inflation_rate=.10, inflation_mode=dollar_mode,
        calculate_income_taxes=True, calculate_payroll_taxes=True,
        calculate_state_taxes=True, state_of_residence="CO",
        special_income_streams=[dict(name="Delayed payment", owner="husband", amount=10_000,
            start_age=62, end_age=63, enabled=True, taxable=taxable,
            adjustment_mode=adjustment_mode, adjustment_pct=adjustment_pct)],
    )
    # Today's-dollar amount inflates through its start: 10,000 * 1.1**2.
    # Subsequent steps are respectively 1, 1.08, or 1 + .10*.25.
    # Start and end ages are inclusive; the fourth simulation year is outside.
    factors = np.array([1, 1.1, 1.21, 1.331, 1.4641])
    special = np.array([0, 0, 12_100, third_year, 0])
    pension = np.array([0, 50_000, 50_000, 50_000, 50_000])
    ordinary = pension + special if taxable else pension
    gross = pension + special
    # Every paid year stays in the 12% ordinary bracket. Deduction and first
    # bracket inflate fully; fixed pension and stream escalation remain separate.
    federal = np.zeros(5)
    federal[1:] = 1_240 * factors[1:] + (ordinary[1:] - 28_500 * factors[1:]) * .12
    state = ordinary * .044
    discount = factors if dollar_mode == "real" else np.ones(5)
    assert result["breakdown_by_class"]["special_income"][0] == pytest.approx(special / discount, rel=0, abs=1e-7)
    assert result["gross_income"][0] == pytest.approx(gross / discount, rel=0, abs=1e-7)
    assert result["magi"][0] == pytest.approx(ordinary / discount, rel=0, abs=1e-7)
    assert result["federal_ordinary_tax"][0] == pytest.approx(federal / discount, rel=0, abs=1e-7)
    assert result["state_income_tax"][0] == pytest.approx(state / discount, rel=0, abs=1e-7)
    assert result["payroll_tax"][0] == pytest.approx(np.zeros(5), rel=0, abs=1e-7)
    assert result["post_tax_assets"][0] == pytest.approx(np.cumsum(gross - federal - state) / discount, rel=0, abs=1e-7)
    assert result["total_assets"][0] == pytest.approx(np.cumsum(gross - federal - state) / discount, rel=0, abs=1e-7)
