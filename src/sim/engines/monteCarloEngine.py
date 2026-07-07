# monteCarloEngine.py

import numpy as np
from src.utils.io_utils import (
    load_historical_asset_returns_csv,
    load_historical_inflation_csv,
)


def _prepare_historical_window_data(sim_config):
    """
    Load and cache historical asset return arrays plus matching historical
    inflation arrays and valid rolling-window start indices for the configured
    simulation length.

    Cached fields on sim_config
    ---------------------------
    _hist_years
    _hist_eq
    _hist_bd
    _hist_cs
    _hist_re
    _hist_inflation
    _hist_window_start_indices
    _hist_num_windows
    """
    hist = load_historical_asset_returns_csv(
        filename=sim_config.historical_asset_returns_file
    )
    infl = load_historical_inflation_csv(
        filename=sim_config.historical_inflation_file
    )

    years = np.asarray(hist["years"], dtype=int)
    eq = np.asarray(hist["eq"], dtype=float)
    bd = np.asarray(hist["bd"], dtype=float)
    cs = np.asarray(hist["cs"], dtype=float)
    re = np.asarray(hist["re"], dtype=float)

    infl_years = np.asarray(infl["years"], dtype=int)
    inflation = np.asarray(infl["inflation"], dtype=float)

    if len(years) != len(infl_years) or not np.array_equal(years, infl_years):
        raise ValueError(
            "Historical asset return years and historical inflation years must match exactly. "
            f"Returns years: {years[0]}..{years[-1]} ({len(years)} rows), "
            f"Inflation years: {infl_years[0]}..{infl_years[-1]} ({len(infl_years)} rows)"
        )

    n_years = len(years)
    window_len = int(sim_config.years_to_simulate)

    if window_len <= 0:
        raise ValueError("years_to_simulate must be > 0 for rolling historical windows")

    if n_years < window_len:
        raise ValueError(
            f"Historical data file has only {n_years} rows, but "
            f"years_to_simulate is {window_len}. "
            f"Need at least as many historical years as the simulation horizon."
        )

    if getattr(sim_config, "historical_window_mode", "rolling_overlapping_all") != "rolling_overlapping_all":
        raise ValueError(
            f"Unsupported historical_window_mode: {sim_config.historical_window_mode}"
        )

    # Overlapping rolling windows:
    # for N years of data and window length W, valid start indices are 0..N-W
    start_indices = np.arange(0, n_years - window_len + 1, dtype=int)

    if len(start_indices) == 0:
        raise ValueError(
            "No valid rolling historical windows available for the configured horizon"
        )

    sim_config._hist_years = years
    sim_config._hist_eq = eq
    sim_config._hist_bd = bd
    sim_config._hist_cs = cs
    sim_config._hist_re = re
    sim_config._hist_inflation = inflation
    sim_config._hist_window_start_indices = start_indices
    sim_config._hist_num_windows = int(len(start_indices))


def prepare_market_path_sampling(sim_config):
    """
    Precompute market-path data once per run.

    For Monte Carlo path-based annual sampling, this stores:
      - sim_config._mc_means
      - sim_config._mc_std_devs
      - sim_config._mc_cov_matrix
      - sim_config._mc_cholesky

    For rolling historical windows, this stores:
      - sim_config._hist_years
      - sim_config._hist_eq
      - sim_config._hist_bd
      - sim_config._hist_cs
      - sim_config._hist_re
      - sim_config._hist_window_start_indices
      - sim_config._hist_num_windows
    """

    # --- reset Monte Carlo caches ---
    sim_config._mc_means = np.array([
        sim_config.eq_mean,
        sim_config.bd_mean,
        sim_config.cs_mean,
        sim_config.re_mean,
    ], dtype=float)

    sim_config._mc_std_devs = np.array([
        sim_config.eq_std,
        sim_config.bd_std,
        sim_config.cs_std,
        sim_config.re_std,
    ], dtype=float)

    sim_config._mc_cov_matrix = None
    sim_config._mc_cholesky = None

    # --- reset historical caches ---
    sim_config._hist_years = None
    sim_config._hist_eq = None
    sim_config._hist_bd = None
    sim_config._hist_cs = None
    sim_config._hist_re = None
    sim_config._hist_inflation = None
    sim_config._hist_window_start_indices = None
    sim_config._hist_num_windows = 0

    is_monte_carlo = (
        sim_config.subplot_mode == "monte_carlo"
        and sim_config.sim_type == "portfolio_sim"
    )

    if not is_monte_carlo:
        return

    mode = getattr(sim_config, "monte_carlo_mode", "pathBasedAnnualSampling")

    if mode == "pathBasedAnnualSampling":
        use_correlated = bool(getattr(sim_config, "use_correlated_returns", True))
        if not use_correlated:
            return

        corr_matrix = np.asarray(sim_config.return_correlation_matrix, dtype=float)
        sim_config._mc_cov_matrix = build_covariance_matrix(
            sim_config._mc_std_devs,
            corr_matrix
        )
        sim_config._mc_cholesky = np.linalg.cholesky(sim_config._mc_cov_matrix)
        return

    if mode == "rollingHistoricalWindows":
        _prepare_historical_window_data(sim_config)
        return


    raise ValueError(f"Unsupported monte_carlo_mode: {mode}")

