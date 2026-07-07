# ============================================
# constants.py
# All default values and tables for Portfolio Simulator
# ============================================


# ---- Personal Finance Defaults ----
DEFAULT_HUSBAND_AGE      = 55
DEFAULT_HUSBAND_RETIRE   = 65
DEFAULT_HUSBAND_INCOME   = 65000
DEFAULT_HUSBAND_SOC      = 19000
DEFAULT_HUSBAND_SOC_AGE  = 65
DEFAULT_HUSBAND_PENSION  = 15000
DEFAULT_HUSBAND_PENSION_AGE = 65
DEFAULT_HUSBAND_PENSION_INFLATION_ADJ = 0
DEFAULT_HUSBAND_ANNUITY  = 0
DEFAULT_HUSBAND_ANNUITY_AGE = 65
DEFAULT_HUSBAND_401K_CONTRIB = 3000
DEFAULT_HUSBAND_401K_MATCH  = 2000

DEFAULT_WIFE_AGE         = 55
DEFAULT_WIFE_RETIRE      = 65
DEFAULT_WIFE_INCOME      = 50000
DEFAULT_WIFE_SOC         = 17000
DEFAULT_WIFE_SOC_AGE     = 65
DEFAULT_WIFE_PENSION     = 0
DEFAULT_WIFE_PENSION_AGE = 65
DEFAULT_WIFE_PENSION_INFLATION_ADJ = 0
DEFAULT_WIFE_ANNUITY     = 15000
DEFAULT_WIFE_ANNUITY_AGE = 65
DEFAULT_WIFE_401K_CONTRIB   = 0
DEFAULT_WIFE_401K_MATCH    = 0

# ---- Portfolio Simulation Defaults ----
DEFAULT_EQUITY_PRE_H       = 50000
DEFAULT_EQUITY_POST_H      = 0
DEFAULT_EQUITY_ROTH_H      = 0

DEFAULT_BOND_PRE_H         = 25000
DEFAULT_BOND_POST_H        = 0
DEFAULT_BOND_ROTH_H        = 0

DEFAULT_CASH_PRE_H         = 25000
DEFAULT_CASH_POST_H        = 2000
DEFAULT_CASH_ROTH_H        = 0

DEFAULT_HSA_CASH_H         = 0
DEFAULT_HSA_EQUITY_H       = 0
DEFAULT_HSA_BOND_H         = 0

DEFAULT_REAL_ESTATE_H      = 50000


DEFAULT_EQUITY_PRE_W       = 0
DEFAULT_EQUITY_POST_W      = 0
DEFAULT_EQUITY_ROTH_W      = 0

DEFAULT_BOND_PRE_W         = 0
DEFAULT_BOND_POST_W        = 0
DEFAULT_BOND_ROTH_W        = 0

DEFAULT_CASH_PRE_W         = 0
DEFAULT_CASH_POST_W        = 2000
DEFAULT_CASH_ROTH_W        = 0

DEFAULT_HSA_CASH_W         = 0
DEFAULT_HSA_EQUITY_W       = 0
DEFAULT_HSA_BOND_W         = 0

DEFAULT_REAL_ESTATE_W      = 50000

DEFAULT_EXPENSES         = 100000

DEFAULT_ENABLE_SECOND_PERSON = 1

# Years to simulate
DEFAULT_INFLATION         = 2.8

DEFAULT_YEARS       = 30
DEFAULT_SIMULATIONS = 500
DEFAULT_FUND_EXPENSE = 0.2

# ---- Asset Class Returns & Volatility ----
EQUITY_MEAN = 12.0
BOND_MEAN   = 5.0
CASH_MEAN   = 4.25

EQUITY_STD = 15.0
BOND_STD   = 7.0
CASH_STD   = 1.0

# Default mean returns (%) for GUI fields
DEFAULT_EQ_MEAN = EQUITY_MEAN
DEFAULT_BD_MEAN = BOND_MEAN
DEFAULT_CS_MEAN = CASH_MEAN

# Default standard deviations (%) for GUI fields
DEFAULT_EQ_STD = EQUITY_STD
DEFAULT_BD_STD = BOND_STD
DEFAULT_CS_STD = CASH_STD

# ---- RMD Constants ----
RMD_START_AGE = 73

# ===============================
# ---- UNIFORM LIFETIME TABLE ----
# For RMD calculations, ages 73-120
# ===============================
UNIFORM_LIFETIME_TABLE = {
    73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9,
    78: 22.0, 79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5,
    83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2, 87: 14.4,
    88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8,
    93: 10.1, 94: 9.5, 95: 8.9, 96: 8.4, 97: 7.8,
    98: 7.3, 99: 6.8, 100: 6.4, 101: 6.0, 102: 5.6,
    103: 5.2, 104: 4.9, 105: 4.6, 106: 4.3, 107: 4.1,
    108: 3.9, 109: 3.7, 110: 3.5, 111: 3.4, 112: 3.3,
    113: 3.1, 114: 3.0, 115: 2.9, 116: 2.8, 117: 2.7,
    118: 2.5, 119: 2.3, 120: 2.0
}


title_font   = ("Arial", 17, "bold")
header_font  = ("Arial", 13, "bold")
body_font    = ("Arial", 12)
meta_font    = ("Arial", 12)





