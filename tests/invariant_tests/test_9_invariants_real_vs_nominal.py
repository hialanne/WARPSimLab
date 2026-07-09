import numpy as np

from src.warpsimlab.sim.simulation import run_pipeline


def run_case(make_case, **overrides):
    hp, wp, h, w, e, cfg = make_case(**overrides)

    result = run_pipeline(
        hp,
        wp,
        h,
        w,
        e,
        cfg,
    )

    return result["core"], cfg


def test_real_plot_mode_deflates_total_assets_relative_to_nominal(make_case):
    nominal_core, nominal_cfg = run_case(
        make_case,
        plot_mode="nominal",
        inflation_rate=0.03,
        years_to_simulate=5,
    )

    real_core, real_cfg = run_case(
        make_case,
        plot_mode="real",
        inflation_rate=0.03,
        years_to_simulate=5,
    )

    nominal = nominal_core["total_assets"][0]
    real = real_core["total_assets"][0]

    np.testing.assert_allclose(real[0], nominal[0], rtol=0.0, atol=1e-8)
    assert np.all(real[1:] <= nominal[1:] + 1e-8)


def test_real_plot_mode_deflates_pre_and_post_tax_assets_relative_to_nominal(make_case):
    nominal_core, nominal_cfg = run_case(
        make_case,
        plot_mode="nominal",
        inflation_rate=0.03,
        years_to_simulate=5,
    )

    real_core, real_cfg = run_case(
        make_case,
        plot_mode="real",
        inflation_rate=0.03,
        years_to_simulate=5,
    )

    nominal_pre = nominal_core["pre_tax_assets"][0]
    real_pre = real_core["pre_tax_assets"][0]

    nominal_post = nominal_core["post_tax_assets"][0]
    real_post = real_core["post_tax_assets"][0]

    np.testing.assert_allclose(real_pre[0], nominal_pre[0], rtol=0.0, atol=1e-8)
    np.testing.assert_allclose(real_post[0], nominal_post[0], rtol=0.0, atol=1e-8)

    assert np.all(real_pre[1:] <= nominal_pre[1:] + 1e-8)
    assert np.all(real_post[1:] <= nominal_post[1:] + 1e-8)


def test_zero_inflation_makes_real_and_nominal_match_for_deflated_series(make_case):
    nominal_core, nominal_cfg = run_case(
        make_case,
        plot_mode="nominal",
        inflation_rate=0.0,
        years_to_simulate=5,
    )

    real_core, real_cfg = run_case(
        make_case,
        plot_mode="real",
        inflation_rate=0.0,
        years_to_simulate=5,
    )

    np.testing.assert_allclose(
        real_core["total_assets"],
        nominal_core["total_assets"],
        rtol=0.0,
        atol=1e-8,
    )

    np.testing.assert_allclose(
        real_core["pre_tax_assets"],
        nominal_core["pre_tax_assets"],
        rtol=0.0,
        atol=1e-8,
    )

    np.testing.assert_allclose(
        real_core["post_tax_assets"],
        nominal_core["post_tax_assets"],
        rtol=0.0,
        atol=1e-8,
    )

    np.testing.assert_allclose(
        real_core["cash"],
        nominal_core["cash"],
        rtol=0.0,
        atol=1e-8,
    )