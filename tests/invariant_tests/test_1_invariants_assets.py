import numpy as np

from src.warpsimlab.sim.simulation import run_pipeline


EPS = 1e-9


def run_case(make_case, **overrides):
    """
    Helper that runs the real simulation pipeline using the scenario
    produced by make_case and returns the raw core results.
    """
    husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config = make_case(**overrides)

    result = run_pipeline(
        husband_portfolio,
        wife_portfolio,
        husband,
        wife,
        expenses,
        sim_config,
    )

    return result["core"], sim_config


def test_asset_buckets_never_negative(make_case):
    """
    Core invariant:
    The engine should never produce negative asset balances.
    """

    core, cfg = run_case(make_case)

    assert np.all(core["total_assets"] >= -EPS)
    assert np.all(core["pre_tax_assets"] >= -EPS)
    assert np.all(core["post_tax_assets"] >= -EPS)

    assert np.all(core["cash"] >= -EPS)
    assert np.all(core["bonds"] >= -EPS)
    assert np.all(core["real_estate"] >= -EPS)


def test_asset_composition_identity_without_realestate(make_case):
    """
    If real estate is disabled, the total assets should equal the sum
    of pre-tax and post-tax assets.
    """

    core, cfg = run_case(make_case, include_realestate=False)

    np.testing.assert_allclose(
        core["total_assets"],
        core["pre_tax_assets"] + core["post_tax_assets"],
        rtol=0.0,
        atol=1e-8,
    )


def test_asset_composition_identity_with_realestate(make_case):
    """
    If real estate is enabled, the total assets must equal
    pre-tax + post-tax + real estate.
    """

    core, cfg = run_case(make_case, include_realestate=True)

    np.testing.assert_allclose(
        core["total_assets"],
        core["pre_tax_assets"]
        + core["post_tax_assets"]
        + core["real_estate"],
        rtol=0.0,
        atol=1e-8,
    )


def test_net_profit_identity(make_case):
    """
    Accounting identity:
    net_profit = net_income - expenses
    """

    core, cfg = run_case(make_case)

    np.testing.assert_allclose(
        core["net_profit"],
        core["net_income"] - core["expense_amt"],
        rtol=0.0,
        atol=1e-8,
    )