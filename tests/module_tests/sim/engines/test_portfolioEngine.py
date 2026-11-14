
from src.warpsimlab.sim.simulationObject import RunContext
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
    sim_initial_allocation_mode="original-allocation",
    custom_stock=0.7,
    custom_bonds=0.2,
    custom_cash=0.1,
    results_mode="deterministic",
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
    post_tax_bond_interest_yield=0.0,
    post_tax_cash_interest_yield=0.0,
    post_tax_equity_dividend_yield=0.0,
):
    config = types.SimpleNamespace(
        include_realestate=include_realestate,
        sim_initial_allocation_mode=sim_initial_allocation_mode,
        custom_stock=custom_stock,
        custom_bonds=custom_bonds,
        custom_cash=custom_cash,
        results_mode=results_mode,
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
        post_tax_bond_interest_yield=post_tax_bond_interest_yield,
        post_tax_cash_interest_yield=post_tax_cash_interest_yield,
        post_tax_equity_dividend_yield=post_tax_equity_dividend_yield,
    )
    run_context = RunContext(post_tax_bond_interest_yield_normalized=post_tax_bond_interest_yield,
        post_tax_cash_interest_yield_normalized=post_tax_cash_interest_yield,
        post_tax_equity_dividend_yield_normalized=post_tax_equity_dividend_yield)
    return config, run_context

@pytest.fixture(autouse=True)
def patch_portfolio_state(monkeypatch):
    monkeypatch.setattr(pe, "PortfolioState", DummyPortfolioState)


def test_initialize_portfolio_returns_inputs():
    out = pe.initialize_portfolio(1, 2, 3, 4, 5, 6)
    assert out == (1, 2, 3, 4, 5, 6)


def test_create_sim_portfolio_original_allocation_records_ratios_and_keeps_holdings():
    run_context = RunContext()
    p = make_portfolio(
        equity_pre=60,
        bond_pre=30,
        cash_pre=10,
        equity_post=20,
        bond_post=20,
        cash_post=60,
        real_estate=999,
    )
    cfg, run_context = make_config(include_realestate=True, sim_initial_allocation_mode="original-allocation")

    ps = pe.create_sim_portfolio(p, cfg, run_context=run_context)

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


@pytest.mark.parametrize("mode,ratios", [
    ("original-allocation", None), ("30-30-40", (0.3, 0.3, 0.4)),
    ("50-30-20", (0.5, 0.3, 0.2)), ("70-20-10", (0.7, 0.2, 0.1)),
    ("custom", (0.7, 0.2, 0.1)),
])
def test_initialization_and_rebalance_preserve_each_category_total(mode, ratios):
    p = make_portfolio(equity_pre=60, bond_pre=30, cash_pre=10,
        equity_post=40, bond_post=40, cash_post=120, equity_roth=90, bond_roth=150,
        cash_roth=60, hsa_equity=40, hsa_bond=80, hsa_cash=280, real_estate=999)
    cfg, run = make_config(include_realestate=True, sim_initial_allocation_mode=mode)
    ps = pe.create_sim_portfolio(p, cfg, run_context=run)
    buckets = [("pre", ("eq_pre", "bd_pre", "cs_pre"), (60, 30, 10)),
        ("post", ("eq_post", "bd_post", "cs_post"), (40, 40, 120)),
        ("roth", ("eq_roth", "bd_roth", "cs_roth"), (90, 150, 60)),
        ("hsa", ("hsa_eq", "hsa_bd", "hsa_cs"), (40, 80, 280))]
    for bucket, attrs, original in buckets:
        total = sum(original)
        for asset, attr, amount in zip(("eq", "bd", "cs"), attrs, original):
            expected = amount
            if ratios is not None:
                expected = total * ratios[("eq", "bd", "cs").index(asset)]

            assert getattr(ps, attr) == pytest.approx(expected)
            if ratios is None:
                assert getattr(ps, f"{asset}_ratio_{bucket}") == pytest.approx(amount / total)

        # Unequal returns create drift within every category.
        for attr, growth in zip(attrs, (1.1, 1.02, 1.0)):
            setattr(ps, attr, getattr(ps, attr) * growth)

    totals = []
    for _, attrs, _ in buckets:
        totals.append(sum(getattr(ps, attr) for attr in attrs))
    pe.rebalance(ps, cfg, run_context=run)
    for (_, attrs, original), total in zip(buckets, totals):
        for index, attr in enumerate(attrs):
            target = original[index] / sum(original)
            if ratios is not None:
                target = ratios[index]

            assert getattr(ps, attr) == pytest.approx(total * target)
        assert sum(getattr(ps, attr) for attr in attrs) == pytest.approx(total)
    assert ps.re_post == 999


