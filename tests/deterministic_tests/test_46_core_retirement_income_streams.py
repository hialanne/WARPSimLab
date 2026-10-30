import numpy as np
import pytest
from tests.architectural_helpers import make_person as build_person, make_portfolio, make_simulation

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


def make_person(
    *,
    age=60,
    retire_age=65,
    income=0.0,
    ss=0.0,
    ss_age=99,
    pension=0.0,
    pension_age=99,
    annuity=0.0,
    annuity_age=99,
    pension_inflation_adjustment_pct=0.0,
):
    return build_person(
        age=age,
        retire_age=retire_age,
        income=income,
        ss=ss,
        ss_age=ss_age,
        pension=pension,
        pension_age=pension_age,
        annuity=annuity,
        annuity_age=annuity_age,
        pension_inflation_adjustment_pct=pension_inflation_adjustment_pct,
    )


def make_config(
    *,
    years_to_simulate=5,
    inflation_rate=0.0,
    second_person_enabled=False,
    calculate_income_taxes=False,
):
    return make_simulation(
        years_to_simulate=years_to_simulate,
        inflation_rate=inflation_rate,
        results_mode="baseline",
        calculate_income_taxes=calculate_income_taxes,
        second_person_enabled=second_person_enabled,
        sim_initial_allocation_mode="dont-rebalance",
        retirement_withdraw_dollars=0.0,
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
    husband=None,
    wife=None,
    years_to_simulate=5,
    inflation_rate=0.0,
    second_person_enabled=False,
    calculate_income_taxes=False,
):
    install_zero_market_path(monkeypatch)

    if husband is None:
        husband = make_person()

    if wife is None:
        wife = make_person(
            age=0,
            retire_age=100,
        )

    return simulate_yearly_portfolios(
        make_portfolio(),
        make_portfolio(),
        husband,
        wife,
        DynamicExpenses(),
        make_config(
            years_to_simulate=years_to_simulate,
            inflation_rate=inflation_rate,
            second_person_enabled=second_person_enabled,
            calculate_income_taxes=calculate_income_taxes,
        ),
        num_sims=1,
    )


def test_social_security_starts_at_configured_age(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=63,
            ss=24_000.0,
            ss_age=65,
        ),
        years_to_simulate=4,
    )

    # Simulation years use ages 64, 65, 66, and 67.
    expected = [
        0.0,
        0.0,
        24_000.0,
        24_000.0,
        24_000.0,
    ]

    assert (
        results["breakdown_by_class"]["ss"][0]
        == pytest.approx(expected)
    )

    assert results["gross_income"][0] == pytest.approx(
        expected
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            0.0,
            0.0,
            24_000.0,
            48_000.0,
            72_000.0,
        ]
    )


def test_pension_starts_at_configured_age(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=61,
            pension=18_000.0,
            pension_age=63,
        ),
        years_to_simulate=4,
    )

    expected = [
        0.0,
        0.0,
        18_000.0,
        18_000.0,
        18_000.0,
    ]

    assert (
        results["breakdown_by_class"]["pension"][0]
        == pytest.approx(expected)
    )

    assert results["gross_income"][0] == pytest.approx(
        expected
    )


def test_annuity_starts_at_configured_age(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=64,
            annuity=12_000.0,
            annuity_age=66,
        ),
        years_to_simulate=4,
    )

    expected = [
        0.0,
        0.0,
        12_000.0,
        12_000.0,
        12_000.0,
    ]

    assert (
        results["breakdown_by_class"]["annuity"][0]
        == pytest.approx(expected)
    )

    assert results["gross_income"][0] == pytest.approx(
        expected
    )


def test_all_retirement_income_streams_are_combined(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=64,
            ss=24_000.0,
            ss_age=65,
            pension=18_000.0,
            pension_age=65,
            annuity=12_000.0,
            annuity_age=65,
        ),
        years_to_simulate=2,
    )

    expected_total = 54_000.0

    assert (
        results["breakdown_by_class"]["ss"][0, 1]
        == pytest.approx(24_000.0)
    )
    assert (
        results["breakdown_by_class"]["pension"][0, 1]
        == pytest.approx(18_000.0)
    )
    assert (
        results["breakdown_by_class"]["annuity"][0, 1]
        == pytest.approx(12_000.0)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        expected_total
    )
    assert results["net_income"][0, 1] == pytest.approx(
        expected_total
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            0.0,
            54_000.0,
            108_000.0,
        ]
    )


