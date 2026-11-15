import numpy as np
import pytest
from scripts.run_top4_fixed_e1_e2 import confidence, exact_budget_mask, gate_mask, metrics, score_matrix


def test_accuracy_and_macro_precision_are_distinct():
    result = metrics(np.array([0, 0, 0, 1]), np.array([0, 0, 0, 0]), np.array([0, 1]))
    assert result['accuracy'] == .75
    assert result['precision_macro'] == .375
    assert result['recall_macro'] == .5
    assert result['macro_f1'] == pytest.approx(3 / 7)


def test_binary_score_conversion_preserves_historical_margin():
    class Model:
        classes_ = np.array([0, 1])
        def decision_function(self, x):
            return np.array([-2., 0., 3.])
    scores = score_matrix(Model(), np.zeros((3, 1)), np.array([0, 1]))
    np.testing.assert_array_equal(confidence(scores, 'margin'), [2, 0, 3])
    np.testing.assert_array_equal(np.argmax(scores, axis=1), [0, 0, 1])


def test_threshold_uses_only_oof_and_test_fractions_can_differ():
    oof = np.array([[0., 1.], [0., 2.], [0., 3.], [0., 4.]])
    test = np.array([[0., .1], [0., .2], [0., .3]])
    mask, threshold = gate_mask(oof, test, .25, 'margin')
    assert threshold == 1.75 and mask.all()


def test_entropy_is_stable_and_orders_uncertainty_in_opposite_direction():
    scores = np.array([[10000., 10000.], [10000., -10000.]])
    entropy = confidence(scores, 'softmax_entropy')
    assert np.isfinite(entropy).all() and entropy[0] > entropy[1]
    assert exact_budget_mask(scores, 1, 'softmax_entropy').tolist() == [True, False]


@pytest.mark.parametrize('gate', ['margin', 'maximum_score', 'softmax_entropy'])
def test_matched_budget_has_exact_count_with_ties(gate):
    scores = np.ones((10, 3))
    mask = exact_budget_mask(scores, 3, gate)
    assert mask.sum() == 3 and mask[:3].all()