import copy
import numpy as np


def _sequence_risk_length_to_years(length_label):
    mapping = {
        "Short": 1,
        "Medium": 3,
        "Long": 5,
    }
    return mapping.get(length_label, 3)


def _sequence_risk_depth_to_base_shocks(depth_label):
    """
    Returns per-asset shocked annual returns for the peak downturn year.

    These values REPLACE the original sampled annual returns in the
    affected window.

    Cash is intentionally left unchanged by this function. The caller
    should preserve original cash returns.
    """
    mapping = {
        "Mild": {
            "eq": -0.10,
            "bd":  0.00,
            "re": -0.05,
        },
        "Moderate": {
            "eq": -0.20,
            "bd": -0.05,
            "re": -0.10,
        },
        "Severe": {
            "eq": -0.35,
            "bd": -0.10,
            "re": -0.20,
        },
    }
    return mapping.get(depth_label, mapping["Moderate"])


def _sequence_risk_profile_for_length(length_label):
    """
    Front-loaded severity profile.
    """
    mapping = {
        "Short":  [1.00],
        "Medium": [1.00, 0.60, 0.20],
        "Long":   [1.00, 0.70, 0.40, 0.15, 0.00],
    }
    return mapping.get(length_label, mapping["Medium"])


def _resolve_sequence_risk_start_year(
    *,
    sim_config,
    years_to_simulate,
    withdrawal_start_year,
):
    """
    Returns the simulation-year index (1..years_to_simulate) where the
    downturn starts.

    Option B anchor:
    - Early/Mid/Late are anchored to the first withdrawal year.
    - Custom is anchored to the first withdrawal year plus user offset.

    If no valid withdrawal start year is available, fall back to year 1.
    """
    timing = getattr(sim_config, "sequence_risk_timing", "None")
    offset = int(getattr(sim_config, "sequence_risk_start_year_offset", 0) or 0)

    anchor_year = withdrawal_start_year if withdrawal_start_year is not None else 1
    anchor_year = max(1, min(int(anchor_year), int(years_to_simulate)))

    remaining_years = max(1, years_to_simulate - anchor_year + 1)

    if timing == "Early downturn":
        start_year = anchor_year

    elif timing == "Mid-retirement downturn":
        # roughly halfway through withdrawal phase
        start_year = anchor_year + int(round((remaining_years - 1) * 0.50))

    elif timing == "Late downturn":
        # roughly 75% into withdrawal phase
        start_year = anchor_year + int(round((remaining_years - 1) * 0.75))

    elif timing == "Custom":
        start_year = anchor_year + offset

    else:
        # Covers "None" and any unknown value
        return None

    start_year = max(1, min(int(start_year), int(years_to_simulate)))
    return start_year


