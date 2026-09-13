#!/usr/bin/env python3
"""Chunked, resumable extraction for slow KTH-TIPS2-b descriptors.

The WSL environment on this machine restarts unpredictably roughly every
~55 minutes (observed via dmesg: a clean systemd shutdown+remount, not a
crash), which is longer than a single-pass extraction of the slower
extractors (dinov2/dinov2_large/mae_base/siglip_base, ~80 min each at
~1 img/s on CPU). A single `extract_one` call has no partial-progress
checkpoint, so an interruption loses the entire pass.

This script splits the 4,752-row manifest into small chunks (default 400
images, ~7 min each at 1 img/s) and saves each chunk to disk immediately
after computing it. Re-running the script skips chunks already written, so
an interruption loses at most one chunk. Once all chunks for an extractor
exist, `--merge` concatenates them into the same `<extractor>.npy` /
`_labels.npy` / `_classes.json` layout that `kth_tips2b_extension.py`
(and therefore `run_confirmatory_nested.py`) expect.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np


REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DEFAULT_MANIFEST = HERE / "KTH-TIPS2-b_manifest.csv"
DEFAULT_OUTPUT = REPO / "embeddings_extensions/KTHTIPS2b"
SOTA_EXTRACTORS = {"eva02_base", "mae_base", "siglip_base"}


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_shared():
    return _load_module("extension_shared", REPO / "src/vistex_reference12_extension.py")


def chunk_dir(output: Path, extractor: str) -> Path:
    return output / f"{extractor}_chunks"


def chunk_ranges(n_total: int, chunk_size: int) -> list[tuple[int, int]]:
    return [(start, min(start + chunk_size, n_total)) for start in range(0, n_total, chunk_size)]


def extract_slice(extractor: str, paths: list[str], device: str, batch_size: int) -> np.ndarray:
    base = _load_module("base_extractors", REPO / "src/01_extract_features.py")
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
    return np.asarray(features)


def run_chunks(extractor: str, manifest: Path, output: Path, device: str, batch_size: int,
                chunk_size: int) -> None:
    shared = load_shared()
    paths, classes, labels = shared.discover_manifest_images(manifest, REPO)
    ranges = chunk_ranges(len(paths), chunk_size)
    cdir = chunk_dir(output, extractor)
    cdir.mkdir(parents=True, exist_ok=True)
    pending = []
    for index, (start, end) in enumerate(ranges):
        chunk_path = cdir / f"chunk_{index:03d}.npy"
        if chunk_path.exists():
            existing = np.load(chunk_path, mmap_mode="r")
            if existing.shape[0] == end - start and np.isfinite(existing[: min(32, len(existing))]).all():
                print(f"[{extractor}] chunk {index} ({start}:{end}) already done, skip", flush=True)
                continue
        pending.append((index, start, end, chunk_path))
    if not pending:
        print(f"[{extractor}] all {len(ranges)} chunks already done", flush=True)
        return
    print(f"[{extractor}] {len(pending)}/{len(ranges)} chunks remaining, "
          f"chunk_size={chunk_size}", flush=True)
    for index, start, end, chunk_path in pending:
        print(f"[{extractor}] computing chunk {index} ({start}:{end}) of {len(paths)}", flush=True)
        features = extract_slice(extractor, paths[start:end], device, batch_size)
        if features.ndim != 2 or features.shape[0] != end - start or not np.isfinite(features).all():
            raise ValueError(f"invalid chunk features for {extractor} [{start}:{end}]: {features.shape}")
        tmp = chunk_path.with_suffix(".tmp.npy")
        np.save(tmp, features)
        tmp.replace(chunk_path)
        print(f"[{extractor}] wrote chunk {index} ({features.shape})", flush=True)


def merge_chunks(extractor: str, manifest: Path, output: Path, chunk_size: int) -> None:
    shared = load_shared()
    paths, classes, labels = shared.discover_manifest_images(manifest, REPO)
    ranges = chunk_ranges(len(paths), chunk_size)
    cdir = chunk_dir(output, extractor)
    parts = []
    for index, (start, end) in enumerate(ranges):
        chunk_path = cdir / f"chunk_{index:03d}.npy"
        if not chunk_path.exists():
            raise SystemExit(f"missing chunk {index} for {extractor}: {chunk_path}")
        part = np.load(chunk_path)
        if part.shape[0] != end - start:
            raise SystemExit(f"chunk {index} for {extractor} has wrong length: {part.shape}")
        parts.append(part)
    features = np.concatenate(parts, axis=0).astype(np.float32)
    if features.shape[0] != len(labels) or not np.isfinite(features).all():
        raise SystemExit(f"merged features invalid for {extractor}: {features.shape}")
    output.mkdir(parents=True, exist_ok=True)
    np.save(output / f"{extractor}.npy", features)
    np.save(output / f"{extractor}_labels.npy", labels)
    (output / f"{extractor}_classes.json").write_text(json.dumps(classes, indent=2) + "\n")
    print(f"[{extractor}] merged {len(ranges)} chunks -> {features.shape}", flush=True)
    for index in range(len(ranges)):
        (cdir / f"chunk_{index:03d}.npy").unlink()
    cdir.rmdir()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extractor", required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cpu")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--chunk-size", type=int, default=400)
    parser.add_argument("--merge", action="store_true", help="merge existing chunks instead of extracting")
    args = parser.parse_args()
    if args.merge:
        merge_chunks(args.extractor, args.manifest.resolve(), args.output.resolve(), args.chunk_size)
    else:
        run_chunks(args.extractor, args.manifest.resolve(), args.output.resolve(), args.device,
                   args.batch_size, args.chunk_size)


if __name__ == "__main__":
    main()
