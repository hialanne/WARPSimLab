# test_statsCollector.py

import numpy as np
import types

from src.warpsimlab.sim.engines.statsCollector import (
    compute_portfolio_statistics,
    optional_stats,
    aggregate_year_end_values
)


# ---------------------------------------------------------
# compute_portfolio_statistics
# ---------------------------------------------------------

def test_compute_portfolio_statistics_basic_percentiles():
    # 3 simulations, 3 years
    data = np.array([
        [100, 200, 300],
        [200, 300, 400],
        [300, 400, 500],
    ])

    stats = compute_portfolio_statistics(data, years=2, inflation_rate=0.0)

    # Median should be the middle row
    assert np.allclose(stats["median"], [200, 300, 400])

    # 10th percentile should be near the lowest values
    assert stats["pct10"].shape == (3,)
    assert stats["pct90"].shape == (3,)

    # Ensure expected keys exist
    expected_keys = {
        "pct1", "pct10", "pct20", "pct30", "pct40",
        "median",
        "pct60", "pct70", "pct80", "pct90", "pct99"
    }
    assert set(stats.keys()) == expected_keys


def test_compute_portfolio_statistics_shape_matches_years():
    sims = 5
    years = 4
    data = np.random.rand(sims, years + 1)

    stats = compute_portfolio_statistics(data, years=years, inflation_rate=0.0)

    for arr in stats.values():
        assert arr.shape == (years + 1,)


# ---------------------------------------------------------
# optional_stats
# ---------------------------------------------------------

def test_optional_stats_returns_none_when_disabled():
    data = np.random.rand(3, 4)
    result = optional_stats(data, years=3, inflation_rate=0.0, enabled=False)
    assert result is None


def test_optional_stats_returns_none_when_results_missing():
    result = optional_stats(None, years=3, inflation_rate=0.0, enabled=True)
    assert result is None


def test_optional_stats_returns_median_when_enabled():
    data = np.array([
        [100, 200],
        [200, 300],
        [300, 400],
    ])

    result = optional_stats(data, years=1, inflation_rate=0.0, enabled=True)

    expected_median = np.array([200, 300])
    assert np.allclose(result, expected_median)


# ---------------------------------------------------------
# aggregate_year_end_values
# ---------------------------------------------------------

class DummyPortfolio:
    def __init__(self, eq_pre, bd_pre, cs_pre, eq_post, bd_post, cs_post, re_post=0):
        self.eq_pre = eq_pre
        self.bd_pre = bd_pre
        self.cs_pre = cs_pre
        self.eq_post = eq_post
        self.bd_post = bd_post
        self.cs_post = cs_post
        self.re_post = re_post

    @property
    def total_value(self):
        return (
            self.eq_pre + self.bd_pre + self.cs_pre +
            self.eq_post + self.bd_post + self.cs_post
        )


def make_config(second_person=False, include_realestate=False):
    return types.SimpleNamespace(
        second_person_enabled=second_person,
        include_realestate=include_realestate
    )


def test_aggregate_year_end_values_single_person():
    h = DummyPortfolio(10, 20, 30, 40, 50, 60)

    total, cash, bonds, realestate = aggregate_year_end_values(
        h, None, make_config()
    )

    assert total == h.total_value
    assert cash == (30 + 60)
    assert bonds == (20 + 50)
    assert realestate == 0


def test_aggregate_year_end_values_with_real_estate():
    h = DummyPortfolio(10, 20, 30, 40, 50, 60, re_post=100)

    total, cash, bonds, realestate = aggregate_year_end_values(
        h, None, make_config(include_realestate=True)
    )

    assert realestate == 100
    assert total == h.total_value + 100


def test_aggregate_year_end_values_couple():
    h = DummyPortfolio(10, 20, 30, 40, 50, 60)
    w = DummyPortfolio(1, 2, 3, 4, 5, 6)

    total, cash, bonds, realestate = aggregate_year_end_values(
        h, w, make_config(second_person=True)
    )

    assert total == h.total_value + w.total_value
    assert cash == (30 + 60 + 3 + 6)
    assert bonds == (20 + 50 + 2 + 5)
    assert realestate == 0