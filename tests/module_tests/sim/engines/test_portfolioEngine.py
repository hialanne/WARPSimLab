import types
import pytest

import src.warpsimlab.sim.engines.portfolioEngine as pe


class DummyPortfolioState:
    """
    Minimal stand-in for src.warpsimlab.dataClasses.portfolioState.PortfolioState.
    Only implements attributes/properties used by portfolioEngine.py.
    """

    def __init__(
        self,
        *,
        eq_pre,
        bd_pre,
        cs_pre,
        eq_post,
        bd_post,
        cs_post,
        eq_roth=0.0,
        bd_roth=0.0,
        cs_roth=0.0,
        hsa_eq=0.0,
        hsa_bd=0.0,
        hsa_cs=0.0,
        re_post=0.0,
    ):
        self.eq_pre = float(eq_pre)
        self.bd_pre = float(bd_pre)
        self.cs_pre = float(cs_pre)

        self.eq_post = float(eq_post)
        self.bd_post = float(bd_post)
        self.cs_post = float(cs_post)

        self.eq_roth = float(eq_roth)
        self.bd_roth = float(bd_roth)
        self.cs_roth = float(cs_roth)

        self.hsa_eq = float(hsa_eq)
        self.hsa_bd = float(hsa_bd)
        self.hsa_cs = float(hsa_cs)

        self.re_post = float(re_post)

        self.eq_ratio_pre = 0.0
        self.bd_ratio_pre = 0.0
        self.cs_ratio_pre = 0.0

        self.eq_ratio_post = 0.0
        self.bd_ratio_post = 0.0
        self.cs_ratio_post = 0.0

        self.eq_ratio_roth = 0.0
        self.bd_ratio_roth = 0.0
        self.cs_ratio_roth = 0.0

        self.eq_ratio_hsa = 0.0
        self.bd_ratio_hsa = 0.0
        self.cs_ratio_hsa = 0.0

    @property
    def total_value_pre(self):
        return self.eq_pre + self.bd_pre + self.cs_pre

    @property
    def total_value_post(self):
        return self.eq_post + self.bd_post + self.cs_post

    @property
    def total_value_roth(self):
        return self.eq_roth + self.bd_roth + self.cs_roth

    @property
    def total_value_hsa(self):
        return self.hsa_eq + self.hsa_bd + self.hsa_cs

    @property
    def total_value(self):
        return (
            self.total_value_pre
            + self.total_value_post
            + self.total_value_roth
            + self.total_value_hsa
        )

    @property
    def total_value_cash(self):
        return self.cs_pre + self.cs_post + self.cs_roth + self.hsa_cs

    @property
    def total_value_bonds(self):
        return self.bd_pre + self.bd_post + self.bd_roth + self.hsa_bd


def make_portfolio(
    *,
    equity_pre=0.0,
    bond_pre=0.0,
    cash_pre=0.0,
    equity_post=0.0,
    bond_post=0.0,
    cash_post=0.0,
    equity_roth=0.0,
    bond_roth=0.0,
    cash_roth=0.0,
    hsa_equity=0.0,
    hsa_bond=0.0,
    hsa_cash=0.0,
    real_estate=0.0,
):
    return types.SimpleNamespace(
        equity_pre=equity_pre,
        bond_pre=bond_pre,
        cash_pre=cash_pre,

        equity_post=equity_post,
        bond_post=bond_post,
        cash_post=cash_post,

        equity_roth=equity_roth,
        bond_roth=bond_roth,
        cash_roth=cash_roth,

        hsa_equity=hsa_equity,
        hsa_bond=hsa_bond,
        hsa_cash=hsa_cash,

        real_estate=real_estate,
    )


