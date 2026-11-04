"""Bind the recovered pooler to another archive; two fixed rows, no timing."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixed_rows(size):
    if size < 2:
        raise ValueError("two distinct rows required")
    return [0, size - 1]


def benchmarks_active(proc=Path("/proc")):
    for path in proc.glob("[0-9]*/cmdline"):
        try:
            command = path.read_bytes().split(b"\0")
        except (OSError, PermissionError):
            continue
        if any(Path(os.fsdecode(arg)).name in {"benchmark_local_single_image.py", "benchmark_cascade_multidataset.py"}
               for arg in command if arg):
            return True
    return False


def run(args):
    import numpy as np
    from local_deit_reconstruction import verified_state_path
    from run_confirmatory_nested import canonical_labels, load_manifest, l2_rows

    cfg = json.loads(args.config.read_text())["provenance"]["arguments"]
    dataset = cfg["dataset"]
    if dataset not in {"DTD", "CUReT", "SoilOriginal", "Outex13Official1360"}:
        raise ValueError("only four pending non-KTH datasets; no new FMD retry")
    resolve = lambda p: Path(p) if Path(p).is_absolute() else ROOT / p
    base = resolve(cfg["embedding_root"]) / dataset
    embedding = base / "deit_s.npy"
    y = canonical_labels(np.load(base / "deit_s_labels.npy", allow_pickle=False))
    cache = l2_rows(np.load(embedding, allow_pickle=False))
    if cache.shape != (len(y), 384) or not np.isfinite(cache).all():
        raise ValueError("invalid archive dimensions or values")
    _, rows = load_manifest(resolve(cfg["manifest_root"]), dataset, y)
    selected = fixed_rows(len(rows))
    images = [resolve(rows[i].get("source_path") or rows[i]["path"]) for i in selected]
    for i, path in zip(selected, images):
        if digest(path) != (rows[i].get("source_sha256") or rows[i].get("sha256")):
            raise ValueError("image source drift")
    state, evidence = verified_state_path(args.reconstruction)
    legacy = ROOT / "src/01_extract_features.py"
    if digest(legacy) != evidence["legacy_source_sha256"]:
        raise ValueError("extractor source drift")
    report = {"status": "binding_inputs_prepared", "dataset": dataset, "seed": 42,
        "row_indices": selected, "row_selection": "first and last full-manifest rows, before model execution",
        "tolerance": 1e-4, "checks": [], "physical_latency_published": False,
        "embedding_sha256": digest(embedding), "config_sha256": digest(args.config),
        "source_sha256": digest(__file__), "protocol_sha256": digest(args.protocol),
        "legacy_source_sha256": digest(legacy), "image_sha256": {str(p): digest(p) for p in images},
        "recovered_state_evidence_sha256": digest(args.reconstruction),
        "limitation": "two fixed images only; not full-library or universal vector parity; no timing; recovered pooler not pretrained"}
    if args.execute and benchmarks_active():
        raise RuntimeError("benchmark active; no GPU diagnostic launched")
    args.output.mkdir(parents=True, exist_ok=False)
    save = lambda: (args.output / "diagnostic.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    save()
    if not args.execute:
        print(json.dumps({"status": report["status"], "dataset": dataset, "row_indices": selected}))
        return
    try:
        import torch
        from PIL import Image
        from diagnose_dinov2_small_gpu_parity import compare_vectors
        from local_deit_reconstruction import load_reconstructed_deit
        torch.set_num_threads(2)
        if torch.cuda.mem_get_info()[0] < 1024**3:
            raise RuntimeError("less than 1 GiB GPU free; no fallback")
        shutil.copyfile(state, args.output / "pooler_state.pt")
        report["pooler_state_sha256"] = digest(args.output / "pooler_state.pt")
        fn = load_reconstructed_deit(args.reconstruction, "cuda")
        vectors = {}
        for i, path in zip(selected, images):
            with Image.open(path) as image:
                value = fn(image.convert("RGB"))
            report["checks"].append({"row_index": i, **compare_vectors(value, cache[i])})
            vectors[f"row{i}_online"], vectors[f"row{i}_archived"] = value, cache[i]
            save()
        np.savez_compressed(args.output / "vectors.npz", **vectors)
        report.update(status="diagnostic_complete", vectors_sha256=digest(args.output / "vectors.npz"),
                      all_rows_pass=all(c["pass"] for c in report["checks"]))
        if not report["all_rows_pass"]:
            report["requires_review"] = True
        save()
        print(json.dumps(report["checks"]))
    except Exception as exc:
        report.update(status="diagnostic_error", requires_review=True, error=f"{type(exc).__name__}: {exc}")
        save()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--reconstruction", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true", help="otherwise only prepare immutable input evidence; no model/GPU")
    args = parser.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    run(args)
