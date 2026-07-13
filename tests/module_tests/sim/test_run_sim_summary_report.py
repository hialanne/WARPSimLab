# test_run_sim_summary_report.py

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.warpsimlab.sim import run_sim_summary_report as mod


def test_get_report_option_reads_nested_value():
    options = {
        "portfolio_visuals": {
            "include_normal_projection": True,
        }
    }

    assert (
        mod._get_report_option(
            options,
            ["portfolio_visuals", "include_normal_projection"],
            default=False,
        )
        is True
    )


def test_get_report_option_returns_default_for_missing_path():
    options = {
        "portfolio_visuals": {}
    }

    assert (
        mod._get_report_option(
            options,
            ["portfolio_visuals", "include_monte_carlo_analysis"],
            default="missing",
        )
        == "missing"
    )


def test_as_float_handles_none_invalid_and_numeric_values():
    assert mod._as_float(None, default=7.0) == pytest.approx(7.0)
    assert mod._as_float("not-a-number", default=5.0) == pytest.approx(5.0)
    assert mod._as_float("12.5") == pytest.approx(12.5)
    assert mod._as_float(3) == pytest.approx(3.0)


def test_array_value_reads_existing_values_and_defaults_safely():
    results = {
        "taxes": [1.0, "2.5", None],
    }

    assert mod._array_value(results, "taxes", 0) == pytest.approx(1.0)
    assert mod._array_value(results, "taxes", 1) == pytest.approx(2.5)
    assert mod._array_value(results, "taxes", 2, default=9.0) == pytest.approx(9.0)
    assert mod._array_value(results, "taxes", 99, default=8.0) == pytest.approx(8.0)
    assert mod._array_value(results, "missing", 0, default=6.0) == pytest.approx(6.0)


def test_clamp_index_bounds_values():
    assert mod._clamp_index(-5, 10) == 0
    assert mod._clamp_index(3, 10) == 3
    assert mod._clamp_index(99, 10) == 9
    assert mod._clamp_index(5, 0) == 0


def test_rate_fraction_to_percent():
    assert mod._rate_fraction_to_percent(None) is None
    assert mod._rate_fraction_to_percent(0.075) == pytest.approx(7.5)


def test_build_projection_period_label():
    cfg = SimpleNamespace(start_year=2025, years_to_simulate=30)

    assert mod._build_projection_period_label(cfg) == "2025-2055 (30 Years)"


def test_build_projection_period_label_returns_na_for_invalid_values():
    cfg = SimpleNamespace(start_year="bad", years_to_simulate=30)

    assert mod._build_projection_period_label(cfg) == "N/A"


def test_build_report_basis_label():
    assert (
        mod._build_report_basis_label(SimpleNamespace(plot_mode="real"))
        == "Real Dollars (Inflation Adjusted)"
    )
    assert (
        mod._build_report_basis_label(SimpleNamespace(plot_mode="raw"))
        == "Raw Dollars (Future Nominal Values)"
    )
    assert mod._build_report_basis_label(SimpleNamespace(plot_mode="nominal")) == "N/A"


def test_friendly_label_maps_known_values_and_preserves_unknowns():
    assert mod._friendly_label("pathBasedAnnualSampling") == "Path-Based Annual Sampling"
    assert mod._friendly_label("rollingHistoricalWindows") == "Rolling Historical Windows"
    assert mod._friendly_label("maintain-current-allocation") == "Maintain Current Allocation"
    assert mod._friendly_label("custom-value") == "custom-value"


def test_build_portfolio_milestone_computes_totals():
    results = {
        "year": [2030],
        "pre_tax_assets": [100.0],
        "post_tax_assets": [200.0],
        "real_estate": [50.0],
    }

    milestone = mod._build_portfolio_milestone(results, 0)

    assert milestone["Year"] == pytest.approx(2030.0)
    assert milestone["Pre-Tax Assets"] == pytest.approx(100.0)
    assert milestone["Post-Tax Assets"] == pytest.approx(200.0)
    assert milestone["Total Portfolio"] == pytest.approx(300.0)
    assert milestone["Real Estate"] == pytest.approx(50.0)
    assert milestone["Total Assets"] == pytest.approx(350.0)


