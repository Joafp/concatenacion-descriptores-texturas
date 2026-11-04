"""Evaluate a frozen soft-vote route while acquiring every block at most once."""
import numpy as np


def feature_order(member):
    """Historical block_matrices appends fold-fitted N-grams last."""
    return tuple(n for n in member if n != "rgb_ngram_svd") + (("rgb_ngram_svd",) if "rgb_ngram_svd" in member else ())


def evaluate_route(recipe, acquire, score, labels):
    features, scores = {}, {}
    def member_scores(member):
        key = tuple(member)
        if key not in scores:
            for name in feature_order(member):
                if name not in features:
                    features[name] = np.asarray(acquire(name)).reshape(1, -1)
            x = np.concatenate([features[n] for n in feature_order(member)], axis=1)
            scores[key] = np.asarray(score(key, x)).reshape(1, -1)
        return scores[key]
    members = recipe["members"]
    gate = bool(members)
    if recipe.get("base"):
        base_scores = member_scores((recipe["base"],))
        ranked = np.sort(base_scores[0])
        margin = float(ranked[-1] - ranked[-2])
        gate = bool(members) and margin < recipe["threshold"]
        if not gate:
            return {"prediction": int(labels[np.argmax(base_scores)]), "escalated": False,
                    "blocks": list(features), "classifier_calls": len(scores)}
    if not members:
        raise ValueError("A static recipe needs at least one member")
    vote = np.mean([member_scores(member) for member in members], axis=0)
    return {"prediction": int(labels[np.argmax(vote)]), "escalated": gate,
            "blocks": list(features), "classifier_calls": len(scores)}
