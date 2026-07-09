import numpy as np
import pytest

from src.warpsimlab.sim.simulation import run_pipeline

# This is deep money passing in the core.  Need to ponder.
#pytest.skip("Skipping invariant tests for now", allow_module_level=True)



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



def test_zeroed_wife_case_matches_single_person_case_for_household_outputs(make_case):
    single_core, single_cfg = run_case(
        make_case,
        second_person_enabled=False,
        years_to_simulate=5,
    )

    couple_zero_wife_core, couple_zero_wife_cfg = run_case(
        make_case,
        second_person_enabled=True,
        years_to_simulate=5,
        wife_income=0.0,
        wife_ss=0.0,
        wife_pension=0.0,
        wife_annuity=0.0,
        wife_annual_401k_contribution=0.0,
        wife_annual_employer_match=0.0,
        wife_equity_pre=0.0,
        wife_equity_post=0.0,
        wife_bond_pre=0.0,
        wife_bond_post=0.0,
        wife_cash_pre=0.0,
        wife_cash_post=0.0,
        wife_real_estate=0.0,
    )

    np.testing.assert_allclose(
        single_core["total_assets"],
        couple_zero_wife_core["total_assets"],
        rtol=0.0,
        atol=1e-8,
    )

    np.testing.assert_allclose(
        single_core["net_income"],
        couple_zero_wife_core["net_income"],
        rtol=0.0,
        atol=1e-8,
    )

    np.testing.assert_allclose(
        single_core["expense_amt"],
        couple_zero_wife_core["expense_amt"],
        rtol=0.0,
        atol=1e-8,
    )


def test_zeroed_wife_case_matches_single_person_case_for_husband_outputs(make_case):
    single_core, single_cfg = run_case(
        make_case,
        second_person_enabled=False,
        years_to_simulate=5,
    )

    couple_zero_wife_core, couple_zero_wife_cfg = run_case(
        make_case,
        second_person_enabled=True,
        years_to_simulate=5,
        wife_income=0.0,
        wife_ss=0.0,
        wife_pension=0.0,
        wife_annuity=0.0,
        wife_annual_401k_contribution=0.0,
        wife_annual_employer_match=0.0,
        wife_equity_pre=0.0,
        wife_equity_post=0.0,
        wife_bond_pre=0.0,
        wife_bond_post=0.0,
        wife_cash_pre=0.0,
        wife_cash_post=0.0,
        wife_real_estate=0.0,
    )

    np.testing.assert_allclose(
        single_core["net_income"],
        couple_zero_wife_core["net_income"],
        rtol=0.0,
        atol=1e-8,
    )

    np.testing.assert_allclose(
        single_core["pre_tax_assets"],
        couple_zero_wife_core["pre_tax_assets"],
        rtol=0.0,
        atol=1e-8,
    )

    np.testing.assert_allclose(
        single_core["post_tax_assets"],
        couple_zero_wife_core["post_tax_assets"],
        rtol=0.0,
        atol=1e-8,
    )


def test_zeroed_wife_case_has_zero_wife_income_series(make_case):
    core, cfg = run_case(
        make_case,
        second_person_enabled=True,
        years_to_simulate=5,
        wife_income=0.0,
        wife_ss=0.0,
        wife_pension=0.0,
        wife_annuity=0.0,
        wife_annual_401k_contribution=0.0,
        wife_annual_employer_match=0.0,
        wife_equity_pre=0.0,
        wife_equity_post=0.0,
        wife_bond_pre=0.0,
        wife_bond_post=0.0,
        wife_cash_pre=0.0,
        wife_cash_post=0.0,
        wife_real_estate=0.0,

        # Had to also zero out the husband.  By design, profits move into general household funds, and then return to both spouses.
        husband_income=0.0,
        husband_ss=0.0,
        husband_pension=0.0,
        husband_annuity=0.0,
        husband_annual_401k_contribution=0.0,
        husband_annual_employer_match=0.0,
        husband_equity_pre=0.0,
        husband_equity_post=0.0,
        husband_bond_pre=0.0,
        husband_bond_post=0.0,
        husband_cash_pre=0.0,
        husband_cash_post=0.0,
        husband_real_estate=0.0,

    )

    assert np.allclose(core["net_income_wife"], 0.0)