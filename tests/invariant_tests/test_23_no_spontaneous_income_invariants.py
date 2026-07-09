import numpy as np

from src.warpsimlab.sim.simulation import run_pipeline


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


def test_all_income_series_stay_zero_when_all_income_sources_and_yields_are_zero(make_case):
    core, cfg = run_case(
        make_case,
        second_person_enabled=False,
        calculate_income_taxes=False,
        calculate_state_taxes=False,
        include_rmd=False,
        always_use_expense_mode=False,
        retirement_withdraw_mode="Off",
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
        husband_equity_pre=0.0,
        husband_equity_post=0.0,
        husband_bond_pre=0.0,
        husband_bond_post=0.0,
        husband_cash_pre=0.0,
        husband_cash_post=0.0,
        husband_real_estate=0.0,
        wife_equity_pre=0.0,
        wife_equity_post=0.0,
        wife_bond_pre=0.0,
        wife_bond_post=0.0,
        wife_cash_pre=0.0,
        wife_cash_post=0.0,
        wife_real_estate=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        annual_expense=0.0,
        use_fund_expenses=False,
        eq_mean=0.0,
        bd_mean=0.0,
        cs_mean=0.0,
        re_mean=0.0,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_std=0.0,
        years_to_simulate=5,
    )

    assert np.allclose(core["gross_income"], 0.0)
    assert np.allclose(core["net_income"], 0.0)
    assert np.allclose(core["taxes"], 0.0)
    assert np.allclose(core["bond_interest"], 0.0)
    assert np.allclose(core["cash_interest"], 0.0)
    assert np.allclose(core["qualified_dividends"], 0.0)

    for key, arr in core["breakdown_by_class"].items():
        assert np.allclose(arr, 0.0), key


def test_no_spontaneous_income_also_implies_zero_net_profit_when_expenses_are_zero(make_case):
    core, cfg = run_case(
        make_case,
        second_person_enabled=False,
        calculate_income_taxes=False,
        calculate_state_taxes=False,
        include_rmd=False,
        always_use_expense_mode=False,
        retirement_withdraw_mode="Off",
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
        husband_equity_pre=0.0,
        husband_equity_post=0.0,
        husband_bond_pre=0.0,
        husband_bond_post=0.0,
        husband_cash_pre=0.0,
        husband_cash_post=0.0,
        husband_real_estate=0.0,
        wife_equity_pre=0.0,
        wife_equity_post=0.0,
        wife_bond_pre=0.0,
        wife_bond_post=0.0,
        wife_cash_pre=0.0,
        wife_cash_post=0.0,
        wife_real_estate=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        annual_expense=0.0,
        use_fund_expenses=False,
        eq_mean=0.0,
        bd_mean=0.0,
        cs_mean=0.0,
        re_mean=0.0,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_std=0.0,
        years_to_simulate=5,
    )

    assert np.allclose(core["net_profit"], 0.0)


def test_no_spontaneous_income_keeps_person_level_income_zero(make_case):
    core, cfg = run_case(
        make_case,
        second_person_enabled=True,
        calculate_income_taxes=False,
        calculate_state_taxes=False,
        include_rmd=False,
        always_use_expense_mode=False,
        retirement_withdraw_mode="Off",
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
        husband_equity_pre=0.0,
        husband_equity_post=0.0,
        husband_bond_pre=0.0,
        husband_bond_post=0.0,
        husband_cash_pre=0.0,
        husband_cash_post=0.0,
        husband_real_estate=0.0,
        wife_equity_pre=0.0,
        wife_equity_post=0.0,
        wife_bond_pre=0.0,
        wife_bond_post=0.0,
        wife_cash_pre=0.0,
        wife_cash_post=0.0,
        wife_real_estate=0.0,
        post_tax_equity_dividend_yield=0.0,
        post_tax_bond_interest_yield=0.0,
        post_tax_cash_interest_yield=0.0,
        annual_expense=0.0,
        use_fund_expenses=False,
        eq_mean=0.0,
        bd_mean=0.0,
        cs_mean=0.0,
        re_mean=0.0,
        eq_std=0.0,
        bd_std=0.0,
        cs_std=0.0,
        re_std=0.0,
        years_to_simulate=5,
    )

    assert np.allclose(core["net_income_husband"], 0.0)
    assert np.allclose(core["net_income_wife"], 0.0)