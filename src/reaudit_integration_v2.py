#!/usr/bin/env python3
"""Recalculate saved integration-v2 metrics and audit their protocol and costs.

No models are fitted and no historical results are overwritten. Weighted costs
are diagnostic recalculations from saved fold routes and the current profile.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold

from register_nested_frontiers import CONDITIONS, REPO, ROOT
from rgb_ngram_descriptor import _manifest_digest
from run_confirmatory_nested import load_dataset, load_manifest, manifest_groups, official_split_indices
from run_topk_individual_control import outer_indices
from fsc_tex.cost_model import DEFAULT_HARDWARE_LATENCY_MS, DEFAULT_POLICY_OVERHEAD_MS

OUT = REPO / "results/analysis/integration_v2/reaudit_20261021"


def pareto(frame, cost_column):
    values = frame[cost_column].to_numpy(float)
    quality = frame.macro_f1_recomputed.to_numpy(float)
    return np.asarray([not np.any((quality >= quality[i]) & (values <= values[i])
                                  & ((quality > quality[i]) | (values < values[i])))
                       for i in range(len(frame))])


def main():
    policy_rows, fold_rows, condition_rows, cache_rows = [], [], [], []
    manifests = {}
    input_hashes = {}
    historical_summary = pd.read_csv(REPO / "results/analysis/integration_v2/nested_frontier_summary.csv")
    for folder, (dataset, manifest_rel, official, direction, invert, embedding_rel) in CONDITIONS.items():
        directory = ROOT / folder
        paths = {key: next(directory.glob(pattern)) for key, pattern in {
            "metrics": "*_nested_frontier.csv", "folds": "*_cv_folds.json",
            "metadata": "*_metadata.json", "predictions": "*_oof_predictions.csv"}.items()}
        for path in paths.values():
            input_hashes[str(path.relative_to(REPO))] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path = REPO / manifest_rel / "sample_manifests" / f"{dataset}.csv"
        input_hashes[str(manifest_path.relative_to(REPO))] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        archived = pd.read_csv(paths["metrics"])
        oof = pd.read_csv(paths["predictions"])
        meta = json.loads(paths["metadata"].read_text())
        fold_log = pd.DataFrame(json.loads(paths["folds"].read_text()))
        cache, y = load_dataset(REPO, dataset, REPO / embedding_rel if embedding_rel else None)
        groups, rows = load_manifest(REPO / manifest_rel, dataset, y)
        manifests[dataset] = (rows, _manifest_digest(rows, REPO))
        train, test = outer_indices(dataset, 42, 0, y, groups, rows, official, direction, invert)
        inner = groups if meta["inner_group_column"] == "group" else manifest_groups(rows, meta["inner_group_column"])
        splits = list(StratifiedGroupKFold(n_splits=meta["cv_folds"], shuffle=True,
                                          random_state=142).split(train, y[train], inner[train]))
        counts = {}
        group_overlap_total = 0
        missing_classes_total = 0
        for fold, (fit_pos, val_pos) in enumerate(splits):
            fit, val = train[fit_pos], train[val_pos]
            log = fold_log[fold_log.cv_fold == fold]
            counts[fold] = len(val)
            overlap = len(set(inner[fit]).intersection(inner[val]))
            missing_classes = sorted(set(np.unique(y)).difference(y[fit]))
            group_overlap_total += overlap
            missing_classes_total += len(missing_classes)
            fold_rows.append({"condition": folder, "cv_fold": fold,
                              "n_fit": len(fit), "n_validation": len(val),
                              "group_overlap": overlap, "missing_training_classes": str(missing_classes),
                              "recorded_sizes_match": bool((log.n_fit == len(fit)).all() and
                                                           (log.n_validation == len(val)).all())})
        local = []
        for _, row in archived.iterrows():
            prediction = oof[row.policy].to_numpy()
            f1 = float(f1_score(y[train], prediction, labels=np.unique(y), average="macro", zero_division=0))
            acc = float(accuracy_score(y[train], prediction))
            unions = json.loads(row.rescue_union_by_cv_fold)
            bases = json.loads(row.base_blocks_by_cv_fold)
            fold_costs, weights = [], []
            for fold in range(len(splits)):
                union = set(unions[str(fold)])
                weights.append(counts[fold])
                if row.policy.startswith("cascade_"):
                    q = float(row.policy.rsplit("_q", 1)[1])
                    log = fold_log[(fold_log.cv_fold == fold) & (fold_log.threshold_quantile == q)].iloc[0]
                    rate = float(log.escalated) / counts[fold]
                    base = bases[str(fold)]
                    cost = DEFAULT_HARDWARE_LATENCY_MS[base] + DEFAULT_POLICY_OVERHEAD_MS
                    cost += rate * sum(DEFAULT_HARDWARE_LATENCY_MS[b] for b in union if b != base)
                else:
                    cost = sum(DEFAULT_HARDWARE_LATENCY_MS[b] for b in union)
                fold_costs.append(cost)
            weighted = float(np.average(fold_costs, weights=weights))
            local.append({"condition": folder, "dataset": dataset, "policy": row.policy,
                          "macro_f1_archived": row.macro_f1_oof, "macro_f1_recomputed": f1,
                          "f1_abs_error": abs(f1 - row.macro_f1_oof),
                          "accuracy_abs_error": abs(acc - row.accuracy_oof),
                          "cost_archived_ms": row.projected_extractor_plus_gate_ms,
                          "cost_equal_fold_recomputed_ms": float(np.mean(fold_costs)),
                          "cost_image_weighted_ms": weighted,
                          "cost_weighting_delta_ms": weighted - row.projected_extractor_plus_gate_ms,
                          "archived_pareto": row.pareto_nondominated})
        frame = pd.DataFrame(local)
        frame["pareto_equal_fold_recomputed"] = pareto(frame, "cost_equal_fold_recomputed_ms")
        frame["pareto_image_weighted"] = pareto(frame, "cost_image_weighted_ms")
        policy_rows += frame.to_dict("records")
        official_match = None
        official_overlap = None
        if dataset == "DTD":
            official_train, official_test = official_split_indices(rows, 1)
            official_match = set(train) == set(official_train) and set(test) == set(official_test)
            official_overlap = len(set(train).intersection(official_test))
        summary_rows = historical_summary[historical_summary.condition == folder]
        summary_match = len(summary_rows) == len(archived)
        if summary_match:
            left = summary_rows.set_index("policy").sort_index()
            right = archived.set_index("policy").sort_index()
            summary_match = (left.index.equals(right.index) and
                             np.allclose(left.macro_f1_oof, right.macro_f1_oof, atol=1e-14, rtol=0))
        condition_rows.append({"condition": folder, "dataset": dataset, "policies": len(frame),
                               "oof_exact_train_order": np.array_equal(oof.row_index.to_numpy(), train),
                               "oof_labels_match": np.array_equal(oof.label.to_numpy(), y[train]),
                               "oof_row_indices_unique": bool(oof.row_index.is_unique),
                               "outer_group_overlap": len(set(groups[train]).intersection(groups[test])),
                               "cv_group_overlap": group_overlap_total,
                               "cv_missing_training_classes": missing_classes_total,
                               "max_f1_abs_error": float(frame.f1_abs_error.max()),
                               "summary_matches_predictions": summary_match,
                               "validation_fold_sizes": json.dumps(list(counts.values())),
                               "max_cost_weighting_abs_delta_ms": float(frame.cost_weighting_delta_ms.abs().max()),
                               "pareto_changes_after_weighting": int((frame.pareto_image_weighted != frame.archived_pareto).sum()),
                               "dtd_matches_official1": official_match,
                               "dtd_training_rows_in_official1_test": official_overlap})
    for path in (REPO / "results").rglob("metadata.json"):
        if "rgb_ngram_count_cache" not in path.parts:
            continue
        metadata = json.loads(path.read_text())
        dataset = path.parent.parent.name
        if dataset not in manifests:
            continue
        rows, digest = manifests[dataset]
        directory = path.parent
        files = [directory / name for name in ("keys.npy", "counts.npy", "indptr.npy")]
        present = all(p.is_file() for p in files)
        shape_ok = False
        if present:
            keys, counts, ptr = [np.load(p, mmap_mode="r") for p in files]
            shape_ok = (len(ptr) == len(rows) + 1 and int(ptr[0]) == 0 and
                        int(ptr[-1]) == len(keys) == len(counts) and bool(np.all(ptr[1:] >= ptr[:-1])))
        cache_rows.append({"dataset": dataset, "path": str(directory.relative_to(REPO)),
                           "metadata_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                           "samples": metadata.get("samples"), "expected_samples": len(rows),
                           "manifest_digest_matches_current": metadata.get("manifest_sha256") == digest,
                           "count_files_present": present, "count_index_shapes_match": shape_ok,
                           "implementation": metadata.get("implementation"),
                           "scope": "metadata and array indices; source image bytes not rehashed"})
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(policy_rows).to_csv(OUT / "policy_recalculation.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(OUT / "fold_reconstruction.csv", index=False)
    pd.DataFrame(condition_rows).to_csv(OUT / "condition_checks.csv", index=False)
    pd.DataFrame(cache_rows).to_csv(OUT / "ngram_cache_inventory.csv", index=False)
    policies = pd.DataFrame(policy_rows)
    caches = pd.DataFrame(cache_rows)
    summary = {
        "verification_status": "ANALYZED",
        "scope": "saved-prediction recalculation and current-code protocol reconstruction; no retraining",
        "conditions": len(condition_rows), "policy_rows": len(policy_rows),
        "max_macro_f1_abs_error": float(policies.f1_abs_error.max()),
        "max_accuracy_abs_error": float(policies.accuracy_abs_error.max()),
        "cost_rows_changed_above_1e_8_ms": int((policies.cost_weighting_delta_ms.abs() > 1e-8).sum()),
        "pareto_flags_changed_after_cost_weighting": int((policies.archived_pareto != policies.pareto_image_weighted).sum()),
        "ngram_caches_found": len(cache_rows),
        "ngram_cache_manifest_matches": int(caches.manifest_digest_matches_current.sum()),
        "training_reproduced": False,
        "input_file_hashes": input_hashes,
        "current_source_hashes": {
            name: hashlib.sha256((REPO / "src" / name).read_bytes()).hexdigest()
            for name in ("reaudit_integration_v2.py", "run_rescue_nested_selection.py",
                         "register_nested_frontiers.py", "rgb_ngram_descriptor.py", "singleton_ranking.py")
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(pd.DataFrame(condition_rows).to_string(index=False))
    print("N-gram caches:", len(cache_rows))
    if cache_rows:
        print(pd.DataFrame(cache_rows).groupby("dataset")[["manifest_digest_matches_current", "count_files_present", "count_index_shapes_match"]].sum().to_string())


if __name__ == "__main__":
    main()
