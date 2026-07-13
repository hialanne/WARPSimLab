import numpy as np
import pytest

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.dataClasses.person import Person
from src.warpsimlab.dataClasses.portfolio import Portfolio
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios
from src.warpsimlab.sim.simulationObject import Simulation


def make_person(
    *,
    age=40,
    retire_age=100,
    income=0.0,
    pension=0.0,
    pension_age=99,
    pension_inflation_adjustment_pct=0.0,
):
    return Person(
        age=age,
        retire_age=retire_age,
        income=income,
        ss=0.0,
        ss_age=99,
        pension=pension,
        pension_age=pension_age,
        annuity=0.0,
        annuity_age=99,
        annual_401k_contribution=0.0,
        annual_employer_match=0.0,
        pension_inflation_adjustment_pct=(
            pension_inflation_adjustment_pct
        ),
    )


def make_portfolio():
    return Portfolio(
        equity_pre=0.0,
        equity_post=0.0,
        bond_pre=0.0,
        bond_post=0.0,
        cash_pre=0.0,
        cash_post=0.0,
        real_estate=0.0,
        equity_roth=0.0,
        bond_roth=0.0,
        cash_roth=0.0,
        hsa_cash=0.0,
        hsa_equity=0.0,
        hsa_bond=0.0,
    )


def make_config(
    *,
    plot_mode="raw",
    years_to_simulate=2,
    special_income_streams=None,
):
    config = Simulation(
        start_year=2026,
        years_to_simulate=years_to_simulate,
        inflation_rate=0.99,
        num_sims=1,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode=plot_mode,
        subplot_mode="monte_carlo",
        include_rmd=False,
        calculate_income_taxes=False,
        calculate_payroll_taxes=False,
        tax_filing_status="Single",
        calculate_state_taxes=False,
        state_of_residence="TX",
        second_person_enabled=False,
        eq_mean=0.0,
        bd_mean=0.0,
        cs_mean=0.0,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        sim_type="portfolio_sim",
        sim_initial_allocation_mode="dont-rebalance",
        rebalance_every_year=False,
        include_realestate=False,
        re_mean=0.0,
        re_std=0.0,
        output_csv="None",
        retirement_withdraw_mode="Off",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=0.0,
        always_use_expense_mode=True,
        sequence_risk_enabled=False,
        scenario_expense_multiplier=1.0,
        overlay_tax_impacts=False,
        overlay_fund_expense_impacts=False,
        overlay_household_expenses=False,
        overlay_profit_loss=False,
        overlay_retirement_age=False,
        show_simulated_shortfall_rate=False,
        use_snapshot_annotations=False,
        user_annotation_strings=[],
        root=None,
    )

    config.monte_carlo_mode = "rollingHistoricalWindows"
    config.disable_sequence_risk_for_historical = True
    config.use_correlated_returns = False

    config.special_income_streams = (
        list(special_income_streams)
        if special_income_streams is not None
        else []
    )

    return config


def make_expenses(
    *,
    annual_amount=0.0,
):
    expenses = DynamicExpenses()

    if annual_amount > 0.0:
        expenses.add_expense(
            start_year=2027,
            cost=annual_amount,
            end_year=None,
        )

    return expenses


def install_historical_data(
    monkeypatch,
    *,
    inflation_rates,
    window_start_indices,
):
    inflation_rates = np.asarray(
        inflation_rates,
        dtype=float,
    )
    window_start_indices = np.asarray(
        window_start_indices,
        dtype=int,
    )

    def fake_prepare_market_path_sampling(sim_config):
        data_length = len(inflation_rates)

        sim_config._hist_num_windows = len(
            window_start_indices
        )
        sim_config._hist_window_start_indices = (
            window_start_indices.copy()
        )
        sim_config._hist_inflation = inflation_rates.copy()

        sim_config._hist_years = np.arange(
            2000,
            2000 + data_length,
            dtype=int,
        )

        sim_config._hist_eq_returns = np.zeros(
            data_length,
            dtype=float,
        )
        sim_config._hist_bd_returns = np.zeros(
            data_length,
            dtype=float,
        )
        sim_config._hist_cs_returns = np.zeros(
            data_length,
            dtype=float,
        )
        sim_config._hist_re_returns = np.zeros(
            data_length,
            dtype=float,
        )

    monkeypatch.setattr(
        monteCarloEngine,
        "prepare_market_path_sampling",
        fake_prepare_market_path_sampling,
    )

    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        assert sim_index == (
            sim_config._active_historical_sim_index
        )

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
    expenses=None,
    plot_mode="raw",
    special_income_streams=None,
    inflation_rates=None,
    window_start_indices=None,
):
    if husband is None:
        husband = make_person()

    if expenses is None:
        expenses = DynamicExpenses()

    if inflation_rates is None:
        inflation_rates = [
            0.10,
            0.20,
            -0.10,
        ]

    if window_start_indices is None:
        window_start_indices = [
            0,
            1,
        ]

    install_historical_data(
        monkeypatch,
        inflation_rates=inflation_rates,
        window_start_indices=window_start_indices,
    )

    return simulate_yearly_portfolios(
        make_portfolio(),
        make_portfolio(),
        husband,
        make_person(),
        expenses,
        make_config(
            plot_mode=plot_mode,
            years_to_simulate=2,
            special_income_streams=special_income_streams,
        ),
        num_sims=99,
    )


