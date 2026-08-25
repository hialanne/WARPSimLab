import math
from numbers import Integral, Real

from .validationError import SimulationValidationError


ROTH_FLOW_TYPES = {
    "roth_ira_contribution",
    "roth_workplace_contribution",
    "roth_conversion",
}

SIM_TYPES = {
    "income_sim",
    "cashflow_sim",
    "operating_balance_sim",
    "portfolio_sim",
    "summary_sim",
    "summary_report",
    "year_by_year_report",
    "tax_report",
    "historical_window_risk_report",
    "monte_carlo_risk_report",
    "spending_comparison_report",
    "asset_allocation_comparison_report",
    "retirement_ss_comparison_report",
}

INITIAL_ALLOCATION_MODES = {
    "none",
    "maintain-current-allocation",
    "dont-rebalance",
    "30-30-40",
    "50-30-20",
    "70-20-10",
    "custom",
}

PLOT_MODES = {
    "raw",
    "real",
}

SUBPLOT_MODES = {
    "fill",
    "monte_carlo",
    "sub_categories",
    "pre_post_tax",
}

MONTE_CARLO_PLOT_STYLES = {
    "fill",
    "line",
    "all_lines",
}

MONTE_CARLO_MODES = {
    "pathBasedAnnualSampling",
    "rollingHistoricalWindows",
}

HISTORICAL_WINDOW_MODES = {
    "rolling_overlapping_all",
}

RETIREMENT_WITHDRAW_MODES = {
    "Off",
    "Percentage",
    "Percentage + Inflation",
    "Fixed Dollar Amount",
    "Fixed Dollar Amount + Inflation",
}

PORTFOLIO_FIELDS = (
    "equity_pre",
    "equity_post",
    "equity_roth",
    "bond_pre",
    "bond_post",
    "bond_roth",
    "cash_pre",
    "cash_post",
    "cash_roth",
    "hsa_cash",
    "hsa_equity",
    "hsa_bond",
    "real_estate",
)

PERSON_NONNEGATIVE_FIELDS = (
    "income",
    "ss",
    "pension",
    "annuity",
    "annual_401k_contribution",
    "annual_employer_match",
)

PERSON_AGE_FIELDS = (
    "age",
    "retire_age",
    "ss_age",
    "pension_age",
    "annuity_age",
)


def _fail(message):
    raise SimulationValidationError(message)


def _require(condition, message):
    if not condition:
        _fail(message)


def _require_real(name, value, minimum=None, strictly_positive=False):
    if value is None or (isinstance(value, str) and not value.strip()):
        _fail(f"{name} must not be blank and must be numeric.")

    if isinstance(value, bool) or not isinstance(value, Real):
        _fail(f"{name} must be numeric.")

    if not math.isfinite(float(value)):
        _fail(f"{name} must be finite.")

    if strictly_positive and value <= 0:
        _fail(f"{name} must be greater than 0.")

    if minimum is not None and value < minimum:
        _fail(f"{name} must be at least {minimum}.")


def _require_integer(name, value, minimum=None, strictly_positive=False):
    if value is None or (isinstance(value, str) and not value.strip()):
        _fail(f"{name} must not be blank and must be an integer.")

    if isinstance(value, bool) or not isinstance(value, Integral):
        _fail(f"{name} must be an integer.")

    if strictly_positive and value <= 0:
        _fail(f"{name} must be greater than 0.")

    if minimum is not None and value < minimum:
        _fail(f"{name} must be at least {minimum}.")


def _require_bool(name, value):
    if not isinstance(value, bool):
        _fail(f"{name} must be True or False.")


def _require_choice(name, value, valid_values):
    if value not in valid_values:
        _fail(f"{name} has unsupported value {value!r}. Valid values are: {sorted(valid_values)}.")


def _require_dict_keys(name, value, required_keys):
    if not isinstance(value, dict):
        _fail(f"{name} must be a dictionary.")

    missing = [key for key in required_keys if key not in value]
    if missing:
        _fail(f"{name} is missing required field(s): {', '.join(missing)}.")


def _validate_person(label, person):
    _require(person is not None, f"{label} is required.")

    for field in PERSON_AGE_FIELDS:
        value = getattr(person, field, None)
        _require_integer(f"{label}.{field}", value, minimum=0)

    for field in PERSON_NONNEGATIVE_FIELDS:
        value = getattr(person, field, None)
        _require_real(f"{label}.{field}", value, minimum=0.0)

    _require_real(
        f"{label}.pension_inflation_adjustment_pct",
        getattr(person, "pension_inflation_adjustment_pct", None),
    )


