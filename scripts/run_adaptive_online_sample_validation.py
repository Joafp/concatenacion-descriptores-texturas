#!/usr/bin/env python3
"""Measure online routing latency and embedding agreement for a saved sample protocol."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import timm
import torch
from PIL import Image
from torchvision import transforms

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from run_confirmatory_nested import audit_gate, load_dataset, load_manifest, make_model  # noqa: E402
from run_adaptive_descriptor_pilot import margin  # noqa: E402
from run_adaptive_sample_generalization import (  # noqa: E402
    sha256, split_rows,
)


MODEL_NAMES = {
    "resnet50": "resnet50.a1_in1k",
    "beitv2_base_final": "beitv2_base_patch16_224.in1k_ft_in22k_in1k",
}


def load_extractor(name: str, device: str):
    model = timm.create_model(MODEL_NAMES[name], pretrained=True, num_classes=0).to(device).eval()
    cfg = timm.data.resolve_model_data_config(model)
    transform = transforms.Compose([
        transforms.Resize(cfg["input_size"][1:]),
        transforms.CenterCrop(cfg["input_size"][1:]),
        transforms.ToTensor(),
        transforms.Normalize(mean=cfg["mean"], std=cfg["std"]),
    ])
    return model, transform


def extract(path: Path, extractor, device: str) -> np.ndarray:
    model, transform = extractor
    with Image.open(path) as handle:
        tensor = transform(handle.convert("RGB")).unsqueeze(0).to(device)
    with torch.inference_mode():
        features = model(tensor)
    if device == "cuda":
        torch.cuda.synchronize()
    result = features.cpu().numpy().astype(np.float32, copy=False)
    return result / np.maximum(np.linalg.norm(result, axis=1, keepdims=True), 1e-12)


def predict(path: Path, policy: str, base_extractor, extra_extractor,
            base_clf, full_clf, threshold: float, device: str):
    if device == "cuda":
        torch.cuda.synchronize()
    began = time.perf_counter()
    base_x = extract(path, base_extractor, device)
    requested = policy == "full" or bool(margin(base_clf, base_x)[0] <= threshold)
    extra_x = extract(path, extra_extractor, device) if requested else None
    if requested:
        prediction = int(full_clf.predict(np.concatenate((base_x, extra_x), axis=1))[0])
    else:
        prediction = int(base_clf.predict(base_x)[0])
    if device == "cuda":
        torch.cuda.synchronize()
    return prediction, requested, (time.perf_counter() - began) * 1000.0, base_x, extra_x


def summary(samples: list[float]) -> dict:
    return {"mean_ms": float(np.mean(samples)), "median_ms": float(np.median(samples)),
            "p95_ms": float(np.percentile(samples, 95))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("CUReT", "KTHTIPS2b"), required=True)
    parser.add_argument("--split-number", type=int, default=1)
    parser.add_argument("--curet-direction", choices=("a_to_b", "b_to_a"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--embedding-root", type=Path, required=True)
    parser.add_argument("--prior-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=5)
    args = parser.parse_args()
    if args.dataset == "CUReT" and args.curet_direction is None:
        parser.error("CUReT requires --curet-direction")
    if args.dataset == "KTHTIPS2b" and args.curet_direction is not None:
        parser.error("--curet-direction is only valid for CUReT")
    if args.n < 2 or args.warmup < 0:
        parser.error("n must be >= 2 and warmup >= 0")

    audit_root, manifest_root, embedding_root, prior_path, output = [
        p.resolve() if p.is_absolute() else (REPO / p).resolve()
        for p in (args.audit_root, args.manifest_root, args.embedding_root,
                  args.prior_json, args.output)
    ]
    prior = json.loads(prior_path.read_text())
    if prior.get("dataset") != args.dataset or prior.get("seed") != args.seed:
        raise ValueError("prior result dataset/seed does not match timing request")
    if args.dataset == "CUReT":
        if prior.get("curet_direction") != args.curet_direction:
            raise ValueError("CUReT prior direction does not match timing request")
    elif prior.get("official_split_number") != args.split_number or "adapted" not in prior.get("outer_protocol", ""):
        raise ValueError("KTH timing requires the matching adapted-LOPO prior")
    audit_gate(audit_root, args.dataset)
    cache, y = load_dataset(REPO, args.dataset, embedding_root=embedding_root)
    groups, rows = load_manifest(manifest_root, args.dataset, y)
    train, test, _, outer_protocol, _, _, _ = split_rows(
        args.dataset, rows, y, args.split_number, args.curet_direction
    )
    manifest_path = manifest_root / "sample_manifests" / f"{args.dataset}.csv"
    embedding_dataset = {"KTHTIPS2b": "KTH-TIPS2-b"}.get(args.dataset, args.dataset)
    embedding_dir = embedding_root / embedding_dataset
    expected = {
        "audit_csv_sha256": sha256(audit_root / "data_audit.csv"),
        "manifest_csv_sha256": sha256(manifest_path),
        "resnet50_npy_sha256": sha256(embedding_dir / "resnet50.npy"),
        "beitv2_base_final_npy_sha256": sha256(embedding_dir / "beitv2_base_final.npy"),
        "resnet50_labels_sha256": sha256(embedding_dir / "resnet50_labels.npy"),
        "beitv2_base_final_labels_sha256": sha256(embedding_dir / "beitv2_base_final_labels.npy"),
    }
    if any(prior.get("provenance", {}).get(k) != v for k, v in expected.items()):
        raise ValueError("prior provenance no longer matches audited inputs")

    base_x, extra_x = cache["resnet50"], cache["beitv2_base_final"]
    full_x = np.concatenate((base_x, extra_x), axis=1)
    base_clf, full_clf = make_model("svm", args.seed), make_model("svm", args.seed)
    base_clf.fit(base_x[train], y[train])
    full_clf.fit(full_x[train], y[train])
    threshold = float(prior["train_oof_margin_threshold"])
    indices = test[np.linspace(0, len(test) - 1, min(args.n, len(test)), dtype=int)]
    reference_csv = prior_path.with_name(prior_path.stem + "_per_sample.csv")
    with reference_csv.open(newline="") as handle:
        ref_rows = {int(r["row_id"]): r for r in csv.DictReader(handle)}
    if any(int(i) not in ref_rows for i in indices):
        raise ValueError("timing rows are not covered by the prior per-sample artifact")
    paths = []
    for i in indices:
        row = rows[int(i)]
        p = Path(row.get("source_path") or row.get("path"))
        p = p if p.is_absolute() else REPO / p
        if not p.is_file():
            raise FileNotFoundError(p)
        expected_sha = row.get("source_sha256") or row.get("sha256")
        if sha256(p) != expected_sha:
            raise ValueError(f"timing image SHA-256 mismatch: manifest row {i}")
        paths.append(p)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    base_extractor = load_extractor("resnet50", device)
    extra_extractor = load_extractor("beitv2_base_final", device)
    for warm in range(args.warmup):
        for policy in ("adaptive", "full"):
            predict(paths[warm % len(paths)], policy, base_extractor, extra_extractor,
                    base_clf, full_clf, threshold, device)

    latencies = {"adaptive": [], "full": []}
    predictions = {"adaptive": [], "full": []}
    requests = []
    base_cosines, extra_cosines = [], []
    for j, (row_idx, path) in enumerate(zip(indices, paths, strict=True)):
        order = ("adaptive", "full") if j % 2 == 0 else ("full", "adaptive")
        measured = {}
        for policy in order:
            measured[policy] = predict(path, policy, base_extractor, extra_extractor,
                                       base_clf, full_clf, threshold, device)
        for policy in ("adaptive", "full"):
            pred, requested, latency, _, _ = measured[policy]
            predictions[policy].append(pred)
            latencies[policy].append(latency)
            if policy == "adaptive":
                requests.append(requested)
        # The full route necessarily extracts both blocks and supplies the
        # source-vs-cache identity check for this exact timing image.
        _, _, _, observed_base, observed_extra = measured["full"]
        base_cosines.append(float(np.sum(observed_base[0] * base_x[int(row_idx)])))
        extra_cosines.append(float(np.sum(observed_extra[0] * extra_x[int(row_idx)])))

    agreement = {
        "adaptive_prediction": float(np.mean([
            p == int(ref_rows[int(i)]["adaptive_prediction"])
            for i, p in zip(indices, predictions["adaptive"], strict=True)])),
        "full_prediction": float(np.mean([
            p == int(ref_rows[int(i)]["full_prediction"])
            for i, p in zip(indices, predictions["full"], strict=True)])),
        "request_extra": float(np.mean([
            r == bool(int(ref_rows[int(i)]["request_extra"]))
            for i, r in zip(indices, requests, strict=True)])),
    }
    result = {
        "status": "exploratory_online_image_to_prediction_validation",
        "dataset": args.dataset,
        "outer_protocol": outer_protocol,
        "official_split_number": args.split_number if args.dataset == "KTHTIPS2b" else None,
        "curet_direction": args.curet_direction,
        "n_images": len(indices),
        "train_oof_threshold": threshold,
        "device": device,
        "torch_version": torch.__version__,
        "timm_version": timm.__version__,
        "batch_size": 1,
        "warmup_per_policy": args.warmup,
        "model_load_and_classifier_fit_excluded": True,
        "source_paths_exist_and_sha256_match": len(paths),
        "adaptive_extra_fraction": float(np.mean(requests)),
        "agreement_with_precomputed_predictions": agreement,
        "source_vs_embedding_cosine": {
            "resnet50_min": float(np.min(base_cosines)),
            "resnet50_median": float(np.median(base_cosines)),
            "beitv2_final_min": float(np.min(extra_cosines)),
            "beitv2_final_median": float(np.median(extra_cosines)),
        },
        "adaptive": summary(latencies["adaptive"]),
        "full": summary(latencies["full"]),
        "mean_latency_reduction_fraction": float(
            1 - np.mean(latencies["adaptive"]) / np.mean(latencies["full"])),
        "limitations": [
            "The timing subset is used only for latency and representation identity, not external accuracy.",
            "Model loading and SVM fitting are excluded; both models stay resident.",
            "Single-image GPU inference is not batched throughput.",
        ],
        "provenance": expected,
    }
    output.mkdir(parents=True, exist_ok=True)
    tag = args.curet_direction or f"LOPO_split{args.split_number}"
    stem = prior_path.stem.replace("_resnet50_then_beitv2_base_final", "")
    path = output / f"online_sample_latency_{stem}_n{len(indices)}.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print("output", path)


if __name__ == "__main__":
    main()
