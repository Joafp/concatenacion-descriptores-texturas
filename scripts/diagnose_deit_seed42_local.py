"""Reconstruct the original seeded DeiT loader, without altering the archive."""
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


def run(args):
    import numpy as np
    import torch
    from diagnose_dinov2_small_gpu_parity import compare_vectors
    from reextract_confirmatory_embeddings import load_legacy_extractors
    from run_confirmatory_nested import load_dataset, load_manifest

    torch.set_num_threads(2)
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"status": "preflight", "physical_latency_published": False,
        "seed": 42, "tolerance": 1e-4, "checks": [],
        "authorization": "Reconstruct original seed-42 state; integrate only if parity passes",
        "source_sha256": digest(__file__), "protocol_sha256": digest(args.protocol)}

    def save():
        (args.output / "diagnostic.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    save()
    try:
        failed = json.loads(args.prior.read_text())
        status = json.loads((args.run / "status.json").read_text())
        cfg_path = Path(status["provenance"]["arguments"]["reference_config"])
        cfg_path = cfg_path if cfg_path.is_absolute() else ROOT / cfg_path
        cfg = json.loads(cfg_path.read_text())["provenance"]["arguments"]

        def resolve(value):
            p = Path(value)
            return p if p.is_absolute() else ROOT / p

        cache, y = load_dataset(ROOT, status["dataset"], resolve(cfg["embedding_root"]))
        _, rows = load_manifest(resolve(cfg["manifest_root"]), status["dataset"], y)
        metadata_path = resolve(cfg["embedding_root"]) / status["dataset"] / "deit_s_metadata.json"
        metadata = json.loads(metadata_path.read_text())
        embedding = metadata_path.with_name("deit_s.npy")
        if metadata["seed"] != 42 or digest(embedding) != metadata["embedding_sha256"]:
            raise ValueError("original seed or embedding hash mismatch")
        selected = failed["row_indices"]
        paths = []
        for idx in selected:
            row = rows[idx]
            path = resolve(row.get("source_path") or row["path"])
            if digest(path) != (row.get("source_sha256") or row.get("sha256")):
                raise ValueError("source image hash mismatch")
            paths.append(str(path))
        free, total = torch.cuda.mem_get_info()
        if free < 1024**3:
            raise RuntimeError("less than 1 GiB GPU free; do not disturb existing activity")
        report.update(status="inputs_frozen_before_loading", row_indices=selected,
            original_metadata_sha256=digest(metadata_path), embedding_sha256=digest(embedding),
            prior_sha256=digest(args.prior), image_sha256={p: digest(p) for p in paths},
            legacy_source_sha256=digest(ROOT / "src/01_extract_features.py"),
            gpu_free_before_bytes=free, gpu_total_bytes=total,
            gpu_contention="shared; numerical diagnosis only", torch_version=torch.__version__)
        save()
        legacy = load_legacy_extractors()
        # Exactly the original ordering: set all seeds, then construct processor/model.
        legacy.set_seed(42)
        ext = legacy.get_extractor("deit_s", device="cuda")
        state = {k: v.detach().cpu() for k, v in ext.model.state_dict().items() if "pooler" in k}
        torch.save(state, args.output / "pooler_state.pt")
        report["pooler_state_sha256"] = digest(args.output / "pooler_state.pt")
        report["pooler_parameter_names"] = sorted(state)
        values = ext.extract(paths, batch_size=1)
        vectors = {}
        for idx, value in zip(selected, values):
            vector = np.asarray(value, dtype=np.float32).ravel()
            vector /= max(float(np.linalg.norm(vector)), 1e-12)
            check = {"row_index": idx, **compare_vectors(vector, cache["deit_s"][idx])}
            report["checks"].append(check)
            vectors[f"row{idx}_seed42"] = vector
            vectors[f"row{idx}_archived"] = cache["deit_s"][idx]
            print(json.dumps(check), flush=True)
            save()
        np.savez_compressed(args.output / "vectors.npz", **vectors)
        report.update(status="diagnostic_complete", all_rows_pass=all(c["pass"] for c in report["checks"]),
            vectors_sha256=digest(args.output / "vectors.npz"),
            limitation="two fixed FMD images; not general parity or timing; reconstructed pooler is not pretrained")
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