def test_create_sim_portfolio_preset_rebalance_70_20_10_applies_to_pre_and_post():
    run_context = RunContext()
    p = make_portfolio(
        equity_pre=60,
        bond_pre=30,
        cash_pre=10,
        equity_post=20,
        bond_post=20,
        cash_post=60,
    )
    cfg, run_context = make_config(sim_initial_allocation_mode="70-20-10")

    ps = pe.create_sim_portfolio(p, cfg, run_context=run_context)

    assert ps.eq_pre == pytest.approx(70.0)
    assert ps.bd_pre == pytest.approx(20.0)
    assert ps.cs_pre == pytest.approx(10.0)

    assert ps.eq_post == pytest.approx(70.0)
    assert ps.bd_post == pytest.approx(20.0)
    assert ps.cs_post == pytest.approx(10.0)


def test_create_sim_portfolio_custom_rebalance_applies_to_pre_and_post():
    run_context = RunContext()
    p = make_portfolio(
        equity_pre=60,
        bond_pre=30,
        cash_pre=10,
        equity_post=20,
        bond_post=20,
        cash_post=60,
    )
    cfg, run_context = make_config(sim_initial_allocation_mode='custom', custom_stock=0.5, custom_bonds=0.3, custom_cash=0.2)

    ps = pe.create_sim_portfolio(p, cfg, run_context=run_context)

    assert ps.eq_pre == pytest.approx(50.0)
    assert ps.bd_pre == pytest.approx(30.0)
    assert ps.cs_pre == pytest.approx(20.0)

    assert ps.eq_post == pytest.approx(50.0)
    assert ps.bd_post == pytest.approx(30.0)
    assert ps.cs_post == pytest.approx(20.0)


def test_original_allocation_empty_categories_have_no_invented_targets():
    cfg, run = make_config(sim_initial_allocation_mode="original-allocation")
    ps = pe.create_sim_portfolio(make_portfolio(), cfg, run_context=run)
    assert ps.total_value == 0
    for bucket in ("pre", "post", "roth", "hsa"):
        for asset in ("eq", "bd", "cs"):
            assert getattr(ps, f"{asset}_ratio_{bucket}") == 0


def test_original_allocation_empty_starting_category_keeps_new_assets():
    cfg, run = make_config(sim_initial_allocation_mode="original-allocation")
    ps = pe.create_sim_portfolio(make_portfolio(equity_pre=100), cfg, run_context=run)
    ps.eq_post, ps.bd_post, ps.cs_post = 20, 30, 50
    ps.eq_roth, ps.bd_roth, ps.cs_roth = 10, 20, 30
    ps.hsa_eq, ps.hsa_bd, ps.hsa_cs = 5, 10, 15
    pe.rebalance(ps, cfg, run_context=run)
    assert (ps.eq_pre, ps.bd_pre, ps.cs_pre) == (100, 0, 0)
    assert (ps.eq_post, ps.bd_post, ps.cs_post) == (20, 30, 50)
    assert (ps.eq_roth, ps.bd_roth, ps.cs_roth) == (10, 20, 30)
    assert (ps.hsa_eq, ps.hsa_bd, ps.hsa_cs) == (5, 10, 15)


def test_survivor_merge_uses_deceased_current_allocation_when_original_category_empty():
    cfg, run = make_config(sim_initial_allocation_mode="original-allocation")
    survivor = pe.create_sim_portfolio(make_portfolio(equity_pre=80, bond_pre=20), cfg, run_context=run)
    deceased = pe.create_sim_portfolio(make_portfolio(), cfg, run_context=run)
    deceased.eq_pre, deceased.bd_pre, deceased.cs_pre = 60, 100, 40
    pe.transfer_portfolio_to_survivor(deceased, survivor)
    survivor.eq_pre, survivor.bd_pre, survivor.cs_pre = 200, 50, 50
    pe.rebalance(survivor, cfg, run_context=run)
    assert (survivor.eq_pre, survivor.bd_pre, survivor.cs_pre) == pytest.approx((140, 120, 40))
    assert deceased.total_value == 0


