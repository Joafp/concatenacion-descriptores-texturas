#!/usr/bin/env python3
"""Run the frozen exploratory robustness suite for complementary budget fusion.

This suite deliberately keeps every condition in an exploratory output tree:
the zero-gain threshold was chosen after inspecting development results, so this
run is not a preregistered confirmatory experiment.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_complementary_budget_pilot.py"
DEFAULT_OUTPUT = ROOT / "results/exploratory/complementary_budget_frozen_v2"


def conditions() -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for split in range(1, 11):
        result.append({"dataset": "DTD", "official_split": split})
    for fold in range(5):
        result.append({"dataset": "FMD", "fold": fold})
    for direction in ("a_to_b", "b_to_a"):
        result.append({"dataset": "CUReT", "curet_direction": direction})
    result.append({"dataset": "Outex13Official1360", "official_split": 1})
    for fold in range(5):
        result.append({"dataset": "SoilOriginal", "fold": fold})
    result.append({
        "dataset": "KTHTIPS2b",
        "official_split": 1,
        "invert_official_split": True,
        "inner_group_column": "sample",
    })
    return result


def condition_key(condition: dict[str, object]) -> str:
    dataset = str(condition["dataset"])
    if "curet_direction" in condition:
        protocol = f"curet_half_indices:{condition['curet_direction']}"
    elif "official_split" in condition:
        suffix = "_inverted" if condition.get("invert_official_split") else ""
        protocol = f"official{condition['official_split']}{suffix}"
    else:
        protocol = f"fold{condition['fold']}"
    return f"{dataset}_{protocol}_svm_s42_b128"


def command_for(condition: dict[str, object], output: Path) -> list[str]:
    command = [
        sys.executable, str(RUNNER),
        "--dataset", str(condition["dataset"]),
        "--classifier", "svm",
        "--seed", "42",
        "--inner-folds", "3",
        "--dimension-budget", "128",
        "--rank-choices", "8", "16", "32",
        "--min-inner-gain", "0",
        "--output", str(output),
    ]
    for option in ("fold", "official_split", "curet_direction",
                   "inner_group_column"):
        if option in condition:
            command.extend((f"--{option.replace('_', '-')}", str(condition[option])))
    if condition.get("invert_official_split"):
        command.append("--invert-official-split")
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--resume", action="store_true",
                        help="continue a prior suite without overwriting completed conditions")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    status_path = output / "suite_status.json"
    plan = conditions()
    frozen = {
        "status": "EXPLORATORY_ROBUSTNESS_AUDIT_NOT_CONFIRMATORY",
        "protocol_version": 2,
        "reason": "min_inner_gain=0 was selected after inspecting development external results",
        "rank_feasibility": "requested ranks checked separately for each descriptor and inner fold",
        "seed": 42,
        "classifier": "linear SVM, C=1, balanced classes",
        "inner_folds": 3,
        "dimension_budget": 128,
        "rank_choices": [8, 16, 32],
        "min_inner_gain": 0,
        "conditions": plan,
        "runner": str(RUNNER),
        "started_at_unix": time.time(),
    }
    if status_path.exists() and not args.resume:
        parser.error(f"{status_path} exists; pass --resume to continue without overwriting")
    if not status_path.exists():
        status_path.write_text(json.dumps(frozen, indent=2) + "\n", encoding="utf-8")
    else:
        saved = json.loads(status_path.read_text(encoding="utf-8"))
        if (saved.get("conditions") != plan or saved.get("dimension_budget") != 128
                or saved.get("protocol_version") != 2):
            parser.error("existing suite metadata does not match the frozen plan")

    for index, condition in enumerate(plan, start=1):
        key = condition_key(condition)
        result_path = output / f"{key}.json"
        if result_path.exists():
            print(f"[{index}/{len(plan)}] already complete: {key}", flush=True)
            continue
        command = command_for(condition, output)
        print(f"[{index}/{len(plan)}] start: {key}", flush=True)
        environment = os.environ.copy()
        environment.setdefault("PYTHONUNBUFFERED", "1")
        started = time.perf_counter()
        completed = subprocess.run(command, cwd=ROOT, env=environment, check=False)
        elapsed = time.perf_counter() - started
        if completed.returncode != 0 or not result_path.exists():
            print(f"[{index}/{len(plan)}] FAILED: {key}; exit={completed.returncode}",
                  flush=True)
            return completed.returncode or 1
        row = json.loads(result_path.read_text(encoding="utf-8"))
        print(json.dumps({
            "suite_progress": f"{index}/{len(plan)}",
            "key": key,
            "outer_macro_f1": row["outer_macro_f1"],
            "dimensions_used": row["dimensions_used"],
            "elapsed_seconds": elapsed,
        }, ensure_ascii=False), flush=True)
    print(f"SUITE_COMPLETE conditions={len(plan)} output={output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
