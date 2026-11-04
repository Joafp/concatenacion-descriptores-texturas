import numpy as np
from carlos_hybrid import ensemble_scores, select_full_rescue


def test_duplicate_members_keep_vote_weight():
    scores = {('a',): np.array([[4., 0.]]), ('b',): np.array([[0., 5.]])}
    assert ensemble_scores(scores, [('a',), ('b',)]).argmax() == 1
    assert ensemble_scores(scores, [('a',), ('a',), ('b',)]).argmax() == 0


def test_full_rescue_reuses_base_cost_and_deduplicates_model_calls():
    y = np.array([0, 1, 0, 1])
    singles = {'base': np.eye(2)[[1, 1, 0, 1]]}
    members = [('base', 'a'), ('base', 'a')]
    result = select_full_rescue(singles, {('base', 'a'): np.eye(2)[y]}, members,
        y, np.arange(2), {'base': np.arange(4)}, {'base': 1., 'a': 2.}, 2.1,
        quantiles=(.5,), overhead=0.)
    chosen = result['selected']
    assert chosen['members'] == [list(m) for m in members]
    assert chosen['training_macro_f1'] == 1.
    assert chosen['training_projected_ms'] == 2.
    assert chosen['training_classifier_calls'] == 1.5


def test_full_rescue_budget_can_return_base_only_or_infeasible():
    y = np.array([0, 1, 0, 1])
    args = ({'base': np.eye(2)[y]}, {('a',): np.eye(2)[y]}, [('a',)], y,
            np.arange(2), {'base': np.arange(4)}, {'base': 1., 'a': 10.})
    assert select_full_rescue(*args, budget=.5)['feasible'] is False
    assert select_full_rescue(*args, budget=1.1)['selected']['members'] == []
