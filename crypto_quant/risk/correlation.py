"""
Advanced Correlation Module (Quant-Grade)

Adds:
- Return conversion (price → returns)
- NaN handling
- Minimum observation filtering
- Rolling correlation support
- Stable ranking
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional


class CorrelationError(Exception):
    pass


# =========================
# Core Function
# =========================

def correlation_filter(
    df: pd.DataFrame,
    threshold: float = 0.9,
    method: str = "pearson",
    use_returns: bool = True,
    min_periods: int = 50
) -> List[Tuple[str, str, float]]:
    """
    Compute high correlations with proper quant safeguards.
    """

    if df is None or df.empty:
        return []

    if len(df.columns) < 2:
        raise CorrelationError("Need at least 2 columns")

    # Convert prices → returns (critical fix)
    if use_returns:
        df = df.pct_change()

    # Clean data
    df = df.replace([np.inf, -np.inf], np.nan).dropna(how="all")

    # Drop columns with too few observations
    valid_cols = [
        col for col in df.columns
        if df[col].count() >= min_periods
    ]

    df = df[valid_cols]

    if len(df.columns) < 2:
        return []

    # Correlation matrix
    corr_matrix = df.corr(method=method, min_periods=min_periods)

    results: List[Tuple[str, str, float]] = []

    cols = corr_matrix.columns

    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            corr_val = corr_matrix.iloc[i, j]

            if pd.isna(corr_val):
                continue

            if abs(corr_val) >= threshold:
                results.append((cols[i], cols[j], float(corr_val)))

    # Sort strongest first
    results.sort(key=lambda x: abs(x[2]), reverse=True)

    return results


# =========================
# Rolling Correlation (IMPORTANT)
# =========================

def rolling_correlation(
    df: pd.DataFrame,
    window: int = 50,
    method: str = "pearson"
) -> pd.DataFrame:
    """
    Compute rolling correlation matrix (captures regime shifts).
    """

    if df is None or df.empty:
        raise CorrelationError("Empty DataFrame")

    returns = df.pct_change().dropna()

    rolling_corr = returns.rolling(window).corr()

    return rolling_corr


# =========================
# Report
# =========================

def correlation_report(
    df: pd.DataFrame,
    threshold: float = 0.9,
    **kwargs
) -> pd.DataFrame:

    pairs = correlation_filter(df, threshold, **kwargs)

    if not pairs:
        return pd.DataFrame(
            columns=["asset_a", "asset_b", "correlation", "abs_correlation"]
        )

    return pd.DataFrame([
        {
            "asset_a": a,
            "asset_b": b,
            "correlation": c,
            "abs_correlation": abs(c)
        }
        for a, b, c in pairs
    ])


# =========================
# Redundancy Reduction (KEY FOR PORTFOLIO)
# =========================

def remove_correlated_assets(
    df: pd.DataFrame,
    threshold: float = 0.9
) -> List[str]:
    """
    Remove highly correlated assets (keep diversified set).
    """

    corr_matrix = df.pct_change().corr().abs()

    upper = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )

    to_drop = [
        column for column in upper.columns
        if any(upper[column] > threshold)
    ]

    return [col for col in df.columns if col not in to_drop]