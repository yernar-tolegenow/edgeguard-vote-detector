"""Simple detection metrics."""

from __future__ import annotations

import numpy as np


def confusion(y_true, y_pred) -> dict[str, int]:
    yt = np.asarray(y_true, dtype=bool)
    yp = np.asarray(y_pred, dtype=bool)
    if yt.shape != yp.shape:
        raise ValueError("y_true and y_pred must have the same length")
    return {
        "tp": int(np.sum(yt & yp)),
        "fp": int(np.sum(~yt & yp)),
        "fn": int(np.sum(yt & ~yp)),
        "tn": int(np.sum(~yt & ~yp)),
    }


def scores(y_true, y_pred) -> dict[str, float]:
    """Precision, recall, F1 and false-alarm rate (FP among normal samples)."""
    c = confusion(y_true, y_pred)
    precision = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else 0.0
    recall = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    far = c["fp"] / (c["fp"] + c["tn"]) if c["fp"] + c["tn"] else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "false_alarm_rate": far}
