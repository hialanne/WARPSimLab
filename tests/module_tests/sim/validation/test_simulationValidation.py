import math

import pytest

from src.warpsimlab.sim.validation import SimulationValidationError, validate_simulation_inputs


def _valid_inputs(scenario_builders):
    return {
        "husband_portfolio": scenario_builders.Portfolio(equity_pre=100000.0),
        "wife_portfolio": scenario_builders.Portfolio(),
        "husband": scenario_builders.Person(age=50, retire_age=65, income=75000.0),
        "wife": scenario_builders.Person(age=48, retire_age=65),
        "expenses": scenario_builders.DynamicExpenses(),
        "sim_config": scenario_builders.make_config(),
    }


def _validate(inputs):
    validate_simulation_inputs(
        inputs["husband_portfolio"],
        inputs["wife_portfolio"],
        inputs["husband"],
        inputs["wife"],
        inputs["expenses"],
        inputs["sim_config"],
    )


def _valid_special_income():
    return {
        "owner": "husband",
        "name": "Consulting",
        "amount": 5000.0,
        "start_age": 60,
        "end_age": 65,
        "taxable": True,
        "enabled": True,
        "inflation_adjustment_pct": 0.0,
    }


def _valid_roth_flow():
    return {
        "owner": "husband",
        "type": "roth_conversion",
        "name": "Conversion",
        "amount": 10000.0,
        "start_age": 60,
        "end_age": 65,
        "enabled": True,
        "inflation_adjustment_pct": 0.0,
    }


def test_valid_inputs_pass(scenario_builders):
    _validate(_valid_inputs(scenario_builders))


def test_missing_sim_config_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["sim_config"] = None

    with pytest.raises(SimulationValidationError, match="Simulation configuration is required"):
        _validate(inputs)


def test_missing_husband_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["husband"] = None

    with pytest.raises(SimulationValidationError, match="husband is required"):
        _validate(inputs)


def test_missing_husband_portfolio_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["husband_portfolio"] = None

    with pytest.raises(SimulationValidationError, match="husband portfolio is required"):
        _validate(inputs)