def test_pension_uses_partial_inflation_adjustment(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=64,
            pension=20_000.0,
            pension_age=65,
            pension_inflation_adjustment_pct=50.0,
        ),
        years_to_simulate=3,
        inflation_rate=0.10,
    )

    # Ten percent inflation with a 50 percent adjustment
    # produces pension growth of 5 percent per year.
    assert (
        results["breakdown_by_class"]["pension"][0]
        == pytest.approx(
            [
                0.0,
                21_000.0,
                22_050.0,
                23_152.50,
            ]
        )
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            0.0,
            21_000.0,
            43_050.0,
            66_202.50,
        ]
    )


def test_zero_pension_adjustment_keeps_pension_level(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=64,
            pension=20_000.0,
            pension_age=65,
            pension_inflation_adjustment_pct=0.0,
        ),
        years_to_simulate=3,
        inflation_rate=0.10,
    )

    assert (
        results["breakdown_by_class"]["pension"][0]
        == pytest.approx(
            [
                0.0,
                20_000.0,
                20_000.0,
                20_000.0,
            ]
        )
    )


def test_retirement_income_is_attributed_to_correct_spouse(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=64,
            ss=20_000.0,
            ss_age=65,
            pension=10_000.0,
            pension_age=65,
        ),
        wife=make_person(
            age=64,
            ss=15_000.0,
            ss_age=65,
            annuity=5_000.0,
            annuity_age=65,
        ),
        years_to_simulate=1,
        second_person_enabled=True,
    )

    assert results["net_income_husband"][0, 1] == (
        pytest.approx(30_000.0)
    )

    assert results["net_income_wife"][0, 1] == (
        pytest.approx(20_000.0)
    )

    assert results["net_income"][0, 1] == pytest.approx(
        50_000.0
    )

    assert (
        results["net_income_husband"][0, 1]
        + results["net_income_wife"][0, 1]
        == pytest.approx(results["net_income"][0, 1])
    )


def test_wife_retirement_income_is_ignored_when_disabled(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=64,
        ),
        wife=make_person(
            age=64,
            ss=20_000.0,
            ss_age=65,
            pension=10_000.0,
            pension_age=65,
            annuity=5_000.0,
            annuity_age=65,
        ),
        years_to_simulate=1,
        second_person_enabled=False,
    )

    assert (
        results["breakdown_by_class"]["ss"][0, 1]
        == pytest.approx(0.0)
    )
    assert (
        results["breakdown_by_class"]["pension"][0, 1]
        == pytest.approx(0.0)
    )
    assert (
        results["breakdown_by_class"]["annuity"][0, 1]
        == pytest.approx(0.0)
    )

    assert results["gross_income"][0, 1] == pytest.approx(
        0.0
    )
    assert results["net_income_wife"][0, 1] == pytest.approx(
        0.0
    )


def test_retirement_income_is_subject_to_income_tax(
    monkeypatch,
):
    untaxed_results = run_core(
        monkeypatch,
        husband=make_person(
            age=64,
            pension=100_000.0,
            pension_age=65,
        ),
        years_to_simulate=1,
        calculate_income_taxes=False,
    )

    taxed_results = run_core(
        monkeypatch,
        husband=make_person(
            age=64,
            pension=100_000.0,
            pension_age=65,
        ),
        years_to_simulate=1,
        calculate_income_taxes=True,
    )

    assert untaxed_results["gross_income"][0, 1] == (
        pytest.approx(100_000.0)
    )
    assert taxed_results["gross_income"][0, 1] == (
        pytest.approx(100_000.0)
    )

    assert untaxed_results["taxes"][0, 1] == pytest.approx(
        0.0
    )
    assert taxed_results["taxes"][0, 1] > 0.0

    assert taxed_results["net_income"][0, 1] < (
        untaxed_results["net_income"][0, 1]
    )

    assert taxed_results["post_tax_assets"][0, 1] == (
        pytest.approx(
            taxed_results["net_income"][0, 1]
        )
    )


def test_social_security_and_pension_continue_after_retirement(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=64,
            retire_age=65,
            ss=20_000.0,
            ss_age=65,
            pension=10_000.0,
            pension_age=65,
        ),
        years_to_simulate=3,
    )

    assert (
        results["breakdown_by_class"]["ss"][0]
        == pytest.approx(
            [
                0.0,
                20_000.0,
                20_000.0,
                20_000.0,
            ]
        )
    )

    assert (
        results["breakdown_by_class"]["pension"][0]
        == pytest.approx(
            [
                0.0,
                10_000.0,
                10_000.0,
                10_000.0,
            ]
        )
    )

    assert results["gross_income"][0] == pytest.approx(
        [
            0.0,
            30_000.0,
            30_000.0,
            30_000.0,
        ]
    )