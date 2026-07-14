from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.warpsimlab.dataClasses.portfolioState import PortfolioState
from src.warpsimlab.sim.engines import rothEngine


def make_sim_config(
    *,
    second_person_enabled: bool = True,
    roth_flows=None,
    years_to_simulate: int = 10,
    inflation_rate: float = 0.03,
):
    return SimpleNamespace(
        second_person_enabled=second_person_enabled,
        roth_flows=[] if roth_flows is None else roth_flows,
        years_to_simulate=years_to_simulate,
        inflation_rate=inflation_rate,
        subplot_mode="default",
        sim_type="portfolio_sim",
        monte_carlo_mode="pathBasedAnnualSampling",
        _active_historical_sim_index=None,
        _hist_inflation=None,
        _hist_window_start_indices=None,
    )


def make_flow(
    *,
    flow_type=rothEngine.ROTH_IRA_CONTRIBUTION,
    owner="husband",
    amount=1000.0,
    start_age=0,
    end_age=120,
    inflation_adjustment_pct=0.0,
    enabled=True,
):
    return {
        "type": flow_type,
        "owner": owner,
        "amount": amount,
        "start_age": start_age,
        "end_age": end_age,
        "inflation_adjustment_pct": inflation_adjustment_pct,
        "enabled": enabled,
    }


def make_requested_flows(
    *,
    ira_husband=0.0,
    ira_wife=0.0,
    workplace_husband=0.0,
    workplace_wife=0.0,
    conversion_husband=0.0,
    conversion_wife=0.0,
):
    ira_total = ira_husband + ira_wife
    workplace_total = workplace_husband + workplace_wife

    return {
        rothEngine.ROTH_IRA_CONTRIBUTION: {
            "husband": ira_husband,
            "wife": ira_wife,
            "total": ira_total,
        },
        rothEngine.ROTH_WORKPLACE_CONTRIBUTION: {
            "husband": workplace_husband,
            "wife": workplace_wife,
            "total": workplace_total,
        },
        rothEngine.ROTH_CONVERSION: {
            "husband": conversion_husband,
            "wife": conversion_wife,
            "total": conversion_husband + conversion_wife,
        },
        "requested_contribution_total": ira_total + workplace_total,
    }


def make_portfolio(
    *,
    eq_pre=0.0,
    bd_pre=0.0,
    cs_pre=0.0,
    eq_roth=0.0,
    bd_roth=0.0,
    cs_roth=0.0,
):
    return PortfolioState(
        eq_pre=eq_pre,
        bd_pre=bd_pre,
        cs_pre=cs_pre,
        eq_post=0.0,
        bd_post=0.0,
        cs_post=0.0,
        eq_roth=eq_roth,
        bd_roth=bd_roth,
        cs_roth=cs_roth,
        hsa_eq=0.0,
        hsa_bd=0.0,
        hsa_cs=0.0,
        re_post=0.0,
    )


def test_calculate_roth_flows_returns_zero_totals_when_no_flows():
    cfg = make_sim_config(roth_flows=[])

    result = rothEngine.calculate_roth_flows_for_year(
        curr_husband_age=50,
        curr_wife_age=48,
        year=3,
        sim_config=cfg,
    )

    for flow_type in rothEngine.ROTH_FLOW_TYPES:
        assert result[flow_type] == {
            "husband": 0.0,
            "wife": 0.0,
            "total": 0.0,
        }


def test_calculate_roth_flows_ignores_disabled_invalid_and_out_of_range_flows():
    cfg = make_sim_config(
        roth_flows=[
            make_flow(enabled=False, amount=100.0),
            make_flow(flow_type="invalid", amount=200.0),
            make_flow(owner="invalid", amount=300.0),
            make_flow(amount=400.0, start_age=60, end_age=70),
        ]
    )

    result = rothEngine.calculate_roth_flows_for_year(
        curr_husband_age=50,
        curr_wife_age=50,
        year=1,
        sim_config=cfg,
    )

    assert result[rothEngine.ROTH_IRA_CONTRIBUTION]["total"] == 0.0


