#!/usr/bin/env python3
"""Remove N-grams from fitted rescue members while freezing the selected route.

This conditional ablation retains the 22-block policy's base and threshold.
Policies with an N-gram base are explicitly ineligible rather than imputed.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score

from run_confirmatory_nested import load_dataset, load_manifest
from run_rescue_nested_selection import REPO, COMMON_21, fit_scores, sha256_file, launch_provenance
from fsc_tex.utility import compute_margins
from fsc_tex.cost_model import DEFAULT_HARDWARE_LATENCY_MS as LATENCIES, DEFAULT_POLICY_OVERHEAD_MS as OVERHEAD


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    def resolve(path):
        if path is None:
            return None
        path = Path(path)
        return (REPO / path).resolve() if not path.is_absolute() else path
    ref, output = resolve(args.reference_run), resolve(args.output)
    if output.exists() and any(output.iterdir()):
        parser.error("choose an empty output directory")
    original = json.loads((ref / "metadata.json").read_text())
    assert original["status"] == "complete" and len(original["library"]) == 22
    for source, digest in original["provenance"]["source_sha256"].items():
        assert sha256_file(REPO / source) == digest, f"source drift: {source}"
    cfg = original["provenance"]["arguments"]
    cache, y = load_dataset(REPO, original["dataset"], resolve(cfg["embedding_root"]))
    cache = {name: cache[name] for name in COMMON_21}
    root = resolve(cfg["manifest_root"])
    groups, rows = load_manifest(root, original["dataset"], y)
    provenance = launch_provenance(args, root / "sample_manifests" / f"{original['dataset']}.csv",
                                   cache, y, {"per_descriptor_latency_ms": LATENCIES, "policy_overhead_ms": OVERHEAD})
    for key in ("manifest_sha256", "labels_sha256", "embedding_array_sha256"):
        assert provenance[key] == original["provenance"][key]
    provenance["source_sha256"][str(Path(__file__).relative_to(REPO))] = sha256_file(Path(__file__))
    selections = json.loads((ref / "selections.json").read_text())
    reference_pred = pd.read_csv(ref / "predictions.csv")
    labels, output_rows, records, score_arrays = np.unique(y), [], [], {}
    for fold_path in sorted(ref.glob("fold*.json")):
        fold = json.loads(fold_path.read_text())
        number = fold["producer_fold"]
        fit, val = np.asarray(fold["fit_indices"]), np.asarray(fold["validation_indices"])
        assert not set(groups[fit]).intersection(groups[val])
        fitted = {}
        def evaluate(subset):
            key = tuple(sorted(subset))
            if key not in fitted:
                fitted[key] = fit_scores(cache, list(key), fit, val, y, labels, cfg["seed"])[0]
            return fitted[key]
        for decision in (s for s in selections if s["producer_fold"] == number):
            record = {"producer_fold": number, "policy": decision["policy"], "eligible": False}
            if not decision["feasible"]:
                record["reason"] = "original selection infeasible"
                records.append(record)
                continue
            chosen = decision["selected"]
            if chosen["base"] == "rgb_ngram_svd":
                record["reason"] = "cannot preserve a removed base"
                records.append(record)
                continue
            members = [[name for name in subset if name != "rgb_ngram_svd"] for subset in chosen["members"]]
            if any(not member for member in members):
                record["reason"] = "empty rescue after removing color"
                records.append(record)
                continue
            base = chosen["base"]
            base_scores = evaluate([base])
            margin = compute_margins(base_scores)
            base_pred = labels[np.argmax(base_scores, axis=1)]
            gate = margin < chosen["threshold"] if members else np.zeros(len(val), dtype=bool)
            selected_reference = reference_pred[(reference_pred.producer_fold == number)
                                                & (reference_pred.policy == decision["policy"])].set_index("row_index").loc[val]
            assert np.allclose(margin, selected_reference.base_margin, atol=1e-10, rtol=1e-10)
            assert np.array_equal(gate, selected_reference.escalated.to_numpy(dtype=bool))
            rescue = (labels[np.argmax(np.mean([evaluate(member) for member in members], axis=0), axis=1)]
                      if members else base_pred)
            prediction = np.where(gate, rescue, base_pred)
            union = {name for subset in members for name in subset}
            cost = (LATENCIES[base] + OVERHEAD + gate * sum(LATENCIES[n] for n in union - {base})
                    if members else np.full(len(val), LATENCIES[base]))
            for pos, row_index in enumerate(val):
                output_rows.append({"row_index": int(row_index), "label": int(y[row_index]),
                    "producer_fold": number, "policy": decision["policy"],
                    "prediction": int(prediction[pos]), "base_prediction": int(base_pred[pos]),
                    "rescue_prediction": int(rescue[pos]), "base_margin": float(margin[pos]),
                    "escalated": bool(gate[pos]), "projected_ms": float(cost[pos])})
            record.update(eligible=True, base=base, threshold=chosen["threshold"],
                          original_members=chosen["members"], ablated_members=members,
                          rows_with_changed_prediction=int(np.sum(prediction != selected_reference.prediction)),
                          color_present_in_original=any("rgb_ngram_svd" in m for m in chosen["members"]))
            records.append(record)
        order = sorted(fitted)
        score_arrays[f"fold{number}_rows"] = val
        score_arrays[f"fold{number}_scores"] = (np.stack([fitted[s] for s in order])
            if order else np.empty((0, len(val), len(labels)), dtype=float))
        score_arrays[f"fold{number}_subset_json"] = np.asarray([json.dumps(list(s)) for s in order])
        print(f"completed frozen-route color ablation fold {number}", flush=True)
    pred = pd.DataFrame(output_rows, columns=["row_index", "label", "producer_fold", "policy",
        "prediction", "base_prediction", "rescue_prediction", "base_margin", "escalated", "projected_ms"])
    results = []
    for policy in sorted({s["policy"] for s in selections}):
        group = pred[pred.policy == policy]
        complete = len(group) == len(reference_pred[reference_pred.policy == "best_individual"]) and group.row_index.is_unique
        results.append({"policy": policy, "complete_oof_coverage": complete, "n_rows": len(group),
                        "macro_f1_oof": f1_score(group.label, group.prediction, average="macro", zero_division=0) if complete else None,
                        "accuracy_oof": accuracy_score(group.label, group.prediction) if complete else None,
                        "projected_ms": group.projected_ms.mean() if complete else None})
    output.mkdir(parents=True, exist_ok=True)
    pred.to_csv(output / "predictions.csv", index=False)
    pd.DataFrame(results).to_csv(output / "results.csv", index=False)
    (output / "decisions.json").write_text(json.dumps(records, indent=2) + "\n")
    np.savez_compressed(output / "validation_scores.npz", **score_arrays)
    (output / "metadata.json").write_text(json.dumps({"status": "complete", "provenance": provenance,
        "dataset": original["dataset"], "reference_run": str(ref),
        "reference_metadata_sha256": sha256_file(ref / "metadata.json"),
        "scope": "conditional frozen-route color removal, no reselection or external evaluation"}, indent=2) + "\n")
    print(pd.DataFrame(results).to_string(index=False))


if __name__ == "__main__":
    main()
