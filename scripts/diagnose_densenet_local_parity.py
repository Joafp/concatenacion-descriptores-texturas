"""Bounded DenseNet numerical diagnosis: original batches versus single images.

Four configurations fixed before execution; never relax archive tolerance.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args):
    import numpy as np
    import torch
    from PIL import Image
    from diagnose_dinov2_small_gpu_parity import compare_vectors
    from reextract_confirmatory_embeddings import load_legacy_extractors
    from run_confirmatory_nested import load_dataset

    torch.set_num_threads(2)
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"status": "preflight", "tolerance": 1e-4, "physical_latency_published": False,
        "source_sha256": digest(__file__), "protocol_sha256": digest(args.protocol), "checks": []}

    def save():
        (args.output / "diagnostic.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    save()
    try:
        prior = json.loads(args.prior.read_text())
        if "densenet121" not in prior.get("error", ""):
            raise ValueError("expected DenseNet parity failure")
        base = ROOT / "embeddings_confirmatory/FMD"
        metadata_path = base / "densenet121_metadata.json"
        metadata = json.loads(metadata_path.read_text())
        manifest = Path(metadata["manifest"])
        if digest(manifest) != metadata["manifest_sha256"] or digest(base / "densenet121.npy") != metadata["embedding_sha256"]:
            raise ValueError("original archive or manifest hash mismatch")
        with manifest.open() as handle:
            rows = list(csv.DictReader(handle))
        if [int(r["row_id"]) for r in rows] != list(range(len(rows))):
            raise ValueError("original row order is not contiguous")
        selected = prior["row_indices"]
        batch_indices = {idx: list(range((idx // 16) * 16, min((idx // 16) * 16 + 16, len(rows)))) for idx in selected}
        images, hashes = {}, {}
        for idx in sorted({i for indices in batch_indices.values() for i in indices}):
            path = Path(rows[idx]["path"])
            hashes[str(path)] = digest(path)
            with Image.open(path) as image:
                images[idx] = image.convert("RGB").copy()
        for idx in selected:
            path = str(Path(rows[idx]["path"]))
            if hashes[path] != prior["image_sha256"][path]:
                raise ValueError("fixed diagnosis image mismatch")
        free, total = torch.cuda.mem_get_info()
        if free < 2 * 1024**3:
            raise RuntimeError("less than 2 GiB GPU free; preserve unrelated activity")
        cache, _ = load_dataset(ROOT, "FMD", ROOT / "embeddings_confirmatory")
        default_matmul = torch.backends.cuda.matmul.allow_tf32
        default_cudnn = torch.backends.cudnn.allow_tf32
        report.update(status="inputs_frozen", row_indices=selected, original_batch_indices=batch_indices,
            metadata_sha256=digest(metadata_path), manifest_sha256=digest(manifest), image_sha256=hashes,
            gpu_free_before_bytes=free, gpu_total_bytes=total, torch_version=torch.__version__,
            default_precision={"matmul_allow_tf32": default_matmul, "cudnn_allow_tf32": default_cudnn,
                "cudnn_benchmark": torch.backends.cudnn.benchmark, "cudnn_deterministic": torch.backends.cudnn.deterministic},
            configurations=["default_single", "default_original_batch16", "no_tf32_single", "no_tf32_original_batch16"])
        save()
        legacy = load_legacy_extractors()
        legacy.set_seed(42)
        ext = legacy.get_extractor("densenet121", device="cuda")
        vectors = {}
        for mode in report["configurations"]:
            no_tf32 = mode.startswith("no_tf32")
            torch.backends.cuda.matmul.allow_tf32 = False if no_tf32 else default_matmul
            torch.backends.cudnn.allow_tf32 = False if no_tf32 else default_cudnn
            for idx in selected:
                indices = batch_indices[idx] if "batch16" in mode else [idx]
                tensor = torch.stack([ext.transform(images[i]) for i in indices]).to("cuda")
                with torch.inference_mode():
                    value = ext.model(tensor)[indices.index(idx)].cpu().numpy().ravel().astype(np.float32)
                value /= max(float(np.linalg.norm(value)), 1e-12)
                check = {"mode": mode, "row_index": idx, **compare_vectors(value, cache["densenet121"][idx])}
                report["checks"].append(check)
                vectors[f"{mode}_row{idx}"] = value
                print(json.dumps(check), flush=True)
                save()
        torch.backends.cuda.matmul.allow_tf32 = default_matmul
        torch.backends.cudnn.allow_tf32 = default_cudnn
        np.savez_compressed(args.output / "vectors.npz", **vectors)
        report.update(status="diagnostic_complete", vectors_sha256=digest(args.output / "vectors.npz"),
            configuration_passes={mode: all(c["pass"] for c in report["checks"] if c["mode"] == mode) for mode in report["configurations"]},
            limitation="two fixed rows, four predefined numeric modes; no timing or full-library parity")
        save()
    except Exception as exc:
        report.update(status="diagnostic_error", error=f"{type(exc).__name__}: {exc}")
        save()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    run(args)
