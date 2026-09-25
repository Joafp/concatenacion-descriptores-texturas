#!/usr/bin/env python3
"""Merge completed isolated BEiTv2-22 conditions into canonical result folders."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path


CSV_KEYS = {
    "nested_fold_results.csv": (
        "dataset", "classifier", "seed", "outer_fold", "run_mode", "method"
    ),
    "random_subset_results.csv": (
        "dataset", "classifier", "seed", "outer_fold", "run_mode", "method"
    ),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def merge_csv(destination: Path, sources: list[Path], keys: tuple[str, ...]) -> None:
    rows = read_csv(destination)
    by_key = {tuple(row.get(key, "") for key in keys): row for row in rows}
    fieldnames = list(rows[0]) if rows else []
    for source in sources:
        for row in read_csv(source):
            if not fieldnames:
                fieldnames = list(row)
            by_key[tuple(row.get(key, "") for key in keys)] = row
    if not fieldnames:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(
        by_key.values(),
        key=lambda row: (
            row.get("dataset", ""), row.get("classifier", ""),
            int(row.get("seed", 0)), int(row.get("outer_fold", 0)),
            row.get("method", ""),
        ),
    )
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ordered)
    temporary.replace(destination)


def merge_jsonl(destination: Path, sources: list[Path]) -> None:
    records: dict[tuple, dict] = {}
    for path in [destination, *sources]:
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            key = (
                row.get("dataset"), row.get("classifier"), row.get("seed"),
                row.get("outer_fold"), row.get("run_mode"),
            )
            records[key] = row
    if not records:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with temporary.open("w") as handle:
        for key in sorted(records, key=lambda value: tuple(str(v) for v in value)):
            handle.write(json.dumps(records[key], sort_keys=True) + "\n")
    temporary.replace(destination)


def copy_completed_artifacts(canonical: Path, parts_root: Path) -> None:
    completed = []
    for checkpoint in parts_root.glob("*/checkpoints/*.json"):
        part = checkpoint.parent.parent
        topk_checkpoints = list((part / "topk_individual_control").glob("*.json"))
        if topk_checkpoints:
            completed.append(part)

    for filename, keys in CSV_KEYS.items():
        merge_csv(canonical / filename, [part / filename for part in completed], keys)
    merge_jsonl(canonical / "selected_subsets.jsonl",
                [part / "selected_subsets.jsonl" for part in completed])
    merge_csv(
        canonical / "topk_individual_control" / "nested_fold_results.csv",
        [part / "topk_individual_control" / "nested_fold_results.csv" for part in completed],
        CSV_KEYS["nested_fold_results.csv"],
    )

    for part in completed:
        for relative in ("checkpoints", "logs", "topk_individual_control"):
            source_dir = part / relative
            if not source_dir.is_dir():
                continue
            target_dir = canonical / relative
            target_dir.mkdir(parents=True, exist_ok=True)
            for source in source_dir.glob("*.json"):
                shutil.copy2(source, target_dir / source.name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    canonical = args.root / "ngram22_beitv2"
    parts_root = args.root / "ngram22_beitv2_parts"
    if parts_root.is_dir():
        copy_completed_artifacts(canonical, parts_root)


if __name__ == "__main__":
    main()