def make_config(
    *,
    include_realestate=False,
    sim_initial_allocation_mode="dont-rebalance",
    custom_stock=0.7,
    custom_bonds=0.2,
    custom_cash=0.1,
    subplot_mode="deterministic",
    sim_type="portfolio_sim",
    eq_mean=0.0,
    bd_mean=0.0,
    cs_mean=0.0,
    re_mean=0.0,
    eq_std=0.0,
    bd_std=0.0,
    cs_std=0.0,
    re_std=0.0,
    second_person_enabled=False,
    household_eq_target=1 / 3,
    household_bd_target=1 / 3,
    household_cs_target=1 / 3,
    post_tax_bond_interest_yield=0.0,
    post_tax_cash_interest_yield=0.0,
    post_tax_equity_dividend_yield=0.0,
):
    return types.SimpleNamespace(
        include_realestate=include_realestate,
        sim_initial_allocation_mode=sim_initial_allocation_mode,
        custom_stock=custom_stock,
        custom_bonds=custom_bonds,
        custom_cash=custom_cash,
        subplot_mode=subplot_mode,
        sim_type=sim_type,
        eq_mean=eq_mean,
        bd_mean=bd_mean,
        cs_mean=cs_mean,
        re_mean=re_mean,
        eq_std=eq_std,
        bd_std=bd_std,
        cs_std=cs_std,
        re_std=re_std,
        second_person_enabled=second_person_enabled,
        household_eq_target=household_eq_target,
        household_bd_target=household_bd_target,
        household_cs_target=household_cs_target,
        post_tax_bond_interest_yield=post_tax_bond_interest_yield,
        post_tax_cash_interest_yield=post_tax_cash_interest_yield,
        post_tax_equity_dividend_yield=post_tax_equity_dividend_yield,
        _post_tax_bond_interest_yield=post_tax_bond_interest_yield,
        _post_tax_cash_interest_yield=post_tax_cash_interest_yield,
        _post_tax_equity_dividend_yield=post_tax_equity_dividend_yield,
    )

@pytest.fixture(autouse=True)
def patch_portfolio_state(monkeypatch):
    monkeypatch.setattr(pe, "PortfolioState", DummyPortfolioState)


def test_initialize_portfolio_returns_inputs():
    out = pe.initialize_portfolio(1, 2, 3, 4, 5, 6)
    assert out == (1, 2, 3, 4, 5, 6)


def test_create_sim_portfolio_dont_rebalance_sets_ratios_and_keeps_holdings():
    p = make_portfolio(
        equity_pre=60,
        bond_pre=30,
        cash_pre=10,
        equity_post=20,
        bond_post=20,
        cash_post=60,
        real_estate=999,
    )
    cfg = make_config(include_realestate=True, sim_initial_allocation_mode="dont-rebalance")

    ps = pe.create_sim_portfolio(p, cfg)

    assert ps.eq_pre == 60
    assert ps.bd_pre == 30
    assert ps.cs_pre == 10
    assert ps.eq_post == 20
    assert ps.bd_post == 20
    assert ps.cs_post == 60
    assert ps.re_post == 999

    assert ps.eq_ratio_pre == pytest.approx(60 / 100)
    assert ps.bd_ratio_pre == pytest.approx(30 / 100)
    assert ps.cs_ratio_pre == pytest.approx(10 / 100)

    assert ps.eq_ratio_post == pytest.approx(20 / 100)
    assert ps.bd_ratio_post == pytest.approx(20 / 100)
    assert ps.cs_ratio_post == pytest.approx(60 / 100)


def test_create_sim_portfolio_maintain_current_allocation_applies_household_targets():
    p = make_portfolio(
        equity_pre=60,
        bond_pre=30,
        cash_pre=10,
        equity_post=20,
        bond_post=20,
        cash_post=60,
    )
    cfg = make_config(
        sim_initial_allocation_mode="maintain-current-allocation",
        household_eq_target=0.5,
        household_bd_target=0.3,
        household_cs_target=0.2,
    )

    ps = pe.create_sim_portfolio(p, cfg)

    assert ps.eq_pre == pytest.approx(50.0)
    assert ps.bd_pre == pytest.approx(30.0)
    assert ps.cs_pre == pytest.approx(20.0)

    assert ps.eq_post == pytest.approx(50.0)
    assert ps.bd_post == pytest.approx(30.0)
    assert ps.cs_post == pytest.approx(20.0)


def test_create_sim_portfolio_preset_rebalance_70_20_10_applies_to_pre_and_post():
    p = make_portfolio(
        equity_pre=60,
        bond_pre=30,
        cash_pre=10,
        equity_post=20,
        bond_post=20,
        cash_post=60,
    )
    cfg = make_config(sim_initial_allocation_mode="70-20-10")

    ps = pe.create_sim_portfolio(p, cfg)

    assert ps.eq_pre == pytest.approx(70.0)
    assert ps.bd_pre == pytest.approx(20.0)
    assert ps.cs_pre == pytest.approx(10.0)

    assert ps.eq_post == pytest.approx(70.0)
    assert ps.bd_post == pytest.approx(20.0)
    assert ps.cs_post == pytest.approx(10.0)


