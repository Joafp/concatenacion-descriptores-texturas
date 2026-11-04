#!/usr/bin/env python3
"""Paired-pool nested development evaluation (static core with optional color)."""

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score
from sklearn.model_selection import StratifiedGroupKFold

from budgeted_rescue import acquisition_cost, select_policy
from fsc_tex.cost_model import DEFAULT_HARDWARE_LATENCY_MS as LATENCIES, DEFAULT_POLICY_OVERHEAD_MS as OVERHEAD
from fsc_tex.utility import compute_margins
from run_confirmatory_nested import load_dataset, load_manifest, manifest_groups
from run_topk_individual_control import outer_indices
from run_weighted_lottery_selection import rank_weights
from run_rescue_nested_selection import (
    REPO, COMMON_21, fit_scores, load_existing_ngram, launch_provenance, sha256_file,
    class_counts,
)


def index_hash(indices):
    return hashlib.sha256(np.asarray(indices, dtype="<i8").tobytes()).hexdigest()


def candidate_pool(ranked, seed, draws, subset_size, include_ngram):
    """Paired static-core candidates; color is an optional matched extension."""
    core = [name for name in ranked if name != "rgb_ngram_svd"]
    if len(set(core)) != len(core) or not 2 <= subset_size <= len(core):
        raise ValueError("invalid static core or subset size")
    candidates = {tuple(sorted(core[:k])) for k in (2, 3, 4, 5)}
    rng = np.random.default_rng(seed)
    weights = rank_weights(core, 8.)
    for _ in range(draws):
        candidates.add(tuple(sorted(core[i] for i in rng.choice(
            len(core), size=subset_size, replace=False, p=weights))))
    candidates.add(tuple(sorted(sorted(core, key=lambda n: (LATENCIES[n], n))[:3])))
    if include_ngram:
        candidates |= {tuple(sorted((*subset, "rgb_ngram_svd")))
                       for subset in list(candidates)}
    return sorted(candidates)


