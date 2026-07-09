from src.warpsimlab.sim import simulation


def test_run_simulation_routes_cashflow_sim(monkeypatch):
    called = {}

    def fake_runner(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config):
        called["args"] = (husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config)
        return "cashflow-result"

    monkeypatch.setattr("src.warpsimlab.sim.run_sim_income.run_sim_income", fake_runner)

    sim_config = type("SimConfig", (), {"sim_type": "cashflow_sim"})()

    result = simulation.run_simulation("hp", "wp", "h", "w", "exp", sim_config)

    assert result == "cashflow-result"
    assert called["args"] == ("hp", "wp", "h", "w", "exp", sim_config)


def test_run_simulation_routes_operating_balance_sim(monkeypatch):
    called = {}

    def fake_runner(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config):
        called["args"] = (husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config)
        return "operating-balance-result"

    monkeypatch.setattr("src.warpsimlab.sim.run_sim_operating_balance.run_sim_operating_balance", fake_runner)

    sim_config = type("SimConfig", (), {"sim_type": "operating_balance_sim"})()

    result = simulation.run_simulation("hp", "wp", "h", "w", "exp", sim_config)

    assert result == "operating-balance-result"
    assert called["args"] == ("hp", "wp", "h", "w", "exp", sim_config)


def test_run_simulation_routes_portfolio_sim(monkeypatch):
    called = {}

    def fake_runner(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config):
        called["args"] = (husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config)
        return "portfolio-result"

    monkeypatch.setattr("src.warpsimlab.sim.run_sim_portfolio.run_sim_portfolio", fake_runner)

    sim_config = type("SimConfig", (), {"sim_type": "portfolio_sim"})()

    result = simulation.run_simulation("hp", "wp", "h", "w", "exp", sim_config)

    assert result == "portfolio-result"
    assert called["args"] == ("hp", "wp", "h", "w", "exp", sim_config)


def test_run_simulation_routes_summary_sim(monkeypatch):
    called = {}

    def fake_runner(husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config):
        called["args"] = (husband_portfolio, wife_portfolio, husband, wife, expenses, sim_config)
        return "summary-result"

    monkeypatch.setattr("src.warpsimlab.sim.run_sim_summary.run_sim_summary", fake_runner)

    sim_config = type("SimConfig", (), {"sim_type": "summary_sim"})()

    result = simulation.run_simulation("hp", "wp", "h", "w", "exp", sim_config)

    assert result == "summary-result"
    assert called["args"] == ("hp", "wp", "h", "w", "exp", sim_config)