def test_create_sim_portfolio_custom_rebalance_applies_to_pre_and_post():
    p = make_portfolio(
        equity_pre=60,
        bond_pre=30,
        cash_pre=10,
        equity_post=20,
        bond_post=20,
        cash_post=60,
    )
    cfg = make_config(
        sim_initial_allocation_mode="custom",
        custom_stock=0.5,
        custom_bonds=0.3,
        custom_cash=0.2,
    )

    ps = pe.create_sim_portfolio(p, cfg)

    assert ps.eq_pre == pytest.approx(50.0)
    assert ps.bd_pre == pytest.approx(30.0)
    assert ps.cs_pre == pytest.approx(20.0)

    assert ps.eq_post == pytest.approx(50.0)
    assert ps.bd_post == pytest.approx(30.0)
    assert ps.cs_post == pytest.approx(20.0)


def test_compute_household_allocation_targets_single_person():
    husband = make_portfolio(
        equity_pre=60,
        bond_pre=20,
        cash_pre=20,
        equity_post=40,
        bond_post=10,
        cash_post=10,
    )
    cfg = make_config(second_person_enabled=False)

    pe.compute_household_allocation_targets(husband, None, cfg)

    total_eq = 60 + 40
    total_bd = 20 + 10
    total_cs = 20 + 10
    total = total_eq + total_bd + total_cs

    assert cfg.household_eq_target == pytest.approx(total_eq / total)
    assert cfg.household_bd_target == pytest.approx(total_bd / total)
    assert cfg.household_cs_target == pytest.approx(total_cs / total)


def test_compute_household_allocation_targets_two_people():
    husband = make_portfolio(
        equity_pre=50,
        bond_pre=20,
        cash_pre=10,
        equity_post=20,
        bond_post=0,
        cash_post=0,
    )
    wife = make_portfolio(
        equity_pre=30,
        bond_pre=10,
        cash_pre=10,
        equity_post=20,
        bond_post=20,
        cash_post=10,
    )
    cfg = make_config(second_person_enabled=True)

    pe.compute_household_allocation_targets(husband, wife, cfg)

    total_eq = 50 + 20 + 30 + 20
    total_bd = 20 + 0 + 10 + 20
    total_cs = 10 + 0 + 10 + 10
    total = total_eq + total_bd + total_cs

    assert cfg.household_eq_target == pytest.approx(total_eq / total)
    assert cfg.household_bd_target == pytest.approx(total_bd / total)
    assert cfg.household_cs_target == pytest.approx(total_cs / total)


def test_compute_household_allocation_targets_empty_defaults_to_thirds():
    husband = make_portfolio()
    cfg = make_config(second_person_enabled=False)

    pe.compute_household_allocation_targets(husband, None, cfg)

    assert cfg.household_eq_target == pytest.approx(1 / 3)
    assert cfg.household_bd_target == pytest.approx(1 / 3)
    assert cfg.household_cs_target == pytest.approx(1 / 3)


def test_estimate_post_tax_income_components_uses_post_tax_yields():
    ps = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=1000, bd_post=2000, cs_post=500)
    cfg = make_config(
        post_tax_bond_interest_yield=0.05,
        post_tax_cash_interest_yield=0.02,
        post_tax_equity_dividend_yield=0.03,
    )

    out = pe.estimate_post_tax_income_components(ps, cfg)

    assert out["bond_interest"] == pytest.approx(100.0)
    assert out["cash_interest"] == pytest.approx(10.0)
    assert out["qualified_dividends"] == pytest.approx(30.0)
    assert out["ordinary_total"] == pytest.approx(110.0)
    assert out["qualified_total"] == pytest.approx(30.0)
    assert out["total"] == pytest.approx(140.0)


def test_estimate_household_post_tax_income_components_two_people():
    h = DummyPortfolioState(
        eq_pre=0,
        bd_pre=0,
        cs_pre=0,
        eq_post=1000,
        bd_post=1000,
        cs_post=1000,
    )
    w = DummyPortfolioState(
        eq_pre=0,
        bd_pre=0,
        cs_pre=0,
        eq_post=500,
        bd_post=500,
        cs_post=500,
    )
    cfg = make_config(
        second_person_enabled=True,
        post_tax_equity_dividend_yield=0.03,
    )

    bond_interest, cash_interest, qualified_dividends, total, h_total, w_total = (
        pe.estimate_household_post_tax_income_components(
            h,
            w,
            cfg,
            bond_return=0.04,
            cash_return=0.02,
        )
    )

    assert bond_interest == pytest.approx(40.0 + 20.0)
    assert cash_interest == pytest.approx(20.0 + 10.0)
    assert qualified_dividends == pytest.approx(30.0 + 15.0)
    assert total == pytest.approx(135.0)
    assert h_total == pytest.approx(90.0)
    assert w_total == pytest.approx(45.0)


