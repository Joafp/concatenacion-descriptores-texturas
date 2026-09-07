#!/usr/bin/env python3
"""Isolated extraction and audit support for the VisTex Reference-12 extension."""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import importlib.util
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import torch


REPO = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO / "results/confirmatory/recovery/vistex/VisTex_Reference12_manifest.csv"
DEFAULT_EMBEDDINGS = REPO / "embeddings_extensions/VisTexReference12"
DEFAULT_RESULTS = REPO / "results/extensions/vistex_reference12"
CANONICAL_EXTRACTORS = (
    "lbp", "drlbp", "gabor", "glcm", "hog",
    "vgg16", "resnet50", "resnet101", "densenet121", "efficientnet_b0",
    "convnext_v2_t", "vit_b16", "deit_s", "swin_t", "eva02_base",
    "dinov2_small", "dinov2", "dinov2_large", "mae_base", "siglip_base",
)
SOTA_EXTRACTORS = {"eva02_base", "mae_base", "siglip_base"}


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path = DEFAULT_MANIFEST) -> tuple[list[dict], list[str], np.ndarray]:
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    required = {"row_id", "label", "group", "source_path", "source_sha256", "official_split"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"manifest must contain {sorted(required)}")
    if [int(row["row_id"]) for row in rows] != list(range(len(rows))):
        raise ValueError("manifest row IDs are not canonical")
    classes = sorted({row["label"] for row in rows})
    class_to_index = {label: index for index, label in enumerate(classes)}
    labels = np.asarray([class_to_index[row["label"]] for row in rows], dtype=np.int64)
    return rows, classes, labels


def discover_manifest_images(path: Path = DEFAULT_MANIFEST, repo: Path = REPO):
    rows, classes, labels = load_manifest(path)
    paths = [(repo / row["source_path"]).resolve() for row in rows]
    missing = [str(image) for image in paths if not image.is_file()]
    if missing:
        raise FileNotFoundError(f"manifest source images missing: {missing[:3]}")
    for row, image in zip(rows, paths):
        if file_sha256(image) != row["source_sha256"]:
            raise ValueError(f"manifest source hash mismatch: {image}")
    return [str(image) for image in paths], classes, labels


def validate_manifest(path: Path = DEFAULT_MANIFEST, repo: Path = REPO) -> dict:
    rows, classes, labels = load_manifest(path)
    paths, discovered_classes, discovered_labels = discover_manifest_images(path, repo)
    counts = Counter(row["label"] for row in rows)
    hashes = [row["source_sha256"] for row in rows]
    checks = {
        "rows_140": len(rows) == 140,
        "classes_12": len(classes) == 12,
        "minimum_7": min(counts.values()) >= 7,
        "canonical_labels": classes == discovered_classes and np.array_equal(labels, discovered_labels),
        "unique_paths": len(set(paths)) == len(paths),
        "unique_groups": len({row["group"] for row in rows}) == len(rows),
        "unique_hashes": len(set(hashes)) == len(hashes),
        "no_cross_label_hashes": all(
            len({row["label"] for row in rows if row["source_sha256"] == digest}) == 1
            for digest in set(hashes)
        ),
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "rows": len(rows), "classes": len(classes), "counts": dict(sorted(counts.items()))}


def validate_embeddings(directory: Path, labels: np.ndarray, classes: list[str]) -> dict:
    details = {}
    reference = None
    for extractor in CANONICAL_EXTRACTORS:
        feature_path = directory / f"{extractor}.npy"
        label_path = directory / f"{extractor}_labels.npy"
        classes_path = directory / f"{extractor}_classes.json"
        if not feature_path.exists() or not label_path.exists() or not classes_path.exists():
            details[extractor] = {"status": "MISSING"}
            continue
        features = np.load(feature_path, mmap_mode="r")
        observed = np.load(label_path, allow_pickle=False)
        observed_classes = json.loads(classes_path.read_text())
        finite = all(np.isfinite(features[start:start + 64]).all()
                     for start in range(0, len(features), 64))
        ok = (features.ndim == 2 and features.shape[0] == len(labels)
              and np.array_equal(observed, labels) and observed_classes == classes and finite)
        if reference is None:
            reference = observed
        ok = ok and np.array_equal(reference, observed)
        details[extractor] = {"status": "PASS" if ok else "FAIL",
                              "shape": list(features.shape), "finite": bool(finite)}
    complete = len(details) == 20 and all(item["status"] == "PASS" for item in details.values())
    return {"status": "PASS_REEXTRACTED_GROUP_AWARE" if complete else "BLOCKED_DATA_LEAKAGE_RISK",
            "extractors": details}


