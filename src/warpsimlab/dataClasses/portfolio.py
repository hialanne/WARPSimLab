class Portfolio:
    def __init__(
        self,
        equity_pre,
        equity_post,
        bond_pre,
        bond_post,
        cash_pre,
        cash_post,
        real_estate,
        equity_roth=0.0,
        bond_roth=0.0,
        cash_roth=0.0,
        hsa_cash=0.0,
        hsa_equity=0.0,
        hsa_bond=0.0,
    ):
        self.equity_pre = equity_pre
        self.equity_post = equity_post
        self.equity_roth = equity_roth

        self.bond_pre = bond_pre
        self.bond_post = bond_post
        self.bond_roth = bond_roth

        self.cash_pre = cash_pre
        self.cash_post = cash_post
        self.cash_roth = cash_roth

        self.hsa_cash = hsa_cash
        self.hsa_equity = hsa_equity
        self.hsa_bond = hsa_bond

        self.real_estate = real_estate