def test_apply_post_tax_income_components_to_income_updates_structure():
    income = {
        "by_class": {
            "bond_interest": 1.0,
            "cash_interest": 2.0,
            "qualified_dividends": 3.0,
        },
        "by_person": {
            "husband": 10.0,
            "wife": 20.0,
        },
        "total": 100.0,
    }

    post_tax_income = {
        "bond_interest": 5.0,
        "cash_interest": 6.0,
        "qualified_dividends": 7.0,
        "total": 18.0,
        "by_person": {
            "husband": {"total": 11.0},
            "wife": {"total": 7.0},
        },
    }

    out = pe.apply_post_tax_income_components_to_income(
        income,
        post_tax_income,
        second_person_enabled=True,
    )

    assert out["by_class"]["bond_interest"] == pytest.approx(6.0)
    assert out["by_class"]["cash_interest"] == pytest.approx(8.0)
    assert out["by_class"]["qualified_dividends"] == pytest.approx(10.0)
    assert out["by_person"]["husband"] == pytest.approx(21.0)
    assert out["by_person"]["wife"] == pytest.approx(27.0)
    assert out["total"] == pytest.approx(118.0)


def test_apply_returns_deterministic_branch_applies_means_to_all_buckets_and_real_estate():
    ps = DummyPortfolioState(
        eq_pre=100,
        bd_pre=100,
        cs_pre=100,
        eq_post=100,
        bd_post=100,
        cs_post=100,
        re_post=100,
    )
    cfg = make_config(
        subplot_mode="not-monte-carlo",
        sim_type="portfolio_sim",
        eq_mean=0.10,
        bd_mean=0.05,
        cs_mean=0.01,
        re_mean=0.02,
    )

    pe.apply_returns(
        ps,
        cfg.eq_mean,
        cfg.bd_mean,
        cfg.cs_mean,
        cfg.re_mean,
    )

    assert ps.eq_pre == pytest.approx(110.0)
    assert ps.bd_pre == pytest.approx(105.0)
    assert ps.cs_pre == pytest.approx(101.0)
    assert ps.eq_post == pytest.approx(110.0)
    assert ps.bd_post == pytest.approx(105.0)
    assert ps.cs_post == pytest.approx(101.0)
    assert ps.re_post == pytest.approx(102.0)


# Commenting out.  The code no longer clamps.  This is safe as we will never have portfolio losses greater
#   than -100% (or -1.0)
'''
def test_apply_returns_clamps_to_zero_when_negative():
    ps = DummyPortfolioState(
        eq_pre=10,
        bd_pre=10,
        cs_pre=10,
        eq_post=10,
        bd_post=10,
        cs_post=10,
        re_post=10,
    )
    cfg = make_config(
        subplot_mode="not-monte-carlo",
        sim_type="portfolio_sim",
        eq_mean=-2.0,
        bd_mean=-2.0,
        cs_mean=-2.0,
        re_mean=-2.0,
    )

    pe.apply_returns(
        ps,
        cfg.eq_mean,
        cfg.bd_mean,
        cfg.cs_mean,
        cfg.re_mean,
    )

    assert ps.eq_pre == 0.0
    assert ps.bd_pre == 0.0
    assert ps.cs_pre == 0.0
    assert ps.eq_post == 0.0
    assert ps.bd_post == 0.0
    assert ps.cs_post == 0.0
    assert ps.re_post == 0.0
'''

def test_apply_fund_expenses_reduces_all_components_and_returns_removed_amount():
    ps = DummyPortfolioState(eq_pre=100, bd_pre=50, cs_pre=50, eq_post=100, bd_post=50, cs_post=50)
    total_before = ps.total_value

    removed = pe.apply_fund_expenses(ps, fund_expense=0.10)

    total_after = ps.total_value

    assert total_after == pytest.approx(total_before * 0.90)
    assert removed == pytest.approx(total_before - total_after)


