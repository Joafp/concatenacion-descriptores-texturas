#!/usr/bin/env python3
"""Re-extract one descriptor in a manifest-defined, immutable sample order."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path

import numpy as np
import torch


REPO = Path(__file__).resolve().parents[1]
SOTA_EXTRACTORS = {"eva02_base", "mae_base", "siglip_base"}


def load_legacy_extractors():
    path = REPO / "src" / "01_extract_features.py"
    spec = importlib.util.spec_from_file_location("legacy_extractors", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import extractors from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_sota_extractors():
    path = REPO / "src" / "extract_sota_2024.py"
    spec = importlib.util.spec_from_file_location("sota_extractors", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import extractors from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_manifest(path: Path) -> tuple[list[Path], np.ndarray, list[str]]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"row_id", "path", "label", "class_name"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"manifest requires columns {sorted(required)}")
    if [int(row["row_id"]) for row in rows] != list(range(len(rows))):
        raise ValueError("manifest row_id must be contiguous and ordered")
    paths = [Path(row["path"]) for row in rows]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"manifest contains {len(missing)} missing files; first={missing[0]}")
    labels = np.asarray([int(row["label"]) for row in rows], dtype=np.int64)
    classes = [name for _, name in sorted({(int(row["label"]), row["class_name"]) for row in rows})]
    if sorted(np.unique(labels).tolist()) != list(range(len(classes))):
        raise ValueError("labels must be zero-based and contiguous")
    return paths, labels, classes


def atomic_save_npy(path: Path, value: np.ndarray) -> None:
    temporary = path.with_suffix(".tmp.npy")
    np.save(temporary, value)
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--extractor", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    legacy = load_legacy_extractors()
    if args.extractor not in legacy.EXTRACTORS and args.extractor not in SOTA_EXTRACTORS:
        raise ValueError(f"unknown extractor: {args.extractor}")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA_REQUIRED: refusing confirmatory extraction on CPU")
    legacy.set_seed(args.seed)
    paths, labels, classes = read_manifest(args.manifest.resolve())
    args.output.mkdir(parents=True, exist_ok=True)

    started = time.time()
    if args.extractor in SOTA_EXTRACTORS:
        sota = load_sota_extractors()
        sota.DEVICE = "cuda"
        sota.BATCH_SIZE = args.batch_size
        model, transform, model_kind = sota.load_model_and_transform(args.extractor)
        embeddings = sota.extract_embeddings(model, transform, paths, model_kind)
    else:
        extractor = legacy.get_extractor(args.extractor, device="cuda")
        embeddings = extractor.extract(paths, batch_size=args.batch_size)
    if embeddings.ndim != 2 or len(embeddings) != len(labels):
        raise ValueError("embedding shape does not match manifest")
    if not np.isfinite(embeddings).all():
        raise ValueError("embedding contains NaN or infinity")

    embedding_path = args.output / f"{args.extractor}.npy"
    labels_path = args.output / f"{args.extractor}_labels.npy"
    atomic_save_npy(embedding_path, embeddings)
    atomic_save_npy(labels_path, labels)
    (args.output / f"{args.extractor}_classes.json").write_text(json.dumps(classes, indent=2) + "\n")
    metadata = {
        "extractor": args.extractor,
        "manifest": str(args.manifest.resolve()),
        "manifest_sha256": sha256(args.manifest.resolve()),
        "rows": len(labels),
        "dimensions": embeddings.shape[1],
        "classes": len(classes),
        "seed": args.seed,
        "device": torch.cuda.get_device_name(0),
        "torch": torch.__version__,
        "elapsed_seconds": time.time() - started,
        "embedding_sha256": sha256(embedding_path),
    }
    (args.output / f"{args.extractor}_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