@pytest.mark.parametrize("age", [50, 55])
def test_calculate_roth_flows_age_range_is_inclusive(age):
    cfg = make_sim_config(
        roth_flows=[
            make_flow(
                amount=1200.0,
                start_age=50,
                end_age=55,
            )
        ]
    )

    result = rothEngine.calculate_roth_flows_for_year(
        curr_husband_age=age,
        curr_wife_age=0,
        year=1,
        sim_config=cfg,
    )

    assert result[rothEngine.ROTH_IRA_CONTRIBUTION]["husband"] == pytest.approx(
        1200.0
    )


def test_calculate_roth_flows_sums_multiple_active_flows():
    cfg = make_sim_config(
        roth_flows=[
            make_flow(amount=1000.0),
            make_flow(amount=2500.0),
            make_flow(
                flow_type=rothEngine.ROTH_CONVERSION,
                amount=3000.0,
            ),
        ]
    )

    result = rothEngine.calculate_roth_flows_for_year(
        curr_husband_age=50,
        curr_wife_age=0,
        year=1,
        sim_config=cfg,
    )

    assert result[rothEngine.ROTH_IRA_CONTRIBUTION]["husband"] == pytest.approx(
        3500.0
    )
    assert result[rothEngine.ROTH_CONVERSION]["husband"] == pytest.approx(
        3000.0
    )


def test_calculate_roth_flows_ignores_wife_when_second_person_disabled():
    cfg = make_sim_config(
        second_person_enabled=False,
        roth_flows=[
            make_flow(owner="wife", amount=2000.0),
        ],
    )

    result = rothEngine.calculate_roth_flows_for_year(
        curr_husband_age=50,
        curr_wife_age=50,
        year=1,
        sim_config=cfg,
    )

    assert result[rothEngine.ROTH_IRA_CONTRIBUTION]["wife"] == 0.0
    assert result[rothEngine.ROTH_IRA_CONTRIBUTION]["total"] == 0.0


def test_calculate_roth_flows_applies_percent_of_inflation_adjustment():
    cfg = make_sim_config(
        inflation_rate=0.04,
        roth_flows=[
            make_flow(
                amount=1000.0,
                inflation_adjustment_pct=50.0,
            )
        ],
    )

    result = rothEngine.calculate_roth_flows_for_year(
        curr_husband_age=50,
        curr_wife_age=0,
        year=2,
        sim_config=cfg,
    )

    assert result[rothEngine.ROTH_IRA_CONTRIBUTION]["husband"] == pytest.approx(
        1000.0 * 1.02**2
    )


def test_calculate_roth_flows_uses_historical_inflation_path():
    cfg = make_sim_config(
        years_to_simulate=3,
        roth_flows=[
            make_flow(
                amount=1000.0,
                inflation_adjustment_pct=100.0,
            )
        ],
    )
    cfg.subplot_mode = "monte_carlo"
    cfg.monte_carlo_mode = "rollingHistoricalWindows"
    cfg._active_historical_sim_index = 0
    cfg._hist_window_start_indices = [1]
    cfg._hist_inflation = [0.99, 0.02, 0.03, 0.04]

    result = rothEngine.calculate_roth_flows_for_year(
        curr_husband_age=50,
        curr_wife_age=0,
        year=2,
        sim_config=cfg,
    )

    assert result[rothEngine.ROTH_IRA_CONTRIBUTION]["husband"] == pytest.approx(
        1000.0 * 1.02 * 1.03
    )


def test_prepare_requested_roth_flows_caps_only_workplace_contributions_by_wages():
    cfg = make_sim_config(
        roth_flows=[
            make_flow(
                flow_type=rothEngine.ROTH_IRA_CONTRIBUTION,
                owner="husband",
                amount=7000.0,
            ),
            make_flow(
                flow_type=rothEngine.ROTH_WORKPLACE_CONTRIBUTION,
                owner="husband",
                amount=12000.0,
            ),
            make_flow(
                flow_type=rothEngine.ROTH_CONVERSION,
                owner="husband",
                amount=50000.0,
            ),
            make_flow(
                flow_type=rothEngine.ROTH_WORKPLACE_CONTRIBUTION,
                owner="wife",
                amount=9000.0,
            ),
        ]
    )

    result = rothEngine.prepare_requested_roth_flows(
        curr_husband_age=50,
        curr_wife_age=48,
        year=1,
        payroll_wages_husband=5000.0,
        payroll_wages_wife=4000.0,
        second_person_enabled=True,
        sim_config=cfg,
    )

    assert result[rothEngine.ROTH_IRA_CONTRIBUTION]["husband"] == pytest.approx(
        7000.0
    )
    assert result[rothEngine.ROTH_WORKPLACE_CONTRIBUTION][
        "husband"
    ] == pytest.approx(5000.0)
    assert result[rothEngine.ROTH_WORKPLACE_CONTRIBUTION][
        "wife"
    ] == pytest.approx(4000.0)
    assert result[rothEngine.ROTH_CONVERSION]["husband"] == pytest.approx(
        50000.0
    )
    assert result["requested_contribution_total"] == pytest.approx(16000.0)


