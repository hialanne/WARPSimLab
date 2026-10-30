import numpy as np
import pytest
from tests.architectural_helpers import make_person as build_person, make_portfolio, make_simulation

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.engines import withdrawalEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


RMD_START_AGE = 73
RMD_DIVISOR_AGE_73 = 25.0


@pytest.fixture(autouse=True)
def install_test_rmd_table(monkeypatch):
    """
    Use a small deterministic RMD table.

    A $100,000 pre-tax balance at age 73 therefore produces a $4,000 RMD.
    """
    monkeypatch.setattr(
        withdrawalEngine,
        "RMD_START_AGE",
        RMD_START_AGE,
        raising=False,
    )
    monkeypatch.setattr(
        withdrawalEngine,
        "UNIFORM_LIFETIME_TABLE",
        {
            73: RMD_DIVISOR_AGE_73,
            74: 24.0,
        },
        raising=False,
    )


def make_person(
    *,
    age=72,
    retire_age=65,
):
    return build_person(age=age, retire_age=retire_age)


def make_config(
    *,
    years_to_simulate=1,
    second_person_enabled=False,
    include_rmd=True,
    retirement_withdraw_mode="Off",
    retirement_withdraw_dollars=0.0,
):
    return make_simulation(
        years_to_simulate=years_to_simulate,
        results_mode="baseline",
        include_rmd=include_rmd,
        second_person_enabled=second_person_enabled,
        sim_initial_allocation_mode="dont-rebalance",
        retirement_withdraw_mode=retirement_withdraw_mode,
        retirement_withdraw_dollars=retirement_withdraw_dollars,
        always_use_expense_mode=False,
    )


def install_zero_market_path(monkeypatch):
    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        zeros = np.zeros(years_to_simulate + 1, dtype=float)

        return {
            "eq": zeros.copy(),
            "bd": zeros.copy(),
            "cs": zeros.copy(),
            "re": zeros.copy(),
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )


def run_simulation(
    monkeypatch,
    *,
    husband_portfolio,
    husband=None,
    wife_portfolio=None,
    wife=None,
    years_to_simulate=1,
    second_person_enabled=False,
    include_rmd=True,
    retirement_withdraw_mode="Off",
    retirement_withdraw_dollars=0.0,
):
    install_zero_market_path(monkeypatch)

    if husband is None:
        husband = make_person()

    if wife is None:
        wife = make_person()

    if wife_portfolio is None:
        wife_portfolio = make_portfolio()

    config = make_config(
        years_to_simulate=years_to_simulate,
        second_person_enabled=second_person_enabled,
        include_rmd=include_rmd,
        retirement_withdraw_mode=retirement_withdraw_mode,
        retirement_withdraw_dollars=retirement_withdraw_dollars,
    )

    return simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        DynamicExpenses(),
        config,
        num_sims=1,
    )


def test_rmd_only_withdraws_from_pre_tax_assets(monkeypatch):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=100_000.0,
        ),
    )

    expected_rmd = 100_000.0 / RMD_DIVISOR_AGE_73

    assert expected_rmd == pytest.approx(4_000.0)

    assert (
        results["breakdown_by_class"]["rmd"][0, 1]
        == pytest.approx(expected_rmd)
    )
    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(0.0)
    )

    assert results["pre_tax_assets"][0, 0] == pytest.approx(
        100_000.0
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        96_000.0
    )
    assert results["total_assets"][0, 1] == pytest.approx(
        96_000.0
    )


def test_rmd_only_is_not_double_counted_in_gross_income(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=100_000.0,
        ),
    )

    expected_rmd = 4_000.0

    assert (
        results["breakdown_by_class"]["rmd"][0, 1]
        == pytest.approx(expected_rmd)
    )
    assert results["gross_income"][0, 1] == pytest.approx(expected_rmd)
    assert results["gross_income"][0, 1] == pytest.approx(
        expected_rmd
    )
    assert results["net_income"][0, 1] == pytest.approx(
        expected_rmd
    )

    assert results["gross_income"][0, 1] != pytest.approx(
        expected_rmd * 2.0
    )


