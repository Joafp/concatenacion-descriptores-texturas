#!/usr/bin/env python3
"""Measure per-image extraction time for the two exploratory routing blocks.

The model-load time is excluded. Each timed item includes disk decode,
preprocessing, GPU inference, synchronization, and CPU feature transfer.
This is a per-block benchmark, not a full routed-system latency benchmark.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
import timm
import torch
from PIL import Image
from sklearn.model_selection import StratifiedGroupKFold
from torchvision import transforms


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from run_confirmatory_nested import (  # noqa: E402
    canonical_labels, load_manifest, official_split_indices,
)


MODELS = {
    "resnet50": "resnet50.a1_in1k",
    "beitv2_base_final": "beitv2_base_patch16_224.in1k_ft_in22k_in1k",
}


def measure_one(model_key: str, paths: list[Path], indices: np.ndarray,
                reference: np.ndarray, device: str, warmup: int) -> dict:
    model = timm.create_model(MODELS[model_key], pretrained=True, num_classes=0).to(device).eval()
    cfg = timm.data.resolve_model_data_config(model)
    transform = transforms.Compose([
        transforms.Resize(cfg["input_size"][1:]),
        transforms.CenterCrop(cfg["input_size"][1:]),
        transforms.ToTensor(),
        transforms.Normalize(mean=cfg["mean"], std=cfg["std"]),
    ])

    def extract(path: Path) -> np.ndarray:
        with Image.open(path) as handle:
            image = transform(handle.convert("RGB")).unsqueeze(0).to(device)
        with torch.inference_mode():
            vector = model(image)
        if device == "cuda":
            torch.cuda.synchronize()
        return vector.cpu().numpy().ravel()

    for i in range(warmup):
        extract(paths[i % len(paths)])
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    latencies = []
    cosines = []
    for path, row_idx in zip(paths, indices, strict=True):
        if device == "cuda":
            torch.cuda.synchronize()
        started = time.perf_counter()
        vector = extract(path)
        latencies.append((time.perf_counter() - started) * 1000.0)
        expected = np.asarray(reference[row_idx], dtype=np.float64)
        observed = np.asarray(vector, dtype=np.float64)
        cosines.append(float(np.dot(expected, observed) /
                             max(np.linalg.norm(expected) * np.linalg.norm(observed), 1e-12)))
    result = {
        "model": MODELS[model_key],
        "n_timed_images": len(paths),
        "warmup_images": warmup,
        "mean_ms": float(np.mean(latencies)),
        "median_ms": float(np.median(latencies)),
        "p95_ms": float(np.percentile(latencies, 95)),
        "min_reference_cosine": float(np.min(cosines)),
        "median_reference_cosine": float(np.median(cosines)),
        "gpu_peak_allocated_mb": (float(torch.cuda.max_memory_allocated() / 2**20)
                                  if device == "cuda" else None),
        "latencies_ms": latencies,
    }
    del model
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="FMD")
    parser.add_argument("--embedding-root", type=Path, default=REPO / "embeddings_confirmatory")
    parser.add_argument("--manifest-root", type=Path, default=REPO / "results" / "confirmatory")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outer-fold", type=int, default=0, choices=range(5))
    parser.add_argument("--official-split", type=int)
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--output", type=Path,
                        default=REPO / "results" / "exploratory" / "adaptive_descriptor_pilot")
    args = parser.parse_args()
    if args.n < 2 or args.warmup < 0:
        parser.error("n must be >= 2 and warmup >= 0")
    root = args.embedding_root / args.dataset
    y = canonical_labels(np.load(root / "resnet50_labels.npy", allow_pickle=False))
    groups, rows = load_manifest(args.manifest_root, args.dataset, y)
    if args.official_split is not None:
        _, test = official_split_indices(rows, args.official_split)
    else:
        splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=args.seed)
        _, test = list(splitter.split(np.zeros(len(y)), y, groups))[args.outer_fold]
    indices = test[np.linspace(0, len(test) - 1, min(args.n, len(test)), dtype=int)]
    paths = []
    for row_idx in indices:
        path = Path(rows[row_idx].get("source_path") or rows[row_idx]["path"])
        if not path.is_absolute():
            path = REPO / path
        if not path.is_file():
            raise FileNotFoundError(path)
        paths.append(path)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    result = {
        "dataset": args.dataset,
        "seed": args.seed,
        "outer_fold": (None if args.official_split is not None else args.outer_fold),
        "official_split": args.official_split,
        "split_protocol": ("manifest-defined official split" if args.official_split is not None
                            else "StratifiedGroupKFold"),
        "device": device,
        "torch_version": torch.__version__,
        "timm_version": timm.__version__,
        "model_load_excluded": True,
        "batch_size": 1,
        "blocks": {},
    }
    for key in MODELS:
        reference = np.load(root / f"{key}.npy", mmap_mode="r")
        result["blocks"][key] = measure_one(key, paths, indices, reference, device, args.warmup)
        print(key, result["blocks"][key]["median_ms"], flush=True)
    args.output.mkdir(parents=True, exist_ok=True)
    split_tag = f"official{args.official_split}" if args.official_split is not None else f"f{args.outer_fold}"
    path = args.output / f"latency_{args.dataset}_s{args.seed}_{split_tag}_n{len(indices)}.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(path)


if __name__ == "__main__":
    main()
