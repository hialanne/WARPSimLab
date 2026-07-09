import types
import pytest

from src.warpsimlab.sim.engines import taxEngine


def make_config(
    *,
    years_to_simulate=5,
    inflation_rate=0.0,
    calculate_income_taxes=True,
    calculate_state_taxes=False,
    tax_filing_status="Single",
    state_of_residence=None,
):
    return types.SimpleNamespace(
        years_to_simulate=years_to_simulate,
        inflation_rate=inflation_rate,
        calculate_income_taxes=calculate_income_taxes,
        calculate_state_taxes=calculate_state_taxes,
        tax_filing_status=tax_filing_status,
        state_of_residence=state_of_residence,

        subplot_mode="standard",
        sim_type="cashflow_sim",
        monte_carlo_mode="pathBasedAnnualSampling",
    )


def init_year(cfg, year):
    taxEngine.initialize_tax_engine_for_simulation(cfg)
    return taxEngine.prepare_tax_year_cache(year, cfg)


# -------------------------
# allocate_tax_proportionally
# -------------------------

def test_allocate_tax_proportionally_zero_income_or_zero_tax_returns_zeros():
    out = taxEngine.allocate_tax_proportionally(
        total_tax=100.0,
        by_person_income={"husband": 0.0, "wife": 0.0},
    )
    assert out == {"husband": 0.0, "wife": 0.0}

    out2 = taxEngine.allocate_tax_proportionally(
        total_tax=0.0,
        by_person_income={"husband": 100.0, "wife": 50.0},
    )
    assert out2 == {"husband": 0.0, "wife": 0.0}


def test_allocate_tax_proportionally_sums_to_total_and_is_proportional():
    out = taxEngine.allocate_tax_proportionally(
        total_tax=300.0,
        by_person_income={"husband": 200.0, "wife": 100.0},
    )
    assert out["husband"] == pytest.approx(200.0)
    assert out["wife"] == pytest.approx(100.0)
    assert out["husband"] + out["wife"] == pytest.approx(300.0)


# -------------------------
# Federal ordinary income tax
# -------------------------

def test_federal_tax_single_below_standard_deduction_is_zero():
    cfg = make_config(
        tax_filing_status="Single",
        inflation_rate=0.0,
        calculate_income_taxes=True,
    )
    year_cache = init_year(cfg, 0)

    tax, marginal_rate = taxEngine.calculate_us_federal_income_tax(16100.0, year_cache)
    assert tax == pytest.approx(0.0)
    assert marginal_rate == pytest.approx(0.0)


def test_federal_tax_single_first_bracket_exact():
    cfg = make_config(
        tax_filing_status="Single",
        inflation_rate=0.0,
        calculate_income_taxes=True,
    )
    year_cache = init_year(cfg, 0)

    total_income = 16100.0 + 12400.0
    tax, marginal_rate = taxEngine.calculate_us_federal_income_tax(total_income, year_cache)
    assert tax == pytest.approx(12400.0 * 0.10)
    assert marginal_rate == pytest.approx(0.10)


def test_federal_tax_single_second_bracket_edge():
    cfg = make_config(
        tax_filing_status="Single",
        inflation_rate=0.0,
        calculate_income_taxes=True,
    )
    year_cache = init_year(cfg, 0)

    total_income = 16100.0 + 50400.0
    expected = 12400.0 * 0.10 + (50400.0 - 12400.0) * 0.12

    tax, marginal_rate = taxEngine.calculate_us_federal_income_tax(total_income, year_cache)
    assert tax == pytest.approx(expected)
    assert marginal_rate == pytest.approx(0.12)


def test_federal_tax_married_below_standard_deduction_is_zero():
    cfg = make_config(
        tax_filing_status="Married Filing Jointly",
        inflation_rate=0.0,
        calculate_income_taxes=True,
    )
    year_cache = init_year(cfg, 0)

    tax, marginal_rate = taxEngine.calculate_us_federal_income_tax(32200.0, year_cache)
    assert tax == pytest.approx(0.0)
    assert marginal_rate == pytest.approx(0.0)


def test_federal_tax_inflation_adjusts_deduction_and_brackets():
    cfg = make_config(
        tax_filing_status="Single",
        inflation_rate=0.10,
        calculate_income_taxes=True,
    )
    year_cache = init_year(cfg, 1)

    standard = 16100.0 * 1.10
    taxable = 12400.0 * 1.10
    total_income = standard + taxable

    tax, marginal_rate = taxEngine.calculate_us_federal_income_tax(total_income, year_cache)
    assert tax == pytest.approx(taxable * 0.10)
    assert marginal_rate == pytest.approx(0.10)