def test_allocate_funded_contributions_returns_zero_when_nothing_requested():
    result = rothEngine.allocate_funded_contributions(
        requested_ira_husband=0.0,
        requested_ira_wife=0.0,
        requested_workplace_husband=0.0,
        requested_workplace_wife=0.0,
        funded_total=1000.0,
    )

    assert result[rothEngine.ROTH_IRA_CONTRIBUTION]["total"] == 0.0
    assert result[rothEngine.ROTH_WORKPLACE_CONTRIBUTION]["total"] == 0.0


@pytest.mark.parametrize(
    ("funded_total", "expected_scale"),
    [
        (0.0, 0.0),
        (5000.0, 0.5),
        (10000.0, 1.0),
        (15000.0, 1.0),
    ],
)
def test_allocate_funded_contributions_scales_proportionally(
    funded_total,
    expected_scale,
):
    result = rothEngine.allocate_funded_contributions(
        requested_ira_husband=4000.0,
        requested_ira_wife=1000.0,
        requested_workplace_husband=3000.0,
        requested_workplace_wife=2000.0,
        funded_total=funded_total,
    )

    assert result[rothEngine.ROTH_IRA_CONTRIBUTION]["husband"] == pytest.approx(
        4000.0 * expected_scale
    )
    assert result[rothEngine.ROTH_IRA_CONTRIBUTION]["wife"] == pytest.approx(
        1000.0 * expected_scale
    )
    assert result[rothEngine.ROTH_WORKPLACE_CONTRIBUTION][
        "husband"
    ] == pytest.approx(3000.0 * expected_scale)
    assert result[rothEngine.ROTH_WORKPLACE_CONTRIBUTION][
        "wife"
    ] == pytest.approx(2000.0 * expected_scale)


def test_resolve_funded_contributions_adds_combined_total():
    requested = make_requested_flows(
        ira_husband=4000.0,
        ira_wife=1000.0,
        workplace_husband=3000.0,
        workplace_wife=2000.0,
    )

    result = rothEngine.resolve_funded_contributions(
        requested_flows=requested,
        funded_total=5000.0,
    )

    assert result["total"] == pytest.approx(5000.0)
    assert result[rothEngine.ROTH_IRA_CONTRIBUTION]["total"] == pytest.approx(
        2500.0
    )
    assert result[rothEngine.ROTH_WORKPLACE_CONTRIBUTION][
        "total"
    ] == pytest.approx(2500.0)


@pytest.mark.parametrize(
    ("uncovered_amount", "expected_funded", "expected_remaining"),
    [
        (0.0, 10000.0, 0.0),
        (2500.0, 7500.0, 0.0),
        (10000.0, 0.0, 0.0),
        (13000.0, 0.0, 3000.0),
    ],
)
def test_resolve_contribution_shortfall_uses_contributions_first(
    uncovered_amount,
    expected_funded,
    expected_remaining,
):
    requested = make_requested_flows(
        ira_husband=4000.0,
        ira_wife=1000.0,
        workplace_husband=3000.0,
        workplace_wife=2000.0,
    )

    result = rothEngine.resolve_contribution_shortfall(
        requested_flows=requested,
        uncovered_amount=uncovered_amount,
    )

    assert result["funded_contributions"]["total"] == pytest.approx(
        expected_funded
    )
    assert result["remaining_uncovered"] == pytest.approx(expected_remaining)


