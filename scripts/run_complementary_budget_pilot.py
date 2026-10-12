#!/usr/bin/env python3
"""Run one leakage-safe pilot of rank-budgeted complementary fusion.

PCA and shrinkage-LDA projections are refit inside each grouped inner split.
An inner-CV greedy search allocates ranks under a fixed total dimension cap;
only then is the selected representation evaluated on the external test.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from complementary_budget_fusion import (  # noqa: E402
    FoldFeatures,
    concatenate_ranked,
    fit_descriptor_projections,
    select_rank_allocation,
)
from curet_confirmatory_protocol import curet_half_indices  # noqa: E402
from run_confirmatory_nested import (  # noqa: E402
    audit_gate,
    file_sha256,
    load_dataset,
    load_manifest,
    manifest_groups,
    official_split_indices,
)
from run_topk_individual_control import outer_indices  # noqa: E402


PRIMARY22 = (
    "lbp", "drlbp", "gabor", "glcm", "hog",
    "resnet50", "resnet101", "vgg16", "densenet121", "efficientnet_b0",
    "convnext_v2_t", "vit_b16", "deit_s", "swin_t", "eva02_base",
    "dinov2_small", "dinov2", "dinov2_large", "mae_base", "siglip_base",
    "beitv2_base_final", "rgb_ngram_svd",
)


def data_roots(dataset: str) -> tuple[Path, Path | None]:
    if dataset in {"DTD", "FMD", "CUReT"}:
        return ROOT / "results/confirmatory", None
    directory = {"Outex13Official1360": "outex13_official1360",
                 "SoilOriginal": "soil_original", "KTHTIPS2b": "kth_tips2b"}[dataset]
    return ROOT / "results/extensions" / directory, ROOT / "embeddings_extensions"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def make_classifier(seed: int):
    return LinearSVC(C=1.0, class_weight="balanced", random_state=seed,
                     dual="auto", max_iter=10000)


def fit_ngram_block(dataset: str, output_root: Path, repo: Path, rows: list[dict],
                    seed: int):
    from rgb_ngram_descriptor import (RGBNgramSVDBlock, _manifest_digest,
                                      build_count_cache)

    count_dir = output_root / "rgb_ngram_count_cache" / dataset / "rgb_ngram_impl1"
    metadata_path = count_dir / "metadata.json"
    expected_digest = _manifest_digest(rows, repo)
    reusable = False
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        reusable = (metadata.get("manifest_sha256") == expected_digest
                    and metadata.get("implementation") == "rgb_ngram_impl1"
                    and metadata.get("samples") == len(rows))
    if not reusable:
        count_dir = (output_root / "complementary_budget" / "rgb_ngram_count_cache"
                     / dataset / "rgb_ngram_impl1")
    counts = build_count_cache(rows, repo, count_dir, "rgb_ngram_impl1")
    return RGBNgramSVDBlock(counts, n_components=256, random_state=seed,
                            hash_bins=8192)


def grouped_splits(train: np.ndarray, y: np.ndarray, groups: np.ndarray,
                   requested: int, seed: int):
    n_splits = min(requested, len(np.unique(groups[train])))
    if n_splits < 2:
        raise ValueError("inner grouping leaves fewer than two folds")
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True,
                                    random_state=seed)
    splits = list(splitter.split(np.zeros(len(train)), y[train], groups[train]))
    result = [(train[fit_pos], train[val_pos]) for fit_pos, val_pos in splits]
    for fit_idx, val_idx in result:
        if set(groups[fit_idx]) & set(groups[val_idx]):
            raise AssertionError("inner grouped split leaks a source group")
        if not set(np.unique(y[train])).issubset(set(np.unique(y[fit_idx]))):
            raise ValueError("an inner training fold omits one or more classes")
    return result


def make_fold_cache(cache: dict[str, np.ndarray], descriptors: tuple[str, ...],
                    fit_idx: np.ndarray, val_idx: np.ndarray, y: np.ndarray,
                    ngram_block, seed: int, pca_components: int,
                    max_rank: int) -> tuple[FoldFeatures, dict]:
    local_cache = cache
    ngram_audit = None
    if ngram_block is not None:
        ngram_train, ngram_val, ngram_audit = ngram_block.transform(fit_idx, val_idx)
        local_cache = dict(cache)
        ngram_full = np.zeros((len(y), ngram_train.shape[1]), dtype=np.float32)
        ngram_full[fit_idx] = ngram_train
        ngram_full[val_idx] = ngram_val
        local_cache["rgb_ngram_svd"] = ngram_full
    train_features, val_features, detail = fit_descriptor_projections(
        local_cache, descriptors, fit_idx, val_idx, y,
        pca_components=pca_components, max_rank=max_rank, seed=seed,
    )
    return FoldFeatures(train_features, val_features), {
        "projection": detail, "rgb_ngram": ngram_audit,
    }


def read_baseline_rows(dataset: str, classifier: str, seed: int, fold: int,
                       result_root: Path) -> dict[str, dict]:
    path = result_root / "ngram22_beitv2" / "nested_fold_results.csv"
    if not path.exists():
        return {"status": "unavailable", "path": str(path)}
    def rows_by_method(csv_path: Path) -> dict[str, dict]:
        if not csv_path.exists():
            return {}
        frame = pd.read_csv(csv_path)
        matched = frame[(frame.dataset == dataset) & (frame.classifier == classifier)
                        & (frame.seed == seed) & (frame.outer_fold == fold)
                        & (frame.run_mode == "full")]
        return {
            str(row.method): {
                key: (value.item() if isinstance(value, np.generic) else value)
                for key, value in row._asdict().items()
            }
            for row in matched.itertuples(index=False)
        }

    methods = rows_by_method(path)
    topk_path = (result_root / "ngram22_beitv2" / "topk_individual_control"
                 / "nested_fold_results.csv")
    methods.update(rows_by_method(topk_path))
    wanted = ("full_concat", "gfs", "best_individual", "topk_individual")
    return {method: methods[method] for method in wanted if method in methods} | {
        "source": {"path": str(path), "sha256": sha(path),
                   "topk_path": str(topk_path),
                   "topk_sha256": sha(topk_path) if topk_path.exists() else None}}


def run(args) -> dict:
    started = time.perf_counter()
    dataset = args.dataset
    output_root, embedding_root = data_roots(dataset)
    audit_gate(output_root, dataset)
    cache, y = load_dataset(ROOT, dataset, embedding_root=embedding_root)
    missing = sorted(set(PRIMARY22).difference(cache) - {"rgb_ngram_svd"})
    if missing:
        raise FileNotFoundError(f"primary descriptors missing: {missing}")
    groups, manifest_rows = load_manifest(output_root, dataset, y)
    inner_groups = (groups if args.inner_group_column is None else
                    manifest_groups(manifest_rows, args.inner_group_column))

    if dataset == "CUReT":
        if args.curet_direction is None:
            raise ValueError("CUReT requires --curet-direction")
        train, test = curet_half_indices(manifest_rows, args.curet_direction)
        outer_fold = {"a_to_b": 0, "b_to_a": 1}[args.curet_direction]
        protocol = f"curet_half_indices:{args.curet_direction}"
    elif args.official_split is not None:
        train, test = official_split_indices(manifest_rows, args.official_split)
        if args.invert_official_split:
            train, test = test, train
        outer_fold = args.official_split - 1
        protocol = f"official{args.official_split}{'_inverted' if args.invert_official_split else ''}"
    else:
        train, test = outer_indices(dataset, args.seed, args.fold, y, groups,
                                    manifest_rows)
        outer_fold = args.fold
        protocol = f"fold{args.fold}"
    if set(groups[train]) & set(groups[test]):
        raise AssertionError("outer split leaks a source group")

    ngram_block = fit_ngram_block(dataset, output_root, ROOT, manifest_rows, args.seed)
    inner = grouped_splits(train, y, inner_groups, args.inner_folds, args.seed + 1)
    fold_features = []
    fold_details = []
    train_indices, validation_indices = [], []
    for fold_id, (fit_idx, val_idx) in enumerate(inner):
        fold, details = make_fold_cache(
            cache, PRIMARY22, fit_idx, val_idx, y, ngram_block,
            args.seed + fold_id, args.pca_components, args.max_rank,
        )
        fold_features.append(fold)
        fold_details.append(details)
        train_indices.append(fit_idx)
        validation_indices.append(val_idx)

    # Keep the requested rank grid intact. The allocator already checks rank
    # availability separately for each descriptor and inner fold; taking a
    # global minimum here would let a low-dimensional block (e.g. GLCM) cap
    # the ranks of unrelated high-dimensional descriptors as well.
    effective_rank_choices = tuple(sorted({int(rank) for rank in args.rank_choices
                                           if int(rank) > 0}))
    allocation, history = select_rank_allocation(
        fold_features, y, train_indices, validation_indices, PRIMARY22,
        make_classifier, total_budget=args.dimension_budget,
        rank_choices=effective_rank_choices, min_gain=args.min_inner_gain,
        seed=args.seed,
    )
    inner_selected = next(row["inner_macro_f1"] for row in reversed(history)
                          if "inner_macro_f1" in row)

    # Refit each projection using all outer-training rows, then touch outer test.
    ngram_train, ngram_test, outer_ngram_audit = ngram_block.transform(train, test)
    final_cache = dict(cache)
    ngram_full = np.zeros((len(y), ngram_train.shape[1]), dtype=np.float32)
    ngram_full[train] = ngram_train
    ngram_full[test] = ngram_test
    final_cache["rgb_ngram_svd"] = ngram_full
    outer_train_features, outer_test_features, outer_projection_details = fit_descriptor_projections(
        final_cache, PRIMARY22, train, test, y,
        pca_components=args.pca_components, max_rank=args.max_rank,
        seed=args.seed,
    )
    x_train = concatenate_ranked(outer_train_features, allocation)
    x_test = concatenate_ranked(outer_test_features, allocation)
    classifier = make_classifier(args.seed)
    classifier.fit(x_train, y[train])
    prediction = classifier.predict(x_test)
    labels = np.unique(y)

    # Explicit controls separate the effect of supervised per-block projection
    # from the effect of choosing blocks/ranks jointly under the same cap.
    uniform_rank = min(
        args.max_rank, args.dimension_budget // len(PRIMARY22),
        min(outer_train_features[name].shape[1] for name in PRIMARY22),
    )
    if uniform_rank < 1:
        raise ValueError("the dimension budget is too small for a uniform control")
    uniform_allocation = {name: uniform_rank for name in PRIMARY22}
    x_uniform_train = concatenate_ranked(outer_train_features, uniform_allocation)
    x_uniform_test = concatenate_ranked(outer_test_features, uniform_allocation)
    uniform_model = make_classifier(args.seed)
    uniform_model.fit(x_uniform_train, y[train])
    uniform_prediction = uniform_model.predict(x_uniform_test)

    single_scores = []
    for name in PRIMARY22:
        rank = min(args.max_rank,
                   min(fold.train[name].shape[1] for fold in fold_features))
        scores = []
        for fold_id, fold in enumerate(fold_features):
            model = make_classifier(args.seed + fold_id)
            model.fit(fold.train[name][:, :rank], y[train_indices[fold_id]])
            pred = model.predict(fold.validation[name][:, :rank])
            scores.append(float(f1_score(
                y[validation_indices[fold_id]], pred, labels=np.unique(y),
                average="macro", zero_division=0)))
        single_scores.append((float(np.mean(scores)), name, rank))
    single_inner_f1, single_name, single_rank = max(
        single_scores, key=lambda row: (row[0], row[1]))
    single_model = make_classifier(args.seed)
    single_model.fit(outer_train_features[single_name][:, :single_rank], y[train])
    single_prediction = single_model.predict(outer_test_features[single_name][:, :single_rank])
    def outer_f1(pred):
        return float(f1_score(y[test], pred, labels=labels, average="macro",
                              zero_division=0))
    internal_controls = {
        "uniform_22_block_LDA": {
            "allocation": uniform_allocation,
            "dimensions": int(sum(uniform_allocation.values())),
            "macro_f1": outer_f1(uniform_prediction),
        },
        "best_single_block_LDA_selected_by_inner_CV": {
            "descriptor": single_name, "rank": int(single_rank),
            "inner_macro_f1": single_inner_f1,
            "dimensions": int(single_rank),
            "macro_f1": outer_f1(single_prediction),
        },
    }
    result_root = args.output.resolve()
    result_root.mkdir(parents=True, exist_ok=True)
    key = f"{dataset}_{protocol}_{args.classifier}_s{args.seed}_b{args.dimension_budget}"
    if args.classifier != "svm":
        raise ValueError("first implementation currently supports the SVM pilot only")
    predictions_path = result_root / f"{key}_predictions.csv"
    with predictions_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row_id", "label", "prediction"])
        writer.writeheader()
        writer.writerows({"row_id": int(index), "label": int(y[index]),
                          "prediction": int(pred)}
                         for index, pred in zip(test, prediction))

    baseline_rows = read_baseline_rows(dataset, args.classifier, args.seed,
                                       outer_fold, output_root)
    result = {
        "status": "EXPLORATORY_SINGLE_OUTER_SPLIT",
        "method": "PCA plus shrinkage-LDA per descriptor; grouped-CV greedy rank allocation",
        "hypothesis": "A capped, class-discriminative subspace allocation retains complementary information with fewer dimensions than flat concatenation.",
        "dataset": dataset, "protocol": protocol, "classifier": args.classifier,
        "seed": args.seed, "outer_fold": outer_fold,
        "n_train": int(len(train)), "n_test": int(len(test)),
        "n_classes": int(len(labels)), "inner_folds": len(inner),
        "dimension_budget": args.dimension_budget,
        "dimensions_used": int(sum(allocation.values())),
        "requested_rank_choices": list(args.rank_choices),
        "effective_rank_choices": list(effective_rank_choices),
        "min_inner_gain": args.min_inner_gain,
        "selected_rank_by_descriptor": allocation,
        "inner_selection_history": history,
        "selected_inner_macro_f1": inner_selected,
        "outer_macro_f1": outer_f1(prediction),
        "outer_accuracy": float(accuracy_score(y[test], prediction)),
        "internal_outer_controls": internal_controls,
        "baseline_rows_same_outer_condition": baseline_rows,
        "projections_refit_on_outer_train": outer_projection_details,
        "inner_projection_details": fold_details,
        "outer_test_predictions": str(predictions_path),
        "outer_test_used_for_rank_selection": False,
        "outer_rgb_ngram_projection": outer_ngram_audit,
        "limitations": [
            "one exploratory outer condition; not a confirmatory performance claim",
            "PCA/LDA projection dimensions are learned from embeddings; this does not reduce the cost of running the frozen image encoders",
            "the rank search is greedy and its result can depend on the fixed inner folds",
        ],
        "provenance": {
            "audit_sha256": sha(output_root / "data_audit.csv"),
            "manifest_sha256": sha(output_root / "sample_manifests" / f"{dataset}.csv"),
            "runner_sha256": sha(Path(__file__)),
            "method_sha256": sha(ROOT / "src/complementary_budget_fusion.py"),
            "baseline": baseline_rows.get("source") if isinstance(baseline_rows, dict) else None,
        },
        "elapsed_seconds": time.perf_counter() - started,
    }
    (result_root / f"{key}.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "dataset": dataset,
                      "protocol": protocol, "macro_f1": result["outer_macro_f1"],
                      "dimensions_used": result["dimensions_used"],
                      "selected": allocation,
                      "elapsed_seconds": result["elapsed_seconds"]},
                     ensure_ascii=False, indent=2), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("DTD", "FMD", "CUReT",
                        "Outex13Official1360", "SoilOriginal", "KTHTIPS2b"),
                        default="DTD")
    parser.add_argument("--classifier", choices=("svm",), default="svm")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fold", type=int, default=0)
    parser.add_argument("--official-split", type=int)
    parser.add_argument("--curet-direction", choices=("a_to_b", "b_to_a"))
    parser.add_argument("--invert-official-split", action="store_true")
    parser.add_argument("--inner-group-column", default=None)
    parser.add_argument("--inner-folds", type=int, default=3)
    parser.add_argument("--dimension-budget", type=int, default=128)
    parser.add_argument("--rank-choices", type=int, nargs="+", default=(8, 16, 32))
    parser.add_argument("--pca-components", type=int, default=64)
    parser.add_argument("--max-rank", type=int, default=32)
    parser.add_argument("--min-inner-gain", type=float, default=0.001)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results/exploratory/complementary_budget")
    args = parser.parse_args()
    if args.dimension_budget < min(args.rank_choices):
        parser.error("dimension budget must be at least the minimum rank choice")
    if args.inner_folds < 2 or args.pca_components < 1 or args.max_rank < 1:
        parser.error("inner folds, PCA components and max rank must be positive (folds >= 2)")
    run(args)


if __name__ == "__main__":
    main()
