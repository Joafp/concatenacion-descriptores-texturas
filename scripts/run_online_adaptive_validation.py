#!/usr/bin/env python3
"""Check actual image-to-prediction latency of the two-block exploratory router.

Loads frozen extractors once, fits SVMs only on the training side of an existing
outer fold, and routes test images using a threshold learned from inner OOF
training predictions by run_adaptive_descriptor_pilot.py.
"""

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
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from torchvision import transforms


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from run_confirmatory_nested import (  # noqa: E402
    audit_gate, load_dataset, load_manifest, make_model, official_split_indices,
)
from run_adaptive_descriptor_pilot import margin  # noqa: E402
from curet_confirmatory_protocol import curet_half_indices  # noqa: E402


MODEL_NAMES = {
    "resnet50": "resnet50.a1_in1k",
    "beitv2_base_final": "beitv2_base_patch16_224.in1k_ft_in22k_in1k",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_extractor(key: str, device: str):
    model = timm.create_model(MODEL_NAMES[key], pretrained=True, num_classes=0).to(device).eval()
    cfg = timm.data.resolve_model_data_config(model)
    transform = transforms.Compose([
        transforms.Resize(cfg["input_size"][1:]),
        transforms.CenterCrop(cfg["input_size"][1:]),
        transforms.ToTensor(),
        transforms.Normalize(mean=cfg["mean"], std=cfg["std"]),
    ])
    return model, transform


def extract(path: Path, model, transform, device: str) -> np.ndarray:
    with Image.open(path) as handle:
        tensor = transform(handle.convert("RGB")).unsqueeze(0).to(device)
    with torch.inference_mode():
        vector = model(tensor)
    if device == "cuda":
        torch.cuda.synchronize()
    x = vector.cpu().numpy().astype(np.float32, copy=False)
    return x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)


def timed_predict(path: Path, policy: str, base_extractor, extra_extractor,
                  base_clf, full_clf, threshold: float, device: str):
    if device == "cuda":
        torch.cuda.synchronize()
    began = time.perf_counter()
    base_x = extract(path, *base_extractor, device)
    need_extra = policy == "full" or bool(margin(base_clf, base_x)[0] <= threshold)
    if need_extra:
        extra_x = extract(path, *extra_extractor, device)
        predicted = int(full_clf.predict(np.concatenate((base_x, extra_x), axis=1))[0])
    else:
        predicted = int(base_clf.predict(base_x)[0])
    if device == "cuda":
        torch.cuda.synchronize()
    return predicted, need_extra, (time.perf_counter() - began) * 1000.0


