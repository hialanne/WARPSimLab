import types
import pytest

from src.warpsimlab.sim.engines.incomeEngine import (
    calculate_income,
    initialize_income_engine_for_simulation,
    calculate_income_breakdown,
    calculate_social_security,
    calculate_pre_tax_401k_contributions,
    apply_employee_401k_to_income,
)


def make_person(
    *,
    age=40,
    retire_age=65,
    income=100000.0,
    ss_age=67,
    ss=20000.0,
    pension_age=65,
    pension=12000.0,
    pension_inflation_adjustment_pct=0.0,
    annuity_age=70,
    annuity=5000.0,
    annual_401k_contribution=10000.0,
    annual_employer_match=5000.0,
):
    return types.SimpleNamespace(
        age=age,
        retire_age=retire_age,
        income=income,
        ss_age=ss_age,
        ss=ss,
        pension_age=pension_age,
        pension=pension,
        pension_inflation_adjustment_pct=pension_inflation_adjustment_pct,
        annuity_age=annuity_age,
        annuity=annuity,
        annual_401k_contribution=annual_401k_contribution,
        annual_employer_match=annual_employer_match,
    )


def make_config(
    *,
    inflation_rate=0.0,
    second_person_enabled=False,
    years_to_simulate=10,
):
    return types.SimpleNamespace(
        inflation_rate=inflation_rate,
        second_person_enabled=second_person_enabled,
        years_to_simulate=years_to_simulate,
        subplot_mode="standard",
        sim_type="cashflow_sim",
        monte_carlo_mode="pathBasedAnnualSampling",
    )


def init_income(husband, wife, sim_config):
    initialize_income_engine_for_simulation(husband, wife, sim_config)
    return sim_config


# -------------------------
# calculate_income
# -------------------------

def test_calculate_income_husband_work_only_inflation_adjusted():
    husband = make_person(
        age=40, retire_age=65, income=100.0, ss=0.0, pension=0.0, annuity=0.0
    )
    wife = make_person(
        age=40, retire_age=65, income=999.0, ss=0.0, pension=0.0, annuity=0.0
    )
    sim_config = make_config(inflation_rate=0.10, second_person_enabled=False)
    init_income(husband, wife, sim_config)

    total = calculate_income(
        husband,
        wife,
        curr_husband_age=42,
        curr_wife_age=0,
        rmd_h=0.0,
        rmd_w=0.0,
        year=2,
        sim_config=sim_config,
    )

    assert total == pytest.approx(100.0 * (1.10 ** 2))


def test_calculate_income_includes_husband_rmd_and_ignores_wife_when_disabled():
    husband = make_person(income=0.0, ss=0.0, pension=0.0, annuity=0.0)
    wife = make_person(income=0.0, ss=0.0, pension=0.0, annuity=0.0)
    sim_config = make_config(inflation_rate=0.25, second_person_enabled=False)
    init_income(husband, wife, sim_config)

    total = calculate_income(
        husband,
        wife,
        curr_husband_age=80,
        curr_wife_age=80,
        rmd_h=1234.5,
        rmd_w=9999.9,
        year=5,
        sim_config=sim_config,
    )

    assert total == pytest.approx(1234.5)


@pytest.mark.parametrize(
    "curr_age, ss_age, expected_receives_ss",
    [
        (66, 67, False),
        (67, 67, True),
        (69, 67, True),
        (69, 75, False),
        (70, 75, True),
    ],
)
def test_calculate_income_social_security_start_rule(curr_age, ss_age, expected_receives_ss):
    husband = make_person(
        income=0.0,
        ss_age=ss_age,
        ss=100.0,
        pension=0.0,
        annuity=0.0,
        retire_age=0,
    )
    wife = make_person(
        income=0.0,
        ss_age=ss_age,
        ss=100.0,
        pension=0.0,
        annuity=0.0,
        retire_age=0,
    )
    sim_config = make_config(inflation_rate=0.0, second_person_enabled=False)
    init_income(husband, wife, sim_config)

    total = calculate_income(
        husband,
        wife,
        curr_husband_age=curr_age,
        curr_wife_age=0,
        rmd_h=0.0,
        rmd_w=0.0,
        year=1,
        sim_config=sim_config,
    )

    if expected_receives_ss:
        assert total == pytest.approx(100.0)
    else:
        assert total == pytest.approx(0.0)


