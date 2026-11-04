import numpy as np
import pytest
import local_external_panel as panel


class FakeModel:
    def __init__(self):
        self.params = {}

    def set_params(self, **kwargs):
        self.params.update(kwargs)
        return self

    def fit(self, x, y):
        self.classes_ = np.unique(y)
        return self


def test_classifier_and_training_rows_are_forwarded(monkeypatch):
    calls = []
    model = FakeModel()
    monkeypatch.setattr(panel, "make_model", lambda name, seed: calls.append((name, seed)) or model)
    monkeypatch.setattr(panel, "block_matrices", lambda cache, subset, fit, evaluate, ng:
        (np.ones((len(fit), 2)), np.ones((len(evaluate), 2))))
    monkeypatch.setattr(panel, "training_score_scale", lambda model, x: 2.)
    monkeypatch.setattr(panel, "decision_scores", lambda model, x, scale: np.ones((len(x), 2)))
    fitted, scale, values = panel.fit_member({}, ["a"], np.array([0, 1]), np.array([2]),
        np.array([0, 1, 0]), np.array([0, 1]), "resmlp", 42)
    assert calls == [("resmlp", 42)]
    assert fitted.params["device"] == "cpu"
    assert scale == 2 and values.shape == (1, 2)


def test_rejects_fit_evaluation_overlap():
    with pytest.raises(ValueError, match="overlap"):
        panel.fit_member({}, [], [0], [0], np.array([0]), np.array([0]), "svm", 42)


def test_training_oof_never_uses_external_rows(monkeypatch):
    y = np.array([0, 1] * 10)
    train = np.arange(12)
    calls = []

    def fake(cache, subset, fit, evaluate, labels_y, labels, classifier, seed, ng):
        calls.append((set(fit), set(evaluate), classifier))
        return None, 1., np.ones((len(evaluate), 2))

    monkeypatch.setattr(panel, "fit_member", fake)
    scores, folds = panel.training_oof({}, [("a",)], train, y, np.arange(20),
        np.array([0, 1]), "resmlp", 42, n_splits=3)
    assert np.isfinite(scores[("a",)]).all() and len(folds) == 3
    assert all(not a & b and a | b == set(train) and clf == "resmlp" for a, b, clf in calls)
