# test_gui_scenarioPlots.py

from types import SimpleNamespace

import pytest

from src.warpsimlab.gui.scenario import gui_scenarioPlots as mod


class DummyCanvas:
    def __init__(self):
        self.draw_idle_count = 0
        self.manager = SimpleNamespace(set_window_title=lambda title: None)

    def draw_idle(self):
        self.draw_idle_count += 1


class DummyFigure:
    def __init__(self):
        self.canvas = DummyCanvas()


class DummyAxis:
    def __init__(self, xlim=(0, 1), ylim=(0, 1), title=""):
        self._xlim = xlim
        self._ylim = ylim
        self._title = title
        self.clear_count = 0

    def get_xlim(self):
        return self._xlim

    def get_ylim(self):
        return self._ylim

    def set_xlim(self, value):
        self._xlim = value

    def set_ylim(self, value):
        self._ylim = value

    def clear(self):
        self.clear_count += 1

    def get_title(self):
        return self._title

    def set_title(self, title):
        self._title = title


def _make_main_gui():
    return SimpleNamespace(
        display_settings={"scenario_explorer": {"layout_mode": None, "layout": None}},
        root=SimpleNamespace(),
    )


def _make_controller(mode="scenario_view"):
    return SimpleNamespace(
        main_gui=_make_main_gui(),
        mode=mode,
        sliders_frame=None,
        income_ax=DummyAxis(),
        portfolio_ax=DummyAxis(),
        income_fig=DummyFigure(),
        portfolio_fig=DummyFigure(),
        baseline_results=None,
        scenario_results=None,
        window=None,
    )


def _make_manager(mode="scenario_view"):
    return mod.ScenarioPlotManager(_make_controller(mode))


def _make_result():
    return {
        "p": {
            "years": [2026, 2027],
            "years_list": [2026, 2027],
            "net_profit": [1, 2],
            "taxes": [3, 4],
            "expense_amt": [5, 6],
            "portfolio_plot_data": {"total": [100, 110]},
            "breakdown_by_class": {
                "work": 1,
                "pension": 2,
                "annuity": 3,
                "ss": 4,
                "special_income": 5,
                "rmd": 6,
                "withdrawal": 7,
                "cash_interest": 8,
                "bond_interest": 9,
                "qualified_equity_distributions": 10,
            },
        },
        "sim_config": SimpleNamespace(
            sim_type="portfolio_sim",
            annotate_plots=True,
            use_snapshot_annotations=False,
            scenario_explorer_annotations=["old"],
        ),
        "husband": SimpleNamespace(),
        "wife": None,
    }


@pytest.mark.parametrize(
    "mode,result_source,expected",
    [
        ("scenario_view", mod.RESULT_SOURCE_BASELINE, "Original"),
        ("scenario_view", mod.RESULT_SOURCE_SCENARIO, "Scenario"),
        ("compare_cashflow", mod.RESULT_SOURCE_SCENARIO, "Changed"),
        ("compare_portfolio", mod.RESULT_SOURCE_SCENARIO, "Changed"),
    ],
)
def test_panel_role_label(mode, result_source, expected):
    manager = _make_manager(mode)
    panel = {"result_source": result_source, "plot_family": mod.PLOT_FAMILY_CASHFLOW}

    assert manager.panel_role_label(panel) == expected


@pytest.mark.parametrize(
    "plot_family,expected",
    [
        (mod.PLOT_FAMILY_CASHFLOW, "Original Cash Flow"),
        (mod.PLOT_FAMILY_PORTFOLIO, "Original Portfolio"),
    ],
)


def test_panel_window_title_uses_role_and_family(plot_family, expected):
    manager = _make_manager()
    panel = {"result_source": mod.RESULT_SOURCE_BASELINE, "plot_family": plot_family}

    assert manager.panel_window_title(panel) == expected


def test_display_sim_config_returns_copy_and_sets_cashflow_type():
    manager = _make_manager()
    result = _make_result()
    panel = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_CASHFLOW}

    display_config = manager.display_sim_config(result, panel)

    assert display_config is not result["sim_config"]
    assert display_config.sim_type == "cashflow_sim"
    assert result["sim_config"].sim_type == "portfolio_sim"
    assert display_config.use_snapshot_annotations is False
    assert display_config.scenario_explorer_annotations == []


def test_display_sim_config_reads_annotation_checkbox():
    manager = _make_manager()
    manager.controller.sliders_frame = SimpleNamespace(enable_annotations=SimpleNamespace(get=lambda: True))
    result = _make_result()
    panel = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_PORTFOLIO}

    display_config = manager.display_sim_config(result, panel)

    assert display_config.use_snapshot_annotations is True
    assert display_config.sim_type == "portfolio_sim"


def test_sync_compare_axes_returns_when_families_differ():
    manager = _make_manager()
    c = manager.controller
    c.income_ax = DummyAxis((1, 2), (10, 20))
    c.portfolio_ax = DummyAxis((3, 4), (30, 40))

    left = {"plot_family": mod.PLOT_FAMILY_CASHFLOW}
    right = {"plot_family": mod.PLOT_FAMILY_PORTFOLIO}

    manager.sync_compare_axes(left, right)

    assert c.income_ax.get_xlim() == (1, 2)
    assert c.portfolio_ax.get_xlim() == (3, 4)
    assert c.income_ax.get_ylim() == (10, 20)
    assert c.portfolio_ax.get_ylim() == (30, 40)
    assert c.income_fig.canvas.draw_idle_count == 0
    assert c.portfolio_fig.canvas.draw_idle_count == 0