def apply_sequence_risk_overlay(
    market_path,
    sim_config,
    years_to_simulate,
    withdrawal_start_year,
):
    """
    Applies a sequence-risk downturn window to an already-generated market path.

    Returns
    -------
    (adjusted_market_path, metadata_dict)

    metadata_dict keys:
      - enabled
      - applied
      - start_year
      - end_year
      - length_years
      - timing
      - depth
    """
    enabled = bool(getattr(sim_config, "sequence_risk_enabled", False))
    timing = getattr(sim_config, "sequence_risk_timing", "None")

    metadata = {
        "enabled": enabled,
        "applied": False,
        "start_year": None,
        "end_year": None,
        "length_years": 0,
        "timing": timing,
        "depth": getattr(sim_config, "sequence_risk_depth", "Moderate"),
    }

    if not enabled or timing == "None":
        return market_path, metadata

    start_year = _resolve_sequence_risk_start_year(
        sim_config=sim_config,
        years_to_simulate=years_to_simulate,
        withdrawal_start_year=withdrawal_start_year,
    )

    if start_year is None:
        return market_path, metadata

    length_label = getattr(sim_config, "sequence_risk_length", "Medium")
    length_years = _sequence_risk_length_to_years(length_label)
    profile = _sequence_risk_profile_for_length(length_label)
    base_shocks = _sequence_risk_depth_to_base_shocks(
        getattr(sim_config, "sequence_risk_depth", "Moderate")
    )

    adjusted = {
        "eq": np.array(market_path["eq"], copy=True),
        "bd": np.array(market_path["bd"], copy=True),
        "cs": np.array(market_path["cs"], copy=True),
        "re": np.array(market_path["re"], copy=True),
    }

    last_year_applied = None

    for i, scale in enumerate(profile):
        year = start_year + i
        if year > years_to_simulate:
            break

        adjusted["eq"][year] = base_shocks["eq"] * scale
        adjusted["bd"][year] = base_shocks["bd"] * scale
        adjusted["re"][year] = base_shocks["re"] * scale

        # Preserve original cash return
        adjusted["cs"][year] = market_path["cs"][year]

        last_year_applied = year

    if last_year_applied is None:
        return market_path, metadata

    metadata["applied"] = True
    metadata["start_year"] = start_year
    metadata["end_year"] = last_year_applied
    metadata["length_years"] = max(0, last_year_applied - start_year + 1)

    return adjusted, metadata


def _build_historical_market_path(sim_config, years_to_simulate, sim_index):
    """
    Build one market path from the cached historical rolling windows.

    Parameters
    ----------
    sim_index : int
        Zero-based simulation index. In rolling historical mode, each sim_index
        maps to one overlapping historical window.
    """
    if sim_index is None:
        raise ValueError(
            "sim_index is required for rollingHistoricalWindows mode"
        )

    if sim_config._hist_window_start_indices is None or sim_config._hist_num_windows <= 0:
        raise RuntimeError(
            "Historical rolling-window data not prepared. "
            "Call prepare_market_path_sampling(sim_config) before simulation."
        )

    sim_index = int(sim_index)

    if sim_index < 0 or sim_index >= sim_config._hist_num_windows:
        raise IndexError(
            f"Historical sim_index {sim_index} is out of range for "
            f"{sim_config._hist_num_windows} available rolling windows."
        )

    start_idx = int(sim_config._hist_window_start_indices[sim_index])
    end_idx = start_idx + int(years_to_simulate)

    eq = np.zeros(years_to_simulate + 1)
    bd = np.zeros(years_to_simulate + 1)
    cs = np.zeros(years_to_simulate + 1)
    re = np.zeros(years_to_simulate + 1)

    eq[1:] = sim_config._hist_eq[start_idx:end_idx]
    bd[1:] = sim_config._hist_bd[start_idx:end_idx]
    cs[1:] = sim_config._hist_cs[start_idx:end_idx]
    re[1:] = sim_config._hist_re[start_idx:end_idx]

    return {"eq": eq, "bd": bd, "cs": cs, "re": re}


