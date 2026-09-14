from types import SimpleNamespace

import pytest

from src.warpsimlab.gui.scenario import gui_scenarioPlots as mod


class DummyCanvas:
    def __init__(self):
        self.draw_idle_count = 0
        self.window_title = None
        self.manager = SimpleNamespace(set_window_title=self._set_window_title)

    def _set_window_title(self, title):
        self.window_title = title

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


def _make_manager():
    return mod.ScenarioPlotManager(_make_main_gui(), lambda: None)


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
        ("income_compare", mod.RESULT_SOURCE_SCENARIO, "Changed"),
        ("cashflow_compare", mod.RESULT_SOURCE_SCENARIO, "Changed"),
        ("portfolio_compare", mod.RESULT_SOURCE_SCENARIO, "Changed"),
    ],
)
def test_panel_role_label(mode, result_source, expected):
    manager = _make_manager()
    panel = {"result_source": result_source, "plot_family": mod.PLOT_FAMILY_CASHFLOW}

    assert manager.panel_role_label(panel, mode) == expected


@pytest.mark.parametrize(
    "plot_family,expected",
    [
        (mod.PLOT_FAMILY_INCOME, "Original Income"),
        (mod.PLOT_FAMILY_CASHFLOW, "Original Cash Flow"),
        (mod.PLOT_FAMILY_PORTFOLIO, "Original Portfolio"),
    ],
)
def test_panel_window_title_uses_role_and_family(plot_family, expected):
    manager = _make_manager()
    panel = {"result_source": mod.RESULT_SOURCE_BASELINE, "plot_family": plot_family}

    assert manager.panel_window_title(panel, "scenario_view") == expected


def test_apply_panel_window_title_updates_figure_manager():
    manager = _make_manager()
    fig = DummyFigure()
    panel = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_PORTFOLIO}

    manager.apply_panel_window_title(fig, panel, "portfolio_compare")

    assert fig.canvas.window_title == "Changed Portfolio"


def test_display_sim_config_returns_copy():
    manager = _make_manager()
    result = _make_result()
    panel = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_PORTFOLIO}

    display_config = manager.display_sim_config(result, panel, False)

    assert display_config is not result["sim_config"]
    assert result["sim_config"].sim_type == "portfolio_sim"
    assert result["sim_config"].use_snapshot_annotations is False
    assert result["sim_config"].scenario_explorer_annotations == ["old"]

    assert display_config.sim_type == "portfolio_sim"
    assert display_config.use_snapshot_annotations is False
    assert display_config.scenario_explorer_annotations == []


def test_display_sim_config_sets_annotation_state_from_explicit_argument():
    manager = _make_manager()
    result = _make_result()
    panel = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_PORTFOLIO}

    display_config = manager.display_sim_config(result, panel, True)

    assert display_config.use_snapshot_annotations is True
    assert result["sim_config"].use_snapshot_annotations is False


def test_display_sim_config_sets_income_sim_type():
    manager = _make_manager()
    result = _make_result()
    panel = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_INCOME}

    display_config = manager.display_sim_config(result, panel, False)

    assert display_config.sim_type == "income_sim"
    assert result["sim_config"].sim_type == "portfolio_sim"


def test_display_sim_config_sets_cashflow_sim_type():
    manager = _make_manager()
    result = _make_result()
    panel = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_CASHFLOW}

    display_config = manager.display_sim_config(result, panel, False)

    assert display_config.sim_type == "cashflow_sim"
    assert result["sim_config"].sim_type == "portfolio_sim"


def test_has_plots_false_until_both_axes_exist():
    manager = _make_manager()

    assert manager.has_plots() is False

    manager.income_ax = DummyAxis()

    assert manager.has_plots() is False

    manager.portfolio_ax = DummyAxis()

    assert manager.has_plots() is True


