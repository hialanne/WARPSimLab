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
    retire_age=65,
    income=0.0,
):
    return Person(
        age=age,
        retire_age=retire_age,
        income=income,
        ss=0.0,
        ss_age=99,
        pension=0.0,
        pension_age=99,
        annuity=0.0,
        annuity_age=99,
        annual_401k_contribution=0.0,
        annual_employer_match=0.0,
        pension_inflation_adjustment_pct=0.0,
    )


def make_portfolio(
    *,
    equity_pre=0.0,
    bond_pre=0.0,
    cash_pre=0.0,
    equity_post=0.0,
    bond_post=0.0,
    cash_post=0.0,
    equity_roth=0.0,
    bond_roth=0.0,
    cash_roth=0.0,
    hsa_equity=0.0,
    hsa_bond=0.0,
    hsa_cash=0.0,
    real_estate=0.0,
):
    return Portfolio(
        equity_pre=equity_pre,
        equity_post=equity_post,
        bond_pre=bond_pre,
        bond_post=bond_post,
        cash_pre=cash_pre,
        cash_post=cash_post,
        real_estate=real_estate,
        equity_roth=equity_roth,
        bond_roth=bond_roth,
        cash_roth=cash_roth,
        hsa_cash=hsa_cash,
        hsa_equity=hsa_equity,
        hsa_bond=hsa_bond,
    )


def make_config(
    *,
    years_to_simulate=3,
    inflation_rate=0.0,
    plot_mode="raw",
    include_realestate=False,
    always_use_expense_mode=True,
    withdrawal_amount=0.0,
):
    config = Simulation(
        start_year=2026,
        years_to_simulate=years_to_simulate,
        inflation_rate=inflation_rate,
        num_sims=1,
        fund_expense=0.0,
        use_fund_expenses=False,
        plot_mode=plot_mode,
        subplot_mode="baseline",
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
        include_realestate=include_realestate,
        re_mean=0.0,
        re_std=0.0,
        output_csv="None",
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_pct=4.0,
        retirement_withdraw_dollars=withdrawal_amount,
        always_use_expense_mode=always_use_expense_mode,
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

    config.monte_carlo_mode = "pathBasedAnnualSampling"
    config.use_correlated_returns = False

    return config


def make_expenses(
    *,
    amount=0.0,
    start_year=2027,
):
    expenses = DynamicExpenses()

    if amount > 0.0:
        expenses.add_expense(
            start_year=start_year,
            end_year=None,
            cost=amount,
            comment="Boundary test expense",
        )

    return expenses


def install_market_path(
    monkeypatch,
    *,
    equity_return=0.0,
    bond_return=0.0,
    cash_return=0.0,
    real_estate_return=0.0,
):
    monkeypatch.setattr(
        monteCarloEngine,
        "prepare_market_path_sampling",
        lambda sim_config: None,
    )

    def fake_generate_market_path(
        sim_config,
        years_to_simulate,
        sim_index=None,
    ):
        equity = np.zeros(
            years_to_simulate + 1,
            dtype=float,
        )
        bonds = np.zeros(
            years_to_simulate + 1,
            dtype=float,
        )
        cash = np.zeros(
            years_to_simulate + 1,
            dtype=float,
        )
        real_estate = np.zeros(
            years_to_simulate + 1,
            dtype=float,
        )

        equity[1:] = equity_return
        bonds[1:] = bond_return
        cash[1:] = cash_return
        real_estate[1:] = real_estate_return

        return {
            "eq": equity,
            "bd": bonds,
            "cs": cash,
            "re": real_estate,
        }

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )


def run_core(
    monkeypatch,
    *,
    portfolio=None,
    person=None,
    expenses=None,
    years_to_simulate=3,
    inflation_rate=0.0,
    plot_mode="raw",
    include_realestate=False,
    always_use_expense_mode=True,
    withdrawal_amount=0.0,
    equity_return=0.0,
    bond_return=0.0,
    cash_return=0.0,
    real_estate_return=0.0,
):
    install_market_path(
        monkeypatch,
        equity_return=equity_return,
        bond_return=bond_return,
        cash_return=cash_return,
        real_estate_return=real_estate_return,
    )

    if portfolio is None:
        portfolio = make_portfolio()

    if person is None:
        person = make_person()

    if expenses is None:
        expenses = DynamicExpenses()

    return simulate_yearly_portfolios(
        portfolio,
        make_portfolio(),
        person,
        make_person(),
        expenses,
        make_config(
            years_to_simulate=years_to_simulate,
            inflation_rate=inflation_rate,
            plot_mode=plot_mode,
            include_realestate=include_realestate,
            always_use_expense_mode=always_use_expense_mode,
            withdrawal_amount=withdrawal_amount,
        ),
        num_sims=1,
    )