def test_calculate_income_pension_inflation_adjustment_uses_pct_of_inflation_rate():
    husband = make_person(
        income=0.0,
        ss=0.0,
        annuity=0.0,
        pension_age=60,
        pension=100.0,
        pension_inflation_adjustment_pct=50.0,
        retire_age=0,
    )
    wife = make_person(income=0.0, ss=0.0, pension=0.0, annuity=0.0)
    sim_config = make_config(inflation_rate=0.10, second_person_enabled=False)
    init_income(husband, wife, sim_config)

    total = calculate_income(
        husband,
        wife,
        curr_husband_age=65,
        curr_wife_age=0,
        rmd_h=0.0,
        rmd_w=0.0,
        year=3,
        sim_config=sim_config,
    )

    assert total == pytest.approx(100.0 * (1.05 ** 3))


def test_calculate_income_annuity_not_inflation_adjusted():
    husband = make_person(
        income=0.0,
        ss=0.0,
        pension=0.0,
        annuity_age=60,
        annuity=100.0,
        retire_age=0,
    )
    wife = make_person(income=0.0, ss=0.0, pension=0.0, annuity=0.0)
    sim_config = make_config(inflation_rate=0.50, second_person_enabled=False)
    init_income(husband, wife, sim_config)

    total = calculate_income(
        husband,
        wife,
        curr_husband_age=70,
        curr_wife_age=0,
        rmd_h=0.0,
        rmd_w=0.0,
        year=10,
        sim_config=sim_config,
    )

    assert total == pytest.approx(100.0)


def test_calculate_income_second_person_enabled_includes_wife_income():
    husband = make_person(
        age=40, retire_age=65, income=100.0, ss=0.0, pension=0.0, annuity=0.0
    )
    wife = make_person(
        age=40, retire_age=65, income=200.0, ss=0.0, pension=0.0, annuity=0.0
    )
    sim_config = make_config(inflation_rate=0.0, second_person_enabled=True)
    init_income(husband, wife, sim_config)

    total = calculate_income(
        husband,
        wife,
        curr_husband_age=50,
        curr_wife_age=50,
        rmd_h=0.0,
        rmd_w=0.0,
        year=1,
        sim_config=sim_config,
    )

    assert total == pytest.approx(300.0)


def test_calculate_income_combines_all_enabled_income_classes_for_both_people():
    husband = make_person(
        retire_age=65,
        income=100.0,
        ss_age=67,
        ss=20.0,
        pension_age=60,
        pension=30.0,
        pension_inflation_adjustment_pct=100.0,
        annuity_age=70,
        annuity=40.0,
    )
    wife = make_person(
        retire_age=65,
        income=200.0,
        ss_age=66,
        ss=50.0,
        pension_age=62,
        pension=60.0,
        pension_inflation_adjustment_pct=50.0,
        annuity_age=68,
        annuity=70.0,
    )
    sim_config = make_config(inflation_rate=0.10, second_person_enabled=True)
    init_income(husband, wife, sim_config)

    total = calculate_income(
        husband,
        wife,
        curr_husband_age=70,
        curr_wife_age=69,
        rmd_h=11.0,
        rmd_w=13.0,
        year=2,
        sim_config=sim_config,
    )

    expected_h = (
        20.0 * (1.10 ** 2)
        + 30.0 * (1.10 ** 2)
        + 40.0
        + 11.0
    )
    expected_w = (
        50.0 * (1.10 ** 2)
        + 60.0 * (1.05 ** 2)
        + 70.0
        + 13.0
    )

    assert total == pytest.approx(expected_h + expected_w)


# -------------------------
# calculate_income_breakdown
# -------------------------