def _validate_portfolio(label, portfolio):
    _require(portfolio is not None, f"{label} portfolio is required.")

    for field in PORTFOLIO_FIELDS:
        value = getattr(portfolio, field, None)
        _require_real(f"{label}_portfolio.{field}", value, minimum=0.0)


def _validate_expenses(expenses):
    _require(expenses is not None, "Expenses are required.")

    expense_list = getattr(expenses, "expenses", None)
    _require(isinstance(expense_list, list), "Expenses must contain an expenses list.")

    required_keys = {"start_year", "end_year", "cost", "comment"}

    for index, expense in enumerate(expense_list):
        name = f"expenses[{index}]"
        _require_dict_keys(name, expense, required_keys)

        entry = index + 1

        _require_integer(f"Expenses / Start Year (entry {entry})", expense["start_year"], minimum=0)
        _require_real(f"Expenses / Annual Amount (entry {entry})", expense["cost"], minimum=0.0)

        end_year = expense["end_year"]
        if end_year is not None:
            _require_integer(f"Expenses / End Year (entry {entry})", end_year, minimum=0)
            _require(
                end_year >= expense["start_year"],
                f"Expenses / End Year (entry {entry}) must be greater than or equal to Start Year.",
            )

        _require(
            isinstance(expense["comment"], str),
            f"Expenses / Description (entry {entry}) must be text.",
        )

def _validate_special_income_streams(sim_config):
    streams = getattr(sim_config, "special_income_streams", None)
    _require(isinstance(streams, list), "special_income_streams must be a list.")

    required_keys = {
        "owner",
        "name",
        "amount",
        "start_age",
        "end_age",
        "taxable",
        "enabled",
        "inflation_adjustment_pct",
    }

    for index, stream in enumerate(streams):
        name = f"special_income_streams[{index}]"
        _require_dict_keys(name, stream, required_keys)

        _require(stream["owner"] in {"husband", "wife"}, f"{name}.owner is invalid.")
        _require(isinstance(stream["name"], str), f"{name}.name must be a string.")
        _require_real(f"{name}.amount", stream["amount"], minimum=0.0)
        _require_integer(f"{name}.start_age", stream["start_age"], minimum=0)
        _require_integer(f"{name}.end_age", stream["end_age"], minimum=0)
        _require(
            stream["end_age"] >= stream["start_age"],
            f"{name}.end_age must be greater than or equal to start_age.",
        )
        _require_bool(f"{name}.taxable", stream["taxable"])
        _require_bool(f"{name}.enabled", stream["enabled"])
        _require_real(f"{name}.inflation_adjustment_pct", stream["inflation_adjustment_pct"])


def _validate_roth_flows(sim_config):
    flows = getattr(sim_config, "roth_flows", None)
    _require(isinstance(flows, list), "roth_flows must be a list.")

    required_keys = {
        "owner",
        "type",
        "name",
        "amount",
        "start_age",
        "end_age",
        "enabled",
        "inflation_adjustment_pct",
    }

    for index, flow in enumerate(flows):
        name = f"roth_flows[{index}]"
        _require_dict_keys(name, flow, required_keys)

        _require(flow["owner"] in {"husband", "wife"}, f"{name}.owner is invalid.")
        _require(flow["type"] in ROTH_FLOW_TYPES, f"{name}.type is invalid.")
        _require(isinstance(flow["name"], str), f"{name}.name must be a string.")
        _require_real(f"{name}.amount", flow["amount"], minimum=0.0)
        _require_integer(f"{name}.start_age", flow["start_age"], minimum=0)
        _require_integer(f"{name}.end_age", flow["end_age"], minimum=0)
        _require(
            flow["end_age"] >= flow["start_age"],
            f"{name}.end_age must be greater than or equal to start_age.",
        )
        _require_bool(f"{name}.enabled", flow["enabled"])
        _require_real(f"{name}.inflation_adjustment_pct", flow["inflation_adjustment_pct"])


