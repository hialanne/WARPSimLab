from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.warpsimlab.sim import run_sim_year_by_year_report as mod


def test_year_row_financial_aggregation_and_household_ages():
    results = {key: [value] for key, value in dict(
        year=2025, pre_tax_assets=100, post_tax_assets=200, roth_assets=300,
        hsa_assets=40, real_estate=500, wages=1000, employee_401k_contributions=100,
        hsa_employee_contributions=20, hsa_employer_contributions=10,
        pensions=50, annuities=60, husband_death_event=1, wife_death_event=0,
        filing_status_single=1).items()}
    row = mod._build_year_row(results, 0, SimpleNamespace(age=65), SimpleNamespace(age=60), SimpleNamespace(second_person_enabled=True))
    assert row["Total Portfolio"] == 640
    assert row["Total Assets"] == 1140
    assert row["Gross Wages"] == 1120  # Employer HSA contribution is not wages.
    assert row["Pensions and Annuities"] == 110
    assert row["Age 1"] == 65 and row["Age 2"] == 60
    assert "Age" not in row
    assert row["Life Event"] == "Husband Died"
    assert row["Filing Status"] == "Single"
    assert row["Taxes"] == 0


@pytest.mark.parametrize("h,w,label", [(0, 0, ""), (1, 0, "Husband Died"), (0, 1, "Wife Died"), (1, 1, "Both Died")])
def test_life_event_labels(h, w, label):
    assert mod._build_life_event({"husband_death_event": [h], "wife_death_event": [w]}, 0) == label


@pytest.mark.parametrize("values", [None, [], [None], ["bad"], 3])
def test_missing_or_invalid_series_uses_default(values):
    assert mod._array_value({"taxes": values}, "taxes", 0, default=7) == 7


@pytest.mark.parametrize("years,label", [([], "N/A"), (["bad"], "N/A"), ([2025], "2025-2025 (0 Years)"), ([2025, 2026], "2025-2026 (1 Years)")])
def test_projection_period(years, label):
    assert mod._build_projection_period_label({"year": years}) == label


@pytest.mark.parametrize("fail", [False, True])
def test_pipeline_temporary_options_restored_on_success_and_failure(monkeypatch, scenario_builders, fail):
    config = scenario_builders.make_config(include_realestate=False, calculate_simulated_shortfall_rate=True,
                                          report_options={"custom": True})
    before = vars(config).copy()
    def pipeline(*args, **kwargs):
        assert args[-1] is config
        assert config.include_realestate is True
        assert config.calculate_simulated_shortfall_rate is False
        assert kwargs == {"force_num_sims": 1}
        if fail:
            raise RuntimeError("pipeline failed")
        return {"summary_results": {"year": [2025, 2026]}}
    monkeypatch.setattr(mod, "run_pipeline", pipeline)
    args = (None, None, SimpleNamespace(age=60), None, None, config)
    if fail:
        with pytest.raises(RuntimeError, match="pipeline failed"):
            mod.build_year_by_year_report_data_from_pipeline(*args)
    else:
        report = mod.build_year_by_year_report_data_from_pipeline(*args)
        assert [r["Age"] for r in report.year_rows] == [60, 61]
        assert report.report_options["_always_use_expense_mode"] is True
        assert report.report_options is not config.report_options
        assert report.report_metadata["Projection Period"] == "2025-2026 (1 Years)"
    assert vars(config) == before


def test_runner_passes_report_to_generator(monkeypatch):
    build, generate = Mock(return_value=object()), Mock(return_value="report.html")
    monkeypatch.setattr(mod, "build_year_by_year_report_data_from_pipeline", build)
    monkeypatch.setattr(mod, "generate_year_by_year_report", generate)
    assert mod.run_sim_year_by_year_report(*range(6)) == "report.html"
    build.assert_called_once_with(*range(6))
    generate.assert_called_once_with(build.return_value)
