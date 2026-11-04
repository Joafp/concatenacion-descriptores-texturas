#!/usr/bin/env python3
"""Recalculate the P1-A development checks from saved smoke artifacts."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "results/exploratory/integration_v4"
OUT = REPO / "results/analysis/integration_v4/ngram_integration_20261021"
RUNS = {
    "auto22": "smoke22_fmd_20261021",
    "ngram_base22": "smoke22_fmd_ngram_base_20261021",
    "matched21": "smoke21_fmd_matched_20261021",
}


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def indices_hash(indices):
    return hashlib.sha256(np.asarray(indices, dtype="<i8").tobytes()).hexdigest()


def main():
    policy_checks, projection_checks, runs = [], [], {}
    inputs = {}
    canonical = pd.read_csv(REPO / "results/analysis/integration_v3/canonical_registry_20261021/canonical_conditions.csv")
    canonical_hash = canonical.set_index("condition_id").loc["FMD_s42_f0", "train_indices_sha256"]
    for run_name, folder in RUNS.items():
        path = ROOT / folder
        metadata_path = next(path.glob("*_metadata.json"))
        pred_path = next(path.glob("*_oof_predictions.csv"))
        frontier_path = next(path.glob("*_nested_frontier.csv"))
        fold_path = next(path.glob("*_cv_folds.json"))
        meta, folds = json.loads(metadata_path.read_text()), json.loads(fold_path.read_text())
        pred, frontier = pd.read_csv(pred_path), pd.read_csv(frontier_path)
        profile = meta["execution_provenance"]["cost_profile"]
        latency, overhead = profile["per_descriptor_latency_ms"], profile["policy_overhead_ms"]
        assert pred["row_index"].is_unique and not pred.isna().any().any()
        assert indices_hash(pred["row_index"]) == meta["outer_train_indices_sha256"] == canonical_hash
        for source, digest in meta["execution_provenance"]["source_sha256"].items():
            assert sha256_file(REPO / source) == digest, f"source changed after smoke: {source}"
        for _, row in frontier.iterrows():
            policy = row["policy"]
            costs = np.full(len(pred), np.nan)
            unions = json.loads(row["rescue_union_by_cv_fold"])
            base_by_fold = json.loads(row["base_blocks_by_cv_fold"])
            cascade = policy.startswith("cascade_")
            for fold, union in unions.items():
                mask = pred["cv_fold"].to_numpy() == int(fold)
                if cascade:
                    rescue, q = policy.removeprefix("cascade_").rsplit("_q", 1)
                    gate = pred[f"escalate_q{q}"].to_numpy(dtype=bool)
                    expected_gate = pred["base_margin"].to_numpy() < pred[f"threshold_q{q}"].to_numpy()
                    assert np.array_equal(gate, expected_gate)
                    expected_pred = np.where(gate, pred[f"static_{rescue}"], pred["base"])
                    assert np.array_equal(pred[policy], expected_pred)
                    base = base_by_fold[fold]
                    extra = sum(latency[block] for block in set(union) - {base})
                    costs[mask] = latency[base] + overhead + gate[mask] * extra
                else:
                    costs[mask] = sum(latency[block] for block in set(union))
            f1 = f1_score(pred["label"], pred[policy], average="macro", zero_division=0)
            accuracy = accuracy_score(pred["label"], pred[policy])
            f1_error, acc_error = abs(f1 - row["macro_f1_oof"]), abs(accuracy - row["accuracy_oof"])
            cost_error = abs(float(costs.mean()) - row["projected_extractor_plus_gate_ms"])
            assert f1_error < 1e-12 and acc_error < 1e-12 and cost_error < 1e-9
            policy_checks.append({"run": run_name, "policy": policy,
                                  "macro_f1_error": f1_error, "accuracy_error": acc_error,
                                  "per_image_cost_error_ms": cost_error})
        audits = []
        if len(meta["library"]) == 22:
            audit_path = next(path.glob("*_ngram_transform_audit.json"))
            audits = json.loads(audit_path.read_text())
            allowed = set(pred["row_index"])
            for i, audit in enumerate(audits):
                fit, evaluation = set(audit["train_indices"]), set(audit["evaluation_indices"])
                assert not fit.intersection(evaluation) and (fit | evaluation).issubset(allowed)
                assert indices_hash(audit["train_indices"]) == audit["train_indices_sha256"]
                assert indices_hash(audit["evaluation_indices"]) == audit["evaluation_indices_sha256"]
                assert audit["components"] == min(256, len(fit) - 1, audit["hash_bins"] - 1)
                projection_checks.append({"run": run_name, "projection": i,
                                          "fit_rows": len(fit), "evaluation_rows": len(evaluation),
                                          "components": audit["components"], "overlap": 0,
                                          "outside_outer_training": 0})
        runs[run_name] = {
            "library_blocks": len(meta["library"]), "nominal_dimensions": meta["nominal_library_dimensions"],
            "producer_folds": meta["cv_folds"], "calibration_folds": meta["calibration_folds"],
            "oof_rows": len(pred), "projection_count": len(audits),
            "base_macro_f1": float(frontier.set_index("policy").loc["base", "macro_f1_oof"]),
            "ngram_rank_by_fold": [fold["ranked_blocks"].index("rgb_ngram_svd") + 1
                                   for fold in folds["fold_artifacts"]]
                                  if len(meta["library"]) == 22 else [],
            "rank_cache_hit_by_fold": [fold["ranking_cache"]["cache_hit"] for fold in folds["fold_artifacts"]],
            "prediction_path": str(pred_path.relative_to(REPO)),
        }
        for file in path.iterdir():
            if file.is_file():
                inputs[str(file.relative_to(REPO))] = sha256_file(file)

    auto = pd.read_csv(REPO / runs["auto22"]["prediction_path"])
    matched = pd.read_csv(REPO / runs["matched21"]["prediction_path"])
    assert np.array_equal(auto["row_index"], matched["row_index"])
    assert np.array_equal(auto["cv_fold"], matched["cv_fold"])
    assert np.array_equal(auto["base"], matched["base"])
    assert all(np.array_equal(auto[f"static_top{k}"], matched[f"static_top{k}"]) for k in (3, 4, 5))
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(policy_checks).to_csv(OUT / "policy_checks.csv", index=False)
    pd.DataFrame(projection_checks).to_csv(OUT / "projection_checks.csv", index=False)
    summary = {"status": "ANALYZED", "runs": runs, "policy_rows_checked": len(policy_checks),
               "projection_count_checked": len(projection_checks),
               "max_macro_f1_error": max(row["macro_f1_error"] for row in policy_checks),
               "max_cost_error_ms": max(row["per_image_cost_error_ms"] for row in policy_checks),
               "input_sha256": inputs,
               "scope": "development smokes on outer-training data; no external metrics, statistical superiority or physical latency inference"}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: value for key, value in summary.items() if key != "input_sha256"}, indent=2))


if __name__ == "__main__":
    main()