def test_income_breakdown_sums_by_class_and_tracks_by_person():
    husband = make_person(
        income=100.0,
        retire_age=65,
        ss_age=67,
        ss=10.0,
        pension_age=60,
        pension=20.0,
        pension_inflation_adjustment_pct=0.0,
        annuity_age=70,
        annuity=30.0,
        age=60,
    )
    wife = make_person(
        income=200.0,
        retire_age=65,
        ss_age=67,
        ss=40.0,
        pension_age=60,
        pension=50.0,
        pension_inflation_adjustment_pct=0.0,
        annuity_age=70,
        annuity=60.0,
        age=60,
    )
    sim_config = make_config(
        inflation_rate=0.0,
        second_person_enabled=True,
        years_to_simulate=10,
    )
    init_income(husband, wife, sim_config)

    rmd_h = 7.0
    rmd_w = 11.0

    out = calculate_income_breakdown(
        husband,
        wife,
        curr_husband_age=62,
        curr_wife_age=62,
        rmd_h=rmd_h,
        rmd_w=rmd_w,
        year=2,
        sim_config=sim_config,
    )

    assert set(out.keys()) == {
        "total",
        "by_class",
        "by_person",
        "non_taxable_income",
        "work_by_person",
    }

    assert set(out["by_class"].keys()) == {
        "work",
        "pension",
        "annuity",
        "ss",
        "rmd",
        "withdrawal",
        "bond_interest",
        "cash_interest",
        "qualified_dividends",
        "special_income",
    }

    assert out["by_class"]["special_income"] == pytest.approx(0.0)
    assert out["non_taxable_income"] == pytest.approx(0.0)
    assert out["by_class"]["work"] == pytest.approx(100.0 + 200.0)
    assert out["by_class"]["pension"] == pytest.approx(20.0 + 50.0)
    assert out["by_class"]["ss"] == pytest.approx(0.0)
    assert out["by_class"]["annuity"] == pytest.approx(0.0)
    assert out["by_class"]["rmd"] == pytest.approx(rmd_h + rmd_w)
    assert out["by_class"]["withdrawal"] == pytest.approx(0.0)
    assert out["by_class"]["bond_interest"] == pytest.approx(0.0)
    assert out["by_class"]["cash_interest"] == pytest.approx(0.0)
    assert out["by_class"]["qualified_dividends"] == pytest.approx(0.0)

    assert out["by_person"]["husband"] == pytest.approx(100.0 + 20.0 + rmd_h)
    assert out["by_person"]["wife"] == pytest.approx(200.0 + 50.0 + rmd_w)

    expected_total = sum(out["by_class"].values())
    assert out["total"] == pytest.approx(expected_total)


def test_income_breakdown_inflation_applies_to_work_ss_and_configured_pension():
    husband = make_person(
        income=100.0,
        retire_age=75,
        ss_age=67,
        ss=20.0,
        pension_age=60,
        pension=30.0,
        pension_inflation_adjustment_pct=50.0,
        annuity_age=70,
        annuity=40.0,
    )
    wife = make_person(
        income=0.0,
        ss=0.0,
        pension=0.0,
        annuity=0.0,
    )
    sim_config = make_config(
        inflation_rate=0.10,
        second_person_enabled=False,
        years_to_simulate=10,
    )
    init_income(husband, wife, sim_config)

    out = calculate_income_breakdown(
        husband,
        wife,
        curr_husband_age=70,
        curr_wife_age=0,
        rmd_h=5.0,
        rmd_w=0.0,
        year=2,
        sim_config=sim_config,
    )

    assert out["by_class"]["work"] == pytest.approx(100.0 * (1.10 ** 2))
    assert out["by_class"]["ss"] == pytest.approx(20.0 * (1.10 ** 2))
    assert out["by_class"]["pension"] == pytest.approx(30.0 * (1.05 ** 2))
    assert out["by_class"]["annuity"] == pytest.approx(40.0)
    assert out["by_class"]["rmd"] == pytest.approx(5.0)

    expected_husband = (
        100.0 * (1.10 ** 2)
        + 20.0 * (1.10 ** 2)
        + 30.0 * (1.05 ** 2)
        + 40.0
        + 5.0
    )
    assert out["by_person"]["husband"] == pytest.approx(expected_husband)
    assert out["by_person"]["wife"] == pytest.approx(0.0)
    assert out["total"] == pytest.approx(sum(out["by_class"].values()))


