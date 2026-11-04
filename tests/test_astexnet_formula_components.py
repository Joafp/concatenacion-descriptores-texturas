import numpy as np
import pytest

from astexnet_formula_components import (
    hellinger_l2, magnitude_histogram, center_histogram, scale_weights,
    weighted_concatenation,
)


def test_hellinger_normalization():
    np.testing.assert_allclose(hellinger_l2([1, 3]), [.5, np.sqrt(.75)])


def test_magnitude_formula_uses_clipping_then_floor_times_seven():
    values = np.arange(101, dtype=float)
    threshold = 99.
    expected = np.floor(np.minimum(values, threshold) / threshold * 7).astype(int)
    np.testing.assert_array_equal(magnitude_histogram(values), np.bincount(expected, minlength=8) / 101)


def test_constant_positive_magnitude_maps_to_last_bin():
    np.testing.assert_array_equal(magnitude_histogram(np.ones((3, 3))), [0] * 7 + [1])


def test_center_threshold_is_strict():
    np.testing.assert_array_equal(center_histogram([1, 1, 1, 1]), [1, 0])
    np.testing.assert_array_equal(center_histogram([0, 1, 2, 3]), [.75, .25])


def test_scale_weights_are_frobenius_and_sum_to_one():
    np.testing.assert_allclose(scale_weights([[[3., 4.]], [[0., 10.]]]), [1/3, 2/3])


def test_weighted_concat_keeps_order_not_voting():
    np.testing.assert_array_equal(weighted_concatenation([[2, 4], [8]], [.25, .75]), [.5, 1, 6])


@pytest.mark.parametrize('function,value', [(hellinger_l2, [0, 0]),
                                         (hellinger_l2, [-1, 2]),
                                         (magnitude_histogram, [0, 0]),
                                         (magnitude_histogram, [-1, 3]),
                                         (center_histogram, [float('nan')]),
                                         (scale_weights, [[[0, 0]]])])
def test_undefined_or_nonfinite_inputs_fail_explicitly(function, value):
    with pytest.raises(ValueError):
        function(value)


def test_invalid_weights_not_silently_renormalized():
    with pytest.raises(ValueError):
        weighted_concatenation([[1], [2]], [.5, .6])
