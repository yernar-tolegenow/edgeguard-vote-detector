import numpy as np
import pytest

from edgeguard.mitigation import Action, MitigationController, State
from edgeguard.voting import k_of_n_vote


def test_two_of_three_vote():
    a = np.array([1, 1, 0, 0], dtype=bool)
    b = np.array([1, 0, 1, 0], dtype=bool)
    c = np.array([0, 1, 1, 0], dtype=bool)
    np.testing.assert_array_equal(k_of_n_vote([a, b, c], k=2), [True, True, True, False])
    np.testing.assert_array_equal(k_of_n_vote([a, b, c], k=3), [False, False, False, False])


def test_vote_checks_k():
    with pytest.raises(ValueError):
        k_of_n_vote([np.array([True])], k=2)
    with pytest.raises(ValueError):
        k_of_n_vote([], k=1)


def test_single_alarm_never_blocks():
    ctrl = MitigationController(block_after=2)
    steps = ctrl.run([0, 1, 0, 0])
    assert [s for s, _ in steps] == [State.NORMAL, State.SUSPECT, State.NORMAL, State.NORMAL]
    assert all(a != Action.BLOCK for _, a in steps)


def test_escalation_and_release():
    ctrl = MitigationController(block_after=2, quarantine_after=4, release_after=2)
    states = [s for s, _ in ctrl.run([1, 1, 1, 1, 0, 0, 0, 0])]
    assert states == [
        State.SUSPECT,
        State.BLOCKED,
        State.BLOCKED,
        State.QUARANTINE,
        State.QUARANTINE,
        State.RECOVERY,
        State.RECOVERY,
        State.NORMAL,
    ]


def test_alarm_during_recovery_blocks_again():
    ctrl = MitigationController(block_after=2, quarantine_after=10, release_after=1)
    states = [s for s, _ in ctrl.run([1, 1, 0, 1])]
    assert states[-2] == State.RECOVERY
    assert states[-1] == State.BLOCKED


def test_run_starts_from_normal_each_time():
    ctrl = MitigationController()
    ctrl.run([1, 1, 1])
    assert ctrl.run([0])[0][0] == State.NORMAL


def test_counters_must_be_positive():
    with pytest.raises(ValueError):
        MitigationController(block_after=0)
