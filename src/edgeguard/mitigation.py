"""A small state machine that turns alarms into actions.

States and what the gateway does in each one:

    NORMAL      accept traffic
    SUSPECT     accept, but watch closely (one alarm seen)
    BLOCKED     block the source for a short time
    QUARANTINE  isolate the source (alarms keep coming)
    RECOVERY    accept again, but watch closely before going back to NORMAL

Rules are simple on purpose so they are easy to test and explain:
- One alarm moves NORMAL to SUSPECT. Blocking needs `block_after` alarms in a row,
  so a single false alarm never blocks real traffic.
- If alarms continue for `quarantine_after` samples, BLOCKED becomes QUARANTINE.
- After `release_after` quiet samples the source is released to RECOVERY, and after
  another `release_after` quiet samples it is back to NORMAL.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum


class State(str, Enum):
    NORMAL = "normal"
    SUSPECT = "suspect"
    BLOCKED = "blocked"
    QUARANTINE = "quarantine"
    RECOVERY = "recovery"


class Action(str, Enum):
    ACCEPT = "accept"
    MONITOR = "accept_and_monitor"
    BLOCK = "temporary_block"
    QUARANTINE = "quarantine"


ACTION_FOR_STATE = {
    State.NORMAL: Action.ACCEPT,
    State.SUSPECT: Action.MONITOR,
    State.BLOCKED: Action.BLOCK,
    State.QUARANTINE: Action.QUARANTINE,
    State.RECOVERY: Action.MONITOR,
}


@dataclass
class MitigationController:
    block_after: int = 2
    quarantine_after: int = 5
    release_after: int = 10

    def __post_init__(self) -> None:
        if self.block_after < 1 or self.quarantine_after < 1 or self.release_after < 1:
            raise ValueError("all counters must be at least 1")
        self.reset()

    def reset(self) -> None:
        self.state = State.NORMAL
        self.alarm_run = 0  # alarms in a row
        self.quiet_run = 0  # quiet samples in a row

    def step(self, alarm: bool) -> tuple[State, Action]:
        """Feed one vote result and get the new state and action."""
        if alarm:
            self.alarm_run += 1
            self.quiet_run = 0
        else:
            self.quiet_run += 1
            self.alarm_run = 0

        s = self.state
        if s == State.NORMAL:
            if alarm:
                s = State.BLOCKED if self.alarm_run >= self.block_after else State.SUSPECT
        elif s == State.SUSPECT:
            if alarm and self.alarm_run >= self.block_after:
                s = State.BLOCKED
            elif not alarm:
                s = State.NORMAL
        elif s == State.BLOCKED:
            if alarm and self.alarm_run >= self.quarantine_after:
                s = State.QUARANTINE
            elif not alarm and self.quiet_run >= self.release_after:
                s = State.RECOVERY
                self.quiet_run = 0
        elif s == State.QUARANTINE:
            if not alarm and self.quiet_run >= self.release_after:
                s = State.RECOVERY
                self.quiet_run = 0
        elif s == State.RECOVERY:
            if alarm:
                s = State.BLOCKED
            elif self.quiet_run >= self.release_after:
                s = State.NORMAL

        self.state = s
        return s, ACTION_FOR_STATE[s]

    def run(self, alarms: Iterable[bool]) -> list[tuple[State, Action]]:
        """Run the controller over a whole sequence, starting from NORMAL."""
        self.reset()
        return [self.step(bool(a)) for a in alarms]
