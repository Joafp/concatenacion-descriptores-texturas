"""Descriptive metrics only when prediction rows, folds and labels match exactly."""
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score


def aligned_quality(reference, candidate):
    keys = ["row_index", "producer_fold"]
    columns = keys + ["label", "prediction"]
    for frame in (reference, candidate):
        if frame.duplicated(keys).any() or frame[columns].isna().any().any():
            raise ValueError("duplicate or missing prediction records")
    a = reference[columns].sort_values(keys).reset_index(drop=True)
    b = candidate[columns].sort_values(keys).reset_index(drop=True)
    if not a[keys + ["label"]].equals(b[keys + ["label"]]):
        raise ValueError("different images, producer folds or labels")
    labels = sorted(a.label.unique())
    return {"n": len(b), "macro_f1": float(f1_score(b.label, b.prediction,
             labels=labels, average="macro", zero_division=0)),
            "accuracy": float(accuracy_score(b.label, b.prediction))}
