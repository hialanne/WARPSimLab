# portfolioPlotData.py

from dataclasses import dataclass
from typing import Optional, Dict
import numpy as np


@dataclass
class PortfolioPlotData:
    years: np.ndarray
    percentiles: Dict[str, np.ndarray]  # keys: 'pct1', 'pct5', ... 'median'

    # Variants
    median_without_fund_expenses: Optional[np.ndarray] = None
    median_without_taxes: Optional[np.ndarray] = None
    median_without_taxes_or_fund_expenses: Optional[np.ndarray] = None

    # unchanged
    cash: Optional[np.ndarray] = None
    bonds: Optional[np.ndarray] = None
    realestate: Optional[np.ndarray] = None
    pre_tax_assets: Optional[np.ndarray] = None
    post_tax_assets: Optional[np.ndarray] = None
    roth_assets: Optional[np.ndarray] = None
    hsa_assets: Optional[np.ndarray] = None

    raw_total_assets: Optional[np.ndarray] = None

    simulated_shortfall_rate: Optional[float] = None

    def __post_init__(self):
        self.years = np.array(self.years)
        for k, v in self.percentiles.items():
            self.percentiles[k] = np.array(v)

        optional_attrs = [
            "median_without_fund_expenses",
            "median_without_taxes",
            "median_without_taxes_or_fund_expenses",
            "cash",
            "bonds",
            "realestate",
            "pre_tax_assets",
            "post_tax_assets",
            "roth_assets",
            "hsa_assets",
        ]

        for attr in optional_attrs:
            val = getattr(self, attr)
            if val is not None:
                setattr(self, attr, np.array(val))

        if self.raw_total_assets is not None:
            self.raw_total_assets = np.array(self.raw_total_assets)