def summary(values: list[float]) -> dict:
    return {
        "mean_ms": float(np.mean(values)),
        "median_ms": float(np.median(values)),
        "p95_ms": float(np.percentile(values, 95)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="FMD")
    parser.add_argument("--embedding-root", type=Path, default=REPO / "embeddings_confirmatory")
    parser.add_argument("--manifest-root", type=Path, default=REPO / "results" / "confirmatory")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outer-fold", type=int, default=0, choices=range(5))
    parser.add_argument("--official-split", type=int,
                        help="Use manifest official split (split number; 1 selects official_split when present).")
    parser.add_argument("--curet-direction", choices=("a_to_b", "b_to_a"))
    parser.add_argument("--prior-json", type=Path)
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--budget", type=float, default=0.5)
    parser.add_argument("--output", type=Path,
                        default=REPO / "results" / "exploratory" / "adaptive_descriptor_pilot")
    args = parser.parse_args()
    if args.n < 2 or args.warmup < 0 or not 0 < args.budget < 1:
        parser.error("n must be >= 2, warmup >= 0, and budget in (0,1)")
    split_tag = (f"official{args.official_split}" if args.official_split is not None else
                 (args.curet_direction or f"f{args.outer_fold}"))
    prior = args.prior_json or (args.output / (f"{args.dataset}_svm_s{args.seed}_{split_tag}"
                           "_resnet50_then_beitv2_base_final.json"))
    pilot = json.loads(prior.read_text())
    if "budgets" in pilot:
        matching = [row for row in pilot["budgets"]
                    if row.get("target_extra_fraction", row.get("target_budget")) == args.budget]
        if len(matching) != 1:
            raise ValueError("Required pre-specified budget is absent")
        threshold = float(matching[0].get("train_oof_margin_threshold", matching[0].get("threshold")))
    else:
        if pilot.get("target_extra_fraction") != args.budget:
            raise ValueError("Official-split pilot budget does not match requested budget")
        threshold = float(pilot["train_oof_margin_threshold"])

    audit_gate(args.manifest_root, args.dataset)
    cache, y = load_dataset(REPO, args.dataset, embedding_root=args.embedding_root)
    groups, rows = load_manifest(args.manifest_root, args.dataset, y)
    provenance = pilot.get("provenance")
    if provenance:
        embedding_dataset = {"KTHTIPS2b": "KTH-TIPS2-b"}.get(args.dataset, args.dataset)
        embedding_dir = args.embedding_root / embedding_dataset
        current_hashes = {
            "audit_csv_sha256": sha256(args.manifest_root / "data_audit.csv"),
            "manifest_csv_sha256": sha256(args.manifest_root / "sample_manifests" / f"{args.dataset}.csv"),
            "resnet50_npy_sha256": sha256(embedding_dir / "resnet50.npy"),
            "beitv2_base_final_npy_sha256": sha256(embedding_dir / "beitv2_base_final.npy"),
            "resnet50_labels_sha256": sha256(embedding_dir / "resnet50_labels.npy"),
            "beitv2_base_final_labels_sha256": sha256(embedding_dir / "beitv2_base_final_labels.npy"),
        }
        provenance_aliases = {
                          "audit_csv_sha256": "audit_sha256", "manifest_csv_sha256": "manifest_sha256",
                          "resnet50_npy_sha256": "resnet50_sha256",
                          "beitv2_base_final_npy_sha256": "beitv2_final_sha256",
                          "resnet50_labels_sha256": "resnet50_labels_sha256",
                          "beitv2_base_final_labels_sha256": "beitv2_labels_sha256",
                      }
        mismatches = [key for key, value in current_hashes.items()
                      if (key in provenance or provenance_aliases[key] in provenance)
                      and provenance.get(key, provenance.get(provenance_aliases[key])) != value]
        if mismatches:
            raise ValueError(f"Pilot provenance no longer matches inputs: {mismatches}")
    if args.curet_direction is not None:
        if args.dataset != "CUReT" or args.official_split is not None:
            raise ValueError("--curet-direction requires CUReT and excludes --official-split")
        train, test = curet_half_indices(rows, args.curet_direction)
    elif args.official_split is not None:
        train, test = official_split_indices(rows, args.official_split)
    else:
        split = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=args.seed)
        train, test = list(split.split(np.zeros(len(y)), y, groups))[args.outer_fold]
    if set(groups[train]).intersection(groups[test]):
        raise AssertionError("Outer group leakage")
    base_clf, full_clf = make_model("svm", args.seed), make_model("svm", args.seed)
    base_x = cache["resnet50"]
    full_x = np.concatenate((base_x, cache["beitv2_base_final"]), axis=1)
    base_clf.fit(base_x[train], y[train])
    full_clf.fit(full_x[train], y[train])

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
    base_extractor = load_extractor("resnet50", device)
    extra_extractor = load_extractor("beitv2_base_final", device)
    for i in range(args.warmup):
        for policy in ("adaptive", "full"):
            timed_predict(paths[i % len(paths)], policy, base_extractor, extra_extractor,
                          base_clf, full_clf, threshold, device)

    elapsed = {"adaptive": [], "full": []}
    predictions = {"adaptive": [], "full": []}
    requests = []
    for i, path in enumerate(paths):
        # Alternate execution order to reduce systematic warm-cache advantage.
        order = ("adaptive", "full") if i % 2 == 0 else ("full", "adaptive")
        observed = {}
        for policy in order:
            observed[policy] = timed_predict(path, policy, base_extractor, extra_extractor,
                                             base_clf, full_clf, threshold, device)
        for policy in ("adaptive", "full"):
            pred, _, milliseconds = observed[policy]
            elapsed[policy].append(milliseconds)
            predictions[policy].append(pred)
        requests.append(bool(observed["adaptive"][1]))
    per_sample = prior.with_name(prior.stem + "_per_sample.csv")
    with per_sample.open(newline="") as handle:
        reference_rows = list(csv.DictReader(handle))
    reference = {
        int(row["row_id"]): row for row in reference_rows
        if "budget" not in row or float(row["budget"]) == args.budget
    }
    if any(int(index) not in reference for index in indices):
        raise AssertionError("Timed sample missing from cached pilot")
    agreement = {
        "adaptive_prediction": float(np.mean([
            prediction == int(reference[int(index)].get("adaptive_prediction", reference[int(index)].get("adaptive_pred")))
            for index, prediction in zip(indices, predictions["adaptive"])
        ])),
        "full_prediction": float(np.mean([
            prediction == int(reference[int(index)].get("full_prediction", reference[int(index)].get("full_pred")))
            for index, prediction in zip(indices, predictions["full"])
        ])),
        "request_extra": float(np.mean([
            int(request) == int(reference[int(index)]["request_extra"])
            for index, request in zip(indices, requests)
        ])),
    }
    labels = np.unique(y)
    result = {
        "status": "exploratory_online_image_to_prediction_validation",
        "dataset": args.dataset,
        "outer_fold": (None if args.official_split is not None else args.outer_fold),
        "official_split": args.official_split,
        "outer_protocol": ("manifest-defined official split" if args.official_split is not None
                           else "StratifiedGroupKFold"),
        "n_images": len(indices),
        "budget": args.budget,
        "train_oof_threshold": threshold,
        "device": device,
        "batch_size": 1,
        "warmup_per_policy": args.warmup,
        "model_load_and_classifier_fit_excluded": True,
        "adaptive_extra_fraction": float(np.mean(requests)),
        "agreement_with_precomputed_pilot": agreement,
        "adaptive": {
            **summary(elapsed["adaptive"]),
            "macro_f1_on_timing_subset": float(f1_score(y[indices], predictions["adaptive"],
                                                    labels=labels, average="macro", zero_division=0)),
            "accuracy_on_timing_subset": float(accuracy_score(y[indices], predictions["adaptive"])),
        },
        "full": {
            **summary(elapsed["full"]),
            "macro_f1_on_timing_subset": float(f1_score(y[indices], predictions["full"],
                                                    labels=labels, average="macro", zero_division=0)),
            "accuracy_on_timing_subset": float(accuracy_score(y[indices], predictions["full"])),
        },
        "mean_latency_reduction_fraction": float(1 - np.mean(elapsed["adaptive"]) /
                                                 np.mean(elapsed["full"])),
        "limitations": [
            "Timing subset is not a new held-out accuracy benchmark.",
            "Both models stay resident; model loading and classifier fitting are excluded.",
            "Single-image GPU inference differs from batched throughput.",
        ],
    }
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / (f"online_latency_{args.dataset}_s{args.seed}_{split_tag}"
                          f"_n{len(indices)}_budget{args.budget}.json")
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
