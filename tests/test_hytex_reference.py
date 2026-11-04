import numpy as np
import pytest
import torch
from torch import nn

from hytex_reference import empirical_t75, hytex_descriptor, HyTexFusionHead, fuse_features


def test_source_table_percentiles_follow_inverse_cdf_not_interpolation():
    samples = [[1, 1, 2, 2, 0, 3, 3, 1], [12, 5, 20, 2, 30, 1, 10, 8],
               [1, 0, 2, 1, 0, 2, 1, 1], [4, 6, 5, 7, 6, 5, 4, 6],
               [18, 2, 20, 1, 22, 3, 19, 2]]
    np.testing.assert_array_equal(empirical_t75(samples), [2, 12, 1, 6, 19])
    assert np.percentile(samples[0], 75) != empirical_t75(samples[0])


def test_constant_image_has_defined_ties_and_normalized_histograms():
    feature = hytex_descriptor(np.ones((5, 5)))
    assert feature.shape == (514,) and feature.dtype == np.float32
    assert feature[255] == feature[511] == feature[513] == 1.
    assert np.count_nonzero(feature) == 3
    np.testing.assert_allclose([feature[:256].sum(), feature[256:512].sum(), feature[512:].sum()], 1.)


def test_center_code_uses_global_image_mean_not_local_window_mean():
    gray = np.zeros((5, 5))
    gray[-1, -1] = 100
    feature = hytex_descriptor(gray)
    np.testing.assert_array_equal(feature[512:], [1., 0.])


def test_positive_affine_intensity_change_preserves_descriptor():
    image = np.arange(25).reshape(5, 5)
    np.testing.assert_array_equal(hytex_descriptor(image), hytex_descriptor(3 * image + 4))


@pytest.mark.parametrize('gray', [np.ones((2, 2)), np.ones((3, 3, 3)), [[np.nan] * 3] * 3])
def test_invalid_images_fail(gray):
    with pytest.raises(ValueError):
        hytex_descriptor(gray)


def test_classifier_architecture_and_logits():
    model = HyTexFusionHead(3)
    assert [type(layer) for layer in model] == [nn.Linear, nn.ReLU, nn.Dropout, nn.Linear]
    assert model[2].p == .5 and model.eval()(torch.zeros(2, 1538)).shape == (2, 3)


def test_concat_order_and_dimensions():
    deep, local = torch.ones(2, 1024), torch.full((2, 514), 2.)
    fused = fuse_features(deep, local)
    assert torch.equal(fused[:, :1024], deep) and torch.equal(fused[:, 1024:], local)
    with pytest.raises(ValueError):
        fuse_features(deep[:, :768], local)
