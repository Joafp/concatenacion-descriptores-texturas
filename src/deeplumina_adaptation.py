"""Auditable DeepLumina-inspired adaptation primitives.

This is not the authors' implementation. It intentionally exposes the local
choices (NumPy RNG, sklearn LinearSVC and a cached timm backbone) so a frozen
experiment manifest can hash and disclose them before any dataset run.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np
from sklearn.svm import LinearSVC


def yiq_luminance(rgb: np.ndarray) -> np.ndarray:
    """Compute paper's Y channel from RGB values in [0, 1]."""
    x = np.asarray(rgb, dtype=np.float32)
    if x.ndim < 3 or x.shape[-1] != 3:
        raise ValueError("expected RGB array with last dimension 3")
    if not np.isfinite(x).all() or (x.min() < 0.0) or (x.max() > 1.0):
        raise ValueError("RGB values must be finite and in [0, 1]")
    return (0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2]).astype(np.float32)


def concatenate_fc1000(rgb_fc: np.ndarray, y_fc: np.ndarray) -> np.ndarray:
    """Return ordered [RGB fc1000, YIQ-Y fc1000] features."""
    rgb_fc = np.asarray(rgb_fc)
    y_fc = np.asarray(y_fc)
    if rgb_fc.ndim != 2 or y_fc.ndim != 2 or rgb_fc.shape != y_fc.shape:
        raise ValueError("RGB/Y fc outputs must have identical (n, 1000) shape")
    if rgb_fc.shape[1] != 1000:
        raise ValueError("fc1000 branches must each have 1000 outputs")
    if not np.isfinite(rgb_fc).all() or not np.isfinite(y_fc).all():
        raise ValueError("feature outputs must be finite")
    return np.concatenate((rgb_fc, y_fc), axis=1)


def sparse_random_codebook(
    n_classes: int = 10,
    seed: int = 42,
    candidates: int = 10_000,
) -> np.ndarray:
    """Choose the best disclosed sparse-random ternary ECOC candidate.

    This deterministic NumPy implementation approximates MATLAB's documented
    recipe; it is not expected to reproduce MATLAB's RNG/code matrix. Invalid,
    empty-sign, duplicate and negated duplicate columns are rejected within a
    candidate. Candidate ties keep the earliest candidate.
    """
    if n_classes < 2 or candidates < 1:
        raise ValueError("need at least two classes and one candidate")
    n_columns = math.ceil(15 * math.log2(n_classes))
    rng = np.random.default_rng(seed)
    best: np.ndarray | None = None
    best_distance = -1.0
    probabilities = (0.25, 0.50, 0.25)  # values -1, 0, +1
    for _ in range(candidates):
        raw = rng.choice(np.array([-1, 0, 1], dtype=np.int8),
                         size=(n_classes, n_columns), p=probabilities)
        cols: list[np.ndarray] = []
        seen: set[tuple[int, ...]] = set()
        for col in raw.T:
            if not (np.any(col < 0) and np.any(col > 0)):
                continue
            key = tuple(int(v) for v in col)
            negated = tuple(-v for v in key)
            if key in seen or negated in seen:
                continue
            cols.append(col.copy())
            seen.add(key)
        if not cols:
            continue
        matrix = np.stack(cols, axis=1)
        distances = []
        for i in range(n_classes):
            for j in range(i + 1, n_classes):
                d = 0.5 * np.sum(np.abs(matrix[i]) * np.abs(matrix[j]) *
                                 np.abs(matrix[i] - matrix[j]))
                distances.append(float(d))
        minimum = min(distances)
        if minimum > best_distance:
            best, best_distance = matrix, minimum
    if best is None:
        raise RuntimeError("no valid ECOC candidate generated")
    return best


def fit_ecoc_svm(
    features: np.ndarray,
    labels: Sequence[int],
    codebook: np.ndarray,
) -> list[LinearSVC | None]:
    """Fit one fixed LinearSVC per nonempty ECOC column; 0-code rows ignored."""
    x = np.asarray(features, dtype=np.float32)
    y = np.asarray(labels, dtype=np.int64)
    code = np.asarray(codebook, dtype=np.int8)
    if x.ndim != 2 or y.shape != (x.shape[0],) or code.ndim != 2:
        raise ValueError("invalid feature, label or codebook shape")
    if not np.isfinite(x).all() or not np.isin(code, (-1, 0, 1)).all():
        raise ValueError("features must be finite and codebook ternary")
    if y.size and (y.min() < 0 or y.max() >= code.shape[0]):
        raise ValueError("labels must be integer class indices represented by codebook")
    models: list[LinearSVC | None] = []
    for j in range(code.shape[1]):
        target = code[y, j]
        active = target != 0
        if not (np.any(target[active] == -1) and np.any(target[active] == 1)):
            models.append(None)
            continue
        model = LinearSVC(C=1.0, penalty="l2", loss="squared_hinge", dual=True,
                          fit_intercept=True, class_weight=None, tol=1e-4,
                          max_iter=10_000, random_state=42)
        model.fit(x[active], target[active])
        models.append(model)
    if any(model is None for model in models):
        raise ValueError("codebook contains a column without both learner signs")
    return models


def ecoc_hinge_scores(
    features: np.ndarray,
    models: Sequence[LinearSVC],
    codebook: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return learner margins and per-class mean hinge losses (lower is better)."""
    x = np.asarray(features, dtype=np.float32)
    code = np.asarray(codebook, dtype=np.int8)
    if x.ndim != 2 or code.ndim != 2 or len(models) != code.shape[1]:
        raise ValueError("feature/model/codebook shape mismatch")
    if any(model is None for model in models):
        raise ValueError("all codebook learners must be fitted")
    margins = np.column_stack([np.asarray(model.decision_function(x)).reshape(-1)
                               for model in models])
    losses = np.empty((x.shape[0], code.shape[0]), dtype=np.float64)
    for c in range(code.shape[0]):
        active = code[c] != 0
        signed_margin = margins[:, active] * code[c, active]
        losses[:, c] = np.maximum(0.0, 1.0 - signed_margin).mean(axis=1)
    return margins, losses


def predict_ecoc(
    features: np.ndarray,
    models: Sequence[LinearSVC],
    codebook: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Predict by minimum mean hinge loss; np.argmin breaks ties by class index."""
    margins, losses = ecoc_hinge_scores(features, models, codebook)
    return np.argmin(losses, axis=1).astype(np.int64), margins, losses