def test_federal_tax_negative_income_is_zero():
    cfg = make_config(
        tax_filing_status="Single",
        inflation_rate=0.0,
        calculate_income_taxes=True,
    )
    year_cache = init_year(cfg, 0)

    tax, marginal_rate = taxEngine.calculate_us_federal_income_tax(-1000.0, year_cache)
    assert tax == pytest.approx(0.0)
    assert marginal_rate == pytest.approx(0.0)


# -------------------------
# Qualified dividend tax
# -------------------------

def test_qualified_dividend_tax_zero_when_no_dividends():
    cfg = make_config(
        tax_filing_status="Single",
        inflation_rate=0.0,
        calculate_income_taxes=True,
    )
    year_cache = init_year(cfg, 0)

    tax = taxEngine.calculate_us_federal_qualified_dividend_tax(
        ordinary_income=50000.0,
        qualified_dividends=0.0,
        year_cache=year_cache,
    )
    assert tax == pytest.approx(0.0)


def test_qualified_dividend_tax_single_all_in_zero_percent_band():
    cfg = make_config(
        tax_filing_status="Single",
        inflation_rate=0.0,
        calculate_income_taxes=True,
    )
    year_cache = init_year(cfg, 0)

    tax = taxEngine.calculate_us_federal_qualified_dividend_tax(
        ordinary_income=30000.0,
        qualified_dividends=10000.0,
        year_cache=year_cache,
    )
    assert tax == pytest.approx(0.0)


def test_qualified_dividend_tax_single_crosses_from_zero_to_fifteen_percent():
    cfg = make_config(
        tax_filing_status="Single",
        inflation_rate=0.0,
        calculate_income_taxes=True,
    )
    year_cache = init_year(cfg, 0)

    qualified_dividends = 30000.0
    expected = (qualified_dividends - 24450.0) * 0.15

    tax = taxEngine.calculate_us_federal_qualified_dividend_tax(
        ordinary_income=40000.0,
        qualified_dividends=qualified_dividends,
        year_cache=year_cache,
    )
    assert tax == pytest.approx(expected)


def test_qualified_dividend_tax_single_crosses_into_twenty_percent_band():
    cfg = make_config(
        tax_filing_status="Single",
        inflation_rate=0.0,
        calculate_income_taxes=True,
    )
    year_cache = init_year(cfg, 0)

    tax = taxEngine.calculate_us_federal_qualified_dividend_tax(
        ordinary_income=600000.0,
        qualified_dividends=10000.0,
        year_cache=year_cache,
    )
    assert tax == pytest.approx(10000.0 * 0.20)


# -------------------------
# State income tax
# -------------------------

def test_state_tax_missing_or_none_state_is_zero():
    cfg = make_config(
        calculate_state_taxes=True,
        state_of_residence=None,
    )
    year_cache = init_year(cfg, 0)
    assert taxEngine.calculate_state_income_tax(
        total_income=100000.0,
        year_cache=year_cache,
        sim_config=cfg,
    ) == pytest.approx(0.0)

    cfg2 = make_config(
        calculate_state_taxes=True,
        state_of_residence="AK",
    )
    year_cache2 = init_year(cfg2, 0)
    assert taxEngine.calculate_state_income_tax(
        total_income=100000.0,
        year_cache=year_cache2,
        sim_config=cfg2,
    ) == pytest.approx(0.0)


def test_state_tax_flat_state_colorado():
    cfg = make_config(
        calculate_state_taxes=True,
        state_of_residence="CO",
    )
    year_cache = init_year(cfg, 0)

    tax = taxEngine.calculate_state_income_tax(
        total_income=100000.0,
        year_cache=year_cache,
        sim_config=cfg,
    )
    assert tax == pytest.approx(100000.0 * 0.044)


def test_state_tax_progressive_alabama_single_year0():
    cfg = make_config(
        calculate_state_taxes=True,
        state_of_residence="AL",
        tax_filing_status="Single",
        inflation_rate=0.0,
    )
    year_cache = init_year(cfg, 0)

    income = 10000.0
    expected = (
        500.0 * 0.02
        + (3000.0 - 500.0) * 0.04
        + (10000.0 - 3000.0) * 0.05
    )

    tax = taxEngine.calculate_state_income_tax(
        total_income=income,
        year_cache=year_cache,
        sim_config=cfg,
    )
    assert tax == pytest.approx(expected)


def test_state_tax_progressive_inflates_brackets():
    cfg = make_config(
        calculate_state_taxes=True,
        state_of_residence="AL",
        tax_filing_status="Single",
        inflation_rate=0.10,
    )
    year_cache = init_year(cfg, 1)

    income = 10000.0
    upper1 = 500.0 * 1.10
    upper2 = 3000.0 * 1.10

    expected = (
        upper1 * 0.02
        + (upper2 - upper1) * 0.04
        + (income - upper2) * 0.05
    )

    tax = taxEngine.calculate_state_income_tax(
        total_income=income,
        year_cache=year_cache,
        sim_config=cfg,
    )
    assert tax == pytest.approx(expected)