def test_income_breakdown_second_person_disabled_should_ignore_wife_rmd_everywhere():
    husband = make_person(income=0.0, ss=0.0, pension=0.0, annuity=0.0)
    wife = make_person(income=0.0, ss=0.0, pension=0.0, annuity=0.0)
    sim_config = make_config(
        inflation_rate=0.0,
        second_person_enabled=False,
        years_to_simulate=10,
    )
    init_income(husband, wife, sim_config)

    out = calculate_income_breakdown(
        husband,
        wife,
        curr_husband_age=80,
        curr_wife_age=80,
        rmd_h=100.0,
        rmd_w=200.0,
        year=0,
        sim_config=sim_config,
    )

    assert out["by_person"]["husband"] == pytest.approx(100.0)
    assert out["by_person"]["wife"] == pytest.approx(0.0)
    assert out["by_class"]["rmd"] == pytest.approx(100.0)
    assert out["total"] == pytest.approx(100.0)


# -------------------------
# calculate_social_security
# -------------------------

def test_calculate_social_security_matches_min_rule_and_inflation():
    husband = make_person(
        age=68,
        ss_age=67,
        ss=100.0,
        income=0.0,
        pension=0.0,
        annuity=0.0,
        retire_age=0,
    )
    wife = make_person(
        age=69,
        ss_age=75,
        ss=200.0,
        income=0.0,
        pension=0.0,
        annuity=0.0,
        retire_age=0,
    )
    sim_config = make_config(inflation_rate=0.10, second_person_enabled=True)
    init_income(husband, wife, sim_config)

    h_ss, w_ss = calculate_social_security(husband, wife, year=1, sim_config=sim_config)

    assert h_ss == pytest.approx(100.0 * 1.10)
    assert w_ss == pytest.approx(200.0 * 1.10)


def test_calculate_social_security_returns_zero_for_disabled_wife():
    husband = make_person(
        age=70, ss_age=67, ss=100.0, income=0.0, pension=0.0, annuity=0.0, retire_age=0
    )
    wife = make_person(
        age=90, ss_age=60, ss=999.0, income=0.0, pension=0.0, annuity=0.0, retire_age=0
    )
    sim_config = make_config(inflation_rate=0.0, second_person_enabled=False)
    init_income(husband, wife, sim_config)

    h_ss, w_ss = calculate_social_security(husband, wife, year=0, sim_config=sim_config)

    assert h_ss == pytest.approx(100.0)
    assert w_ss == pytest.approx(0.0)


# -------------------------
# calculate_pre_tax_401k_contributions
# -------------------------

def test_calculate_pre_tax_401k_contributions_inflated_until_retirement():
    person = make_person(
        age=40,
        retire_age=65,
        annual_401k_contribution=100.0,
        annual_employer_match=50.0,
        income=1000.0,
        ss=0.0,
        pension=0.0,
        annuity=0.0,
    )
    husband = person
    wife = make_person(income=0.0, ss=0.0, pension=0.0, annuity=0.0)
    sim_config = make_config(inflation_rate=0.10, second_person_enabled=False)
    init_income(husband, wife, sim_config)

    employee, employer = calculate_pre_tax_401k_contributions(
        person, current_age=50, year=2, sim_config=sim_config
    )
    assert employee == pytest.approx(100.0 * (1.10 ** 2))
    assert employer == pytest.approx(50.0 * (1.10 ** 2))

    employee2, employer2 = calculate_pre_tax_401k_contributions(
        person, current_age=65, year=2, sim_config=sim_config
    )
    assert employee2 == pytest.approx(0.0)
    assert employer2 == pytest.approx(0.0)


def test_calculate_pre_tax_401k_contributions_zero_when_retired():
    person = make_person(
        retire_age=60,
        annual_401k_contribution=123.0,
        annual_employer_match=45.0,
    )
    husband = person
    wife = make_person(income=0.0, ss=0.0, pension=0.0, annuity=0.0)
    sim_config = make_config(inflation_rate=0.10)
    init_income(husband, wife, sim_config)

    employee, employer = calculate_pre_tax_401k_contributions(
        person, current_age=75, year=10, sim_config=sim_config
    )

    assert employee == pytest.approx(0.0)
    assert employer == pytest.approx(0.0)


def test_calculate_pre_tax_401k_contributions_employee_capped_by_current_work_income():
    person = make_person(
        retire_age=65,
        income=100.0,
        annual_401k_contribution=250.0,
        annual_employer_match=50.0,
        ss=0.0,
        pension=0.0,
        annuity=0.0,
    )
    husband = person
    wife = make_person(income=0.0, ss=0.0, pension=0.0, annuity=0.0)
    sim_config = make_config(inflation_rate=0.0)
    init_income(husband, wife, sim_config)

    employee, employer = calculate_pre_tax_401k_contributions(
        person, current_age=50, year=0, sim_config=sim_config
    )

    assert employee == pytest.approx(100.0)
    assert employer == pytest.approx(50.0)


