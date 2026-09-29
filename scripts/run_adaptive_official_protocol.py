#!/usr/bin/env python3
"""Exploratory adaptive two-block evaluation on audited official splits.

The routing threshold and requested-block budget are frozen at the training
OOF median and 50%, respectively. This script does not write confirmatory
outputs and does not infer a new split protocol.
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

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from run_confirmatory_nested import (  # noqa: E402
    audit_gate,
    load_dataset,
    load_manifest,
    make_model,
    official_split_indices,
)
from run_adaptive_descriptor_pilot import margin, metrics  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rooted(path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (REPO / path).resolve()


def run(dataset: str, split_number: int, seed: int, audit_root: Path,
        manifest_root: Path, embedding_root: Path, output: Path,
        random_repeats: int = 200) -> dict:
    audit_root, manifest_root, embedding_root, output = map(
        rooted, (audit_root, manifest_root, embedding_root, output)
    )
    audit_gate(audit_root, dataset)
    cache, y = load_dataset(REPO, dataset, embedding_root=embedding_root)
    groups, rows = load_manifest(manifest_root, dataset, y)
    if not {"resnet50", "beitv2_base_final"}.issubset(cache):
        raise ValueError("Frozen ResNet50 -> BEiTv2-final blocks are not both available")
    train, test = official_split_indices(rows, split_number)
    if set(groups[train]).intersection(groups[test]):
        raise AssertionError("Outer official split has group leakage after purge")

    x_base = cache["resnet50"]
    x_full = np.concatenate((x_base, cache["beitv2_base_final"]), axis=1)
    base_model, full_model = make_model("svm", seed), make_model("svm", seed)
    base_model.fit(x_base[train], y[train])
    full_model.fit(x_full[train], y[train])
    pred_base = np.asarray(base_model.predict(x_base[test]))
    pred_full = np.asarray(full_model.predict(x_full[test]))
    test_margin = margin(base_model, x_base[test])

    # The threshold is estimated from 4-fold OOF margins inside official train.
    # For KTH, a physical sample (a/b/c/d) is the acquisition group. Hash-per-
    # image groups are insufficient because images from the same sample would
    # leak across inner folds. A one-sample-per-class official train side may
    # therefore make the frozen 4-fold OOF threshold infeasible; fail closed.
    if dataset == "KTHTIPS2b" and all("sample" in row for row in rows):
        oof_groups = np.asarray([f"{row['label']}::{row['sample']}" for row in rows])
    else:
        oof_groups = groups
    inner = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=seed + 1)
    oof_margin = np.full(len(train), np.nan, dtype=np.float64)
    inner_fold_classes = []
    for inner_train_rel, inner_val_rel in inner.split(x_base[train], y[train], oof_groups[train]):
        tr, val = train[inner_train_rel], train[inner_val_rel]
        inner_model = make_model("svm", seed)
        inner_model.fit(x_base[tr], y[tr])
        oof_margin[inner_val_rel] = margin(inner_model, x_base[val])
        inner_fold_classes.append(int(len(np.unique(y[tr]))))
    if not np.isfinite(oof_margin).all():
        raise AssertionError("Incomplete OOF margins")
    if min(inner_fold_classes) < len(np.unique(y[train])):
        raise ValueError("An inner fold loses training classes; frozen OOF threshold is infeasible")

    threshold = float(np.quantile(oof_margin, 0.5))
    requested = test_margin <= threshold
    adaptive = np.where(requested, pred_full, pred_base)
    labels = np.unique(y)
    rng = np.random.default_rng(seed + split_number * 1000)
    n_requested = int(requested.sum())
    random_scores, random_acc = [], []
    for _ in range(random_repeats):
        random_mask = np.zeros(len(test), dtype=bool)
        random_mask[rng.choice(len(test), n_requested, replace=False)] = True
        random_prediction = np.where(random_mask, pred_full, pred_base)
        row = metrics(y[test], random_prediction, labels)
        random_scores.append(row["macro_f1"])
        random_acc.append(row["accuracy"])

    manifest_path = manifest_root / "sample_manifests" / f"{dataset}.csv"
    audit_path = audit_root / "data_audit.csv"
    embedding_dir = embedding_root / {"KTHTIPS2b": "KTH-TIPS2-b"}.get(dataset, dataset)
    result = {
        "status": "exploratory_precomputed_embedding_simulation",
        "dataset": dataset,
        "outer_protocol": "manifest-defined official split",
        "official_split_number": split_number,
        "seed": seed,
        "base_block": "resnet50",
        "extra_block": "beitv2_base_final",
        "target_extra_fraction": 0.5,
        "threshold_source": "median of 4-fold grouped OOF margins on official training partition only",
        "train_oof_margin_threshold": threshold,
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "n_classes": int(len(labels)),
        "base_dimensions": int(x_base.shape[1]),
        "full_dimensions": int(x_full.shape[1]),
        "train_test_group_intersection": 0,
        "inner_train_class_counts_min": int(min(inner_fold_classes)),
        "adaptive_extra_fraction": float(requested.mean()),
        "base_only": metrics(y[test], pred_base, labels),
        "adaptive": metrics(y[test], adaptive, labels),
        "random_same_count_mean_macro_f1": float(np.mean(random_scores)),
        "random_same_count_sd_macro_f1": float(np.std(random_scores, ddof=1)),
        "random_same_count_mean_accuracy": float(np.mean(random_acc)),
        "full_for_all": metrics(y[test], pred_full, labels),
        "random_repeats": random_repeats,
        "provenance": {
            "audit_csv": str(audit_path.relative_to(REPO)),
            "audit_csv_sha256": sha256(audit_path),
            "manifest_csv": str(manifest_path.relative_to(REPO)),
            "manifest_csv_sha256": sha256(manifest_path),
            "resnet50_npy_sha256": sha256(embedding_dir / "resnet50.npy"),
            "beitv2_base_final_npy_sha256": sha256(embedding_dir / "beitv2_base_final.npy"),
            "resnet50_labels_sha256": sha256(embedding_dir / "resnet50_labels.npy"),
            "beitv2_base_final_labels_sha256": sha256(embedding_dir / "beitv2_base_final_labels.npy"),
        },
        "limitations": [
            "Precomputed embeddings simulate block requests and do not themselves measure extraction latency.",
            "This official-split evaluation is not comparable to grouped 5-fold results unless protocol, test rows, and metric match.",
            "Fold/split estimates are descriptive; no inferential claim is made.",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    stem = f"{dataset}_svm_s{seed}_official{split_number}_resnet50_then_beitv2_base_final"
    (output / f"{stem}.json").write_text(json.dumps(result, indent=2) + "\n")
    with (output / f"{stem}_per_sample.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "row_id", "true_label", "base_prediction", "full_prediction",
            "adaptive_prediction", "base_margin", "request_extra",
        ])
        writer.writeheader()
        for position, row_id in enumerate(test):
            writer.writerow({
                "row_id": int(row_id), "true_label": int(y[row_id]),
                "base_prediction": int(pred_base[position]),
                "full_prediction": int(pred_full[position]),
                "adaptive_prediction": int(adaptive[position]),
                "base_margin": float(test_margin[position]),
                "request_extra": int(requested[position]),
            })
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--split-number", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--embedding-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-repeats", type=int, default=200)
    args = parser.parse_args()
    if args.split_number < 1 or args.random_repeats < 2:
        parser.error("split-number must be >= 1 and random-repeats >= 2")
    print(json.dumps(run(args.dataset, args.split_number, args.seed, args.audit_root,
                         args.manifest_root, args.embedding_root, args.output,
                         args.random_repeats), indent=2))


if __name__ == "__main__":
    main()