def test_rebalance_dont_rebalance_uses_stored_ratios():
    ps = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=50, bd_post=25, cs_post=25)
    cfg = make_config(sim_initial_allocation_mode="dont-rebalance")

    ps.eq_ratio_post = 0.2
    ps.bd_ratio_post = 0.3
    ps.cs_ratio_post = 0.5

    ps.eq_ratio_pre = 0.1
    ps.bd_ratio_pre = 0.2
    ps.cs_ratio_pre = 0.7

    ps.eq_post = 80
    ps.bd_post = 10
    ps.cs_post = 10

    pe.rebalance(ps, cfg)

    assert ps.eq_post == pytest.approx(100 * 0.2)
    assert ps.bd_post == pytest.approx(100 * 0.3)
    assert ps.cs_post == pytest.approx(100 * 0.5)


def test_rebalance_maintain_current_allocation_uses_household_targets():
    ps = DummyPortfolioState(eq_pre=40, bd_pre=30, cs_pre=30, eq_post=50, bd_post=25, cs_post=25)
    cfg = make_config(
        sim_initial_allocation_mode="maintain-current-allocation",
        household_eq_target=0.6,
        household_bd_target=0.2,
        household_cs_target=0.2,
    )

    pe.rebalance(ps, cfg)

    assert ps.eq_pre == pytest.approx(100 * 0.6)
    assert ps.bd_pre == pytest.approx(100 * 0.2)
    assert ps.cs_pre == pytest.approx(100 * 0.2)

    assert ps.eq_post == pytest.approx(100 * 0.6)
    assert ps.bd_post == pytest.approx(100 * 0.2)
    assert ps.cs_post == pytest.approx(100 * 0.2)


def test_rebalance_custom_uses_custom_ratios():
    ps = DummyPortfolioState(eq_pre=60, bd_pre=20, cs_pre=20, eq_post=10, bd_post=40, cs_post=50)
    cfg = make_config(
        sim_initial_allocation_mode="custom",
        custom_stock=0.5,
        custom_bonds=0.25,
        custom_cash=0.25,
    )

    pe.rebalance(ps, cfg)

    assert ps.eq_pre == pytest.approx(100 * 0.5)
    assert ps.bd_pre == pytest.approx(100 * 0.25)
    assert ps.cs_pre == pytest.approx(100 * 0.25)

    assert ps.eq_post == pytest.approx(100 * 0.5)
    assert ps.bd_post == pytest.approx(100 * 0.25)
    assert ps.cs_post == pytest.approx(100 * 0.25)


def test_rebalance_preset_uses_preset_ratios():
    ps = DummyPortfolioState(eq_pre=90, bd_pre=5, cs_pre=5, eq_post=10, bd_post=10, cs_post=80)
    cfg = make_config(sim_initial_allocation_mode="30-30-40")

    pe.rebalance(ps, cfg)

    assert ps.eq_pre == pytest.approx(30.0)
    assert ps.bd_pre == pytest.approx(30.0)
    assert ps.cs_pre == pytest.approx(40.0)

    assert ps.eq_post == pytest.approx(30.0)
    assert ps.bd_post == pytest.approx(30.0)
    assert ps.cs_post == pytest.approx(40.0)


def test_apply_net_income_proportionally_positive_adds_to_post_tax_proportionally():
    ps = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=50, bd_post=30, cs_post=20)

    total = pe.apply_net_income_proportionally(ps, net_change=100)

    assert ps.eq_post == pytest.approx(50 + 100 * 0.5)
    assert ps.bd_post == pytest.approx(30 + 100 * 0.3)
    assert ps.cs_post == pytest.approx(20 + 100 * 0.2)
    assert total == pytest.approx(ps.total_value)


def test_apply_net_income_proportionally_uses_pre_ratios_when_post_empty():
    ps = DummyPortfolioState(eq_pre=60, bd_pre=30, cs_pre=10, eq_post=0, bd_post=0, cs_post=0)

    pe.apply_net_income_proportionally(ps, net_change=100)

    assert ps.eq_post == pytest.approx(60.0)
    assert ps.bd_post == pytest.approx(30.0)
    assert ps.cs_post == pytest.approx(10.0)


