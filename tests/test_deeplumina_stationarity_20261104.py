import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_deeplumina_stationarity_20261104 import primal_objective_and_gradient, gradient_ratio


def test_analytic_gradient_matches_finite_difference_with_bias_and_ignored_codes():
    x = np.array([[1., 0.3], [-2., 1.], [0.1, -0.2], [1.2, 0.5]])
    targets = np.array([[1., 0.], [-1., 1.], [0., -1.], [1., -1.]])
    weights = np.array([[0.1, -0.2], [0.05, 0.3]])
    intercepts = np.array([0.1, -0.2])
    _, grad_w, grad_b = primal_objective_and_gradient(x, targets, weights, intercepts, 0.7, 2.0)
    epsilon = 1e-6
    for j in range(2):
        for k in range(2):
            plus, minus = weights.copy(), weights.copy()
            plus[j, k] += epsilon; minus[j, k] -= epsilon
            f_plus = primal_objective_and_gradient(x, targets, plus, intercepts, 0.7, 2.0)[0][j]
            f_minus = primal_objective_and_gradient(x, targets, minus, intercepts, 0.7, 2.0)[0][j]
            assert grad_w[j, k] == pytest.approx((f_plus-f_minus)/(2*epsilon), rel=1e-7, abs=1e-7)
        plus, minus = intercepts.copy(), intercepts.copy()
        plus[j] += epsilon; minus[j] -= epsilon
        f_plus = primal_objective_and_gradient(x, targets, weights, plus, 0.7, 2.0)[0][j]
        f_minus = primal_objective_and_gradient(x, targets, weights, minus, 0.7, 2.0)[0][j]
        assert grad_b[j] == pytest.approx((f_plus-f_minus)/(2*epsilon), rel=1e-7, abs=1e-7)


def test_relative_gradient_is_one_at_origin_and_requires_both_signs():
    x = np.array([[1., 0.], [0., 1.], [2., 3.]])
    y = np.array([[1.], [-1.], [0.]])
    _, _, _, ratio = gradient_ratio(x, y, np.zeros((1, 2)), np.zeros(1))
    assert ratio[0] == pytest.approx(1.0)
    with pytest.raises(ValueError):
        gradient_ratio(x, np.ones((3, 1)), np.zeros((1, 2)), np.zeros(1))