def assert_all_result_arrays_are_finite(results):
    for key, value in results.items():
        if isinstance(value, np.ndarray):
            if np.issubdtype(value.dtype, np.number):
                assert np.all(
                    np.isfinite(value)
                ), key

    for key, value in results["breakdown_by_class"].items():
        assert np.all(
            np.isfinite(value)
        ), key


def assert_asset_balances_are_nonnegative(results):
    asset_keys = [
        "total_assets",
        "pre_tax_assets",
        "post_tax_assets",
        "roth_assets",
        "hsa_assets",
        "cash",
        "bonds",
        "real_estate",
    ]

    for key in asset_keys:
        assert np.all(
            results[key] >= -1e-8
        ), key


def test_zero_assets_zero_income_remain_zero(monkeypatch):
    results = run_core(
        monkeypatch,
        years_to_simulate=4,
    )

    zero_keys = [
        "total_assets",
        "pre_tax_assets",
        "post_tax_assets",
        "roth_assets",
        "hsa_assets",
        "cash",
        "bonds",
        "real_estate",
        "gross_income",
        "net_income",
        "expense_amt",
        "uncovered_expense",
        "taxes",
        "fund_expenses",
        "roth_withdrawals",
        "hsa_withdrawals",
    ]

    for key in zero_keys:
        assert results[key] == pytest.approx(
            np.zeros((1, 5))
        )

    for values in results["breakdown_by_class"].values():
        assert values == pytest.approx(
            np.zeros((1, 5))
        )

    assert_all_result_arrays_are_finite(results)


def test_negative_one_hundred_percent_return_exhausts_assets(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        portfolio=make_portfolio(
            equity_pre=25_000.0,
            equity_post=25_000.0,
            equity_roth=25_000.0,
            hsa_equity=25_000.0,
        ),
        years_to_simulate=3,
        equity_return=-1.0,
    )

    assert results["total_assets"][0] == pytest.approx(
        [
            100_000.0,
            0.0,
            0.0,
            0.0,
        ]
    )

    assert results["pre_tax_assets"][0] == pytest.approx(
        [
            25_000.0,
            0.0,
            0.0,
            0.0,
        ]
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            25_000.0,
            0.0,
            0.0,
            0.0,
        ]
    )

    assert results["roth_assets"][0] == pytest.approx(
        [
            25_000.0,
            0.0,
            0.0,
            0.0,
        ]
    )

    assert results["hsa_assets"][0] == pytest.approx(
        [
            25_000.0,
            0.0,
            0.0,
            0.0,
        ]
    )

    assert_asset_balances_are_nonnegative(results)
    assert_all_result_arrays_are_finite(results)


def test_complete_loss_remains_stable_in_later_years(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        person=make_person(
            income=0.0,
        ),
        expenses=make_expenses(
            amount=10_000.0,
        ),
        years_to_simulate=4,
        equity_return=-1.0,
    )

    assert results["post_tax_assets"][0] == pytest.approx(
        [
            100_000.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]
    )

    assert results["uncovered_expense"][0] == pytest.approx(
        [
            0.0,
            0.0,
            10_000.0,
            10_000.0,
            10_000.0,
        ]
    )

    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            10_000.0,
            10_000.0,
            10_000.0,
            10_000.0,
        ]
    )

    assert_asset_balances_are_nonnegative(results)
    assert_all_result_arrays_are_finite(results)


def test_expense_larger_than_all_assets_reports_shortfall(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        portfolio=make_portfolio(
            equity_pre=20_000.0,
            equity_post=30_000.0,
            equity_roth=40_000.0,
            hsa_equity=10_000.0,
        ),
        expenses=make_expenses(
            amount=250_000.0,
        ),
        years_to_simulate=2,
    )

    assert results["expense_amt"][0] == pytest.approx(
        [
            0.0,
            250_000.0,
            250_000.0,
        ]
    )

    assert results["total_assets"][0] == pytest.approx(
        [
            100_000.0,
            0.0,
            0.0,
        ]
    )

    assert results["uncovered_expense"][0] == pytest.approx(
        [
            0.0,
            150_000.0,
            250_000.0,
        ]
    )

    assert_asset_balances_are_nonnegative(results)
    assert_all_result_arrays_are_finite(results)