def build_historical_inflation_rate_path(sim_config, years_to_simulate, sim_index):
    """
    Returns annual inflation rates aligned to the selected historical window.

    Index 0 is 0.0 so year indexing aligns with simulation year indexing.
    """
    if sim_index is None:
        raise ValueError("sim_index is required for rollingHistoricalWindows mode")

    if sim_config._hist_window_start_indices is None or sim_config._hist_num_windows <= 0:
        raise RuntimeError(
            "Historical rolling-window data not prepared. "
            "Call prepare_market_path_sampling(sim_config) before simulation."
        )

    sim_index = int(sim_index)

    if sim_index < 0 or sim_index >= sim_config._hist_num_windows:
        raise IndexError(
            f"Historical sim_index {sim_index} is out of range for "
            f"{sim_config._hist_num_windows} available rolling windows."
        )

    start_idx = int(sim_config._hist_window_start_indices[sim_index])
    end_idx = start_idx + int(years_to_simulate)

    inflation_rates = np.zeros(years_to_simulate + 1, dtype=float)
    inflation_rates[1:] = sim_config._hist_inflation[start_idx:end_idx]

    return inflation_rates


def build_historical_inflation_factor_path(sim_config, years_to_simulate, sim_index):
    """
    Returns cumulative inflation factors aligned to the selected historical window.

    factor[0] = 1.0
    factor[1] = 1 + inflation_year_1
    factor[2] = (1 + inflation_year_1) * (1 + inflation_year_2)
    etc.
    """
    inflation_rates = build_historical_inflation_rate_path(
        sim_config=sim_config,
        years_to_simulate=years_to_simulate,
        sim_index=sim_index,
    )

    factors = np.ones(years_to_simulate + 1, dtype=float)
    for year in range(1, years_to_simulate + 1):
        factors[year] = factors[year - 1] * (1.0 + inflation_rates[year])

    return factors


def generate_market_path(sim_config, years_to_simulate, sim_index=None):
    """
    Generate a sequence of yearly market returns for one simulation path.

    Returns
    -------
    dict
        {
            "eq": np.ndarray shape (years_to_simulate + 1,),
            "bd": np.ndarray shape (years_to_simulate + 1,),
            "cs": np.ndarray shape (years_to_simulate + 1,),
            "re": np.ndarray shape (years_to_simulate + 1,),
        }

    Index 0 is unused for returns so that path[year] lines up naturally
    with simulation year indexing where year 0 is the initial state.
    """

    eq = np.zeros(years_to_simulate + 1)
    bd = np.zeros(years_to_simulate + 1)
    cs = np.zeros(years_to_simulate + 1)
    re = np.zeros(years_to_simulate + 1)

    is_monte_carlo = (
        sim_config.subplot_mode == "monte_carlo"
        and sim_config.sim_type == "portfolio_sim"
    )

    if not is_monte_carlo:
        eq[1:] = sim_config.eq_mean
        bd[1:] = sim_config.bd_mean
        cs[1:] = sim_config.cs_mean
        re[1:] = sim_config.re_mean
        return {"eq": eq, "bd": bd, "cs": cs, "re": re}

    mode = getattr(sim_config, "monte_carlo_mode", "pathBasedAnnualSampling")

    if mode == "pathBasedAnnualSampling":
        use_correlated = bool(getattr(sim_config, "use_correlated_returns", True))

        means = sim_config._mc_means
        std_devs = sim_config._mc_std_devs

        if means is None or std_devs is None:
            raise RuntimeError(
                "Monte Carlo sampling data not prepared. "
                "Call prepare_market_path_sampling(sim_config) before simulation."
            )

        if use_correlated:
            chol = sim_config._mc_cholesky
            if chol is None:
                raise RuntimeError(
                    "Cholesky factor not prepared. "
                    "Call prepare_market_path_sampling(sim_config) before simulation."
                )

            z = np.random.normal(size=(years_to_simulate, 4))
            draws = z @ chol.T + means
        else:
            draws = np.column_stack([
                np.random.normal(sim_config.eq_mean, sim_config.eq_std, years_to_simulate),
                np.random.normal(sim_config.bd_mean, sim_config.bd_std, years_to_simulate),
                np.random.normal(sim_config.cs_mean, sim_config.cs_std, years_to_simulate),
                np.random.normal(sim_config.re_mean, sim_config.re_std, years_to_simulate),
            ])

        eq[1:] = draws[:, 0]
        bd[1:] = draws[:, 1]
        cs[1:] = draws[:, 2]
        re[1:] = draws[:, 3]

        return {"eq": eq, "bd": bd, "cs": cs, "re": re}

    elif mode == "independentAnnualSampling":
        # Keep this mode intact. The yearly loop may sample per-year elsewhere;
        # these arrays remain placeholders for interface compatibility.
        eq[1:] = np.nan
        bd[1:] = np.nan
        cs[1:] = np.nan
        re[1:] = np.nan
        return {"eq": eq, "bd": bd, "cs": cs, "re": re}

    elif mode == "rollingHistoricalWindows":
        return _build_historical_market_path(
            sim_config=sim_config,
            years_to_simulate=years_to_simulate,
            sim_index=sim_index,
        )

    else:
        raise ValueError(
            f"Unsupported monte_carlo_mode: {mode}"
        )


