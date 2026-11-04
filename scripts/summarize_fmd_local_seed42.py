"""Aggregate five audited FMD/42 folds, refusing missing or repeated test rows."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import f1_score


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def summarize(args):
    queue = json.loads((args.followup / "queue_status.json").read_text())
    if queue["status"] != "complete_quality_and_replay" or queue["completed"] != [1, 2, 3, 4]:
        raise ValueError("follow-up queue is incomplete")
    runs = [args.pilot] + [args.followup / f"fold{i}" for i in range(1, 5)]
    audits = [args.pilot_audit] + [args.followup / f"fold{i}_audit" for i in range(1, 5)]
    frames, scores, sources = [], [], {}
    for fold, (folder, audit_folder) in enumerate(zip(runs, audits)):
        status = json.loads((folder / "status.json").read_text())
        if (status["status"], status["dataset"], status["seed"], status["outer_fold"], status["classifier"]) != (
                "external_quality_complete_timing_pending", "FMD", 42, fold, args.classifier):
            raise ValueError("unexpected condition or incomplete run")
        audit = json.loads((audit_folder / "audit.json").read_text())
        if audit["status"] != "CACHED_HEAD_PREDICTIONS_REPLAYED" or audit["source_status_sha256"] != digest(folder / "status.json"):
            raise ValueError("missing or stale head replay")
        for name in ("metrics.csv", "predictions.csv"):
            if digest(folder / name) != status["output_sha256"][name]:
                raise ValueError("output drift")
        frame = pd.read_csv(folder / "predictions.csv")
        if frame.duplicated(["policy", "row_index"]).any():
            raise ValueError("duplicate prediction rows")
        for policy, group in frame.groupby("policy"):
            if len(group) != 200:
                raise ValueError("incomplete fold prediction coverage")
        if set(frame.policy) != {"Completa-22", "Top-4", "Ens-diversidad", "Ens-tombola", "Adaptive-selection-margin"}:
            raise ValueError("wrong method coverage")
        frames.append(frame.assign(outer_fold=fold))
        scores.append(pd.read_csv(folder / "metrics.csv").assign(outer_fold=fold))
        for path in (folder / "status.json", folder / "metrics.csv", folder / "predictions.csv", audit_folder / "audit.json"):
            sources[str(path.resolve())] = digest(path)
    predictions = pd.concat(frames, ignore_index=True)
    metrics = pd.concat(scores, ignore_index=True)
    if predictions.duplicated(["policy", "row_index"]).any():
        raise ValueError("external folds repeat images")
    methods = []
    reference_labels = None
    for policy, group in predictions.groupby("policy"):
        labels = group.set_index("row_index").label.sort_index()
        if len(group) != 1000 or set(labels.index) != set(range(1000)):
            raise ValueError("five folds do not cover all 1000 FMD rows")
        if reference_labels is not None and not labels.equals(reference_labels):
            raise ValueError("methods do not have identical ground truth")
        reference_labels = labels
        m = metrics[metrics.policy == policy]
        methods.append({"classifier": args.classifier, "dataset": "FMD", "seed": 42,
            "method": policy, "conditions": len(m), "external_rows": len(group),
            "mean_fold_macro_f1": float(m.macro_f1.mean()),
            "pooled_macro_f1": float(f1_score(group.label, group.prediction, average="macro", zero_division=0)),
            "mean_escalation_fraction": float(group.escalated.mean()), "measured_ms_per_image": None})
    args.output.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(methods).to_csv(args.output / "seed42_summary.csv", index=False)
    metrics.to_csv(args.output / "fold_metrics.csv", index=False)
    predictions.to_csv(args.output / "predictions.csv", index=False)
    report = {"status": "FIVE_FOLDS_REAGGREGATED_AFTER_HEAD_REPLAY", "classifier": args.classifier,
        "physical_latency_published": False, "all_three_fmd_seeds_complete": False,
        "scope": "one seed, five disjoint external folds; not the final three-seed FMD mean",
        "source_sha256": digest(__file__), "input_sha256": sources, "methods": methods}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(pd.DataFrame(methods).to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=Path, required=True)
    parser.add_argument("--pilot-audit", type=Path, required=True)
    parser.add_argument("--followup", type=Path, required=True)
    parser.add_argument("--classifier", choices=("svm", "resmlp"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    summarize(parser.parse_args())
