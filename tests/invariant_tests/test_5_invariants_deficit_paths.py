import numpy as np
import pytest

from src.warpsimlab.sim.simulation import run_pipeline

EPS = 1e-9

#pytest.skip("Skipping invariant tests for now", allow_module_level=True)



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


def test_assets_never_negative_even_under_stress(make_case):
    core, cfg = run_case(
        make_case,
        husband_income=0.0,
        wife_income=0.0,
        annual_expense=200_000.0,
    )

    assert np.all(core["total_assets"] >= -EPS)


def test_emergency_tax_paths_non_negative(make_case):
    core, cfg = run_case(
        make_case,
        husband_income=0.0,
        wife_income=0.0,
        annual_expense=200_000.0,
    )

    assert np.all(core["final_tax_delta_uncovered"] >= -EPS)
    assert np.all(core["emergency_pre_tax_used"] >= -EPS)


def test_deficit_eventually_surfaces_when_resources_exhausted(make_case):
    core, cfg = run_case(
        make_case,
        husband_income=0.0,
        wife_income=0.0,
        annual_expense=500_000.0,
    )

    uncovered = core["final_tax_delta_uncovered"]

    assert np.any(uncovered > 0.0)