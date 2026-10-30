"""RMD/conversion and mixed-account funding oracles with all engines active."""

import pytest


@pytest.mark.parametrize("expense_mode", [True, False], ids=["expenses", "retirement"])
@pytest.mark.parametrize("requested,converted,remaining_pre,federal,state", [
    (25_000, 25_000, 500, 990, 1_144),
    (30_000, 25_500, 0, 1_040, 1_166),
])
def test_rmd_reserved_before_conversion_and_taxes_paid_from_cash(
    run_financial_case, expense_mode, requested, converted, remaining_pre, federal, state,
):
    # At age 73, 26,500 / 26.5 = 1,000 RMD. Conversions cannot consume it.
    # Ordinary income is RMD + actual conversion; conversion itself supplies no cash.
    result = run_financial_case(
        husband=dict(age=72, retire_age=65),
        h_assets=dict(cash_pre=26_500, cash_post=10_000), include_rmd=True,
        always_use_expense_mode=expense_mode, calculate_income_taxes=True,
        calculate_state_taxes=True, state_of_residence="CO",
        roth_flows=[dict(name="Conversion after RMD", owner="husband", enabled=True,
                         type="roth_conversion", amount=requested, start_age=73, end_age=73,
                         inflation_adjustment_pct=0)],
    )
    taxes = federal + state
    assert result["rmd_husband"][0, 1] == pytest.approx(1_000, rel=0, abs=1e-7)
    assert result["roth_conversions"][0, 1] == pytest.approx(converted, rel=0, abs=1e-7)
    assert result["pre_tax_assets"][0, 1] == pytest.approx(remaining_pre, rel=0, abs=1e-7)
    assert result["roth_assets"][0, 1] == pytest.approx(converted, rel=0, abs=1e-7)
    assert result["magi"][0, 1] == pytest.approx(1_000 + converted, rel=0, abs=1e-7)
    assert result["federal_ordinary_tax"][0, 1] == pytest.approx(federal, rel=0, abs=1e-7)
    assert result["state_income_tax"][0, 1] == pytest.approx(state, rel=0, abs=1e-7)
    assert result["post_tax_assets"][0, 1] == pytest.approx(11_000 - taxes, rel=0, abs=1e-7)
    assert result["total_assets"][0, 1] == pytest.approx(36_500 - taxes, rel=0, abs=1e-7)
    assert result["funding_gap"][0, 1] == 0


def test_next_rmd_uses_prior_year_balance_after_returns_and_fees(run_financial_case):
    result = run_financial_case(
        husband=dict(age=72, retire_age=65), h_assets=dict(equity_pre=26_500),
        include_rmd=True, years_to_simulate=2, eq_mean=.10,
        use_fund_expenses=True, fund_expense=.01,
    )
    # Year 1: (26,500 - 1,000) * 1.10 * .99 = 27,769.50.
    # Year 2 RMD: 27,769.50 / 25.5 = 1,089. Cash RMDs also incur the model's fee.
    pre_second = (27_769.5 - 1_089) * 1.10 * .99
    assert result["rmd_husband"][0] == pytest.approx([0, 1_000, 1_089], rel=0, abs=1e-7)
    assert result["pre_tax_assets"][0] == pytest.approx([26_500, 27_769.5, pre_second], rel=0, abs=1e-7)
    assert result["post_tax_assets"][0] == pytest.approx([0, 990, 2_058.21], rel=0, abs=1e-7)
    assert result["fund_expenses"][0] == pytest.approx([
        0, (28_050 + 1_000) * .01, ((27_769.5 - 1_089) * 1.10 + 2_079) * .01], rel=0, abs=1e-7)
    assert result["total_assets"][0, 2] == pytest.approx(pre_second + 2_058.21, rel=0, abs=1e-7)


