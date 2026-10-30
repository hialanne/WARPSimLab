from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from src.warpsimlab.sim import run_sim_tax_report as mod


def test_lifetime_tax_summary_uses_ratio_of_totals_and_excludes_opening_bill():
    summary = mod._build_lifetime_tax_summary({
        "federal_ordinary_tax": [0, 100, 300], "federal_qualified_dividend_tax": [0, 10, 20],
        "state_income_tax": [0, 20, 30], "payroll_tax": [0, 40, 50],
        "taxes": [0, 170, 400], "gross_income": [0, 1000, 3000],
        "tax_bracket": [0, .12, .22]})
    assert summary["Lifetime Federal Income Tax"] == 430
    assert summary["Lifetime Total Tax"] == 570
    assert summary["Average Effective Tax Rate"] == pytest.approx(570 / 4000)
    assert summary["Highest Annual Tax Bill"] == 400
    assert summary["Lowest Annual Tax Bill"] == 170
    assert summary["Highest Marginal Tax Bracket"] == .22
    assert mod._build_lifetime_tax_summary({})["Average Effective Tax Rate"] == 0


def test_rmd_first_positive_year_and_account_balance_summaries():
    results = {"year": [2025, 2026, 2027], "rmd": [0, 100, 300],
               "rmd_husband": [0, 100, 100], "rmd_wife": [0, 0, 200],
               "roth_assets": [500, 600, 700], "roth_conversions": [0, 50, 75],
               "hsa_assets": [100, 200, 300], "medicare_cost": [0, 1000, 1200], "irmaa": [0, 200, 300]}
    assert mod._build_rmd_summary(results, False) == {"First RMD Year": 2026, "Largest RMD": 300, "Lifetime RMD Withdrawals": 400}
    couple = mod._build_rmd_summary(results, True)
    assert couple["Husband First RMD Year"] == 2026
    assert couple["Wife First RMD Year"] == 2027
    assert couple["Lifetime Total RMD"] == 400
    assert mod._build_rmd_summary({}, False)["First RMD Year"] is None
    assert mod._build_roth_summary(results) == {"Starting Roth Balance": 500, "Ending Roth Balance": 700, "Total Roth Conversions": 125, "Total Roth Withdrawals": 0}
    assert mod._build_hsa_summary(results)["Ending HSA Balance"] == 300
    assert mod._build_medicare_summary(results)["Lifetime Medicare and IRMAA Outlays"] == 2700


def test_tax_rows_exclude_opening_and_terminal_year_and_preserve_tax_components():
    keys = ("gross_income taxes federal_ordinary_tax federal_qualified_dividend_tax filing_status_single irmaa_lookback_available irmaa_lookback_magi federal_bracket_lower_threshold federal_bracket_upper_threshold magi state_income_tax payroll_tax social_security_payroll_tax medicare_tax additional_medicare_tax tax_bracket taxable_ordinary_income medicare_cost irmaa pre_tax_withdrawals emergency_pre_tax_used roth_conversions roth_withdrawals hsa_qualified_withdrawals hsa_taxable_withdrawals qualified_equity_distributions rmd rmd_husband rmd_wife").split()
    results = {key: [0, 0, 0] for key in keys}
    results.update(year=[2025, 2026, 2027], terminal_year=2027, gross_income=[0, 1000, 0],
                   taxes=[0, 150, 0], federal_ordinary_tax=[0, 100, 0],
                   federal_qualified_dividend_tax=[0, 10, 0], filing_status_single=[0, 1, 1],
                   federal_bracket_upper_threshold=[0, -1, -1])
    rows = mod._build_yearly_tax_rows(results, SimpleNamespace(age=65), None, SimpleNamespace())
    assert len(rows) == 1
    row = rows[0]
    assert row["Year"] == 2026 and row["Age"] == 66
    assert row["Federal Income Tax"] == 110
    assert row["Effective Tax Rate"] == .15
    assert row["Upper Bracket Limit"] is None
    assert row["IRMAA Lookback MAGI"] is None
    assert row["Filing Status"] == "Single"


def test_irmaa_rows_milestones_and_reference_tiers():
    core = {key: np.zeros((1, 3)) for key in (
        "husband_alive wife_alive irmaa_lookback_available irmaa_level irmaa_filing_status_single irmaa_lookback_magi irmaa_lower_threshold irmaa_upper_threshold irmaa medicare_cost").split()}
    core.update(year=np.array([[2025, 2026, 2027]]), terminal_year=np.array([-1]))
    core["husband_alive"][:] = 1
    core["irmaa_lookback_available"][0, 2] = 1
    core["irmaa_level"][0, 2] = 1
    core["irmaa"][0, 2] = 1000
    rows = mod._build_irmaa_yearly_rows(core, SimpleNamespace(age=63, medicare_start_age=65), None, SimpleNamespace())
    assert [row["IRMAA Tier"] for row in rows] == ["Not on Medicare", "Tier 1"]
    assert rows[1]["MAGI Year"] == 2025
    milestones = mod._build_irmaa_milestones(rows)
    assert milestones["First Medicare Year"]["Year"] == 2027
    assert milestones["First IRMAA Year"]["Annual IRMAA"] == 1000
    assert "Status" in mod._build_irmaa_milestones([])["First Medicare Year"]
    reference = mod._build_irmaa_reference_rows()
    assert len(reference) == 6 and reference[0]["Annual IRMAA / Person"] == 0
    for row in reference:
        assert row["Annual IRMAA / Two People"] == 2 * row["Annual IRMAA / Person"]


@pytest.mark.parametrize("fail", [False, True])
def test_pipeline_restores_shortfall_flag(monkeypatch, scenario_builders, fail):
    config = scenario_builders.make_config(calculate_simulated_shortfall_rate=True)
    def pipeline(*args, **kwargs):
        assert config.calculate_simulated_shortfall_rate is False
        assert kwargs == {"force_num_sims": 1}
        if fail:
            raise RuntimeError("pipeline failed")
        return {"summary_results": {}, "core": {"year": np.empty((1, 0)), "terminal_year": [-1]}}
    monkeypatch.setattr(mod, "run_pipeline", pipeline)
    args = (None, None, SimpleNamespace(age=60), None, None, config)
    if fail:
        with pytest.raises(RuntimeError, match="pipeline failed"):
            mod.build_tax_report_data_from_pipeline(*args)
    else:
        report = mod.build_tax_report_data_from_pipeline(*args)
        assert report["yearly_tax_rows"] == []
        assert report["report_metadata"]["Projection Period"] == "N/A"
    assert config.calculate_simulated_shortfall_rate is True


def test_runner_passes_report_to_generator(monkeypatch):
    from src.warpsimlab.reports import tax_report
    build, generate = Mock(return_value={"report": True}), Mock(return_value="tax.html")
    monkeypatch.setattr(mod, "build_tax_report_data_from_pipeline", build)
    monkeypatch.setattr(tax_report, "generate_tax_report", generate)
    assert mod.run_sim_tax_report(*range(6)) == "tax.html"
    generate.assert_called_once_with(build.return_value)
