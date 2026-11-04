"""Deterministic training-OOF selection under a projected mean acquisition budget.

Budgets constrain the estimated mean on selection data, not every image or an
unknown evaluation distribution. Classifier latency is not in this profile.
"""

import numpy as np
from sklearn.metrics import f1_score


def acquisition_cost(base, members, escalation_rate, latencies, overhead):
    union = {block for subset in members for block in subset}
    if not members:
        return float(latencies[base])
    return float(latencies[base] + overhead
                 + escalation_rate * sum(latencies[block] for block in union - {base}))


def singleton_frontier(scores, y, labels, latencies):
    quality = {name: float(f1_score(y, labels[np.argmax(value, axis=1)],
                                    average="macro", zero_division=0))
               for name, value in scores.items()}
    return sorted(name for name in scores if not any(
        quality[other] >= quality[name] and latencies[other] <= latencies[name]
        and (quality[other] > quality[name] or latencies[other] < latencies[name])
        for other in scores if other != name))


def select_policy(single_scores, member_scores, y, labels, margins, latencies,
                  budget, quantiles=(.1, .25, .5), max_members=3, overhead=.45,
                  criterion="marginal_cost"):
    """Select using only supplied training OOF scores; no validation inputs.

    Both criteria use identical candidates, base frontier, budget, and stopping
    rule. They differ only in ranking positive member gains: gain/delta-cost
    versus gain. Zero-cost positive gains precede finite ratios.
    """
    if criterion not in {"marginal_cost", "relevance"}:
        raise ValueError(criterion)
    if budget <= 0 or max_members < 1:
        raise ValueError("positive budget and max_members required")
    candidates = sorted(member_scores)
    bases = singleton_frontier(single_scores, y, labels, latencies)
    points, paths = [], []
    for base in bases:
        base_pred = labels[np.argmax(single_scores[base], axis=1)]
        base_f1 = float(f1_score(y, base_pred, average="macro", zero_division=0))
        if latencies[base] > budget:
            continue
        base_point = {"base": base, "members": [], "quantile": None, "threshold": None,
                      "training_macro_f1": base_f1, "training_projected_ms": float(latencies[base]),
                      "training_escalation_fraction": 0., "training_classifier_calls": 1.}
        points.append(base_point)
        for q in quantiles:
            threshold = float(np.quantile(margins[base], q))
            gate = margins[base] < threshold
            rate = float(gate.mean())
            chosen, current_f1, total_scores = [], base_f1, None
            path = {"base": base, "quantile": float(q), "threshold": threshold, "steps": []}
            for _ in range(max_members):
                current_cost = acquisition_cost(base, chosen, rate, latencies, overhead)
                options = []
                for candidate in candidates:
                    if candidate in chosen:
                        continue
                    members = chosen + [candidate]
                    cost = acquisition_cost(base, members, rate, latencies, overhead)
                    if cost > budget + 1e-10:
                        continue
                    summed = member_scores[candidate] if total_scores is None else total_scores + member_scores[candidate]
                    pred = base_pred.copy()
                    pred[gate] = labels[np.argmax(summed[gate], axis=1)]
                    quality = float(f1_score(y, pred, average="macro", zero_division=0))
                    gain = quality - current_f1
                    if gain <= 1e-12:
                        continue
                    delta = cost - current_cost
                    merit = gain if criterion == "relevance" else (gain / delta if delta > 1e-12 else float("inf"))
                    options.append((merit, gain, cost, candidate, quality, summed))
                if not options:
                    break
                best = min(options, key=lambda x: (-x[0], -x[1], x[2], x[3]))
                merit, gain, cost, member, current_f1, total_scores = best
                chosen.append(member)
                point = {"base": base, "members": [list(item) for item in chosen],
                         "quantile": float(q), "threshold": threshold,
                         "training_macro_f1": current_f1, "training_projected_ms": cost,
                         "training_escalation_fraction": rate,
                         "training_classifier_calls": 1 + rate * len(chosen)}
                points.append(point)
                path["steps"].append({**point, "gain": gain,
                                       "merit": merit if np.isfinite(merit) else "positive_gain_zero_cost"})
            paths.append(path)
    if not points:
        return {"feasible": False, "budget_ms": float(budget), "criterion": criterion,
                "base_candidates": bases, "reason": "no base fits the training mean budget", "paths": paths}
    selected = min(points, key=lambda p: (-p["training_macro_f1"], p["training_projected_ms"],
                                         len(p["members"]), p["base"],
                                         -1 if p["quantile"] is None else p["quantile"],
                                         tuple(tuple(m) for m in p["members"])))
    return {"feasible": True, "budget_ms": float(budget), "criterion": criterion,
            "base_candidates": bases, "selected": selected, "paths": paths}
