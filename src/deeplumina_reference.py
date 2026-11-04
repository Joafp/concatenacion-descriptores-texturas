"""DeepLumina reference equations, YIQ-Y luminance, feature concatenation, and sparse-random ECOC-SVM.

Source paper: Simon & Uma (2022), "DeepLumina: A Method Based on Deep Features and Luminance
Information for Color Texture Classification", Computational Intelligence and Neuroscience,
DOI: 10.1155/2022/9510987.

Protocol specification: docs/fsc_tex/PROTOCOLO_DEEPLUMINA_ADAPTACION_FMD_2026-11-03.md
"""
import hashlib
import json
import math
import numpy as np
import torch
from sklearn.svm import LinearSVC

CHECKPOINT_SHA = "1ba5b660e7c175b3c27c557fc7dc8b2815be830c516815b0155f61b403f27380"
MODEL_NAME = "resnet101.a1_in1k"
METHOD = "DeepLumina adapted; ResNet101 fc1000 RGB+YIQ-Y + ECOC-SVM sparse-random"

LINEAR_SVC_PARAMS = dict(
    C=1.0,
    penalty="l2",
    loss="squared_hinge",
    dual=True,
    fit_intercept=True,
    class_weight=None,
    tol=1e-4,
    max_iter=10000,
    random_state=42,
)


def compute_yiq_luminance(rgb_float):
    """Compute Y channel from float32 RGB in [0, 1] using paper equation Y = 0.299R + 0.587G + 0.114B."""
    arr = np.asarray(rgb_float, dtype=np.float32)
    if arr.ndim != 3 or arr.shape[2] != 3 or not np.isfinite(arr).all():
        raise ValueError("finite HxWx3 RGB float array required")
    if (arr < -1e-6).any() or (arr > 1.0 + 1e-6).any():
        raise ValueError("RGB float values must be in [0, 1]")
    weights = np.array([0.299, 0.587, 0.114], dtype=np.float32)
    y = arr @ weights
    return np.stack([y, y, y], axis=-1).astype(np.float32)


def fuse_rgb_and_luminance_fc1000(rgb_fc, y_fc):
    """Concatenate RGB fc1000 (1000D) and YIQ-Y fc1000 (1000D) into 2000D without extra scaling."""
    if (
        rgb_fc.ndim != 2
        or y_fc.ndim != 2
        or rgb_fc.shape != y_fc.shape
        or rgb_fc.shape[1] != 1000
        or not torch.isfinite(rgb_fc).all()
        or not torch.isfinite(y_fc).all()
    ):
        raise ValueError("aligned finite (N, 1000) RGB and YIQ-Y fc1000 tensors required")
    return torch.cat([rgb_fc, y_fc.to(device=rgb_fc.device, dtype=rgb_fc.dtype)], dim=1)


def filter_coding_columns(matrix):
    """Discard columns lacking both +1 and -1, and discard duplicate or negated columns."""
    matrix = np.asarray(matrix, dtype=np.int8)
    if matrix.ndim != 2 or not np.isin(matrix, (-1, 0, 1)).all():
        raise ValueError("2D ternarycoding matrix in {-1, 0, +1} required")
    kept = []
    for col_idx in range(matrix.shape[1]):
        col = matrix[:, col_idx]
        if not ((col == 1).any() and (col == -1).any()):
            continue
        is_dup = False
        for prev in kept:
            if np.array_equal(col, prev) or np.array_equal(col, -prev):
                is_dup = True
                break
        if not is_dup:
            kept.append(col.copy())
    if not kept:
        return np.empty((matrix.shape[0], 0), dtype=np.int8)
    return np.stack(kept, axis=1)


def min_pairwise_row_distance(matrix):
    """Compute min_{i<j} 0.5 * sum_l |m_il| |m_jl| |m_il - m_jl|."""
    matrix = np.asarray(matrix, dtype=np.int64)
    k, l_cols = matrix.shape
    if k < 2 or l_cols == 0:
        return 0.0
    abs_m = np.abs(matrix)
    min_dist = float("inf")
    for i in range(k):
        for j in range(i + 1, k):
            diff = np.abs(matrix[i] - matrix[j])
            dist = 0.5 * float(np.sum(abs_m[i] * abs_m[j] * diff))
            if dist < min_dist:
                min_dist = dist
    return min_dist


def generate_sparse_random_coding_matrix(n_classes, seed=42, n_candidates=10000):
    """Generate deterministic MathWorks-style sparse-random ternary coding matrix."""
    if n_classes < 3:
        raise ValueError("sparse-random ECOC requires at least 3 classes")
    raw_cols = int(math.ceil(15.0 * math.log2(n_classes)))
    rng = np.random.default_rng(seed)
    best_matrix = None
    best_distance = -1.0
    values = np.array([-1, 0, 1], dtype=np.int8)
    probs = np.array([0.25, 0.50, 0.25], dtype=np.float64)
    for _ in range(n_candidates):
        candidate = rng.choice(values, size=(n_classes, raw_cols), p=probs)
        filtered = filter_coding_columns(candidate)
        if filtered.shape[1] == 0:
            continue
        dist = min_pairwise_row_distance(filtered)
        if dist > best_distance:
            best_distance = dist
            best_matrix = filtered
    if best_matrix is None or best_distance <= 0:
        raise RuntimeError("failed to generate valid sparse-random coding matrix")
    return best_matrix, {
        "n_classes": int(n_classes),
        "raw_columns": int(raw_cols),
        "kept_columns": int(best_matrix.shape[1]),
        "n_candidates": int(n_candidates),
        "seed": int(seed),
        "min_pairwise_distance": float(best_distance),
        "matrix_sha256": hashlib.sha256(best_matrix.tobytes()).hexdigest(),
    }


