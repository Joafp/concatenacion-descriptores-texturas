import numpy as np

from analyze_block_redundancy import linear_cka
from run_carlos_paired_controls import gram_similarities, ensemble_predictions


def test_gram_implementation_matches_carlos_feature_space_cka():
    rng = np.random.default_rng(42)
    x, y = rng.normal(size=(12, 3)), rng.normal(size=(12, 19))
    sim = gram_similarities({"x": x, "y": y, "constant": np.ones((12, 2))})
    np.testing.assert_allclose(sim[("x", "y")], linear_cka(x, y), atol=1e-12)
    np.testing.assert_allclose(sim[("x", "x")], 1., atol=1e-12)
    assert sim[("x", "y")] == sim[("y", "x")]
    assert sim[("x", "constant")] == 0


def test_ensembles_preserve_duplicate_vote_weights_and_label_mapping():
    values = {("a",): np.asarray([[3., 0.]]), ("b",): np.asarray([[0., 1.]])}
    soft, hard = ensemble_predictions(values, [["a"], ["b"], ["b"]], np.asarray([5, 9]))
    assert soft.tolist() == [5]
    assert hard.tolist() == [9]


def test_hard_vote_ties_use_first_ordered_class():
    values = {("a",): np.asarray([[2., 0.]]), ("b",): np.asarray([[0., 2.]])}
    _, hard = ensemble_predictions(values, [["a"], ["b"]], np.asarray([5, 9]))
    assert hard.tolist() == [5]
