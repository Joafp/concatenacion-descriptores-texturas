#!/usr/bin/env python3
"""Exploratory adaptive routing on audited CUReT halves or KTH physical samples.

CUReT uses the repository's deterministic, condition-grouped a_to_b/b_to_a
halves. KTH reverses each manifest split's official one-sample-train roles to
evaluate three physical samples for training and the remaining sample for test;
it is explicitly an adapted leave-one-physical-sample-out protocol, not the
official Caputo train/test direction.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from run_confirmatory_nested import (  # noqa: E402
    audit_gate, canonical_labels, load_dataset, load_manifest, make_model,
    official_split_indices,
)
from curet_confirmatory_protocol import curet_half_indices  # noqa: E402
from run_adaptive_descriptor_pilot import margin, metrics  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rooted(path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (REPO / path).resolve()


def source_validation(rows: list[dict]) -> dict:
    checked = 0
    for row in rows:
        path_value = row.get("source_path") or row.get("path")
        expected = row.get("source_sha256") or row.get("sha256")
        if not path_value or not expected:
            raise ValueError("audited manifest must bind every row to a source path and SHA-256")
        path = Path(path_value)
        if not path.is_absolute():
            path = REPO / path
        if not path.is_file():
            raise FileNotFoundError(path)
        if sha256(path) != expected:
            raise ValueError(f"source SHA-256 mismatch for manifest row {row['row_id']}")
        checked += 1
    return {"checked_rows": checked, "missing": 0, "sha256_mismatches": 0}


def source_sha_from_rows(rows: list[dict], indices: np.ndarray) -> list[str]:
    return [rows[int(i)].get("source_sha256") or rows[int(i)].get("sha256") or ""
            for i in indices]


def split_rows(dataset: str, rows: list[dict], y: np.ndarray,
               split_number: int, curet_direction: str | None):
    if dataset == "CUReT":
        if curet_direction not in {"a_to_b", "b_to_a"}:
            raise ValueError("CUReT requires --curet-direction a_to_b or b_to_a")
        train, test = curet_half_indices(rows, curet_direction)
        outer_protocol = f"condition-grouped deterministic halves ({curet_direction})"
        group_ids = np.asarray([row["group"] for row in rows], dtype=str)
        physical_ids = group_ids
        inner_group_ids = group_ids
        group_semantics = "condition_id shared across all 61 material classes"
        inner_splits = 4
    else:
        if curet_direction is not None:
            raise ValueError("--curet-direction is only valid for CUReT")
        official_train, official_test = official_split_indices(rows, split_number)
        # The KTH manifest follows Caputo: one sample per class trains and the
        # other three test. The requested LOPO adaptation holds out the sample
        # named by the official train role and trains on its complement.
        train, test = official_test, official_train
        outer_protocol = (
            "adapted leave-one-physical-sample-out; inverted official split roles "
            "(3 physical samples train, 1 held-out test); not Caputo direction"
        )
        group_ids = np.asarray([
            f"{row['label']}::{row['sample']}" for row in rows
        ], dtype=str)
        physical_ids = group_ids
        inner_group_ids = group_ids
        group_semantics = "label::sample (one physical sample per material class)"
        inner_splits = 3

    # Retain the complete held-out test and conservatively purge from train
    # every source image whose verified SHA-256 occurs in that test. This is
    # essential for the inverted KTH LOPO direction; the manifest's original
    # one-sample-train purge does not protect the inverse roles.
    source_sha = np.asarray([
        row.get("source_sha256") or row.get("sha256") or "" for row in rows
    ], dtype=str)
    if np.any(source_sha == ""):
        raise ValueError("manifest must bind every row to a source SHA-256")
    test_sha = set(source_sha[test])
    train_candidates = train
    train = np.asarray([i for i in train_candidates if source_sha[i] not in test_sha],
                       dtype=np.int64)
    purged = np.asarray([i for i in train_candidates if source_sha[i] in test_sha],
                        dtype=np.int64)
    if set(group_ids[train]).intersection(group_ids[test]):
        raise AssertionError("outer split leaks condition/physical groups")
    sha_overlap = set(source_sha[train]).intersection(source_sha[test])
    if sha_overlap:
        raise AssertionError("outer split leaks duplicate source-image SHA-256")
    physical_overlap = set(physical_ids[train]).intersection(physical_ids[test])
    if physical_overlap:
        raise AssertionError("outer split leaks physical samples or CUReT conditions")
    if set(np.unique(y[train])) != set(np.unique(y)) or set(np.unique(y[test])) != set(np.unique(y)):
        raise ValueError("outer train and held-out test must both contain every class")
    return (train, test, inner_group_ids, outer_protocol, group_semantics, inner_splits,
            {"train_candidate_rows": int(len(train_candidates)),
             "purged_train_rows": int(len(purged)),
             "purged_source_sha256_groups": int(len(set(source_sha[purged]))),
             "train_test_source_sha256_intersection": int(len(sha_overlap)),
             "physical_sample_train_test_intersection": (
                 int(len(physical_overlap)) if dataset == "KTHTIPS2b" else None),
             "condition_train_test_intersection": (
                 int(len(physical_overlap)) if dataset == "CUReT" else None)})


def evaluate(dataset: str, split_number: int, seed: int, audit_root: Path,
             manifest_root: Path, embedding_root: Path, output: Path,
             curet_direction: str | None, random_repeats: int) -> dict:
    audit_root, manifest_root, embedding_root, output = map(
        rooted, (audit_root, manifest_root, embedding_root, output)
    )
    audit_gate(audit_root, dataset)
    cache, y = load_dataset(REPO, dataset, embedding_root=embedding_root)
    if not {"resnet50", "beitv2_base_final"}.issubset(cache):
        raise ValueError("Frozen ResNet50 -> BEiTv2-final blocks are not both available")
    image_dataset = {"KTHTIPS2b": "KTH-TIPS2-b"}.get(dataset, dataset)
    embedding_dir = embedding_root / image_dataset
    groups, rows = load_manifest(manifest_root, dataset, y)
    train, test, inner_groups, outer_protocol, group_semantics, inner_splits, purge = split_rows(
        dataset, rows, y, split_number, curet_direction
    )
    sources = source_validation(rows)

    x_base = cache["resnet50"]
    x_extra = cache["beitv2_base_final"]
    x_full = np.concatenate((x_base, x_extra), axis=1)
    labels = np.unique(y)
    base_model = make_model("svm", seed)
    full_model = make_model("svm", seed)
    base_model.fit(x_base[train], y[train])
    full_model.fit(x_full[train], y[train])
    pred_base = np.asarray(base_model.predict(x_base[test]))
    pred_full = np.asarray(full_model.predict(x_full[test]))
    test_margin = margin(base_model, x_base[test])

    inner = StratifiedGroupKFold(n_splits=inner_splits, shuffle=True,
                                 random_state=seed + 1)
    oof_margin = np.full(len(train), np.nan, dtype=np.float64)
    inner_fold_classes = []
    for inner_train_rel, inner_val_rel in inner.split(
            x_base[train], y[train], inner_groups[train]):
        tr, val = train[inner_train_rel], train[inner_val_rel]
        inner_model = make_model("svm", seed)
        inner_model.fit(x_base[tr], y[tr])
        oof_margin[inner_val_rel] = margin(inner_model, x_base[val])
        inner_fold_classes.append(int(len(np.unique(y[tr]))))
    if not np.isfinite(oof_margin).all():
        raise AssertionError("incomplete inner OOF margins")
    if min(inner_fold_classes) != len(labels):
        raise ValueError("an inner OOF training fold loses one or more classes")

    threshold = float(np.quantile(oof_margin, 0.5))
    requested = test_margin <= threshold
    adaptive = np.where(requested, pred_full, pred_base)
    random_scores, random_acc = [], []
    rng = np.random.default_rng(seed + split_number * 1000 +
                                (0 if curet_direction == "a_to_b" else 1))
    n_requested = int(requested.sum())
    for _ in range(random_repeats):
        random_mask = np.zeros(len(test), dtype=bool)
        random_mask[rng.choice(len(test), n_requested, replace=False)] = True
        random_prediction = np.where(random_mask, pred_full, pred_base)
        row = metrics(y[test], random_prediction, labels)
        random_scores.append(row["macro_f1"])
        random_acc.append(row["accuracy"])

    manifest_path = manifest_root / "sample_manifests" / f"{dataset}.csv"
    audit_path = audit_root / "data_audit.csv"
    result = {
        "status": "exploratory_adapted_sample_generalization",
        "dataset": dataset,
        "outer_protocol": outer_protocol,
        "official_split_number": split_number if dataset == "KTHTIPS2b" else None,
        "curet_direction": curet_direction,
        "seed": seed,
        "base_block": "resnet50",
        "extra_block": "beitv2_base_final",
        "classifier": "LinearSVC C=1 class_weight=balanced",
        "target_extra_fraction": 0.5,
        "threshold_source": (
            f"median of {inner_splits}-fold StratifiedGroupKFold OOF margins "
            "from outer training only"
        ),
        "threshold_inner_fold_count": inner_splits,
        "inner_group_semantics": group_semantics,
        "inner_train_class_counts": inner_fold_classes,
        "train_oof_margin_threshold": threshold,
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "n_classes": int(len(labels)),
        "base_dimensions": int(x_base.shape[1]),
        "full_dimensions": int(x_full.shape[1]),
        "train_test_group_intersection": 0,
        "train_test_source_sha256_intersection": purge[
            "train_test_source_sha256_intersection"],
        "physical_sample_train_test_intersection": purge[
            "physical_sample_train_test_intersection"],
        "condition_train_test_intersection": purge["condition_train_test_intersection"],
        "purge_audit": purge,
        "n_train_source_sha_groups": int(len(set(source_sha_from_rows(rows, train)))),
        "n_test_source_sha_groups": int(len(set(source_sha_from_rows(rows, test)))),
        "n_train_physical_sample_groups": (
            int(len(set(f"{rows[i]['label']}::{rows[i]['sample']}" for i in train)))
            if dataset == "KTHTIPS2b" else None),
        "n_test_physical_sample_groups": (
            int(len(set(f"{rows[i]['label']}::{rows[i]['sample']}" for i in test)))
            if dataset == "KTHTIPS2b" else None),
        "n_train_condition_groups": (
            int(len(set(rows[i]["group"] for i in train))) if dataset == "CUReT" else None),
        "n_test_condition_groups": (
            int(len(set(rows[i]["group"] for i in test))) if dataset == "CUReT" else None),
        "source_sha256_validation": sources,
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
            "beitv2_base_final_labels_sha256": sha256(
                embedding_dir / "beitv2_base_final_labels.npy"),
        },
        "limitations": [
            "Exploratory descriptive evaluation; no inferential claims across overlapping folds.",
            "The 50% target is approximate because requests are threshold decisions, not quotas.",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    tag = curet_direction or f"LOPO_split{split_number}"
    stem = f"{dataset}_svm_s{seed}_{tag}_resnet50_then_beitv2_base_final"
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
    parser.add_argument("--dataset", choices=("CUReT", "KTHTIPS2b"), required=True)
    parser.add_argument("--split-number", type=int, default=1)
    parser.add_argument("--curet-direction", choices=("a_to_b", "b_to_a"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--embedding-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-repeats", type=int, default=200)
    args = parser.parse_args()
    if args.split_number not in range(1, 5) or args.random_repeats < 2:
        parser.error("split-number must be 1–4 and random-repeats must be >= 2")
    if (args.dataset == "CUReT") != (args.curet_direction is not None):
        parser.error("CUReT requires --curet-direction; KTHTIPS2b must omit it")
    result = evaluate(args.dataset, args.split_number, args.seed, args.audit_root,
                      args.manifest_root, args.embedding_root, args.output,
                      args.curet_direction, args.random_repeats)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
