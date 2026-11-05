"""Independent QCD limits, ownership, funding and spendable-cash contracts."""

import pytest

from src.warpsimlab.dataClasses.portfolioState import PortfolioState
from src.warpsimlab.sim.engines.withdrawalEngine import calculate_qcd, calculate_retirement_withdrawal
from src.warpsimlab.sim.simulationObject import PathContext, RunContext
from tests.architectural_helpers import make_simulation


@pytest.mark.parametrize("owner", ["husband", "wife"])
@pytest.mark.parametrize("amount,rmd,expected", [(0, 10_000, 0), (5_000, 10_000, 5_000),
    (10_000, 10_000, 10_000), (15_000, 10_000, 15_000), (15_000, 0, 15_000),
    (200_000, 10_000, 111_000)])
def test_fixed_qcd_offsets_rmd_and_preserves_unmodified_portfolio(owner, amount, rmd, expected):
    config = make_simulation()
    config.qcd_settings[owner].update(enabled=True, amount=amount)
    portfolio = PortfolioState(100_000, 100_000, 100_000, 0, 0, 0, 0)
    before = vars(portfolio).copy()
    result = calculate_qcd(portfolio, owner, 75, True, rmd, 1, config)
    assert result == {"qcd": expected, "rmd_offset": min(expected, rmd),
                      "taxable_rmd": max(0, rmd - expected)}
    assert vars(portfolio) == before
    other = "wife"
    if owner == "wife":
        other = "husband"

    assert calculate_qcd(portfolio, other, 75, True, rmd, 1, config)["qcd"] == 0


@pytest.mark.parametrize("percent,rmd,expected", [(0, 10_000, 0), (50, 10_000, 5_000),
    (100, 10_000, 10_000), (75, 10_000, 7_500), (100, 0, 0), (100, 200_000, 111_000)])
def test_percentage_qcd_is_based_on_required_rmd(percent, rmd, expected):
    config = make_simulation()
    config.qcd_settings["husband"].update(enabled=True, mode="Percent of RMD", percent=percent)
    portfolio = PortfolioState(300_000, 0, 0, 0, 0, 0, 0)
    result = calculate_qcd(portfolio, "husband", 75, True, rmd, 1, config)
    assert result["qcd"] == expected
    assert result["taxable_rmd"] == max(0, rmd - expected)


@pytest.mark.parametrize("age,start,end,alive,enabled,expected", [
    (70, 70.5, None, True, True, 0), (71, 70.5, None, True, True, 1_000),
    (74, 75, 77, True, True, 0), (75, 75, 77, True, True, 1_000),
    (77, 75, 77, True, True, 1_000), (78, 75, 77, True, True, 0),
    (75, 70.5, None, False, True, 0), (75, 70.5, None, True, False, 0)])
def test_qcd_age_window_death_and_disabled_settings(age, start, end, alive, enabled, expected):
    config = make_simulation()
    config.qcd_settings["husband"].update(enabled=enabled, amount=1_000, start_age=start, end_age=end)
    portfolio = PortfolioState(100_000, 0, 0, 0, 0, 0, 0)
    result = calculate_qcd(portfolio, "husband", age, alive, 5_000, 1, config)
    assert result == {"qcd": expected, "rmd_offset": expected, "taxable_rmd": 5_000 - expected}


@pytest.mark.parametrize("pre_tax", [0, 500, 1_000, 2_000])
def test_qcd_cannot_use_taxable_roth_hsa_or_real_estate_assets(pre_tax):
    config = make_simulation()
    config.qcd_settings["husband"].update(enabled=True, amount=1_000)
    portfolio = PortfolioState(pre_tax / 2, pre_tax / 4, pre_tax / 4, 50_000, 0, 0, 50_000,
                               eq_roth=50_000, hsa_eq=50_000)
    result = calculate_qcd(portfolio, "husband", 75, True, 0, 1, config)
    assert result["qcd"] == min(pre_tax, 1_000)


