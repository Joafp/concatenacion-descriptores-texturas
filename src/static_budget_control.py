"""Static, equal-weight ensemble control selected only from training OOF scores.

Exhaustive within the supplied candidate pool and maximum unique member count,
not exhaustive over all concatenations in a descriptor library.
"""
from itertools import combinations
import numpy as np


def macro_f1_labels(y, prediction, labels):
    labels = np.asarray(labels)
    truth = np.searchsorted(labels, y)
    predicted = np.searchsorted(labels, prediction)
    if not np.array_equal(labels[truth], y) or not np.array_equal(labels[predicted], prediction):
        raise ValueError("labels must be sorted and contain all observations")
    counts = np.bincount(truth * len(labels) + predicted,
                         minlength=len(labels) ** 2).reshape(len(labels), len(labels))
    denominator = counts.sum(axis=0) + counts.sum(axis=1)
    return float(np.divide(2.0 * counts.diagonal(), denominator,
                          out=np.zeros(len(labels)), where=denominator != 0).mean())


def select_static_ensembles(scores, y, labels, latencies, budgets, max_members=3):
    """No producer-validation labels, scores, predictions or metrics accepted."""
    if max_members < 1 or not budgets or min(budgets) <= 0:
        raise ValueError("positive budgets and member bound required")
    candidates = sorted(scores)
    if not candidates or not np.array_equal(np.unique(y), labels):
        raise ValueError("complete training class coverage required")
    shape = (len(y), len(labels))
    for member, array in scores.items():
        if not member or len(set(member)) != len(member):
            raise ValueError("each candidate must contain unique descriptor blocks")
        if np.shape(array) != shape or not np.isfinite(array).all():
            raise ValueError("invalid training score array")
        if any(not np.isfinite(latencies[n]) or latencies[n] < 0 for n in member):
            raise ValueError("invalid acquisition cost")
    best, counts = {}, {float(b): 0 for b in budgets}
    visited = 0
    for size in range(1, min(max_members, len(candidates)) + 1):
        for members in combinations(candidates, size):
            union = sorted({n for member in members for n in member})
            cost = float(sum(latencies[n] for n in union))
            feasible = [float(b) for b in budgets if cost <= b + 1e-10]
            if not feasible:
                continue
            score = np.sum([scores[m] for m in members], axis=0)
            quality = macro_f1_labels(y, labels[np.argmax(score, axis=1)], labels)
            point = {"members": [list(m) for m in members], "blocks": union,
                     "training_macro_f1": quality, "projected_ms": cost,
                     "classifier_calls": size}
            key = (-quality, cost, size, members)
            visited += 1
            for budget in feasible:
                counts[budget] += 1
                if budget not in best or key < best[budget][0]:
                    best[budget] = (key, point)
    return {str(float(b)): {"feasible": float(b) in best,
             "budget_ms": float(b), "feasible_combinations": counts[float(b)],
             "selected": best[float(b)][1] if float(b) in best else None,
             "visited_unique_combinations": visited}
            for b in budgets}
