"""Run preparation has one owner per independent financial core execution."""

from collections import Counter
from copy import deepcopy

import numpy as np
import pytest

from src.warpsimlab.sim import run_sim_core, run_sim_risk_reports
from src.warpsimlab.sim.engines import diagnosticEngine, medicareEngine, monteCarloEngine, portfolioEngine, taxEngine
from src.warpsimlab.sim.simulation import run_pipeline
from src.warpsimlab.sim.simulationObject import RunContext
from tests.architectural_helpers import assert_tree_equal, make_execution_case


@pytest.mark.parametrize("correlated", [False, True])
def test_core_owns_one_advancing_rng_and_prepares_once(monkeypatch, correlated):
    case = make_execution_case(results_mode="risk_analysis", use_correlated_returns=correlated)
    preparations, paths, normal_calls = [], [], []
    counts = Counter()
    original_rng = np.random.default_rng
    original_generate = monteCarloEngine.generate_market_path
    original_prepare = monteCarloEngine.prepare_market_path_sampling

    class RecordingGenerator:
        def __init__(self, seed):
            self.generator = original_rng(seed)

        def normal(self, *args, **kwargs):
            normal_calls.append((self, args, kwargs.copy()))
            return self.generator.normal(*args, **kwargs)

    def prepare(config, run_context=None):
        preparations.append(run_context)
        return original_prepare(config, run_context=run_context)

    def generate(config, years_to_simulate, sim_index=None, run_context=None):
        paths.append((run_context, run_context.mc_rng, sim_index))
        return original_generate(config, years_to_simulate, sim_index, run_context=run_context)

    def count_preparation(module, name):
        original = getattr(module, name)

        def counted(*args, **kwargs):
            counts[name] += 1
            return original(*args, **kwargs)

        monkeypatch.setattr(module, name, counted)

    monkeypatch.setattr(monteCarloEngine.np.random, "default_rng", RecordingGenerator)
    monkeypatch.setattr(monteCarloEngine, "prepare_market_path_sampling", prepare)
    monkeypatch.setattr(monteCarloEngine, "generate_market_path", generate)
    count_preparation(monteCarloEngine, "build_covariance_matrix")
    count_preparation(monteCarloEngine, "build_covariance_factor")
    count_preparation(taxEngine, "prepare_tax_run_context")
    count_preparation(medicareEngine, "prepare_medicare_run_context")
    first, first_run = run_pipeline(**case, return_run_context=True)
    second, second_run = run_pipeline(**case, return_run_context=True)
    assert first_run is not second_run
    assert preparations == [first_run, second_run]
    path_count = case["sim_config"].num_sims
    assert len(paths) == 2 * path_count
    for index, run in enumerate((first_run, second_run)):
        selected = paths[index * path_count:(index + 1) * path_count]
        assert all(context is run and rng is run.mc_rng for context, rng, _ in selected)
        assert [path_index for _, _, path_index in selected] == list(range(path_count))
    assert counts["prepare_tax_run_context"] == 2
    assert counts["prepare_medicare_run_context"] == 2
    assert counts["build_covariance_matrix"] == 2 * correlated
    assert counts["build_covariance_factor"] == 2 * correlated
    years = case["sim_config"].years_to_simulate
    if correlated:
        assert len(normal_calls) == 2 * path_count
        assert all(args == () and kwargs == {"size": (years, 4)} for _, args, kwargs in normal_calls)
    else:
        config = case["sim_config"]
        expected = [(config.eq_mean, config.eq_std, years), (config.bd_mean, config.bd_std, years),
            (config.cs_mean, config.cs_std, years), (config.re_mean, config.re_std, years)]
        assert [args for _, args, _ in normal_calls] == expected * (2 * path_count)
        assert all(kwargs == {} for _, _, kwargs in normal_calls)
    assert first.keys() == second.keys()
    for key in first:
        if key == "portfolio_plot_data":
            assert_tree_equal(vars(first[key]), vars(second[key]))
        else:
            assert_tree_equal(first[key], second[key])
    assert not any(name.startswith(("_mc_", "_hist_", "_post_tax_")) for name in vars(case["sim_config"]))


def test_secondary_cores_have_independent_contexts(monkeypatch):
    contexts = []
    original = run_sim_core.RunContext

    def create():
        context = original()
        contexts.append(context)
        return context

    monkeypatch.setattr(run_sim_core, "RunContext", create)
    case = make_execution_case(results_mode="risk_analysis", overlay_tax_impacts=True,
        overlay_fund_expense_impacts=True, calculate_simulated_shortfall_rate=True)
    result, baseline = run_pipeline(**case, return_run_context=True)
    assert len(contexts) == 4
    assert baseline is contexts[0]
    assert len({id(context) for context in contexts}) == 4
    assert len({id(context.mc_rng) for context in contexts}) == 4
    assert all(context.mc_seed == monteCarloEngine.MONTE_CARLO_SEED for context in contexts)
    assert hasattr(result["portfolio_plot_data"], "median_without_taxes_or_fund_expenses")


def test_allocation_and_normalized_yields_keep_configuration_independent(monkeypatch):
    case = make_execution_case(sim_initial_allocation_mode="maintain-current-allocation",
        post_tax_equity_dividend_yield=-0.01, post_tax_bond_interest_yield=0.04,
        post_tax_cash_interest_yield=-0.02)
    config = case["sim_config"]
    calls = []
    original = portfolioEngine.compute_household_allocation_targets
    initial = deepcopy(case["husband_portfolio"])

    def prepare(husband_portfolio, wife_portfolio, actual_config, run_context=None):
        assert vars(husband_portfolio) == vars(initial)
        calls.append(run_context)
        return original(husband_portfolio, wife_portfolio, actual_config, run_context=run_context)

    monkeypatch.setattr(portfolioEngine, "compute_household_allocation_targets", prepare)
    _, run = run_pipeline(**case, return_run_context=True)
    assert calls == [run]
    assert run.household_eq_target + run.household_bd_target + run.household_cs_target == pytest.approx(1.0)
    assert run.post_tax_equity_dividend_yield_normalized == 0.0
    assert run.post_tax_bond_interest_yield_normalized == 0.04
    assert run.post_tax_cash_interest_yield_normalized == 0.0
    assert config.post_tax_equity_dividend_yield == -0.01
    assert config.post_tax_cash_interest_yield == -0.02
    assert not hasattr(config, "household_eq_target")


def test_standalone_market_preparation_returns_explicit_context_and_report_seed():
    config = make_execution_case(results_mode="risk_analysis")["sim_config"]
    run = monteCarloEngine.prepare_market_path_sampling(config)
    assert isinstance(run, RunContext)
    first = monteCarloEngine.generate_market_path(config, 3, run_context=run)
    second = monteCarloEngine.generate_market_path(config, 3, run_context=run)
    assert not np.array_equal(first["eq"], second["eq"])
    snapshot = run_sim_risk_reports._build_simulation_snapshot(config, "Monte Carlo", 2, 3, run_context=run)
    assert snapshot["Random Seed"] == run.mc_seed
    assert not hasattr(config, "_mc_seed")


def test_run_diagnostics_preserve_prepared_state_and_exclude_rng(diagnostic_home):
    config = make_execution_case(results_mode="risk_analysis")["sim_config"]
    run = monteCarloEngine.prepare_market_path_sampling(config)
    path = diagnosticEngine._write_diagnostic_report("test", config, {}, [], run_context=run)
    assert path is not None
    report = path.read_text(encoding="utf-8")
    assert "Run Context" in report
    assert f"mc_seed: {run.mc_seed}" in report
    assert "mc_means:" in report
    assert "mc_rng:" not in report
