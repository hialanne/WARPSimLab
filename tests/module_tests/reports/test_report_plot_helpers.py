# test_report_plot_helpers.py

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from src.warpsimlab.reports import report_plot_helpers as mod


class DummyFig:
    def __init__(self):
        self.savefig_calls = []

    def savefig(self, *args, **kwargs):
        self.savefig_calls.append((args, kwargs))


class DummyAx:
    pass


@pytest.fixture
def dummy_figure(monkeypatch):
    fig = DummyFig()
    ax = DummyAx()
    close_calls = []

    monkeypatch.setattr(mod.plt, "subplots", lambda *args, **kwargs: (fig, ax))
    monkeypatch.setattr(mod.plt, "close", lambda closed_fig: close_calls.append(closed_fig))

    return SimpleNamespace(fig=fig, ax=ax, close_calls=close_calls)


def make_plot_data():
    return SimpleNamespace(
        years=np.array([2025, 2026, 2027]),
        percentiles={
            "p10": np.array([90.0, 95.0, 100.0]),
            "median": np.array([100.0, 110.0, 120.0]),
            "p90": np.array([110.0, 125.0, 140.0]),
        },
        median_without_fund_expenses=np.array([100.0, 111.0, 122.0]),
        median_without_taxes=np.array([100.0, 112.0, 124.0]),
        median_without_taxes_or_fund_expenses=np.array([100.0, 113.0, 126.0]),
        cash=np.array([10.0, 11.0, 12.0]),
        bonds=np.array([20.0, 21.0, 22.0]),
        realestate=np.array([30.0, 31.0, 32.0]),
        pre_tax_assets=np.array([40.0, 41.0, 42.0]),
        post_tax_assets=np.array([60.0, 69.0, 78.0]),
        raw_total_assets=np.array([[100.0, 110.0, 120.0]]),
        simulated_shortfall_rate=0.25,
    )


def test_ensure_output_folder_creates_directory(tmp_path):
    output_folder = tmp_path / "reports" / "assets"

    mod._ensure_output_folder(output_folder)

    assert output_folder.exists()
    assert output_folder.is_dir()


def test_build_portfolio_only_plot_data_replaces_median_with_pre_plus_post_assets():
    portfolio_plot_data = make_plot_data()
    summary_results = {
        "pre_tax_assets": np.array([100.0, 110.0, 120.0]),
        "post_tax_assets": np.array([40.0, 50.0, 60.0]),
    }

    result = mod._build_portfolio_only_plot_data(
        portfolio_plot_data,
        summary_results,
    )

    np.testing.assert_allclose(
        result.percentiles["median"],
        np.array([140.0, 160.0, 180.0]),
    )
    np.testing.assert_allclose(result.pre_tax_assets, summary_results["pre_tax_assets"])
    np.testing.assert_allclose(result.post_tax_assets, summary_results["post_tax_assets"])

    assert result.realestate is None
    assert result.raw_total_assets is None
    assert result.median_without_fund_expenses is None
    assert result.median_without_taxes is None
    assert result.median_without_taxes_or_fund_expenses is None
    assert result.simulated_shortfall_rate == pytest.approx(0.25)


def test_build_portfolio_only_plot_data_preserves_non_median_percentiles():
    portfolio_plot_data = make_plot_data()
    summary_results = {
        "pre_tax_assets": [1.0, 2.0, 3.0],
        "post_tax_assets": [4.0, 5.0, 6.0],
    }

    result = mod._build_portfolio_only_plot_data(
        portfolio_plot_data,
        summary_results,
    )

    np.testing.assert_allclose(result.percentiles["p10"], portfolio_plot_data.percentiles["p10"])
    np.testing.assert_allclose(result.percentiles["p90"], portfolio_plot_data.percentiles["p90"])


