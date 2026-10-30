"""Real-core annual health costs, HSA funding, and modeled survivor transitions.

All financial engines and market preparation run unpatched. Returns are zero;
expected arrays below are hand-calculated, not generated reference baselines.
"""

import numpy as np
import pytest

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.dataClasses.person import Person
from src.warpsimlab.dataClasses.portfolio import Portfolio
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


@pytest.fixture
def run_health_case(scenario_builders):
    """Reuse shared configuration defaults with real people, expenses and assets."""
    def run(*, husband=None, wife=None, h_assets=None, w_assets=None,
            qualified=0.0, ordinary=0.0, **config_overrides):
        def person(overrides):
            values = dict(age=60, retire_age=60, income=0, ss=0, ss_age=70,
                          pension=0, pension_age=60, annuity=0, annuity_age=60)
            values.update(overrides or {})
            return Person(**values)

        def portfolio(overrides):
            values = dict(equity_pre=0, equity_post=0, bond_pre=0, bond_post=0,
                          cash_pre=0, cash_post=0, real_estate=0)
            values.update(overrides or {})
            return Portfolio(**values)

        config_values = dict(start_year=2026, years_to_simulate=4)
        config_values.update(config_overrides)
        config = scenario_builders.make_config(**config_values)
        expenses = DynamicExpenses()
        for amount, eligible in [(qualified, True), (ordinary, False)]:
            if amount:
                expenses.add_expense(config.start_year + 1, amount, is_hsa_eligible=eligible)
        return simulate_yearly_portfolios(
            portfolio(h_assets), portfolio(w_assets), person(husband), person(wife),
            expenses, config, num_sims=config.num_sims,
        )

    return run


def test_medicare_age_activation_and_inflation_reduce_assets_once(run_health_case):
    result = run_health_case(
        husband=dict(age=63, medicare_annual_cost=3_000),
        wife=dict(age=64, medicare_annual_cost=4_000),
        second_person_enabled=True, tax_filing_status="Married filing jointly",
        years_to_simulate=3, inflation_rate=0.10, h_assets=dict(cash_post=100_000),
    )
    h_cost = np.array([0, 0, 3_630, 3_993])
    w_cost = np.array([0, 4_400, 4_840, 5_324])
    assert result["medicare_cost_husband"][0] == pytest.approx(h_cost)
    assert result["medicare_cost_wife"][0] == pytest.approx(w_cost)
    assert result["medicare_cost"][0] == pytest.approx(h_cost + w_cost)
    assert result["total_assets"][0] == pytest.approx(100_000 - np.cumsum(h_cost + w_cost))
    assert result["expense_amt"][0] == pytest.approx(np.zeros(4))
    assert result["funding_gap"][0] == pytest.approx(np.zeros(4))


@pytest.mark.parametrize("expense_mode", [True, False])
@pytest.mark.parametrize("assets,gap", [(10_000, 0), (1_000, 3_147.92)])
def test_medicare_and_irmaa_are_funded_in_both_cash_flow_modes(
    run_health_case, expense_mode, assets, gap,
):
    # Level 1: 12 * (202.90 * 0.4 + 14.50) = 1,147.92 surcharge.
    result = run_health_case(
        husband=dict(age=65, medicare_annual_cost=3_000),
        h_assets=dict(cash_post=assets), years_to_simulate=1,
        always_use_expense_mode=expense_mode, irmaa_enabled=True,
        historical_magi=dict(two_years_prior=110_000, one_year_prior=0),
    )
    assert result["medicare_cost"][0, 1] == 3_000
    assert result["irmaa"][0, 1] == pytest.approx(1_147.92)
    assert result["irmaa_level"][0, 1] == 1
    assert result["total_assets"][0, 1] == pytest.approx(max(0, assets - 4_147.92))
    assert result["funding_gap"][0, 1] == pytest.approx(gap)


