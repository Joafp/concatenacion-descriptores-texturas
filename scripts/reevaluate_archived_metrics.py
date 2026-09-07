#!/usr/bin/env python3
"""Re-evaluate archived representation subsets with additional metrics.

This script does not repeat model/subset selection.  It reconstructs each
outer split, fits the archived selected representation once, and stores the
predictions-derived metrics needed for the manuscript extension.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import label_binarize


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from run_confirmatory_nested import (  # noqa: E402
    curet_half_indices,
    load_dataset,
    load_manifest,
    make_model,
    official_split_indices,
)


FIELDS = [
    "dataset",
    "classifier",
    "seed",
    "outer_fold",
    "method",
    "selected",
    "n_test",
    "accuracy",
    "balanced_accuracy",
    "precision_macro",
    "recall_macro",
    "macro_f1",
    "roc_auc_ovr_macro",
    "fit_predict_seconds",
    "archived_accuracy",
    "archived_macro_f1",
    "delta_accuracy_vs_archive",
    "delta_macro_f1_vs_archive",
]

SOURCES = [
    {
        "result_root": ROOT / "results/confirmatory",
        "embedding_root": None,
    },
    {
        "result_root": ROOT / "results/extensions/outex13_official1360",
        "embedding_root": ROOT / "embeddings_extensions",
    },
]


def read_archived_rows(result_root: Path) -> pd.DataFrame:
    frames = [pd.read_csv(result_root / "nested_fold_results.csv")]
    topk = result_root / "topk_individual_control/nested_fold_results.csv"
    frames.append(pd.read_csv(topk))
    data = pd.concat(frames, ignore_index=True)
    data = data[data["run_mode"].eq("full")].copy()
    key = ["dataset", "classifier", "seed", "outer_fold", "method"]
    if data.duplicated(key).any():
        raise RuntimeError(f"Duplicate archived result keys in {result_root}")
    return data.sort_values(key)


def outer_indices(dataset, seed, fold, y, groups, manifest_rows):
    if dataset == "DTD":
        return official_split_indices(manifest_rows, int(fold) + 1)
    if dataset == "Outex13Official1360":
        return official_split_indices(manifest_rows, 1)
    if dataset == "CUReT":
        direction = {0: "a_to_b", 1: "b_to_a"}[int(fold)]
        return curet_half_indices(manifest_rows, direction)
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=int(seed))
    return list(splitter.split(np.zeros(len(y)), y, groups))[int(fold)]


def macro_ovr_auc(y_true: np.ndarray, scores: np.ndarray, classes: np.ndarray) -> float:
    binary = label_binarize(y_true, classes=classes)
    if binary.shape[1] != scores.shape[1]:
        raise RuntimeError("Score columns do not match fitted classes")
    per_class = []
    for column in range(binary.shape[1]):
        if np.unique(binary[:, column]).size != 2:
            raise RuntimeError(f"AUC undefined: class {classes[column]} absent from test split")
        per_class.append(roc_auc_score(binary[:, column], scores[:, column]))
    return float(np.mean(per_class))


def evaluate(cache, y, train, test, classifier, seed, selected):
    matrix = np.concatenate([cache[name] for name in selected], axis=1)
    model = make_model(classifier, int(seed))
    started = time.perf_counter()
    model.fit(matrix[train], y[train])
    prediction = model.predict(matrix[test])
    if hasattr(model, "decision_function"):
        scores = np.asarray(model.decision_function(matrix[test]))
    elif hasattr(model, "predict_proba"):
        scores = np.asarray(model.predict_proba(matrix[test]))
    else:
        raise RuntimeError(f"{classifier} exposes no class score method")
    elapsed = time.perf_counter() - started
    classes = np.asarray(model.classes_)
    return {
        "n_test": len(test),
        "accuracy": float(accuracy_score(y[test], prediction)),
        "balanced_accuracy": float(balanced_accuracy_score(y[test], prediction)),
        "precision_macro": float(
            precision_score(y[test], prediction, average="macro", zero_division=0)
        ),
        "recall_macro": float(
            recall_score(y[test], prediction, average="macro", zero_division=0)
        ),
        "macro_f1": float(f1_score(y[test], prediction, average="macro")),
        "roc_auc_ovr_macro": macro_ovr_auc(y[test], scores, classes),
        "fit_predict_seconds": elapsed,
    }


def append_row(path: Path, row: dict) -> None:
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)
        handle.flush()
        os.fsync(handle.fileno())


def key_of(row) -> tuple:
    return (
        str(row["dataset"]),
        str(row["classifier"]),
        int(row["seed"]),
        int(row["outer_fold"]),
        str(row["method"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", help="optional exact dataset filter")
    parser.add_argument("--classifier", choices=("svm", "resmlp"))
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results/confirmatory/extended_metrics/nested_fold_metrics.csv",
    )
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)

    completed = set()
    if output.exists():
        completed = {key_of(row) for row in csv.DictReader(output.open(encoding="utf-8"))}

    written = 0
    for config in SOURCES:
        result_root = config["result_root"]
        archived = read_archived_rows(result_root)
        if args.dataset:
            archived = archived[archived["dataset"].eq(args.dataset)]
        if args.classifier:
            archived = archived[archived["classifier"].eq(args.classifier)]
        for dataset, dataset_rows in archived.groupby("dataset", sort=True):
            cache, y = load_dataset(ROOT, dataset, embedding_root=config["embedding_root"])
            groups, manifest_rows = load_manifest(result_root, dataset, y)
            for _, archived_row in dataset_rows.iterrows():
                key = key_of(archived_row)
                if key in completed:
                    print("RESUME skip", "__".join(map(str, key)), flush=True)
                    continue
                train, test = outer_indices(
                    dataset,
                    int(archived_row.seed),
                    int(archived_row.outer_fold),
                    y,
                    groups,
                    manifest_rows,
                )
                selected = str(archived_row.selected).split("+")
                metrics = evaluate(
                    cache,
                    y,
                    train,
                    test,
                    str(archived_row.classifier),
                    int(archived_row.seed),
                    selected,
                )
                row = {
                    "dataset": dataset,
                    "classifier": archived_row.classifier,
                    "seed": int(archived_row.seed),
                    "outer_fold": int(archived_row.outer_fold),
                    "method": archived_row.method,
                    "selected": archived_row.selected,
                    **metrics,
                    "archived_accuracy": float(archived_row.accuracy),
                    "archived_macro_f1": float(archived_row.macro_f1),
                    "delta_accuracy_vs_archive": metrics["accuracy"] - float(archived_row.accuracy),
                    "delta_macro_f1_vs_archive": metrics["macro_f1"] - float(archived_row.macro_f1),
                }
                append_row(output, row)
                completed.add(key)
                written += 1
                print(
                    f"WROTE {dataset} {archived_row.classifier} fold={int(archived_row.outer_fold)} "
                    f"{archived_row.method}",
                    flush=True,
                )
    print(f"Completed: wrote {written} new rows to {output}")


if __name__ == "__main__":
    main()
