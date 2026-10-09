"""Three simple detectors. Each one returns a True/False flag per sample.

Positions without enough history are always False ("warm-up").
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest

from .features import EPS, MAD_SCALE, as_array, ewma, feature_matrix, first_difference, robust_z


class RobustZDetector:
    """Flags a sample whose residual is far from the median of recent residuals.

    The residual is the reading minus its EWMA. Taking the residual first removes
    most of the slow daily cycle, so the score reacts to the attack and not to the
    normal rise and fall of consumption.
    """

    name = "robust_z"

    def __init__(self, window: int = 96, threshold: float = 3.5, alpha: float = 0.3) -> None:
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        self.window = window
        self.threshold = threshold
        self.alpha = alpha

    def predict(self, x) -> np.ndarray:
        arr = as_array(x)
        residual = arr - ewma(arr, self.alpha)
        z = robust_z(residual, self.window)
        return np.nan_to_num(np.abs(z), nan=0.0) > self.threshold


class SuddenChangeDetector:
    """Flags a sharp jump between two samples, whatever the signal level is."""

    name = "sudden_change"

    def __init__(self, window: int = 96, threshold: float = 5.0) -> None:
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        self.window = window
        self.threshold = threshold

    def predict(self, x) -> np.ndarray:
        arr = as_array(x)
        diff = first_difference(arr)
        flags = np.zeros(arr.size, dtype=bool)
        for t in range(self.window + 1, arr.size):
            past = diff[t - self.window : t]
            spread = MAD_SCALE * np.median(np.abs(past - np.median(past))) + EPS
            flags[t] = abs(diff[t]) > self.threshold * spread
        return flags


class IsolationForestDetector:
    """Flags samples whose feature vector looks unusual.

    It must be fitted on a benign (attack-free) part of the stream first.
    """

    name = "isolation_forest"

    def __init__(
        self,
        window: int = 96,
        contamination: float = 0.01,
        random_state: int = 42,
        n_estimators: int = 100,
    ) -> None:
        self.window = window
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
        )
        self.fitted = False

    def fit(self, x_benign) -> IsolationForestDetector:
        feats = feature_matrix(x_benign, self.window)
        rows = feats[~np.isnan(feats).any(axis=1)]
        if len(rows) < 10:
            raise ValueError("benign data is too short for the chosen window")
        self.model.fit(rows)
        self.fitted = True
        return self

    def predict(self, x) -> np.ndarray:
        if not self.fitted:
            raise RuntimeError("call fit() on benign data before predict()")
        feats = feature_matrix(x, self.window)
        ok = ~np.isnan(feats).any(axis=1)
        flags = np.zeros(len(feats), dtype=bool)
        if ok.any():
            flags[ok] = self.model.predict(feats[ok]) == -1
        return flags
