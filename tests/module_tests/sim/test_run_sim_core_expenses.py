from types import SimpleNamespace

import pytest


def _config(**overrides):
    values = dict(
        calculate_income_taxes=True,
        calculate_payroll_taxes=False,
        calculate_state_taxes=False,
        use_fund_expenses=False,
        fund_expense=0.0,
        rebalance_every_year=False,
        _post_tax_equity_dividend_yield=0.0,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def _portfolio(pre_tax=100.0):
    return SimpleNamespace(total_value_pre=pre_tax)


def _income(total=100.0, husband=100.0, wife=0.0):
    return {
        "total": total,
        "by_class": {
            "work": total,
            "pension": 0.0,
            "annuity": 0.0,
            "ss": 0.0,
            "rmd": 0.0,
            "withdrawal": 0.0,
            "tax_funding_withdrawal": 0.0,
            "bond_interest": 0.0,
            "cash_interest": 0.0,
            "qualified_equity_distributions": 0.0,
            "special_income": 0.0,
            "roth_conversion": 0.0,
        },
        "non_taxable_income": 0.0,
        "by_person": {"husband": husband, "wife": wife},
        "work_by_person": {"husband": husband, "wife": wife},
    }


def _funded(total=0.0):
    return {"total": total}


def _patch_common(monkeypatch, mod):
    monkeypatch.setattr(mod.withdrawalEngine, "calculate_rmds", lambda *a, **k: 0.0)
    monkeypatch.setattr(mod.withdrawalEngine, "withdraw_rmds", lambda *a, **k: 0.0)
    monkeypatch.setattr(mod.incomeEngine, "calculate_income_breakdown", lambda *a, **k: _income())
    monkeypatch.setattr(
        mod.portfolioEngine, "estimate_household_post_tax_income_components",
        lambda *a, **k: (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    )
    monkeypatch.setattr(mod.incomeEngine, "calculate_pre_tax_401k_contributions", lambda *a, **k: (0.0, 0.0))
    monkeypatch.setattr(mod.incomeEngine, "apply_employee_401k_to_income", lambda *a, **k: None)
    monkeypatch.setattr(mod.portfolioEngine, "apply_pre_tax_contribution", lambda *a, **k: None)
    monkeypatch.setattr(
        mod.hsaEngine, "calculate_hsa_contributions",
        lambda *a, **k: {"employee": 0.0, "employer": 0.0, "total": 0.0},
    )
    monkeypatch.setattr(mod.hsaEngine, "apply_employee_hsa_to_income", lambda *a, **k: None)
    monkeypatch.setattr(mod.hsaEngine, "deposit_hsa_contributions", lambda *a, **k: None)
    monkeypatch.setattr(
        mod.rothEngine, "prepare_requested_roth_flows",
        lambda **k: {"requested_contribution_total": 0.0},
    )
    monkeypatch.setattr(
        mod.rothEngine, "apply_roth_conversions",
        lambda **k: {"husband": 0.0, "wife": 0.0, "total": 0.0},
    )
    monkeypatch.setattr(
        mod.taxEngine, "calculate_employee_payroll_tax_split",
        lambda **k: (0.0, 0.0, 0.0, 0.0),
    )
    monkeypatch.setattr(
        mod.expenseEngine, "calculate_expense_breakdown",
        lambda *a, **k: {"total": 50.0, "hsa_eligible": 0.0, "non_hsa": 50.0},
    )
    monkeypatch.setattr(
        mod.hsaEngine, "pay_qualified_hsa_expenses",
        lambda *a, **k: {"paid": 0.0, "uncovered": 0.0},
    )
    monkeypatch.setattr(
        mod.taxEngine, "calculate_total_income_tax_split",
        lambda **k: (10.0, 0.0, 0.0, 10.0, 0.12),
    )

    zero_draw = {
        "post_tax_used": 0.0,
        "pre_tax_used": 0.0,
        "roth_used": 0.0,
        "hsa_used": 0.0,
        "real_estate_used": 0.0,
        "uncovered": 0.0,
    }

    monkeypatch.setattr(mod.portfolioEngine, "apply_net_income_single", lambda *a, **k: dict(zero_draw))
    monkeypatch.setattr(mod.portfolioEngine, "apply_net_income_couple", lambda *a, **k: dict(zero_draw))
    monkeypatch.setattr(
        mod.rothEngine, "resolve_contribution_shortfall",
        lambda **k: {"funded_contributions": _funded(), "remaining_uncovered": 0.0},
    )
    monkeypatch.setattr(mod.portfolioEngine, "deduct_post_tax_amount", lambda *a, **k: 0.0)
    monkeypatch.setattr(
        mod.rothEngine, "deposit_funded_roth_contributions",
        lambda **k: {"husband": 0.0, "wife": 0.0, "total": k["funded_contributions"]["total"]},
    )
    monkeypatch.setattr(mod.portfolioEngine, "apply_returns_and_fund_expenses", lambda *a, **k: 0.0)
    monkeypatch.setattr(mod.portfolioEngine, "rebalance", lambda *a, **k: None)
    monkeypatch.setattr(
        mod.taxEngine, "allocate_tax_proportionally_couple",
        lambda total, h, w: (total * h / (h + w), total * w / (h + w)),
    )


@pytest.fixture
def mod():
    from src.warpsimlab.sim import run_sim_core_expenses as mod
    return mod


def test_expense_year_withdraws_each_rmd_once(mod, monkeypatch):
    _patch_common(monkeypatch, mod)
    h_port, w_port = _portfolio(), _portfolio()
    calls = []

    monkeypatch.setattr(
        mod.withdrawalEngine,
        "calculate_rmds",
        lambda port, *a, **k: 5.0 if port is h_port else 7.0,
    )
    monkeypatch.setattr(
        mod.withdrawalEngine,
        "withdraw_rmds",
        lambda port, amount: calls.append((port, amount)),
    )
    monkeypatch.setattr(
        mod.incomeEngine,
        "calculate_income_breakdown",
        lambda h, w, ha, wa, rmd_h, rmd_w, year, cfg: _income(rmd_h + rmd_w, rmd_h, rmd_w),
    )
    monkeypatch.setattr(
        mod.expenseEngine,
        "calculate_expense_breakdown",
        lambda *a, **k: {"total": 0.0, "hsa_eligible": 0.0, "non_hsa": 0.0},
    )
    monkeypatch.setattr(
        mod.taxEngine,
        "calculate_total_income_tax_split",
        lambda **k: (0.0, 0.0, 0.0, 0.0, 0.0),
    )

    result = mod.simulate_expense_year(
        h_port,
        w_port,
        SimpleNamespace(),
        SimpleNamespace(),
        SimpleNamespace(),
        _config(),
        1,
        {"year": 1},
        74,
        72,
        {"eq": 0.0, "bd": 0.0, "cs": 0.0, "re": 0.0},
        True,
    )

    assert calls == [(h_port, 5.0), (w_port, 7.0)]
    assert result["rmd_h"] == pytest.approx(5.0)
    assert result["rmd_w"] == pytest.approx(7.0)


def test_expense_year_emergency_pre_tax_draw_recomputes_tax_and_is_reported(mod, monkeypatch):
    _patch_common(monkeypatch, mod)

    monkeypatch.setattr(
        mod.expenseEngine,
        "calculate_expense_breakdown",
        lambda *a, **k: {"total": 120.0, "hsa_eligible": 0.0, "non_hsa": 120.0},
    )
    monkeypatch.setattr(
        mod.portfolioEngine,
        "apply_net_income_single",
        lambda *a, **k: {
            "post_tax_used": 5.0,
            "pre_tax_used": 25.0,
            "roth_used": 0.0,
            "hsa_used": 0.0,
            "real_estate_used": 0.0,
            "uncovered": 0.0,
        },
    )

    tax_calls = []

    def tax_split(**kwargs):
        tax_calls.append(kwargs["ordinary_income"])
        if len(tax_calls) == 1:
            return 10.0, 0.0, 0.0, 10.0, 0.22
        return 16.0, 0.0, 0.0, 16.0, 0.22

    monkeypatch.setattr(mod.taxEngine, "calculate_total_income_tax_split", tax_split)
    monkeypatch.setattr(mod.portfolioEngine, "deduct_post_tax_amount", lambda *a, **k: 6.0)

    result = mod.simulate_expense_year(
        _portfolio(),
        _portfolio(),
        SimpleNamespace(),
        SimpleNamespace(),
        SimpleNamespace(),
        _config(),
        1,
        {"year": 1},
        61,
        0,
        {"eq": 0.0, "bd": 0.0, "cs": 0.0, "re": 0.0},
        False,
    )

    assert tax_calls == pytest.approx([100.0, 125.0])
    assert result["emergency_pre_tax_used"] == pytest.approx(25.0)
    assert result["pre_tax_withdrawal"] == pytest.approx(25.0)
    assert result["cash_flow_shortfall"] == pytest.approx(30.0)
    assert result["final_tax_delta"] == pytest.approx(6.0)
    assert result["final_tax_delta_deducted"] == pytest.approx(6.0)
    assert result["gross_income"] == pytest.approx(125.0)


def test_expense_year_distinguishes_qualified_and_taxable_hsa_withdrawals(mod, monkeypatch):
    _patch_common(monkeypatch, mod)

    monkeypatch.setattr(
        mod.expenseEngine,
        "calculate_expense_breakdown",
        lambda *a, **k: {"total": 40.0, "hsa_eligible": 15.0, "non_hsa": 25.0},
    )
    monkeypatch.setattr(
        mod.hsaEngine,
        "pay_qualified_hsa_expenses",
        lambda *a, **k: {"paid": 10.0, "uncovered": 5.0},
    )
    monkeypatch.setattr(
        mod.portfolioEngine,
        "apply_net_income_single",
        lambda *a, **k: {
            "post_tax_used": 0.0,
            "pre_tax_used": 0.0,
            "roth_used": 0.0,
            "hsa_used": 4.0,
            "real_estate_used": 0.0,
            "uncovered": 0.0,
        },
    )

    tax_calls = []

    def tax_split(**kwargs):
        tax_calls.append(kwargs["ordinary_income"])
        return 0.0, 0.0, 0.0, 0.0, 0.0

    monkeypatch.setattr(mod.taxEngine, "calculate_total_income_tax_split", tax_split)

    result = mod.simulate_expense_year(
        _portfolio(),
        _portfolio(),
        SimpleNamespace(),
        SimpleNamespace(),
        SimpleNamespace(),
        _config(calculate_income_taxes=False),
        1,
        {"year": 1},
        61,
        0,
        {"eq": 0.0, "bd": 0.0, "cs": 0.0, "re": 0.0},
        False,
    )

    assert result["qualified_hsa_withdrawal"] == pytest.approx(10.0)
    assert result["taxable_hsa_withdrawal"] == pytest.approx(4.0)
    assert result["wd_hsa"] == pytest.approx(14.0)
    assert result["gross_income"] == pytest.approx(104.0)
    assert tax_calls[-1] == pytest.approx(104.0)


def test_expense_year_reduces_roth_contributions_before_reporting_uncovered(mod, monkeypatch):
    _patch_common(monkeypatch, mod)

    monkeypatch.setattr(
        mod.rothEngine,
        "prepare_requested_roth_flows",
        lambda **k: {"requested_contribution_total": 20.0},
    )
    monkeypatch.setattr(
        mod.taxEngine,
        "calculate_total_income_tax_split",
        lambda **k: (0.0, 0.0, 0.0, 0.0, 0.0),
    )
    monkeypatch.setattr(
        mod.expenseEngine,
        "calculate_expense_breakdown",
        lambda *a, **k: {"total": 100.0, "hsa_eligible": 0.0, "non_hsa": 100.0},
    )
    monkeypatch.setattr(
        mod.portfolioEngine,
        "apply_net_income_single",
        lambda *a, **k: {
            "post_tax_used": 0.0,
            "pre_tax_used": 0.0,
            "roth_used": 0.0,
            "hsa_used": 0.0,
            "real_estate_used": 0.0,
            "uncovered": 12.0,
        },
    )

    seen = {}

    def resolve(**kwargs):
        seen["uncovered_amount"] = kwargs["uncovered_amount"]
        return {
            "funded_contributions": _funded(8.0),
            "remaining_uncovered": 4.0,
        }

    monkeypatch.setattr(mod.rothEngine, "resolve_contribution_shortfall", resolve)

    result = mod.simulate_expense_year(
        _portfolio(),
        _portfolio(),
        SimpleNamespace(),
        SimpleNamespace(),
        SimpleNamespace(),
        _config(calculate_income_taxes=False),
        1,
        {"year": 1},
        61,
        0,
        {"eq": 0.0, "bd": 0.0, "cs": 0.0, "re": 0.0},
        False,
    )

    assert seen["uncovered_amount"] == pytest.approx(12.0)
    assert result["funded_roth_contributions"]["total"] == pytest.approx(8.0)
    assert result["uncovered_expense"] == pytest.approx(4.0)
    assert result["net_profit"] == pytest.approx(-8.0)


def test_expense_year_applies_price_return_and_rebalances_both_people(mod, monkeypatch):
    _patch_common(monkeypatch, mod)

    cfg = _config(
        rebalance_every_year=True,
        use_fund_expenses=True,
        fund_expense=0.002,
        _post_tax_equity_dividend_yield=0.015,
    )

    h_port, w_port = _portfolio(), _portfolio()
    return_calls = []
    rebalance_calls = []

    def apply_returns(port, *args):
        return_calls.append((port, args))
        return 3.0 if port is h_port else 4.0

    monkeypatch.setattr(mod.portfolioEngine, "apply_returns_and_fund_expenses", apply_returns)
    monkeypatch.setattr(
        mod.portfolioEngine,
        "rebalance",
        lambda port, cfg: rebalance_calls.append(port),
    )

    result = mod.simulate_expense_year(
        h_port,
        w_port,
        SimpleNamespace(),
        SimpleNamespace(),
        SimpleNamespace(),
        cfg,
        1,
        {"year": 1},
        61,
        60,
        {"eq": 0.08, "bd": 0.03, "cs": 0.01, "re": 0.04},
        True,
    )

    assert len(return_calls) == 2
    assert return_calls[0][1] == pytest.approx((0.08, 0.065, 0.03, 0.01, 0.04, 0.002))
    assert rebalance_calls == [h_port, w_port]
    assert result["fund_expenses"] == pytest.approx(7.0)