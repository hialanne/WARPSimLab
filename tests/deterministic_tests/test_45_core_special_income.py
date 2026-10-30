import numpy as np
import pytest
from tests.architectural_helpers import make_person, make_portfolio, make_simulation

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios


def make_config(
    *,
    years_to_simulate=3,
    inflation_rate=0.0,
    second_person_enabled=False,
    calculate_income_taxes=False,
    special_income_streams=None,
):
    config = make_simulation(
        years_to_simulate=years_to_simulate,
        inflation_rate=inflation_rate,
        results_mode="baseline",
        calculate_income_taxes=calculate_income_taxes,
        second_person_enabled=second_person_enabled,
        sim_initial_allocation_mode="dont-rebalance",
        retirement_withdraw_dollars=0.0,
    )

    config.special_income_streams = (
        list(special_income_streams)
        if special_income_streams is not None
        else []
    )

    return config


def make_stream(
    *,
    amount,
    owner="husband",
    start_age=0,
    end_age=120,
    taxable=True,
    enabled=True,
    inflation_adjustment_pct=100.0,
):
    return {
        "amount": amount,
        "owner": owner,
        "start_age": start_age,
        "end_age": end_age,
        "taxable": taxable,
        "enabled": enabled,
        "inflation_adjustment_pct": inflation_adjustment_pct,
    }


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
    years_to_simulate=3,
    inflation_rate=0.0,
    second_person_enabled=False,
    calculate_income_taxes=False,
    special_income_streams=None,
):
    install_zero_market_path(monkeypatch)

    if husband is None:
        husband = make_person()

    if wife is None:
        wife = make_person()

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
            special_income_streams=special_income_streams,
        ),
        num_sims=1,
    )


def test_special_income_enters_income_and_post_tax_assets(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        years_to_simulate=2,
        special_income_streams=[
            make_stream(
                amount=10_000.0,
                owner="husband",
                taxable=True,
            ),
        ],
    )

    expected = [
        0.0,
        10_000.0,
        10_000.0,
    ]

    assert (
        results["breakdown_by_class"]["special_income"][0]
        == pytest.approx(expected)
    )

    assert results["gross_income"][0] == pytest.approx(
        expected
    )
    assert results["net_income"][0] == pytest.approx(
        expected
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            0.0,
            10_000.0,
            20_000.0,
        ]
    )


def test_special_income_obeys_inclusive_age_range(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=58,
        ),
        years_to_simulate=4,
        special_income_streams=[
            make_stream(
                amount=12_000.0,
                owner="husband",
                start_age=60,
                end_age=61,
            ),
        ],
    )

    # Simulation years use ages 59, 60, 61, and 62.
    assert (
        results["breakdown_by_class"]["special_income"][0]
        == pytest.approx(
            [
                0.0,
                0.0,
                12_000.0,
                12_000.0,
                0.0,
            ]
        )
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            0.0,
            0.0,
            12_000.0,
            24_000.0,
            24_000.0,
        ]
    )


def test_special_income_uses_partial_inflation_adjustment(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        years_to_simulate=3,
        inflation_rate=0.10,
        special_income_streams=[
            make_stream(
                amount=10_000.0,
                inflation_adjustment_pct=50.0,
            ),
        ],
    )

    # A 10% inflation rate with a 50% adjustment produces
    # annual income growth of 5%.
    assert (
        results["breakdown_by_class"]["special_income"][0]
        == pytest.approx(
            [
                0.0,
                10_500.0,
                11_025.0,
                11_576.25,
            ]
        )
    )

    assert results["gross_income"][0] == pytest.approx(
        [
            0.0,
            10_500.0,
            11_025.0,
            11_576.25,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            0.0,
            10_500.0,
            21_525.0,
            33_101.25,
        ]
    )


def test_special_income_is_attributed_to_correct_spouse(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=60,
        ),
        wife=make_person(
            age=60,
        ),
        years_to_simulate=1,
        second_person_enabled=True,
        special_income_streams=[
            make_stream(
                amount=15_000.0,
                owner="husband",
            ),
            make_stream(
                amount=25_000.0,
                owner="wife",
            ),
        ],
    )

    assert (
        results["breakdown_by_class"]["special_income"][0, 1]
        == pytest.approx(40_000.0)
    )

    assert results["net_income_husband"][0, 1] == (
        pytest.approx(15_000.0)
    )
    assert results["net_income_wife"][0, 1] == (
        pytest.approx(25_000.0)
    )

    assert results["net_income"][0, 1] == pytest.approx(
        40_000.0
    )

    assert (
        results["net_income_husband"][0, 1]
        + results["net_income_wife"][0, 1]
        == pytest.approx(results["net_income"][0, 1])
    )


def test_wife_special_income_is_ignored_for_single_person(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=60,
        ),
        wife=make_person(
            age=60,
        ),
        years_to_simulate=1,
        second_person_enabled=False,
        special_income_streams=[
            make_stream(
                amount=25_000.0,
                owner="wife",
            ),
        ],
    )

    assert (
        results["breakdown_by_class"]["special_income"][0, 1]
        == pytest.approx(0.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        0.0
    )
    assert results["net_income_wife"][0, 1] == pytest.approx(
        0.0
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )


def test_disabled_and_nonpositive_streams_are_ignored(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        years_to_simulate=1,
        special_income_streams=[
            make_stream(
                amount=10_000.0,
                enabled=False,
            ),
            make_stream(
                amount=0.0,
            ),
            make_stream(
                amount=-5_000.0,
            ),
        ],
    )

    assert (
        results["breakdown_by_class"]["special_income"][0, 1]
        == pytest.approx(0.0)
    )
    assert results["gross_income"][0, 1] == pytest.approx(
        0.0
    )
    assert results["post_tax_assets"][0, 1] == pytest.approx(
        0.0
    )


def test_non_taxable_special_income_is_not_subject_to_income_tax(
    monkeypatch,
):
    taxable_results = run_core(
        monkeypatch,
        years_to_simulate=1,
        calculate_income_taxes=True,
        special_income_streams=[
            make_stream(
                amount=100_000.0,
                taxable=True,
            ),
        ],
    )

    non_taxable_results = run_core(
        monkeypatch,
        years_to_simulate=1,
        calculate_income_taxes=True,
        special_income_streams=[
            make_stream(
                amount=100_000.0,
                taxable=False,
            ),
        ],
    )

    assert taxable_results["gross_income"][0, 1] == (
        pytest.approx(100_000.0)
    )
    assert non_taxable_results["gross_income"][0, 1] == (
        pytest.approx(100_000.0)
    )

    assert taxable_results["taxes"][0, 1] > 0.0

    assert non_taxable_results["taxes"][0, 1] == (
        pytest.approx(0.0)
    )

    assert non_taxable_results["net_income"][0, 1] == (
        pytest.approx(100_000.0)
    )

    assert taxable_results["net_income"][0, 1] < (
        non_taxable_results["net_income"][0, 1]
    )

    assert taxable_results["post_tax_assets"][0, 1] == (
        pytest.approx(
            taxable_results["net_income"][0, 1]
        )
    )

    assert non_taxable_results["post_tax_assets"][0, 1] == (
        pytest.approx(100_000.0)
    )