def test_sync_compare_axes_applies_shared_ranges():
    manager = _make_manager()
    c = manager.controller
    c.income_ax = DummyAxis((1, 5), (10, 40))
    c.portfolio_ax = DummyAxis((0, 6), (-5, 30))

    left = {"plot_family": mod.PLOT_FAMILY_PORTFOLIO}
    right = {"plot_family": mod.PLOT_FAMILY_PORTFOLIO}

    manager.sync_compare_axes(left, right)

    assert c.income_ax.get_xlim() == (0, 6)
    assert c.portfolio_ax.get_xlim() == (0, 6)
    assert c.income_ax.get_ylim() == (-5, 40)
    assert c.portfolio_ax.get_ylim() == (-5, 40)
    assert c.income_fig.canvas.draw_idle_count == 1
    assert c.portfolio_fig.canvas.draw_idle_count == 1


def test_draw_panel_returns_when_result_missing():
    manager = _make_manager()
    ax = DummyAxis(title="Existing")
    fig = DummyFigure()
    panel = {"result_source": mod.RESULT_SOURCE_BASELINE, "plot_family": mod.PLOT_FAMILY_CASHFLOW}

    manager.draw_panel(ax, fig, panel)

    assert ax.clear_count == 0
    assert ax.get_title() == "Existing"
    assert fig.canvas.draw_idle_count == 0


def test_draw_panel_cashflow_calls_income_plot(monkeypatch):
    manager = _make_manager(mode="compare_cashflow")
    result = _make_result()
    manager.controller.scenario_results = result

    ax = DummyAxis(title="Cash Flow")
    fig = DummyFigure()
    panel = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_CASHFLOW}
    received = {}

    def fake_draw_yearly_income(ax_arg, years, net_profit, cashflow_total, breakdown, taxes, expense_amt,
                                husband, wife, sim_config):
        received["ax"] = ax_arg
        received["years"] = years
        received["net_profit"] = net_profit
        received["cashflow_total"] = cashflow_total
        received["breakdown"] = breakdown
        received["sim_config"] = sim_config

    monkeypatch.setattr(mod, "draw_yearly_income", fake_draw_yearly_income)
    monkeypatch.setattr(manager, "apply_panel_window_title", lambda fig_arg, panel_arg: None)

    manager.draw_panel(ax, fig, panel)

    assert ax.clear_count == 1
    assert received["ax"] is ax
    assert received["years"] == [2026, 2027]
    assert received["net_profit"] == [1, 2]
    assert received["breakdown"]["income"] == 15
    assert received["cashflow_total"] == 55
    assert received["sim_config"].sim_type == "cashflow_sim"
    assert ax.get_title() == "Changed Cash Flow"
    assert fig.canvas.draw_idle_count == 1


def test_draw_panel_portfolio_calls_portfolio_plot(monkeypatch):
    manager = _make_manager()
    result = _make_result()
    manager.controller.baseline_results = result

    ax = DummyAxis(title="Portfolio Projection")
    fig = DummyFigure()
    panel = {"result_source": mod.RESULT_SOURCE_BASELINE, "plot_family": mod.PLOT_FAMILY_PORTFOLIO}
    received = {}

    def fake_draw_portfolio_projection(ax_arg, years, portfolio_plot_data, **kwargs):
        received["ax"] = ax_arg
        received["years"] = years
        received["portfolio_plot_data"] = portfolio_plot_data
        received["kwargs"] = kwargs

    monkeypatch.setattr(mod, "draw_portfolio_projection", fake_draw_portfolio_projection)
    monkeypatch.setattr(manager, "apply_panel_window_title", lambda fig_arg, panel_arg: None)

    manager.draw_panel(ax, fig, panel)

    assert ax.clear_count == 1
    assert received["ax"] is ax
    assert received["years"] == [2026, 2027]
    assert received["portfolio_plot_data"] == {"total": [100, 110]}
    assert received["kwargs"]["husband"] is result["husband"]
    assert received["kwargs"]["wife"] is None
    assert ax.get_title() == "Original Portfolio Projection"
    assert fig.canvas.draw_idle_count == 1


def test_render_panels_draws_both_and_optionally_syncs(monkeypatch):
    manager = _make_manager()
    left = {"result_source": mod.RESULT_SOURCE_BASELINE, "plot_family": mod.PLOT_FAMILY_PORTFOLIO}
    right = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_PORTFOLIO}
    calls = {"draw": [], "sync": 0}

    monkeypatch.setattr(manager, "draw_panel", lambda ax, fig, panel: calls["draw"].append((ax, fig, panel)))
    monkeypatch.setattr(manager, "sync_compare_axes", lambda left_arg, right_arg: calls.__setitem__("sync", calls["sync"] + 1))

    manager.render_panels(left, right, sync_axes=True)

    assert len(calls["draw"]) == 2
    assert calls["draw"][0][2] is left
    assert calls["draw"][1][2] is right
    assert calls["sync"] == 1