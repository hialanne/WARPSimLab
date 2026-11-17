"""Household allocation and account-preserving Scenario Explorer conversion."""

import copy

import pytest

from src.warpsimlab.gui.scenario import gui_scenarioState as mod
from src.warpsimlab.sim.engines import portfolioEngine
from tests.architectural_helpers import make_portfolio, make_simulation


# Explicit test-side mappings keep missing or misclassified production fields detectable.
BUCKETS = (
    ("equity_pre", "bond_pre", "cash_pre"),
    ("equity_post", "bond_post", "cash_post"),
    ("equity_roth", "bond_roth", "cash_roth"),
    ("hsa_equity", "hsa_bond", "hsa_cash"),
)
STATE_BUCKETS = (("eq_pre", "bd_pre", "cs_pre"), ("eq_post", "bd_post", "cs_post"),
                 ("eq_roth", "bd_roth", "cs_roth"), ("hsa_eq", "hsa_bd", "hsa_cs"))


def mixed_household():
    return {
        "husband": make_portfolio(equity_pre=300, bond_pre=100, cash_pre=100,
            equity_post=0, bond_post=200, cash_post=100, equity_roth=100, bond_roth=0,
            cash_roth=100, hsa_equity=0, hsa_bond=0, hsa_cash=100, real_estate=1234),
        "wife": make_portfolio(equity_pre=100, bond_pre=0, cash_pre=100,
            equity_post=100, bond_post=100, cash_post=0, equity_roth=0, bond_roth=100,
            cash_roth=100, hsa_equity=100, hsa_bond=0, hsa_cash=100, real_estate=5678),
    }


def asset_values(portfolios):
    totals = [0.0, 0.0, 0.0]
    for portfolio in portfolios.values():
        for fields in BUCKETS:
            for index, field in enumerate(fields):
                totals[index] += getattr(portfolio, field)
    return totals


@pytest.mark.parametrize("owner", ["husband", "wife"])
@pytest.mark.parametrize("fields", BUCKETS, ids=["deferred", "taxable", "roth", "hsa"])
def test_household_allocation_includes_each_person_and_account(owner, fields):
    portfolios = {"husband": make_portfolio(), "wife": make_portfolio()}
    for field, amount in zip(fields, (123, 234, 643)):
        setattr(portfolios[owner], field, amount)
    portfolios[owner].real_estate = 999999
    assert mod.compute_portfolio_asset_values(portfolios) == [123, 234, 643]
    assert mod.compute_portfolio_percentages(portfolios) == (12, 23, 65)


@pytest.mark.parametrize("amounts,expected", [((334, 333, 333), (33, 33, 34)),
    ((336, 338, 326), (34, 34, 32)), ((125, 225, 650), (12, 22, 66))])
def test_display_rounds_stock_and_bonds_then_calculates_cash(amounts, expected):
    portfolio = make_portfolio(equity_pre=amounts[0], bond_pre=amounts[1], cash_pre=amounts[2])
    assert mod.compute_portfolio_percentages({"husband": portfolio}) == expected


@pytest.mark.parametrize("portfolios", [{}, {"husband": make_portfolio(), "wife": make_portfolio()}])
def test_empty_household_allocation_and_conversion_are_safe(portfolios):
    original = copy.deepcopy(portfolios)
    assert mod.compute_portfolio_percentages(portfolios) == (0, 0, 100)
    mod.apply_scenario_allocation(portfolios, 75, 25)
    assert asset_values(portfolios) == [0, 0, 0]
    for owner in portfolios:
        assert vars(portfolios[owner]) == vars(original[owner])


@pytest.mark.parametrize("stock_delta,bond_delta,extreme", [(10, 0, None), (-10, 0, None),
    (0, 10, None), (0, -10, None), (20, 10, None), (-10, 20, None),
    (0, 0, (100, 0)), (0, 0, (0, 100)), (0, 0, (0, 0))],
    ids=["stock_from_cash", "stock_to_cash", "bond_from_cash", "bond_to_cash", "buy_both",
         "stock_to_bonds", "all_stock", "all_bonds", "all_cash"])
