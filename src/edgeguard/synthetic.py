"""Synthetic utility data with labelled attacks.

The thesis uses real datasets (UCI household power, Edge-IIoTset). They are large
and have their own licenses, so this repository ships a small synthetic generator
instead. It gives the tests and the demo a stream with known attack positions.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SyntheticStream:
    values: np.ndarray  # the readings
    labels: np.ndarray  # True where an attack is active
    train_size: int  # first samples are attack-free and can be used for fitting


def make_utility_stream(
    n: int = 3000,
    train_size: int = 1000,
    period: int = 96,
    seed: int = 42,
) -> SyntheticStream:
    """Create a daily-cycle consumption signal with three attack types.

    - spike: false data injection, a few readings pushed far up
    - shift: spoofing, the level suddenly moves and stays there for a while
    - flood: denial-of-service, readings become very noisy
    Attacks are only placed after `train_size`.
    """
    if n < train_size + 500:
        raise ValueError("n must be at least train_size + 500")
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    base = 10.0 + 2.0 * np.sin(2 * np.pi * t / period) + 0.5 * np.sin(2 * np.pi * t / (7 * period))
    values = base + rng.normal(0.0, 0.15, n)
    labels = np.zeros(n, dtype=bool)

    span = n - train_size
    # spike attack: 5 short bursts
    for k in range(5):
        start = train_size + int(span * (0.05 + 0.04 * k))
        values[start : start + 3] += 6.0
        labels[start : start + 3] = True
    # shift attack
    s0 = train_size + int(span * 0.40)
    values[s0 : s0 + 40] += 4.0
    labels[s0 : s0 + 40] = True
    # flood attack
    f0 = train_size + int(span * 0.70)
    values[f0 : f0 + 30] += rng.normal(0.0, 3.0, 30)
    labels[f0 : f0 + 30] = True

    return SyntheticStream(values=values, labels=labels, train_size=train_size)
