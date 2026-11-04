"""Authorized CLS parity diagnosis; no changes to archived embeddings or heads."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_safe(value):
    """Transformers loading-info keys can be sets in newer local runtimes."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, set):
        return [json_safe(v) for v in sorted(value, key=str)]
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def run(args):
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoModel, AutoImageProcessor
    from diagnose_dinov2_small_gpu_parity import compare_vectors
    from run_confirmatory_nested import load_dataset, load_manifest

    torch.set_num_threads(2)
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"status": "preflight", "physical_latency_published": False,
        "authorization": "Diagnose CLS; correct online adapter only if original tolerance passes",
        "tolerance": 1e-4, "tap": "last_hidden_state[:,0,:]", "device": "cuda",
        "source_sha256": digest(__file__), "protocol_sha256": digest(args.protocol), "checks": []}

    def save():
        (args.output / "diagnostic.json").write_text(json.dumps(json_safe(report), indent=2, allow_nan=False) + "\n")

    save()
    try:
        failed = json.loads(args.prior.read_text())
        if failed["status"] != "blocked_online_parity_or_runtime" or "deit_s" not in failed.get("error", ""):
            raise ValueError("expected archived DeiT parity failure")
        quality = json.loads((args.run / "status.json").read_text())
        cfg_path = Path(quality["provenance"]["arguments"]["reference_config"])
        cfg_path = cfg_path if cfg_path.is_absolute() else ROOT / cfg_path
        cfg = json.loads(cfg_path.read_text())["provenance"]["arguments"]

        def resolve(value):
            p = Path(value)
            return p if p.is_absolute() else ROOT / p

        cache, y = load_dataset(ROOT, quality["dataset"], resolve(cfg["embedding_root"]))
        _, rows = load_manifest(resolve(cfg["manifest_root"]), quality["dataset"], y)
        selected = failed["row_indices"]
        images = []
        hashes = {}
        for idx in selected:
            row = rows[idx]
            path = resolve(row.get("source_path") or row["path"])
            if digest(path) != (row.get("source_sha256") or row.get("sha256")):
                raise ValueError("image hash mismatch")
            hashes[str(path)] = digest(path)
            with Image.open(path) as image:
                images.append(image.convert("RGB").copy())
        free, total = torch.cuda.mem_get_info()
        if free < 1024**3:
            raise RuntimeError("less than 1 GiB GPU free; preserve unrelated activity")
        report.update(status="inputs_frozen_before_forward", row_indices=selected,
            image_sha256=hashes, prior_sha256=digest(args.prior),
            embedding_sha256=digest(resolve(cfg["embedding_root"]) / quality["dataset"] / "deit_s.npy"),
            gpu_free_before_bytes=free, gpu_total_bytes=total,
            gpu_contention="shared; numeric checks only", transformers_version=__import__("transformers").__version__)
        save()
        name = "facebook/deit-small-patch16-224"
        processor = AutoImageProcessor.from_pretrained(name, local_files_only=True)
        # Do not instantiate an untrained pooler. CLS does not use it.
        model, loading = AutoModel.from_pretrained(name, local_files_only=True,
            add_pooling_layer=False, output_loading_info=True)
        report["loading_info"] = {k: loading.get(k, []) for k in ["missing_keys", "unexpected_keys", "mismatched_keys"]}
        if loading.get("missing_keys") or loading.get("mismatched_keys"):
            raise ValueError("backbone weights missing or mismatched even with pooling disabled")
        model = model.to("cuda").eval()
        vectors = {}
        for idx, image in zip(selected, images):
            inputs = processor(images=[image], return_tensors="pt").to("cuda")
            with torch.inference_mode():
                output = model(**inputs)
                vector = output.last_hidden_state[:, 0, :].cpu().numpy().ravel().astype(np.float32)
            vector /= max(float(np.linalg.norm(vector)), 1e-12)
            target = cache["deit_s"][idx]
            check = {"row_index": idx, **compare_vectors(vector, target)}
            report["checks"].append(check)
            vectors[f"row{idx}_cls"] = vector
            vectors[f"row{idx}_archived"] = target
            print(json.dumps(check), flush=True)
            save()
        np.savez_compressed(args.output / "vectors.npz", **vectors)
        report.update(status="diagnostic_complete", all_rows_pass=all(c["pass"] for c in report["checks"]),
            vectors_sha256=digest(args.output / "vectors.npz"),
            limitation="two fixed FMD images only; no general parity or latency claim")
        save()
    except Exception as exc:
        report.update(status="diagnostic_error", error=f"{type(exc).__name__}: {exc}")
        save()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    run(args)
