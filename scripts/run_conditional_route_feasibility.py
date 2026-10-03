#!/usr/bin/env python3
"""Exploratory, train-only feasibility screen for conditional descriptor routes.

The outer test partition is identified solely to exclude it. Every prediction
and label used for this diagnostic belongs to the outer training partition.
This script does not train a routing policy or estimate external performance.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from run_confirmatory_nested import (  # noqa: E402
    canonical_labels,
    l2_rows,
    load_manifest,
    make_model,
    official_split_indices,
)


# Fixed before inspecting the OOF outcomes. This is an exploratory library:
# all branches share the inexpensive DINOv2-small first stage.
ROUTES = {
    "small": ("dinov2_small",),
    "small_beit": ("dinov2_small", "beitv2_base_final"),
    "small_base": ("dinov2_small", "dinov2"),
    "small_large": ("dinov2_small", "dinov2_large"),
    "small_base_large": ("dinov2_small", "dinov2", "dinov2_large"),
}

DATASETS = {
    "DTD": (ROOT / "embeddings" / "DTD", ROOT / "results" / "confirmatory"),
    "Outex13Official1360": (
        ROOT / "embeddings_extensions" / "Outex13Official1360",
        ROOT / "results" / "extensions" / "outex13_official1360",
    ),
}


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_blocks(base: Path) -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, str]]:
    names = sorted({name for route in ROUTES.values() for name in route})
    cache = {}
    reference = None
    hashes = {}
    for name in names:
        path = base / f"{name}.npy"
        label_path = base / f"{name}_labels.npy"
        if not path.is_file() or not label_path.is_file():
            raise FileNotFoundError(f"missing paired embedding: {path}, {label_path}")
        x = np.load(path, allow_pickle=False)
        y = canonical_labels(np.load(label_path, allow_pickle=False))
        if x.ndim != 2 or len(x) != len(y) or not np.isfinite(x).all():
            raise ValueError(f"invalid embedding: {path}")
        if reference is None:
            reference = y
        elif not np.array_equal(reference, y):
            raise ValueError(f"label order mismatch: {label_path}")
        cache[name] = l2_rows(x)
        hashes[name] = file_hash(path)
    assert reference is not None
    return cache, reference, hashes


def oof_predictions(
    matrices: dict[str, np.ndarray],
    y: np.ndarray,
    groups: np.ndarray,
    outer_train: np.ndarray,
    seed: int,
    n_splits: int,
) -> tuple[dict[str, np.ndarray], list[dict[str, int]]]:
    if n_splits < 2 or len(np.unique(groups[outer_train])) < n_splits:
        raise ValueError("not enough groups for requested inner folds")
    local_y = y[outer_train]
    local_groups = groups[outer_train]
    predictions = {name: np.full(len(outer_train), -1, dtype=np.int64) for name in matrices}
    fold_audit = []
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for fold, (fit_pos, val_pos) in enumerate(
        splitter.split(outer_train, local_y, local_groups)
    ):
        fit_groups = set(local_groups[fit_pos])
        val_groups = set(local_groups[val_pos])
        if fit_groups.intersection(val_groups):
            raise AssertionError("inner group leakage")
        if len(np.unique(local_y[fit_pos])) != len(np.unique(local_y)):
            raise ValueError(f"inner fold {fold} has absent training classes")
        fold_audit.append({
            "fold": fold,
            "n_fit": len(fit_pos),
            "n_validation": len(val_pos),
            "n_fit_groups": len(fit_groups),
            "n_validation_groups": len(val_groups),
        })
        for name, x in matrices.items():
            model = make_model("svm", seed)
            model.fit(x[outer_train[fit_pos]], local_y[fit_pos])
            predictions[name][val_pos] = model.predict(x[outer_train[val_pos]])
    if any(np.any(pred < 0) for pred in predictions.values()):
        raise AssertionError("OOF predictions do not cover every training row")
    return predictions, fold_audit


def summarize(predictions: dict[str, np.ndarray], y: np.ndarray) -> dict:
    fixed = {
        name: {
            "macro_f1": float(f1_score(y, pred, average="macro")),
            "accuracy": float(accuracy_score(y, pred)),
            "n_correct": int(np.sum(pred == y)),
        }
        for name, pred in predictions.items()
    }
    best_name = max(fixed, key=lambda name: (fixed[name]["accuracy"], name))
    correct = np.stack([pred == y for pred in predictions.values()])
    any_correct = correct.any(axis=0)
    base_correct = predictions["small"] == y
    corrections = {}
    for name, pred in predictions.items():
        route_correct = pred == y
        corrections[name] = {
            "fixes_small": int(np.sum(~base_correct & route_correct)),
            "breaks_small": int(np.sum(base_correct & ~route_correct)),
        }
    return {
        "fixed_routes": fixed,
        "best_fixed_accuracy_route": best_name,
        "oracle_accuracy": float(np.mean(any_correct)),
        "oracle_correct": int(np.sum(any_correct)),
        "oracle_gain_vs_best_fixed_accuracy": float(
            np.mean(any_correct) - fixed[best_name]["accuracy"]
        ),
        "correction_vs_small": corrections,
    }


def run(dataset: str, split: int, seed: int, folds: int, output: Path) -> dict:
    embedding_dir, result_dir = DATASETS[dataset]
    cache, y, hashes = load_blocks(embedding_dir)
    groups, rows = load_manifest(result_dir, dataset, y)
    outer_train, outer_test = official_split_indices(rows, split)
    matrices = {
        name: np.concatenate([cache[block] for block in blocks], axis=1)
        for name, blocks in ROUTES.items()
    }
    predictions, fold_audit = oof_predictions(
        matrices, y, groups, outer_train, seed, folds
    )
    summary = summarize(predictions, y[outer_train])
    result = {
        "status": "EXPLORATORY_TRAIN_ONLY",
        "dataset": dataset,
        "outer_split": split,
        "seed": seed,
        "inner_folds": folds,
        "classifier": "LinearSVC(C=1, class_weight=balanced)",
        "n_outer_train": len(outer_train),
        "n_outer_test_excluded": len(outer_test),
        "manifest_sha256": file_hash(result_dir / "sample_manifests" / f"{dataset}.csv"),
        "embedding_sha256": hashes,
        "routes": {name: list(blocks) for name, blocks in ROUTES.items()},
        "fold_audit": fold_audit,
        **summary,
        "interpretation_limit": (
            "The label-assisted OOF oracle is retrospective, not a learned gate. "
            "It is an accuracy ceiling only for selecting among these fixed "
            "OOF predictions; it is not a macro-F1 or external-test ceiling. "
            "Cached embeddings do not measure inference latency."
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    stem = f"{dataset}_official{split}_seed{seed}"
    (output / f"{stem}.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    with (output / f"{stem}_oof.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["row_id", "label", *ROUTES])
        for pos, row_id in enumerate(outer_train):
            writer.writerow([
                int(row_id), int(y[row_id]),
                *(int(predictions[name][pos]) for name in ROUTES),
            ])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    parser.add_argument("--split", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--folds", type=int, default=4)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "exploratory" / "conditional_acquisition" / "feasibility",
    )
    args = parser.parse_args()
    result = run(args.dataset, args.split, args.seed, args.folds, args.output)
    print(json.dumps({
        "dataset": result["dataset"],
        "best_fixed_accuracy_route": result["best_fixed_accuracy_route"],
        "oracle_accuracy": result["oracle_accuracy"],
        "oracle_gain_vs_best_fixed_accuracy": result["oracle_gain_vs_best_fixed_accuracy"],
    }, indent=2))


if __name__ == "__main__":
    main()