@pytest.mark.parametrize("enabled", [True, False])
def test_roth_conversion_changes_irmaa_only_two_years_later(run_health_case, enabled):
    result = run_health_case(
        husband=dict(age=65), years_to_simulate=4, irmaa_enabled=enabled,
        calculate_income_taxes=True,
        h_assets=dict(cash_pre=200_000, cash_post=100_000),
        historical_magi=dict(two_years_prior=None, one_year_prior=None),
        roth_flows=[dict(enabled=True, type="roth_conversion", owner="husband",
                         amount=120_000, start_age=66, end_age=66,
                         inflation_adjustment_pct=0)],
    )
    assert result["roth_conversions"][0] == pytest.approx([0, 120_000, 0, 0, 0])
    assert result["magi"][0] == pytest.approx([0, 120_000, 0, 0, 0])
    assert result["federal_ordinary_tax"][0, 1] > 0
    assert result["irmaa_lookback_available"][0].tolist() == [False, False, False, True, True]
    assert np.isnan(result["irmaa_lookback_magi"][0, 1:3]).all()
    assert result["irmaa_lookback_magi"][0, 3:] == pytest.approx([120_000, 0])
    assert result["irmaa"][0] == pytest.approx([0, 0, 0, 1_147.92 if enabled else 0, 0])


def test_survivor_irmaa_uses_historical_filing_status_until_two_year_lag_expires(run_health_case):
    result = run_health_case(
        husband=dict(age=70, modeled_death_age=71),
        wife=dict(age=70, pension=150_000),
        h_assets=dict(cash_post=50_000), second_person_enabled=True,
        tax_filing_status="Married filing jointly", irmaa_enabled=True,
        historical_magi=dict(two_years_prior=150_000, one_year_prior=150_000),
    )
    assert result["filing_status_single"][0].tolist() == [False, False, True, True, True]
    assert result["irmaa_level"][0].tolist() == [-1, 0, 0, 0, 2]
    assert result["irmaa_husband"][0] == pytest.approx(np.zeros(5))
    assert result["irmaa_wife"][0] == pytest.approx([0, 0, 0, 0, 2_884.80])


@pytest.mark.parametrize("deceased", ["husband", "wife"])
def test_death_stops_owner_income_and_health_costs_and_preserves_survivor_cashflow(
    run_health_case, deceased,
):
    people = {
        "husband": dict(age=70, pension=12_000, annuity=3_000, ss=24_000,
                        medicare_annual_cost=3_000),
        "wife": dict(age=70, pension=8_000, annuity=2_000, ss=18_000,
                     medicare_annual_cost=2_000),
    }
    people[deceased]["modeled_death_age"] = 72
    result = run_health_case(
        **people, ordinary=20_000, second_person_enabled=True,
        tax_filing_status="Married filing jointly", years_to_simulate=3,
        h_assets=dict(cash_post=50_000), w_assets=dict(cash_post=50_000),
    )
    survivor = "wife" if deceased == "husband" else "husband"
    pension = 8_000 if survivor == "wife" else 12_000
    annuity = 2_000 if survivor == "wife" else 3_000
    premium = 2_000 if survivor == "wife" else 3_000
    survivor_income = pension + annuity + 24_000
    assert result[f"{deceased}_alive"][0].tolist() == [True, True, False, False]
    assert result[f"{deceased}_death_event"][0].tolist() == [False, False, True, False]
    assert result["survivor_expense_factor"][0] == pytest.approx([1, 1, 0.75, 0.75])
    assert result["expense_amt"][0] == pytest.approx([0, 20_000, 15_000, 15_000])
    assert result["breakdown_by_class"]["ss"][0] == pytest.approx([0, 42_000, 24_000, 24_000])
    assert result["breakdown_by_class"]["pension"][0] == pytest.approx([0, 20_000, pension, pension])
    assert result["breakdown_by_class"]["annuity"][0] == pytest.approx([0, 5_000, annuity, annuity])
    assert result[f"net_income_{deceased}"][0, 2:] == pytest.approx([0, 0])
    assert result[f"net_income_{survivor}"][0, 2:] == pytest.approx([survivor_income] * 2)
    assert result["medicare_cost"][0] == pytest.approx([0, 5_000, premium, premium])
    gains = np.array([0, 67_000 - 20_000 - 5_000,
                      survivor_income - 15_000 - premium, survivor_income - 15_000 - premium])
    assert result["total_assets"][0] == pytest.approx(100_000 + np.cumsum(gains))


