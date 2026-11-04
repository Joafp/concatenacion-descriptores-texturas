"""Training-only GFS and explicitly distinct static budget controls.

The caller supplies only an internal evaluation callback. Producer-validation
labels or predictions have no place in the selector's interface.
"""
import math


def cost_of(subset, costs):
    return float(sum(costs[name] for name in sorted(set(subset))))


def greedy_selection(names, evaluate, costs, max_k=8, budget=None,
                     min_improvement=0.001, patience=2):
    """Preserve archived GFS stopping/best-step/tie rules; optionally filter cost.

    Budget filtering is a separate adapted method, not the historical GFS.
    It starts its own path rather than truncating the unrestricted path.
    """
    if len(set(names)) != len(names) or not names or max_k < 1 or patience < 1:
        raise ValueError("unique library and positive bounds required")
    if not math.isfinite(min_improvement) or min_improvement < 0:
        raise ValueError("invalid improvement threshold")
    if any(not math.isfinite(costs[n]) or costs[n] < 0 for n in names):
        raise ValueError("invalid block costs")
    if budget is not None and (not math.isfinite(budget) or budget <= 0):
        raise ValueError("invalid budget")
    chosen, remaining, history, best = [], sorted(names), [], None
    previous, low = None, 0
    for step in range(1, min(max_k, len(names)) + 1):
        candidates = []
        for name in remaining:
            subset = chosen + [name]
            cost = cost_of(subset, costs)
            if budget is not None and cost > budget + 1e-10:
                continue
            score = float(evaluate(tuple(sorted(subset))))
            if not math.isfinite(score):
                raise ValueError("nonfinite internal score")
            candidates.append({"added": name, "inner_f1": score, "projected_ms": cost})
        if not candidates:
            break
        winner = max(candidates, key=lambda c: (c["inner_f1"], c["added"]))
        chosen.append(winner["added"])
        remaining.remove(winner["added"])
        gain = None if previous is None else winner["inner_f1"] - previous
        history.append({"step": step, "selected": chosen.copy(), "improvement": gain,
                        "candidates": candidates, **winner})
        if best is None or winner["inner_f1"] > best["inner_f1"]:
            best = {"blocks": sorted(chosen), "inner_f1": winner["inner_f1"],
                    "projected_ms": winner["projected_ms"], "k": len(chosen)}
        low = low + 1 if gain is not None and gain < min_improvement else 0
        previous = winner["inner_f1"]
        if low >= patience:
            break
    return {"feasible": best is not None, "budget_ms": budget,
            "selected": best, "history": history}


def inherited_topk(ranking, gfs, evaluate, costs):
    """k comes from GFS, not the validation producer or a separate prefix sweep."""
    if not gfs["feasible"] or len(set(ranking)) != len(ranking):
        raise ValueError("feasible GFS and unique ranking required")
    k = gfs["selected"]["k"]
    subset = sorted(ranking[:k])
    if len(subset) != k:
        raise ValueError("ranking shorter than inherited k")
    return {"feasible": True, "budget_ms": None, "selected": {
        "blocks": subset, "k": k, "inner_f1": float(evaluate(tuple(subset))),
        "projected_ms": cost_of(subset, costs)}, "k_source": "unrestricted_gfs"}


def budget_prefix(ranking, evaluate, costs, budget, max_k=8):
    """Best feasible prefix by internal F1, NOT Top-k with k inherited from GFS."""
    if budget <= 0 or not math.isfinite(budget) or max_k < 1:
        raise ValueError("invalid prefix bounds")
    if not ranking or len(set(ranking)) != len(ranking):
        raise ValueError("unique ranking required")
    candidates = []
    for k in range(1, min(max_k, len(ranking)) + 1):
        subset = sorted(ranking[:k])
        cost = cost_of(subset, costs)
        if cost > budget + 1e-10:
            continue
        score = float(evaluate(tuple(subset)))
        if not math.isfinite(score):
            raise ValueError("nonfinite internal score")
        candidates.append({"blocks": subset, "k": k, "inner_f1": score, "projected_ms": cost})
    best = min(candidates, key=lambda c: (-c["inner_f1"], c["projected_ms"], c["k"], c["blocks"])) if candidates else None
    return {"feasible": best is not None, "budget_ms": budget, "selected": best,
            "candidates": candidates, "k_source": "budget_feasible_internal_prefix_search",
            "reason": None if best else "no_feasible_prefix; no skipped blocks or fallback"}
