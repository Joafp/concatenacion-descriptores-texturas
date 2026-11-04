"""Classifier-specific training-OOF scores for the local external comparison."""
from __future__ import annotations

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

from ensemble_scoring import decision_scores, training_score_scale
from run_confirmatory_nested import make_model
from run_rescue_nested_selection import block_matrices


def fit_member(cache, subset, fit, evaluate, y, labels, classifier, seed, ngram=None):
    if set(fit).intersection(evaluate):
        raise ValueError("fit/evaluation overlap")
    if not np.array_equal(np.unique(y[fit]), labels):
        raise ValueError("fit is missing classes")
    xfit, xeval = block_matrices(cache, list(subset), fit, evaluate, ngram)
    model = make_model(classifier, seed)
    if classifier == "resmlp":
        # Keep head training off the GPU used by online extractors. Explicitly
        # recorded as a reconstruction setting, not bitwise historical parity.
        model.set_params(device="cpu")
    model.fit(xfit, y[fit])
    if not np.array_equal(model.classes_, labels):
        raise ValueError("classifier class order mismatch")
    scale = training_score_scale(model, xfit)
    return model, scale, decision_scores(model, xeval, scale)


def training_oof(cache, subsets, train, y, groups, labels, classifier, seed,
                 n_splits=3, ngram=None, on_complete=None):
    """Only train indices enter fitting/scoring; no external-test argument."""
    train = np.asarray(train)
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    splits = list(splitter.split(train, y[train], groups[train]))
    log = []
    for fold, (a, b) in enumerate(splits):
        fit, val = train[a], train[b]
        if set(groups[fit]).intersection(groups[val]):
            raise ValueError("inner group leakage")
        log.append({"fold": fold, "fit_indices": fit.tolist(), "validation_indices": val.tolist()})
    output = {}
    for number, subset in enumerate(subsets):
        scores = np.full((len(train), len(labels)), np.nan)
        for a, b in splits:
            _, _, value = fit_member(cache, subset, train[a], train[b], y,
                                      labels, classifier, seed, ngram)
            scores[b] = value
        if not np.isfinite(scores).all():
            raise ValueError("incomplete inner OOF")
        output[tuple(subset)] = scores
        if on_complete:
            on_complete(number + 1, len(subsets), subset)
    return output, log