def test_save_portfolio_projection_report_plot_calls_draw_and_saves_file(
    tmp_path,
    monkeypatch,
    dummy_figure,
):
    draw_calls = []

    def fake_draw_portfolio_projection(*args, **kwargs):
        draw_calls.append((args, kwargs))

    monkeypatch.setattr(mod, "draw_portfolio_projection", fake_draw_portfolio_projection)

    output_folder = tmp_path / "reports"
    filename = "portfolio.png"
    years_list = np.array([2025, 2026])
    portfolio_plot_data = make_plot_data()
    sim_config = SimpleNamespace(
        annotate_plots=True,
        sim_rebalance="none",
    )
    husband = SimpleNamespace(name="Husband")
    wife = SimpleNamespace(name="Wife")

    image_path = mod.save_portfolio_projection_report_plot(
        output_folder=str(output_folder),
        filename=filename,
        years_list=years_list,
        portfolio_plot_data=portfolio_plot_data,
        sim_config=sim_config,
        husband=husband,
        wife=wife,
        summary_results=None,
    )

    assert image_path == str(output_folder / filename)
    assert output_folder.exists()

    assert len(draw_calls) == 1
    args, kwargs = draw_calls[0]
    assert args[0] is dummy_figure.ax
    np.testing.assert_allclose(args[1], years_list)
    assert args[2] is portfolio_plot_data
    assert kwargs["sim_config"] is sim_config
    assert kwargs["annotate_plots"] is True
    assert kwargs["sim_rebalance_string"] == "none"
    assert kwargs["husband"] is husband
    assert kwargs["wife"] is wife

    assert len(dummy_figure.fig.savefig_calls) == 1
    save_args, save_kwargs = dummy_figure.fig.savefig_calls[0]
    assert save_args[0] == str(output_folder / filename)
    assert save_kwargs["dpi"] == 200
    assert save_kwargs["bbox_inches"] == "tight"

    assert dummy_figure.close_calls == [dummy_figure.fig]


def test_save_portfolio_projection_uses_portfolio_only_data_when_summary_results_present(
    tmp_path,
    monkeypatch,
    dummy_figure,
):
    sentinel_plot_data = object()
    build_calls = []
    draw_calls = []

    def fake_build_portfolio_only_plot_data(portfolio_plot_data, summary_results):
        build_calls.append((portfolio_plot_data, summary_results))
        return sentinel_plot_data

    def fake_draw_portfolio_projection(*args, **kwargs):
        draw_calls.append((args, kwargs))

    monkeypatch.setattr(mod, "_build_portfolio_only_plot_data", fake_build_portfolio_only_plot_data)
    monkeypatch.setattr(mod, "draw_portfolio_projection", fake_draw_portfolio_projection)

    original_plot_data = make_plot_data()
    summary_results = {
        "pre_tax_assets": [1.0],
        "post_tax_assets": [2.0],
    }

    mod.save_portfolio_projection_report_plot(
        output_folder=str(tmp_path),
        filename="portfolio.png",
        years_list=[2025],
        portfolio_plot_data=original_plot_data,
        sim_config=SimpleNamespace(),
        summary_results=summary_results,
    )

    assert build_calls == [(original_plot_data, summary_results)]
    assert draw_calls[0][0][2] is sentinel_plot_data


def test_save_portfolio_projection_does_not_build_portfolio_only_data_without_summary_results(
    tmp_path,
    monkeypatch,
    dummy_figure,
):
    monkeypatch.setattr(
        mod,
        "_build_portfolio_only_plot_data",
        lambda *args, **kwargs: pytest.fail("_build_portfolio_only_plot_data should not be called"),
    )
    monkeypatch.setattr(mod, "draw_portfolio_projection", lambda *args, **kwargs: None)

    mod.save_portfolio_projection_report_plot(
        output_folder=str(tmp_path),
        filename="portfolio.png",
        years_list=[2025],
        portfolio_plot_data=make_plot_data(),
        sim_config=SimpleNamespace(),
        summary_results=None,
    )


