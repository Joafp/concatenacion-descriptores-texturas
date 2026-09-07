#!/usr/bin/env python3
"""Orquestador/dry-run del plan confirmatorio congelado."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


DATASETS = ("DTD", "FMD", "Outex13", "CUReT", "Soil", "VisTex")
CLASSIFIERS = ("svm", "resmlp")
SEEDS = (42, 123, 2026)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="run eligible conditions; default is dry-run")
    parser.add_argument("--smoke", action="store_true", help="only seed 42/fold 0 with reduced search")
    parser.add_argument("--n-jobs", type=int, default=2, help="bounded SVM candidate parallelism")
    parser.add_argument("--datasets", nargs="+", choices=DATASETS, default=list(DATASETS),
                        help="datasets to schedule (default: all)")
    parser.add_argument("--classifiers", nargs="+", choices=CLASSIFIERS, default=list(CLASSIFIERS),
                        help="classifiers to schedule (default: all)")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if args.n_jobs < 1:
        parser.error("--n-jobs must be >= 1")
    repo = args.repo.resolve(); out = repo / "results" / "confirmatory"
    out.mkdir(parents=True, exist_ok=True); (out / "logs").mkdir(exist_ok=True)
    audit_path = out / "data_audit.csv"
    if not audit_path.exists():
        subprocess.run([sys.executable, str(repo / "src/confirmatory_data_audit.py")], cwd=repo, check=True)
    with audit_path.open(newline="") as handle:
        audit = {r["dataset"]: r for r in csv.DictReader(handle)}
    conditions = []
    seeds = SEEDS[:1] if args.smoke else SEEDS
    folds = range(1) if args.smoke else range(5)
    for dataset in args.datasets:
        eligible = audit[dataset]["status"].startswith("PASS")
        for classifier in args.classifiers:
            if dataset == "DTD":
                official_splits = range(1, 2) if args.smoke else range(1, 11)
                for official_split in official_splits:
                    mode = "smoke" if args.smoke else "full"
                    checkpoint_root = out / "smoke" if args.smoke else out
                    checkpoint = checkpoint_root / "checkpoints" / f"{dataset}__{classifier}__42__official{official_split}__{mode}.json"
                    item = {"dataset": dataset, "classifier": classifier, "seed": 42,
                            "fold": None, "official_split": official_split,
                            "run_mode": mode,
                            "status": "complete" if checkpoint.exists() else ("pending" if eligible else "BLOCKED_DATA_LEAKAGE_RISK")}
                    conditions.append(item)
                    if args.execute and eligible and not checkpoint.exists():
                        command = [sys.executable, str(repo / "src/run_confirmatory_nested.py"),
                                   "--dataset", dataset, "--classifier", classifier,
                                   "--seed", "42", "--fold", "0", "--official-split", str(official_split),
                                   "--n-jobs", str(args.n_jobs)]
                        if args.smoke:
                            command.append("--smoke")
                        completed = subprocess.run(command, cwd=repo)
                        item["status"] = "complete" if completed.returncode == 0 else "failed"
                        if completed.returncode != 0:
                            break
                continue
            if dataset == "CUReT":
                directions = ("a_to_b",) if args.smoke else ("a_to_b", "b_to_a")
                for fold, curet_direction in enumerate(directions):
                    mode = "smoke" if args.smoke else "full"
                    checkpoint_root = out / "smoke" if args.smoke else out
                    checkpoint = checkpoint_root / "checkpoints" / f"{dataset}__{classifier}__42__{curet_direction}__{mode}.json"
                    item = {"dataset": dataset, "classifier": classifier, "seed": 42,
                            "fold": fold, "official_split": None,
                            "curet_direction": curet_direction, "run_mode": mode,
                            "status": "complete" if checkpoint.exists() else ("pending" if eligible else "BLOCKED_DATA_LEAKAGE_RISK")}
                    conditions.append(item)
                    if args.execute and eligible and not checkpoint.exists():
                        command = [sys.executable, str(repo / "src/run_confirmatory_nested.py"),
                                   "--dataset", dataset, "--classifier", classifier,
                                   "--seed", "42", "--fold", str(fold),
                                   "--curet-direction", curet_direction,
                                   "--n-jobs", str(args.n_jobs)]
                        if args.smoke:
                            command.append("--smoke")
                        completed = subprocess.run(command, cwd=repo)
                        item["status"] = "complete" if completed.returncode == 0 else "failed"
                        if completed.returncode != 0:
                            break
                continue
            for seed in seeds:
                for fold in folds:
                    mode = "smoke" if args.smoke else "full"
                    checkpoint_root = out / "smoke" if args.smoke else out
                    checkpoint = checkpoint_root / "checkpoints" / f"{dataset}__{classifier}__{seed}__fold{fold}__{mode}.json"
                    item = {"dataset": dataset, "classifier": classifier, "seed": seed, "fold": fold,
                            "run_mode": mode,
                            "status": "complete" if checkpoint.exists() else ("pending" if eligible else "BLOCKED_DATA_LEAKAGE_RISK")}
                    conditions.append(item)
                    if args.execute and eligible and not checkpoint.exists():
                        command = [sys.executable, str(repo / "src/run_confirmatory_nested.py"),
                                   "--dataset", dataset, "--classifier", classifier,
                                   "--seed", str(seed), "--fold", str(fold), "--n-jobs", str(args.n_jobs)]
                        if args.smoke:
                            command.append("--smoke")
                        completed = subprocess.run(command, cwd=repo)
                        item["status"] = "complete" if completed.returncode == 0 else "failed"
                        if completed.returncode != 0:
                            break
    manifest = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "execute" if args.execute else "dry-run",
        "smoke": args.smoke,
        "n_jobs": args.n_jobs,
        "selected_datasets": args.datasets,
        "selected_classifiers": args.classifiers,
        "frozen": {"datasets": DATASETS, "classifiers": CLASSIFIERS, "seeds": SEEDS,
                   "outer_folds": 5, "inner_folds": 4, "max_k": 8, "random_subsets": 100},
        "official_protocols": {"DTD": "10 supplied train/val/test splits; train+val inner selection; test once"},
        "project_protocols": {
            "CUReT": "deterministic complementary reproduction; not an official historical split"
        },
        "conditions": conditions,
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2))
    counts = {}
    for item in conditions:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    print(json.dumps(counts, indent=2))
    if counts.get("failed", 0):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
