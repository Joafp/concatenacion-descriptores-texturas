"""Authorized extractor-only GPU parity diagnostic; no quality fits or timings."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
TOLERANCE = 1e-4
CONDITIONS = ("FMD_s42", "Outex_s123")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare_vectors(online, target):
    online = np.asarray(online, dtype=np.float32).ravel()
    target = np.asarray(target, dtype=np.float32).ravel()
    same_shape = online.shape == target.shape
    finite = bool(np.isfinite(online).all() and np.isfinite(target).all())
    result = {"same_shape": same_shape, "finite": finite,
              "tolerance": TOLERANCE, "pass": False}
    if same_shape and finite:
        delta = online.astype(np.float64) - target.astype(np.float64)
        maximum = float(np.max(np.abs(delta)))
        result.update(max_abs_error=maximum, mean_abs_error=float(np.abs(delta).mean()),
            l2_error=float(np.linalg.norm(delta)),
            cosine=float(np.dot(online.astype(np.float64), target.astype(np.float64)) /
                         max(np.linalg.norm(online.astype(np.float64)) * np.linalg.norm(target.astype(np.float64)), 1e-30)),
            **{"pass": maximum <= TOLERANCE})
    return result


def run(output):
    import importlib.metadata
    import torch
    from PIL import Image
    from benchmark_cascade_multidataset import extractor
    from run_confirmatory_nested import load_manifest

    output.mkdir(parents=True, exist_ok=False)
    protocol = ROOT / "docs/fsc_tex/DIAGNOSTICO_PARIDAD_GPU_2026-10-26.md"
    report = {"schema": "extractor-gpu-parity-diagnostic/1", "status": "preflight",
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "authorization": "Sí, diagnosticar paridad en GPU",
        "scope": "DINOv2-small only; same first two frozen pilot rows per condition; no training or quality experiment rerun",
        "fixed_tolerance": TOLERANCE, "physical_latency_published": False,
        "quality_experiments_repeated": False, "original_outputs_modified": False,
        "protocol_sha256": digest(protocol), "script_sha256": digest(__file__),
        "packages": {name: importlib.metadata.version(name) for name in ("torch", "timm", "transformers", "numpy")},
        "input_sha256": {}, "results": []}
    def save():
        (output / "diagnostic.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    save()
    try:
        assert torch.cuda.is_available(), "CUDA is unavailable"
        free, total = torch.cuda.mem_get_info()
        report.update(device=torch.cuda.get_device_name(), gpu_free_before_bytes=free,
            gpu_total_bytes=total, gpu_contention="present; no timing inference allowed",
            numerical_settings={"matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
                "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
                "float32_matmul_precision": torch.get_float32_matmul_precision()})
        assert free >= 512 * 1024**2, "Less than 512 MiB free; do not disturb unrelated GPU activity"
        samples = []
        for condition in CONDITIONS:
            prior_path = ROOT / f"results/exploratory/integration_v14/physical_routes_20261026/{condition}/status.json"
            prior = json.loads(prior_path.read_text())
            assert prior["status"] == "blocked_parity_or_runtime" and "dinov2_small" in prior["error"]
            suite = ROOT / f"results/exploratory/integration_v11/replication_20261026/{condition}"
            metadata_path = suite / "paired/metadata.json"
            metadata = json.loads(metadata_path.read_text())
            cfg = metadata["provenance"]["arguments"]
            def resolve(value):
                path = Path(value)
                return path if path.is_absolute() else ROOT / path
            embedding_dir = resolve(cfg["embedding_root"]) / metadata["dataset"]
            label_path = embedding_dir / "dinov2_small_labels.npy"
            embedding_path = embedding_dir / "dinov2_small.npy"
            labels = np.load(label_path, allow_pickle=False)
            cache = np.load(embedding_path, allow_pickle=False)
            _, rows = load_manifest(resolve(cfg["manifest_root"]), metadata["dataset"], labels)
            for path in (prior_path, metadata_path, embedding_path, label_path,
                         resolve(cfg["manifest_root"]) / "sample_manifests" / f"{metadata['dataset']}.csv"):
                report["input_sha256"][str(path.relative_to(ROOT))] = digest(path)
            for row_id in prior["rows"][:2]:
                row = rows[row_id]
                path = resolve(row.get("source_path") or row["path"])
                assert digest(path) == (row.get("source_sha256") or row.get("sha256")), path
                report["input_sha256"][str(path.relative_to(ROOT))] = digest(path)
                target = np.asarray(cache[row_id], dtype=np.float32).ravel()
                target = target / max(float(np.linalg.norm(target)), 1e-12)
                samples.append({"condition": condition, "row_index": row_id,
                                "path": path, "target": target})
        report.update(status="inputs_frozen_before_gpu_extraction",
                      frozen_rows=[{"condition": s["condition"], "row_index": s["row_index"]} for s in samples],
                      extractor_adapter_sha256=digest(ROOT / "scripts/benchmark_cascade_multidataset.py"),
                      legacy_extractor_sha256=digest(ROOT / "src/01_extract_features.py"))
        save()
        print(f"Inputs frozen; {len(samples)} rows, one DINOv2-small model on GPU, fixed tolerance {TOLERANCE}", flush=True)
        raw = extractor("dinov2_small", "cuda")
        vectors = {}
        for sample in samples:
            with Image.open(sample["path"]) as im:
                value = np.asarray(raw(im.convert("RGB")), dtype=np.float32).ravel()
            # Preserve the same second normalization used by the blocked pilot.
            value = value / max(float(np.linalg.norm(value)), 1e-12)
            metrics = compare_vectors(value, sample["target"])
            report["results"].append({"condition": sample["condition"], "row_index": sample["row_index"], **metrics})
            vectors[f"{sample['condition']}_{sample['row_index']}_gpu"] = value
            vectors[f"{sample['condition']}_{sample['row_index']}_cached"] = sample["target"]
            print(json.dumps(report["results"][-1]), flush=True)
            save()
        np.savez_compressed(output / "diagnostic_vectors.npz", **vectors)
        report.update(status="diagnostic_complete", all_rows_pass=all(r["pass"] for r in report["results"]),
            gpu_max_allocated_bytes=torch.cuda.max_memory_allocated(),
            vectors_sha256=digest(output / "diagnostic_vectors.npz"),
            limitation="Extractor-only four-row diagnostic; no proof of full-route parity, CPU cause, physical speedup or benchmark validity")
        save()
    except Exception as exc:
        report.update(status="diagnostic_runtime_error", error=f"{type(exc).__name__}: {exc}")
        save()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    run(args.output.resolve())