def test_build_income_milestone_combines_pensions_and_annuities():
    results = {
        "year": [2030],
        "wages": [100.0],
        "rmd": [5.0],
        "social_security": [10.0],
        "pensions": [20.0],
        "annuities": [30.0],
        "gross_income": [165.0],
        "ira_401k": [7.0],
        "taxes": [15.0],
        "tax_bracket": [0.22],
        "net_income": [150.0],
        "expenses": [80.0],
        "net_cash_flow": [70.0],
        "fund_expenses": [2.0],
    }

    milestone = mod._build_income_milestone(results, 0)

    assert milestone["Year"] == pytest.approx(2030.0)
    assert milestone["Wages"] == pytest.approx(100.0)
    assert milestone["RMD"] == pytest.approx(5.0)
    assert milestone["Social Security"] == pytest.approx(10.0)
    assert milestone["Pensions & Annuities"] == pytest.approx(50.0)
    assert milestone["Gross Income"] == pytest.approx(165.0)
    assert milestone["401k or IRA Contribution"] == pytest.approx(7.0)
    assert milestone["Taxes"] == pytest.approx(15.0)
    assert milestone["Tax Bracket"] == pytest.approx(0.22)
    assert milestone["Net Income"] == pytest.approx(150.0)
    assert milestone["Household Expenses"] == pytest.approx(80.0)
    assert milestone["Net Cash Flow"] == pytest.approx(70.0)
    assert milestone["Fund Expenses"] == pytest.approx(2.0)


def test_calculate_retirement_index_single_person_clamps_to_results_length():
    results = {"year": [2025, 2026, 2027]}
    husband = SimpleNamespace(age=60, retire_age=65)
    wife = SimpleNamespace(age=50, retire_age=99)
    cfg = SimpleNamespace(second_person_enabled=False)

    assert mod._calculate_retirement_index(results, husband, wife, cfg) == 2


def test_calculate_retirement_index_couple_uses_later_retirement_offset():
    results = {"year": [2025, 2026, 2027, 2028, 2029, 2030]}
    husband = SimpleNamespace(age=60, retire_age=63)
    wife = SimpleNamespace(age=50, retire_age=55)
    cfg = SimpleNamespace(second_person_enabled=True)

    assert mod._calculate_retirement_index(results, husband, wife, cfg) == 5


def test_build_simulation_totals_sums_series_and_portfolio_values():
    results = {
        "pre_tax_assets": [100.0, 120.0, 140.0],
        "post_tax_assets": [50.0, 60.0, 70.0],
        "gross_income": [0.0, 100.0, 100.0],
        "taxes": [0.0, 10.0, 11.0],
        "expenses": [0.0, 60.0, 65.0],
        "net_cash_flow": [0.0, 30.0, 24.0],
        "fund_expenses": [0.0, 1.0, 2.0],
    }

    totals = mod._build_simulation_totals(results, simulated_shortfall_rate=0.25)

    assert totals["Portfolio Start"] == pytest.approx(150.0)
    assert totals["Portfolio End"] == pytest.approx(210.0)
    assert totals["Maximum Portfolio"] == pytest.approx(210.0)
    assert totals["Minimum Portfolio"] == pytest.approx(150.0)
    assert totals["Total Income"] == pytest.approx(200.0)
    assert totals["Taxes Paid"] == pytest.approx(21.0)
    assert totals["Household Expenses"] == pytest.approx(125.0)
    assert totals["Net Cash Flow"] == pytest.approx(54.0)
    assert totals["Fund Expenses"] == pytest.approx(3.0)
    assert totals["Simulated Shortfall Rate"] == pytest.approx(0.25)


