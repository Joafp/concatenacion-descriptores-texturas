#!/usr/bin/env python3
"""Exploratory two-block routing pilot; never writes confirmatory results.

The stored embeddings simulate conditional acquisition. They do not measure
feature-extraction latency or establish a real end-to-end speedup.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from run_confirmatory_nested import load_dataset, load_manifest, make_model  # noqa: E402


def margin(model, x: np.ndarray) -> np.ndarray:
    scores = np.asarray(model.decision_function(x))
    if scores.ndim == 1:
        return np.abs(scores)
    top_two = np.partition(scores, -2, axis=1)[:, -2:]
    return top_two[:, 1] - top_two[:, 0]


def metrics(y_true: np.ndarray, y_pred: np.ndarray, labels: np.ndarray) -> dict:
    return {
        "macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
    }


def run(dataset: str, seed: int, outer_fold: int, base: str, extra: str,
        budgets: tuple[float, ...], random_repeats: int, output: Path,
        embedding_root: Path | None, manifest_root: Path) -> dict:
    cache, y = load_dataset(REPO, dataset, embedding_root=embedding_root)
    groups, _ = load_manifest(manifest_root, dataset, y)
    if base not in cache or extra not in cache or base == extra:
        raise ValueError(f"Two distinct available blocks required: {base}, {extra}")
    outer = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    train, test = list(outer.split(np.zeros(len(y)), y, groups))[outer_fold]
    if set(groups[train]).intersection(groups[test]):
        raise AssertionError("Outer group leakage")

    x_base = cache[base]
    x_full = np.concatenate((cache[base], cache[extra]), axis=1)
    base_model = make_model("svm", seed)
    full_model = make_model("svm", seed)
    base_model.fit(x_base[train], y[train])
    full_model.fit(x_full[train], y[train])
    pred_base = np.asarray(base_model.predict(x_base[test]))
    pred_full = np.asarray(full_model.predict(x_full[test]))
    test_margin = margin(base_model, x_base[test])

    # The threshold sees only out-of-fold training predictions, never test labels.
    inner = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=seed + 1)
    oof_margin = np.full(len(train), np.nan)
    for inner_train_rel, inner_val_rel in inner.split(x_base[train], y[train], groups[train]):
        tr, val = train[inner_train_rel], train[inner_val_rel]
        inner_model = make_model("svm", seed)
        inner_model.fit(x_base[tr], y[tr])
        oof_margin[inner_val_rel] = margin(inner_model, x_base[val])
    if not np.isfinite(oof_margin).all():
        raise AssertionError("Missing inner out-of-fold margins")

    labels = np.unique(y)
    result = {
        "status": "exploratory_precomputed_embedding_simulation",
        "dataset": dataset,
        "seed": seed,
        "outer_fold": outer_fold,
        "base_block": base,
        "extra_block": extra,
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "n_classes": int(len(labels)),
        "base_dimensions": int(x_base.shape[1]),
        "full_dimensions": int(x_full.shape[1]),
        "base_only": metrics(y[test], pred_base, labels),
        "full_for_all": metrics(y[test], pred_full, labels),
        "budgets": [],
        "limitations": [
            "Embeddings were precomputed; requested-block fraction is not measured latency.",
            "One outer fold is a screening pilot, not confirmatory evidence.",
            "The two blocks were fixed before this pilot; no test-based descriptor search.",
        ],
    }
    sample_rows = []
    rng = np.random.default_rng(seed + 1000 * outer_fold)
    for budget in budgets:
        threshold = float(np.quantile(oof_margin, budget))
        request_extra = test_margin <= threshold
        routed = np.where(request_extra, pred_full, pred_base)
        n_extra = int(request_extra.sum())
        random_f1 = []
        random_acc = []
        for _ in range(random_repeats):
            random_request = np.zeros(len(test), dtype=bool)
            random_request[rng.choice(len(test), n_extra, replace=False)] = True
            random_pred = np.where(random_request, pred_full, pred_base)
            m = metrics(y[test], random_pred, labels)
            random_f1.append(m["macro_f1"])
            random_acc.append(m["accuracy"])
        result["budgets"].append({
            "target_extra_fraction": budget,
            "train_oof_margin_threshold": threshold,
            "test_extra_fraction": float(request_extra.mean()),
            "test_extra_count": n_extra,
            "adaptive": metrics(y[test], routed, labels),
            "random_same_count_mean_macro_f1": float(np.mean(random_f1)),
            "random_same_count_sd_macro_f1": float(np.std(random_f1, ddof=1)),
            "random_same_count_mean_accuracy": float(np.mean(random_acc)),
            "random_repeats": random_repeats,
        })
        for pos, row_idx in enumerate(test):
            sample_rows.append({
                "budget": budget,
                "row_id": int(row_idx),
                "true_label": int(y[row_idx]),
                "base_prediction": int(pred_base[pos]),
                "full_prediction": int(pred_full[pos]),
                "adaptive_prediction": int(routed[pos]),
                "base_margin": float(test_margin[pos]),
                "request_extra": int(request_extra[pos]),
            })
    output.mkdir(parents=True, exist_ok=True)
    stem = f"{dataset}_svm_s{seed}_f{outer_fold}_{base}_then_{extra}"
    (output / f"{stem}.json").write_text(json.dumps(result, indent=2) + "\n")
    with (output / f"{stem}_per_sample.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0]))
        writer.writeheader()
        writer.writerows(sample_rows)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="FMD")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outer-fold", type=int, default=0, choices=range(5))
    parser.add_argument("--base", default="resnet50")
    parser.add_argument("--extra", default="beitv2_base_final")
    parser.add_argument("--budgets", type=float, nargs="+", default=[0.25, 0.5, 0.75])
    parser.add_argument("--random-repeats", type=int, default=200)
    parser.add_argument("--embedding-root", type=Path)
    parser.add_argument("--manifest-root", type=Path,
                        default=REPO / "results" / "confirmatory")
    parser.add_argument("--output", type=Path,
                        default=REPO / "results" / "exploratory" / "adaptive_descriptor_pilot")
    args = parser.parse_args()
    if any(not 0 < budget < 1 for budget in args.budgets):
        parser.error("budgets must lie strictly between 0 and 1")
    if args.random_repeats < 2:
        parser.error("random-repeats must be >= 2")
    result = run(args.dataset, args.seed, args.outer_fold, args.base, args.extra,
                 tuple(args.budgets), args.random_repeats, args.output,
                 args.embedding_root, args.manifest_root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
