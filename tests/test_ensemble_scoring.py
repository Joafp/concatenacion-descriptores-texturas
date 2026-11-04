"""Training-derived member scales must not depend on inference batch makeup."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ensemble_scoring import decision_scores, training_score_scale  # noqa: E402


class LinearScoreModel:
    def decision_function(self, x):
        return np.asarray(x)[:, 0] * 2.0 - 1.0


def test_frozen_training_scale_is_batch_independent():
    model = LinearScoreModel()
    x_train = np.array([[0.0], [0.5], [1.0]])
    x_test = np.array([[0.2], [0.8], [100.0]])
    scale = training_score_scale(model, x_train)

    together = decision_scores(model, x_test, scale)
    separately = np.concatenate([
        decision_scores(model, x_test[i:i + 1], scale)
        for i in range(len(x_test))
    ])

    np.testing.assert_allclose(together, separately, rtol=0.0, atol=0.0)
