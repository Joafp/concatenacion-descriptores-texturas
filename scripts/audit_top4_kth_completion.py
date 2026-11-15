#!/usr/bin/env python3
"""Replay E1/E2 metrics across 25 preserved and two new conditions; never fit models."""
from __future__ import annotations
import argparse
import gzip
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import numpy as np
import pandas as pd
from run_top4_fixed_e1_e2 import METRICS, metrics, gate_mask, exact_budget_mask, projected_cost
from build_accuracy_primary_thesis_20261115_v3 import exact_signed_rank, holm
from validate_kth_reference_recipe import sha, dump


def audit(folder, output):
    if output.exists():
        raise FileExistsError("new audit folder required")
    state = json.loads((folder / "status.json").read_text())
    if state["status"] != "complete" or len(state["states"]) != 27 or set(state["states"].values()) != {"complete"}:
        raise ValueError("the six-dataset completion is not fully closed")
    frozen = json.loads((folder / "protocol_frozen.json").read_text())
    if sha(folder / "protocol_frozen.json") != state["protocol_sha256"]:
        raise ValueError("completion protocol changed")
    sources = dict(frozen["sources"])
    sources[str((folder / "status.json").relative_to(ROOT))] = sha(folder / "status.json")
    sources[str((folder / "protocol_frozen.json").relative_to(ROOT))] = state["protocol_sha256"]
    for name, expected in sources.items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"frozen source changed: {name}")
    records, e2, bases, references = [], [], [], []
    reference_frames = {}
    for c in frozen["conditions"]:
        case = ROOT / frozen["condition_sources"][c["id"]]
        status = json.loads((case / "status.json").read_text())
        if status["status"] != "complete":
            raise ValueError(f"incomplete condition: {c['id']}")
        sources[str((case / "status.json").relative_to(ROOT))] = sha(case / "status.json")
        for name, expected in status["sha256"].items():
            if sha(case / name) != expected:
                raise ValueError(f"condition artifact changed: {case/name}")
            sources[str((case / name).relative_to(ROOT))] = expected
        result = json.loads((case / "result.json").read_text())
        with gzip.open(case / "scores_predictions.json.gz", "rt") as handle:
            payload = json.load(handle)
        if payload["test_indices"] != c["test_indices"] or result["top4_blocks"] != c["top4_blocks"]:
            raise ValueError("test identity or fixed-four composition changed")
        y, labels = np.asarray(payload["y_true"]), np.asarray(payload["class_order"])
        for name, pred in payload["predictions"].items():
            actual = metrics(y, np.asarray(pred), labels)
            reported = result["metrics"][name] if name in result["metrics"] else result[name]["metrics"]
            if any(abs(actual[m] - reported[m]) > 1e-12 for m in METRICS):
                raise ValueError(f"prediction metric replay failed: {c['id']}/{name}")
        mask = np.asarray(payload["request_masks"]["selected_cascade"], dtype=bool)
        direct = np.asarray(payload["predictions"]["top4_direct"])
        conditional = np.asarray(payload["predictions"]["selected_cascade"])
        chosen = result["selected_cascade"]
        base = chosen["cheap"]
        expected = direct if not base else np.where(mask, direct, payload["predictions"][base])
        if not np.array_equal(conditional, expected):
            raise ValueError("conditional route is not the saved direct/base prediction")
        cost = sum(c["component_costs_ms"][b] for b in c["top4_blocks"])
        conditional_cost = cost if chosen["route"] == "topk_direct" else projected_cost(c, base, mask)
        if abs(cost - result["direct_projected_component_ms"]) > 1e-9 or abs(conditional_cost - chosen["projected_component_ms"]) > 1e-9:
            raise ValueError("component cost replay differs")
        row = {"id": c["id"], "dataset": c["dataset"], "outer_fold": c["outer_fold"],
               "source_folder": str(case.relative_to(ROOT)), "request_fraction": float(mask.mean()),
               "direct_projected_ms": cost, "cascade_projected_ms": conditional_cost,
               "random_accuracy": result["random_selected_route"]["accuracy"]["mean"], "cheap": base}
        for route, values in [("direct", result["metrics"]["top4_direct"]), ("cascade", chosen["metrics"])]:
            row.update({f"{route}_{metric}": values[metric] for metric in METRICS})
        records.append(row)
        for block in c["cheap_candidates"]:
            bases.append({"id": c["id"], "dataset": c["dataset"], "base": block, **result["metrics"][block]})
        for gate_row in json.loads((case / "e2.json").read_text()):
            gate_row = gate_row.copy()
            gate_base, q = gate_row["base"], gate_row["q"]
            oof = np.asarray(payload["oof_scores"][gate_base])
            test = np.asarray(payload["test_scores"][gate_base])
            active, threshold = gate_mask(oof, test, q, gate_row["gate"])
            if gate_row["mode"] == "matched_test_count_diagnostic":
                margin, _ = gate_mask(oof, test, q, "margin")
                active = exact_budget_mask(test, int(margin.sum()), gate_row["gate"])
            prediction = np.where(active, direct, payload["predictions"][gate_base])
            actual = metrics(y, prediction, labels)
            if any(abs(actual[m] - gate_row["metrics"][m]) > 1e-12 for m in METRICS):
                raise ValueError(f"E2 metric replay failed: {c['id']}")
            if abs(float(active.mean()) - gate_row["request_fraction"]) > 1e-12 or threshold != gate_row["threshold_oof"]:
                raise ValueError("E2 coverage/threshold differs")
            gate_row.update(gate_row.pop("metrics"))
            e2.append(gate_row)
        source = c["sweep_source"]
        if source not in reference_frames:
            sources[source] = sha(ROOT / source)
            reference_frames[source] = pd.read_csv(ROOT / source, float_precision="round_trip")
        sweep = reference_frames[source]
        old = sweep[(sweep.dataset == c["dataset"]) & (sweep.classifier == "svm") & (sweep.seed == 42)
                    & (sweep.k == 4) & (sweep.outer_fold == c["outer_fold"])]
        if len(old) != 1:
            raise ValueError("ambiguous direct Top-4 reference")
        old = old.iloc[0]
        references.append({"id": c["id"], "accuracy_delta": row["direct_accuracy"] - float(old.accuracy),
                           "macro_f1_delta": row["direct_macro_f1"] - float(old.macro_f1)})

    frame, gates, comparisons = pd.DataFrame(records), pd.DataFrame(e2), pd.DataFrame(references)
    if len(frame) != 27 or frame.dataset.nunique() != 6 or len(gates) != 27 * 18:
        raise ValueError("coverage is not 27 E1 cases and 486 E2 rows across six datasets")
    if comparisons.accuracy_delta.abs().max() > 1e-12 or comparisons.macro_f1_delta.abs().max() > 1e-12:
        raise ValueError("new direct results differ from saved Top-4 reference")
    means = frame.groupby("dataset").mean(numeric_only=True)
    gate_means = gates.groupby(["dataset", "mode", "q", "gate"])[METRICS + ["request_fraction", "projected_component_ms"]].mean().reset_index()
    statistics = []
    for mode in gate_means["mode"].unique():
        for metric in METRICS:
            family = []
            for q in [.25, .5, .75]:
                matrix = gate_means[(gate_means["mode"] == mode) & (gate_means.q == q)].pivot(index="dataset", columns="gate", values=metric)
                for a, b in itertools.combinations(["margin", "maximum_score", "softmax_entropy"], 2):
                    difference = matrix[a] - matrix[b]
                    family.append({"mode": mode, "metric": metric, "q": q, "a": a, "b": b, "datasets": 6,
                                   "mean_difference": float(difference.mean()), "p_exact": exact_signed_rank(difference.to_numpy())})
            for row, adjusted in zip(family, holm([r["p_exact"] for r in family]), strict=True):
                statistics.append({**row, "p_holm_family9": adjusted})
    summary = {"status": "audited_complete_six_datasets", "primary_metric": "accuracy",
               "completed_conditions": 27, "new_conditions": 2, "reused_conditions": 25,
               "complete_datasets": sorted(frame.dataset.unique()), "e2_rows": len(gates),
               "mean_accuracy_direct": float(means.direct_accuracy.mean()),
               "mean_accuracy_cascade": float(means.cascade_accuracy.mean()),
               "accuracy_difference_pp": float(100 * (means.cascade_accuracy - means.direct_accuracy).mean()),
               "paired_accuracy_p_exact": exact_signed_rank((means.cascade_accuracy - means.direct_accuracy).to_numpy()),
               "mean_direct_projected_ms": float(means.direct_projected_ms.mean()),
               "mean_cascade_projected_ms": float(means.cascade_projected_ms.mean()),
               "projected_reduction_ratio": float(1 - means.cascade_projected_ms.mean() / means.direct_projected_ms.mean()),
               "max_absolute_direct_accuracy_reference_delta": float(comparisons.accuracy_delta.abs().max()),
               "max_absolute_direct_macro_f1_reference_delta": float(comparisons.macro_f1_delta.abs().max()),
               "costs_are_projections_not_online_policy_latency": True,
               "incomplete_dataset_averages_reported": False, "no_new_fits_or_model_predictions_in_audit": True}
    output.mkdir(parents=True, exist_ok=False)
    for name, data in [("e1_conditions.csv", frame), ("e1_complete_dataset_means.csv", means.reset_index()),
                       ("e1_cheap_candidate_test_metrics.csv", pd.DataFrame(bases)), ("e2_conditions.csv", gates),
                       ("e2_complete_dataset_means.csv", gate_means), ("e2_statistics.csv", pd.DataFrame(statistics)),
                       ("direct_reference_comparison.csv", comparisons)]:
        data.to_csv(output / name, index=False)
    dump(output / "summary.json", summary)
    dump(output / "provenance.json", {"sources": sources, "script_sha256": sha(__file__),
                                      "outputs": {f.name: sha(f) for f in output.iterdir() if f.is_file()}})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit(args.folder.resolve(), args.output.resolve())