def validate_correlation_matrix(corr_matrix, atol=1e-10):
    """
    Validate that a correlation matrix is usable for multivariate sampling.

    Requirements:
      - shape is (4, 4)
      - symmetric
      - diagonal entries are 1
      - all values are in [-1, 1]
      - positive semidefinite
    """
    corr_matrix = np.asarray(corr_matrix, dtype=float)

    if corr_matrix.shape != (4, 4):
        raise ValueError(f"Correlation matrix must be shape (4, 4), got {corr_matrix.shape}")

    if not np.allclose(corr_matrix, corr_matrix.T, atol=atol):
        raise ValueError("Correlation matrix must be symmetric")

    if not np.allclose(np.diag(corr_matrix), 1.0, atol=atol):
        raise ValueError("Correlation matrix diagonal must be all 1.0")

    if np.any(corr_matrix < -1.0 - atol) or np.any(corr_matrix > 1.0 + atol):
        raise ValueError("Correlation matrix entries must be between -1 and 1")

    eigvals = np.linalg.eigvalsh(corr_matrix)
    if np.min(eigvals) < -1e-8:
        raise ValueError(
            "Correlation matrix must be positive semidefinite. "
            f"Minimum eigenvalue was {np.min(eigvals):.12f}"
        )


def build_covariance_matrix(std_devs, corr_matrix):
    """
    Convert per-asset standard deviations + correlation matrix
    into a covariance matrix.

    cov = D @ corr @ D
    where D = diag(std_devs)
    """
    std_devs = np.asarray(std_devs, dtype=float)
    corr_matrix = np.asarray(corr_matrix, dtype=float)

    if std_devs.shape != (4,):
        raise ValueError(f"std_devs must have shape (4,), got {std_devs.shape}")

    validate_correlation_matrix(corr_matrix)

    std_diag = np.diag(std_devs)
    cov_matrix = std_diag @ corr_matrix @ std_diag

    # mild symmetry cleanup for floating-point noise
    cov_matrix = (cov_matrix + cov_matrix.T) / 2.0

    eigvals = np.linalg.eigvalsh(cov_matrix)
    if np.min(eigvals) < -1e-8:
        raise ValueError(
            "Covariance matrix must be positive semidefinite. "
            f"Minimum eigenvalue was {np.min(eigvals):.12f}"
        )

    return cov_matrix


def debug_validate_correlated_sampling(sim_config, sample_size=100000):
    """
    Debug helper to compare target vs empirical correlation matrix.
    """
    means = np.array([
        sim_config.eq_mean,
        sim_config.bd_mean,
        sim_config.cs_mean,
        sim_config.re_mean,
    ], dtype=float)

    std_devs = np.array([
        sim_config.eq_std,
        sim_config.bd_std,
        sim_config.cs_std,
        sim_config.re_std,
    ], dtype=float)

    corr_matrix = np.asarray(sim_config.return_correlation_matrix, dtype=float)
    cov_matrix = build_covariance_matrix(std_devs, corr_matrix)

    draws = np.random.multivariate_normal(
        mean=means,
        cov=cov_matrix,
        size=sample_size,
        check_valid="raise",
    )

    empirical_corr = np.corrcoef(draws, rowvar=False)

    print("Target correlation matrix:")
    print(corr_matrix)
    print()
    print("Empirical correlation matrix:")
    print(empirical_corr)