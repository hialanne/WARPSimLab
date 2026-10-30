"""Real mixed-account cases and strict accounting comparisons for invariants."""

import numpy as np

from tests.architectural_helpers import make_execution_case


ACCOUNT_COMPONENTS = {
    "pre_tax_assets": ("pre_tax_equity", "pre_tax_bonds", "pre_tax_cash"),
    "post_tax_assets": ("post_tax_equity", "post_tax_bonds", "post_tax_cash"),
    "roth_assets": ("roth_equity", "roth_bonds", "roth_cash"),
    "hsa_assets": ("hsa_equity", "hsa_bonds", "hsa_cash"),
}


def assert_money_equal(actual, expected, label=""):
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-7, err_msg=label)


def accounting_case(*, expense_mode=True, market="fixed", balance_scale=1.0, **overrides):
    values = dict(
        always_use_expense_mode=expense_mode, overlay_profit_loss=False,
        results_mode="fill" if market == "fixed" else "risk_analysis",
        risk_analysis_mode="historical_windows" if market == "historical" else "monte_carlo",
        historical_window_start_year=2000 if market == "historical" else None,
        historical_window_stop_year=2002 if market == "historical" else None,
    )
    values.update(overrides)
    case = make_execution_case(**values)
    for name in ("husband_portfolio", "wife_portfolio"):
        portfolio = case[name]
        for field, value in vars(portfolio).items():
            setattr(portfolio, field, value * balance_scale)
    return case