def test_sync_compare_axes_returns_when_families_differ():
    manager = _make_manager()
    manager.income_ax = DummyAxis((1, 2), (10, 20))
    manager.portfolio_ax = DummyAxis((3, 4), (30, 40))
    manager.income_fig = DummyFigure()
    manager.portfolio_fig = DummyFigure()

    left = {"plot_family": mod.PLOT_FAMILY_CASHFLOW}
    right = {"plot_family": mod.PLOT_FAMILY_PORTFOLIO}

    manager.sync_compare_axes(left, right)

    assert manager.income_ax.get_xlim() == (1, 2)
    assert manager.portfolio_ax.get_xlim() == (3, 4)
    assert manager.income_ax.get_ylim() == (10, 20)
    assert manager.portfolio_ax.get_ylim() == (30, 40)
    assert manager.income_fig.canvas.draw_idle_count == 0
    assert manager.portfolio_fig.canvas.draw_idle_count == 0


def test_sync_compare_axes_applies_shared_ranges():
    manager = _make_manager()
    manager.income_ax = DummyAxis((1, 5), (10, 40))
    manager.portfolio_ax = DummyAxis((0, 6), (-5, 30))
    manager.income_fig = DummyFigure()
    manager.portfolio_fig = DummyFigure()

    left = {"plot_family": mod.PLOT_FAMILY_PORTFOLIO}
    right = {"plot_family": mod.PLOT_FAMILY_PORTFOLIO}

    manager.sync_compare_axes(left, right)

    assert manager.income_ax.get_xlim() == (0, 6)
    assert manager.portfolio_ax.get_xlim() == (0, 6)
    assert manager.income_ax.get_ylim() == (-5, 40)
    assert manager.portfolio_ax.get_ylim() == (-5, 40)
    assert manager.income_fig.canvas.draw_idle_count == 1
    assert manager.portfolio_fig.canvas.draw_idle_count == 1


def test_draw_panel_returns_without_change_when_baseline_result_missing():
    manager = _make_manager()
    ax = DummyAxis(title="Existing")
    fig = DummyFigure()
    panel = {"result_source": mod.RESULT_SOURCE_BASELINE, "plot_family": mod.PLOT_FAMILY_CASHFLOW}

    manager.draw_panel(
        ax, fig, panel, baseline_results=None, scenario_results=_make_result(),
        mode="cashflow_compare", annotations_enabled=False
    )

    assert ax.clear_count == 0
    assert ax.get_title() == "Existing"
    assert fig.canvas.draw_idle_count == 0


def test_draw_panel_returns_without_change_when_scenario_result_missing():
    manager = _make_manager()
    ax = DummyAxis(title="Existing")
    fig = DummyFigure()
    panel = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_CASHFLOW}

    manager.draw_panel(
        ax, fig, panel, baseline_results=_make_result(), scenario_results=None,
        mode="cashflow_compare", annotations_enabled=False
    )

    assert ax.clear_count == 0
    assert ax.get_title() == "Existing"
    assert fig.canvas.draw_idle_count == 0


def test_draw_panel_income_calls_income_plot(monkeypatch):
    manager = _make_manager()
    result = _make_result()
    ax = DummyAxis(title="Income")
    fig = DummyFigure()
    panel = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_INCOME}
    received = {}

    def fake_draw_yearly_income(
        ax_arg, years, net_profit, income_total, breakdown, taxes, expense_amt, husband, wife, sim_config
    ):
        received["ax"] = ax_arg
        received["years"] = years
        received["net_profit"] = net_profit
        received["income_total"] = income_total
        received["breakdown"] = breakdown
        received["taxes"] = taxes
        received["expense_amt"] = expense_amt
        received["husband"] = husband
        received["wife"] = wife
        received["sim_config"] = sim_config

    monkeypatch.setattr(mod, "draw_yearly_income", fake_draw_yearly_income)

    manager.draw_panel(
        ax, fig, panel, baseline_results=None, scenario_results=result,
        mode="income_compare", annotations_enabled=True
    )

    assert ax.clear_count == 1
    assert received["ax"] is ax
    assert received["years"] == [2026, 2027]
    assert received["net_profit"] == [1, 2]
    assert received["income_total"] == 15
    assert received["breakdown"] == result["p"]["breakdown_by_class"]
    assert received["sim_config"].sim_type == "income_sim"
    assert received["sim_config"].use_snapshot_annotations is True
    assert ax.get_title() == "Changed Income"
    assert fig.canvas.window_title == "Changed Income"
    assert fig.canvas.draw_idle_count == 1


