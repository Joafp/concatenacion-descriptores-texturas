#!/usr/bin/env python3
"""Isolated extraction and audit support for the KTH-TIPS2-b extension.

Official 4-fold protocol (Caputo, Hayman and Mallikarjuna, ICCV 2005): train on
the images of ONE physical sample (a, b, c or d), test on the images of the
OTHER THREE samples, rotating over the four samples. The manifest built by
``results/confirmatory/recovery/kth_tips2b/build_kth_tips2b_manifest.py``
stores this as columns ``split_1``..``split_4`` (one column per choice of
training sample), consumed directly by ``src/run_confirmatory_nested.py``'s
``--official-split`` mechanism -- no invented stratified folds are used here.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from collections import Counter
from pathlib import Path

import torch


REPO = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO / "results/confirmatory/recovery/kth_tips2b/KTH-TIPS2-b_manifest.csv"
DEFAULT_EMBEDDINGS = REPO / "embeddings_extensions/KTHTIPS2b"
DEFAULT_RESULTS = REPO / "results/extensions/kth_tips2b"


def load_shared():
    path = REPO / "src/vistex_reference12_extension.py"
    spec = importlib.util.spec_from_file_location("extension_shared", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_manifest(shared, path: Path) -> dict:
    rows, classes, labels = shared.load_manifest(path)
    checks = {
        "rows_4752": len(rows) == 4752,
        "classes_11": len(classes) == 11,
        "108_images_per_class": all(
            count == 108
            for count in Counter((row["label"], row["sample"]) for row in rows).values()
        ),
        "unique_groups": len({row["group"] for row in rows}) == len(rows),
        "has_four_official_splits": all(f"split_{n}" in rows[0] for n in range(1, 5)),
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "rows": len(rows), "classes": len(classes)}


def write_audit(shared, manifest: Path, embeddings: Path, results: Path) -> dict:
    results.mkdir(parents=True, exist_ok=True)
    manifest_result = validate_manifest(shared, manifest)
    _, classes, labels = shared.load_manifest(manifest)
    embedding_result = shared.validate_embeddings(embeddings, labels, classes)
    status = embedding_result["status"] if manifest_result["status"] == "PASS" else "BLOCKED_DATA_LEAKAGE_RISK"
    report = {"dataset": "KTHTIPS2b", "status": status,
              "manifest": manifest_result, "embeddings": embedding_result}
    (results / "data_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    with (results / "data_audit.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["dataset", "status", "samples", "classes", "extractors"])
        writer.writeheader()
        writer.writerow({"dataset": "KTHTIPS2b", "status": status, "samples": len(labels),
                         "classes": len(classes), "extractors": sum(
                             item["status"] == "PASS" for item in embedding_result["extractors"].values())})
    manifest_dir = results / "sample_manifests"
    manifest_dir.mkdir(exist_ok=True)
    target = manifest_dir / "KTHTIPS2b.csv"
    target.write_bytes(manifest.read_bytes())
    print(json.dumps({"dataset": "KTHTIPS2b", "status": status}, indent=2))
    return report


def main() -> None:
    shared = load_shared()
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract = subparsers.add_parser("extract")
    extract.add_argument("--extractor", required=True, choices=(*shared.CANONICAL_EXTRACTORS, "all"))
    extract.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    extract.add_argument("--output", type=Path, default=DEFAULT_EMBEDDINGS)
    extract.add_argument("--device", choices=("cuda", "cpu"), default="cuda" if torch.cuda.is_available() else "cpu")
    extract.add_argument("--batch-size", type=int, default=16)
    extract.add_argument("--skip-existing", action="store_true")

    audit = subparsers.add_parser("audit")
    audit.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    audit.add_argument("--embeddings", type=Path, default=DEFAULT_EMBEDDINGS)
    audit.add_argument("--results", type=Path, default=DEFAULT_RESULTS)

    args = parser.parse_args()
    if args.command == "extract":
        extractors = shared.CANONICAL_EXTRACTORS if args.extractor == "all" else (args.extractor,)
        for extractor in extractors:
            shared.extract_one(extractor, args.manifest.resolve(), args.output.resolve(), args.device,
                               args.batch_size, args.skip_existing)
    else:
        report = write_audit(shared, args.manifest.resolve(), args.embeddings.resolve(), args.results.resolve())
        if not report["status"].startswith("PASS"):
            raise SystemExit(2)


if __name__ == "__main__":
    main()
