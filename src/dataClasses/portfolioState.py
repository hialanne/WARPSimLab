# portfolioState.py

class PortfolioState:
    def __init__(
        self,
        eq_pre,
        bd_pre,
        cs_pre,
        eq_post,
        bd_post,
        cs_post,
        re_post,
        eq_roth=0.0,
        bd_roth=0.0,
        cs_roth=0.0,
        hsa_eq=0.0,
        hsa_bd=0.0,
        hsa_cs=0.0,
    ):
        self.eq_pre = eq_pre
        self.bd_pre = bd_pre
        self.cs_pre = cs_pre

        self.eq_post = eq_post
        self.bd_post = bd_post
        self.cs_post = cs_post

        self.eq_roth = eq_roth
        self.bd_roth = bd_roth
        self.cs_roth = cs_roth

        self.hsa_eq = hsa_eq
        self.hsa_bd = hsa_bd
        self.hsa_cs = hsa_cs

        self.re_post = re_post

        self.eq_ratio_pre = 0
        self.bd_ratio_pre = 0
        self.cs_ratio_pre = 0

        self.eq_ratio_post = 0
        self.bd_ratio_post = 0
        self.cs_ratio_post = 0

        self.eq_ratio_roth = 0
        self.bd_ratio_roth = 0
        self.cs_ratio_roth = 0

        self.eq_ratio_hsa = 0
        self.bd_ratio_hsa = 0
        self.cs_ratio_hsa = 0

    @property
    def total_value_pre(self):
        return self.eq_pre + self.bd_pre + self.cs_pre

    @property
    def total_value_post(self):
        return self.eq_post + self.bd_post + self.cs_post

    @property
    def total_value_roth(self):
        return self.eq_roth + self.bd_roth + self.cs_roth

    @property
    def total_value_hsa(self):
        return self.hsa_eq + self.hsa_bd + self.hsa_cs

    @property
    def total_value(self):
        return (
            self.total_value_pre
            + self.total_value_post
            + self.total_value_roth
            + self.total_value_hsa
        )

    @property
    def total_value_including_real_estate(self):
        return self.total_value + self.re_post

    @property
    def total_value_cash(self):
        return self.cs_pre + self.cs_post + self.cs_roth + self.hsa_cs

    @property
    def total_value_bonds(self):
        return self.bd_pre + self.bd_post + self.bd_roth + self.hsa_bd

    @property
    def total_value_equity(self):
        return self.eq_pre + self.eq_post + self.eq_roth + self.hsa_eq