import numpy as np

from src.warpsimlab.sim.simulation import run_pipeline


EPS = 1e-9


def run_case(make_case, **overrides):
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


def test_real_estate_series_is_zero_when_real_estate_excluded(make_case):
    core, cfg = run_case(
        make_case,
        include_realestate=False,
        husband_real_estate=250_000.0,
        wife_real_estate=125_000.0,
    )

    assert np.allclose(core["real_estate"], 0.0)


def test_total_assets_increase_when_real_estate_is_included(make_case):
    core_off, cfg_off = run_case(
        make_case,
        include_realestate=False,
        husband_real_estate=250_000.0,
        wife_real_estate=125_000.0,
        second_person_enabled=True,
    )

    core_on, cfg_on = run_case(
        make_case,
        include_realestate=True,
        husband_real_estate=250_000.0,
        wife_real_estate=125_000.0,
        second_person_enabled=True,
    )

    assert np.all(core_on["real_estate"] >= -EPS)
    assert np.all(core_on["total_assets"] >= core_off["total_assets"] - EPS)


def test_real_estate_toggle_changes_only_the_total_assets_identity_term(make_case):
    core_off, cfg_off = run_case(
        make_case,
        include_realestate=False,
        husband_real_estate=300_000.0,
        wife_real_estate=0.0,
    )

    core_on, cfg_on = run_case(
        make_case,
        include_realestate=True,
        husband_real_estate=300_000.0,
        wife_real_estate=0.0,
    )

    np.testing.assert_allclose(
        core_off["pre_tax_assets"],
        core_on["pre_tax_assets"],
        rtol=0.0,
        atol=1e-8,
    )

    np.testing.assert_allclose(
        core_off["post_tax_assets"],
        core_on["post_tax_assets"],
        rtol=0.0,
        atol=1e-8,
    )

    np.testing.assert_allclose(
        core_on["total_assets"] - core_off["total_assets"],
        core_on["real_estate"],
        rtol=0.0,
        atol=1e-8,
    )