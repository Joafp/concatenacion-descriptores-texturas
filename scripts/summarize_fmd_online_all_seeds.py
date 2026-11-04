"""Combine three complete FMD seed summaries; never fill missing conditions."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def aggregate(calls, folds):
    if set(calls.seed) != {42, 123, 2026} or set(folds.seed) != {42, 123, 2026}:
        raise ValueError("all three seeds required")
    if calls.duplicated(["seed", "repeat", "policy", "row_index"]).any():
        raise ValueError("duplicate calls within seed")
    if folds.duplicated(["seed", "policy", "outer_fold"]).any():
        raise ValueError("duplicate fold metrics")
    results = []
    for policy, group in calls.groupby("policy"):
        metrics = folds[folds.policy == policy]
        if len(metrics) != 15 or any(set(g.outer_fold) != set(range(5)) for _, g in metrics.groupby("seed")):
            raise ValueError("fifteen complete conditions per method required")
        if any(set(g.row_index) != set(range(1000)) for _, g in group.groupby("seed")):
            raise ValueError("incomplete image coverage")
        results.append({"policy": policy, "conditions": 15,
            "mean_fold_macro_f1_online": float(metrics.macro_f1_online.mean()),
            "mean_ms": float(group.ms.mean()), "median_ms": float(group.ms.median()),
            "p95_ms": float(group.ms.quantile(.95)), "timed_calls": len(group)})
    if len(results) != 5 or len(folds) != 75:
        raise ValueError("five methods required")
    return pd.DataFrame(results)


def run(args):
    frames, metrics, sources = [], [], {}
    for seed in (42, 123, 2026):
        folder = args.folder / f"summary_FMD_{args.classifier}_s{seed}_online_v1"
        path = folder / "summary.json"
        report = json.loads(path.read_text())
        if (report["status"], report["dataset"], report["classifier"], report["seed"], report["conditions"]) != (
                "FIVE_FMD_ONLINE_FOLDS_CONSOLIDATED", "FMD", args.classifier, seed, 5):
            raise ValueError("seed summary incomplete or mismatched")
        for name, sha in report["output_sha256"].items():
            if digest(folder / name) != sha:
                raise ValueError("seed output drift")
        for source, sha in report["input_sha256"].items():
            if digest(source) != sha:
                raise ValueError("original condition evidence drift")
        sources[str(path)] = digest(path)
        frames.append(pd.read_csv(folder / "online_calls.csv").assign(seed=seed))
        metrics.append(pd.read_csv(folder / "fold_summary.csv").assign(seed=seed))
    calls, folds = pd.concat(frames, ignore_index=True), pd.concat(metrics, ignore_index=True)
    summary = aggregate(calls, folds)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, frame in (("online_calls.csv", calls), ("fold_summary.csv", folds), ("dataset_summary.csv", summary)):
        frame.to_csv(args.output / name, index=False)
    report = {"status": "FMD_ALL_THREE_SEEDS_ONLINE_CONSOLIDATED", "classifier": args.classifier,
        "dataset": "FMD", "conditions": 15, "methods": summary.to_dict("records"),
        "unique_images": int(calls.row_index.nunique()), "call_rows": len(calls),
        "quality_and_time_from_same_calls": True, "isolated_hardware_benchmark": False,
        "source_sha256": digest(__file__), "seed_summary_sha256": sources,
        "scope": "complete FMD/classifier only; repeated images across seeds are not independent datasets",
        "output_sha256": {n: digest(args.output / n) for n in ("online_calls.csv", "fold_summary.csv", "dataset_summary.csv")}}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--classifier", choices=("svm", "resmlp"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
