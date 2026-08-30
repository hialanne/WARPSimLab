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


def _income(total=0.0, husband=0.0, wife=0.0, rmd=0.0):
    return {
        "total": total,
        "by_class": {
            "work": 0.0,
            "pension": 0.0,
            "annuity": 0.0,
            "ss": 0.0,
            "rmd": rmd,
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
        "work_by_person": {"husband": 0.0, "wife": 0.0},
    }


def _requested(mod, *, contribution=0.0, conversion_h=0.0, conversion_w=0.0):
    return {
        mod.rothEngine.ROTH_CONVERSION: {
            "husband": conversion_h,
            "wife": conversion_w,
            "total": conversion_h + conversion_w,
        },
        "requested_contribution_total": contribution,
    }


def _funded(total=0.0):
    return {"total": total}


def _zero_tax_funding():
    return {
        "total": 0.0,
        "pre_tax": 0.0,
        "roth": 0.0,
        "hsa": 0.0,
        "by_person": {"husband": 0.0, "wife": 0.0},
    }


def _patch_common(monkeypatch, mod):
    monkeypatch.setattr(mod.withdrawalEngine, "calculate_rmds", lambda *a, **k: 0.0)
    monkeypatch.setattr(mod.incomeEngine, "calculate_income_breakdown", lambda *a, **k: _income())
    monkeypatch.setattr(
        mod.portfolioEngine,
        "estimate_household_post_tax_income_components",
        lambda *a, **k: (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    )
    monkeypatch.setattr(
        mod.rothEngine,
        "prepare_requested_roth_flows",
        lambda **k: _requested(mod),
    )
    monkeypatch.setattr(
        mod.rothEngine,
        "apply_roth_conversions",
        lambda **k: {"husband": 0.0, "wife": 0.0, "total": 0.0},
    )
    monkeypatch.setattr(
        mod.taxEngine,
        "calculate_employee_payroll_tax_split",
        lambda **k: (0.0, 0.0, 0.0, 0.0),
    )
    monkeypatch.setattr(
        mod.withdrawalEngine,
        "calculate_retirement_withdrawal",
        lambda *a, **k: {
            "total": 30.0,
            "rmd": 0.0,
            "pre_tax": 20.0,
            "post_tax": 10.0,
            "roth": 0.0,
            "hsa": 0.0,
            "uncovered": 0.0,
            "by_person": {"husband": 30.0, "wife": 0.0},
            "rmd_by_person": {"husband": 0.0, "wife": 0.0},
        },
    )
    monkeypatch.setattr(
        mod.rothEngine,
        "resolve_contribution_shortfall",
        lambda **k: {"funded_contributions": _funded(), "remaining_uncovered": 0.0},
    )
    monkeypatch.setattr(
        mod.rothEngine,
        "separate_retirement_contribution_funding",
        lambda **k: {"household": 30.0, "husband": 30.0, "wife": 0.0},
    )
    monkeypatch.setattr(
        mod.taxEngine,
        "calculate_total_income_tax_split",
        lambda **k: (0.0, 0.0, 0.0, 0.0, 0.0),
    )
    monkeypatch.setattr(
        mod.withdrawalEngine,
        "fund_tax_cash_shortfall",
        lambda *a, **k: _zero_tax_funding(),
    )
    monkeypatch.setattr(
        mod.rothEngine,
        "deposit_funded_roth_contributions",
        lambda **k: {"husband": 0.0, "wife": 0.0, "total": k["funded_contributions"]["total"]},
    )
    monkeypatch.setattr(mod.portfolioEngine, "apply_returns_and_fund_expenses", lambda *a, **k: 0.0)
    monkeypatch.setattr(mod.portfolioEngine, "rebalance", lambda *a, **k: None)
    monkeypatch.setattr(
        mod.taxEngine,
        "allocate_tax_proportionally_couple",
        lambda total, h, w: (total * h / (h + w), total * w / (h + w)),
    )


@pytest.fixture
def mod():
    from src.warpsimlab.sim import run_sim_core_withdrawals as mod
    return mod


def test_withdrawal_year_reserves_rmd_before_roth_conversion(mod, monkeypatch):
    _patch_common(monkeypatch, mod)

    h_port = _portfolio(100.0)
    seen = {}

    monkeypatch.setattr(
        mod.withdrawalEngine,
        "calculate_rmds",
        lambda port, *a, **k: 30.0,
    )
    monkeypatch.setattr(
        mod.incomeEngine,
        "calculate_income_breakdown",
        lambda h, w, ha, wa, rmd_h, rmd_w, year, cfg: _income(rmd_h, rmd_h, 0.0, rmd_h),
    )
    monkeypatch.setattr(
        mod.rothEngine,
        "prepare_requested_roth_flows",
        lambda **k: _requested(mod, conversion_h=90.0),
    )

    def apply_conversions(**kwargs):
        seen["requested"] = kwargs["requested_flows"][mod.rothEngine.ROTH_CONVERSION].copy()
        return {
            "husband": seen["requested"]["husband"],
            "wife": 0.0,
            "total": seen["requested"]["husband"],
        }

    monkeypatch.setattr(mod.rothEngine, "apply_roth_conversions", apply_conversions)

    def retirement_withdrawal(*args, **kwargs):
        seen["rmd_h"] = kwargs["rmd_h"]
        return {
            "total": 30.0,
            "rmd": 30.0,
            "pre_tax": 0.0,
            "post_tax": 0.0,
            "roth": 0.0,
            "hsa": 0.0,
            "uncovered": 0.0,
            "by_person": {"husband": 30.0, "wife": 0.0},
            "rmd_by_person": {"husband": 30.0, "wife": 0.0},
        }

    monkeypatch.setattr(
        mod.withdrawalEngine,
        "calculate_retirement_withdrawal",
        retirement_withdrawal,
    )
    monkeypatch.setattr(
        mod.rothEngine,
        "separate_retirement_contribution_funding",
        lambda **k: {"household": 0.0, "husband": 0.0, "wife": 0.0},
    )

    result = mod.simulate_withdrawal_year(
        h_port,
        _portfolio(),
        SimpleNamespace(),
        SimpleNamespace(),
        _config(),
        1,
        {"year": 1},
        75,
        0,
        {"eq": 0.0, "bd": 0.0, "cs": 0.0, "re": 0.0},
        False,
    )

    assert seen["requested"]["husband"] == pytest.approx(70.0)
    assert seen["requested"]["total"] == pytest.approx(70.0)
    assert seen["rmd_h"] == pytest.approx(30.0)
    assert result["rmd_h"] == pytest.approx(30.0)
    assert result["income"]["by_class"]["withdrawal"] == pytest.approx(0.0)


def test_withdrawal_year_reports_spendable_strategy_cash_not_gross_distribution(mod, monkeypatch):
    _patch_common(monkeypatch, mod)

    monkeypatch.setattr(
        mod.withdrawalEngine,
        "calculate_rmds",
        lambda *a, **k: 10.0,
    )
    monkeypatch.setattr(
        mod.incomeEngine,
        "calculate_income_breakdown",
        lambda h, w, ha, wa, rmd_h, rmd_w, year, cfg: _income(10.0, 10.0, 0.0, 10.0),
    )
    monkeypatch.setattr(
        mod.rothEngine,
        "prepare_requested_roth_flows",
        lambda **k: _requested(mod, contribution=20.0),
    )
    monkeypatch.setattr(
        mod.withdrawalEngine,
        "calculate_retirement_withdrawal",
        lambda *a, **k: {
            "total": 80.0,
            "rmd": 10.0,
            "pre_tax": 0.0,
            "post_tax": 70.0,
            "roth": 0.0,
            "hsa": 0.0,
            "uncovered": 0.0,
            "by_person": {"husband": 80.0, "wife": 0.0},
            "rmd_by_person": {"husband": 10.0, "wife": 0.0},
        },
    )
    monkeypatch.setattr(
        mod.rothEngine,
        "resolve_contribution_shortfall",
        lambda **k: {
            "funded_contributions": _funded(20.0),
            "remaining_uncovered": 0.0,
        },
    )

    def separate(**kwargs):
        contribution = kwargs["actual_contribution_total"]
        return {
            "household": 70.0 - contribution,
            "husband": 70.0 - contribution,
            "wife": 0.0,
        }

    monkeypatch.setattr(
        mod.rothEngine,
        "separate_retirement_contribution_funding",
        separate,
    )

    result = mod.simulate_withdrawal_year(
        _portfolio(),
        _portfolio(),
        SimpleNamespace(),
        SimpleNamespace(),
        _config(calculate_income_taxes=False),
        1,
        {"year": 1},
        75,
        0,
        {"eq": 0.0, "bd": 0.0, "cs": 0.0, "re": 0.0},
        False,
    )

    assert result["income"]["by_class"]["rmd"] == pytest.approx(10.0)
    assert result["income"]["by_class"]["withdrawal"] == pytest.approx(50.0)
    assert result["income"]["by_class"]["tax_funding_withdrawal"] == pytest.approx(0.0)
    assert result["income"]["total"] == pytest.approx(60.0)


def test_withdrawal_year_redirects_roth_contribution_cash_to_taxes_first(mod, monkeypatch):
    _patch_common(monkeypatch, mod)

    monkeypatch.setattr(
        mod.rothEngine,
        "prepare_requested_roth_flows",
        lambda **k: _requested(mod, contribution=20.0),
    )
    monkeypatch.setattr(
        mod.withdrawalEngine,
        "calculate_retirement_withdrawal",
        lambda *a, **k: {
            "total": 20.0,
            "rmd": 0.0,
            "pre_tax": 0.0,
            "post_tax": 20.0,
            "roth": 0.0,
            "hsa": 0.0,
            "uncovered": 0.0,
            "by_person": {"husband": 20.0, "wife": 0.0},
            "rmd_by_person": {"husband": 0.0, "wife": 0.0},
        },
    )

    resolve_calls = []

    def resolve(**kwargs):
        resolve_calls.append(kwargs["uncovered_amount"])
        total = 20.0 if len(resolve_calls) == 1 else 10.0
        return {
            "funded_contributions": _funded(total),
            "remaining_uncovered": 0.0,
        }

    monkeypatch.setattr(mod.rothEngine, "resolve_contribution_shortfall", resolve)
    monkeypatch.setattr(
        mod.rothEngine,
        "separate_retirement_contribution_funding",
        lambda **k: {
            "household": 20.0 - k["actual_contribution_total"],
            "husband": 20.0 - k["actual_contribution_total"],
            "wife": 0.0,
        },
    )
    monkeypatch.setattr(
        mod.taxEngine,
        "calculate_total_income_tax_split",
        lambda **k: (10.0, 0.0, 0.0, 10.0, 0.0),
    )

    seen_funding = {}

    def fund_tax(h, w, tax, income, cfg):
        seen_funding["tax"] = tax
        seen_funding["income"] = income
        return _zero_tax_funding()

    monkeypatch.setattr(
        mod.withdrawalEngine,
        "fund_tax_cash_shortfall",
        fund_tax,
    )

    result = mod.simulate_withdrawal_year(
        _portfolio(),
        _portfolio(),
        SimpleNamespace(),
        SimpleNamespace(),
        _config(),
        1,
        {"year": 1},
        75,
        0,
        {"eq": 0.0, "bd": 0.0, "cs": 0.0, "re": 0.0},
        False,
    )

    assert resolve_calls == pytest.approx([0.0, 10.0])
    assert result["funded_roth_contributions"]["total"] == pytest.approx(10.0)
    assert result["income"]["by_class"]["withdrawal"] == pytest.approx(10.0)
    assert seen_funding == pytest.approx({"tax": 10.0, "income": 10.0})


def test_withdrawal_year_tracks_tax_funding_separately_and_by_source(mod, monkeypatch):
    _patch_common(monkeypatch, mod)

    monkeypatch.setattr(
        mod.incomeEngine,
        "calculate_income_breakdown",
        lambda *a, **k: _income(20.0, 20.0),
    )

    tax_calls = []

    def tax_split(**kwargs):
        tax_calls.append(kwargs["ordinary_income"])
        if len(tax_calls) == 1:
            return 30.0, 0.0, 0.0, 30.0, 0.22
        return 35.0, 0.0, 0.0, 35.0, 0.22

    monkeypatch.setattr(mod.taxEngine, "calculate_total_income_tax_split", tax_split)
    monkeypatch.setattr(
        mod.rothEngine,
        "separate_retirement_contribution_funding",
        lambda **k: {"household": 0.0, "husband": 0.0, "wife": 0.0},
    )
    monkeypatch.setattr(
        mod.withdrawalEngine,
        "calculate_retirement_withdrawal",
        lambda *a, **k: {
            "total": 0.0,
            "rmd": 0.0,
            "pre_tax": 0.0,
            "post_tax": 0.0,
            "roth": 0.0,
            "hsa": 0.0,
            "uncovered": 0.0,
            "by_person": {"husband": 0.0, "wife": 0.0},
            "rmd_by_person": {"husband": 0.0, "wife": 0.0},
        },
    )
    monkeypatch.setattr(
        mod.withdrawalEngine,
        "fund_tax_cash_shortfall",
        lambda *a, **k: {
            "total": 10.0,
            "pre_tax": 6.0,
            "roth": 2.0,
            "hsa": 2.0,
            "by_person": {"husband": 10.0, "wife": 0.0},
        },
    )

    result = mod.simulate_withdrawal_year(
        _portfolio(),
        _portfolio(),
        SimpleNamespace(),
        SimpleNamespace(),
        _config(),
        1,
        {"year": 1},
        75,
        0,
        {"eq": 0.0, "bd": 0.0, "cs": 0.0, "re": 0.0},
        False,
    )

    assert tax_calls == pytest.approx([20.0, 28.0])
    assert result["income"]["by_class"]["withdrawal"] == pytest.approx(0.0)
    assert result["income"]["by_class"]["tax_funding_withdrawal"] == pytest.approx(10.0)
    assert result["pre_tax_withdrawal"] == pytest.approx(6.0)
    assert result["wd_roth"] == pytest.approx(2.0)
    assert result["wd_hsa"] == pytest.approx(2.0)
    assert result["taxable_hsa_withdrawal"] == pytest.approx(2.0)
    assert result["final_tax_delta"] == pytest.approx(5.0)
    assert result["final_tax_delta_deducted"] == pytest.approx(0.0)
    assert result["final_tax_delta_uncovered"] == pytest.approx(5.0)

def test_withdrawal_year_applies_price_return_and_rebalances_both_people(mod, monkeypatch):
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

    result = mod.simulate_withdrawal_year(
        h_port,
        w_port,
        SimpleNamespace(),
        SimpleNamespace(),
        cfg,
        1,
        {"year": 1},
        75,
        73,
        {"eq": 0.08, "bd": 0.03, "cs": 0.01, "re": 0.04},
        True,
    )

    assert len(return_calls) == 2
    assert return_calls[0][1] == pytest.approx((0.08, 0.065, 0.03, 0.01, 0.04, 0.002))
    assert rebalance_calls == [h_port, w_port]
    assert result["fund_expenses"] == pytest.approx(7.0)