def oof_scores(cache, subsets, train, y, groups, labels, seed, n_splits, ngram):
    splitter = StratifiedGroupKFold(n_splits=min(n_splits, len(np.unique(groups[train]))),
                                    shuffle=True, random_state=seed)
    splits = list(splitter.split(train, y[train], groups[train]))
    outputs, log = {}, []
    for subset in subsets:
        scores = np.full((len(train), len(labels)), np.nan)
        for fold, (fit_pos, val_pos) in enumerate(splits):
            fit, val = train[fit_pos], train[val_pos]
            if set(groups[fit]).intersection(groups[val]):
                raise AssertionError("selection fold group overlap")
            value, _, _ = fit_scores(cache, list(subset), fit, val, y, labels, seed, ngram)
            scores[val_pos] = value
        if not np.isfinite(scores).all():
            raise AssertionError("incomplete selection OOF scores")
        outputs[subset] = scores
    for fold, (fit_pos, val_pos) in enumerate(splits):
        log.append({"fold": fold, "fit_indices": train[fit_pos].tolist(),
                    "validation_indices": train[val_pos].tolist()})
    return outputs, log


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--embedding-root", type=Path)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fold", type=int, default=0, choices=range(5))
    split = parser.add_mutually_exclusive_group()
    split.add_argument("--official-split", type=int)
    split.add_argument("--curet-direction", choices=("a_to_b", "b_to_a"))
    parser.add_argument("--invert-official-split", action="store_true")
    parser.add_argument("--inner-group-column")
    parser.add_argument("--library", type=int, choices=(21, 22), default=22)
    parser.add_argument("--ngram-count-cache", type=Path)
    parser.add_argument("--producer-folds", type=int, default=3)
    parser.add_argument("--selection-folds", type=int, default=2)
    parser.add_argument("--budgets-ms", type=float, nargs="+", default=[15., 30., 60., 120.])
    parser.add_argument("--quantiles", type=float, nargs="+", default=[.1, .25, .5])
    parser.add_argument("--candidate-draws", type=int, default=5)
    parser.add_argument("--subset-size", type=int, default=4)
    parser.add_argument("--max-members", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (args.library == 22) != bool(args.ngram_count_cache):
        parser.error("library 22 requires an existing --ngram-count-cache; library 21 does not")
    if any(b <= 0 for b in args.budgets_ms) or len(set(args.budgets_ms)) != len(args.budgets_ms):
        parser.error("budgets must be positive and unique")
    if any(not 0 < q < 1 for q in args.quantiles) or len(set(args.quantiles)) != len(args.quantiles):
        parser.error("quantiles must be unique and strictly between 0 and 1")
    if min(args.producer_folds, args.selection_folds) < 2 or args.max_members < 1:
        parser.error("at least two folds and one member required")
    if args.candidate_draws < 0 or not 2 <= args.subset_size <= len(COMMON_21):
        parser.error("invalid candidate draw count or subset size")
    if args.dataset == "CUReT" and args.curet_direction is None:
        parser.error("CUReT requires a direction")
    def resolve(path):
        return (REPO / path).resolve() if path and not path.is_absolute() else path
    output = resolve(args.output)
    if output.exists() and any(output.iterdir()):
        parser.error("choose an empty output directory")
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    cache, y = load_dataset(REPO, args.dataset, resolve(args.embedding_root))
    cache = {name: cache[name] for name in COMMON_21}
    manifest = resolve(args.manifest_root)
    groups, rows = load_manifest(manifest, args.dataset, y)
    if args.dataset == "KTHTIPS2b" and args.inner_group_column is None:
        args.inner_group_column = "sample"
    inner_groups = manifest_groups(rows, args.inner_group_column) if args.inner_group_column else groups
    ngram, ng_provenance = (load_existing_ngram(rows, resolve(args.ngram_count_cache), 256, 8192, args.seed)
                             if args.library == 22 else (None, None))
    library = COMMON_21 + ([ngram.name] if ngram else [])
    train, external_test = outer_indices(args.dataset, args.seed, args.fold, y, groups, rows,
                                         args.official_split, args.curet_direction, args.invert_official_split)
    if set(groups[train]).intersection(groups[external_test]):
        raise AssertionError("outer source groups overlap")
    provenance = launch_provenance(args, manifest / "sample_manifests" / f"{args.dataset}.csv",
                                   cache, y, {"per_descriptor_latency_ms": LATENCIES,
                                              "policy_overhead_ms": OVERHEAD})
    for path in (Path(__file__), Path(__file__).with_name("budgeted_rescue.py")):
        provenance["source_sha256"][str(path.relative_to(REPO))] = sha256_file(path)
    provenance["ngram_count_cache"] = ng_provenance
    metadata = {"status": "running", "candidate_pool_version": "paired_static_core_v1", "dataset": args.dataset, "library": library,
                "nominal_dimensions": sum(x.shape[1] for x in cache.values()) + (256 if ngram else 0),
                "outer_train_indices_sha256": index_hash(train),
                "external_test_indices_sha256": index_hash(external_test),
                "external_test_evaluated": False, "provenance": provenance,
                "budget_scope": "projected mean on selection OOF; evaluation mean can exceed it",
                "classifier_latency_included": False}
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    labels = np.unique(y)
    producer = StratifiedGroupKFold(n_splits=min(args.producer_folds, len(np.unique(inner_groups[train]))),
                                    shuffle=True, random_state=args.seed + 100)
    predictions, selections, selection_arrays, fold_summary = [], [], {}, []
    for fold, (fit_pos, val_pos) in enumerate(producer.split(train, y[train], inner_groups[train])):
        fit, val = train[fit_pos], train[val_pos]
        if set(inner_groups[fit]).intersection(inner_groups[val]):
            raise AssertionError("producer group overlap")
        singleton, inner_log = oof_scores(cache, [(name,) for name in library], fit, y,
                                          inner_groups, labels, args.seed, args.selection_folds, ngram)
        single_scores = {name: singleton[(name,)] for name in library}
        # Mean per selection fold reproduces the rank-only candidate recipe.
        rank = {}
        for name in library:
            rank[name] = float(np.mean([f1_score(y[fit][np.isin(fit, item["validation_indices"])],
                labels[np.argmax(single_scores[name][np.isin(fit, item["validation_indices"])], axis=1)],
                average="macro", zero_division=0) for item in inner_log]))
        ranked = sorted(rank, key=lambda name: (-rank[name], name))
        candidates = candidate_pool(ranked, args.seed * 10000 + args.fold * 100 + fold,
                                    args.candidate_draws, args.subset_size, ngram is not None)
        member_scores, _ = oof_scores(cache, candidates, fit, y, inner_groups, labels,
                                      args.seed, args.selection_folds, ngram)
        margins = {name: compute_margins(value) for name, value in single_scores.items()}
        selection_arrays[f"fold{fold}_rows"] = fit
        selection_arrays[f"fold{fold}_labels"] = y[fit]
        selection_arrays[f"fold{fold}_single_scores"] = np.stack([single_scores[n] for n in library])
        selection_arrays[f"fold{fold}_member_scores"] = np.stack([member_scores[c] for c in candidates])
        selection_arrays[f"fold{fold}_margins"] = np.stack([margins[n] for n in library])
        fitted = {}
        def evaluate(subset):
            key = tuple(sorted(subset))
            if key not in fitted:
                fitted[key] = fit_scores(cache, list(key), fit, val, y, labels, args.seed, ngram)[0]
            return fitted[key]
        for budget in args.budgets_ms:
            for criterion in ("marginal_cost", "relevance"):
                decision = select_policy(single_scores, member_scores, y[fit], labels, margins,
                                          LATENCIES, budget, args.quantiles, args.max_members,
                                          OVERHEAD, criterion)
                policy = f"{criterion}_B{budget:g}"
                selections.append({"producer_fold": fold, "policy": policy, **decision})
                if not decision["feasible"]:
                    continue
                chosen = decision["selected"]
                base = chosen["base"]
                base_score = evaluate([base])
                base_pred = labels[np.argmax(base_score, axis=1)]
                margin = compute_margins(base_score)
                members = chosen["members"]
                gate = margin < chosen["threshold"] if members else np.zeros(len(val), dtype=bool)
                rescue_pred = (labels[np.argmax(np.mean([evaluate(member) for member in members], axis=0), axis=1)]
                               if members else base_pred)
                pred = np.where(gate, rescue_pred, base_pred)
                union = {block for subset in members for block in subset}
                cost = (LATENCIES[base] + OVERHEAD + gate * sum(LATENCIES[n] for n in union - {base})
                        if members else np.full(len(val), LATENCIES[base]))
                for pos, row_index in enumerate(val):
                    predictions.append({"row_index": int(row_index), "label": int(y[row_index]),
                        "producer_fold": fold, "policy": policy, "prediction": int(pred[pos]),
                        "base": base, "base_prediction": int(base_pred[pos]), "base_margin": float(margin[pos]),
                        "rescue_prediction": int(rescue_pred[pos]), "escalated": bool(gate[pos]),
                        "projected_ms": float(cost[pos]), "budget_ms": budget,
                        "classifier_calls": 1 + int(gate[pos]) * len(members)})
                fold_summary.append({"producer_fold": fold, "policy": policy, "budget_ms": budget,
                    "training_cost_ms": chosen["training_projected_ms"],
                    "observed_validation_cost_ms": float(np.mean(cost)),
                    "validation_budget_exceeded": bool(np.mean(cost) > budget + 1e-10)})
        for name, subset in {"best_individual": [ranked[0]], "top3": ranked[:3],
                             "top4": ranked[:4], "top5": ranked[:5], "full_library": library}.items():
            scores = evaluate(subset)
            pred = labels[np.argmax(scores, axis=1)]
            for pos, row_index in enumerate(val):
                predictions.append({"row_index": int(row_index), "label": int(y[row_index]),
                    "producer_fold": fold, "policy": name, "prediction": int(pred[pos]),
                    "projected_ms": sum(LATENCIES[n] for n in set(subset)), "classifier_calls": 1})
        fold_record = {"producer_fold": fold, "fit_indices": fit.tolist(), "validation_indices": val.tolist(),
                       "fit_indices_sha256": index_hash(fit), "validation_indices_sha256": index_hash(val),
                       "fit_label_counts": class_counts(y[fit]), "validation_label_counts": class_counts(y[val]),
                       "selection_splits": inner_log, "library_order": library,
                       "ranked_blocks": ranked, "ranking": rank,
                       "candidate_order": [list(item) for item in candidates],
                       "unique_fitted_validation_models": [list(item) for item in sorted(fitted)]}
        (output / f"fold{fold}.json").write_text(json.dumps(fold_record, indent=2) + "\n")
        print(f"completed producer fold {fold}: {len(fit)} selection rows, {len(val)} validation rows", flush=True)
    pred_frame = pd.DataFrame(predictions)
    result = []
    expected = [f"{criterion}_B{budget:g}" for budget in args.budgets_ms
                for criterion in ("marginal_cost", "relevance")]
    expected += ["best_individual", "top3", "top4", "top5", "full_library"]
    for policy in expected:
        group = pred_frame[pred_frame["policy"] == policy]
        complete = len(group) == len(train) and group["row_index"].nunique() == len(train)
        result.append({"policy": policy, "complete_oof_coverage": complete, "n_rows": len(group),
            "macro_f1_oof": f1_score(group.label, group.prediction, average="macro", zero_division=0) if complete else None,
            "accuracy_oof": accuracy_score(group.label, group.prediction) if complete else None,
            "projected_ms": group.projected_ms.mean() if complete else None})
    pred_frame.to_csv(output / "predictions.csv", index=False)
    pd.DataFrame(result).to_csv(output / "results.csv", index=False)
    pd.DataFrame(fold_summary).to_csv(output / "budget_checks.csv", index=False)
    (output / "selections.json").write_text(json.dumps(selections, indent=2) + "\n")
    np.savez_compressed(output / "selection_oof_scores.npz", **selection_arrays)
    audits = ngram.transformation_audits() if ngram else []
    for audit in audits:
        a, b = set(audit["train_indices"]), set(audit["evaluation_indices"])
        if a.intersection(b) or not (a | b).issubset(set(train)):
            raise AssertionError("N-gram fit/evaluation outside outer training")
    (output / "ngram_transforms.json").write_text(json.dumps(audits, indent=2) + "\n")
    metadata.update(status="complete", elapsed_seconds=time.perf_counter() - started,
                    ngram_projection_count=len(audits),
                    ngram_effective_components=sorted({a["components"] for a in audits}))
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(pd.DataFrame(result).to_string(index=False))


if __name__ == "__main__":
    main()
