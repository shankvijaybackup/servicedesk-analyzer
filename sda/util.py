"""Small shared helpers (deterministic, no side effects)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def to_datetime(series: pd.Series | None) -> pd.Series | None:
    if series is None:
        return None
    return pd.to_datetime(series, errors="coerce", utc=False)


def numeric(series: pd.Series | None) -> pd.Series | None:
    if series is None:
        return None
    return pd.to_numeric(series, errors="coerce")


def compute_mttr_hours(created: pd.Series | None, resolved: pd.Series | None,
                       explicit: pd.Series | None) -> pd.Series | None:
    """Prefer an explicit resolution-time column; else derive from timestamps.

    Returns hours as a float Series, or None if neither source is usable.
    Negative or absurd (>1 year) durations are dropped as data errors.
    """
    if explicit is not None:
        vals = numeric(explicit)
        if vals is not None and vals.notna().sum() > 0:
            vals = vals.where((vals >= 0) & (vals <= 24 * 365))
            return vals
    c = to_datetime(created)
    r = to_datetime(resolved)
    if c is None or r is None:
        return None
    delta = (r - c).dt.total_seconds() / 3600.0
    delta = delta.where((delta >= 0) & (delta <= 24 * 365))
    return delta


def pct(part: float, whole: float) -> float:
    return round(100.0 * part / whole, 1) if whole else 0.0


def safe_round(x, ndigits: int = 1):
    if x is None:
        return None
    try:
        if isinstance(x, float) and (np.isnan(x) or np.isinf(x)):
            return None
        return round(float(x), ndigits)
    except (TypeError, ValueError):
        return None
