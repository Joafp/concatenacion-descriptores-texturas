#!/usr/bin/env python3
"""Replay saved training-only selections and recalculate budget pilot results."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score

from budgeted_rescue import select_policy
from run_confirmatory_nested import canonical_labels
from run_rescue_nested_selection import REPO, sha256_file


def index_hash(values):
    return hashlib.sha256(np.asarray(values, dtype="<i8").tobytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    policy_rows, checks, projection_rows, summary = [], [], [], {}
    canonical = pd.read_csv(REPO / "results/analysis/integration_v3/canonical_registry_20261021/canonical_conditions.csv")
    for run_path in args.runs:
        path = REPO / run_path if not run_path.is_absolute() else run_path
        meta = json.loads((path / "metadata.json").read_text())
        assert meta["status"] == "complete"
        config, profile = meta["provenance"]["arguments"], meta["provenance"]["cost_profile"]
        latencies, overhead = profile["per_descriptor_latency_ms"], profile["policy_overhead_ms"]
        for source, digest in meta["provenance"]["source_sha256"].items():
            assert sha256_file(REPO / source) == digest, f"source drift: {source}"
        manifest = REPO / meta["provenance"]["manifest_path"]
        assert sha256_file(manifest) == meta["provenance"]["manifest_sha256"]
        manifest_rows = pd.read_csv(manifest, dtype=str)
        labels = canonical_labels(manifest_rows["label"].to_numpy())
        group_values = manifest_rows[config["inner_group_column"] or "group"].to_numpy()
        pred = pd.read_csv(path / "predictions.csv")
        result = pd.read_csv(path / "results.csv")
        selections = json.loads((path / "selections.json").read_text())
        arrays = np.load(path / "selection_oof_scores.npz", allow_pickle=False)
        folds = {int(p.stem.removeprefix("fold")): json.loads(p.read_text())
                 for p in path.glob("fold*.json")}
        all_validation = sorted(row for fold in folds.values() for row in fold["validation_indices"])
        assert len(all_validation) == len(set(all_validation))
        assert index_hash(all_validation) == meta["outer_train_indices_sha256"]
        canonical_match = canonical[(canonical.train_indices_sha256 == meta["outer_train_indices_sha256"])
                                     & (canonical.test_indices_sha256 == meta["external_test_indices_sha256"])]
        assert len(canonical_match) == 1
        for fold_number, fold in folds.items():
            fit, val = np.asarray(fold["fit_indices"]), np.asarray(fold["validation_indices"])
            assert not set(fit).intersection(val)
            assert set(fit) | set(val) == set(all_validation)
            assert not set(group_values[fit]).intersection(group_values[val])
            assert index_hash(fit) == fold["fit_indices_sha256"]
            assert index_hash(val) == fold["validation_indices_sha256"]
            assert np.array_equal(arrays[f"fold{fold_number}_rows"], fit)
            assert np.array_equal(arrays[f"fold{fold_number}_labels"], labels[fit])
            inner_val = []
            for split in fold["selection_splits"]:
                a, b = split["fit_indices"], split["validation_indices"]
                assert not set(a).intersection(b) and set(a) | set(b) == set(fit)
                assert not set(group_values[a]).intersection(group_values[b])
                inner_val.extend(b)
            assert sorted(inner_val) == sorted(fit)
            controls = {"best_individual": fold["ranked_blocks"][:1],
                        "top3": fold["ranked_blocks"][:3],
                        "top4": fold["ranked_blocks"][:4],
                        "top5": fold["ranked_blocks"][:5],
                        "full_library": fold["library_order"]}
            for name, subset in controls.items():
                control = pred[(pred.producer_fold == fold_number) & (pred.policy == name)]
                assert set(control.row_index) == set(val)
                assert np.allclose(control.projected_ms,
                                   sum(latencies[n] for n in set(subset)), atol=1e-9, rtol=0)
                assert control.classifier_calls.eq(1).all()
        assert np.array_equal(pred.label.to_numpy(), labels[pred.row_index.to_numpy()])
        for saved in selections:
            fold_id, policy = saved["producer_fold"], saved["policy"]
            fold = folds[fold_id]
            library, candidates = fold["library_order"], [tuple(x) for x in fold["candidate_order"]]
            single = dict(zip(library, arrays[f"fold{fold_id}_single_scores"]))
            members = dict(zip(candidates, arrays[f"fold{fold_id}_member_scores"]))
            margins = dict(zip(library, arrays[f"fold{fold_id}_margins"]))
            fit_y = arrays[f"fold{fold_id}_labels"]
            class_labels = np.unique(labels)
            replay = select_policy(single, members, fit_y, class_labels, margins,
                latencies, saved["budget_ms"], config["quantiles"], config["max_members"],
                overhead, saved["criterion"])
            original = {k: v for k, v in saved.items() if k not in {"producer_fold", "policy"}}
            assert replay == original, f"selection replay mismatch: {policy}/fold{fold_id}"
            validation = pred[(pred.producer_fold == fold_id) & (pred.policy == policy)]
            if not saved["feasible"]:
                assert validation.empty
                checks.append({"dataset": meta["dataset"], "fold": fold_id, "policy": policy,
                               "feasible": False, "replay_matches": True})
                continue
            selected = saved["selected"]
            base, selected_members = selected["base"], selected["members"]
            base_pred = class_labels[np.argmax(single[base], axis=1)]
            union = {n for subset in selected_members for n in subset}
            if selected_members:
                gate = margins[base] < selected["threshold"]
                assert selected["threshold"] == float(np.quantile(margins[base], selected["quantile"]))
                summed = sum(members[tuple(member)] for member in selected_members)
                train_pred = np.where(gate, class_labels[np.argmax(summed, axis=1)], base_pred)
                train_cost = latencies[base] + overhead + gate.mean() * sum(latencies[n] for n in union - {base})
            else:
                train_pred, train_cost = base_pred, latencies[base]
            assert abs(train_cost - selected["training_projected_ms"]) < 1e-9
            assert train_cost <= saved["budget_ms"] + 1e-9
            assert abs(f1_score(fit_y, train_pred, average="macro", zero_division=0)
                       - selected["training_macro_f1"]) < 1e-12
            assert set(validation.row_index) == set(fold["validation_indices"])
            gate = (validation.base_margin.to_numpy() < selected["threshold"]
                    if selected_members else np.zeros(len(validation), dtype=bool))
            assert np.array_equal(gate, validation.escalated.to_numpy(dtype=bool))
            assert np.array_equal(validation.prediction,
                                  np.where(gate, validation.rescue_prediction, validation.base_prediction))
            cost = (latencies[base] + overhead + gate * sum(latencies[n] for n in union - {base})
                    if selected_members else np.full(len(validation), latencies[base]))
            assert np.allclose(cost, validation.projected_ms, atol=1e-9, rtol=0)
            assert np.array_equal(validation.classifier_calls, 1 + gate * len(selected_members))
            checks.append({"dataset": meta["dataset"], "fold": fold_id, "policy": policy,
                           "feasible": True, "replay_matches": True,
                           "budget_ms": saved["budget_ms"], "training_cost_ms": train_cost,
                           "observed_validation_cost_ms": float(np.mean(cost)),
                           "validation_budget_exceeded": bool(np.mean(cost) > saved["budget_ms"] + 1e-9)})
        for _, row in result.iterrows():
            group = pred[pred.policy == row.policy]
            complete = len(group) == len(all_validation) and group.row_index.is_unique
            assert bool(row.complete_oof_coverage) == complete
            if complete:
                macro = f1_score(group.label, group.prediction, average="macro", zero_division=0)
                accuracy = accuracy_score(group.label, group.prediction)
                assert abs(macro - row.macro_f1_oof) < 1e-12
                assert abs(accuracy - row.accuracy_oof) < 1e-12
                assert abs(group.projected_ms.mean() - row.projected_ms) < 1e-9
            else:
                assert pd.isna(row.macro_f1_oof)
            policy_rows.append({"dataset": meta["dataset"], **row.to_dict()})
        original_budget_checks = pd.read_csv(path / "budget_checks.csv")
        recalculated = {(row["fold"], row["policy"]): row for row in checks
                        if row["dataset"] == meta["dataset"] and row["feasible"]}
        assert len(original_budget_checks) == len(recalculated)
        for _, row in original_budget_checks.iterrows():
            check = recalculated[(row.producer_fold, row.policy)]
            assert abs(row.training_cost_ms - check["training_cost_ms"]) < 1e-9
            assert abs(row.observed_validation_cost_ms - check["observed_validation_cost_ms"]) < 1e-9
            assert row.validation_budget_exceeded == check["validation_budget_exceeded"]
        audits = json.loads((path / "ngram_transforms.json").read_text())
        for i, audit in enumerate(audits):
            a, b = set(audit["train_indices"]), set(audit["evaluation_indices"])
            assert not a.intersection(b) and (a | b).issubset(all_validation)
            assert index_hash(audit["train_indices"]) == audit["train_indices_sha256"]
            assert index_hash(audit["evaluation_indices"]) == audit["evaluation_indices_sha256"]
            assert audit["components"] == min(256, len(a) - 1, audit["hash_bins"] - 1)
            projection_rows.append({"dataset": meta["dataset"], "projection": i,
                                    "fit_rows": len(a), "evaluation_rows": len(b),
                                    "components": audit["components"], "overlap": 0})
        summary[meta["dataset"]] = {
            "status": "ANALYZED", "canonical_condition": canonical_match.iloc[0].condition_id,
            "source_hashes_match": True, "selections_replayed": len(selections),
            "policy_results_recalculated": len(result), "ngram_projections": len(audits),
            "input_sha256": {p.name: sha256_file(p) for p in path.iterdir() if p.is_file()},
            "scope": "saved-score selection replay and arithmetic/routing checks; model fitting not independently reproduced"}
    out = REPO / args.output if not args.output.is_absolute() else args.output
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(checks).to_csv(out / "selection_checks.csv", index=False)
    pd.DataFrame(policy_rows).to_csv(out / "results_recalculated.csv", index=False)
    pd.DataFrame(projection_rows).to_csv(out / "projection_checks.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(pd.DataFrame(policy_rows).to_string(index=False))
    print("replayed selections:", len(checks), "audited projections:", len(projection_rows))


if __name__ == "__main__":
    main()