def test_calculate_pre_tax_401k_contributions_employer_zero_when_employee_zero():
    person = make_person(
        retire_age=65,
        income=0.0,
        annual_401k_contribution=100.0,
        annual_employer_match=50.0,
        ss=0.0,
        pension=0.0,
        annuity=0.0,
    )
    husband = person
    wife = make_person(income=0.0, ss=0.0, pension=0.0, annuity=0.0)
    sim_config = make_config(inflation_rate=0.0)
    init_income(husband, wife, sim_config)

    employee, employer = calculate_pre_tax_401k_contributions(
        person, current_age=50, year=0, sim_config=sim_config
    )

    assert employee == pytest.approx(0.0)
    assert employer == pytest.approx(0.0)


# -------------------------
# apply_employee_401k_to_income
# -------------------------

def test_apply_employee_401k_to_income_mutates_expected_fields():
    gross_income = {
        "total": 1000.0,
        "by_person": {"husband": 600.0, "wife": 400.0},
        "by_class": {
            "work": 1000.0,
            "pension": 0.0,
            "annuity": 0.0,
            "ss": 0.0,
            "rmd": 0.0,
            "withdrawal": 0.0,
            "bond_interest": 0.0,
            "cash_interest": 0.0,
            "qualified_dividends": 0.0,
        },
    }

    apply_employee_401k_to_income(
        gross_income, employee_contribution=100.0, person_key="husband"
    )

    assert gross_income["total"] == pytest.approx(900.0)
    assert gross_income["by_person"]["husband"] == pytest.approx(500.0)
    assert gross_income["by_person"]["wife"] == pytest.approx(400.0)
    assert gross_income["by_class"]["work"] == pytest.approx(900.0)

    assert gross_income["by_class"]["pension"] == pytest.approx(0.0)
    assert gross_income["by_class"]["annuity"] == pytest.approx(0.0)
    assert gross_income["by_class"]["ss"] == pytest.approx(0.0)
    assert gross_income["by_class"]["rmd"] == pytest.approx(0.0)
    assert gross_income["by_class"]["withdrawal"] == pytest.approx(0.0)
    assert gross_income["by_class"]["bond_interest"] == pytest.approx(0.0)
    assert gross_income["by_class"]["cash_interest"] == pytest.approx(0.0)
    assert gross_income["by_class"]["qualified_dividends"] == pytest.approx(0.0)


def test_apply_employee_401k_to_income_noop_when_nonpositive():
    gross_income = {
        "total": 1000.0,
        "by_person": {"husband": 600.0, "wife": 400.0},
        "by_class": {
            "work": 1000.0,
            "pension": 0.0,
            "annuity": 0.0,
            "ss": 0.0,
            "rmd": 0.0,
            "withdrawal": 0.0,
            "bond_interest": 0.0,
            "cash_interest": 0.0,
            "qualified_dividends": 0.0,
        },
    }

    apply_employee_401k_to_income(
        gross_income, employee_contribution=0.0, person_key="husband"
    )

    assert gross_income["total"] == pytest.approx(1000.0)
    assert gross_income["by_person"]["husband"] == pytest.approx(600.0)
    assert gross_income["by_person"]["wife"] == pytest.approx(400.0)
    assert gross_income["by_class"]["work"] == pytest.approx(1000.0)
    assert gross_income["by_class"]["pension"] == pytest.approx(0.0)
    assert gross_income["by_class"]["annuity"] == pytest.approx(0.0)
    assert gross_income["by_class"]["ss"] == pytest.approx(0.0)
    assert gross_income["by_class"]["rmd"] == pytest.approx(0.0)
    assert gross_income["by_class"]["withdrawal"] == pytest.approx(0.0)
    assert gross_income["by_class"]["bond_interest"] == pytest.approx(0.0)
    assert gross_income["by_class"]["cash_interest"] == pytest.approx(0.0)
    assert gross_income["by_class"]["qualified_dividends"] == pytest.approx(0.0)