@pytest.mark.parametrize("deceased", ["husband", "wife"])
def test_inherited_buckets_remain_available_for_survivor_qualified_spending(run_health_case, deceased):
    people = {"husband": dict(age=70), "wife": dict(age=70)}
    people[deceased]["modeled_death_age"] = 71
    # Only the deceased owns assets. The survivor must be able to spend them.
    assets = dict(cash_pre=10_000, cash_post=20_000, cash_roth=30_000,
                  hsa_cash=4_000, real_estate=50_000)
    result = run_health_case(
        **people, **{"h_assets" if deceased == "husband" else "w_assets": assets},
        second_person_enabled=True, include_realestate=True,
        qualified=4_000, years_to_simulate=2,
    )
    assert result["hsa_qualified_withdrawals"][0] == pytest.approx([0, 3_000, 1_000])
    assert result["hsa_assets"][0] == pytest.approx([4_000, 1_000, 0])
    assert result["post_tax_assets"][0] == pytest.approx([20_000, 20_000, 18_000])
    assert result["pre_tax_assets"][0] == pytest.approx([10_000] * 3)
    assert result["roth_assets"][0] == pytest.approx([30_000] * 3)
    assert result["real_estate"][0] == pytest.approx([50_000] * 3)
    assert result["total_assets"][0] == pytest.approx([114_000, 111_000, 108_000])
    assert result["funding_gap"][0] == pytest.approx([0, 0, 0])


@pytest.mark.parametrize("second_person", [False, True])
def test_final_death_stores_terminal_assets_without_another_year_of_flows(run_health_case, second_person):
    result = run_health_case(
        husband=dict(age=60, retire_age=100, income=10_000, modeled_death_age=62),
        wife=dict(age=60, retire_age=100, income=20_000, modeled_death_age=62),
        second_person_enabled=second_person, h_assets=dict(cash_post=1_000),
        ordinary=4_000, years_to_simulate=4,
    )
    income = 30_000 if second_person else 10_000
    terminal_assets = 1_000 + income - 4_000
    assert result["terminal_year"].tolist() == [2028]
    assert result["effective_end_index"].tolist() == [2]
    assert result["total_assets"][0, :3] == pytest.approx([1_000, terminal_assets, terminal_assets])
    assert result["gross_income"][0] == pytest.approx([0, income, 0, 0, 0])
    assert result["expense_amt"][0] == pytest.approx([0, 4_000, 0, 0, 0])
    assert result["husband_death_event"][0].tolist() == [False, False, True, False, False]
    assert not result["husband_alive"][0, 2:].any()


def test_hsa_contributions_reduce_income_and_payroll_tax_but_employer_adds_assets(run_health_case):
    result = run_health_case(
        husband=dict(age=40, retire_age=65, income=50_000,
                     annual_401k_contribution=5_000, annual_hsa_contribution=3_000,
                     annual_hsa_employer_contribution=1_000),
        years_to_simulate=1, calculate_income_taxes=True, calculate_payroll_taxes=True,
    )
    # 2027 nominal model uses the 2026 tables without inflation: 42,000 ordinary
    # income - 16,100 deduction; 12,400 at 10%, remaining 13,500 at 12%.
    income_tax = 1_240 + 13_500 * 0.12
    payroll = 47_000 * (0.062 + 0.0145)
    assert result["hsa_employee_contributions"][0, 1] == 3_000
    assert result["hsa_employer_contributions"][0, 1] == 1_000
    assert result["hsa_assets"][0, 1] == pytest.approx(4_000)
    assert result["pre_tax_assets"][0, 1] == 5_000
    assert result["gross_income"][0, 1] == 50_000
    assert result["magi"][0, 1] == 42_000
    assert result["federal_ordinary_tax"][0, 1] == pytest.approx(income_tax)
    assert result["payroll_tax"][0, 1] == pytest.approx(payroll)
    assert result["post_tax_assets"][0, 1] == pytest.approx(42_000 - income_tax - payroll)
    assert result["total_assets"][0, 1] == pytest.approx(51_000 - income_tax - payroll)


