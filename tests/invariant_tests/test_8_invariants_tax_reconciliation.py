import numpy as np
import pytest

from tests.architectural_helpers import run_invariant_case as run_case

#pytest.skip("Skipping invariant tests for now", allow_module_level=True)



def test_final_tax_delta_is_fully_partitioned(make_case):
    core, cfg = run_case(make_case)

    np.testing.assert_allclose(
        core["final_tax_delta"],
        core["final_tax_delta_deducted"] + core["final_tax_delta_uncovered"],
        rtol=0.0,
        atol=1e-8,
    )


def test_zero_tax_delta_means_zero_deducted_and_uncovered(make_case):
    core, cfg = run_case(
        make_case,
        calculate_income_taxes=False,
    )

    assert np.allclose(core["final_tax_delta"], 0.0)
    assert np.allclose(core["final_tax_delta_deducted"], 0.0)
    assert np.allclose(core["final_tax_delta_uncovered"], 0.0)


def test_tax_reconciliation_never_creates_negative_offsets(make_case):
    core, cfg = run_case(
        make_case,
        husband_income=0.0,
        wife_income=0.0,
        annual_expense=300_000.0,
        calculate_income_taxes=True,
    )

    assert np.all(core["final_tax_delta"] >= -1e-8)
    assert np.all(core["final_tax_delta_deducted"] >= -1e-8)
    assert np.all(core["final_tax_delta_uncovered"] >= -1e-8)