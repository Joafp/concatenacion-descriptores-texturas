"""Consolidate both audited CUReT directions without inference or head fits."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from batch1_call_audit import summarize_calls

POLICIES = {"Completa-22", "Top-4", "Ens-diversidad", "Ens-tombola", "Adaptive-selection-margin"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def merge_jobs(jobs, replacements):
    result = []
    for job in jobs:
        new = replacements.get(job["id"], job)
        for field in ("config", "config_sha256", "dataset", "classifier", "seed", "outer_fold"):
            if new[field] != job[field]:
                raise ValueError("continuation scientific condition mismatch")
        result.append(new)
    return result


def combine(frames, metrics, truth, expected_rows=5612):
    if len(frames) != 2 or len(metrics) != 2:
        raise ValueError("two complete directions required")
    calls = pd.concat(frames, ignore_index=True)
    if calls.duplicated(["policy", "repeat", "row_index"]).any():
        raise ValueError("directions repeat external rows")
    if set(calls.row_index) != set(range(expected_rows)):
        raise ValueError("incomplete full-manifest coverage")
    if set(calls["repeat"]) != {0}:
        raise ValueError("expected one timed repetition per image")
    result = summarize_calls(calls, POLICIES, list(range(expected_rows)), truth, sorted(set(truth.values())), 1)
    result = result.rename(columns={"macro_f1_online": "pooled_macro_f1_online"})
    folds = pd.concat(metrics, ignore_index=True)
    result["mean_direction_macro_f1_online"] = result.policy.map(folds.groupby("policy").macro_f1_online.mean())
    result["conditions"] = 2
    return calls, folds, result


def run(args):
    manifest_path = args.folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    jobs = sorted([j for j in manifest["jobs"] if j["dataset"] == "CUReT" and j["classifier"] == args.classifier],
                  key=lambda j: j["outer_fold"])
    overrides = getattr(args, "override_manifest", None)
    if overrides:
        jobs = merge_jobs(jobs, {j["id"]: j for j in json.loads(overrides.read_text())["jobs"]})
    if [j["outer_fold"] for j in jobs] != [0, 1]:
        raise ValueError("expected two unique canonical directions")
    frames, metrics, truth, sources = [], [], {}, {}
    for job in jobs:
        folder, quality = Path(job["online_run"]), Path(job["quality_run"])
        status_path, audit_path = folder / "status.json", Path(job["online_audit"]) / "audit.json"
        status, audit = json.loads(status_path.read_text()), json.loads(audit_path.read_text())
        if (status["status"], status["dataset"], status["classifier"], status["seed"], status["outer_fold"]) != (
                "batch1_online_f1_and_timing_complete", "CUReT", args.classifier, 42, job["outer_fold"]):
            raise ValueError("online condition incomplete or mismatched")
        if audit["status"] != "ONLINE_CALL_RECORDS_REAGGREGATED" or audit["source_status_sha256"] != digest(status_path):
            raise ValueError("missing or stale call audit")
        if digest(quality / "status.json") != status["quality_status_sha256"]:
            raise ValueError("quality status drift")
        q = json.loads((quality / "status.json").read_text())
        for parent, hashes in ((folder, status["output_sha256"]), (quality, q["output_sha256"])):
            for name, sha in hashes.items():
                path = parent / name
                if digest(path) != sha:
                    raise ValueError("output drift")
                sources[str(path)] = sha
        archived = pd.read_csv(quality / "predictions.csv")
        if archived.groupby("row_index").label.nunique().max() != 1:
            raise ValueError("conflicting ground truth")
        labels = archived.drop_duplicates("row_index").set_index("row_index").label.to_dict()
        if set(truth).intersection(labels) or set(labels) != set(status["rows"]) or len(labels) != 2806:
            raise ValueError("wrong canonical external coverage")
        truth.update(labels)
        calls = pd.read_csv(folder / "online_calls.csv")
        recomputed = summarize_calls(calls, POLICIES, status["rows"], labels, sorted(set(labels.values())), 1)
        recorded = pd.read_csv(folder / "online_summary.csv").set_index("policy")
        for row in recomputed.to_dict("records"):
            for key, value in row.items():
                if key != "policy" and not np.isclose(value, recorded.loc[row["policy"], key], atol=1e-10, rtol=0):
                    raise ValueError("summary arithmetic mismatch")
        frames.append(calls.assign(outer_fold=job["outer_fold"]))
        metrics.append(recomputed.assign(outer_fold=job["outer_fold"]))
        for path in (status_path, audit_path, quality / "status.json"):
            sources[str(path)] = digest(path)
    calls, folds, result = combine(frames, metrics, truth)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, frame in (("online_calls.csv", calls), ("direction_metrics.csv", folds), ("dataset_summary.csv", result)):
        frame.to_csv(args.output / name, index=False)
    report = {"status": "TWO_CURET_ONLINE_DIRECTIONS_CONSOLIDATED", "classifier": args.classifier,
        "dataset": "CUReT", "conditions": 2, "call_rows": len(calls), "unique_images": 5612,
        "quality_and_time_from_same_calls": True, "isolated_hardware_benchmark": False,
        "source_sha256": digest(__file__), "manifest_sha256": digest(manifest_path),
        "override_manifest_sha256": digest(overrides) if overrides else None,
        "input_sha256": sources, "methods": result.to_dict("records"),
        "output_sha256": {n: digest(args.output / n) for n in ("online_calls.csv", "direction_metrics.csv", "dataset_summary.csv")}}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(result.to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--classifier", choices=("svm", "resmlp"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--override-manifest", type=Path)
    run(parser.parse_args())