def test_second_person_requires_wife(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["sim_config"].second_person_enabled = True
    inputs["wife"] = None

    with pytest.raises(SimulationValidationError, match="wife is required"):
        _validate(inputs)


def test_second_person_requires_wife_portfolio(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["sim_config"].second_person_enabled = True
    inputs["wife_portfolio"] = None

    with pytest.raises(SimulationValidationError, match="wife portfolio is required"):
        _validate(inputs)


def test_single_person_does_not_require_wife(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["wife"] = None
    inputs["wife_portfolio"] = None

    _validate(inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("years_to_simulate", 0),
        ("years_to_simulate", -1),
        ("num_sims", 0),
        ("num_sims", -1),
        ("historical_window_stride", 0),
        ("historical_window_stride", -1),
    ],
)
def test_positive_integer_config_fields_reject_non_positive_values(scenario_builders, field, value):
    inputs = _valid_inputs(scenario_builders)
    setattr(inputs["sim_config"], field, value)

    with pytest.raises(SimulationValidationError):
        _validate(inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sim_type", "unknown"),
        ("sim_initial_allocation_mode", "unknown"),
        ("plot_mode", "unknown"),
        ("subplot_mode", "unknown"),
        ("monte_carlo_plot_style", "unknown"),
        ("monte_carlo_mode", "unknown"),
        ("historical_window_mode", "unknown"),
        ("retirement_withdraw_mode", "unknown"),
    ],
)
def test_invalid_config_modes_rejected(scenario_builders, field, value):
    inputs = _valid_inputs(scenario_builders)
    setattr(inputs["sim_config"], field, value)

    with pytest.raises(SimulationValidationError):
        _validate(inputs)


@pytest.mark.parametrize(
    "field",
    [
        "second_person_enabled",
        "include_realestate",
        "calculate_income_taxes",
        "calculate_state_taxes",
        "use_fund_expenses",
        "use_correlated_returns",
        "include_rmd",
    ],
)
def test_boolean_config_fields_require_bool(scenario_builders, field):
    inputs = _valid_inputs(scenario_builders)
    setattr(inputs["sim_config"], field, 1)

    with pytest.raises(SimulationValidationError):
        _validate(inputs)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_market_return_rejected(scenario_builders, value):
    inputs = _valid_inputs(scenario_builders)
    inputs["sim_config"].eq_mean = value

    with pytest.raises(SimulationValidationError, match="must be finite"):
        _validate(inputs)


def test_negative_expected_return_is_valid(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["sim_config"].eq_mean = -0.25

    _validate(inputs)


def test_negative_inflation_is_valid(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["sim_config"].inflation_rate = -0.05

    _validate(inputs)


def test_negative_standard_deviation_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["sim_config"].eq_std = -0.01

    with pytest.raises(SimulationValidationError):
        _validate(inputs)


def test_zero_portfolio_is_valid(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["husband_portfolio"] = scenario_builders.Portfolio()

    _validate(inputs)


def test_large_portfolio_is_valid(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["husband_portfolio"].equity_pre = 1.0e15

    _validate(inputs)


def test_negative_portfolio_bucket_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["husband_portfolio"].equity_pre = -1.0

    with pytest.raises(SimulationValidationError):
        _validate(inputs)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_portfolio_bucket_rejected(scenario_builders, value):
    inputs = _valid_inputs(scenario_builders)
    inputs["husband_portfolio"].cash_post = value

    with pytest.raises(SimulationValidationError, match="must be finite"):
        _validate(inputs)


def test_zero_income_is_valid(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["husband"].income = 0.0

    _validate(inputs)


def test_negative_income_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["husband"].income = -1.0

    with pytest.raises(SimulationValidationError):
        _validate(inputs)


def test_retirement_age_before_current_age_is_valid(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["husband"].retire_age = 40

    _validate(inputs)


def test_large_retirement_age_is_valid(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["husband"].retire_age = 150

    _validate(inputs)


def test_negative_pension_inflation_adjustment_is_valid(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["husband"].pension_inflation_adjustment_pct = -50.0

    _validate(inputs)


def test_no_expenses_is_valid(scenario_builders):
    inputs = _valid_inputs(scenario_builders)

    _validate(inputs)


def test_blank_expense_start_year_has_human_readable_error(scenario_builders):
    inputs = _valid_inputs(scenario_builders)

    inputs["expenses"].add_expense(2026, 1000.0, comment="First")
    inputs["expenses"].add_expense(2027, 1000.0, comment="Second")
    inputs["expenses"].add_expense("", 1000.0, comment="Third")

    with pytest.raises(
        SimulationValidationError,
        match=r"Expenses / Start Year \(entry 3\) must not be blank and must be an integer\.",
    ):
        _validate(inputs)


def test_non_integer_expense_start_year_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["expenses"].add_expense("not-a-year", 1000.0)

    with pytest.raises(
        SimulationValidationError,
        match=r"Expenses / Start Year \(entry 1\) must be an integer\.",
    ):
        _validate(inputs)


def test_negative_expense_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["expenses"].add_expense(2026, -1.0)

    with pytest.raises(SimulationValidationError, match="Expenses / Annual Amount"):
        _validate(inputs)


def test_expense_end_before_start_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["expenses"].add_expense(2030, 1000.0, 2029)

    with pytest.raises(
        SimulationValidationError,
        match=r"Expenses / End Year \(entry 1\) must be greater than or equal to Start Year\.",
    ):
        _validate(inputs)


def test_large_expense_is_valid(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["expenses"].add_expense(2026, 1.0e12)

    _validate(inputs)


def test_valid_custom_allocation_passes(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["sim_config"].sim_initial_allocation_mode = "custom"
    inputs["sim_config"].custom_stock = 0.60
    inputs["sim_config"].custom_bonds = 0.30
    inputs["sim_config"].custom_cash = 0.10

    _validate(inputs)


def test_custom_allocation_must_total_one(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["sim_config"].sim_initial_allocation_mode = "custom"
    inputs["sim_config"].custom_stock = 0.60
    inputs["sim_config"].custom_bonds = 0.30
    inputs["sim_config"].custom_cash = 0.20

    with pytest.raises(SimulationValidationError, match="Custom asset allocation must total 1.0"):
        _validate(inputs)


def test_custom_allocation_component_cannot_exceed_one(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["sim_config"].sim_initial_allocation_mode = "custom"
    inputs["sim_config"].custom_stock = 1.20
    inputs["sim_config"].custom_bonds = 0.0
    inputs["sim_config"].custom_cash = 0.0

    with pytest.raises(SimulationValidationError, match="custom_stock cannot exceed 1.0"):
        _validate(inputs)


def test_valid_special_income_passes(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["sim_config"].special_income_streams = [_valid_special_income()]

    _validate(inputs)


def test_special_income_invalid_owner_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    stream = _valid_special_income()
    stream["owner"] = "other"
    inputs["sim_config"].special_income_streams = [stream]

    with pytest.raises(SimulationValidationError, match="owner is invalid"):
        _validate(inputs)


def test_special_income_negative_amount_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    stream = _valid_special_income()
    stream["amount"] = -1.0
    inputs["sim_config"].special_income_streams = [stream]

    with pytest.raises(SimulationValidationError):
        _validate(inputs)


def test_special_income_end_before_start_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    stream = _valid_special_income()
    stream["start_age"] = 70
    stream["end_age"] = 60
    inputs["sim_config"].special_income_streams = [stream]

    with pytest.raises(SimulationValidationError, match="end_age must be greater than or equal to start_age"):
        _validate(inputs)


def test_special_income_negative_inflation_adjustment_is_valid(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    stream = _valid_special_income()
    stream["inflation_adjustment_pct"] = -25.0
    inputs["sim_config"].special_income_streams = [stream]

    _validate(inputs)


def test_valid_roth_flow_passes(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    inputs["sim_config"].roth_flows = [_valid_roth_flow()]

    _validate(inputs)


def test_roth_flow_invalid_owner_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    flow = _valid_roth_flow()
    flow["owner"] = "other"
    inputs["sim_config"].roth_flows = [flow]

    with pytest.raises(SimulationValidationError, match="owner is invalid"):
        _validate(inputs)


def test_roth_flow_invalid_type_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    flow = _valid_roth_flow()
    flow["type"] = "unknown"
    inputs["sim_config"].roth_flows = [flow]

    with pytest.raises(SimulationValidationError, match="type is invalid"):
        _validate(inputs)


def test_roth_flow_negative_amount_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    flow = _valid_roth_flow()
    flow["amount"] = -1.0
    inputs["sim_config"].roth_flows = [flow]

    with pytest.raises(SimulationValidationError):
        _validate(inputs)


def test_roth_flow_end_before_start_rejected(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    flow = _valid_roth_flow()
    flow["start_age"] = 70
    flow["end_age"] = 60
    inputs["sim_config"].roth_flows = [flow]

    with pytest.raises(SimulationValidationError, match="end_age must be greater than or equal to start_age"):
        _validate(inputs)


def test_roth_flow_negative_inflation_adjustment_is_valid(scenario_builders):
    inputs = _valid_inputs(scenario_builders)
    flow = _valid_roth_flow()
    flow["inflation_adjustment_pct"] = -25.0
    inputs["sim_config"].roth_flows = [flow]

    _validate(inputs)