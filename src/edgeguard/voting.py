"""Combine detector flags with a k-of-n vote."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def k_of_n_vote(flags: Sequence[np.ndarray], k: int = 2) -> np.ndarray:
    """Return True where at least `k` of the detectors flagged the sample.

    With three detectors and k=2 this is the "2-of-3" rule: one detector alone
    cannot raise an alarm, which keeps false alarms low.
    """
    if len(flags) == 0:
        raise ValueError("need at least one flag array")
    stacked = np.vstack([np.asarray(f, dtype=bool) for f in flags])
    if not 1 <= k <= stacked.shape[0]:
        raise ValueError("k must be between 1 and the number of detectors")
    return stacked.sum(axis=0) >= k