def test_draw_panel_cashflow_calls_income_plot(monkeypatch):
    manager = _make_manager()
    result = _make_result()
    ax = DummyAxis(title="Cash Flow")
    fig = DummyFigure()
    panel = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_CASHFLOW}
    received = {}

    def fake_draw_yearly_income(
        ax_arg, years, net_profit, cashflow_total, breakdown, taxes, expense_amt, husband, wife, sim_config
    ):
        received["ax"] = ax_arg
        received["years"] = years
        received["net_profit"] = net_profit
        received["cashflow_total"] = cashflow_total
        received["breakdown"] = breakdown
        received["sim_config"] = sim_config

    monkeypatch.setattr(mod, "draw_yearly_income", fake_draw_yearly_income)

    manager.draw_panel(
        ax, fig, panel, baseline_results=None, scenario_results=result,
        mode="cashflow_compare", annotations_enabled=False
    )

    assert ax.clear_count == 1
    assert received["ax"] is ax
    assert received["years"] == [2026, 2027]
    assert received["net_profit"] == [1, 2]
    assert received["breakdown"]["income"] == 15
    assert received["cashflow_total"] == 55
    assert received["sim_config"].sim_type == "cashflow_sim"
    assert received["sim_config"].use_snapshot_annotations is False
    assert ax.get_title() == "Changed Cash Flow"
    assert fig.canvas.window_title == "Changed Cash Flow"
    assert fig.canvas.draw_idle_count == 1


def test_draw_panel_does_not_modify_original_breakdown(monkeypatch):
    manager = _make_manager()
    result = _make_result()
    original_breakdown = dict(result["p"]["breakdown_by_class"])
    ax = DummyAxis(title="Cash Flow")
    fig = DummyFigure()
    panel = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_CASHFLOW}

    monkeypatch.setattr(mod, "draw_yearly_income", lambda *args, **kwargs: None)

    manager.draw_panel(
        ax, fig, panel, baseline_results=None, scenario_results=result,
        mode="cashflow_compare", annotations_enabled=False
    )

    assert result["p"]["breakdown_by_class"] == original_breakdown
    assert "income" not in result["p"]["breakdown_by_class"]


def test_draw_panel_portfolio_calls_portfolio_plot(monkeypatch):
    manager = _make_manager()
    result = _make_result()
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

    manager.draw_panel(
        ax, fig, panel, baseline_results=result, scenario_results=None,
        mode="portfolio_compare", annotations_enabled=True
    )

    assert ax.clear_count == 1
    assert received["ax"] is ax
    assert received["years"] == [2026, 2027]
    assert received["portfolio_plot_data"] == {"total": [100, 110]}
    assert received["kwargs"]["husband"] is result["husband"]
    assert received["kwargs"]["wife"] is None
    assert received["kwargs"]["sim_config"].use_snapshot_annotations is True
    assert ax.get_title() == "Original Portfolio Projection"
    assert fig.canvas.window_title == "Original Portfolio"
    assert fig.canvas.draw_idle_count == 1


def test_draw_panel_uses_baseline_or_scenario_result_explicitly(monkeypatch):
    manager = _make_manager()
    baseline = _make_result()
    scenario = _make_result()
    baseline["p"]["years_list"] = [2000]
    scenario["p"]["years_list"] = [2050]

    received_years = []

    def fake_draw_portfolio_projection(ax_arg, years, portfolio_plot_data, **kwargs):
        received_years.append(years)

    monkeypatch.setattr(mod, "draw_portfolio_projection", fake_draw_portfolio_projection)

    baseline_panel = {"result_source": mod.RESULT_SOURCE_BASELINE, "plot_family": mod.PLOT_FAMILY_PORTFOLIO}
    scenario_panel = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_PORTFOLIO}

    manager.draw_panel(
        DummyAxis(), DummyFigure(), baseline_panel, baseline, scenario,
        "portfolio_compare", False
    )
    manager.draw_panel(
        DummyAxis(), DummyFigure(), scenario_panel, baseline, scenario,
        "portfolio_compare", False
    )

    assert received_years == [[2000], [2050]]