@pytest.mark.parametrize("start_year,year", [(2026, 1), (2026, 3), (2028, 2)])
def test_fixed_amount_and_annual_limit_follow_inflation(start_year, year):
    config = make_simulation(start_year=start_year, inflation_rate=.02, inflation_delta=.01)
    config.qcd_settings["husband"].update(enabled=True, amount=10_000)
    portfolio = PortfolioState(1_000_000, 0, 0, 0, 0, 0, 0)
    result = calculate_qcd(portfolio, "husband", 75, True, 0, year, config)
    assert result["qcd"] == pytest.approx(10_000 * 1.03 ** year)
    config.qcd_settings["husband"]["amount"] = 1_000_000
    result = calculate_qcd(portfolio, "husband", 75, True, 0, year, config)
    assert result["qcd"] == pytest.approx(111_000 * 1.03 ** (start_year - 2026 + year))


def test_qcd_uses_path_specific_historical_inflation():
    import numpy as np

    config = make_simulation(results_mode="risk_analysis", risk_analysis_mode="historical_windows")
    config.qcd_settings["husband"].update(enabled=True, amount=10_000)
    run = RunContext(hist_inflation=np.array([.02, -.01, .10]), hist_window_start_indices=np.array([0, 1]))
    portfolio = PortfolioState(1_000_000, 0, 0, 0, 0, 0, 0)
    first = calculate_qcd(portfolio, "husband", 75, True, 0, 2, config,
                          run_context=run, path_context=PathContext(active_historical_sim_index=0))
    second = calculate_qcd(portfolio, "husband", 75, True, 0, 2, config,
                           run_context=run, path_context=PathContext(active_historical_sim_index=1))
    assert first["qcd"] == pytest.approx(10_000 * 1.02 * .99)
    assert second["qcd"] == pytest.approx(10_000 * .99 * 1.10)


@pytest.mark.parametrize("qcd,rmd,target,spendable", [(0, 10_000, 20_000, 20_000),
    (5_000, 10_000, 20_000, 15_000), (10_000, 10_000, 20_000, 10_000),
    (15_000, 10_000, 20_000, 5_000), (25_000, 10_000, 20_000, 0),
    (5_000, 0, 20_000, 15_000)])
def test_withdrawal_target_includes_charity_but_household_cash_does_not(qcd, rmd, target, spendable):
    config = make_simulation(retirement_withdraw_mode="Fixed Dollar Amount", retirement_withdraw_dollars=target)
    portfolio = PortfolioState(100_000, 0, 0, 100_000, 0, 0, 0)
    empty = PortfolioState(0, 0, 0, 0, 0, 0, 0)
    result = calculate_retirement_withdrawal(portfolio, empty, None, None, 1, config, rmd_h=rmd, qcd_h=qcd)
    assert result["total"] == spendable
    assert result["qcd"] == qcd
    assert result["rmd"] == max(0, rmd - qcd)
    assert result["by_person"]["husband"] == spendable
    assert portfolio.total_value == 200_000 - spendable - qcd
    assert portfolio.total_value_pre == 100_000 - max(rmd, qcd)
    assert result["uncovered"] == 0


def test_spouses_have_independent_annual_limits_and_mandatory_distributions():
    config = make_simulation(second_person_enabled=True, retirement_withdraw_mode="Off")
    husband = PortfolioState(200_000, 0, 0, 0, 0, 0, 0)
    wife = PortfolioState(200_000, 0, 0, 0, 0, 0, 0)
    for owner in ("husband", "wife"):
        config.qcd_settings[owner].update(enabled=True, amount=200_000)

    h_qcd = calculate_qcd(husband, "husband", 75, True, 10_000, 1, config)
    w_qcd = calculate_qcd(wife, "wife", 75, True, 20_000, 1, config)
    result = calculate_retirement_withdrawal(husband, wife, None, None, 1, config,
                                            rmd_h=10_000, rmd_w=20_000, qcd_h=h_qcd["qcd"], qcd_w=w_qcd["qcd"])
    assert result["qcd"] == 222_000
    assert result["total"] == 0
    assert result["rmd_by_person"] == {"husband": 0, "wife": 0}
    assert husband.total_value_pre == 89_000
    assert wife.total_value_pre == 89_000
