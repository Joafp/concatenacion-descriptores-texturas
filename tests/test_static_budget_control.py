import numpy as np
from sklearn.metrics import f1_score
from static_budget_control import macro_f1_labels, select_static_ensembles


def test_macro_f1_matches_reference():
    rng = np.random.default_rng(19)
    for size in (6, 31, 680):
        y = rng.integers(0, 6, size)
        p = rng.integers(0, 6, size)
        assert abs(macro_f1_labels(y, p, np.arange(6)) -
                   f1_score(y, p, labels=np.arange(6), average="macro", zero_division=0)) < 1e-14


def test_budget_and_shared_union_are_exact():
    y = np.array([0, 1, 0, 1])
    scores = {("a",): np.array([[2, 0], [0, 2], [0, 2], [0, 2]]),
              ("a", "b"): np.array([[1, 0], [0, 1], [3, 0], [0, 1]])}
    result = select_static_ensembles(scores, y, np.array([0, 1]), {"a": 2., "b": 3.}, [1., 2., 5.])
    assert not result["1.0"]["feasible"]
    assert result["2.0"]["selected"]["members"] == [["a"]]
    assert result["5.0"]["selected"]["training_macro_f1"] == 1.
    assert result["5.0"]["selected"]["projected_ms"] == 5.
    assert result["5.0"]["feasible_combinations"] == 3


def test_ties_do_not_depend_on_mapping_order():
    y = np.array([0, 1])
    scores = {("b",): np.eye(2), ("a",): np.eye(2)}
    kw = dict(y=y, labels=np.array([0, 1]), latencies={"a": 1., "b": 1.}, budgets=[2.])
    a = select_static_ensembles(scores, **kw)
    b = select_static_ensembles(dict(reversed(list(scores.items()))), **kw)
    assert a == b and a["2.0"]["selected"]["members"] == [["a"]]