def test_estimate_post_tax_income_components_uses_post_tax_yields():
    run_context = RunContext()
    ps = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=1000, bd_post=2000, cs_post=500)
    cfg, run_context = make_config(post_tax_bond_interest_yield=0.05, post_tax_cash_interest_yield=0.02, post_tax_equity_dividend_yield=0.03)

    out = pe.estimate_post_tax_income_components(ps, cfg, run_context=run_context)

    assert out["bond_interest"] == pytest.approx(100.0)
    assert out["cash_interest"] == pytest.approx(10.0)
    assert out["qualified_equity_distributions"] == pytest.approx(30.0)
    assert out["ordinary_total"] == pytest.approx(110.0)
    assert out["qualified_total"] == pytest.approx(30.0)
    assert out["total"] == pytest.approx(140.0)


def test_estimate_household_post_tax_income_components_two_people():
    run_context = RunContext()
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
    cfg, run_context = make_config(second_person_enabled=True, post_tax_equity_dividend_yield=0.03)

    bond_interest, cash_interest, qualified_equity_distributions, total, h_total, w_total = (
        pe.estimate_household_post_tax_income_components(h, w, cfg, bond_return=0.04, cash_return=0.02, run_context=run_context)
    )

    assert bond_interest == pytest.approx(40.0 + 20.0)
    assert cash_interest == pytest.approx(20.0 + 10.0)
    assert qualified_equity_distributions == pytest.approx(30.0 + 15.0)
    assert total == pytest.approx(135.0)
    assert h_total == pytest.approx(90.0)
    assert w_total == pytest.approx(45.0)