def test_render_panels_draws_both_with_explicit_inputs(monkeypatch):
    manager = _make_manager()
    manager.income_ax = DummyAxis()
    manager.income_fig = DummyFigure()
    manager.portfolio_ax = DummyAxis()
    manager.portfolio_fig = DummyFigure()

    left = {"result_source": mod.RESULT_SOURCE_BASELINE, "plot_family": mod.PLOT_FAMILY_PORTFOLIO}
    right = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_PORTFOLIO}
    baseline = _make_result()
    scenario = _make_result()
    calls = []

    def fake_draw_panel(ax, fig, panel, baseline_results, scenario_results, mode, annotations_enabled):
        calls.append((ax, fig, panel, baseline_results, scenario_results, mode, annotations_enabled))

    monkeypatch.setattr(manager, "draw_panel", fake_draw_panel)

    manager.render_panels(
        left, right, baseline, scenario, "portfolio_compare", True, sync_axes=False
    )

    assert len(calls) == 2

    assert calls[0][0] is manager.income_ax
    assert calls[0][1] is manager.income_fig
    assert calls[0][2] is left
    assert calls[0][3] is baseline
    assert calls[0][4] is scenario
    assert calls[0][5] == "portfolio_compare"
    assert calls[0][6] is True

    assert calls[1][0] is manager.portfolio_ax
    assert calls[1][1] is manager.portfolio_fig
    assert calls[1][2] is right


def test_render_panels_syncs_axes_when_requested(monkeypatch):
    manager = _make_manager()
    manager.income_ax = DummyAxis()
    manager.income_fig = DummyFigure()
    manager.portfolio_ax = DummyAxis()
    manager.portfolio_fig = DummyFigure()

    left = {"result_source": mod.RESULT_SOURCE_BASELINE, "plot_family": mod.PLOT_FAMILY_PORTFOLIO}
    right = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_PORTFOLIO}
    calls = {"draw": 0, "sync": 0}

    def fake_draw_panel(*args):
        calls["draw"] += 1

    def fake_sync(left_panel, right_panel):
        assert left_panel is left
        assert right_panel is right
        calls["sync"] += 1

    monkeypatch.setattr(manager, "draw_panel", fake_draw_panel)
    monkeypatch.setattr(manager, "sync_compare_axes", fake_sync)

    manager.render_panels(
        left, right, _make_result(), _make_result(),
        "portfolio_compare", False, sync_axes=True
    )

    assert calls["draw"] == 2
    assert calls["sync"] == 1


def test_render_panels_does_not_sync_axes_when_not_requested(monkeypatch):
    manager = _make_manager()
    manager.income_ax = DummyAxis()
    manager.income_fig = DummyFigure()
    manager.portfolio_ax = DummyAxis()
    manager.portfolio_fig = DummyFigure()

    left = {"result_source": mod.RESULT_SOURCE_BASELINE, "plot_family": mod.PLOT_FAMILY_CASHFLOW}
    right = {"result_source": mod.RESULT_SOURCE_SCENARIO, "plot_family": mod.PLOT_FAMILY_CASHFLOW}
    calls = {"sync": 0}

    monkeypatch.setattr(manager, "draw_panel", lambda *args: None)
    monkeypatch.setattr(
        manager, "sync_compare_axes",
        lambda left_panel, right_panel: calls.__setitem__("sync", calls["sync"] + 1)
    )

    manager.render_panels(
        left, right, _make_result(), _make_result(),
        "cashflow_compare", False, sync_axes=False
    )

    assert calls["sync"] == 0