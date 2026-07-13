#test_withdrawalEngine.py

import types
import pytest

import src.warpsimlab.sim.engines.withdrawalEngine as we


class DummyPortfolioState:
    """
    Minimal stand-in for PortfolioState with only what withdrawalEngine uses.
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


def make_person(*, age=65, retire_age=65):
    return types.SimpleNamespace(age=age, retire_age=retire_age)


def make_config(
    *,
    include_rmd=True,
    second_person_enabled=False,
    always_use_expense_mode=False,
    retirement_withdraw_mode="Off",
    retirement_withdraw_pct=4.0,
    retirement_withdraw_dollars=0.0,
    inflation_rate=0.0,
):
    return types.SimpleNamespace(
        include_rmd=include_rmd,
        second_person_enabled=second_person_enabled,
        always_use_expense_mode=always_use_expense_mode,
        retirement_withdraw_mode=retirement_withdraw_mode,
        retirement_withdraw_pct=retirement_withdraw_pct,
        retirement_withdraw_dollars=retirement_withdraw_dollars,
        inflation_rate=inflation_rate,

        subplot_mode="standard",
        sim_type="cashflow_sim",
        monte_carlo_mode="pathBasedAnnualSampling",

        # cache fields used by calculate_retirement_withdrawal may be set during the call
        _ret_withdraw_base_dollars=None,
    )


@pytest.fixture(autouse=True)
def patch_rmd_constants(monkeypatch):
    # Avoid depending on src.warpsimlab.utils.constants during unit tests
    monkeypatch.setattr(we, "RMD_START_AGE", 73, raising=False)
    monkeypatch.setattr(we, "UNIFORM_LIFETIME_TABLE", {73: 25.0, 74: 24.0}, raising=False)


# -------------------------
# RMD helpers
# -------------------------

def test_calculate_rmd_below_start_age_is_zero():
    assert we.calculate_rmd(balance=100000.0, age=72) == 0


def test_calculate_rmd_uses_table_divisor():
    # age 73 divisor=25 => 100000/25 = 4000
    assert we.calculate_rmd(balance=100000.0, age=73) == pytest.approx(4000.0)


def test_calculate_rmd_fallback_divisor_when_age_missing():
    # fallback divisor is 2.0 in code
    assert we.calculate_rmd(balance=100000.0, age=120) == pytest.approx(50000.0)


def test_calculate_rmds_respects_include_rmd_flag():
    port = DummyPortfolioState(eq_pre=100, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)
    person = make_person(age=73)

    cfg = make_config(include_rmd=False)
    assert we.calculate_rmds(port, person, age=73, sim_config=cfg) == 0


def test_calculate_rmds_zero_when_no_pre_tax_assets():
    port = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=100, bd_post=0, cs_post=0)
    person = make_person(age=73)

    cfg = make_config(include_rmd=True)
    assert we.calculate_rmds(port, person, age=73, sim_config=cfg) == 0


def test_withdraw_rmds_withdraws_proportionally_from_pre_tax():
    # total_pre = 60+30+10 = 100; withdraw 10 => remove 6,3,1
    port = DummyPortfolioState(eq_pre=60, bd_pre=30, cs_pre=10, eq_post=0, bd_post=0, cs_post=0)

    taken = we.withdraw_rmds(port, rmd=10.0)

    assert taken == pytest.approx(10.0)
    assert port.eq_pre == pytest.approx(54.0)
    assert port.bd_pre == pytest.approx(27.0)
    assert port.cs_pre == pytest.approx(9.0)


# -------------------------
# calculate_retirement_withdrawal
# -------------------------

def test_retirement_withdrawal_off_only_rmds_withdrawn():
    h = DummyPortfolioState(eq_pre=100000, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)
    w = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)

    husband = make_person(age=73)
    wife = make_person(age=73)

    cfg = make_config(include_rmd=True, second_person_enabled=False, retirement_withdraw_mode="Off")

    out = we.calculate_retirement_withdrawal(h, w, husband, wife, year=0, sim_config=cfg)

    # age=73 => RMD = 100000/25 = 4000 (and it is withdrawn from pre-tax)
    assert out["total"] == pytest.approx(4000.0)
    assert out["pre_tax"] == pytest.approx(0.0)   # per code: only "remaining" withdrawals tracked here
    assert out["post_tax"] == pytest.approx(0.0)
    assert h.total_value_pre == pytest.approx(96000.0)


def test_retirement_withdrawal_percentage_base_is_cached_year0():
    h = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=100000, bd_post=0, cs_post=0)
    w = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)

    husband = make_person(age=60)
    wife = make_person(age=60)

    cfg = make_config(
        include_rmd=False,
        second_person_enabled=False,
        retirement_withdraw_mode="Percentage",
        retirement_withdraw_pct=4.0,
    )

    out1 = we.calculate_retirement_withdrawal(h, w, husband, wife, year=0, sim_config=cfg)
    assert out1["total"] == pytest.approx(4000.0)

    # Change portfolio totals; base should remain cached
    h.eq_post = 200000
    out2 = we.calculate_retirement_withdrawal(h, w, husband, wife, year=1, sim_config=cfg)
    assert out2["total"] == pytest.approx(4000.0)


def test_retirement_withdrawal_percentage_plus_inflation_scales():
    h = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=100000, bd_post=0, cs_post=0)
    w = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)

    husband = make_person(age=60)
    wife = make_person(age=60)

    cfg = make_config(
        include_rmd=False,
        second_person_enabled=False,
        retirement_withdraw_mode="Percentage + Inflation",
        retirement_withdraw_pct=4.0,
        inflation_rate=0.10,
    )

    out_y0 = we.calculate_retirement_withdrawal(h, w, husband, wife, year=0, sim_config=cfg)
    assert out_y0["total"] == pytest.approx(4000.0)

    # year=2 => base * 1.1^2 = 4000*1.21
    out_y2 = we.calculate_retirement_withdrawal(h, w, husband, wife, year=2, sim_config=cfg)
    assert out_y2["total"] == pytest.approx(4000.0 * (1.10 ** 2))


def test_retirement_withdrawal_draws_post_tax_first_then_pre_tax():
    # Request 150: post has 100, pre has 100 => should take 100 post + 50 pre
    h = DummyPortfolioState(eq_pre=100, bd_pre=0, cs_pre=0, eq_post=100, bd_post=0, cs_post=0)
    w = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)

    husband = make_person(age=60)
    wife = make_person(age=60)

    cfg = make_config(
        include_rmd=False,
        second_person_enabled=False,
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_dollars=150.0,
    )

    out = we.calculate_retirement_withdrawal(h, w, husband, wife, year=0, sim_config=cfg)

    assert out["total"] == pytest.approx(150.0)
    assert out["post_tax"] == pytest.approx(100.0)
    assert out["pre_tax"] == pytest.approx(50.0)

    assert h.total_value_post == pytest.approx(0.0)
    assert h.total_value_pre == pytest.approx(50.0)


def test_retirement_withdrawal_never_goes_negative_if_insufficient_assets():
    # Only 80 total available, request 150 => withdraw only 80
    h = DummyPortfolioState(eq_pre=30, bd_pre=0, cs_pre=0, eq_post=50, bd_post=0, cs_post=0)
    w = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)

    husband = make_person(age=60)
    wife = make_person(age=60)

    cfg = make_config(
        include_rmd=False,
        second_person_enabled=False,
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_dollars=150.0,
    )

    out = we.calculate_retirement_withdrawal(h, w, husband, wife, year=0, sim_config=cfg)

    assert out["total"] == pytest.approx(80.0)
    assert out["post_tax"] == pytest.approx(50.0)
    assert out["pre_tax"] == pytest.approx(30.0)
    assert h.total_value_post == pytest.approx(0.0)
    assert h.total_value_pre == pytest.approx(0.0)


def test_retirement_withdrawal_couple_orders_by_larger_post_then_larger_pre():
    # Couple: H has more post-tax, W has more pre-tax.
    # Request 150: should take post from H first (100), then pre from W (50).
    h = DummyPortfolioState(eq_pre=0, bd_pre=0, cs_pre=0, eq_post=100, bd_post=0, cs_post=0)
    w = DummyPortfolioState(eq_pre=100, bd_pre=0, cs_pre=0, eq_post=0, bd_post=0, cs_post=0)

    husband = make_person(age=60)
    wife = make_person(age=60)

    cfg = make_config(
        include_rmd=False,
        second_person_enabled=True,
        retirement_withdraw_mode="Fixed Dollar Amount",
        retirement_withdraw_dollars=150.0,
    )

    out = we.calculate_retirement_withdrawal(h, w, husband, wife, year=0, sim_config=cfg)

    assert out["total"] == pytest.approx(150.0)
    assert out["post_tax"] == pytest.approx(100.0)
    assert out["pre_tax"] == pytest.approx(50.0)

    assert h.total_value_post == pytest.approx(0.0)
    assert w.total_value_pre == pytest.approx(50.0)


# -------------------------
# use_manual_expenses_this_year
# -------------------------

def test_use_manual_expenses_true_when_manual_expenses_flag_set():
    husband = make_person(age=40, retire_age=65)
    wife = make_person(age=40, retire_age=65)

    cfg = make_config(second_person_enabled=True, always_use_expense_mode=True)

    assert we.use_expenses_this_year(cfg, husband, wife, year=0) is True
    assert we.use_expenses_this_year(cfg, husband, wife, year=50) is True


def test_use_manual_expenses_single_person_until_retired_then_false():
    husband = make_person(age=64, retire_age=65)
    wife = make_person(age=0, retire_age=0)

    cfg = make_config(second_person_enabled=False, always_use_expense_mode=False)

    # year 0 => 64 < 65 => not retired => use manual expenses => True
    assert we.use_expenses_this_year(cfg, husband, wife, year=0) is True

    # year 1 => 65 >= 65 => retired => withdrawals => False
    assert we.use_expenses_this_year(cfg, husband, wife, year=1) is False


def test_use_manual_expenses_couple_until_both_retired_then_false():
    husband = make_person(age=64, retire_age=65)
    wife = make_person(age=60, retire_age=62)

    cfg = make_config(second_person_enabled=True, always_use_expense_mode=False)

    # year 0: husband not retired => True
    assert we.use_expenses_this_year(cfg, husband, wife, year=0) is True

    # year 1: husband retired (65), wife not (61) => True
    assert we.use_expenses_this_year(cfg, husband, wife, year=1) is True

    # year 2: husband 66 retired, wife 62 retired => False
    assert we.use_expenses_this_year(cfg, husband, wife, year=2) is False