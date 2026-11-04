import numpy as np
import pytest

from deeplumina_adaptation import (
    concatenate_fc1000,
    ecoc_hinge_scores,
    fit_ecoc_svm,
    predict_ecoc,
    sparse_random_codebook,
    yiq_luminance,
)


def test_yiq_y_equation_and_input_validation():
    rgb = np.array([[[1, 0, 0], [0, 1, 0], [0, 0, 1]]], dtype=np.float32)
    np.testing.assert_allclose(yiq_luminance(rgb), [[0.299, 0.587, 0.114]], atol=1e-7)
    with pytest.raises(ValueError):
        yiq_luminance(np.ones((2, 2), dtype=np.float32))
    with pytest.raises(ValueError):
        yiq_luminance(np.full((1, 1, 3), 2, dtype=np.float32))


def test_fc1000_branch_order_dimension_and_validation():
    rgb = np.tile(np.arange(1000, dtype=np.float32), (2, 1))
    y = rgb + 1000
    out = concatenate_fc1000(rgb, y)
    assert out.shape == (2, 2000)
    np.testing.assert_array_equal(out[:, :1000], rgb)
    np.testing.assert_array_equal(out[:, 1000:], y)
    with pytest.raises(ValueError):
        concatenate_fc1000(rgb[:, :999], y[:, :999])


def test_sparse_random_codebook_is_reproducible_and_valid():
    a = sparse_random_codebook(n_classes=5, seed=42, candidates=250)
    b = sparse_random_codebook(n_classes=5, seed=42, candidates=250)
    np.testing.assert_array_equal(a, b)
    assert a.shape[0] == 5
    assert set(np.unique(a)).issubset({-1, 0, 1})
    for j in range(a.shape[1]):
        assert np.any(a[:, j] == -1) and np.any(a[:, j] == 1)
    cols = [tuple(a[:, j]) for j in range(a.shape[1])]
    assert len(cols) == len(set(cols))
    assert all(tuple(-x for x in c) not in set(cols) for c in cols)


def test_ecoc_fit_ignores_zero_code_rows_and_decoder_tie_is_stable():
    x = np.array([[-2, 0], [-1, 0], [0, 0], [1, 0], [2, 0],
                  [0, -2], [0, -1], [0, 1], [0, 2]], dtype=np.float32)
    y = np.array([0, 0, 1, 1, 1, 2, 2, 3, 3])
    code = np.array([[1, 0], [-1, 1], [0, -1], [0, 1]], dtype=np.int8)
    models = fit_ecoc_svm(x, y, code)
    assert len(models) == 2
    pred, margins, losses = predict_ecoc(x, models, code)
    assert margins.shape == (len(x), 2)
    assert losses.shape == (len(x), 4)
    assert pred.shape == (len(x),)
    # Stubbed all-zero margins give identical unit hinge losses: lower class index wins.
    class ZeroMargin:
        def decision_function(self, features):
            return np.zeros(len(features), dtype=np.float32)

    _, zero_losses = ecoc_hinge_scores(
        np.zeros((1, 2), dtype=np.float32), [ZeroMargin(), ZeroMargin()], code
    )
    assert np.all(zero_losses == 1.0)
    assert int(np.argmin(zero_losses[0])) == 0
