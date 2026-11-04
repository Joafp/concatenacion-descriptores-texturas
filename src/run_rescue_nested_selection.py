#!/usr/bin/env python3
"""Nested outer-training evaluation of cost-aware cascade rescue policies.

The external test split is deliberately not loaded as an evaluation target.
This script estimates candidate policy quality inside the outer training data;
it writes the complete quality-cost table and does not choose a deployment
point when no operational loss tolerance has been specified.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ensemble_scoring import decision_scores, training_score_scale  # noqa: E402
from fsc_tex.cost_model import DEFAULT_HARDWARE_LATENCY_MS, DEFAULT_POLICY_OVERHEAD_MS  # noqa: E402
from run_confirmatory_nested import (  # noqa: E402
    load_dataset, load_manifest, make_model, manifest_groups,
)
from run_topk_individual_control import outer_indices  # noqa: E402
from run_weighted_lottery_selection import rank_weights  # noqa: E402
from singleton_ranking import ranked_singletons  # noqa: E402
from fsc_tex.utility import compute_margins  # noqa: E402

REPO = SRC.parent
COMMON_21 = [
    "beitv2_base_final", "convnext_v2_t", "deit_s", "densenet121", "dinov2",
    "dinov2_large", "dinov2_small", "drlbp", "efficientnet_b0", "eva02_base",
    "gabor", "glcm", "hog", "lbp", "mae_base", "resnet101", "resnet50",
    "siglip_base", "swin_t", "vgg16", "vit_b16",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_array(values: np.ndarray) -> str:
    array = np.ascontiguousarray(values)
    digest = hashlib.sha256()
    digest.update(array.dtype.str.encode("ascii"))
    digest.update(json.dumps(array.shape).encode("ascii"))
    digest.update(memoryview(array).cast("B"))
    return digest.hexdigest()


def class_counts(values: np.ndarray) -> dict[str, int]:
    labels, counts = np.unique(values, return_counts=True)
    return {str(label): int(count) for label, count in zip(labels, counts)}


def launch_provenance(args, manifest_path: Path, cache: dict[str, np.ndarray], y: np.ndarray,
                      cost_profile: dict) -> dict:
    source_paths = [
        Path(__file__), SRC / "ensemble_scoring.py", SRC / "singleton_ranking.py",
        SRC / "run_confirmatory_nested.py", SRC / "run_topk_individual_control.py",
        SRC / "run_weighted_lottery_selection.py", SRC / "fsc_tex/cost_model.py",
        SRC / "fsc_tex/utility.py",
        SRC / "rgb_ngram_descriptor.py", SRC / "run_rgb_ngram_outex13_official.py",
    ]
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                                check=True, capture_output=True, text=True).stdout.strip()
        status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                                check=True, capture_output=True, text=True).stdout
        diff = subprocess.run(["git", "diff", "--binary", "HEAD"], cwd=REPO,
                              check=True, capture_output=True).stdout
        git_state = {"commit": commit, "working_tree_dirty": bool(status),
                     "status_sha256": hashlib.sha256(status.encode()).hexdigest(),
                     "tracked_diff_sha256": hashlib.sha256(diff).hexdigest()}
    except (OSError, subprocess.CalledProcessError) as exc:
        git_state = {"status": "unavailable", "error": str(exc)}
    packages = {}
    for name in ("numpy", "pandas", "scikit-learn", "joblib", "scipy"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    profile_payload = json.dumps(cost_profile, sort_keys=True, separators=(",", ":"))
    return {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "command_argv": list(sys.argv),
        "arguments": {key: (str(value) if isinstance(value, Path) else value)
                      for key, value in vars(args).items()},
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "packages": packages,
        "git": git_state,
        "source_sha256": {str(path.relative_to(REPO)): sha256_file(path)
                           for path in source_paths if path.exists()},
        "manifest_path": str(manifest_path.relative_to(REPO)),
        "manifest_sha256": sha256_file(manifest_path),
        "labels_sha256": sha256_array(y),
        "embedding_array_sha256": {name: sha256_array(cache[name]) for name in sorted(cache)},
        "cost_profile": cost_profile,
        "cost_profile_sha256": hashlib.sha256(profile_payload.encode()).hexdigest(),
    }


def block_matrices(cache, subset, train, evaluate, ngram_block=None):
    static = [name for name in subset
              if ngram_block is None or name != ngram_block.name]
    train_parts = [cache[name][train] for name in static]
    eval_parts = [cache[name][evaluate] for name in static]
    if ngram_block is not None and ngram_block.name in subset:
        ng_train, ng_eval, _ = ngram_block.transform(train, evaluate)
        train_parts.append(ng_train)
        eval_parts.append(ng_eval)
    return np.concatenate(train_parts, axis=1), np.concatenate(eval_parts, axis=1)


def fit_scores(cache, subset, train, evaluate, y, labels, seed, ngram_block=None):
    if not np.array_equal(np.unique(y[train]), labels):
        raise ValueError("classifier fit is missing one or more expected classes")
    x_train, x_eval = block_matrices(cache, subset, train, evaluate, ngram_block)
    model = make_model("svm", seed)
    model.fit(x_train, y[train])
    scale = training_score_scale(model, x_train)
    scores = decision_scores(model, x_eval, scale)
    return scores, labels[np.argmax(scores, axis=1)], scale


def base_oof_margins(cache, block, train, y, groups, seed, n_splits, ngram_block=None):
    n_splits = min(n_splits, len(np.unique(groups[train])))
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    margins = np.full(len(train), np.nan, dtype=np.float64)
    for train_pos, val_pos in splitter.split(train, y[train], groups[train]):
        fit_idx, val_idx = train[train_pos], train[val_pos]
        x_fit, x_val = block_matrices(cache, [block], fit_idx, val_idx, ngram_block)
        model = make_model("svm", seed)
        model.fit(x_fit, y[fit_idx])
        scale = training_score_scale(model, x_fit)
        margins[val_pos] = compute_margins(decision_scores(model, x_val, scale))
    if not np.isfinite(margins).all():
        raise RuntimeError("inner OOF margins did not cover all training rows")
    return margins


def load_existing_ngram(rows, path: Path, components: int, bins: int, seed: int):
    """Read a matching count cache without rebuilding or changing its files."""
    from rgb_ngram_descriptor import RGBNgramSVDBlock, _manifest_digest
    from run_rgb_ngram_outex13_official import IMPLEMENTATIONS

    metadata_path = path / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if (metadata.get("manifest_sha256") != _manifest_digest(rows, REPO)
            or metadata.get("samples") != len(rows)):
        raise ValueError("N-gram count cache does not match the current manifest")
    if (metadata.get("implementation") != "rgb_ngram_impl1"
            or metadata.get("config") != IMPLEMENTATIONS["rgb_ngram_impl1"]):
        raise ValueError("N-gram count cache implementation/configuration mismatch")
    counts = {name: np.load(path / f"{name}.npy", mmap_mode="r", allow_pickle=False)
              for name in ("keys", "counts", "indptr")}
    ptr = counts["indptr"]
    if (any(values.ndim != 1 for values in counts.values())
            or len(ptr) != len(rows) + 1 or ptr[0] != 0
            or np.any(np.diff(ptr) < 0)
            or int(ptr[-1]) != len(counts["keys"])
            or len(counts["keys"]) != len(counts["counts"])):
        raise ValueError("invalid N-gram count cache index structure")
    block = RGBNgramSVDBlock(counts, n_components=components,
                             hash_bins=bins, random_state=seed)
    provenance = {
        "path": str(path), "metadata": metadata,
        "file_sha256": {name: sha256_file(path / name) for name in
                        ("metadata.json", "keys.npy", "counts.npy", "indptr.npy")},
        "requested_components": components, "hash_bins": bins,
        "random_state": seed,
        "reuse_scope": "label-free counts reused; SVD fitted separately for each train/evaluation pair",
    }
    return block, provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--base-block", default="auto",
                        help="descriptor selected by singleton inner-CV ranking, or a fixed descriptor name")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fold", type=int, default=0, choices=range(5))
    split = parser.add_mutually_exclusive_group()
    split.add_argument("--official-split", type=int, choices=range(1, 11))
    split.add_argument("--curet-direction", choices=("a_to_b", "b_to_a"))
    parser.add_argument("--invert-official-split", action="store_true")
    parser.add_argument("--inner-group-column")
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--embedding-root", type=Path)
    parser.add_argument("--include-rgb-ngram", action="store_true")
    parser.add_argument("--ngram-count-cache", type=Path,
                        help="existing manifest-matched label-free count cache")
    parser.add_argument("--ngram-components", type=int, default=256)
    parser.add_argument("--ngram-hash-bins", type=int, default=8192)
    parser.add_argument("--cv-folds", type=int, default=4)
    parser.add_argument("--calibration-folds", type=int, default=4)
    parser.add_argument("--escalation-quantiles", type=float, nargs="+", default=[0.10, 0.25, 0.50])
    parser.add_argument("--members", type=int, default=5,
                        help="number of rank-sampled rescue subsets for the 5-member policy")
    parser.add_argument("--subset-size", type=int, default=4)
    parser.add_argument("--beta", type=float, default=8.0)
    parser.add_argument("--ranking-cache", type=Path,
                        default=Path("results/exploratory/integration_v4/ranking_cache"),
                        help="versioned cache directory; kept separate from older runs")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if any(not 0 < q < 1 for q in args.escalation_quantiles):
        parser.error("all escalation quantiles must lie strictly between zero and one")
    if len(set(args.escalation_quantiles)) != len(args.escalation_quantiles):
        parser.error("--escalation-quantiles cannot contain duplicates")
    if args.members < 5:
        parser.error("--members must be at least 5 to compare the 3-member and 5-member policies")
    if args.dataset == "CUReT" and not args.curet_direction:
        parser.error("CUReT requires --curet-direction")
    if args.include_rgb_ngram != bool(args.ngram_count_cache):
        parser.error("--include-rgb-ngram and --ngram-count-cache must be supplied together")
    if args.ngram_components < 1 or args.ngram_hash_bins < 2:
        parser.error("N-gram components must be positive and hash bins >= 2")

    output = ((REPO / args.output).resolve() if not args.output.is_absolute()
              else args.output.resolve())
    ranking_cache = ((REPO / args.ranking_cache).resolve() if not args.ranking_cache.is_absolute()
                     else args.ranking_cache.resolve())
    split_tag = (f"official{args.official_split}"
                 + ("_inverted" if args.invert_official_split else "")
                 if args.official_split is not None else
                 args.curet_direction or f"fold{args.fold}")
    stem = f"{args.dataset}_seed{args.seed}_{split_tag}"
    expected_outputs = [output / f"{stem}_nested_frontier.csv",
                        output / f"{stem}_cv_folds.json",
                        output / f"{stem}_oof_predictions.csv",
                        output / f"{stem}_metadata.json",
                        output / f"{stem}_oof_trace.csv"]
    if args.include_rgb_ngram:
        expected_outputs.append(output / f"{stem}_ngram_transform_audit.json")
    collisions = [str(path) for path in expected_outputs if path.exists()]
    if collisions:
        parser.error("output files already exist; choose a new --output directory: "
                     + ", ".join(collisions))

    started = time.perf_counter()
    embedding_root = ((REPO / args.embedding_root).resolve()
                      if args.embedding_root and not args.embedding_root.is_absolute()
                      else args.embedding_root.resolve() if args.embedding_root else None)
    manifest_root = ((REPO / args.manifest_root).resolve()
                     if not args.manifest_root.is_absolute() else args.manifest_root)
    cache, y = load_dataset(REPO, args.dataset, embedding_root)
    missing = sorted(set(COMMON_21).difference(cache))
    if missing:
        raise ValueError(f"dataset lacks common-21 blocks: {missing}")
    cache = {name: cache[name] for name in COMMON_21}
    groups, rows = load_manifest(manifest_root, args.dataset, y)
    ngram_block, ngram_provenance = None, None
    if args.include_rgb_ngram:
        count_path = ((REPO / args.ngram_count_cache).resolve()
                      if not args.ngram_count_cache.is_absolute() else args.ngram_count_cache.resolve())
        ngram_block, ngram_provenance = load_existing_ngram(
            rows, count_path, args.ngram_components, args.ngram_hash_bins, args.seed)
    library = COMMON_21 + ([ngram_block.name] if ngram_block is not None else [])
    library_tag = "primary22_ngram" if ngram_block is not None else "common21"
    if args.base_block != "auto" and args.base_block not in library:
        raise ValueError(f"base block {args.base_block!r} is not in {library_tag}")
    manifest_path = manifest_root / "sample_manifests" / f"{args.dataset}.csv"
    cost_profile = {"per_descriptor_latency_ms": DEFAULT_HARDWARE_LATENCY_MS,
                    "policy_overhead_ms": DEFAULT_POLICY_OVERHEAD_MS,
                    "scope": "archived profile projection; excludes classifier latency"}
    provenance = launch_provenance(args, manifest_path, cache, y, cost_profile)
    provenance["ngram_count_cache"] = ngram_provenance
    outer_train, outer_test = outer_indices(
        args.dataset, args.seed, args.fold, y, groups, rows,
        args.official_split, args.curet_direction, args.invert_official_split,
    )
    inner_groups = (groups if args.inner_group_column is None
                    else manifest_groups(rows, args.inner_group_column))
    n_cv = min(args.cv_folds, len(np.unique(inner_groups[outer_train])))
    cv = StratifiedGroupKFold(n_splits=n_cv, shuffle=True, random_state=args.seed + 100)
    labels = np.unique(y)
    oof: dict[str, np.ndarray] = {}
    candidate_metadata: dict[str, list[dict]] = {}
    policy_names = ["base", "static_top3", "static_top4", "static_top5",
                    "static_ensemble3", "static_ensemble5"]
    policy_names += [f"cascade_{name}_q{q:g}" for name in
                     ("top3", "top4", "top5", "ensemble3", "ensemble5")
                     for q in args.escalation_quantiles]
    for name in policy_names:
        oof[name] = np.full(len(outer_train), -1, dtype=y.dtype)

    fold_records = []
    fold_artifacts = []
    fold_base_blocks: dict[int, str] = {}
    oof_fold = np.full(len(outer_train), -1, dtype=int)
    oof_base_block = np.full(len(outer_train), "", dtype=object)
    oof_base_margin = np.full(len(outer_train), np.nan, dtype=float)
    threshold_by_q = {q: np.full(len(outer_train), np.nan, dtype=float)
                      for q in args.escalation_quantiles}
    escalate_by_q = {q: np.zeros(len(outer_train), dtype=bool)
                      for q in args.escalation_quantiles}
    for cv_fold, (fit_pos, val_pos) in enumerate(cv.split(outer_train, y[outer_train],
                                                           inner_groups[outer_train])):
        fit_idx, val_idx = outer_train[fit_pos], outer_train[val_pos]
        if set(inner_groups[fit_idx]).intersection(inner_groups[val_idx]):
            raise AssertionError("nested policy validation group leakage")
        split_tag = (f"official{args.official_split}"
                     + ("_inverted" if args.invert_official_split else "")
                     if args.official_split is not None else
                     args.curet_direction or f"f{args.fold}")
        key = (f"{args.dataset}_{library_tag}_svm_s{args.seed}_{split_tag}_cv{cv_fold}_"
               f"inner-{args.inner_group_column or 'group'}")
        rank, rank_info = ranked_singletons(
            cache, fit_idx, y, inner_groups, "svm", args.seed, key,
            cache_dir=ranking_cache,
            n_jobs=4, n_splits=args.calibration_folds,
            protocol_signature={"selection": f"{library_tag}_singleton_macro_f1", "nested_cv_fold": cv_fold},
            return_info=True, ngram_block=ngram_block,
        )
        ranked = [name for name, _ in sorted(rank.items(), key=lambda pair: (-pair[1], pair[0]))]
        base_block = args.base_block if args.base_block != "auto" else ranked[0]
        fold_base_blocks[cv_fold] = base_block
        sizes = {k: ranked[:k] for k in (3, 4, 5)}
        rng = np.random.default_rng(args.seed * 10000 + args.fold * 100 + cv_fold)
        probs = rank_weights(ranked, args.beta)
        sampled = [sorted(ranked[i] for i in rng.choice(len(ranked), size=args.subset_size,
                                                        replace=False, p=probs))
                   for _ in range(args.members)]
        train_margin = base_oof_margins(cache, base_block, fit_idx, y, inner_groups,
                                        args.seed, args.calibration_folds, ngram_block)
        base_scores, base_pred, _ = fit_scores(cache, [base_block], fit_idx, val_idx,
                                                 y, labels, args.seed, ngram_block)
        base_margin = compute_margins(base_scores)
        oof_fold[val_pos] = cv_fold
        oof_base_block[val_pos] = base_block
        oof_base_margin[val_pos] = base_margin
        oof["base"][val_pos] = base_pred
        candidate_scores = {}
        for k, subset in sizes.items():
            scores, pred, _ = fit_scores(cache, subset, fit_idx, val_idx, y, labels, args.seed, ngram_block)
            oof[f"static_top{k}"][val_pos] = pred
            candidate_scores[f"top{k}"] = scores
            candidate_metadata.setdefault(f"top{k}", []).append(
                {"cv_fold": cv_fold, "subset": subset, "union": subset})
        member_cache = {}
        for subset in sorted({tuple(s) for s in sampled}):
            scores, _, scale = fit_scores(cache, list(subset), fit_idx, val_idx,
                                           y, labels, args.seed, ngram_block)
            member_cache[subset] = scores
        for n_members in (3, 5):
            use = sampled[:min(n_members, len(sampled))]
            ensemble_scores = np.mean([member_cache[tuple(s)] for s in use], axis=0)
            ensemble_pred = labels[np.argmax(ensemble_scores, axis=1)]
            oof[f"static_ensemble{n_members}"][val_pos] = ensemble_pred
            candidate_scores[f"ensemble{n_members}"] = ensemble_scores
            member_metadata = {
                "cv_fold": cv_fold, "members": use,
                "union": sorted({block for subset in use for block in subset}),
            }
            candidate_metadata.setdefault(f"ensemble{n_members}", []).append(member_metadata)
        fold_thresholds = []
        for q in args.escalation_quantiles:
            threshold = float(np.quantile(train_margin, q))
            escalate = base_margin < threshold
            threshold_by_q[q][val_pos] = threshold
            escalate_by_q[q][val_pos] = escalate
            for rescue_name, scores in candidate_scores.items():
                rescue_pred = labels[np.argmax(scores, axis=1)]
                pred = base_pred.copy()
                pred[escalate] = rescue_pred[escalate]
                oof[f"cascade_{rescue_name}_q{q:g}"][val_pos] = pred
            fold_records.append({
                "cv_fold": cv_fold, "n_fit": len(fit_idx), "n_validation": len(val_idx),
                "threshold_quantile": q, "threshold": threshold,
                "escalated": int(escalate.sum()), "escalation_fraction": float(np.mean(escalate)),
                "ranked_top5": ranked[:5], "selected_base_block": base_block,
                "gate_definition": "escalate iff frozen base margin < training-OOF quantile threshold",
                "ranking_cache_key": key,
            })
            fold_thresholds.append({
                "quantile": q, "threshold": threshold,
                "escalated_validation_rows": val_idx[escalate].astype(int).tolist(),
                "n_escalated": int(escalate.sum()),
            })

        unique_member_subsets = sorted({tuple(member) for member in sampled})
        fold_artifacts.append({
            "cv_fold": cv_fold,
            "fit_indices": fit_idx.astype(int).tolist(),
            "validation_indices": val_idx.astype(int).tolist(),
            "fit_indices_sha256": hashlib.sha256(np.asarray(fit_idx, dtype="<i8").tobytes()).hexdigest(),
            "validation_indices_sha256": hashlib.sha256(np.asarray(val_idx, dtype="<i8").tobytes()).hexdigest(),
            "n_fit": int(len(fit_idx)), "n_validation": int(len(val_idx)),
            "fit_label_counts": class_counts(y[fit_idx]),
            "validation_label_counts": class_counts(y[val_idx]),
            "fit_group_count": int(len(np.unique(inner_groups[fit_idx]))),
            "validation_group_count": int(len(np.unique(inner_groups[val_idx]))),
            "base_block": base_block, "ranked_blocks": ranked,
            "ranking_scores": {name: float(score) for name, score in rank.items()},
            "ranking_cache": rank_info,
            "topk_subsets": {str(k): subset for k, subset in sizes.items()},
            "sampled_ensemble_members": sampled,
            "unique_ensemble_subsets_and_models": [list(member) for member in unique_member_subsets],
            "unique_ensemble_model_count": len(unique_member_subsets),
            "model_fit_accounting_excluding_rank_and_calibration": {
                "base": 1, "topk_candidates": len(sizes),
                "unique_sampled_ensemble_members": len(unique_member_subsets),
            },
            "thresholds_and_gates": fold_thresholds,
        })

    if any((pred < 0).any() for pred in oof.values()):
        raise RuntimeError("one or more policy OOF predictions are missing")
    records = []
    for name, pred in oof.items():
        rescue_name = name.split("cascade_", 1)[1].rsplit("_q", 1)[0] if name.startswith("cascade_") else None
        if name == "base":
            union_by_fold, is_cascade = {fold: [block] for fold, block in fold_base_blocks.items()}, False
        elif name.startswith("static_top"):
            candidate = name.removeprefix("static_")
            candidate_folds = candidate_metadata[candidate]
            union_by_fold = {item["cv_fold"]: item["union"] for item in candidate_folds}
            is_cascade = False
        elif name.startswith("static_ensemble"):
            candidate = name.removeprefix("static_")
            candidate_folds = candidate_metadata[candidate]
            union_by_fold = {item["cv_fold"]: item["union"] for item in candidate_folds}
            is_cascade = False
        else:
            candidate_folds = candidate_metadata[rescue_name]
            union_by_fold = {item["cv_fold"]: item["union"] for item in candidate_folds}
            is_cascade = True
        missing_costs = sorted(set(block for blocks in union_by_fold.values()
                                   for block in blocks).difference(DEFAULT_HARDWARE_LATENCY_MS))
        if is_cascade:
            q = float(name.rsplit("_q", 1)[1])
            per_fold_costs = []
            per_fold_rates = []
            for cv_fold, fold_union in union_by_fold.items():
                fold_union = set(fold_union)
                fold_missing = fold_union.difference(DEFAULT_HARDWARE_LATENCY_MS)
                rate_row = next(rec for rec in fold_records
                                if rec["cv_fold"] == cv_fold and rec["threshold_quantile"] == q)
                per_fold_rates.append((rate_row["escalation_fraction"], rate_row["n_validation"]))
                base_block = fold_base_blocks[cv_fold]
                base_cost = DEFAULT_HARDWARE_LATENCY_MS.get(base_block)
                if base_cost is None or fold_missing:
                    per_fold_costs.append(None)
                else:
                    extra = sum(DEFAULT_HARDWARE_LATENCY_MS[b] for b in fold_union
                                if b != base_block)
                    per_fold_costs.append(base_cost + DEFAULT_POLICY_OVERHEAD_MS
                                          + rate_row["escalation_fraction"] * extra)
            fold_escalated = sum(rate * size for rate, size in per_fold_rates) / sum(
                size for _, size in per_fold_rates)
            fold_weights = [next(item["n_validation"] for item in fold_artifacts
                                 if item["cv_fold"] == cv_fold)
                            for cv_fold in union_by_fold]
            cost = (float(np.average(per_fold_costs, weights=fold_weights))
                    if per_fold_costs and all(value is not None for value in per_fold_costs) else None)
            missing_costs = sorted(set(block for blocks in union_by_fold.values()
                                       for block in blocks).difference(DEFAULT_HARDWARE_LATENCY_MS))
        else:
            per_fold_costs = [sum(DEFAULT_HARDWARE_LATENCY_MS[b] for b in blocks)
                              if set(blocks).issubset(DEFAULT_HARDWARE_LATENCY_MS) else None
                              for blocks in union_by_fold.values()]
            validation_weights = [len(record["validation_indices"]) for record in fold_artifacts]
            cost = (float(np.average(per_fold_costs, weights=validation_weights))
                    if per_fold_costs and all(value is not None for value in per_fold_costs) else None)
            fold_escalated = 0.0
        records.append({
            "dataset": args.dataset, "policy": name,
            "macro_f1_oof": float(f1_score(y[outer_train], pred, labels=labels,
                                           average="macro", zero_division=0)),
            "accuracy_oof": float(accuracy_score(y[outer_train], pred)),
            "projected_extractor_plus_gate_ms": cost,
            "mean_escalation_fraction": fold_escalated,
            "base_blocks_by_cv_fold": json.dumps(fold_base_blocks),
            "rescue_union_by_cv_fold": json.dumps(union_by_fold),
            "rescue_union_blocks_mean": (float(np.mean([len(v) for v in union_by_fold.values()]))
                                           if name != "base" else 1),
            "missing_hardware_profile": ";".join(missing_costs),
            "classifier_latency_included": False, "external_test_used": False,
            "selection_protocol": "nested grouped CV within outer-training split",
        })
    result = pd.DataFrame(records)
    valid_cost = result["projected_extractor_plus_gate_ms"].notna()
    result["pareto_nondominated"] = False
    for idx, row in result[valid_cost].iterrows():
        dominated = ((result.loc[valid_cost, "macro_f1_oof"] >= row["macro_f1_oof"])
                     & (result.loc[valid_cost, "projected_extractor_plus_gate_ms"] <= row["projected_extractor_plus_gate_ms"])
                     & ((result.loc[valid_cost, "macro_f1_oof"] > row["macro_f1_oof"])
                        | (result.loc[valid_cost, "projected_extractor_plus_gate_ms"] < row["projected_extractor_plus_gate_ms"])))
        result.loc[idx, "pareto_nondominated"] = not bool(dominated.any())
    ngram_audits = ngram_block.transformation_audits() if ngram_block is not None else []
    allowed_rows = set(outer_train.tolist())
    for audit in ngram_audits:
        fit_set, eval_set = set(audit["train_indices"]), set(audit["evaluation_indices"])
        if fit_set.intersection(eval_set) or not (fit_set | eval_set).issubset(allowed_rows):
            raise AssertionError("N-gram projection used overlapping or external rows")
    output.mkdir(parents=True, exist_ok=True)
    if ngram_block is not None:
        (output / f"{stem}_ngram_transform_audit.json").write_text(
            json.dumps(ngram_audits, indent=2) + "\n", encoding="utf-8")
    result.to_csv(output / f"{stem}_nested_frontier.csv", index=False)
    cv_payload = {"folds": fold_records, "fold_artifacts": fold_artifacts}
    (output / f"{stem}_cv_folds.json").write_text(
        json.dumps(cv_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    predictions = pd.DataFrame({"row_index": outer_train, "label": y[outer_train],
                                "cv_fold": oof_fold, "base_block": oof_base_block,
                                "base_margin": oof_base_margin, **oof})
    for q in args.escalation_quantiles:
        qtag = f"{q:g}"
        predictions[f"threshold_q{qtag}"] = threshold_by_q[q]
        predictions[f"escalate_q{qtag}"] = escalate_by_q[q]
    predictions.to_csv(output / f"{stem}_oof_predictions.csv", index=False)
    predictions[["row_index", "label", "cv_fold", "base_block", "base_margin"]
                + [col for q in args.escalation_quantiles
                   for col in (f"threshold_q{q:g}", f"escalate_q{q:g}")]
                + [col for col in oof]].to_csv(output / f"{stem}_oof_trace.csv", index=False)
    metadata = {
        "dataset": args.dataset, "seed": args.seed, "outer_fold": args.fold,
        "official_split": args.official_split,
        "official_split_inverted": args.invert_official_split,
        "curet_direction": args.curet_direction,
        "outer_train_rows": int(len(outer_train)), "external_test_rows_not_evaluated": int(len(outer_test)),
        "base_block_selection": ("best individual macro-F1 from inner ranking per producer fold"
                                  if args.base_block == "auto" else f"fixed descriptor: {args.base_block}"),
        "base_blocks_by_cv_fold": fold_base_blocks,
        "inner_group_column": args.inner_group_column or "group",
        "library": library, "library_tag": library_tag,
        "nominal_library_dimensions": sum(cache[name].shape[1] for name in COMMON_21)
            + (ngram_block.n_components if ngram_block is not None else 0),
        "ngram_projection_count": len(ngram_audits),
        "ngram_effective_components": sorted({audit["components"] for audit in ngram_audits}),
        "cv_folds": n_cv, "calibration_folds": args.calibration_folds,
        "escalation_quantiles": args.escalation_quantiles, "subset_size": args.subset_size,
        "ensemble_member_counts": [3, 5], "sampling_beta": args.beta,
        "decision": "report full frontier; no single point selected because an operational loss tolerance is not specified",
        "cost_note": "extractor latency plus gate overhead projection; excludes classifier and is not a physical measurement",
        "cost_aggregation": "validation-image weighted mean over producer folds",
        "execution_provenance": provenance,
        "fold_artifact_file": f"{stem}_cv_folds.json",
        "prediction_trace_file": f"{stem}_oof_trace.csv",
        "external_test_indices_sha256": hashlib.sha256(
            np.asarray(outer_test, dtype="<i8").tobytes()).hexdigest(),
        "outer_train_indices_sha256": hashlib.sha256(
            np.asarray(outer_train, dtype="<i8").tobytes()).hexdigest(),
        "outer_train_label_counts": class_counts(y[outer_train]),
        "elapsed_seconds": time.perf_counter() - started,
    }
    (output / f"{stem}_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(result[["policy", "macro_f1_oof", "projected_extractor_plus_gate_ms",
                  "mean_escalation_fraction", "pareto_nondominated"]].to_string(index=False))
    print(f"Saved nested outer-training frontier to {output}; external test was not evaluated.")


if __name__ == "__main__":
    main()
