import copy

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
    income=50_000.0,
    annual_401k_contribution=5_000.0,
    annual_employer_match=2_500.0,
):
    return Person(
        age=age,
        retire_age=retire_age,
        income=income,
        ss=20_000.0,
        ss_age=67,
        pension=10_000.0,
        pension_age=65,
        annuity=5_000.0,
        annuity_age=70,
        annual_401k_contribution=annual_401k_contribution,
        annual_employer_match=annual_employer_match,
        pension_inflation_adjustment_pct=50.0,
    )


def make_portfolio(
    *,
    equity_pre=50_000.0,
    bond_pre=20_000.0,
    cash_pre=10_000.0,
    equity_post=40_000.0,
    bond_post=15_000.0,
    cash_post=5_000.0,
    equity_roth=30_000.0,
    bond_roth=10_000.0,
    cash_roth=5_000.0,
    hsa_equity=20_000.0,
    hsa_bond=8_000.0,
    hsa_cash=2_000.0,
    real_estate=100_000.0,
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


def make_expenses():
    expenses = DynamicExpenses()

    expenses.add_expense(
        start_year=2027,
        end_year=None,
        cost=30_000.0,
        comment="Living expenses",
    )

    expenses.add_expense(
        start_year=2028,
        end_year=2028,
        cost=15_000.0,
        comment="One-time expense",
    )

    return expenses


def make_config(
    *,
    years_to_simulate=3,
    num_sims=1,
):
    config = Simulation(
        start_year=2026,
        years_to_simulate=years_to_simulate,
        inflation_rate=0.02,
        num_sims=num_sims,
        fund_expense=0.005,
        use_fund_expenses=True,
        plot_mode="raw",
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
        post_tax_equity_dividend_yield=0.02,
        post_tax_bond_interest_yield=0.03,
        post_tax_cash_interest_yield=0.01,
        sim_type="portfolio_sim",
        sim_initial_allocation_mode="dont-rebalance",
        rebalance_every_year=False,
        include_realestate=True,
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

    config.monte_carlo_mode = "pathBasedAnnualSampling"
    config.use_correlated_returns = False

    return config


def make_path(
    *,
    years_to_simulate,
    equity_return=0.05,
    bond_return=0.02,
    cash_return=0.01,
    real_estate_return=0.03,
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


def install_identical_market_paths(
    monkeypatch,
    *,
    equity_return=0.05,
    bond_return=0.02,
    cash_return=0.01,
    real_estate_return=0.03,
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
        return make_path(
            years_to_simulate=years_to_simulate,
            equity_return=equity_return,
            bond_return=bond_return,
            cash_return=cash_return,
            real_estate_return=real_estate_return,
        )

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )


def install_different_market_paths(monkeypatch):
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
        equity_returns = {
            0: 0.10,
            1: 0.00,
            2: -0.10,
        }

        return make_path(
            years_to_simulate=years_to_simulate,
            equity_return=equity_returns[sim_index],
            bond_return=0.0,
            cash_return=0.0,
            real_estate_return=0.0,
        )

    monkeypatch.setattr(
        monteCarloEngine,
        "generate_market_path",
        fake_generate_market_path,
    )


def run_core(
    *,
    husband_portfolio,
    wife_portfolio,
    husband,
    wife,
    expenses,
    config,
    num_sims,
):
    return simulate_yearly_portfolios(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        config,
        num_sims=num_sims,
    )


def public_attributes(obj):
    return {
        key: copy.deepcopy(value)
        for key, value in vars(obj).items()
        if not key.startswith("_")
    }


def assert_objects_equal(actual, expected):
    actual_values = public_attributes(actual)
    expected_values = public_attributes(expected)

    assert actual_values.keys() == expected_values.keys()

    for key in actual_values:
        actual_value = actual_values[key]
        expected_value = expected_values[key]

        if isinstance(actual_value, np.ndarray):
            assert np.array_equal(
                actual_value,
                expected_value,
            )
        else:
            assert actual_value == expected_value


def test_input_portfolios_are_not_mutated(monkeypatch):
    install_identical_market_paths(monkeypatch)

    husband_portfolio = make_portfolio()
    wife_portfolio = make_portfolio(
        equity_pre=10_000.0,
        bond_pre=5_000.0,
        cash_pre=2_000.0,
        equity_post=8_000.0,
        bond_post=4_000.0,
        cash_post=1_000.0,
        equity_roth=6_000.0,
        bond_roth=3_000.0,
        cash_roth=1_000.0,
        hsa_equity=4_000.0,
        hsa_bond=2_000.0,
        hsa_cash=500.0,
        real_estate=25_000.0,
    )

    husband_before = copy.deepcopy(husband_portfolio)
    wife_before = copy.deepcopy(wife_portfolio)

    run_core(
        husband_portfolio=husband_portfolio,
        wife_portfolio=wife_portfolio,
        husband=make_person(),
        wife=make_person(),
        expenses=make_expenses(),
        config=make_config(),
        num_sims=1,
    )

    assert_objects_equal(
        husband_portfolio,
        husband_before,
    )
    assert_objects_equal(
        wife_portfolio,
        wife_before,
    )


def test_input_people_are_not_mutated(monkeypatch):
    install_identical_market_paths(monkeypatch)

    husband = make_person(
        age=62,
        retire_age=65,
        income=80_000.0,
        annual_401k_contribution=8_000.0,
        annual_employer_match=4_000.0,
    )

    wife = make_person(
        age=60,
        retire_age=67,
        income=40_000.0,
        annual_401k_contribution=4_000.0,
        annual_employer_match=2_000.0,
    )

    husband_before = copy.deepcopy(husband)
    wife_before = copy.deepcopy(wife)

    config = make_config()
    config.second_person_enabled = True

    run_core(
        husband_portfolio=make_portfolio(),
        wife_portfolio=make_portfolio(),
        husband=husband,
        wife=wife,
        expenses=make_expenses(),
        config=config,
        num_sims=1,
    )

    assert_objects_equal(
        husband,
        husband_before,
    )
    assert_objects_equal(
        wife,
        wife_before,
    )


def test_dynamic_expenses_are_not_mutated(monkeypatch):
    install_identical_market_paths(monkeypatch)

    expenses = make_expenses()
    expenses_before = copy.deepcopy(expenses)

    run_core(
        husband_portfolio=make_portfolio(),
        wife_portfolio=make_portfolio(),
        husband=make_person(),
        wife=make_person(),
        expenses=expenses,
        config=make_config(),
        num_sims=1,
    )

    assert_objects_equal(
        expenses,
        expenses_before,
    )


def test_user_config_values_are_not_mutated_by_standard_run(
    monkeypatch,
):
    install_identical_market_paths(monkeypatch)

    config = make_config()
    config_before = copy.deepcopy(config)

    original_keys = set(vars(config_before))

    run_core(
        husband_portfolio=make_portfolio(),
        wife_portfolio=make_portfolio(),
        husband=make_person(),
        wife=make_person(),
        expenses=make_expenses(),
        config=config,
        num_sims=1,
    )

    for key in original_keys:
        actual_value = getattr(config, key)
        expected_value = getattr(config_before, key)

        if isinstance(actual_value, np.ndarray):
            assert np.array_equal(
                actual_value,
                expected_value,
            )
        else:
            assert actual_value == expected_value


def test_identical_simulations_do_not_leak_state_between_rows(
    monkeypatch,
):
    install_identical_market_paths(monkeypatch)

    results = run_core(
        husband_portfolio=make_portfolio(),
        wife_portfolio=make_portfolio(),
        husband=make_person(),
        wife=make_person(),
        expenses=make_expenses(),
        config=make_config(
            num_sims=3,
        ),
        num_sims=3,
    )

    array_keys = [
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
        "ira_401k",
        "fund_expenses",
        "qualified_dividends",
        "bond_interest",
        "cash_interest",
    ]

    for key in array_keys:
        assert results[key][1] == pytest.approx(
            results[key][0]
        )
        assert results[key][2] == pytest.approx(
            results[key][0]
        )

    for values in results["breakdown_by_class"].values():
        assert values[1] == pytest.approx(values[0])
        assert values[2] == pytest.approx(values[0])


def test_different_simulation_rows_do_not_contaminate_each_other(
    monkeypatch,
):
    install_different_market_paths(monkeypatch)

    config = make_config(
        years_to_simulate=2,
        num_sims=3,
    )
    config.use_fund_expenses = False
    config.fund_expense = 0.0

    results = run_core(
        husband_portfolio=make_portfolio(
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
        ),
        wife_portfolio=make_portfolio(
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
        ),
        husband=make_person(
            income=0.0,
            annual_401k_contribution=0.0,
            annual_employer_match=0.0,
        ),
        wife=make_person(
            income=0.0,
            annual_401k_contribution=0.0,
            annual_employer_match=0.0,
        ),
        expenses=DynamicExpenses(),
        config=config,
        num_sims=3,
    )

    assert results["total_assets"][0] == pytest.approx(
        [
            50_000.0,
            55_000.0,
            60_500.0,
        ]
    )

    assert results["total_assets"][1] == pytest.approx(
        [
            50_000.0,
            50_000.0,
            50_000.0,
        ]
    )

    assert results["total_assets"][2] == pytest.approx(
        [
            50_000.0,
            45_000.0,
            40_500.0,
        ]
    )


def test_repeated_runs_with_same_inputs_are_identical(
    monkeypatch,
):
    install_identical_market_paths(monkeypatch)

    husband_portfolio = make_portfolio()
    wife_portfolio = make_portfolio()
    husband = make_person()
    wife = make_person()
    expenses = make_expenses()

    first_results = run_core(
        husband_portfolio=husband_portfolio,
        wife_portfolio=wife_portfolio,
        husband=husband,
        wife=wife,
        expenses=expenses,
        config=make_config(),
        num_sims=1,
    )

    second_results = run_core(
        husband_portfolio=husband_portfolio,
        wife_portfolio=wife_portfolio,
        husband=husband,
        wife=wife,
        expenses=expenses,
        config=make_config(),
        num_sims=1,
    )

    array_keys = [
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
        "net_profit",
        "expense_amt",
        "uncovered_expense",
        "ira_401k",
        "taxes",
        "fund_expenses",
        "qualified_dividends",
        "bond_interest",
        "cash_interest",
    ]

    for key in array_keys:
        assert second_results[key] == pytest.approx(
            first_results[key]
        )

    for key in first_results["breakdown_by_class"]:
        assert (
            second_results["breakdown_by_class"][key]
            == pytest.approx(
                first_results["breakdown_by_class"][key]
            )
        )


def test_result_rows_do_not_share_memory(monkeypatch):
    install_identical_market_paths(monkeypatch)

    results = run_core(
        husband_portfolio=make_portfolio(),
        wife_portfolio=make_portfolio(),
        husband=make_person(),
        wife=make_person(),
        expenses=make_expenses(),
        config=make_config(
            num_sims=3,
        ),
        num_sims=3,
    )

    keys = [
        "total_assets",
        "pre_tax_assets",
        "post_tax_assets",
        "gross_income",
        "net_income",
        "expense_amt",
    ]

    for key in keys:
        assert not np.shares_memory(
            results[key][0],
            results[key][1],
        )
        assert not np.shares_memory(
            results[key][1],
            results[key][2],
        )

    for values in results["breakdown_by_class"].values():
        assert not np.shares_memory(
            values[0],
            values[1],
        )
        assert not np.shares_memory(
            values[1],
            values[2],
        )


def test_mutating_returned_results_does_not_mutate_inputs(
    monkeypatch,
):
    install_identical_market_paths(monkeypatch)

    husband_portfolio = make_portfolio()
    husband = make_person()
    expenses = make_expenses()

    portfolio_before = copy.deepcopy(husband_portfolio)
    person_before = copy.deepcopy(husband)
    expenses_before = copy.deepcopy(expenses)

    results = run_core(
        husband_portfolio=husband_portfolio,
        wife_portfolio=make_portfolio(),
        husband=husband,
        wife=make_person(),
        expenses=expenses,
        config=make_config(),
        num_sims=1,
    )

    results["total_assets"][0, :] = -999.0
    results["gross_income"][0, :] = -999.0

    for values in results["breakdown_by_class"].values():
        values[0, :] = -999.0

    assert_objects_equal(
        husband_portfolio,
        portfolio_before,
    )
    assert_objects_equal(
        husband,
        person_before,
    )
    assert_objects_equal(
        expenses,
        expenses_before,
    )