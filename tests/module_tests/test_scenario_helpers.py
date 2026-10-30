"""Shared scenario defaults must not leak mutable inputs between tests."""

import numpy as np

from tests.architectural_helpers import make_simulation


def test_real_config_builder_creates_independent_mutable_defaults():
    first, second = make_simulation(), make_simulation()
    first.historical_magi["two_years_prior"] = 200_000
    first.user_annotation_strings.append([{"text": "first run", "color": None}])
    first.scenario_explorer_annotations.append([{"text": "modified", "color": None}])
    first.report_options["columns"] = ["taxes"]
    first.special_income_streams.append({"amount": 1_000})
    first.roth_flows.append({"amount": 2_000})
    original_correlation = second.return_correlation_matrix.copy()
    first.return_correlation_matrix[0, 1] = 0.99

    assert second.historical_magi == {"two_years_prior": None, "one_year_prior": None}
    assert second.user_annotation_strings == []
    assert second.scenario_explorer_annotations == []
    assert second.report_options == {}
    assert second.special_income_streams == []
    assert second.roth_flows == []
    assert not np.shares_memory(first.return_correlation_matrix, second.return_correlation_matrix)
    np.testing.assert_array_equal(second.return_correlation_matrix, original_correlation)


def test_lightweight_config_fixture_creates_independent_mutable_defaults(scenario_builders):
    first, second = scenario_builders.make_config(), scenario_builders.make_config()
    first.historical_magi["one_year_prior"] = 100_000
    first.special_income_streams.append({"amount": 1_000})
    first.roth_flows.append({"amount": 2_000})
    first.user_annotation_strings.append([{"text": "first", "color": None}])

    assert second.historical_magi == {"two_years_prior": None, "one_year_prior": None}
    assert second.special_income_streams == []
    assert second.roth_flows == []
    assert second.user_annotation_strings == []