# -------------------------
# Total split tax calculation
# -------------------------

def test_total_income_tax_split_returns_all_zero_when_flags_off():
    cfg = make_config(
        calculate_income_taxes=False,
        calculate_state_taxes=False,
        tax_filing_status="Single",
    )
    year_cache = init_year(cfg, 0)

    federal_ordinary_tax, federal_qualified_dividend_tax, state_income_tax, total_tax, federal_marginal_rate = (
        taxEngine.calculate_total_income_tax_split(
            ordinary_income=999999.0,
            qualified_dividends=50000.0,
            year_cache=year_cache,
            sim_config=cfg,
        )
    )

    assert federal_ordinary_tax == pytest.approx(0.0)
    assert federal_qualified_dividend_tax == pytest.approx(0.0)
    assert state_income_tax == pytest.approx(0.0)
    assert total_tax == pytest.approx(0.0)
    assert federal_marginal_rate == pytest.approx(0.0)


def test_total_income_tax_split_federal_only():
    cfg = make_config(
        calculate_income_taxes=True,
        calculate_state_taxes=False,
        tax_filing_status="Single",
    )
    year_cache = init_year(cfg, 0)

    federal_ordinary_tax, federal_qualified_dividend_tax, state_income_tax, total_tax, federal_marginal_rate = (
        taxEngine.calculate_total_income_tax_split(
            ordinary_income=16100.0 + 12400.0,
            qualified_dividends=0.0,
            year_cache=year_cache,
            sim_config=cfg,
        )
    )

    assert federal_ordinary_tax == pytest.approx(12400.0 * 0.10)
    assert federal_qualified_dividend_tax == pytest.approx(0.0)
    assert state_income_tax == pytest.approx(0.0)
    assert total_tax == pytest.approx(12400.0 * 0.10)
    assert federal_marginal_rate == pytest.approx(0.10)


def test_total_income_tax_split_state_only():
    cfg = make_config(
        calculate_income_taxes=False,
        calculate_state_taxes=True,
        state_of_residence="CO",
    )
    year_cache = init_year(cfg, 0)

    federal_ordinary_tax, federal_qualified_dividend_tax, state_income_tax, total_tax, federal_marginal_rate = (
        taxEngine.calculate_total_income_tax_split(
            ordinary_income=90000.0,
            qualified_dividends=10000.0,
            year_cache=year_cache,
            sim_config=cfg,
        )
    )

    expected_state_tax = (90000.0 + 10000.0) * 0.044

    assert federal_ordinary_tax == pytest.approx(0.0)
    assert federal_qualified_dividend_tax == pytest.approx(0.0)
    assert state_income_tax == pytest.approx(expected_state_tax)
    assert total_tax == pytest.approx(expected_state_tax)
    assert federal_marginal_rate == pytest.approx(0.0)


def test_total_income_tax_split_negative_inputs_raise_runtime_error():
    cfg = make_config(
        calculate_income_taxes=True,
        calculate_state_taxes=True,
        tax_filing_status="Single",
        state_of_residence="CO",
    )
    year_cache = init_year(cfg, 0)

    with pytest.raises(RuntimeError, match="negative income inputs"):
        taxEngine.calculate_total_income_tax_split(
            ordinary_income=-100.0,
            qualified_dividends=-50.0,
            year_cache=year_cache,
            sim_config=cfg,
        )


# -------------------------
# Marginal federal rate
# -------------------------

def test_get_us_federal_marginal_tax_rate_none_when_disabled():
    cfg = make_config(calculate_income_taxes=False)
    assert taxEngine.get_us_federal_marginal_tax_rate(
        total_income=100000.0,
        year=0,
        sim_config=cfg,
    ) is None


def test_get_us_federal_marginal_tax_rate_single_known_bracket():
    cfg = make_config(
        calculate_income_taxes=True,
        tax_filing_status="Single",
        inflation_rate=0.0,
    )
    taxEngine.initialize_tax_engine_for_simulation(cfg)

    total_income = 16100.0 + 60000.0

    rate = taxEngine.get_us_federal_marginal_tax_rate(
        total_income=total_income,
        year=0,
        sim_config=cfg,
    )
    assert rate == pytest.approx(0.22)


def test_get_us_federal_marginal_tax_rate_single_below_deduction_is_ten_percent():
    cfg = make_config(
        calculate_income_taxes=True,
        tax_filing_status="Single",
        inflation_rate=0.0,
    )
    taxEngine.initialize_tax_engine_for_simulation(cfg)

    rate = taxEngine.get_us_federal_marginal_tax_rate(
        total_income=10000.0,
        year=0,
        sim_config=cfg,
    )
    assert rate == pytest.approx(0.10)
