"""Fold-local discriminative projections and rank-budget allocation.

Each descriptor is compressed with PCA fitted on the current training fold,
then projected by shrinkage LDA.  A grouped inner-CV greedy search allocates a
fixed total number of dimensions among descriptor blocks.  No labels or
statistics from the outer test are used to fit projections or choose ranks.

This is an experimental method, not a claim of novelty or superiority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import f1_score
from sklearn.preprocessing import normalize
import sys


@dataclass(frozen=True)
class FoldFeatures:
    train: Mapping[str, np.ndarray]
    validation: Mapping[str, np.ndarray]


def fit_descriptor_projections(
    cache: Mapping[str, np.ndarray],
    descriptors: Sequence[str],
    fit_indices: np.ndarray,
    transform_indices: np.ndarray,
    y: np.ndarray,
    *,
    pca_components: int = 64,
    max_rank: int = 32,
    seed: int = 42,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, dict]]:
    """Fit one PCA+LDA map per block, using only ``fit_indices`` labels/data."""
    fitted: dict[str, np.ndarray] = {}
    transformed: dict[str, np.ndarray] = {}
    details: dict[str, dict] = {}
    labels = np.asarray(y)[fit_indices]
    n_classes = len(np.unique(labels))
    if n_classes < 2:
        raise ValueError("projection training fold has fewer than two classes")

    for name in descriptors:
        x = np.asarray(cache[name], dtype=np.float32)
        pca_dim = min(pca_components, x.shape[1], len(fit_indices) - 1)
        if pca_dim < 1:
            raise ValueError(f"not enough training rows for PCA: {name}")
        pca = PCA(n_components=pca_dim, svd_solver="randomized",
                  random_state=seed)
        x_fit = pca.fit_transform(x[fit_indices])
        x_transform = pca.transform(x[transform_indices])
        rank = min(max_rank, pca_dim, n_classes - 1)
        lda = LinearDiscriminantAnalysis(solver="eigen", shrinkage="auto",
                                         n_components=rank)
        lda.fit(x_fit, labels)
        z_fit = lda.transform(x_fit).astype(np.float32, copy=False)
        z_transform = lda.transform(x_transform).astype(np.float32, copy=False)
        fitted[name] = normalize(z_fit, norm="l2", copy=False)
        transformed[name] = normalize(z_transform, norm="l2", copy=False)
        details[name] = {
            "input_dimensions": int(x.shape[1]),
            "pca_dimensions": int(pca_dim),
            "available_lda_rank": int(z_fit.shape[1]),
            "pca_fit_rows": int(len(fit_indices)),
            "labels_used_for_lda": True,
        }
    return fitted, transformed, details


def concatenate_ranked(features: Mapping[str, np.ndarray],
                       allocation: Mapping[str, int]) -> np.ndarray:
    """Join the first r discriminant coordinates from every allocated block."""
    if not allocation:
        raise ValueError("at least one descriptor rank must be allocated")
    parts = []
    for name in sorted(allocation):
        rank = int(allocation[name])
        if name not in features or not 1 <= rank <= features[name].shape[1]:
            raise ValueError(f"invalid rank {rank} for descriptor {name}")
        parts.append(features[name][:, :rank])
    return np.concatenate(parts, axis=1)


def select_rank_allocation(
    fold_features: Sequence[FoldFeatures],
    y: np.ndarray,
    train_indices: Sequence[np.ndarray],
    validation_indices: Sequence[np.ndarray],
    descriptors: Sequence[str],
    make_classifier,
    *,
    total_budget: int = 128,
    rank_choices: Sequence[int] = (8, 16, 32),
    min_gain: float = 0.001,
    seed: int = 42,
) -> tuple[dict[str, int], list[dict]]:
    """Greedily add or increase descriptor ranks under a hard dimension cap."""
    allocation: dict[str, int] = {}
    history: list[dict] = []
    current_score = float("-inf")
    candidates = tuple(sorted(descriptors))
    choices = tuple(sorted({int(r) for r in rank_choices if int(r) > 0}))
    if total_budget < min(choices):
        raise ValueError("dimension budget is smaller than the minimum rank choice")

    # The ranking is derived exclusively from inner folds. A step can add a
    # new descriptor or increase the rank already assigned to one.
    while True:
        options = []
        for name in candidates:
            old_rank = allocation.get(name, 0)
            for rank in choices:
                if rank <= old_rank:
                    continue
                available_rank = min(
                    min(fold.train[name].shape[1], fold.validation[name].shape[1])
                    for fold in fold_features
                )
                if rank > available_rank:
                    continue
                proposed_dimensions = sum(allocation.values()) - old_rank + rank
                if proposed_dimensions > total_budget:
                    continue
                proposal = dict(allocation)
                proposal[name] = rank
                scores = []
                for fold_id, fold in enumerate(fold_features):
                    model = make_classifier(seed + fold_id)
                    x_fit = concatenate_ranked(fold.train, proposal)
                    x_valid = concatenate_ranked(fold.validation, proposal)
                    model.fit(x_fit, np.asarray(y)[train_indices[fold_id]])
                    pred = model.predict(x_valid)
                    scores.append(float(f1_score(
                        np.asarray(y)[validation_indices[fold_id]], pred,
                        labels=np.unique(y), average="macro", zero_division=0)))
                score = float(np.mean(scores))
                options.append((score, name, rank, proposal, proposed_dimensions))
        if not options:
            break
        score, name, rank, proposal, dimensions = max(
            options, key=lambda item: (item[0], item[1], -item[2]))
        gain = score - current_score if np.isfinite(current_score) else None
        if gain is not None and gain < min_gain:
            history.append({"stopped": "inner_cv_gain_below_threshold",
                            "best_candidate": name, "candidate_rank": rank,
                            "candidate_macro_f1": score, "gain": gain,
                            "threshold": min_gain})
            break
        allocation = proposal
        current_score = score
        history.append({"step": len([row for row in history if "step" in row]) + 1,
                        "descriptor": name, "rank": rank,
                        "total_dimensions": dimensions,
                        "inner_macro_f1": score, "gain": gain})
        print(f"rank-budget step={history[-1]['step']} add={name}:{rank} "
              f"dims={dimensions}/{total_budget} inner_macro_f1={score:.5f}",
              file=sys.stderr, flush=True)
        if dimensions == total_budget:
            break
    if not allocation:
        raise RuntimeError("rank allocation selected no descriptor")
    return allocation, history
