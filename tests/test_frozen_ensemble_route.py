import numpy as np
from frozen_ensemble_route import evaluate_route, feature_order


def test_gate_equality_exits_base_without_extra_features():
    called = []
    def acquire(name):
        called.append(name)
        return [1.]
    result = evaluate_route({"base": "a", "threshold": 1., "members": [["b"]]},
                            acquire, lambda _, x: np.array([[1., 0.]]), np.array([0, 1]))
    assert called == ["a"] and not result["escalated"]


def test_duplicate_votes_keep_multiplicity_but_not_extraction_or_calls():
    called = []
    def acquire(name):
        called.append(name)
        return [1.]
    def score(member, x):
        return np.array([[2., 0.]]) if member == ("a",) else np.array([[0., 3.]])
    result = evaluate_route({"members": [["a"], ["a"], ["b"]]}, acquire, score, np.array([0, 1]))
    assert result["prediction"] == 0 and called == ["a", "b"] and result["classifier_calls"] == 2


def test_ngram_keeps_historical_last_position():
    assert feature_order(("a", "rgb_ngram_svd", "z")) == ("a", "z", "rgb_ngram_svd")
