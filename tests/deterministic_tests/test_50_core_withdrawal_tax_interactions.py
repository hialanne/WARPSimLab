import numpy as np
import pytest
from tests.architectural_helpers import make_person as build_person, make_portfolio as build_portfolio, make_simulation

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.engines import withdrawalEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


@pytest.fixture(autouse=True)
def install_test_rmd_table(monkeypatch):
    monkeypatch.setattr(
        withdrawalEngine,
        "RMD_START_AGE",
        73,
        raising=False,
    )

    monkeypatch.setattr(
        withdrawalEngine,
        "UNIFORM_LIFETIME_TABLE",
        {
            73: 25.0,
            74: 24.0,
        },
        raising=False,
    )


def make_person(
    *,
    age=70,
    retire_age=65,
):
    return build_person(age=age, retire_age=retire_age)


def make_portfolio(
    *,
    pre_tax=0.0,
    post_tax=0.0,
    roth=0.0,
    hsa=0.0,
):
    return build_portfolio(equity_pre=pre_tax, equity_post=post_tax, equity_roth=roth, hsa_equity=hsa)


def make_config(
    *,
    withdrawal_amount,
    include_rmd=False,
    calculate_income_taxes=False,
    calculate_state_taxes=False,
    years_to_simulate=1,
):
    return make_simulation(
        years_to_simulate=years_to_simulate,
        results_mode="baseline",
        include_rmd=include_rmd,
        calculate_income_taxes=calculate_income_taxes,
        calculate_state_taxes=calculate_state_taxes,
        state_of_residence="CO",
        sim_initial_allocation_mode="dont-rebalance",
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_dollars=withdrawal_amount,
        always_use_expense_mode=False,
    )


def install_zero_market_path(monkeypatch):
    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        zeros = np.zeros(
            years_to_simulate + 1,
            dtype=float,
        )

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


def run_core(
    monkeypatch,
    *,
    pre_tax=0.0,
    post_tax=0.0,
    roth=0.0,
    hsa=0.0,
    withdrawal_amount=0.0,
    include_rmd=False,
    calculate_income_taxes=False,
    calculate_state_taxes=False,
    age=70,
    years_to_simulate=1,
):
    install_zero_market_path(monkeypatch)

    return simulate_yearly_portfolios(
        make_portfolio(
            pre_tax=pre_tax,
            post_tax=post_tax,
            roth=roth,
            hsa=hsa,
        ),
        make_portfolio(),
        make_person(
            age=age,
        ),
        make_person(),
        DynamicExpenses(),
        make_config(
            withdrawal_amount=withdrawal_amount,
            include_rmd=include_rmd,
            calculate_income_taxes=calculate_income_taxes,
            calculate_state_taxes=calculate_state_taxes,
            years_to_simulate=years_to_simulate,
        ),
        num_sims=1,
    )


def test_pre_tax_withdrawal_generates_federal_income_tax(
    monkeypatch,
):
    untaxed = run_core(
        monkeypatch,
        pre_tax=100_000.0,
        withdrawal_amount=60_000.0,
        calculate_income_taxes=False,
    )

    taxed = run_core(
        monkeypatch,
        pre_tax=100_000.0,
        withdrawal_amount=60_000.0,
        calculate_income_taxes=True,
    )

    assert untaxed["gross_income"][0, 1] == pytest.approx(
        60_000.0
    )
    assert taxed["gross_income"][0, 1] == pytest.approx(
        60_000.0
    )

    assert untaxed["taxes"][0, 1] == pytest.approx(
        0.0
    )
    assert taxed["taxes"][0, 1] > 0.0

    assert taxed["federal_ordinary_tax"][0, 1] > 0.0
    assert taxed["federal_qualified_dividend_tax"][0, 1] == (
        pytest.approx(0.0)
    )


def test_withdrawal_tax_reduces_net_income_not_assets(
    monkeypatch,
):
    untaxed = run_core(
        monkeypatch,
        pre_tax=100_000.0,
        withdrawal_amount=60_000.0,
        calculate_income_taxes=False,
    )

    taxed = run_core(
        monkeypatch,
        pre_tax=100_000.0,
        withdrawal_amount=60_000.0,
        calculate_income_taxes=True,
    )

    assert taxed["taxes"][0, 1] > 0.0

    assert taxed["total_assets"][0, 1] == pytest.approx(
        untaxed["total_assets"][0, 1]
    )

    assert taxed["net_income"][0, 1] == pytest.approx(
        untaxed["net_income"][0, 1]
        - taxed["taxes"][0, 1]
    )


def test_requested_withdrawal_is_not_increased_by_tax(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        pre_tax=100_000.0,
        withdrawal_amount=60_000.0,
        calculate_income_taxes=True,
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0, 1]
        == pytest.approx(60_000.0)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        60_000.0
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        40_000.0
    )

    assert results["total_assets"][0, 1] == pytest.approx(
        40_000.0
    )

    assert results["net_income"][0, 1] == pytest.approx(
        60_000.0 - results["taxes"][0, 1]
    )


def test_post_tax_withdrawal_does_not_generate_income_tax(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        post_tax=100_000.0,
        withdrawal_amount=60_000.0,
        calculate_income_taxes=True,
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        60_000.0
    )

    assert results["taxes"][0, 1] == pytest.approx(
        0.0
    )

    assert results["federal_ordinary_tax"][0, 1] == (
        pytest.approx(0.0)
    )

    assert results["post_tax_assets"][0, 1] == pytest.approx(
        40_000.0
    )