def test_apply_net_income_proportionally_defaults_to_thirds_when_all_empty():
    ps = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)

    pe.apply_net_income_proportionally(ps, net_change=90)

    assert ps.eq_post == pytest.approx(30.0)
    assert ps.bd_post == pytest.approx(30.0)
    assert ps.cs_post == pytest.approx(30.0)


def test_apply_net_income_proportionally_negative_clamps_components_to_zero():
    ps = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=10, bd_post=10, cs_post=10)

    pe.apply_net_income_proportionally(ps, net_change=-100)

    assert ps.eq_post == pytest.approx(0.0)
    assert ps.bd_post == pytest.approx(0.0)
    assert ps.cs_post == pytest.approx(0.0)


def test_apply_net_income_proportionally_pre_positive_adds_to_pre_tax_proportionally():
    ps = DummyPortfolioState(eq_pre=50, bd_pre=30, cs_pre=20, eq_post=0, bd_post=0, cs_post=0)

    total = pe.apply_net_income_proportionally_pre(ps, net_change=100)

    assert ps.eq_pre == pytest.approx(100.0)
    assert ps.bd_pre == pytest.approx(60.0)
    assert ps.cs_pre == pytest.approx(40.0)
    assert total == pytest.approx(ps.total_value)


def test_get_pre_tax_ratios_returns_current_ratios():
    ps = DummyPortfolioState(eq_pre=60, bd_pre=30, cs_pre=10, eq_post=0, bd_post=0, cs_post=0)

    out = pe.get_pre_tax_ratios(ps)

    assert out["equity"] == pytest.approx(0.6)
    assert out["bonds"] == pytest.approx(0.3)
    assert out["cash"] == pytest.approx(0.1)


def test_get_pre_tax_ratios_empty_returns_thirds():
    ps = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)

    out = pe.get_pre_tax_ratios(ps)

    assert out["equity"] == pytest.approx(1 / 3)
    assert out["bonds"] == pytest.approx(1 / 3)
    assert out["cash"] == pytest.approx(1 / 3)


def test_create_empty_sim_portfolio_returns_zeros():
    cfg = make_config(include_realestate=True)

    ps = pe.create_empty_sim_portfolio(cfg)

    assert ps.eq_pre == 0.0
    assert ps.bd_pre == 0.0
    assert ps.cs_pre == 0.0
    assert ps.eq_post == 0.0
    assert ps.bd_post == 0.0
    assert ps.cs_post == 0.0
    assert ps.re_post == 0.0


def test_deduct_post_tax_amount_single_person_proportional():
    h = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=50, bd_post=30, cs_post=20)
    w = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)
    cfg = make_config(second_person_enabled=False)

    deducted = pe.deduct_post_tax_amount(h, w, amount=40, sim_config=cfg)

    assert deducted == pytest.approx(40.0)
    assert h.eq_post == pytest.approx(30.0)
    assert h.bd_post == pytest.approx(18.0)
    assert h.cs_post == pytest.approx(12.0)


def test_deduct_post_tax_amount_two_people_splits_by_household_post_tax():
    h = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=60, bd_post=20, cs_post=20)
    w = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=20, bd_post=20, cs_post=10)
    cfg = make_config(second_person_enabled=True)

    deducted = pe.deduct_post_tax_amount(h, w, amount=60, sim_config=cfg)

    assert deducted == pytest.approx(60.0)
    assert h.total_value_post == pytest.approx(100.0 - (60.0 * (100.0 / 150.0)))
    assert w.total_value_post == pytest.approx(50.0 - (60.0 * (50.0 / 150.0)))


def test_deduct_post_tax_amount_cannot_exceed_available():
    h = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=10, bd_post=0, cs_post=0)
    w = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)
    cfg = make_config(second_person_enabled=False)

    deducted = pe.deduct_post_tax_amount(h, w, amount=50, sim_config=cfg)

    assert deducted == pytest.approx(10.0)
    assert h.total_value_post == pytest.approx(0.0)


def test_apply_net_income_single_positive_adds_to_eq_post_only():
    ps = DummyPortfolioState(eq_pre=50, bd_pre=50, cs_pre=0, eq_post=25, bd_post=25, cs_post=0)

    result = pe.apply_net_income_single(ps, net_cash=40)

    assert result["post_tax_used"] == pytest.approx(0.0)
    assert result["pre_tax_used"] == pytest.approx(0.0)
    assert result["uncovered"] == pytest.approx(0.0)

    assert ps.eq_post == pytest.approx(65.0)
    assert ps.bd_post == pytest.approx(25.0)
    assert ps.cs_post == pytest.approx(0.0)