def test_withdrawal_larger_than_all_assets_is_capped(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        portfolio=make_portfolio(
            equity_post=10_000.0,
            equity_pre=20_000.0,
            equity_roth=30_000.0,
            hsa_equity=40_000.0,
        ),
        person=make_person(
            age=70,
            retire_age=65,
        ),
        years_to_simulate=2,
        always_use_expense_mode=False,
        withdrawal_amount=250_000.0,
    )

    assert (
        results["breakdown_by_class"]["withdrawal"][0]
        == pytest.approx(
            [
                0.0,
                100_000.0,
                0.0,
            ]
        )
    )

    assert results["gross_income"][0] == pytest.approx(
        [
            0.0,
            100_000.0,
            0.0,
        ]
    )

    assert results["roth_withdrawals"][0] == pytest.approx(
        [
            0.0,
            30_000.0,
            0.0,
        ]
    )

    assert results["hsa_withdrawals"][0] == pytest.approx(
        [
            0.0,
            40_000.0,
            0.0,
        ]
    )

    assert results["total_assets"][0] == pytest.approx(
        [
            100_000.0,
            0.0,
            0.0,
        ]
    )

    assert_asset_balances_are_nonnegative(results)
    assert_all_result_arrays_are_finite(results)


def test_near_total_loss_preserves_small_positive_balance(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        portfolio=make_portfolio(
            equity_pre=100_000.0,
        ),
        years_to_simulate=2,
        equity_return=-0.999,
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        100.0
    )

    assert results["pre_tax_assets"][0, 2] == pytest.approx(
        0.1
    )

    assert results["total_assets"][0] == pytest.approx(
        [
            100_000.0,
            100.0,
            0.1,
        ]
    )

    assert_asset_balances_are_nonnegative(results)
    assert_all_result_arrays_are_finite(results)


def test_all_asset_classes_survive_extreme_valid_returns(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        portfolio=make_portfolio(
            equity_pre=25_000.0,
            bond_pre=25_000.0,
            cash_pre=25_000.0,
            real_estate=25_000.0,
        ),
        years_to_simulate=1,
        include_realestate=True,
        equity_return=-0.90,
        bond_return=-0.80,
        cash_return=-0.50,
        real_estate_return=-0.75,
    )

    assert results["pre_tax_assets"][0, 1] == pytest.approx(
        20_000.0
    )

    assert results["bonds"][0, 1] == pytest.approx(
        5_000.0
    )

    assert results["cash"][0, 1] == pytest.approx(
        12_500.0
    )

    assert results["real_estate"][0, 1] == pytest.approx(
        6_250.0
    )

    expected_total = (
        2_500.0
        + 5_000.0
        + 12_500.0
        + 6_250.0
    )

    assert results["total_assets"][0, 1] == pytest.approx(
        expected_total
    )

    assert_asset_balances_are_nonnegative(results)
    assert_all_result_arrays_are_finite(results)


def test_high_inflation_real_mode_remains_finite(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        portfolio=make_portfolio(
            equity_post=100_000.0,
        ),
        person=make_person(
            income=50_000.0,
        ),
        expenses=make_expenses(
            amount=20_000.0,
        ),
        years_to_simulate=5,
        inflation_rate=1.0,
        plot_mode="real",
        equity_return=0.10,
    )

    assert_asset_balances_are_nonnegative(results)
    assert_all_result_arrays_are_finite(results)

    assert np.all(
        results["gross_income"] >= 0.0
    )

    assert np.all(
        results["expense_amt"] >= 0.0
    )


def test_extreme_scenario_contains_no_nan_or_infinity(
    monkeypatch,
):
    results = run_core(
        monkeypatch,
        portfolio=make_portfolio(
            equity_pre=100_000.0,
            bond_pre=50_000.0,
            cash_pre=25_000.0,
            equity_post=100_000.0,
            bond_post=50_000.0,
            cash_post=25_000.0,
            equity_roth=100_000.0,
            bond_roth=50_000.0,
            cash_roth=25_000.0,
            hsa_equity=50_000.0,
            hsa_bond=25_000.0,
            hsa_cash=10_000.0,
            real_estate=250_000.0,
        ),
        person=make_person(
            income=500_000.0,
        ),
        expenses=make_expenses(
            amount=750_000.0,
        ),
        years_to_simulate=5,
        inflation_rate=0.25,
        include_realestate=True,
        equity_return=-0.75,
        bond_return=-0.50,
        cash_return=-0.25,
        real_estate_return=-0.60,
    )

    assert_asset_balances_are_nonnegative(results)
    assert_all_result_arrays_are_finite(results)

    assert np.all(
        results["uncovered_expense"] >= 0.0
    )

    assert np.all(
        results["expense_amt"] >= 0.0
    )