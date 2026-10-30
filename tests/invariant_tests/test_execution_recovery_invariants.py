"""User-state preservation after failed overlays and changes in execution mode."""

import copy

import pytest

from src.warpsimlab.sim import simulation
from tests.architectural_helpers import assert_tree_equal, public_input_tree, user_config_tree
from tests.invariant_helpers import accounting_case


@pytest.mark.parametrize("market", ["monte_carlo", "historical"])
@pytest.mark.parametrize("stage", ["tax", "fees", "combined"])
def test_failed_real_overlay_restores_user_inputs_and_allows_clean_recovery(monkeypatch, market, stage):
    case = accounting_case(market=market, overlay_tax_impacts=True, overlay_fund_expense_impacts=True)
    fresh = copy.deepcopy(case)
    config = case["sim_config"]
    before_config = user_config_tree(config)
    before_domain = public_input_tree({key: value for key, value in case.items() if key != "sim_config"})
    original = simulation._run_overlay_total_assets_line
    seen = []

    def fail_after_completed_overlay(*args):
        active = args[-1]
        phase = ("combined" if not active.calculate_income_taxes and not active.use_fund_expenses
                 else "tax" if not active.calculate_income_taxes else "fees")
        result = original(*args)
        seen.append(phase)
        if phase == stage:
            raise RuntimeError("injected failure after completed overlay")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(simulation, "_run_overlay_total_assets_line", fail_after_completed_overlay)
        with pytest.raises(RuntimeError, match="after completed overlay"):
            simulation.run_pipeline(**case)
    assert seen[-1] == stage
    assert_tree_equal(user_config_tree(config), before_config, "configuration after failure")
    assert_tree_equal(public_input_tree({key: value for key, value in case.items() if key != "sim_config"}),
                      before_domain, "domain inputs after failure")
    recovered = simulation.run_pipeline(**case)
    clean = simulation.run_pipeline(**fresh)
    assert_tree_equal(recovered["core"], clean["core"], "recovered financial paths")
    assert_tree_equal(recovered["summary_results"], clean["summary_results"])
    for field in ("median_without_taxes", "median_without_fund_expenses", "median_without_taxes_or_fund_expenses"):
        assert_tree_equal(getattr(recovered["portfolio_plot_data"], field), getattr(clean["portfolio_plot_data"], field))
    assert_tree_equal(user_config_tree(config), before_config, "configuration after recovery")


@pytest.mark.parametrize("expense_mode", [False, True])
@pytest.mark.parametrize("dollar_mode", ["nominal", "real"])
def test_changing_market_mode_and_horizon_on_reused_inputs_matches_fresh_cases(expense_mode, dollar_mode):
    case = accounting_case(expense_mode=expense_mode, inflation_mode=dollar_mode)
    pristine = copy.deepcopy(case)
    previous = []
    for market, horizon in [("historical", 8), ("monte_carlo", 5), ("fixed", 3), ("historical", 6), ("monte_carlo", 8)]:
        config = case["sim_config"]
        changes = dict(results_mode="fill" if market == "fixed" else "risk_analysis",
                       risk_analysis_mode="historical_windows" if market == "historical" else "monte_carlo",
                       historical_window_start_year=2000 if market == "historical" else None,
                       historical_window_stop_year=2002 if market == "historical" else None,
                       years_to_simulate=horizon)
        fresh = copy.deepcopy(pristine)
        for field, value in changes.items():
            setattr(config, field, value)
            setattr(fresh["sim_config"], field, value)
        before = user_config_tree(config)
        actual = simulation.run_pipeline(**case)
        expected = simulation.run_pipeline(**fresh)
        assert_tree_equal(actual["core"], expected["core"], f"{market}, {horizon} years")
        assert_tree_equal(user_config_tree(config), before, "only requested public settings changed")
        for output, saved in previous:
            assert_tree_equal(output, saved, "earlier result after mode change")
        previous.append((actual["core"], copy.deepcopy(actual["core"])))
