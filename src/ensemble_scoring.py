"""Batch-independent score scaling for heterogeneous ensemble members."""

from __future__ import annotations

import numpy as np


def raw_decision_scores(model, x: np.ndarray) -> np.ndarray:
    """Return class scores with a consistent two-dimensional shape."""
    if hasattr(model, "decision_function"):
        scores = np.asarray(model.decision_function(x), dtype=np.float64)
    else:
        scores = np.log(np.clip(np.asarray(model.predict_proba(x), dtype=np.float64),
                                1e-12, None))
    if scores.ndim == 1:
        scores = np.column_stack([-scores, scores])
    if scores.ndim != 2 or not np.isfinite(scores).all():
        raise ValueError("member produced invalid decision scores")
    return scores


def training_score_scale(model, x_train: np.ndarray) -> float:
    """Fit one scalar using training rows only; it is fixed at inference time."""
    scores = raw_decision_scores(model, x_train)
    scale = float(scores.std())
    return scale if np.isfinite(scale) and scale > 0 else 1.0


def decision_scores(model, x: np.ndarray, scale: float) -> np.ndarray:
    """Apply a previously frozen training-derived scale to any inference batch."""
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError(f"invalid frozen score scale: {scale}")
    return raw_decision_scores(model, x) / scale


def legacy_batch_decision_scores(model, x: np.ndarray) -> np.ndarray:
    """Reproduce the archived test-batch normalization for paired diagnostics."""
    scores = raw_decision_scores(model, x)
    scale = float(scores.std())
    return scores / scale if np.isfinite(scale) and scale > 0 else scores
