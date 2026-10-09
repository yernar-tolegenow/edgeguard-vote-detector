"""Causal features for a single telemetry stream.

"Causal" means every value at time t is computed only from samples before t.
This is the "no future data" rule from the thesis: a real gateway cannot look
ahead, so the tool must not either.
"""

from __future__ import annotations

import numpy as np

MAD_SCALE = 1.4826  # makes MAD comparable to a standard deviation for normal data
EPS = 1e-9


def as_array(x) -> np.ndarray:
    """Convert input to a 1-D float array and check it."""
    arr = np.asarray(x, dtype=float)
    if arr.ndim != 1:
        raise ValueError("input must be a 1-D sequence of numbers")
    if arr.size == 0:
        raise ValueError("input must not be empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError("input must not contain NaN or infinite values")
    return arr


def rolling_median_mad(x, window: int) -> tuple[np.ndarray, np.ndarray]:
    """Median and MAD of the previous `window` samples (current sample excluded).

    The first `window` positions have no full history, so they are NaN.
    """
    if window < 3:
        raise ValueError("window must be at least 3")
    arr = as_array(x)
    med = np.full(arr.size, np.nan)
    mad = np.full(arr.size, np.nan)
    for t in range(window, arr.size):
        past = arr[t - window : t]
        m = np.median(past)
        med[t] = m
        mad[t] = np.median(np.abs(past - m))
    return med, mad


def robust_z(x, window: int) -> np.ndarray:
    """Robust Z-score of each sample against its own recent past."""
    arr = as_array(x)
    med, mad = rolling_median_mad(arr, window)
    return (arr - med) / (MAD_SCALE * mad + EPS)


def first_difference(x) -> np.ndarray:
    """Change from the previous sample. The first value is 0."""
    arr = as_array(x)
    return np.concatenate(([0.0], np.diff(arr)))


def ewma(x, alpha: float = 0.1) -> np.ndarray:
    """Exponentially weighted moving average of the PAST samples.

    Position t holds the average of samples 0..t-1, so it can be used as an
    expected value for sample t.
    """
    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must be in (0, 1]")
    arr = as_array(x)
    out = np.empty(arr.size)
    out[0] = arr[0]
    level = arr[0]
    for t in range(1, arr.size):
        out[t] = level
        level = alpha * arr[t] + (1 - alpha) * level
    return out


def rolling_std(x, window: int) -> np.ndarray:
    """Standard deviation of the previous `window` samples (NaN at the start)."""
    arr = as_array(x)
    out = np.full(arr.size, np.nan)
    for t in range(window, arr.size):
        out[t] = np.std(arr[t - window : t])
    return out


def feature_matrix(x, window: int, alpha: float = 0.1) -> np.ndarray:
    """Stack the features used by the Isolation Forest.

    Columns: robust Z-score, first difference, distance from EWMA, rolling std.
    Rows before `window` contain NaN.
    """
    arr = as_array(x)
    return np.column_stack(
        [
            robust_z(arr, window),
            first_difference(arr),
            arr - ewma(arr, alpha),
            rolling_std(arr, window),
        ]
    )