def test_separate_retirement_contribution_funding_reconciles_household_and_people():
    withdrawal_result = {
        "total": 30000.0,
        "rmd": 6000.0,
        "by_person": {
            "husband": 18000.0,
            "wife": 12000.0,
        },
        "rmd_by_person": {
            "husband": 4000.0,
            "wife": 2000.0,
        },
    }

    result = rothEngine.separate_retirement_contribution_funding(
        withdrawal_result=withdrawal_result,
        actual_contribution_total=6000.0,
    )

    assert result["household"] == pytest.approx(18000.0)
    assert result["husband"] == pytest.approx(10500.0)
    assert result["wife"] == pytest.approx(7500.0)
    assert result["husband"] + result["wife"] == pytest.approx(
        result["household"]
    )


def test_apply_roth_conversions_applies_actual_capped_amounts_by_owner():
    husband = make_portfolio(
        eq_pre=6000.0,
        bd_pre=3000.0,
        cs_pre=1000.0,
    )
    wife = make_portfolio(
        eq_pre=1000.0,
        bd_pre=1000.0,
        cs_pre=0.0,
    )
    requested = make_requested_flows(
        conversion_husband=4000.0,
        conversion_wife=5000.0,
    )

    result = rothEngine.apply_roth_conversions(
        husband_portfolio=husband,
        wife_portfolio=wife,
        requested_flows=requested,
        second_person_enabled=True,
    )

    assert result == {
        "husband": pytest.approx(4000.0),
        "wife": pytest.approx(2000.0),
        "total": pytest.approx(6000.0),
    }
    assert husband.total_value_pre == pytest.approx(6000.0)
    assert husband.total_value_roth == pytest.approx(4000.0)
    assert wife.total_value_pre == pytest.approx(0.0)
    assert wife.total_value_roth == pytest.approx(2000.0)


def test_apply_roth_conversions_does_not_touch_wife_when_disabled():
    husband = make_portfolio(eq_pre=5000.0)
    wife = make_portfolio(eq_pre=5000.0)
    requested = make_requested_flows(
        conversion_husband=1000.0,
        conversion_wife=2000.0,
    )

    result = rothEngine.apply_roth_conversions(
        husband_portfolio=husband,
        wife_portfolio=wife,
        requested_flows=requested,
        second_person_enabled=False,
    )

    assert result["husband"] == pytest.approx(1000.0)
    assert result["wife"] == 0.0
    assert wife.total_value_pre == pytest.approx(5000.0)
    assert wife.total_value_roth == pytest.approx(0.0)


def test_deposit_funded_roth_contributions_deposits_to_correct_owner():
    husband = make_portfolio(cs_roth=100.0)
    wife = make_portfolio(cs_roth=200.0)

    funded = rothEngine.resolve_funded_contributions(
        requested_flows=make_requested_flows(
            ira_husband=1000.0,
            ira_wife=2000.0,
            workplace_husband=3000.0,
            workplace_wife=4000.0,
        ),
        funded_total=10000.0,
    )

    result = rothEngine.deposit_funded_roth_contributions(
        husband_portfolio=husband,
        wife_portfolio=wife,
        funded_contributions=funded,
        second_person_enabled=True,
    )

    assert result == {
        "husband": pytest.approx(4000.0),
        "wife": pytest.approx(6000.0),
        "total": pytest.approx(10000.0),
    }
    assert husband.cs_roth == pytest.approx(4100.0)
    assert wife.cs_roth == pytest.approx(6200.0)


def test_deposit_funded_roth_contributions_skips_wife_when_disabled():
    husband = make_portfolio()
    wife = make_portfolio()

    funded = rothEngine.resolve_funded_contributions(
        requested_flows=make_requested_flows(
            ira_husband=1000.0,
            ira_wife=2000.0,
            workplace_husband=3000.0,
            workplace_wife=4000.0,
        ),
        funded_total=10000.0,
    )

    result = rothEngine.deposit_funded_roth_contributions(
        husband_portfolio=husband,
        wife_portfolio=wife,
        funded_contributions=funded,
        second_person_enabled=False,
    )

    assert result["husband"] == pytest.approx(4000.0)
    assert result["wife"] == 0.0
    assert result["total"] == pytest.approx(4000.0)
    assert husband.cs_roth == pytest.approx(4000.0)
    assert wife.cs_roth == pytest.approx(0.0)
