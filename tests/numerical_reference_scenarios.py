"""Small, real-pipeline scenarios shared by read-only tests and manual capture."""

from pathlib import Path
from unittest.mock import patch

import numpy as np

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.engines import monteCarloEngine
from src.warpsimlab.sim.run_sim_core import simulate_yearly_portfolios
from src.warpsimlab.sim.simulation import run_pipeline
from tests.architectural_helpers import (
    make_execution_case, make_person, make_portfolio, make_simulation,
    public_input_tree,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests/reference_data/numerical/v1"
CASES = (
    "s1_single", "s2_married_nominal", "s2_married_real", "s2_married_raw",
    "s3_expenses", "s3_withdrawals", "s3_tax_funding", "s4_correlated", "s4_uncorrelated",
    "s5_historical_nominal", "s5_historical_real", "s6_baseline", "s6_modified",
)
SEED = 4201


def json_inputs(value):
    """Convert public pre-run inputs to portable JSON, without runtime caches."""
    value = public_input_tree(value)

    def convert(item):
        if isinstance(item, np.ndarray):
            return item.tolist()
        if isinstance(item, np.generic):
            return item.item()
        if isinstance(item, dict):
            return {key: convert(val) for key, val in item.items()}
        if isinstance(item, (tuple, list)):
            return [convert(val) for val in item]
        if isinstance(item, str):
            # Historical filenames are absolute for production loaders, portable in provenance.
            return item.replace(str(ROOT), "<workspace>")
        if item is None or isinstance(item, (str, int, float, bool)):
            return item
        raise TypeError(f"Unsupported scenario input: {type(item)}")

    return convert(value)


def flow(kind, amount, start, stop):
    return dict(name=kind, enabled=True, owner="husband", type=kind, amount=amount,
                start_age=start, end_age=stop, inflation_adjustment_pct=0.0)


def build_case(name):
    """Keep financial assumptions explicit while reusing existing object builders."""
    if name == "s1_single":
        case = make_execution_case(num_sims=1, years_to_simulate=12,
                                   second_person_enabled=False, tax_filing_status="Single",
                                   always_use_expense_mode=True, roth_flows=[
                                       flow("roth_ira_contribution", 3_000, 61, 64),
                                       flow("roth_workplace_contribution", 4_000, 61, 64),
                                   ], special_income_streams=[])
        case["husband"] = make_person(
            age=60, retire_age=65, income=110_000, ss=28_000, ss_age=67,
            annual_401k_contribution=12_000, annual_employer_match=4_000,
            annual_hsa_contribution=3_000, annual_hsa_employer_contribution=1_000,
            medicare_annual_cost=3_000,
        )
        case["wife"] = make_person()
        case["wife_portfolio"] = make_portfolio()
        case["sim_config"].wife_portfolio = case["wife_portfolio"]
        case["expenses"] = DynamicExpenses()
        case["expenses"].add_expense(2027, 45_000)
        case["expenses"].add_expense(2027, 2_000, is_hsa_eligible=True)
        return case
    if name.startswith("s3_"):
        expenses = DynamicExpenses()
        expenses.add_expense(2027, 65_000)
        expenses.add_expense(2027, 3_000, is_hsa_eligible=True)
        h_port = make_portfolio(cash_pre=180_000, cash_post=2_000,
                                cash_roth=15_000, hsa_cash=2_000)
        w_port = make_portfolio()
        return dict(
            husband=make_person(age=72, retire_age=72), wife=make_person(),
            husband_portfolio=h_port, wife_portfolio=w_port, expenses=expenses,
            sim_config=make_simulation(
                years_to_simulate=4, inflation_rate=0.025,
                husband_portfolio=h_port, wife_portfolio=w_port,
                include_rmd=True, calculate_income_taxes=True,
                calculate_state_taxes=True, state_of_residence="CO",
                roth_flows=[flow("roth_conversion", 180_000 if name == "s3_tax_funding" else 30_000, 73, 73)],
                always_use_expense_mode=name == "s3_expenses",
                retirement_withdraw_mode="Off" if name == "s3_tax_funding" else "Fixed Dollar Amount",
                retirement_withdraw_dollars=65_000,
            ),
        )
    options = dict(num_sims=1)
    if name.startswith("s2_"):
        options["inflation_mode"] = "real" if name.endswith("real") else "nominal"
        if name.endswith("raw"):
            options["years_to_simulate"] = 10
    elif name.startswith("s4_"):
        options.update(num_sims=3, results_mode="risk_analysis",
                       risk_analysis_mode="monte_carlo", always_use_expense_mode=True,
                       use_correlated_returns=name == "s4_correlated")
    elif name.startswith("s5_"):
        options.update(num_sims=3, results_mode="risk_analysis",
                       risk_analysis_mode="historical_windows", always_use_expense_mode=True,
                       inflation_mode="real" if name.endswith("real") else "nominal",
                       historical_asset_returns_file=str(DATA / "historical/asset_returns.csv"),
                       historical_inflation_file=str(DATA / "historical/inflation.csv"))
    else:
        raise ValueError(name)
    case = make_execution_case(**options)
    if name.startswith("s2_"):
        case["husband"].modeled_death_age = 74
    return case


def run_case(name):
    """Return complete core and the inputs actually supplied, before preparation."""
    if name.startswith("s6_"):
        # Existing headless Explorer setup exercises real snapshots and GUI builder.
        from tests.feature_tests.test_scenario_financial_isolation import make_session, session_input_tree

        manager, gui, state = make_session(True)
        inputs = dict(session=json_inputs(session_input_tree(gui, state)),
                      include_realestate=True, plot_style="fill", variant=name)
        original = gui.build_simulation_from_gui

        def observe_builder(*args, **kwargs):
            config = original(*args, **kwargs)
            inputs["resolved_config"] = json_inputs(config)
            return config

        with patch.object(gui, "build_simulation_from_gui", side_effect=observe_builder):
            if name == "s6_baseline":
                manager.compute_baseline_results(True, "fill")
                core = state.baseline_results["p"]["core"]
            else:
                core = manager.compute_scenario_results(True, "fill")["p"]["core"]
        return core, inputs
    case = build_case(name)
    inputs = json_inputs(case)
    inputs["seed"] = SEED
    inputs["boundary"] = "raw" if name.endswith("raw") else "pipeline"
    with patch.object(monteCarloEngine, "MONTE_CARLO_SEED", SEED):
        if name.endswith("raw"):
            core = simulate_yearly_portfolios(**case, num_sims=case["sim_config"].num_sims)
        else:
            core = run_pipeline(**case)["core"]
    return core, inputs


def activation_checks(name, core):
    """Return evidence and missing mechanisms; callers must report all missing ones."""
    checks = {}

    def positive(*fields):
        for field in fields:
            value = core
            for key in field.split("."):
                value = value[key]
            checks[field] = bool(np.any(value > 0))

    positive("taxes")
    if name == "s1_single":
        positive("employee_401k_contributions", "hsa_employee_contributions",
                 "hsa_employer_contributions", "hsa_qualified_withdrawals",
                 "roth_ira_contributions", "roth_workplace_contributions",
                 "medicare_cost", "payroll_tax", "state_income_tax", "fund_expenses",
                 "bond_interest", "cash_interest", "qualified_equity_distributions",
                 "breakdown_by_class.work", "breakdown_by_class.ss")
        checks["wages_and_contributions_stop"] = bool(
            np.all(core["breakdown_by_class"]["work"][:, 5:] == 0)
            and np.all(core["employee_401k_contributions"][:, 5:] == 0)
            and np.all(core["hsa_total_contributions"][:, 5:] == 0))
    elif name.startswith("s3_"):
        positive("rmd_husband", "roth_conversions")
        # Each mode has a different funding path. Checks below protect their union.
        checks["taxable_exhaustion"] = bool(np.any(core["post_tax_assets"][:, 1:] == 0))
        if name == "s3_expenses":
            positive("emergency_pre_tax_used", "hsa_qualified_withdrawals",
                     "funding_gap", "final_tax_delta", "final_tax_delta_uncovered")
            # Balance depletion independently confirms expense-funded Roth use.
            checks["roth_balance_spent"] = bool(np.any(
                np.diff(core["roth_assets"], axis=1) < 0))
        elif name == "s3_withdrawals":
            positive("breakdown_by_class.withdrawal", "roth_withdrawals", "funding_gap")
        else:
            positive("breakdown_by_class.tax_funding_withdrawal", "roth_withdrawals")
    else:
        positive("roth_conversions", "irmaa", "hsa_total_contributions",
                 "husband_death_event", "wife_death_event", "survivor_state",
                 "filing_status_single", "net_income_husband", "net_income_wife")
        checks["final_death"] = bool(np.all(core["terminal_year"] > 0))
        if name.startswith("s2_"):
            positive("rmd_husband", "rmd_wife", "breakdown_by_class.withdrawal")
            if name.endswith("raw"):
                checks["post_terminal_padding"] = bool(
                    np.all(core["effective_end_index"] < core["year"].shape[1] - 1))
        if name.startswith(("s4_", "s5_")):
            checks["three_distinct_paths"] = bool(
                core["total_assets"].shape[0] == 3
                and all(not np.array_equal(core["total_assets"][i], core["total_assets"][j])
                        for i, j in [(0, 1), (0, 2), (1, 2)]))
        if name.startswith("s5_"):
            checks["window_order"] = core["historical_window_start_year"].tolist() == [2000, 2001, 2002]
            checks["window_specific_magi"] = not np.array_equal(core["magi"][0], core["magi"][1])
    return checks