def extract_one(extractor: str, manifest: Path, output: Path, device: str, batch_size: int,
                skip_existing: bool = False) -> None:
    paths, classes, labels = discover_manifest_images(manifest)
    output.mkdir(parents=True, exist_ok=True)
    feature_path = output / f"{extractor}.npy"
    label_path = output / f"{extractor}_labels.npy"
    classes_path = output / f"{extractor}_classes.json"
    if skip_existing and feature_path.exists() and label_path.exists() and classes_path.exists():
        features = np.load(feature_path, mmap_mode="r")
        observed = np.load(label_path, allow_pickle=False)
        observed_classes = json.loads(classes_path.read_text())
        finite = features.ndim == 2 and features.shape[0] == len(labels) and all(
            np.isfinite(features[start:start + 64]).all() for start in range(0, len(features), 64)
        )
        if finite and np.array_equal(observed, labels) and observed_classes == classes:
            print(json.dumps({"extractor": extractor, "status": "SKIP_VALID_EXISTING",
                              "shape": list(features.shape)}), flush=True)
            return
    base = _load_module("base_extractors", REPO / "src/01_extract_features.py")
    started = time.time()
    if extractor in SOTA_EXTRACTORS:
        sota = _load_module("sota_extractors", REPO / "src/extract_sota_2024.py")
        sota.DEVICE = device
        sota.BATCH_SIZE = batch_size
        model, transform, kind = sota.load_model_and_transform(extractor)
        features = sota.extract_embeddings(model, transform, paths, kind)
        del model
    else:
        model = base.get_extractor(extractor, device=device)
        features = model.extract(paths, batch_size=batch_size)
        del model
    features = np.asarray(features)
    if features.ndim != 2 or features.shape[0] != len(labels) or not np.isfinite(features).all():
        raise ValueError(f"invalid features from {extractor}: {features.shape}")
    np.save(feature_path, features)
    np.save(label_path, labels)
    classes_path.write_text(json.dumps(classes, indent=2) + "\n")
    print(json.dumps({"extractor": extractor, "shape": list(features.shape),
                      "seconds": time.time() - started, "device": device}), flush=True)
    del features
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def write_audit(manifest: Path, embeddings: Path, results: Path) -> dict:
    results.mkdir(parents=True, exist_ok=True)
    manifest_result = validate_manifest(manifest)
    _, classes, labels = load_manifest(manifest)
    embedding_result = validate_embeddings(embeddings, labels, classes)
    status = embedding_result["status"] if manifest_result["status"] == "PASS" else "BLOCKED_DATA_LEAKAGE_RISK"
    report = {"dataset": "VisTexReference12", "status": status,
              "manifest": manifest_result, "embeddings": embedding_result}
    (results / "data_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    with (results / "data_audit.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["dataset", "status", "samples", "classes", "extractors"])
        writer.writeheader()
        writer.writerow({"dataset": "VisTexReference12", "status": status, "samples": len(labels),
                         "classes": len(classes), "extractors": sum(
                             item["status"] == "PASS" for item in embedding_result["extractors"].values())})
    manifest_dir = results / "sample_manifests"
    manifest_dir.mkdir(exist_ok=True)
    target = manifest_dir / "VisTexReference12.csv"
    target.write_bytes(manifest.read_bytes())
    print(json.dumps({"dataset": "VisTexReference12", "status": status}, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    extract = subparsers.add_parser("extract")
    extract.add_argument("--extractor", required=True, choices=(*CANONICAL_EXTRACTORS, "all"))
    extract.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    extract.add_argument("--output", type=Path, default=DEFAULT_EMBEDDINGS)
    extract.add_argument("--device", choices=("cuda", "cpu"), default="cuda" if torch.cuda.is_available() else "cpu")
    extract.add_argument("--batch-size", type=int, default=16)
    extract.add_argument("--skip-existing", action="store_true",
                         help="skip only complete, finite embeddings matching this manifest")
    audit = subparsers.add_parser("audit")
    audit.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    audit.add_argument("--embeddings", type=Path, default=DEFAULT_EMBEDDINGS)
    audit.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args()
    if args.command == "extract":
        extractors = CANONICAL_EXTRACTORS if args.extractor == "all" else (args.extractor,)
        for extractor in extractors:
            extract_one(extractor, args.manifest.resolve(), args.output.resolve(), args.device,
                        args.batch_size, args.skip_existing)
    else:
        report = write_audit(args.manifest.resolve(), args.embeddings.resolve(), args.results.resolve())
        if not report["status"].startswith("PASS"):
            raise SystemExit(2)


if __name__ == "__main__":
    main()