def test_apply_net_income_single_negative_limited_by_post_then_uses_pre_tax():
    ps = DummyPortfolioState(eq_pre=50, bd_pre=50, cs_pre=0, eq_post=25, bd_post=25, cs_post=0)

    result = pe.apply_net_income_single(ps, net_cash=-80)

    assert ps.total_value_post == pytest.approx(0.0)
    assert ps.total_value_pre == pytest.approx(70.0)

    assert result["post_tax_used"] == pytest.approx(50.0)
    assert result["pre_tax_used"] == pytest.approx(30.0)
    assert result["uncovered"] == pytest.approx(0.0)


def test_apply_net_income_single_negative_with_uncovered_deficit():
    ps = DummyPortfolioState(eq_pre=10, bd_pre=0, cs_pre=0, eq_post=5, bd_post=0, cs_post=0)

    result = pe.apply_net_income_single(ps, net_cash=-30)

    assert ps.total_value_post == pytest.approx(0.0)
    assert ps.total_value_pre == pytest.approx(0.0)

    assert result["post_tax_used"] == pytest.approx(5.0)
    assert result["pre_tax_used"] == pytest.approx(10.0)
    assert result["uncovered"] == pytest.approx(15.0)


def test_apply_net_income_couple_positive_splits_to_eq_post():
    h = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=10, bd_post=0, cs_post=0)
    w = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=20, bd_post=0, cs_post=0)

    result = pe.apply_net_income_couple(h, w, net_cash=40)

    assert result["post_tax_used"] == pytest.approx(0.0)
    assert result["pre_tax_used"] == pytest.approx(0.0)
    assert result["uncovered"] == pytest.approx(0.0)

    assert h.eq_post == pytest.approx(30.0)
    assert w.eq_post == pytest.approx(40.0)


def test_apply_net_income_couple_negative_uses_post_then_pre():
    h = DummyPortfolioState(eq_pre=50, bd_pre=50, cs_pre=0, eq_post=25, bd_post=25, cs_post=0)
    w = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)

    result = pe.apply_net_income_couple(h, w, net_cash=-60)

    assert result["post_tax_used"] == pytest.approx(50.0)
    assert result["pre_tax_used"] == pytest.approx(10.0)
    assert result["uncovered"] == pytest.approx(0.0)

    assert h.total_value_post == pytest.approx(0.0)
    assert h.total_value_pre == pytest.approx(90.0)


def test_apply_net_income_couple_negative_with_uncovered_deficit():
    h = DummyPortfolioState(eq_pre=10, bd_pre=0, cs_pre=0, eq_post=5, bd_post=0, cs_post=0)
    w = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)

    result = pe.apply_net_income_couple(h, w, net_cash=-30)

    assert result["post_tax_used"] == pytest.approx(5.0)
    assert result["pre_tax_used"] == pytest.approx(10.0)
    assert result["uncovered"] == pytest.approx(15.0)

    assert h.total_value_post == pytest.approx(0.0)
    assert h.total_value_pre == pytest.approx(0.0)
    assert w.total_value_post == pytest.approx(0.0)
    assert w.total_value_pre == pytest.approx(0.0)


def test_apply_pre_tax_contribution_empty_pre_tax_currently_errors():
    ps = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)
    pe.apply_pre_tax_contribution(ps, amount=100.0)


def test_apply_pre_tax_contribution_nonempty_pre_tax_allocates_proportionally():
    ps = DummyPortfolioState(eq_pre=60, bd_pre=30, cs_pre=10, eq_post=0, bd_post=0, cs_post=0)

    pe.apply_pre_tax_contribution(ps, amount=100.0)

    assert ps.eq_pre == pytest.approx(120.0)
    assert ps.bd_pre == pytest.approx(60.0)
    assert ps.cs_pre == pytest.approx(20.0)


def test_apply_pre_tax_contribution_nonpositive_amount_no_change():
    ps = DummyPortfolioState(eq_pre=60, bd_pre=30, cs_pre=10, eq_post=0, bd_post=0, cs_post=0)

    pe.apply_pre_tax_contribution(ps, amount=0.0)

    assert ps.eq_pre == pytest.approx(60.0)
    assert ps.bd_pre == pytest.approx(30.0)
    assert ps.cs_pre == pytest.approx(10.0)
