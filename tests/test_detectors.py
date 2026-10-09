import numpy as np
import pytest

from edgeguard.detectors import IsolationForestDetector, RobustZDetector, SuddenChangeDetector


@pytest.fixture
def stream():
    rng = np.random.default_rng(3)
    t = np.arange(1200)
    x = 10 + np.sin(2 * np.pi * t / 96) + rng.normal(0, 0.1, t.size)
    x[900] += 6.0  # one clear spike
    return x


def test_robust_z_flags_spike_and_has_warm_up(stream):
    flags = RobustZDetector(window=96).predict(stream)
    assert flags[900]
    assert not flags[:96].any()


def test_sudden_change_flags_spike(stream):
    flags = SuddenChangeDetector(window=96).predict(stream)
    assert flags[900]


def test_isolation_forest_needs_fit(stream):
    det = IsolationForestDetector(window=96)
    with pytest.raises(RuntimeError):
        det.predict(stream)
    det.fit(stream[:600])
    flags = det.predict(stream)
    assert flags[900]
    assert flags.shape == stream.shape


def test_isolation_forest_is_reproducible(stream):
    a = IsolationForestDetector(window=96, random_state=7).fit(stream[:600]).predict(stream)
    b = IsolationForestDetector(window=96, random_state=7).fit(stream[:600]).predict(stream)
    np.testing.assert_array_equal(a, b)


def test_isolation_forest_rejects_short_training_data():
    with pytest.raises(ValueError):
        IsolationForestDetector(window=50).fit(np.ones(55))


def test_thresholds_must_be_positive():
    with pytest.raises(ValueError):
        RobustZDetector(threshold=0)
    with pytest.raises(ValueError):
        SuddenChangeDetector(threshold=-1)
