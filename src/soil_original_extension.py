#!/usr/bin/env python3
"""Integrity gate for the leakage-aware Soil Original extension."""

from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter
from pathlib import Path

import numpy as np


REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "results/confirmatory/recovery/soil/Soil_Original_manifest.csv"
EMBEDDINGS = REPO / "embeddings_extensions/SoilOriginal"
RESULTS = REPO / "results/extensions/soil_original"


def load_shared():
    path = REPO / "src/vistex_reference12_extension.py"
    spec = importlib.util.spec_from_file_location("extension_shared", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    shared = load_shared()
    rows, classes, labels = shared.load_manifest(MANIFEST)
    paths = [(REPO / row["source_path"]).resolve() for row in rows]
    counts = Counter(row["label"] for row in rows)
    hashes = [row["source_sha256"] for row in rows]
    groups = [row["group"] for row in rows]
    manifest_checks = {
        "rows_1140_after_exact_dedup": len(rows) == 1140,
        "classes_7": len(classes) == 7,
        "all_sources_exist": all(path.is_file() for path in paths),
        "source_hashes_match": all(shared.file_sha256(path) == row["source_sha256"]
                                    for path, row in zip(paths, rows)),
        "unique_paths": len(set(paths)) == len(paths),
        "unique_exact_hashes": len(set(hashes)) == len(hashes),
        "dependency_groups_present": all(groups) and len(set(groups)) == 962,
        "no_group_crosses_labels": all(
            len({row["label"] for row in rows if row["group"] == group}) == 1
            for group in set(groups)
        ),
        "split_marker": {row["official_split"] for row in rows} == {"NONE_DEFINED_BY_ARCHIVE"},
    }
    embedding_result = shared.validate_embeddings(EMBEDDINGS, labels, classes)
    status = "PASS_REEXTRACTED_GROUP_AWARE" if (
        all(manifest_checks.values()) and embedding_result["status"].startswith("PASS")
    ) else "BLOCKED_DATA_LEAKAGE_RISK"
    report = {
        "dataset": "SoilOriginal", "status": status,
        "manifest": {"status": "PASS" if all(manifest_checks.values()) else "FAIL",
                     "checks": manifest_checks, "rows": len(rows), "classes": len(classes),
                     "groups": len(set(groups)), "counts": dict(sorted(counts.items()))},
        "embeddings": embedding_result,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "data_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    with (RESULTS / "data_audit.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["dataset", "status", "samples", "classes", "extractors"])
        writer.writeheader()
        writer.writerow({"dataset": "SoilOriginal", "status": status, "samples": len(rows),
                         "classes": len(classes), "extractors": 20})
    target_dir = RESULTS / "sample_manifests"
    target_dir.mkdir(exist_ok=True)
    (target_dir / "SoilOriginal.csv").write_bytes(MANIFEST.read_bytes())
    print(json.dumps({"dataset": "SoilOriginal", "status": status,
                      "samples": len(rows), "groups": len(set(groups)), "extractors": 20}, indent=2))
    if not status.startswith("PASS"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
