"""Training-only gate selection for a fixed, duplicate-weighted rescue ensemble."""
import numpy as np
from sklearn.metrics import f1_score

from budgeted_rescue import acquisition_cost, singleton_frontier


def ensemble_scores(scores, members):
    if not members:
        raise ValueError('empty ensemble')
    return np.mean([scores[tuple(m)] for m in members], axis=0)


def select_full_rescue(single_scores, member_scores, members, y, labels, margins,
                       latencies, budget, quantiles=(.1, .25, .5), overhead=.45):
    """Compare base-only with the whole ensemble; never inspect producer validation."""
    rescue = labels[np.argmax(ensemble_scores(member_scores, members), axis=1)]
    points = []
    bases = singleton_frontier(single_scores, y, labels, latencies)
    for base in bases:
        if latencies[base] > budget:
            continue
        prediction = labels[np.argmax(single_scores[base], axis=1)]
        points.append({'base': base, 'members': [], 'quantile': None, 'threshold': None,
                       'training_macro_f1': float(f1_score(y, prediction, average='macro', zero_division=0)),
                       'training_projected_ms': float(latencies[base]),
                       'training_escalation_fraction': 0., 'training_classifier_calls': 1.})
        for q in quantiles:
            threshold = float(np.quantile(margins[base], q))
            gate = margins[base] < threshold
            cost = acquisition_cost(base, members, gate.mean(), latencies, overhead)
            if cost > budget + 1e-10:
                continue
            pred = np.where(gate, rescue, prediction)
            points.append({'base': base, 'members': [list(m) for m in members],
                           'quantile': float(q), 'threshold': threshold,
                           'training_macro_f1': float(f1_score(y, pred, average='macro', zero_division=0)),
                           'training_projected_ms': cost,
                           'training_escalation_fraction': float(gate.mean()),
                           'training_classifier_calls': 1 + float(gate.mean()) * len({tuple(m) for m in members})})
    result = {'feasible': bool(points), 'budget_ms': float(budget), 'base_candidates': bases,
              'criterion': 'full_carlos_rescue', 'points': points}
    if points:
        result['selected'] = min(points, key=lambda p: (-p['training_macro_f1'],
            p['training_projected_ms'], len(p['members']), p['base'],
            -1 if p['quantile'] is None else p['quantile']))
    return result