def test_rmd_is_withdrawn_proportionally_from_pre_tax_assets(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=60_000.0,
            bond_pre=30_000.0,
            cash_pre=10_000.0,
        ),
    )

    expected_rmd = 4_000.0

    expected_equity = 60_000.0 - 2_400.0
    expected_bonds = 30_000.0 - 1_200.0
    expected_cash = 10_000.0 - 400.0

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        96_000.0
    )
    assert results["bonds"][0, 1] == pytest.approx(
        expected_bonds
    )
    assert results["cash"][0, 1] == pytest.approx(
        expected_cash
    )

    actual_equity = (
        results["pre_tax_assets"][0, 1]
        - results["bonds"][0, 1]
        - results["cash"][0, 1]
    )

    assert actual_equity == pytest.approx(expected_equity)
    assert expected_rmd == pytest.approx(
        2_400.0 + 1_200.0 + 400.0
    )


def test_no_rmd_before_start_age(monkeypatch):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            age=71,
            retire_age=65,
        ),
        husband_portfolio=make_portfolio(
            equity_pre=100_000.0,
        ),
    )

    assert (
        results["breakdown_by_class"]["rmd"][0, 1]
        == pytest.approx(0.0)
    )
    assert (results["breakdown_by_class"]["withdrawal"][0, 1] == pytest.approx(0.0))

    assert results["gross_income"][0, 1] == pytest.approx(0.0)
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        100_000.0
    )


def test_disabled_rmd_does_not_withdraw_pre_tax_assets(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=100_000.0,
        ),
        include_rmd=False,
    )

    assert (
        results["breakdown_by_class"]["rmd"][0, 1]
        == pytest.approx(0.0)
    )
    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(0.0)
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        100_000.0
    )
    assert results["gross_income"][0, 1] == pytest.approx(0.0)


def test_fixed_withdrawal_larger_than_rmd_uses_rmd_as_part_of_target(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=100_000.0,
            equity_post=100_000.0,
        ),
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_dollars=10_000.0,
    )

    expected_rmd = 4_000.0
    expected_additional_withdrawal = 6_000.0
    expected_total_withdrawal = 10_000.0

    assert (
        results["breakdown_by_class"]["rmd"][0, 1]
        == pytest.approx(expected_rmd)
    )
    assert results["breakdown_by_class"]["withdrawal"][0, 1] == pytest.approx(expected_additional_withdrawal)

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        96_000.0
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        94_000.0
    )

    assert expected_additional_withdrawal == pytest.approx(
        expected_total_withdrawal - expected_rmd
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        expected_total_withdrawal
    )


def test_rmd_larger_than_fixed_target_becomes_total_withdrawal(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband_portfolio=make_portfolio(
            equity_pre=100_000.0,
            equity_post=100_000.0,
        ),
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_dollars=2_000.0,
    )

    expected_rmd = 4_000.0

    assert (
        results["breakdown_by_class"]["rmd"][0, 1]
        == pytest.approx(expected_rmd)
    )
    assert results["breakdown_by_class"]["withdrawal"][0, 1] == pytest.approx(0.0)

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        96_000.0
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        100_000.0
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        expected_rmd
    )


def test_couple_rmds_are_combined_without_double_counting(
    monkeypatch,
):
    results = run_simulation(
        monkeypatch,
        husband=make_person(
            age=72,
            retire_age=65,
        ),
        wife=make_person(
            age=72,
            retire_age=65,
        ),
        husband_portfolio=make_portfolio(
            equity_pre=100_000.0,
        ),
        wife_portfolio=make_portfolio(
            equity_pre=50_000.0,
        ),
        second_person_enabled=True,
    )

    husband_rmd = 100_000.0 / 25.0
    wife_rmd = 50_000.0 / 25.0
    total_rmd = husband_rmd + wife_rmd

    assert husband_rmd == pytest.approx(4_000.0)
    assert wife_rmd == pytest.approx(2_000.0)
    assert total_rmd == pytest.approx(6_000.0)

    assert (
        results["breakdown_by_class"]["rmd"][0, 1]
        == pytest.approx(total_rmd)
    )
    assert results["breakdown_by_class"]["withdrawal"][0, 1] == pytest.approx(0.0)

    assert results["pre_tax_assets"][0, 0] == pytest.approx(
        150_000.0
    )
    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        144_000.0
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        total_rmd
    )
    assert results["net_income"][0, 1] == pytest.approx(
        total_rmd
    )