def test_apply_post_tax_income_components_to_income_updates_structure():
    income = {
        "by_class": {
            "bond_interest": 1.0,
            "cash_interest": 2.0,
            "qualified_equity_distributions": 3.0,
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
        "qualified_equity_distributions": 7.0,
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
    assert out["by_class"]["qualified_equity_distributions"] == pytest.approx(10.0)
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
    cfg, run_context = make_config(
        results_mode="not-monte-carlo",
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
    cfg, run_context = make_config(
        results_mode="not-monte-carlo",
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


def test_rebalance_original_allocation_uses_stored_ratios():
    run_context = RunContext()
    ps = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=50, bd_post=25, cs_post=25)
    cfg, run_context = make_config(sim_initial_allocation_mode="original-allocation")

    ps.eq_ratio_post = 0.2
    ps.bd_ratio_post = 0.3
    ps.cs_ratio_post = 0.5

    ps.eq_ratio_pre = 0.1
    ps.bd_ratio_pre = 0.2
    ps.cs_ratio_pre = 0.7

    ps.eq_post = 80
    ps.bd_post = 10
    ps.cs_post = 10

    pe.rebalance(ps, cfg, run_context=run_context)

    assert ps.eq_post == pytest.approx(100 * 0.2)
    assert ps.bd_post == pytest.approx(100 * 0.3)
    assert ps.cs_post == pytest.approx(100 * 0.5)


def test_original_allocation_keeps_spouse_targets_independent():
    cfg, run = make_config(sim_initial_allocation_mode="original-allocation")
    husband = pe.create_sim_portfolio(make_portfolio(equity_pre=80, bond_pre=20), cfg, run_context=run)
    wife = pe.create_sim_portfolio(make_portfolio(equity_pre=100, bond_pre=100), cfg, run_context=run)
    husband.eq_pre, husband.bd_pre = 90, 10
    wife.eq_pre, wife.bd_pre = 150, 50
    pe.rebalance(husband, cfg, run_context=run)
    pe.rebalance(wife, cfg, run_context=run)
    assert (husband.eq_pre, husband.bd_pre, husband.cs_pre) == pytest.approx((80, 20, 0))
    assert (wife.eq_pre, wife.bd_pre, wife.cs_pre) == pytest.approx((100, 100, 0))


def test_survivor_targets_use_transfer_time_category_balances_and_empty_target_fallback():
    cfg, run = make_config(sim_initial_allocation_mode="original-allocation", include_realestate=True)
    survivor = pe.create_sim_portfolio(make_portfolio(equity_pre=80_000, bond_pre=20_000,
        cash_post=50_000, equity_roth=20_000, real_estate=1_000), cfg, run_context=run)
    deceased = pe.create_sim_portfolio(make_portfolio(equity_pre=50_000, bond_pre=50_000,
        equity_post=150_000, bond_roth=40_000, hsa_cash=60_000, real_estate=2_000), cfg, run_context=run)
    # The deceased category grows to 200k before transfer; initial balances cannot be the weights.
    deceased.eq_pre, deceased.bd_pre = 150_000, 50_000
    # The survivor's initially empty HSA acquires assets without an original target.
    survivor.hsa_eq, survivor.hsa_bd = 30_000, 10_000
    pe.transfer_portfolio_to_survivor(deceased, survivor)
    assert (survivor.eq_pre, survivor.bd_pre, survivor.cs_pre) == (230_000, 70_000, 0)
    pe.rebalance(survivor, cfg, run_context=run)
    assert (survivor.eq_pre, survivor.bd_pre, survivor.cs_pre) == pytest.approx((180_000, 120_000, 0))
    assert (survivor.eq_post, survivor.bd_post, survivor.cs_post) == pytest.approx((150_000, 0, 50_000))
    assert (survivor.eq_roth, survivor.bd_roth, survivor.cs_roth) == pytest.approx((20_000, 40_000, 0))
    assert (survivor.hsa_eq, survivor.hsa_bd, survivor.hsa_cs) == pytest.approx((30_000, 10_000, 60_000))
    assert survivor.re_post == 3_000
    assert deceased.total_value == 0
    assert deceased.re_post == 0


def test_rebalance_custom_uses_custom_ratios():
    run_context = RunContext()
    ps = DummyPortfolioState(eq_pre=60, bd_pre=20, cs_pre=20, eq_post=10, bd_post=40, cs_post=50)
    cfg, run_context = make_config(sim_initial_allocation_mode='custom', custom_stock=0.5, custom_bonds=0.25, custom_cash=0.25)

    pe.rebalance(ps, cfg, run_context=run_context)

    assert ps.eq_pre == pytest.approx(100 * 0.5)
    assert ps.bd_pre == pytest.approx(100 * 0.25)
    assert ps.cs_pre == pytest.approx(100 * 0.25)

    assert ps.eq_post == pytest.approx(100 * 0.5)
    assert ps.bd_post == pytest.approx(100 * 0.25)
    assert ps.cs_post == pytest.approx(100 * 0.25)


def test_rebalance_preset_uses_preset_ratios():
    run_context = RunContext()
    ps = DummyPortfolioState(eq_pre=90, bd_pre=5, cs_pre=5, eq_post=10, bd_post=10, cs_post=80)
    cfg, run_context = make_config(sim_initial_allocation_mode="30-30-40")

    pe.rebalance(ps, cfg, run_context=run_context)

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
    cfg, run_context = make_config(include_realestate=True)

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
    cfg, run_context = make_config(second_person_enabled=False)

    deducted = pe.deduct_post_tax_amount(h, w, amount=40, sim_config=cfg)

    assert deducted == pytest.approx(40.0)
    assert h.eq_post == pytest.approx(30.0)
    assert h.bd_post == pytest.approx(18.0)
    assert h.cs_post == pytest.approx(12.0)


def test_deduct_post_tax_amount_two_people_splits_by_household_post_tax():
    h = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=60, bd_post=20, cs_post=20)
    w = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=20, bd_post=20, cs_post=10)
    cfg, run_context = make_config(second_person_enabled=True)

    deducted = pe.deduct_post_tax_amount(h, w, amount=60, sim_config=cfg)

    assert deducted == pytest.approx(60.0)
    assert h.total_value_post == pytest.approx(100.0 - (60.0 * (100.0 / 150.0)))
    assert w.total_value_post == pytest.approx(50.0 - (60.0 * (50.0 / 150.0)))


def test_deduct_post_tax_amount_cannot_exceed_available():
    h = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=10, bd_post=0, cs_post=0)
    w = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)
    cfg, run_context = make_config(second_person_enabled=False)

    deducted = pe.deduct_post_tax_amount(h, w, amount=50, sim_config=cfg)

    assert deducted == pytest.approx(10.0)
    assert h.total_value_post == pytest.approx(0.0)


def test_apply_net_income_single_positive_adds_to_eq_post_only():
    ps = DummyPortfolioState(eq_pre=50, bd_pre=50, cs_pre=0, eq_post=25, bd_post=25, cs_post=0)

    result = pe.apply_net_income_single(ps, net_cash=40)

    assert result["post_tax_used"] == pytest.approx(0.0)
    assert result["pre_tax_used"] == pytest.approx(0.0)
    assert result["uncovered"] == pytest.approx(0.0)

    assert ps.eq_post == pytest.approx(45.0)
    assert ps.bd_post == pytest.approx(45.0)
    assert ps.cs_post == pytest.approx(0.0)


def test_apply_net_income_single_positive_empty_post_tax_defaults_to_cash():
    ps = DummyPortfolioState(eq_pre=50, bd_pre=50, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)

    pe.apply_net_income_single(ps, net_cash=40)

    assert ps.eq_post == pytest.approx(0.0)
    assert ps.bd_post == pytest.approx(0.0)
    assert ps.cs_post == pytest.approx(40.0)


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