def test_each_historical_window_uses_its_own_inflation_path(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            income=100_000.0,
        ),
        expenses=make_expenses(
            annual_amount=40_000.0,
        ),
    )

    # Window 0 inflation:
    # year 1: 10%
    # year 2: 20%
    assert (
        results["breakdown_by_class"]["work"][0]
        == pytest.approx(
            [
                0.0,
                110_000.0,
                132_000.0,
            ]
        )
    )

    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            44_000.0,
            52_800.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            0.0,
            66_000.0,
            145_200.0,
        ]
    )

    # Window 1 inflation:
    # year 1: 20%
    # year 2: -10%
    assert (
        results["breakdown_by_class"]["work"][1]
        == pytest.approx(
            [
                0.0,
                120_000.0,
                108_000.0,
            ]
        )
    )

    assert results["expense_amt"][1] == pytest.approx(
        [
            0.0,
            48_000.0,
            43_200.0,
        ]
    )

    assert results["post_tax_assets"][1] == pytest.approx(
        [
            0.0,
            72_000.0,
            136_800.0,
        ]
    )


def test_fixed_config_inflation_is_ignored_in_historical_mode(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            income=100_000.0,
        ),
        inflation_rates=[
            0.05,
            0.00,
        ],
        window_start_indices=[
            0,
        ],
    )

    # make_config deliberately sets inflation_rate to 99%.
    # Historical mode must use 5% and 0%, not that fixed rate.
    assert (
        results["breakdown_by_class"]["work"][0]
        == pytest.approx(
            [
                0.0,
                105_000.0,
                105_000.0,
            ]
        )
    )


def test_historical_inflation_applies_partial_pension_adjustment(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        husband=make_person(
            age=64,
            retire_age=65,
            pension=20_000.0,
            pension_age=65,
            pension_inflation_adjustment_pct=50.0,
        ),
        inflation_rates=[
            0.10,
            0.20,
        ],
        window_start_indices=[
            0,
        ],
    )

    # Year 1:
    # 20,000 x (1 + 10% x 50%) = 21,000
    #
    # Year 2:
    # 21,000 x (1 + 20% x 50%) = 23,100
    assert (
        results["breakdown_by_class"]["pension"][0]
        == pytest.approx(
            [
                0.0,
                21_000.0,
                23_100.0,
            ]
        )
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            0.0,
            21_000.0,
            44_100.0,
        ]
    )


def test_historical_inflation_applies_partial_special_income_adjustment(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        special_income_streams=[
            {
                "amount": 10_000.0,
                "owner": "husband",
                "start_age": 0,
                "end_age": 120,
                "taxable": True,
                "enabled": True,
                "inflation_adjustment_pct": 50.0,
            },
        ],
        inflation_rates=[
            0.10,
            0.20,
        ],
        window_start_indices=[
            0,
        ],
    )

    assert (
        results["breakdown_by_class"]["special_income"][0]
        == pytest.approx(
            [
                0.0,
                10_500.0,
                11_550.0,
            ]
        )
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            0.0,
            10_500.0,
            22_050.0,
        ]
    )


def test_real_mode_deflates_using_each_historical_window(
    monkeypatch,
):
    raw_results = run_core(
        monkeypatch,
        husband=make_person(
            income=100_000.0,
        ),
        expenses=make_expenses(
            annual_amount=40_000.0,
        ),
        plot_mode="raw",
    )

    real_results = run_core(
        monkeypatch,
        husband=make_person(
            income=100_000.0,
        ),
        expenses=make_expenses(
            annual_amount=40_000.0,
        ),
        plot_mode="real",
    )

    window_0_factors = np.array(
        [
            1.0,
            1.10,
            1.10 * 1.20,
        ]
    )

    window_1_factors = np.array(
        [
            1.0,
            1.20,
            1.20 * 0.90,
        ]
    )

    assert real_results["gross_income"][0] == pytest.approx(
        raw_results["gross_income"][0]
        / window_0_factors
    )
    assert real_results["expense_amt"][0] == pytest.approx(
        raw_results["expense_amt"][0]
        / window_0_factors
    )
    assert real_results["post_tax_assets"][0] == pytest.approx(
        raw_results["post_tax_assets"][0]
        / window_0_factors
    )

    assert real_results["gross_income"][1] == pytest.approx(
        raw_results["gross_income"][1]
        / window_1_factors
    )
    assert real_results["expense_amt"][1] == pytest.approx(
        raw_results["expense_amt"][1]
        / window_1_factors
    )
    assert real_results["post_tax_assets"][1] == pytest.approx(
        raw_results["post_tax_assets"][1]
        / window_1_factors
    )


def test_historical_window_metadata_matches_inflation_windows(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        inflation_rates=[
            0.10,
            0.20,
            -0.10,
        ],
        window_start_indices=[
            0,
            1,
        ],
    )

    assert results["historical_window_start_year"] == (
        pytest.approx(
            [
                2000,
                2001,
            ]
        )
    )

    assert results["historical_window_end_year"] == (
        pytest.approx(
            [
                2001,
                2002,
            ]
        )
    )