def test_save_portfolio_projection_closes_figure_when_draw_raises(
    tmp_path,
    monkeypatch,
    dummy_figure,
):
    def raise_from_draw(*args, **kwargs):
        raise RuntimeError("draw failed")

    monkeypatch.setattr(mod, "draw_portfolio_projection", raise_from_draw)

    with pytest.raises(RuntimeError, match="draw failed"):
        mod.save_portfolio_projection_report_plot(
            output_folder=str(tmp_path),
            filename="portfolio.png",
            years_list=[2025],
            portfolio_plot_data=make_plot_data(),
            sim_config=SimpleNamespace(),
        )

    assert dummy_figure.close_calls == [dummy_figure.fig]
    assert dummy_figure.fig.savefig_calls == []


def test_save_income_projection_report_plot_calls_draw_and_saves_file(
    tmp_path,
    monkeypatch,
    dummy_figure,
):
    draw_calls = []

    def fake_draw_yearly_income(*args, **kwargs):
        draw_calls.append((args, kwargs))

    monkeypatch.setattr(mod, "draw_yearly_income", fake_draw_yearly_income)

    output_folder = tmp_path / "reports"
    filename = "income.png"
    years_to_simulate = np.array([2025, 2026])
    net_profit = np.array([0.0, 10.0])
    net_income = np.array([0.0, 50.0])
    breakdown = {"work": np.array([0.0, 50.0])}
    taxes = np.array([0.0, 5.0])
    expenses = np.array([0.0, 35.0])
    husband = SimpleNamespace(name="Husband")
    wife = SimpleNamespace(name="Wife")
    sim_config = SimpleNamespace()

    image_path = mod.save_income_projection_report_plot(
        output_folder=str(output_folder),
        filename=filename,
        years_to_simulate=years_to_simulate,
        net_profit=net_profit,
        net_income=net_income,
        breakdown=breakdown,
        taxes=taxes,
        expenses=expenses,
        husband=husband,
        wife=wife,
        sim_config=sim_config,
    )

    assert image_path == str(output_folder / filename)
    assert output_folder.exists()

    assert len(draw_calls) == 1
    args, kwargs = draw_calls[0]
    assert kwargs == {}
    assert args[0] is dummy_figure.ax
    np.testing.assert_allclose(args[1], years_to_simulate)
    np.testing.assert_allclose(args[2], net_profit)
    np.testing.assert_allclose(args[3], net_income)
    assert args[4] is breakdown
    np.testing.assert_allclose(args[5], taxes)
    np.testing.assert_allclose(args[6], expenses)
    assert args[7] is husband
    assert args[8] is wife
    assert args[9] is sim_config

    assert len(dummy_figure.fig.savefig_calls) == 1
    save_args, save_kwargs = dummy_figure.fig.savefig_calls[0]
    assert save_args[0] == str(output_folder / filename)
    assert save_kwargs["dpi"] == 200
    assert save_kwargs["bbox_inches"] == "tight"

    assert dummy_figure.close_calls == [dummy_figure.fig]


def test_save_income_projection_closes_figure_when_draw_raises(
    tmp_path,
    monkeypatch,
    dummy_figure,
):
    def raise_from_draw(*args, **kwargs):
        raise RuntimeError("income draw failed")

    monkeypatch.setattr(mod, "draw_yearly_income", raise_from_draw)

    with pytest.raises(RuntimeError, match="income draw failed"):
        mod.save_income_projection_report_plot(
            output_folder=str(tmp_path),
            filename="income.png",
            years_to_simulate=[2025],
            net_profit=[0.0],
            net_income=[0.0],
            breakdown={},
            taxes=[0.0],
            expenses=[0.0],
            husband=SimpleNamespace(),
            wife=SimpleNamespace(),
            sim_config=SimpleNamespace(),
        )

    assert dummy_figure.close_calls == [dummy_figure.fig]
    assert dummy_figure.fig.savefig_calls == []