class SparseRandomECOCClassifier:
    """ECOC-SVM classifier with sparse-random ternary matrix and loss-weighted hinge decoding."""

    def __init__(self, coding_matrix, labels, estimators=None, metadata=None):
        coding_matrix = np.asarray(coding_matrix, dtype=np.int8)
        if coding_matrix.ndim != 2 or coding_matrix.shape[0] != len(labels):
            raise ValueError("coding_matrix rows must match labels")
        if len(set(labels)) != len(labels) or len(labels) < 3:
            raise ValueError("distinct labels (>=3) required")
        self.coding_matrix = coding_matrix
        self.labels = tuple(int(x) for x in labels)
        self.estimators = list(estimators) if estimators is not None else []
        self.metadata = dict(metadata or {})

    @classmethod
    def fit_from_features(cls, features, y, labels, seed=42, n_candidates=10000):
        features = np.asarray(features, dtype=np.float32)
        y = np.asarray(y, dtype=np.int64)
        labels = tuple(int(x) for x in labels)
        if (
            features.ndim != 2
            or features.shape[1] != 2000
            or features.shape[0] != y.shape[0]
            or not np.isfinite(features).all()
        ):
            raise ValueError("finite (N, 2000) feature matrix and aligned labels required")
        if set(y.tolist()) != set(labels):
            raise ValueError("all target classes must be present in training labels")
        coding_matrix, meta = generate_sparse_random_coding_matrix(
            len(labels), seed=seed, n_candidates=n_candidates
        )
        label_to_row = {label: idx for idx, label in enumerate(labels)}
        row_indices = np.array([label_to_row[int(val)] for val in y], dtype=np.int64)
        estimators = []
        for col_idx in range(coding_matrix.shape[1]):
            col_codes = coding_matrix[row_indices, col_idx]
            active_mask = col_codes != 0
            x_active = features[active_mask]
            y_active = col_codes[active_mask]
            if not ((y_active == 1).any() and (y_active == -1).any()):
                raise ValueError(f"column {col_idx} lacks both binary classes in training data")
            clf = LinearSVC(**LINEAR_SVC_PARAMS)
            clf.fit(x_active, y_active)
            estimators.append(clf)
        return cls(coding_matrix, labels, estimators=estimators, metadata=meta)

    def validate_fitted(self):
        if len(self.estimators) != self.coding_matrix.shape[1] or not self.estimators:
            raise ValueError("trained ECOC binary estimators required")
        expected_params = json.loads(json.dumps(LinearSVC(**LINEAR_SVC_PARAMS).get_params()))
        for est in self.estimators:
            if not isinstance(est, LinearSVC) or est.n_features_in_ != 2000:
                raise ValueError("each binary learner must be a 2000-D LinearSVC")
            if list(est.classes_) != [-1, 1]:
                raise ValueError("binary learner classes must be [-1, 1]")
            if json.loads(json.dumps(est.get_params())) != expected_params:
                raise ValueError("LinearSVC hyperparameters drifted from frozen specification")

    def decision_margins_and_losses(self, features):
        """Return (margins [N, L], ecoc_losses [N, K]) using loss-weighted hinge decoding."""
        self.validate_fitted()
        features = np.asarray(features, dtype=np.float32)
        if features.ndim != 2 or features.shape[1] != 2000 or not np.isfinite(features).all():
            raise ValueError("finite (N, 2000) features required")
        margins = np.column_stack([est.decision_function(features) for est in self.estimators]).astype(
            np.float64
        )
        if not np.isfinite(margins).all():
            raise ValueError("non-finite binary SVM margins")
        # Loss-weighted hinge decoding:
        # For class k and column l with code m_kl in {-1, 0, +1}:
        # active weight is |m_kl| in {0, 1}, hinge loss is 0.5 * max(0, 1 - m_kl * s_l)
        m = self.coding_matrix.astype(np.float64)  # (K, L)
        abs_m = np.abs(m)  # (K, L)
        denom = np.sum(abs_m, axis=1)  # (K,)
        if np.any(denom <= 0):
            raise ValueError("every class row in coding matrix must have at least one non-zero entry")
        # Broadcast: margins[:, None, :] is (N, 1, L), m[None, :, :] is (1, K, L)
        hinge = 0.5 * np.maximum(0.0, 1.0 - m[None, :, :] * margins[:, None, :])
        weighted_sum = np.sum(abs_m[None, :, :] * hinge, axis=2)  # (N, K)
        losses = weighted_sum / denom[None, :]
        return margins, losses

    def predict_single(self, feature_row):
        margins, losses = self.decision_margins_and_losses(feature_row)
        if margins.shape[0] != 1 or losses.shape != (1, len(self.labels)):
            raise ValueError("single-sample prediction shape mismatch")
        loss_vec = losses[0]
        margin_vec = margins[0]
        # Tie-breaking: smallest class index (np.argmin returns first minimum index)
        best_idx = int(np.argmin(loss_vec))
        prediction = int(self.labels[best_idx])
        # Expose logits = -ecoc_losses so argmax(logits) == argmin(ecoc_losses)
        logits = (-loss_vec).tolist()
        return {
            "prediction": prediction,
            "logits": logits,
            "ecoc_losses": loss_vec.tolist(),
            "binary_margins": margin_vec.tolist(),
        }