def _validate_sim_config(sim_config):
    _require(sim_config is not None, "Simulation configuration is required.")

    _require_choice("sim_config.sim_type", getattr(sim_config, "sim_type", None), SIM_TYPES)
    _require_choice(
        "sim_config.sim_initial_allocation_mode",
        getattr(sim_config, "sim_initial_allocation_mode", None),
        INITIAL_ALLOCATION_MODES,
    )
    _require_choice("sim_config.plot_mode", getattr(sim_config, "plot_mode", None), PLOT_MODES)
    _require_choice("sim_config.subplot_mode", getattr(sim_config, "subplot_mode", None), SUBPLOT_MODES)
    _require_choice(
        "sim_config.monte_carlo_plot_style",
        getattr(sim_config, "monte_carlo_plot_style", None),
        MONTE_CARLO_PLOT_STYLES,
    )
    _require_choice(
        "sim_config.monte_carlo_mode",
        getattr(sim_config, "monte_carlo_mode", None),
        MONTE_CARLO_MODES,
    )
    _require_choice(
        "sim_config.historical_window_mode",
        getattr(sim_config, "historical_window_mode", None),
        HISTORICAL_WINDOW_MODES,
    )
    _require_choice(
        "sim_config.retirement_withdraw_mode",
        getattr(sim_config, "retirement_withdraw_mode", None),
        RETIREMENT_WITHDRAW_MODES,
    )

    _require_integer("sim_config.start_year", getattr(sim_config, "start_year", None), strictly_positive=True)
    _require_integer(
        "sim_config.years_to_simulate",
        getattr(sim_config, "years_to_simulate", None),
        strictly_positive=True,
    )
    _require_integer("sim_config.num_sims", getattr(sim_config, "num_sims", None), strictly_positive=True)

    _require_real("sim_config.inflation_rate", getattr(sim_config, "inflation_rate", None))
    _require_real("sim_config.fund_expense", getattr(sim_config, "fund_expense", None), minimum=0.0)

    for field in ("eq_mean", "bd_mean", "cs_mean", "re_mean"):
        _require_real(f"sim_config.{field}", getattr(sim_config, field, None))

    for field in ("eq_std", "bd_std", "cs_std", "re_std"):
        _require_real(f"sim_config.{field}", getattr(sim_config, field, None), minimum=0.0)

    _require_real(
        "sim_config.retirement_withdraw_pct",
        getattr(sim_config, "retirement_withdraw_pct", None),
        minimum=0.0,
    )
    _require_real(
        "sim_config.retirement_withdraw_dollars",
        getattr(sim_config, "retirement_withdraw_dollars", None),
        minimum=0.0,
    )
    _require_real(
        "sim_config.scenario_expense_multiplier",
        getattr(sim_config, "scenario_expense_multiplier", None),
        minimum=0.0,
    )

    _require_integer(
        "sim_config.historical_window_stride",
        getattr(sim_config, "historical_window_stride", None),
        strictly_positive=True,
    )

    for field in (
        "second_person_enabled",
        "include_realestate",
        "calculate_income_taxes",
        "calculate_state_taxes",
        "use_fund_expenses",
        "use_correlated_returns",
        "include_rmd",
    ):
        _require_bool(f"sim_config.{field}", getattr(sim_config, field, None))

    if sim_config.sim_initial_allocation_mode == "custom":
        stock = getattr(sim_config, "custom_stock", None)
        bonds = getattr(sim_config, "custom_bonds", None)
        cash = getattr(sim_config, "custom_cash", None)

        _require_real("sim_config.custom_stock", stock, minimum=0.0)
        _require_real("sim_config.custom_bonds", bonds, minimum=0.0)
        _require_real("sim_config.custom_cash", cash, minimum=0.0)

        _require(stock <= 1.0, "sim_config.custom_stock cannot exceed 1.0.")
        _require(bonds <= 1.0, "sim_config.custom_bonds cannot exceed 1.0.")
        _require(cash <= 1.0, "sim_config.custom_cash cannot exceed 1.0.")

        allocation_total = stock + bonds + cash
        _require(
            math.isclose(allocation_total, 1.0, rel_tol=0.0, abs_tol=1.0e-9),
            f"Custom asset allocation must total 1.0; current total is {allocation_total:.6f}.",
        )

    _validate_special_income_streams(sim_config)
    _validate_roth_flows(sim_config)


def _validate_household(husband_portfolio, wife_portfolio, husband, wife, sim_config):
    _validate_person("husband", husband)
    _validate_portfolio("husband", husband_portfolio)

    if sim_config.second_person_enabled:
        _validate_person("wife", wife)
        _validate_portfolio("wife", wife_portfolio)


def validate_simulation_inputs(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config):
    """Validate the contract required by the WARPSimLab simulation core."""
    _validate_sim_config(sim_config)
    _validate_household(husband_portfolio, wife_portfolio, husband, wife, sim_config)
    _validate_expenses(expenses)