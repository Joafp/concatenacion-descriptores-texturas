#!/usr/bin/env python3
"""Time and verify four descriptor components on audited source images.

Model loading is excluded. Each measured extraction includes image decode,
preprocessing, model inference, synchronization and feature transfer. The
result is a component benchmark, not full conditional-system wall time.
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from run_confirmatory_nested import load_manifest, official_split_indices  # noqa: E402
from run_conditional_route_feasibility import (  # noqa: E402
    DATASETS, file_hash, load_blocks,
)

BLOCKS = ("dinov2_small", "beitv2_base_final", "dinov2", "dinov2_large")


def module_from_file(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load extractor: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sync() -> None:
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def run(dataset: str, split: int, n: int, output: Path) -> dict:
    if n < 2:
        raise ValueError("n must be at least two")
    embedding_dir, result_dir = DATASETS[dataset]
    cache, y, hashes = load_blocks(embedding_dir)
    _, rows = load_manifest(result_dir, dataset, y)
    _, test = official_split_indices(rows, split)
    indices = test[np.linspace(0, len(test) - 1, min(n, len(test)), dtype=int)]
    paths = []
    for row_id in indices:
        row = rows[int(row_id)]
        path = Path(row.get("source_path") or row.get("path"))
        if not path.is_absolute():
            path = ROOT / path
        if not path.is_file():
            raise FileNotFoundError(path)
        expected = row.get("source_sha256") or row.get("sha256")
        if not expected or file_hash(path) != expected:
            raise ValueError(f"source image checksum mismatch at row {row_id}")
        paths.append(path)
    legacy = module_from_file("conditional_legacy_extractors", ROOT / "src/01_extract_features.py")
    from run_online_adaptive_validation import extract, load_extractor
    device = "cuda" if torch.cuda.is_available() else "cpu"
    timings = {}
    for name in BLOCKS:
        if name == "beitv2_base_final":
            extractor = load_extractor(name, device)
            fn = lambda path: extract(path, *extractor, device)[0]
        else:
            extractor = legacy.get_extractor(name, device=device)
            fn = lambda path: extractor.extract([str(path)], batch_size=1)[0]
        for path in paths[:2]:
            fn(path)
        durations = []
        cosines = []
        for row_id, path in zip(indices, paths, strict=True):
            sync()
            start = time.perf_counter()
            vector = np.asarray(fn(path), dtype=np.float32).reshape(-1)
            sync()
            durations.append((time.perf_counter() - start) * 1000.0)
            reference = cache[name][int(row_id)].reshape(-1)
            cosine = float(np.dot(vector, reference) /
                           max(np.linalg.norm(vector) * np.linalg.norm(reference), 1e-12))
            cosines.append(cosine)
        timings[name] = {
            "mean": float(np.mean(durations)),
            "median": float(np.median(durations)),
            "p95": float(np.percentile(durations, 95)),
            "min_reference_cosine": float(np.min(cosines)),
            "durations_ms": durations,
        }
        print(f"{name}: {timings[name]['mean']:.2f} ms, min cosine {min(cosines):.6f}", flush=True)
        del extractor, fn
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()
    if any(timings[name]["min_reference_cosine"] < 0.999 for name in BLOCKS):
        raise ValueError("online extraction disagrees with cached embeddings")
    result = {
        "status": "EXPLORATORY_MEASURED_COMPONENTS",
        "dataset": dataset,
        "protocol": f"official split {split}; deterministic {len(indices)}-row test subset",
        "rows": indices.tolist(),
        "device": device,
        "model_load_and_svm_fit_excluded": True,
        "per_descriptor_latency_ms": timings,
        "manifest_sha256": file_hash(result_dir / "sample_manifests" / f"{dataset}.csv"),
        "embedding_sha256": hashes,
        "limitation": "Component costs are measured, but summing them is not routed-system wall time.",
    }
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{dataset}_official{split}_n{len(indices)}_components.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    parser.add_argument("--split", type=int, default=1)
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--output", type=Path, default=(
        ROOT / "results/exploratory/conditional_acquisition/timing"
    ))
    args = parser.parse_args()
    result = run(args.dataset, args.split, args.n, args.output)
    print(json.dumps({
        "dataset": result["dataset"],
        "device": result["device"],
        "n": len(result["rows"]),
        "mean_ms": {name: row["mean"] for name, row in result["per_descriptor_latency_ms"].items()},
    }, indent=2))


if __name__ == "__main__":
    main()