def test_hsa_wage_cap_is_per_spouse_and_stops_at_retirement(run_health_case):
    result = run_health_case(
        husband=dict(age=62, retire_age=65, income=10_000, annual_401k_contribution=8_000,
                     annual_hsa_contribution=5_000, annual_hsa_employer_contribution=1_000),
        wife=dict(age=60, retire_age=63, income=20_000, annual_hsa_contribution=3_000,
                  annual_hsa_employer_contribution=500),
        second_person_enabled=True, years_to_simulate=3,
    )
    assert result["hsa_employee_contributions"][0] == pytest.approx([0, 5_000, 5_000, 0])
    assert result["hsa_employer_contributions"][0] == pytest.approx([0, 1_500, 1_500, 0])
    assert result["hsa_total_contributions"][0] == pytest.approx([0, 6_500, 6_500, 0])
    assert result["hsa_assets"][0] == pytest.approx([0, 6_500, 13_000, 13_000])
    assert result["pre_tax_assets"][0] == pytest.approx([0, 8_000, 16_000, 16_000])
    assert result["total_assets"][0] == pytest.approx([0, 31_500, 63_000, 63_000])


@pytest.mark.parametrize("hsa,post,qualified_paid,remaining_post,gap", [
    (50_000, 100_000, 40_000, 100_000, 0),
    (20_000, 100_000, 20_000, 80_000, 0),
    (20_000, 0, 20_000, 0, 20_000),
])
def test_qualified_expense_is_tax_free_and_shortfall_is_funded_only_once(
    run_health_case, hsa, post, qualified_paid, remaining_post, gap,
):
    result = run_health_case(
        h_assets=dict(hsa_cash=hsa, cash_post=post), qualified=40_000,
        years_to_simulate=1, calculate_income_taxes=True,
    )
    assert result["expense_amt"][0, 1] == 40_000
    assert result["hsa_qualified_withdrawals"][0, 1] == qualified_paid
    assert result["hsa_taxable_withdrawals"][0, 1] == 0
    assert result["hsa_withdrawals"][0, 1] == qualified_paid
    assert result["hsa_assets"][0, 1] == pytest.approx(hsa - qualified_paid, abs=1e-8)
    assert result["post_tax_assets"][0, 1] == remaining_post
    assert result["total_assets"][0, 1] == pytest.approx(hsa + post - 40_000 + gap)
    assert result["magi"][0, 1] == 0
    assert result["taxes"][0, 1] == 0
    assert result["funding_gap"][0, 1] == gap


def test_current_year_hsa_contributions_can_fund_qualified_spending(run_health_case):
    result = run_health_case(
        husband=dict(age=40, retire_age=65, income=10_000,
                     annual_hsa_contribution=3_000, annual_hsa_employer_contribution=1_000),
        qualified=4_000, years_to_simulate=1,
    )
    assert result["hsa_total_contributions"][0, 1] == 4_000
    assert result["hsa_qualified_withdrawals"][0, 1] == pytest.approx(4_000)
    assert result["hsa_assets"][0, 1] == pytest.approx(0, abs=1e-9)
    assert result["post_tax_assets"][0, 1] == 7_000
    assert result["total_assets"][0, 1] == pytest.approx(10_000 + 1_000 - 4_000)
    assert result["magi"][0, 1] == 7_000


@pytest.mark.parametrize("deceased", ["husband", "wife"])
def test_survivor_tax_uses_joint_deduction_in_death_year_then_single(run_health_case, deceased):
    survivor = "wife" if deceased == "husband" else "husband"
    people = {deceased: dict(age=70, modeled_death_age=72),
              survivor: dict(age=70, pension=50_000)}
    result = run_health_case(
        **people, second_person_enabled=True, tax_filing_status="Married filing jointly",
        calculate_income_taxes=True, years_to_simulate=3,
    )
    assert result["filing_status_single"][0].tolist() == [False, False, False, True]
    # Joint: (50,000 - 32,200) * 10%; single: 12,400 * 10% + 21,500 * 12%.
    tax = np.array([0, 1_780, 1_780, 3_820])
    assert result["federal_ordinary_tax"][0] == pytest.approx(tax)
    assert result["taxes"][0] == pytest.approx(tax)
    assert result["total_assets"][0] == pytest.approx(np.cumsum([0, 48_220, 48_220, 46_180]))
    assert result[f"net_income_{deceased}"][0, 2:] == pytest.approx([0, 0])


