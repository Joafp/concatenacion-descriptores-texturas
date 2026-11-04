"""Consolidate one complete audited FMD online seed without new inference."""
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


def combine(frames, fold_summaries, labels, repeats):
    if len(frames) != 5 or len(fold_summaries) != 5:
        raise ValueError("five complete folds required")
    calls = pd.concat(frames, ignore_index=True)
    if calls.duplicated(["repeat", "policy", "row_index"]).any():
        raise ValueError("folds repeat external images")
    if set(calls.row_index) != set(range(1000)):
        raise ValueError("folds must cover exactly 1000 FMD images")
    summary = summarize_calls(calls, POLICIES, list(range(1000)), labels,
                              sorted(set(labels.values())), repeats)
    folds = pd.concat(fold_summaries, ignore_index=True)
    means = folds.groupby("policy").macro_f1_online.mean()
    summary = summary.rename(columns={"macro_f1_online": "pooled_macro_f1_online"})
    summary["mean_fold_macro_f1_online"] = summary.policy.map(means)
    summary["conditions"] = 5
    return calls, folds, summary


def run(args):
    manifest = json.loads(args.manifest.read_text())
    jobs = sorted([j for j in manifest["jobs"] if j["dataset"] == "FMD"
                   and j["classifier"] == args.classifier and j["seed"] == args.seed],
                  key=lambda j: j["outer_fold"])
    if [j["outer_fold"] for j in jobs] != list(range(5)):
        raise ValueError("manifest does not contain five unique folds")
    frames, folds, sources, labels, repeat_counts = [], [], {}, {}, set()
    for job in jobs:
        folder, audit_folder = Path(job["online_run"]), Path(job["online_audit"])
        status_path, audit_path = folder / "status.json", audit_folder / "audit.json"
        status = json.loads(status_path.read_text())
        audit = json.loads(audit_path.read_text())
        if (status["status"], status["dataset"], status["classifier"], status["seed"], status["outer_fold"]) != (
                "batch1_online_f1_and_timing_complete", "FMD", args.classifier, args.seed, job["outer_fold"]):
            raise ValueError("incomplete or mismatched online condition")
        if audit["status"] != "ONLINE_CALL_RECORDS_REAGGREGATED" or audit["source_status_sha256"] != digest(status_path):
            raise ValueError("missing or stale call audit")
        if digest(job["config"]) != job["config_sha256"]:
            raise ValueError("config drift")
        quality = Path(job["quality_run"])
        quality_status_path = quality / "status.json"
        quality_status = json.loads(quality_status_path.read_text())
        if digest(quality_status_path) != status["quality_status_sha256"]:
            raise ValueError("quality status drift")
        for name in ("predictions.csv", "fitted_heads.joblib"):
            path = quality / name
            if digest(path) != quality_status["output_sha256"][name]:
                raise ValueError("quality output drift")
            sources[str(path)] = digest(path)
        for name, expected in status["output_sha256"].items():
            path = folder / name
            if digest(path) != expected:
                raise ValueError("online output drift")
            sources[str(path)] = digest(path)
        truth = pd.read_csv(quality / "predictions.csv")
        if truth.groupby("row_index").label.nunique().max() != 1:
            raise ValueError("conflicting labels across policies")
        truth = truth.drop_duplicates("row_index").set_index("row_index").label.to_dict()
        if set(truth) != set(status["rows"]) or len(truth) != 200:
            raise ValueError("incomplete FMD fold")
        if set(labels).intersection(truth):
            raise ValueError("folds repeat external images")
        labels.update(truth)
        calls = pd.read_csv(folder / "online_calls.csv")
        recomputed = summarize_calls(calls, POLICIES, status["rows"], truth,
                                    sorted(set(truth.values())), status["repeats"])
        recorded = pd.read_csv(folder / "online_summary.csv").set_index("policy")
        for row in recomputed.to_dict("records"):
            for key, value in row.items():
                if key != "policy" and not np.isclose(value, recorded.loc[row["policy"], key], rtol=0, atol=1e-10):
                    raise ValueError("online summary mismatch")
        frames.append(calls.assign(outer_fold=job["outer_fold"]))
        folds.append(recomputed.assign(outer_fold=job["outer_fold"]))
        repeat_counts.add(status["repeats"])
        for path in (status_path, audit_path, quality_status_path, Path(job["config"])):
            sources[str(path)] = digest(path)
    if len(repeat_counts) != 1:
        raise ValueError("inconsistent repeat design")
    calls, folds, summary = combine(frames, folds, labels, repeat_counts.pop())
    args.output.mkdir(parents=True, exist_ok=False)
    for name, frame in (("online_calls.csv", calls), ("fold_summary.csv", folds), ("seed_summary.csv", summary)):
        frame.to_csv(args.output / name, index=False)
    report = {"status": "FIVE_FMD_ONLINE_FOLDS_CONSOLIDATED", "dataset": "FMD",
              "classifier": args.classifier, "seed": args.seed, "conditions": 5,
              "call_rows": len(calls), "unique_images": int(calls.row_index.nunique()),
              "all_three_fmd_seeds_complete": False, "quality_and_time_from_same_calls": True,
              "archive_vector_parity_claimed": False, "isolated_hardware_benchmark": False,
              "scope": "one seed only; arithmetic verification, no new inference or significance test",
              "source_sha256": digest(__file__), "manifest_sha256": digest(args.manifest),
              "input_sha256": sources, "methods": summary.to_dict("records"),
              "output_sha256": {n: digest(args.output / n) for n in ("online_calls.csv", "fold_summary.csv", "seed_summary.csv")}}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--classifier", choices=("svm", "resmlp"), required=True)
    parser.add_argument("--seed", type=int, choices=(42, 123, 2026), required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
