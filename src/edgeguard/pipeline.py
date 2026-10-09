"""Run the full chain: three detectors -> 2-of-3 vote -> state machine."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .detectors import IsolationForestDetector, RobustZDetector, SuddenChangeDetector
from .features import as_array
from .mitigation import Action, MitigationController, State
from .voting import k_of_n_vote


@dataclass
class PipelineConfig:
    window: int = 96
    z_threshold: float = 3.5
    change_threshold: float = 5.0
    contamination: float = 0.01
    k: int = 2
    seed: int = 42
    block_after: int = 2
    quarantine_after: int = 5
    release_after: int = 10


@dataclass
class PipelineResult:
    flags: dict[str, np.ndarray]
    alarm: np.ndarray
    states: list[State] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)


def run_pipeline(x, train_size: int, config: PipelineConfig | None = None) -> PipelineResult:
    """Fit on the first `train_size` samples (assumed attack-free) and run on all of them."""
    cfg = config or PipelineConfig()
    arr = as_array(x)
    if not cfg.window < train_size < arr.size:
        raise ValueError("train_size must be larger than window and smaller than the data")

    forest = IsolationForestDetector(
        window=cfg.window, contamination=cfg.contamination, random_state=cfg.seed
    ).fit(arr[:train_size])
    detectors = [
        RobustZDetector(cfg.window, cfg.z_threshold),
        SuddenChangeDetector(cfg.window, cfg.change_threshold),
        forest,
    ]
    flags = {d.name: d.predict(arr) for d in detectors}
    alarm = k_of_n_vote(list(flags.values()), k=cfg.k)

    controller = MitigationController(cfg.block_after, cfg.quarantine_after, cfg.release_after)
    steps = controller.run(alarm)
    return PipelineResult(
        flags=flags,
        alarm=alarm,
        states=[s for s, _ in steps],
        actions=[a for _, a in steps],
    )
