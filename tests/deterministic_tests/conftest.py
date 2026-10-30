"""Real-pipeline construction for independently calculated financial scenarios."""

import pytest

from src.warpsimlab.dataClasses.dynamicExpenses import DynamicExpenses
from src.warpsimlab.sim.simulation import run_pipeline
from tests.architectural_helpers import make_person, make_portfolio, make_simulation


@pytest.fixture
def run_financial_case():
    def run(*, husband=None, wife=None, h_assets=None, w_assets=None,
            expenses=(), **settings):
        h_port = make_portfolio(**(h_assets or {}))
        w_port = make_portfolio(**(w_assets or {}))
        config = make_simulation(husband_portfolio=h_port, wife_portfolio=w_port, **settings)
        spending = DynamicExpenses()
        for expense in expenses:
            spending.add_expense(**expense)
        return run_pipeline(
            h_port, w_port, make_person(**(husband or {})), make_person(**(wife or {})),
            spending, config, force_num_sims=1,
        )["core"]

    return run