def test_save_cumulative_operating_balance_report_plot_computes_cumulative_balance(
    tmp_path,
    monkeypatch,
    dummy_figure,
):
    draw_calls = []

    def fake_draw_operating_balance(*args, **kwargs):
        draw_calls.append((args, kwargs))

    monkeypatch.setattr(mod, "draw_operating_balance", fake_draw_operating_balance)

    output_folder = tmp_path / "reports"
    filename = "operating_balance.png"
    years_to_simulate = np.array([2025, 2026, 2027, 2028])
    net_profit = np.array([0.0, 10.0, -5.0, 20.0])
    portfolio_plot_data = SimpleNamespace(
        percentiles={
            "median": np.array([100.0, 110.0, 105.0, 125.0]),
        }
    )
    husband = SimpleNamespace(name="Husband")
    wife = SimpleNamespace(name="Wife")
    sim_config = SimpleNamespace()

    image_path = mod.save_cumulative_operating_balance_report_plot(
        output_folder=str(output_folder),
        filename=filename,
        years_to_simulate=years_to_simulate,
        net_profit=net_profit,
        portfolio_plot_data=portfolio_plot_data,
        husband=husband,
        wife=wife,
        sim_config=sim_config,
    )

    assert image_path == str(output_folder / filename)
    assert output_folder.exists()

    assert len(draw_calls) == 1
    args, kwargs = draw_calls[0]
    assert kwargs == {}
    assert args[0] is dummy_figure.ax
    np.testing.assert_allclose(args[1], years_to_simulate)
    np.testing.assert_allclose(args[2], net_profit)
    np.testing.assert_allclose(args[3], np.array([0.0, 10.0, 5.0, 25.0]))
    np.testing.assert_allclose(args[4], np.array([100.0, 110.0, 105.0, 125.0]))
    assert args[5] is husband
    assert args[6] is wife
    assert args[7] is sim_config

    assert len(dummy_figure.fig.savefig_calls) == 1
    save_args, save_kwargs = dummy_figure.fig.savefig_calls[0]
    assert save_args[0] == str(output_folder / filename)
    assert save_kwargs["dpi"] == 200
    assert save_kwargs["bbox_inches"] == "tight"

    assert dummy_figure.close_calls == [dummy_figure.fig]


def test_save_cumulative_operating_balance_handles_single_year_net_profit(
    tmp_path,
    monkeypatch,
    dummy_figure,
):
    draw_calls = []

    def fake_draw_operating_balance(*args, **kwargs):
        draw_calls.append((args, kwargs))

    monkeypatch.setattr(mod, "draw_operating_balance", fake_draw_operating_balance)

    portfolio_plot_data = SimpleNamespace(
        percentiles={
            "median": np.array([100.0]),
        }
    )

    mod.save_cumulative_operating_balance_report_plot(
        output_folder=str(tmp_path),
        filename="operating_balance.png",
        years_to_simulate=np.array([2025]),
        net_profit=np.array([99.0]),
        portfolio_plot_data=portfolio_plot_data,
        husband=SimpleNamespace(),
        wife=SimpleNamespace(),
        sim_config=SimpleNamespace(),
    )

    args, kwargs = draw_calls[0]
    np.testing.assert_allclose(args[3], np.array([0.0]))


def test_save_cumulative_operating_balance_closes_figure_when_draw_raises(
    tmp_path,
    monkeypatch,
    dummy_figure,
):
    def raise_from_draw(*args, **kwargs):
        raise RuntimeError("operating draw failed")

    monkeypatch.setattr(mod, "draw_operating_balance", raise_from_draw)

    with pytest.raises(RuntimeError, match="operating draw failed"):
        mod.save_cumulative_operating_balance_report_plot(
            output_folder=str(tmp_path),
            filename="operating_balance.png",
            years_to_simulate=[2025],
            net_profit=[0.0],
            portfolio_plot_data=SimpleNamespace(percentiles={"median": [100.0]}),
            husband=SimpleNamespace(),
            wife=SimpleNamespace(),
            sim_config=SimpleNamespace(),
        )

    assert dummy_figure.close_calls == [dummy_figure.fig]
    assert dummy_figure.fig.savefig_calls == []