def test_qualified_hsa_then_all_account_types_reconcile_tax_and_unfunded_tax(run_financial_case):
    result = run_financial_case(
        husband=dict(age=70, retire_age=65),
        h_assets=dict(cash_post=10_000, cash_pre=20_000, cash_roth=30_000,
                      hsa_cash=40_000, real_estate=50_000), include_realestate=True,
        expenses=[dict(start_year=2027, cost=10_000, is_hsa_eligible=True),
                  dict(start_year=2027, cost=90_000)],
        calculate_income_taxes=True, calculate_state_taxes=True, state_of_residence="CO",
    )
    # HSA pays 10k qualified first. Remaining 90k uses taxable 10k, deferred
    # 20k, Roth 30k, then taxable HSA 30k. Ordinary income = 50k; no payroll.
    # The documented one-pass expense model reports the extra tax as uncovered
    # when post-tax assets are empty, even with remaining real estate.
    federal = 1_240 + (50_000 - 16_100 - 12_400) * .12
    state = 50_000 * .044
    assert result["hsa_qualified_withdrawals"][0, 1] == 10_000
    assert result["hsa_taxable_withdrawals"][0, 1] == 30_000
    assert result["hsa_withdrawals"][0, 1] == 40_000
    assert result["roth_withdrawals"][0, 1] == 30_000
    assert result["emergency_pre_tax_used"][0, 1] == 20_000
    assert result["magi"][0, 1] == 50_000
    assert result["federal_ordinary_tax"][0, 1] == pytest.approx(federal, rel=0, abs=1e-7)
    assert result["state_income_tax"][0, 1] == pytest.approx(state, rel=0, abs=1e-7)
    for key in ("post_tax_assets", "pre_tax_assets", "roth_assets", "hsa_assets", "uncovered_expense", "payroll_tax"):
        assert result[key][0, 1] == 0, key
    assert result["cash_flow_shortfall"][0, 1] == 90_000
    assert result["funding_gap"][0, 1] == pytest.approx(federal + state, rel=0, abs=1e-7)
    assert result["final_tax_delta_uncovered"][0, 1] == pytest.approx(federal + state, rel=0, abs=1e-7)
    assert result["total_assets"][0, 1] == 50_000


@pytest.mark.parametrize("deceased", ["husband", "wife"])
def test_inherited_assets_use_survivor_rmd_age_and_only_survivor_conversion_schedule(
    run_financial_case, deceased,
):
    survivor = "wife" if deceased == "husband" else "husband"
    people = {deceased: dict(age=70, modeled_death_age=71),
              survivor: dict(age=72, retire_age=65)}
    assets = {"h_assets" if deceased == "husband" else "w_assets":
              dict(cash_pre=26_500, cash_post=10_000)}
    result = run_financial_case(
        **people, **assets, years_to_simulate=2, second_person_enabled=True,
        tax_filing_status="Married filing jointly", include_rmd=True,
        calculate_income_taxes=True, calculate_state_taxes=True, state_of_residence="CO",
        roth_flows=[dict(name="Owner conversion", owner=owner, enabled=True,
                         type="roth_conversion", amount=amount, start_age=0, end_age=120,
                         inflation_adjustment_pct=0)
                    for owner, amount in [(deceased, 80_000), (survivor, 10_000)]],
    )
    # All assets transfer before the survivor reaches 73: 26,500 / 26.5 = 1k.
    # RMD then conversion leave 15,500; next year uses age-74 divisor 25.5.
    second_rmd = 15_500 / 25.5
    state_first = 11_000 * .044
    state_second = (10_000 + second_rmd) * .044
    assert result[f"rmd_{deceased}"][0] == pytest.approx([0, 0, 0], rel=0, abs=1e-7)
    assert result[f"rmd_{survivor}"][0] == pytest.approx([0, 1_000, second_rmd], rel=0, abs=1e-7)
    assert result["roth_conversions"][0] == pytest.approx([0, 10_000, 10_000], rel=0, abs=1e-7)
    assert result["pre_tax_assets"][0] == pytest.approx([26_500, 15_500, 5_500 - second_rmd], rel=0, abs=1e-7)
    assert result["roth_assets"][0] == pytest.approx([0, 10_000, 20_000], rel=0, abs=1e-7)
    assert result["magi"][0] == pytest.approx([0, 11_000, 10_000 + second_rmd], rel=0, abs=1e-7)
    assert result["federal_ordinary_tax"][0] == pytest.approx([0, 0, 0], rel=0, abs=1e-7)
    assert result["state_income_tax"][0] == pytest.approx([0, state_first, state_second], rel=0, abs=1e-7)
    assert result["post_tax_assets"][0] == pytest.approx([
        10_000, 11_000 - state_first, 11_000 + second_rmd - state_first - state_second], rel=0, abs=1e-7)
    assert result["total_assets"][0] == pytest.approx([
        36_500, 36_500 - state_first, 36_500 - state_first - state_second], rel=0, abs=1e-7)
    assert result["filing_status_single"][0].tolist() == [False, False, True]