@pytest.mark.parametrize("deceased", ["husband", "wife"])
def test_death_stops_wages_and_hsa_contributions_only_for_deceased_owner(run_health_case, deceased):
    survivor = "wife" if deceased == "husband" else "husband"
    people = {
        deceased: dict(age=40, retire_age=65, income=50_000, modeled_death_age=42,
                       annual_hsa_contribution=3_000, annual_hsa_employer_contribution=1_000),
        survivor: dict(age=40, retire_age=65, income=30_000,
                       annual_hsa_contribution=2_000, annual_hsa_employer_contribution=500),
    }
    result = run_health_case(**people, second_person_enabled=True, years_to_simulate=3)
    assert result["gross_income"][0] == pytest.approx([0, 80_000, 30_000, 30_000])
    assert result["hsa_employee_contributions"][0] == pytest.approx([0, 5_000, 2_000, 2_000])
    assert result["hsa_employer_contributions"][0] == pytest.approx([0, 1_500, 500, 500])
    assert result["hsa_assets"][0] == pytest.approx([0, 6_500, 9_000, 11_500])
    assert result["total_assets"][0] == pytest.approx([0, 81_500, 112_000, 142_500])
    assert result[f"net_income_{deceased}"][0, 2:] == pytest.approx([0, 0])


@pytest.mark.parametrize("deceased", ["husband", "wife"])
def test_transferred_pre_tax_assets_generate_survivor_rmd_without_double_withdrawal(
    run_health_case, deceased,
):
    survivor = "wife" if deceased == "husband" else "husband"
    people = {deceased: dict(age=75, modeled_death_age=76), survivor: dict(age=72)}
    result = run_health_case(
        **people, **{"h_assets" if deceased == "husband" else "w_assets": dict(cash_pre=26_500)},
        second_person_enabled=True, include_rmd=True, years_to_simulate=2,
    )
    # Survivor reaches 73 in year 1: 26,500 / 26.5, then 25,500 / 25.5.
    assert result[f"rmd_{deceased}"][0] == pytest.approx([0, 0, 0])
    assert result[f"rmd_{survivor}"][0] == pytest.approx([0, 1_000, 1_000])
    assert result["pre_tax_assets"][0] == pytest.approx([26_500, 25_500, 24_500])
    assert result["post_tax_assets"][0] == pytest.approx([0, 1_000, 2_000])
    assert result["total_assets"][0] == pytest.approx([26_500] * 3)


def test_deceased_worker_does_not_delay_survivors_retirement_withdrawals(run_health_case):
    result = run_health_case(
        husband=dict(age=60, retire_age=100, income=10_000, modeled_death_age=62),
        wife=dict(age=70), second_person_enabled=True, years_to_simulate=3,
        h_assets=dict(cash_post=100_000), ordinary=4_000,
        always_use_expense_mode=False, retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_dollars=5_000,
    )
    assert result["expense_amt"][0] == pytest.approx([0, 4_000, 0, 0])
    assert result["gross_income"][0] == pytest.approx([0, 10_000, 5_000, 5_000])
    assert result["total_assets"][0] == pytest.approx([100_000, 106_000, 101_000, 96_000])


