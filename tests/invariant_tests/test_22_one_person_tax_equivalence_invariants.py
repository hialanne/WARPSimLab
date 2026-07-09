import numpy as np
import pytest

from src.warpsimlab.sim.simulation import run_pipeline

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


def test_zeroed_wife_case_matches_single_person_case_for_tax_outputs(make_case):
    single_core, single_cfg = run_case(
        make_case,
        second_person_enabled=False,
        tax_filing_status="Single",
        calculate_income_taxes=True,
        calculate_state_taxes=True,
        state_of_residence="CA",
        years_to_simulate=5,
    )

    zero_wife_core, zero_wife_cfg = run_case(
        make_case,
        second_person_enabled=True,
        tax_filing_status="Single",
        calculate_income_taxes=True,
        calculate_state_taxes=True,
        state_of_residence="CA",
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

    np.testing.assert_allclose(single_core["taxes"], zero_wife_core["taxes"], rtol=0.0, atol=1e-8)
    np.testing.assert_allclose(
        single_core["federal_ordinary_tax"],
        zero_wife_core["federal_ordinary_tax"],
        rtol=0.0,
        atol=1e-8,
    )
    np.testing.assert_allclose(
        single_core["federal_qualified_dividend_tax"],
        zero_wife_core["federal_qualified_dividend_tax"],
        rtol=0.0,
        atol=1e-8,
    )
    np.testing.assert_allclose(
        single_core["state_income_tax"],
        zero_wife_core["state_income_tax"],
        rtol=0.0,
        atol=1e-8,
    )


def test_zeroed_wife_case_matches_single_person_case_for_income_accounting_outputs(make_case):
    single_core, single_cfg = run_case(
        make_case,
        second_person_enabled=False,
        tax_filing_status="Single",
        calculate_income_taxes=True,
        calculate_state_taxes=True,
        state_of_residence="CA",
        years_to_simulate=5,
    )

    zero_wife_core, zero_wife_cfg = run_case(
        make_case,
        second_person_enabled=True,
        tax_filing_status="Single",
        calculate_income_taxes=True,
        calculate_state_taxes=True,
        state_of_residence="CA",
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

    np.testing.assert_allclose(single_core["gross_income"], zero_wife_core["gross_income"], rtol=0.0, atol=1e-8)
    np.testing.assert_allclose(single_core["net_profit"], zero_wife_core["net_profit"], rtol=0.0, atol=1e-8)
    np.testing.assert_allclose(single_core["tax_bracket"], zero_wife_core["tax_bracket"], rtol=0.0, atol=1e-8)


def test_zeroed_wife_case_keeps_wife_net_income_zero(make_case):
    core, cfg = run_case(
        make_case,
        second_person_enabled=True,
        tax_filing_status="Single",
        calculate_income_taxes=True,
        calculate_state_taxes=True,
        state_of_residence="CA",
        years_to_simulate=5,
        wife_income=0.0,
        wife_ss=0.0,
        wife_pension=0.0,
        wife_annuity=0.0,
        wife_annual_401k_contribution=0.0,
        wife_annual_employer_match=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        wife_equity_pre=0.0,
        wife_equity_post=0.0,
        wife_bond_pre=0.0,
        wife_bond_post=0.0,
        wife_cash_pre=0.0,
        wife_cash_post=0.0,
        wife_real_estate=0.0,
    )

    assert np.allclose(core["net_income_wife"], 0.0)