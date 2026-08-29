# gui_scenarioSnapshots.py

class ScenarioSnapshots:
    """
    Container for temporary retirement slider values and related overrides.
    Used to pass multiple variables cleanly through the GUI and simulation layers.

    annotation_strings format:
    - List of annotation lines
    - Each line is a list of spans
    - Each span is a dict with at least:
        {
            "text": str,
            "color": Optional[str]
        }
    """

    def __init__(   self, 
                    inflation=0.0, 
                    fund_expense=0.0,
                    custom_stock_percent=0.0, 
                    custom_bonds_percent=0.0, 
                    custom_cash_percent=0.0, 
                    rebalance_var="dont-rebalance",
                    historical_data_multiplier = 1.0,
                    use_snapshot_annotations=False,
                    annotation_strings = None,  # list[list[dict]]; see class docstring
                    scenario_withdraw_pct = None,
                    scenario_expense_multiplier = None,
                    adjust_hist_for_infl_delta = False,
                    delta_inflation = 0.0
    ):
        self.inflation = inflation
        self.fund_expense = fund_expense
        self.custom_stock_percent = custom_stock_percent
        self.custom_bonds_percent = custom_bonds_percent
        self.custom_cash_percent = custom_cash_percent
        self.rebalance_var = rebalance_var
        self.historical_data_multiplier = historical_data_multiplier
        self.use_snapshot_annotations = use_snapshot_annotations

        if annotation_strings is None:
            self.annotation_strings = []
        else:
            self.annotation_strings = annotation_strings

        self.scenario_withdraw_pct = scenario_withdraw_pct
        self.scenario_expense_multiplier = scenario_expense_multiplier
        # Expected span format:
        # {
        #     "text": str,
        #     "color": Optional[str]
        # }

        self.adjust_hist_for_infl_delta = adjust_hist_for_infl_delta
        self.delta_inflation = delta_inflation