def test_sequential_deaths_end_survivor_flows_at_second_death(run_health_case):
    result = run_health_case(
        husband=dict(age=70, pension=12_000, modeled_death_age=71),
        wife=dict(age=70, pension=8_000, modeled_death_age=73),
        second_person_enabled=True, years_to_simulate=4, ordinary=4_000,
        h_assets=dict(cash_post=10_000),
    )
    assert result["terminal_year"].tolist() == [2029]
    assert result["effective_end_index"].tolist() == [3]
    assert result["gross_income"][0] == pytest.approx([0, 8_000, 8_000, 0, 0])
    assert result["expense_amt"][0] == pytest.approx([0, 3_000, 3_000, 0, 0])
    assert result["total_assets"][0, :4] == pytest.approx([10_000, 15_000, 20_000, 20_000])
    assert result["wife_death_event"][0].tolist() == [False, False, False, True, False]


def test_health_costs_hsa_and_mortality_reset_between_real_core_paths(run_health_case):
    result = run_health_case(
        husband=dict(age=63, retire_age=70, income=50_000, modeled_death_age=65,
                     annual_hsa_contribution=3_000, annual_hsa_employer_contribution=500),
        wife=dict(age=64, pension=15_000, medicare_annual_cost=3_000),
        second_person_enabled=True, qualified=4_000, years_to_simulate=4, num_sims=3,
        irmaa_enabled=True, historical_magi=dict(two_years_prior=300_000, one_year_prior=150_000),
        h_assets=dict(hsa_cash=10_000, cash_post=50_000),
    )
    for key in ["total_assets", "hsa_assets", "hsa_total_contributions",
                "hsa_qualified_withdrawals", "medicare_cost", "magi", "irmaa",
                "irmaa_level", "husband_alive", "husband_death_event", "filing_status_single"]:
        np.testing.assert_array_equal(result[key][1], result[key][0], err_msg=key)
        np.testing.assert_array_equal(result[key][2], result[key][0], err_msg=key)


@pytest.mark.parametrize("inflation_mode", ["nominal", "real"])
def test_historical_windows_use_own_inflation_for_health_costs_and_hsa_flows(
    run_health_case, monkeypatch, inflation_mode,
):
    # Supply tiny input datasets, retaining real preparation, path generation,
    # all financial engines, and real-dollar conversion.
    years = np.array([2010, 2011, 2012])
    monkeypatch.setattr(monteCarloEngine, "load_historical_asset_returns_csv", lambda filename: {
        "years": years, "eq": np.zeros(3), "bd": np.zeros(3),
        "cs": np.zeros(3), "re": np.zeros(3),
    })
    monkeypatch.setattr(monteCarloEngine, "load_historical_inflation_csv", lambda filename: {
        "years": years, "inflation": np.array([0.10, 0.20, 0.0]),
    })
    result = run_health_case(
        husband=dict(age=40, retire_age=65, income=10_000,
                     annual_hsa_contribution=1_000, annual_hsa_employer_contribution=500),
        wife=dict(age=65, medicare_annual_cost=2_000), second_person_enabled=True,
        h_assets=dict(cash_post=20_000, hsa_cash=1_000), qualified=500,
        years_to_simulate=2, results_mode="risk_analysis", risk_analysis_mode="historical_windows",
        historical_asset_returns_file="returns.csv", historical_inflation_file="inflation.csv",
        inflation_rate=0.99, inflation_mode=inflation_mode,
    )
    factors = np.array([[1, 1.10, 1.32], [1, 1.20, 1.20]])
    discount = factors if inflation_mode == "real" else np.ones((2, 3))
    flow_factors = factors.copy()
    flow_factors[:, 0] = 0
    for key, base in [("medicare_cost", 2_000), ("hsa_employee_contributions", 1_000),
                      ("hsa_employer_contributions", 500), ("hsa_qualified_withdrawals", 500)]:
        np.testing.assert_allclose(result[key], base * flow_factors / discount, rtol=0, atol=1e-8)
    np.testing.assert_allclose(result["hsa_assets"],
                               np.array([[1_000, 2_100, 3_420], [1_000, 2_200, 3_400]]) / discount,
                               rtol=0, atol=1e-8)
    np.testing.assert_allclose(result["total_assets"],
                               np.array([[21_000, 29_800, 40_360], [21_000, 30_600, 40_200]]) / discount,
                               rtol=0, atol=1e-8)
    assert result["historical_window_start_year"].tolist() == [2010, 2011]
