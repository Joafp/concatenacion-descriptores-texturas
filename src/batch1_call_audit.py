"""Validate online call coverage and recompute quality/time from the same rows."""
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score


def summarize_calls(frame, policies, row_indices, labels_by_row, class_labels, repeats):
    required = {"repeat", "row_index", "label", "policy", "prediction", "escalated", "ms"}
    if not required.issubset(frame.columns):
        raise ValueError("missing online call fields")
    if frame.empty or frame.duplicated(["repeat", "row_index", "policy"]).any():
        raise ValueError("empty or duplicate online calls")
    if set(frame.policy) != set(policies) or set(frame["repeat"]) != set(range(repeats)):
        raise ValueError("method or repeat coverage mismatch")
    if not np.isfinite(frame.ms).all() or (frame.ms <= 0).any():
        raise ValueError("invalid latency observations")
    for _, group in frame.groupby(["repeat", "policy"]):
        if set(group.row_index) != set(row_indices) or len(group) != len(row_indices):
            raise ValueError("image coverage mismatch")
        if any(labels_by_row[int(row)] != label for row, label in zip(group.row_index, group.label)):
            raise ValueError("ground truth mismatch")
    if not set(frame.prediction).issubset(class_labels):
        raise ValueError("prediction outside classifier classes")
    if frame.groupby(["policy", "row_index"]).prediction.nunique().max() != 1 or frame.groupby(["policy", "row_index"]).escalated.nunique().max() != 1:
        raise ValueError("unstable repeated predictions or gates")
    unique = frame.drop_duplicates(["policy", "row_index"])
    result = []
    for policy, group in unique.groupby("policy"):
        times = frame[frame.policy == policy].ms
        result.append({"policy": policy, "external_images": len(group), "timed_calls": len(times),
            "macro_f1_online": float(f1_score(group.label, group.prediction, labels=class_labels, average="macro", zero_division=0)),
            "accuracy_online": float(accuracy_score(group.label, group.prediction)),
            "mean_ms": float(times.mean()), "median_ms": float(times.median()), "p95_ms": float(times.quantile(.95)),
            "escalation_fraction_online": float(group.escalated.mean())})
    return pd.DataFrame(result)