def test_build_simulation_snapshot_includes_payroll_tax_setting():
    cfg = SimpleNamespace(
        start_year=2025,
        years_to_simulate=30,
        inflation_rate=0.03,
        plot_mode="raw",
        second_person_enabled=True,
        calculate_income_taxes=True,
        calculate_payroll_taxes=False,
        calculate_state_taxes=True,
        state_of_residence="NM",
        retirement_withdraw_mode="Off",
        sim_initial_allocation_mode="dont-rebalance",
        use_fund_expenses=False,
    )

    snapshot = mod._build_simulation_snapshot(cfg)

    assert snapshot["Start Year"] == 2025
    assert snapshot["Years Simulated"] == 30
    assert snapshot["Projection End Year"] == 2055
    assert snapshot["Inflation Rate"] == pytest.approx(3.0)
    assert snapshot["Taxes Enabled"] is True
    assert snapshot["Payroll Taxes Enabled"] is False
    assert snapshot["State Taxes Enabled"] is True
    assert snapshot["State of Residence"] == "NM"


def test_portfolio_amount_helpers_handle_none_and_missing_values():
    portfolio = SimpleNamespace(equity_pre=100.0, equity_post="50.5")

    assert mod._portfolio_value(None, "equity_pre") == pytest.approx(0.0)
    assert mod._portfolio_value(portfolio, "missing") == pytest.approx(0.0)
    assert mod._portfolio_amount(portfolio, "equity_pre", "equity_post") == pytest.approx(150.5)
    assert mod._portfolio_total(portfolio, ["equity_pre", "equity_post"]) == pytest.approx(150.5)


def test_build_portfolio_inputs_single_person():
    husband_portfolio = SimpleNamespace(
        equity_pre=100.0,
        equity_post=200.0,
        bond_pre=10.0,
        bond_post=20.0,
        cash_pre=5.0,
        cash_post=15.0,
        real_estate=50.0,
    )
    wife_portfolio = SimpleNamespace(
        equity_pre=999.0,
        equity_post=999.0,
        bond_pre=999.0,
        bond_post=999.0,
        cash_pre=999.0,
        cash_post=999.0,
        real_estate=999.0,
    )
    cfg = SimpleNamespace(
        second_person_enabled=False,
        use_fund_expenses=True,
        fund_expense=0.0015,
        sim_initial_allocation_mode="none",
        rebalance_every_year=False,
    )

    inputs = mod._build_portfolio_inputs(husband_portfolio, wife_portfolio, cfg)
    table = inputs["Starting Portfolio Inputs"]

    assert table["columns"] == ["Asset / Account Type", "Husband", "Total"]
    assert table["rows"][0] == ["Stocks Pre-Tax", "$100", "$100"]
    assert table["rows"][-1] == ["Total Assets", "$400", "$400"]
    assert inputs["Portfolio Settings"]["Fund Expenses Enabled"] is True
    assert inputs["Portfolio Settings"]["Fund Expense Rate"] == pytest.approx(0.15)


def test_build_household_retirement_table_couple_includes_totals():
    husband = SimpleNamespace(
        age=60,
        retire_age=65,
        income=100.0,
        ss=20.0,
        ss_age=67,
        pension=30.0,
        pension_age=65,
        annuity=40.0,
        annuity_age=70,
        annual_401k_contribution=10.0,
        annual_employer_match=5.0,
    )
    wife = SimpleNamespace(
        age=58,
        retire_age=64,
        income=200.0,
        ss=50.0,
        ss_age=67,
        pension=60.0,
        pension_age=65,
        annuity=70.0,
        annuity_age=70,
        annual_401k_contribution=20.0,
        annual_employer_match=8.0,
    )
    cfg = SimpleNamespace(second_person_enabled=True)

    table = mod._build_household_retirement_table(husband, wife, cfg)

    assert table["columns"] == ["Field", "Husband", "Wife", "Total"]
    salary_row = next(row for row in table["rows"] if row[0] == "Salary / Wages")
    assert salary_row == ["Salary / Wages", "$100", "$200", "$300"]


