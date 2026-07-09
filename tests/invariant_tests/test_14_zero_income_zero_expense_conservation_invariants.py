import numpy as np
import pytest

from src.warpsimlab.sim.simulation import run_pipeline

#pytest.skip("Skipping GUI tests for now", allow_module_level=True)


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


def test_total_assets_remain_constant_with_no_income_no_expense_no_returns(make_case):
    core, cfg = run_case(
        make_case,
        husband_income=0.0,
        wife_income=0.0,
        husband_ss=0.0,
        wife_ss=0.0,
        husband_pension=0.0,
        wife_pension=0.0,
        husband_annuity=0.0,
        wife_annuity=0.0,
        husband_annual_401k_contribution=0.0,
        husband_annual_employer_match=0.0,
        wife_annual_401k_contribution=0.0,
        wife_annual_employer_match=0.0,
        annual_expense=0.0,
        calculate_income_taxes=False,
        use_fund_expenses=False,
        include_rmd=False,
        eq_mean=0.0,
        bd_mean=0.0,
        cs_mean=0.0,
        re_mean=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_std=0.0,
        second_person_enabled=False,
        years_to_simulate=5,
    )

    baseline = np.repeat(core["total_assets"][:, [0]], core["total_assets"].shape[1], axis=1)

    np.testing.assert_allclose(
        core["total_assets"],
        baseline,
        rtol=0.0,
        atol=1e-8,
    )


def test_pre_and_post_tax_assets_remain_constant_in_conservation_case(make_case):
    core, cfg = run_case(
        make_case,
        husband_income=0.0,
        wife_income=0.0,
        husband_ss=0.0,
        wife_ss=0.0,
        husband_pension=0.0,
        wife_pension=0.0,
        husband_annuity=0.0,
        wife_annuity=0.0,
        husband_annual_401k_contribution=0.0,
        husband_annual_employer_match=0.0,
        wife_annual_401k_contribution=0.0,
        wife_annual_employer_match=0.0,
        annual_expense=0.0,
        calculate_income_taxes=False,
        use_fund_expenses=False,
        include_rmd=False,
        eq_mean=0.0,
        bd_mean=0.0,
        cs_mean=0.0,
        re_mean=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_std=0.0,
        second_person_enabled=False,
        years_to_simulate=5,
    )

    assert np.allclose(
        core["pre_tax_assets"],
        core["pre_tax_assets"][:, [0]],
        rtol=0.0,
        atol=1e-8,
    )

    assert np.allclose(
        core["post_tax_assets"],
        core["post_tax_assets"][:, [0]],
        rtol=0.0,
        atol=1e-8,
    )

def test_gross_and_net_income_stay_zero_in_conservation_case(make_case):
    core, cfg = run_case(
        make_case,
        husband_income=0.0,
        wife_income=0.0,
        husband_ss=0.0,
        wife_ss=0.0,
        husband_pension=0.0,
        wife_pension=0.0,
        husband_annuity=0.0,
        wife_annuity=0.0,
        husband_annual_401k_contribution=0.0,
        husband_annual_employer_match=0.0,
        wife_annual_401k_contribution=0.0,
        wife_annual_employer_match=0.0,
        annual_expense=0.0,
        calculate_income_taxes=False,
        use_fund_expenses=False,
        include_rmd=False,
        eq_mean=0.0,
        bd_mean=0.0,
        cs_mean=0.0,
        re_mean=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_std=0.0,
        second_person_enabled=False,
        years_to_simulate=5,
    )

    assert np.allclose(core["gross_income"], 0.0)
    assert np.allclose(core["net_income"], 0.0)
    assert np.allclose(core["net_profit"], 0.0)