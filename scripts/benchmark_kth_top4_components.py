#!/usr/bin/env python3
"""New KTH training-image component profile. No classifier F1/online claim.

Uses only local frozen weights, one resident model, two CPU threads and the
global lock. Scientific feature-parity failure is terminal, with no retry.
"""
from __future__ import annotations
import argparse
import csv
import fcntl
import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import torch
import timm
from fsc_tex.executor import OnlineExtractorRegistry

BLOCKS = {
    "resnet50": "timm/resnet50.a1_in1k",
    "beitv2_base_final": "timm/beitv2_base_patch16_224.in1k_ft_in22k_in1k",
    "dinov2": "timm/vit_base_patch14_dinov2.lvd142m",
    "dinov2_large": "timm/vit_large_patch14_dinov2.lvd142m",
    "dinov2_small": "timm/vit_small_patch14_dinov2.lvd142m",
    "eva02_base": "timm/eva02_base_patch14_224.mim_in22k",
    "convnext_v2_t": "timm/convnextv2_tiny.fcmae_ft_in22k_in1k",
    "siglip_base": "google/siglip-base-patch16-224",
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for data in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def training_sample(rows, train, per_class=3):
    rng = np.random.default_rng(42)
    selected = []
    classes = sorted({rows[i]["label"] for i in train})
    for label in classes:
        candidates = [i for i in train if rows[i]["label"] == label]
        if len(candidates) < per_class:
            raise ValueError(f"too few training images for class {label}")
        selected.extend(map(int, rng.choice(candidates, size=per_class, replace=False)))
    if not classes or len(selected) != per_class * len(classes) or not set(selected).issubset(train):
        raise ValueError("invalid stratified training sample")
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {"status": "preparing", "dataset": "KTHTIPS2b", "blocks": {},
              "timing_partition": "outer_training_official1_inverted", "batch_size": 1,
              "warmup_images": 5, "images_per_class": 3, "minimum_cosine": 0.999,
              "cpu_threads": 2, "model_load_excluded": True,
              "scope": "component profile; no classifier quality or full-policy latency"}
    dump(output / "status.json", report)
    try:
        torch.set_num_threads(2)
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA required; CPU substitution is forbidden")
        torch.manual_seed(42)
        torch.cuda.manual_seed_all(42)
        prep = ROOT / "results/analysis/top4_fixed_preparation_20261114_v1/conditions.json"
        condition = next(c for c in json.loads(prep.read_text())
                         if c["dataset"] == "KTHTIPS2b" and c["outer_fold"] == 0)
        manifest = ROOT / condition["manifest_source"]
        with manifest.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        train = condition["train_indices"]
        selected = training_sample(rows, train)
        report["timed_images"] = len(selected)
        sources = {str(p.relative_to(ROOT)): sha(p) for p in
                   (prep, manifest, Path(__file__), ROOT / "src/fsc_tex/executor.py")}
        paths = []
        for i in selected:
            path = ROOT / rows[i]["source_path"]
            digest = sha(path)
            if digest != rows[i]["source_sha256"]:
                raise ValueError(f"source image changed: {path}")
            sources[str(path.relative_to(ROOT))] = digest
            paths.append(path)
        weights = {}
        hub = Path.home() / ".cache/huggingface/hub"
        for block, repo in BLOCKS.items():
            repo_path = hub / ("models--" + repo.replace("/", "--"))
            revision = (repo_path / "refs/main").read_text().strip()
            snapshot = repo_path / "snapshots" / revision
            files = [p for p in snapshot.iterdir() if p.is_file() and p.suffix in {".json", ".bin", ".safetensors"}]
            if not any(p.suffix in {".bin", ".safetensors"} for p in files):
                raise FileNotFoundError(f"local weights unavailable: {repo}")
            weights[block] = {"repository": repo, "revision": revision,
                              "files": {str(p): sha(p) for p in files}}
            reference_path = ROOT / "embeddings_extensions/KTH-TIPS2-b" / f"{block}.npy"
            sources[str(reference_path.relative_to(ROOT))] = sha(reference_path)
        frozen = {**report, "seed": 42, "indices": selected, "sources": sources, "weights": weights,
                  "torch": torch.__version__, "timm": timm.__version__,
                  "gpu": torch.cuda.get_device_name(0),
                  "nvidia_smi": subprocess.check_output(["nvidia-smi", "--query-gpu=name,driver_version,memory.used", "--format=csv,noheader"], text=True)}
        dump(output / "protocol_frozen.json", frozen)
        report["protocol_sha256"] = sha(output / "protocol_frozen.json")
        with (ROOT / "results/analysis/gpu.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            report["status"] = "running"
            dump(output / "status.json", report)
            for block in BLOCKS:
                report["phase"] = "model_loading"
                registry = OnlineExtractorRegistry(device="cuda", seed=42)
                extract = registry.load_extractor(block)
                reference = np.load(ROOT / "embeddings_extensions/KTH-TIPS2-b" / f"{block}.npy", mmap_mode="r")
                for i in range(5):
                    extract(paths[i])
                report["phase"] = "measurement"
                torch.cuda.reset_peak_memory_stats()
                calls = []
                for idx, path in zip(selected, paths, strict=True):
                    torch.cuda.synchronize()
                    started = time.perf_counter()
                    vector = np.asarray(extract(path), dtype=np.float64)
                    torch.cuda.synchronize()
                    elapsed = 1000 * (time.perf_counter() - started)
                    expected = np.asarray(reference[idx], dtype=np.float64)
                    cosine = float(vector @ expected / max(np.linalg.norm(vector) * np.linalg.norm(expected), 1e-12))
                    if vector.shape != expected.shape or not np.isfinite(vector).all() or not np.isfinite(cosine):
                        raise ValueError(f"invalid extracted vector: {block}/{idx}")
                    calls.append({"row_id": idx, "ms": elapsed, "reference_cosine": cosine})
                dump(output / f"{block}_calls.json", calls)
                latencies = [c["ms"] for c in calls]
                min_cosine = min(c["reference_cosine"] for c in calls)
                report["blocks"][block] = {"mean_ms": float(np.mean(latencies)),
                    "median_ms": float(np.median(latencies)), "p95_ms": float(np.percentile(latencies, 95)),
                    "min_reference_cosine": min_cosine, "n_timed_images": len(selected),
                    "gpu_peak_allocated_mb": torch.cuda.max_memory_allocated() / 2**20,
                    "calls_sha256": sha(output / f"{block}_calls.json")}
                dump(output / "status.json", report)
                print(f"{block}: mean={np.mean(latencies):.3f} ms, min_cos={min_cosine:.9f}", flush=True)
                if min_cosine < 0.999:
                    raise ArithmeticError(f"feature fidelity below frozen threshold: {block}: {min_cosine}")
                del extract, registry, reference
                gc.collect()
                torch.cuda.empty_cache()
        report["status"] = "complete"
        dump(output / "profile.json", report)
        report["profile_sha256"] = sha(output / "profile.json")
        dump(output / "status.json", report)
    except Exception as exc:
        report.update(status="requires_review" if isinstance(exc, ArithmeticError) or
                      (isinstance(exc, ValueError) and report.get("phase") == "measurement") else "infrastructure_error",
                      error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
        dump(output / "status.json", report)
        raise


if __name__ == "__main__":
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    main()
