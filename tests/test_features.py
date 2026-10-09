import numpy as np
import pytest

from edgeguard.features import (
    as_array,
    ewma,
    feature_matrix,
    first_difference,
    robust_z,
    rolling_median_mad,
)


def test_as_array_rejects_bad_input():
    with pytest.raises(ValueError):
        as_array([])
    with pytest.raises(ValueError):
        as_array([[1, 2], [3, 4]])
    with pytest.raises(ValueError):
        as_array([1.0, np.nan])


def test_rolling_median_mad_uses_only_the_past():
    x = np.arange(10, dtype=float)
    med, mad = rolling_median_mad(x, window=3)
    assert np.isnan(med[:3]).all()
    assert med[3] == 1.0  # median of 0, 1, 2 (not of 1, 2, 3)
    assert mad[3] == 1.0


def test_features_do_not_change_when_future_changes():
    """The 'no future data' rule: editing a later sample must not change earlier features."""
    rng = np.random.default_rng(0)
    x = rng.normal(size=300)
    y = x.copy()
    y[250:] += 100.0
    fx = feature_matrix(x, window=20)
    fy = feature_matrix(y, window=20)
    np.testing.assert_array_equal(fx[:250], fy[:250])


def test_robust_z_is_large_for_a_spike():
    rng = np.random.default_rng(1)
    x = rng.normal(0, 1, 200)
    x[150] = 20.0
    z = robust_z(x, window=50)
    assert abs(z[150]) > 10


def test_first_difference_and_ewma():
    x = np.array([1.0, 3.0, 6.0])
    np.testing.assert_array_equal(first_difference(x), [0.0, 2.0, 3.0])
    e = ewma(x, alpha=0.5)
    assert e[0] == 1.0 and e[1] == 1.0  # value at t uses samples before t
    assert e[2] == 2.0
    with pytest.raises(ValueError):
        ewma(x, alpha=0.0)


def test_window_must_be_reasonable():
    with pytest.raises(ValueError):
        rolling_median_mad([1.0, 2.0, 3.0], window=2)
