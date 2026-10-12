#!/usr/bin/env python3
"""Validate image-to-prediction timing for one exact archived Top-k cascade.

The prior JSON must come from run_adaptive_topk_cascade.py without
--derive-topk. This script refuses to report timing unless source-extracted
vectors and online predictions agree with the cached experimental artifact.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
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
sys.path.insert(0, str(REPO / "scripts"))

from run_adaptive_descriptor_pilot import margin  # noqa: E402
from run_confirmatory_nested import audit_gate, load_dataset, load_manifest, make_model  # noqa: E402
from run_topk_individual_control import outer_indices  # noqa: E402

TIMM = {
    "resnet50": "resnet50.a1_in1k",
    "beitv2_base_final": "beitv2_base_patch16_224.in1k_ft_in22k_in1k",
    "dinov2_small": "vit_small_patch14_dinov2.lvd142m",
    "dinov2": "vit_base_patch14_dinov2.lvd142m",
    "dinov2_large": "vit_large_patch14_dinov2.lvd142m",
}
HF = {"vit_b16": "google/vit-base-patch16-224"}
SOTA = {"eva02_base", "mae_base", "siglip_base"}


def load_extractor(name: str, device: str, seed: int):
    if name in SOTA:
        spec = importlib.util.spec_from_file_location(
            "sota_online_extractors", REPO / "src" / "extract_sota_2024.py")
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load SOTA extractor implementation")
        sota = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sota)
        sota.DEVICE = device
        model, transform, kind = sota.load_model_and_transform(name)

        def extract(path: Path) -> np.ndarray:
            with Image.open(path) as handle:
                tensor = transform(handle.convert("RGB")).unsqueeze(0).to(device)
            with torch.inference_mode():
                if kind == "timm":
                    vector = model(tensor)
                else:
                    result = model(pixel_values=tensor)
                    vector = (result.pooler_output if getattr(result, "pooler_output", None)
                              is not None else result.last_hidden_state[:, 0])
            if device == "cuda":
                torch.cuda.synchronize()
            return vector.cpu().numpy()
        return model, extract

    if name in HF:
        from transformers import AutoImageProcessor, AutoModel
        # Historical vectors use the checkpoint's randomly initialised pooler.
        torch.manual_seed(seed)
        if device == "cuda":
            torch.cuda.manual_seed_all(seed)
        model = AutoModel.from_pretrained(HF[name]).to(device).eval()
        processor = AutoImageProcessor.from_pretrained(HF[name])

        def extract(path: Path) -> np.ndarray:
            with Image.open(path) as handle:
                inputs = processor(images=handle.convert("RGB"), return_tensors="pt").to(device)
            with torch.inference_mode():
                out = model(**inputs)
            vector = out.pooler_output if out.pooler_output is not None else out.last_hidden_state[:, 0, :]
            if device == "cuda":
                torch.cuda.synchronize()
            return vector.cpu().numpy()
        return model, extract

    model = timm.create_model(TIMM[name], pretrained=True, num_classes=0).to(device).eval()
    cfg = timm.data.resolve_model_data_config(model)
    transform = transforms.Compose([
        transforms.Resize(cfg["input_size"][1:]), transforms.CenterCrop(cfg["input_size"][1:]),
        transforms.ToTensor(), transforms.Normalize(mean=cfg["mean"], std=cfg["std"]),
    ])

    def extract(path: Path) -> np.ndarray:
        with Image.open(path) as handle:
            image = transform(handle.convert("RGB")).unsqueeze(0).to(device)
        with torch.inference_mode():
            vector = model(image)
        if device == "cuda":
            torch.cuda.synchronize()
        return vector.cpu().numpy()
    return model, extract


def l2(vector: np.ndarray) -> np.ndarray:
    return vector / np.maximum(np.linalg.norm(vector, axis=1, keepdims=True), 1e-12)


def stats(values: list[float]) -> dict:
    return {"mean_ms": float(np.mean(values)), "median_ms": float(np.median(values)),
            "p95_ms": float(np.percentile(values, 95))}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prior-json", type=Path, required=True)
    p.add_argument("--audit-root", type=Path, required=True)
    p.add_argument("--manifest-root", type=Path, required=True)
    p.add_argument("--embedding-root", type=Path, required=True)
    p.add_argument("--budget", type=float, default=0.5, choices=(0.25, 0.5, 0.75))
    p.add_argument("--n", type=int, default=30)
    p.add_argument("--warmup", type=int, default=5)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.n < 2 or args.warmup < 0:
        p.error("n must be >= 2 and warmup >= 0")

    prior_path = args.prior_json.resolve()
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    if prior.get("dataset") not in {"KTHTIPS2b", "CUReT", "FMD", "DTD", "SoilOriginal", "Outex13Official1360"} or prior.get("expensive_subset_derived_locally"):
        raise ValueError("requires an exact, non-derived primary22 cascade artifact")
    dataset = prior["dataset"]
    protocol = str(prior["protocol"])
    if dataset == "KTHTIPS2b":
        if not protocol.startswith("official") or "_inverted" not in protocol:
            raise ValueError("requires an inverted official KTH-TIPS2-b partition")
        split = int(protocol.removeprefix("official").split("_")[0])
        direction = None
    elif dataset == "CUReT":
        if not protocol.startswith("curet_half_indices:"):
            raise ValueError("requires a CUReT half-direction partition")
        split = None
        direction = protocol.split(":", 1)[1]
    elif protocol.startswith("official"):
        split = int(protocol.removeprefix("official").split("_")[0])
        direction = None
    elif protocol.startswith("stratified_group_kfold5_fold"):
        split = None
        direction = None
    else:
        raise ValueError(f"unsupported external protocol: {protocol}")
    budget_row = next((row for row in prior["budgets"]
                       if float(row["target_budget"]) == args.budget), None)
    if budget_row is None:
        raise ValueError("requested budget missing from prior artifact")

    audit_root, manifest_root, embedding_root = (x.resolve() for x in
        (args.audit_root, args.manifest_root, args.embedding_root))
    audit_gate(audit_root, dataset)
    cache, y = load_dataset(REPO, dataset, embedding_root=embedding_root)
    groups, rows = load_manifest(manifest_root, dataset, y)
    train, test = outer_indices(dataset, int(prior["seed"]), int(prior["outer_fold"]),
                                y, groups, rows, split, direction, dataset == "KTHTIPS2b")
    cheap = prior["cheap_blocks"]
    expensive = prior["expensive_blocks"]
    unsupported = (set(cheap) | set(expensive)) - (TIMM.keys() | HF.keys() | SOTA)
    if unsupported:
        raise ValueError(f"online extractor not yet implemented: {sorted(unsupported)}")
    base_x = np.concatenate([cache[n] for n in cheap], axis=1)
    topk_x = np.concatenate([cache[n] for n in expensive], axis=1)
    base_clf, topk_clf = make_model(prior["classifier"], int(prior["seed"])), make_model(prior["classifier"], int(prior["seed"]))
    base_clf.fit(base_x[train], y[train]); topk_clf.fit(topk_x[train], y[train])
    threshold = float(budget_row["threshold"])

    reference_path = prior_path.with_name(prior_path.stem + "_per_sample.csv")
    with reference_path.open(newline="", encoding="utf-8") as handle:
        reference = {(float(r["budget"]), int(r["row_id"])): r for r in csv.DictReader(handle)}
    indices = test[np.linspace(0, len(test) - 1, min(args.n, len(test)), dtype=int)]
    paths = []
    for idx in indices:
        row = rows[int(idx)]
        path = Path(row.get("source_path") or row["path"])
        path = path if path.is_absolute() else REPO / path
        if not path.is_file():
            raise FileNotFoundError(path)
        if (args.budget, int(idx)) not in reference:
            raise ValueError(f"missing cached reference for row {idx}")
        paths.append(path)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    extractors = {name: load_extractor(name, device, int(prior["seed"]))[1]
                  for name in dict.fromkeys(cheap + expensive)}
    for i in range(args.warmup):
        for name in extractors:
            extractors[name](paths[i % len(paths)])

    def route(path: Path, force_topk: bool):
        if device == "cuda":
            torch.cuda.synchronize()
        began = time.perf_counter()
        # A standalone Top-k baseline must not pay for the cheap classifier.
        # Otherwise the measured saving of the cascade is overstated.
        base_vectors = [] if force_topk else [l2(extractors[name](path)) for name in cheap]
        base_by_name = {} if force_topk else dict(zip(cheap, base_vectors, strict=True))
        online_base = None if force_topk else np.concatenate(base_vectors, axis=1)
        request = force_topk or bool(margin(base_clf, online_base)[0] <= threshold)
        if request:
            topk_vectors = [base_by_name[name] if name in base_by_name
                            else l2(extractors[name](path)) for name in expensive]
            online_topk = np.concatenate(topk_vectors, axis=1)
            pred = int(topk_clf.predict(online_topk)[0])
        else:
            topk_vectors = []
            pred = int(base_clf.predict(online_base)[0])
        if device == "cuda":
            torch.cuda.synchronize()
        return pred, request, (time.perf_counter() - began) * 1000.0, base_vectors, topk_vectors

    adaptive_latencies, full_latencies = [], []
    request_flags, prediction_match, full_match, vector_cosines, observed_requests, sample_rows = [], [], [], [], [], []
    request_disagreements = []
    for position, (idx, path) in enumerate(zip(indices, paths, strict=True)):
        order = (("adaptive", False), ("full", True)) if position % 2 == 0 else (("full", True), ("adaptive", False))
        measured = {name: route(path, force) for name, force in order}
        pred, request, latency, base_vectors, topk_vectors = measured["adaptive"]
        full_pred, _, full_latency, full_base, full_topk = measured["full"]
        adaptive_latencies.append(latency); full_latencies.append(full_latency); observed_requests.append(request)
        ref = reference[(args.budget, int(idx))]
        request_flags.append(request == bool(int(ref["request_extra"])))
        if not request_flags[-1]:
            request_disagreements.append({"row_id": int(idx),
                                          "cached_margin": float(ref["margin"]),
                                          "threshold": threshold,
                                          "online_margin": float(margin(base_clf, np.concatenate(base_vectors, axis=1))[0])})
        prediction_match.append(pred == int(ref["adaptive_pred"]))
        full_match.append(full_pred == int(ref["topk_pred"]))
        sample_rows.extend([
            {"row_id": int(idx), "route": "adaptive", "latency_ms": latency,
             "prediction": pred, "request_extra": int(request)},
            {"row_id": int(idx), "route": "topk_always", "latency_ms": full_latency,
             "prediction": full_pred, "request_extra": 1},
        ])
        for name, vector in zip(cheap, base_vectors, strict=True):
            vector_cosines.append(float(np.sum(vector[0] * cache[name][int(idx)])))
        for name, vector in zip(expensive, full_topk, strict=True):
            vector_cosines.append(float(np.sum(vector[0] * cache[name][int(idx)])))

    agreement = {"request_decision": float(np.mean(request_flags)),
                 "adaptive_prediction": float(np.mean(prediction_match)),
                 "topk_prediction": float(np.mean(full_match)),
                 "min_source_cache_cosine": float(np.min(vector_cosines))}
    if (any(agreement[key] != 1.0 for key in
            ("request_decision", "adaptive_prediction", "topk_prediction"))
            or agreement["min_source_cache_cosine"] < 0.999):
        raise RuntimeError(f"online agreement failed: {agreement}; request disagreements: {request_disagreements}")
    result = {"status": "exploratory_online_topk_cascade_validation", "dataset": dataset,
              "protocol": protocol, "budget": args.budget, "n_images": len(indices), "device": device,
              "cheap_blocks": cheap, "expensive_blocks": expensive,
              "topk_always_baseline": "standalone Top-k extraction; cheap stage skipped",
              "model_load_and_classifier_fit_excluded": True, "warmup": args.warmup,
              "observed_escalation_fraction": float(np.mean(observed_requests)),
              "online_adaptive": stats(adaptive_latencies), "online_topk_always": stats(full_latencies),
              "mean_latency_reduction_fraction": float(1 - np.mean(adaptive_latencies) / np.mean(full_latencies)),
              "agreement": agreement,
              "limitations": ["One external partition and deterministic timing subset.",
                              "Model loading and classifier fitting are excluded.",
                              "This validates online routing latency, not external accuracy."],
              "prior": str(prior_path)}
    args.output.mkdir(parents=True, exist_ok=True)
    out = args.output / f"online_{prior_path.stem}_q{args.budget:.2f}_n{len(indices)}.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with out.with_name(out.stem + "_per_image.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0]))
        writer.writeheader(); writer.writerows(sample_rows)
    print(json.dumps(result, indent=2)); print("output", out)


if __name__ == "__main__":
    main()