@pytest.mark.parametrize("empty_accounts", [False, True])
def test_proportional_conversion_preserves_all_account_balances(stock_delta, bond_delta, extreme, empty_accounts):
    portfolios = mixed_household()
    portfolios["husband"].note = {"owner": "husband", "values": [1, 2]}
    portfolios["wife"].note = {"owner": "wife", "values": [3, 4]}
    if empty_accounts:
        for fields in (BUCKETS[1], BUCKETS[3]):
            for field in fields:
                setattr(portfolios["wife"], field, 0.0)

    before = copy.deepcopy(portfolios)
    initial = asset_values(before)
    total = sum(initial)
    stocks = initial[0] * 100 / total + stock_delta
    bonds = initial[1] * 100 / total + bond_delta
    if extreme is not None:
        stocks, bonds = extreme

    targets = (total * stocks / 100, total * bonds / 100, total * (100 - stocks - bonds) / 100)
    mod.apply_scenario_allocation(portfolios, stocks, bonds)
    assert asset_values(portfolios) == pytest.approx(targets, abs=1e-9)
    assert sum(asset_values(portfolios)) == pytest.approx(total, abs=1e-9)
    for owner, portfolio in portfolios.items():
        unchanged = copy.deepcopy(vars(before[owner]))
        actual = copy.deepcopy(vars(portfolio))
        for fields in BUCKETS:
            old_values, new_values = [], []
            for field in fields:
                old_values.append(getattr(before[owner], field))
                new_values.append(getattr(portfolio, field))
                del unchanged[field]
                del actual[field]
            assert min(new_values) >= 0
            assert sum(new_values) == pytest.approx(sum(old_values), abs=1e-9)
            # Selling is proportional to existing holdings of that asset; this
            # also proves accounts with no sold holdings supply no proceeds.
            for index in range(3):
                if targets[index] < initial[index]:
                    assert new_values[index] == pytest.approx(old_values[index] * targets[index] / initial[index])
        assert actual == unchanged


@pytest.mark.parametrize("rebalance", [False, True])
def test_adjusted_portfolio_initialization_and_annual_ratios(rebalance):
    portfolios = mixed_household()
    mod.apply_scenario_allocation(portfolios, 60, 25)
    before = copy.deepcopy(portfolios)
    config = make_simulation(sim_initial_allocation_mode="original-allocation", rebalance_every_year=rebalance)
    for owner, portfolio in portfolios.items():
        fresh = portfolioEngine.create_sim_portfolio(portfolio, config)
        for source_fields, state_fields in zip(BUCKETS, STATE_BUCKETS):
            state = portfolioEngine.create_sim_portfolio(portfolio, config)
            original, drifted = [], []
            for source, target, growth in zip(source_fields, state_fields, (1.20, 0.95, 1.03)):
                amount = getattr(portfolio, source)
                assert getattr(state, target) == amount
                original.append(amount)
                drifted.append(amount * growth)
                setattr(state, target, amount * growth)

            if rebalance:
                portfolioEngine.rebalance(state, config)
                total = sum(drifted)
                for field, amount in zip(state_fields, original):
                    assert getattr(state, field) == pytest.approx(total * amount / sum(original))
            else:
                for field, amount in zip(state_fields, drifted):
                    assert getattr(state, field) == amount

            for source, target in zip(source_fields, state_fields):
                assert getattr(fresh, target) == getattr(portfolio, source)
        assert vars(portfolio) == vars(before[owner])


@pytest.mark.parametrize("wife_stock", [0, 100])
def test_conversion_only_reinvests_proceeds_in_the_account_that_sells(wife_stock):
    portfolios = {"husband": make_portfolio(cash_pre=100), "wife": make_portfolio(equity_roth=wife_stock)}
    mod.apply_scenario_allocation(portfolios, 60, 30)
    if wife_stock:
        assert portfolios["husband"].equity_pre == pytest.approx(20)
        assert portfolios["husband"].bond_pre == pytest.approx(60)
        assert portfolios["husband"].cash_pre == pytest.approx(20)
        assert vars(portfolios["wife"]) == vars(make_portfolio(equity_roth=100))
    else:
        assert portfolios["husband"].equity_pre == pytest.approx(60)
        assert portfolios["husband"].bond_pre == pytest.approx(30)
        assert portfolios["husband"].cash_pre == pytest.approx(10)
        assert vars(portfolios["wife"]) == vars(make_portfolio())
    assert vars(portfolios["husband"]) == vars(make_portfolio(
        equity_pre=portfolios["husband"].equity_pre, bond_pre=portfolios["husband"].bond_pre,
        cash_pre=portfolios["husband"].cash_pre))
