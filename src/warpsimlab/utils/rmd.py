# ============================================
# rmd.py
# Required function for RMD calculations
# ============================================

from .constants import UNIFORM_LIFETIME_TABLE, RMD_START_AGE


def calculate_rmd(balance, age):
    """Return RMD for a given balance and age using the uniform lifetime table."""
    if age < RMD_START_AGE:
        return 0
    divisor = UNIFORM_LIFETIME_TABLE.get(age, 2.0)  # fallback for age>120
    return balance / divisor