def test_roth_withdrawal_does_not_generate_income_tax(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        roth=100_000.0,
        withdrawal_amount=60_000.0,
        calculate_income_taxes=True,
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        60_000.0
    )

    assert results["roth_withdrawals"][0, 1] == pytest.approx(
        60_000.0
    )

    assert results["taxes"][0, 1] == pytest.approx(
        0.0
    )

    assert results["roth_assets"][0, 1] == pytest.approx(
        40_000.0
    )


def test_general_hsa_withdrawal_generates_income_tax(monkeypatch):
    results = run_core(monkeypatch, hsa=100_000.0, withdrawal_amount=60_000.0, calculate_income_taxes=True)

    assert results["gross_income"][0, 1] == pytest.approx(60_000.0)
    assert results["hsa_withdrawals"][0, 1] == pytest.approx(60_000.0)
    assert results["hsa_taxable_withdrawals"][0, 1] == pytest.approx(60_000.0)
    assert results["hsa_qualified_withdrawals"][0, 1] == pytest.approx(0.0)
    assert results["taxes"][0, 1] > 0.0
    assert results["federal_ordinary_tax"][0, 1] > 0.0
    assert results["hsa_assets"][0, 1] == pytest.approx(40_000.0)

def test_mixed_withdrawal_tax_matches_same_pre_tax_amount(
    monkeypatch,
):
    mixed = run_core(
        monkeypatch,
        post_tax=20_000.0,
        pre_tax=40_000.0,
        roth=100_000.0,
        withdrawal_amount=100_000.0,
        calculate_income_taxes=True,
    )

    pre_tax_only = run_core(
        monkeypatch,
        pre_tax=40_000.0,
        withdrawal_amount=40_000.0,
        calculate_income_taxes=True,
    )

    assert mixed["gross_income"][0, 1] == pytest.approx(
        100_000.0
    )

    assert mixed["roth_withdrawals"][0, 1] == pytest.approx(
        40_000.0
    )

    assert mixed["taxes"][0, 1] == pytest.approx(
        pre_tax_only["taxes"][0, 1]
    )

    assert mixed["federal_ordinary_tax"][0, 1] == (
        pytest.approx(
            pre_tax_only["federal_ordinary_tax"][0, 1]
        )
    )


def test_state_tax_reduces_net_income_but_not_remaining_assets(
    monkeypatch,
):
    federal_only = run_core(
        monkeypatch,
        pre_tax=100_000.0,
        withdrawal_amount=60_000.0,
        calculate_income_taxes=True,
        calculate_state_taxes=False,
    )

    federal_and_state = run_core(
        monkeypatch,
        pre_tax=100_000.0,
        withdrawal_amount=60_000.0,
        calculate_income_taxes=True,
        calculate_state_taxes=True,
    )

    assert federal_only["state_income_tax"][0, 1] == (
        pytest.approx(0.0)
    )

    assert federal_and_state["state_income_tax"][0, 1] > 0.0

    assert federal_and_state["taxes"][0, 1] > (
        federal_only["taxes"][0, 1]
    )

    assert federal_and_state["total_assets"][0, 1] == (
        pytest.approx(
            federal_only["total_assets"][0, 1]
        )
    )

    assert federal_and_state["net_income"][0, 1] < (
        federal_only["net_income"][0, 1]
    )


def test_rmd_generates_taxable_income(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        pre_tax=1_000_000.0,
        post_tax=50_000.0,
        withdrawal_amount=0.0,
        include_rmd=True,
        calculate_income_taxes=True,
        age=72,
    )

    expected_rmd = 1_000_000.0 / 25.0

    assert (
        results["breakdown_by_class"]["rmd"][0, 1]
        == pytest.approx(expected_rmd)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        expected_rmd
    )

    assert results["taxes"][0, 1] > 0.0

    assert results["federal_ordinary_tax"][0, 1] > 0.0

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        1_000_000.0 - expected_rmd
    )


def test_rmd_tax_reduces_net_income_not_assets(
    monkeypatch,
):
    untaxed = run_core(
        monkeypatch,
        pre_tax=1_000_000.0,
        post_tax=50_000.0,
        withdrawal_amount=0.0,
        include_rmd=True,
        calculate_income_taxes=False,
        age=72,
    )

    taxed = run_core(
        monkeypatch,
        pre_tax=1_000_000.0,
        post_tax=50_000.0,
        withdrawal_amount=0.0,
        include_rmd=True,
        calculate_income_taxes=True,
        age=72,
    )

    assert taxed["taxes"][0, 1] > 0.0

    assert taxed["total_assets"][0, 1] == pytest.approx(
        untaxed["total_assets"][0, 1]
    )

    assert taxed["net_income"][0, 1] == pytest.approx(
        untaxed["net_income"][0, 1]
        - taxed["taxes"][0, 1]
    )


def test_exhausting_pre_tax_assets_does_not_create_negative_assets(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        pre_tax=60_000.0,
        withdrawal_amount=60_000.0,
        calculate_income_taxes=True,
    )

    assert results["taxes"][0, 1] > 0.0

    assert results["total_assets"][0, 1] == pytest.approx(
        0.0
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["roth_assets"][0, 1] == pytest.approx(
        0.0
    )
    assert results["hsa_assets"][0, 1] == pytest.approx(
        0.0
    )

    assert results["net_income"][0, 1] == pytest.approx(
        60_000.0 - results["taxes"][0, 1]
    )

    assert np.isfinite(results["total_assets"][0, 1])
    assert np.isfinite(results["net_income"][0, 1])