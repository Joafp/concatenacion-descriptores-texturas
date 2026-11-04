#!/usr/bin/env python3
"""Exploratory cascade pilot with a rank-sampled ensemble as its rescue route.

All selection and the escalation threshold use outer-training data. Reported
extractor costs are projections from the repository's RTX 4060 profile; this
script evaluates cached embeddings and does not measure image-to-prediction time.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

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
    audit_gate, load_dataset, load_manifest, make_model, manifest_groups,
)
from run_topk_individual_control import outer_indices  # noqa: E402
from run_weighted_lottery_selection import rank_weights  # noqa: E402
from singleton_ranking import condition_key, ranked_singletons  # noqa: E402
from fsc_tex.utility import compute_margins  # noqa: E402

REPO = SRC.parent


def f1(y_true, y_pred, labels):
    return float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--classifier", choices=("svm",), default="svm")
    parser.add_argument("--base-block", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fold", type=int, default=0, choices=range(5))
    split = parser.add_mutually_exclusive_group()
    split.add_argument("--official-split", type=int, choices=range(1, 11))
    split.add_argument("--curet-direction", choices=("a_to_b", "b_to_a"))
    parser.add_argument("--invert-official-split", action="store_true")
    parser.add_argument("--inner-group-column")
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--members", type=int, default=15)
    parser.add_argument("--beta", type=float, default=8.0)
    parser.add_argument("--escalation-quantile", type=float, default=0.25)
    parser.add_argument("--inner-splits", type=int, default=4)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--embedding-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 0 < args.escalation_quantile < 1:
        parser.error("--escalation-quantile must be between zero and one")
    if args.dataset == "CUReT" and not args.curet_direction:
        parser.error("CUReT requires --curet-direction")

    started = time.perf_counter()
    audit_root, manifest_root, output = (p.resolve() for p in
                                         (args.audit_root, args.manifest_root, args.output))
    embedding_root = args.embedding_root.resolve() if args.embedding_root else None
    audit_gate(audit_root, args.dataset)
    cache, y = load_dataset(REPO, args.dataset, embedding_root=embedding_root)
    if args.base_block not in cache:
        raise ValueError(f"base block {args.base_block!r} missing from {args.dataset}")
    groups, rows = load_manifest(manifest_root, args.dataset, y)
    train, test = outer_indices(args.dataset, args.seed, args.fold, y, groups, rows,
                                args.official_split, args.curet_direction,
                                args.invert_official_split)
    if set(groups[train]).intersection(groups[test]):
        raise AssertionError("outer group leakage")
    inner_groups = (groups if args.inner_group_column is None
                    else manifest_groups(rows, args.inner_group_column))
    fold = (args.official_split - 1 if args.official_split is not None
            else {"a_to_b": 0, "b_to_a": 1}[args.curet_direction]
            if args.curet_direction is not None else args.fold)
    labels = np.unique(y)

    # Rank and sample the rescue subsets using only the outer training split.
    names = sorted(cache)
    jobs = 4
    ranking = ranked_singletons(cache, train, y, inner_groups, "svm", args.seed,
                                condition_key(args), n_jobs=jobs)
    ranked = [name for name, _ in sorted(ranking.items(), key=lambda p: (-p[1], p[0]))]
    k = min(args.k, len(ranked))
    rng = np.random.default_rng(args.seed * 1000 + fold * 10 + int(args.beta * 2))
    probs = rank_weights(ranked, args.beta)
    subsets = [sorted(ranked[i] for i in rng.choice(len(ranked), size=k,
                                                     replace=False, p=probs))
               for _ in range(args.members)]
    unique_subsets = sorted({tuple(s) for s in subsets})
    union = sorted({block for subset in subsets for block in subset})

    # Calibrate an economic base stage with normalized OOF margins.
    n_splits = min(args.inner_splits, len(np.unique(inner_groups[train])))
    if n_splits < 2:
        raise ValueError("fewer than two inner groups for OOF threshold calibration")
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True,
                                    random_state=args.seed)
    oof_margins = np.full(len(train), np.nan, dtype=np.float64)
    for tr_pos, val_pos in splitter.split(train, y[train], inner_groups[train]):
        inner_train, inner_val = train[tr_pos], train[val_pos]
        model = make_model("svm", args.seed)
        x_train, x_val = cache[args.base_block][inner_train], cache[args.base_block][inner_val]
        model.fit(x_train, y[inner_train])
        scale = training_score_scale(model, x_train)
        val_scores = decision_scores(model, x_val, scale)
        oof_margins[val_pos] = compute_margins(val_scores)
    if not np.isfinite(oof_margins).all():
        raise RuntimeError("OOF threshold calibration did not cover every training sample")
    threshold = float(np.quantile(oof_margins, args.escalation_quantile))

    # Fit base classifier and rescue members on the complete outer training set.
    base_model = make_model("svm", args.seed)
    x_base_train = cache[args.base_block][train]
    base_model.fit(x_base_train, y[train])
    base_scale = training_score_scale(base_model, x_base_train)
    x_base_test = cache[args.base_block][test]
    base_scores = decision_scores(base_model, x_base_test, base_scale)
    base_margins = compute_margins(base_scores)
    base_predictions = np.asarray(base_model.predict(x_base_test))
    escalate = base_margins < threshold

    fitted = {}
    for subset in unique_subsets:
        x_train = np.concatenate([cache[b][train] for b in subset], axis=1)
        x_test = np.concatenate([cache[b][test] for b in subset], axis=1)
        model = make_model("svm", args.seed)
        model.fit(x_train, y[train])
        scale = training_score_scale(model, x_train)
        fitted[subset] = {
            "scores": decision_scores(model, x_test, scale),
            "predictions": np.asarray(model.predict(x_test)),
            "scale": scale,
        }
    member_scores = [fitted[tuple(s)]["scores"] for s in subsets]
    rescue_scores = np.mean(member_scores, axis=0)
    rescue_predictions = labels[np.argmax(rescue_scores, axis=1)]
    cascade_predictions = base_predictions.copy()
    cascade_predictions[escalate] = rescue_predictions[escalate]

    # Static baselines on the same split and available 21-block library.
    top4 = ranked[:k]
    full = names
    static = {}
    for name, subset in (("Top-k", top4), ("Completa-disponible", full)):
        x_train = np.concatenate([cache[b][train] for b in subset], axis=1)
        x_test = np.concatenate([cache[b][test] for b in subset], axis=1)
        model = make_model("svm", args.seed)
        model.fit(x_train, y[train])
        static[name] = np.asarray(model.predict(x_test))
        if name == "Top-k":
            topk_scale = training_score_scale(model, x_train)
    cascade_topk_predictions = base_predictions.copy()
    cascade_topk_predictions[escalate] = static["Top-k"][escalate]

    # Projection uses extractor latencies once per block in the union. It omits
    # classifier latency and is explicitly not a physical measurement.
    missing_costs = sorted(set(names).difference(DEFAULT_HARDWARE_LATENCY_MS))
    base_latency = DEFAULT_HARDWARE_LATENCY_MS.get(args.base_block)
    extra_union = sorted(set(union).difference({args.base_block}))
    extra_topk = sorted(set(top4).difference({args.base_block}))
    extra_latency = (sum(DEFAULT_HARDWARE_LATENCY_MS[b] for b in extra_union)
                     if set(extra_union).issubset(DEFAULT_HARDWARE_LATENCY_MS) else None)
    extra_topk_latency = (sum(DEFAULT_HARDWARE_LATENCY_MS[b] for b in extra_topk)
                          if set(extra_topk).issubset(DEFAULT_HARDWARE_LATENCY_MS) else None)
    projected_mean = (base_latency + DEFAULT_POLICY_OVERHEAD_MS
                      + float(np.mean(escalate)) * extra_latency
                      if base_latency is not None and extra_latency is not None else None)
    projected_topk_cascade = (base_latency + DEFAULT_POLICY_OVERHEAD_MS
                              + float(np.mean(escalate)) * extra_topk_latency
                              if base_latency is not None and extra_topk_latency is not None else None)
    static_union_latency = (sum(DEFAULT_HARDWARE_LATENCY_MS[b] for b in union)
                            if set(union).issubset(DEFAULT_HARDWARE_LATENCY_MS) else None)
    static_topk_latency = (sum(DEFAULT_HARDWARE_LATENCY_MS[b] for b in top4)
                           if set(top4).issubset(DEFAULT_HARDWARE_LATENCY_MS) else None)
    static_complete_latency = (sum(DEFAULT_HARDWARE_LATENCY_MS[b] for b in names)
                               if set(names).issubset(DEFAULT_HARDWARE_LATENCY_MS) else None)

    y_test = y[test]
    summary = {
        "dataset": args.dataset, "classifier": "svm", "seed": args.seed,
        "outer_fold": fold, "base_block": args.base_block,
        "official_split": args.official_split,
        "official_split_inverted": bool(args.invert_official_split),
        "curet_direction": args.curet_direction,
        "available_blocks": len(names), "available_block_names": names,
        "rgb_ngram_svd_included": "rgb_ngram_svd" in cache,
        "library_note": "dataset-specific available embedding cache; not assumed identical to the 22-descriptor primary library",
        "k": k, "members": args.members, "unique_subsets": len(unique_subsets),
        "beta": args.beta, "escalation_quantile_fixed_on_training": args.escalation_quantile,
        "inner_group_column": args.inner_group_column or "group",
        "threshold_normalized_margin": threshold,
        "n_train": int(len(train)), "n_test": int(len(test)),
        "escalated": int(escalate.sum()), "escalation_fraction": float(np.mean(escalate)),
        "macro_f1": {
            "base": f1(y_test, base_predictions, labels),
            "top_k_static": f1(y_test, static["Top-k"], labels),
            "rescue_ensemble_static": f1(y_test, rescue_predictions, labels),
            "complete_available_static": f1(y_test, static["Completa-disponible"], labels),
            "cascade_with_rescue": f1(y_test, cascade_predictions, labels),
            "cascade_with_top_k_rescue": f1(y_test, cascade_topk_predictions, labels),
        },
        "accuracy": {
            "base": float(accuracy_score(y_test, base_predictions)),
            "top_k_static": float(accuracy_score(y_test, static["Top-k"])),
            "rescue_ensemble_static": float(accuracy_score(y_test, rescue_predictions)),
            "complete_available_static": float(accuracy_score(y_test, static["Completa-disponible"])),
            "cascade_with_rescue": float(accuracy_score(y_test, cascade_predictions)),
            "cascade_with_top_k_rescue": float(accuracy_score(y_test, cascade_topk_predictions)),
        },
        "prediction_agreement": {
            "cascade_vs_static_rescue_ensemble": float(np.mean(cascade_predictions == rescue_predictions)),
            "cascade_vs_static_top_k": float(np.mean(cascade_predictions == static["Top-k"])),
            "cascade_vs_cascade_top_k_rescue": float(np.mean(cascade_predictions == cascade_topk_predictions)),
        },
        "mean_classifier_calls_per_image": float(1 + np.mean(escalate) * len(unique_subsets)),
        "top_k_subset": top4,
        "rescue_subsets": [list(s) for s in subsets], "rescue_union": union,
        "rescue_union_blocks": len(union), "rescue_extra_blocks_after_base": extra_union,
        "base_score_scale": base_scale,
        "member_score_scales": [fitted[tuple(s)]["scale"] for s in subsets],
        "top_k_rescue_score_scale": topk_scale,
        "cost_projection_ms": {
            "base_extractor": base_latency,
            "rescue_union_additional_extractors": extra_latency,
            "cascade_mean_extraction_plus_gate": projected_mean,
            "cascade_top_k_rescue_extraction_plus_gate": projected_topk_cascade,
            "static_rescue_union_extraction": static_union_latency,
            "static_top_k_extraction": static_topk_latency,
            "static_complete_available_extraction": static_complete_latency,
            "missing_hardware_profile_blocks": missing_costs,
            "classifier_latency_included": False,
            "physical_measurement": False,
        },
        "calibration": "OOF normalized margins on outer-training groups only",
        "score_normalization": "member global std fitted on training rows; batch independent",
        "duration_seconds": time.perf_counter() - started,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / f"{args.dataset}_svm_s{args.seed}_fold{fold}_cascade_rescue.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    pd.DataFrame({
        "row_index": test, "label": y_test, "base_margin": base_margins,
        "escalate": escalate.astype(int), "base_prediction": base_predictions,
        "top_k_static_prediction": static["Top-k"],
        "cascade_top_k_rescue_prediction": cascade_topk_predictions,
        "rescue_ensemble_prediction": rescue_predictions,
        "cascade_prediction": cascade_predictions,
        "complete_available_prediction": static["Completa-disponible"],
    }).to_csv(output / f"{args.dataset}_svm_s{args.seed}_fold{fold}_predictions.csv", index=False)
    projected_label = (f"{projected_mean:.2f} ms" if projected_mean is not None
                       else "not available (incomplete hardware profile)")
    print(f"{args.dataset} {args.base_block} q={args.escalation_quantile:.2f}: "
          f"cascade F1={summary['macro_f1']['cascade_with_rescue']:.4f}, "
          f"base={summary['macro_f1']['base']:.4f}, Top-k={summary['macro_f1']['top_k_static']:.4f}, "
          f"ensemble={summary['macro_f1']['rescue_ensemble_static']:.4f}, "
          f"escalated={summary['escalated']}/{len(test)}, union={len(union)}, "
          f"projected extraction={projected_label} (not physical)")


if __name__ == "__main__":
    main()