def test_build_expense_rows_supports_get_expenses_and_ongoing_end_year():
    class Expenses:
        def get_expenses(self):
            return [
                {
                    "start_year": 2025,
                    "end_year": None,
                    "cost": 1000.0,
                    "comment": "",
                },
                {
                    "start_year": 2030,
                    "end_year": 2032,
                    "cost": 2000.0,
                    "comment": "Car",
                },
            ]

    rows = mod._build_expense_rows(Expenses())

    assert rows == [
        {
            "Description": "Expense",
            "Start Year": 2025,
            "End Year": "Ongoing",
            "Annual Amount": 1000.0,
        },
        {
            "Description": "Car",
            "Start Year": 2030,
            "End Year": 2032,
            "Annual Amount": 2000.0,
        },
    ]


def test_build_assumptions_summary_includes_tax_assumptions_and_payroll_flag():
    husband = SimpleNamespace(
        age=60,
        retire_age=65,
        income=100.0,
        ss=20.0,
        ss_age=67,
        pension=0.0,
        pension_age=65,
        annuity=0.0,
        annuity_age=70,
        annual_401k_contribution=10.0,
        annual_employer_match=5.0,
    )
    wife = SimpleNamespace(
        age=58,
        retire_age=64,
        income=0.0,
        ss=0.0,
        ss_age=67,
        pension=0.0,
        pension_age=65,
        annuity=0.0,
        annuity_age=70,
        annual_401k_contribution=0.0,
        annual_employer_match=0.0,
    )
    husband_portfolio = SimpleNamespace(
        equity_pre=100.0,
        equity_post=200.0,
        bond_pre=0.0,
        bond_post=0.0,
        cash_pre=0.0,
        cash_post=0.0,
        real_estate=0.0,
    )
    wife_portfolio = SimpleNamespace(
        equity_pre=0.0,
        equity_post=0.0,
        bond_pre=0.0,
        bond_post=0.0,
        cash_pre=0.0,
        cash_post=0.0,
        real_estate=0.0,
    )
    expenses = [
        {
            "start_year": 2025,
            "end_year": None,
            "cost": 1000.0,
            "comment": "Base expense",
        }
    ]
    cfg = SimpleNamespace(
        second_person_enabled=False,
        use_fund_expenses=False,
        fund_expense=0.0,
        sim_initial_allocation_mode="none",
        rebalance_every_year=False,
        always_use_expense_mode=True,
        retirement_withdraw_mode="Off",
        scenario_expense_multiplier=1.0,
        sequence_risk_enabled=False,
        inflation_rate=0.03,
        eq_mean=0.07,
        bd_mean=0.03,
        cs_mean=0.01,
        re_mean=0.04,
        eq_std=0.15,
        bd_std=0.05,
        cs_std=0.01,
        re_std=0.10,
        tax_filing_status="Single",
        calculate_income_taxes=True,
        calculate_payroll_taxes=False,
        calculate_state_taxes=True,
        state_of_residence="NM",
        include_rmd=False,
    )

    assumptions = mod._build_assumptions_summary(
        husband,
        wife,
        husband_portfolio,
        wife_portfolio,
        expenses,
        cfg,
        report_options={},
    )

    tax_assumptions = assumptions["Tax Assumptions"]
    assert tax_assumptions["Tax Filing Status"] == "Single"
    assert tax_assumptions["Calculate Income Taxes"] is True
    assert tax_assumptions["Calculate Payroll Taxes"] is False
    assert tax_assumptions["Calculate State Taxes"] is True
    assert tax_assumptions["State of Residence"] == "NM"

    assert "Household & Retirement" in assumptions
    assert "Portfolio Inputs" in assumptions
    assert "Expense Inputs" in assumptions
    assert "Market & Inflation Assumptions" in assumptions
