import types
import pytest

from src.warpsimlab.sim.engines.expenseEngine import (
    calculate_expenses,
    initialize_expense_engine_for_simulation,
)


class DummyExpenses:
    def __init__(self, yearly_amount: float):
        self.yearly_amount = yearly_amount
        self.requested_year = None

    def get_total_expense_for_year(self, year: int) -> float:
        self.requested_year = year
        return self.yearly_amount


def make_config(*, inflation_rate: float, start_year: int, scenario_expense_multiplier: float, years_to_simulate: int = 5):
    cfg = types.SimpleNamespace(
        years_to_simulate=years_to_simulate,
        inflation_rate=inflation_rate,
        start_year=start_year,
        scenario_expense_multiplier=scenario_expense_multiplier,
        subplot_mode=None,
        sim_type=None,
    )
    initialize_expense_engine_for_simulation(cfg)
    return cfg


def test_expense_basic_no_inflation():
    expenses = DummyExpenses(10000)
    sim_config = make_config(
        inflation_rate=0.0,
        start_year=2025,
        scenario_expense_multiplier=1.0,
    )

    result = calculate_expenses(expenses, year=0, sim_config=sim_config)

    assert result == 10000


def test_expense_uses_correct_calendar_year():
    expenses = DummyExpenses(10000)
    sim_config = make_config(
        inflation_rate=0.0,
        start_year=2025,
        scenario_expense_multiplier=1.0,
    )

    calculate_expenses(expenses, year=3, sim_config=sim_config)

    assert expenses.requested_year == 2028


def test_expense_scenario_multiplier():
    expenses = DummyExpenses(10000)
    sim_config = make_config(
        inflation_rate=0.0,
        start_year=2025,
        scenario_expense_multiplier=1.5,
    )

    result = calculate_expenses(expenses, year=0, sim_config=sim_config)

    assert result == 15000


def test_expense_inflation_growth():
    expenses = DummyExpenses(10000)
    sim_config = make_config(
        inflation_rate=0.05,
        start_year=2025,
        scenario_expense_multiplier=1.0,
    )

    result = calculate_expenses(expenses, year=2, sim_config=sim_config)

    expected = 10000 * (1.05 ** 2)
    assert result == pytest.approx(expected)


def test_expense_multiplier_then_inflation():
    expenses = DummyExpenses(10000)
    sim_config = make_config(
        inflation_rate=0.10,
        start_year=2025,
        scenario_expense_multiplier=2.0,
    )

    result = calculate_expenses(expenses, year=1, sim_config=sim_config)

    expected = 10000 * 2.0 * 1.10
    assert result == pytest.approx(expected)
