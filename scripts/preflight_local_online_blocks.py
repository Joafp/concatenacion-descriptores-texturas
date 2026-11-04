"""Validate image-to-feature parity with one resident deep extractor at a time.

This is a numerical preflight on fixed external rows, not a latency benchmark.
"""
import argparse
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args):
    import joblib
    import numpy as np
    import torch
    from PIL import Image
    from scipy import sparse
    from sklearn.decomposition import TruncatedSVD
    from sklearn.preprocessing import normalize
    from benchmark_cascade_multidataset import extractor
    from diagnose_dinov2_small_gpu_parity import compare_vectors
    from ensemble_scoring import decision_scores
    from frozen_ensemble_route import evaluate_route
    from run_confirmatory_nested import load_dataset, load_manifest
    from run_rescue_nested_selection import load_existing_ngram

    torch.set_num_threads(2)
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"status": "preflight", "physical_latency_published": False,
        "device": args.device, "tolerance": 1e-4, "script_sha256": digest(__file__),
        "protocol_sha256": digest(args.protocol), "blocks": [],
        "model_residency": "one extractor at a time; no timing inference"}

    def save():
        (args.output / "status.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    save()
    try:
        status = json.loads((args.run / "status.json").read_text())
        if status["status"] != "external_quality_complete_timing_pending":
            raise ValueError("quality run incomplete")
        cfg_path = Path(status["provenance"]["arguments"]["reference_config"])
        cfg_path = cfg_path if cfg_path.is_absolute() else ROOT / cfg_path
        cfg = json.loads(cfg_path.read_text())["provenance"]["arguments"]

        def resolve(value):
            p = Path(value)
            return p if p.is_absolute() else ROOT / p

        heads = joblib.load(args.run / "fitted_heads.joblib")
        cache, y = load_dataset(ROOT, status["dataset"], resolve(cfg["embedding_root"]))
        _, rows = load_manifest(resolve(cfg["manifest_root"]), status["dataset"], y)
        train, test = heads["training_indices"], heads["external_indices"]
        selected = test[np.linspace(0, len(test) - 1, 2, dtype=int)]
        paths = {}
        for idx in selected:
            row = rows[int(idx)]
            p = resolve(row.get("source_path") or row["path"])
            if digest(p) != (row.get("source_sha256") or row.get("sha256")):
                raise ValueError("image hash mismatch")
            paths[int(idx)] = p
        names = sorted({n for recipe in heads["recipes"].values() for m in recipe["members"] for n in m}
                       | {recipe["base"] for recipe in heads["recipes"].values() if recipe.get("base")})
        report.update(status="inputs_frozen", row_indices=selected.tolist(), required_blocks=names,
            quality_status_sha256=digest(args.run / "status.json"),
            frozen_decisions_sha256=digest(args.run / "frozen_decisions.json"),
            image_sha256={str(p): digest(p) for p in paths.values()},
            adapter_sha256=digest(ROOT / "scripts/benchmark_cascade_multidataset.py"))
        if args.device == "cuda":
            free, total = torch.cuda.mem_get_info()
            report.update(gpu_free_before_bytes=free, gpu_total_bytes=total,
                gpu_name=torch.cuda.get_device_name(), contention="shared; no latency conclusions")
            if free < 2 * 1024**3:
                raise RuntimeError("less than 2 GiB free; do not disturb existing GPU work")
        save()
        spec = importlib.util.spec_from_file_location("local_parity_legacy", ROOT / "src/01_extract_features.py")
        legacy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(legacy)
        ng, _ = load_existing_ngram(rows, resolve(cfg["ngram_count_cache"]), 256, 8192, cfg["seed"])
        _, ng_selected, _ = ng.transform(train, selected)
        vectors = {int(i): {} for i in selected}
        for name in names:
            print(f"Online parity: {name}", flush=True)
            raw = None
            ext = None
            if name == ng.name:
                from run_rgb_ngram_outex13_official import count_image
                svd = TruncatedSVD(n_components=min(256, len(train) - 1, 8191), n_iter=5, random_state=cfg["seed"])
                svd.fit_transform(ng._hashed_rows(train))

                def raw(path):
                    with Image.open(path) as image:
                        keys, counts = count_image(np.asarray(image.convert("RGB"), dtype=np.uint8), "rgb_ngram_impl1")
                    bins = np.asarray(keys, dtype=np.uint64) % np.uint64(8192)
                    order = np.argsort(bins, kind="stable")
                    bins, counts = bins[order], np.asarray(counts, dtype=np.float32)[order]
                    unique, starts = np.unique(bins, return_index=True)
                    row = sparse.csr_matrix((np.add.reduceat(counts, starts), unique, [0, len(unique)]), shape=(1, 8192), dtype=np.float32)
                    return normalize(svd.transform(row).astype(np.float32), norm="l2")[0]
            elif legacy.EXTRACTORS.get(name, {}).get("type") == "classical":
                ext = legacy.get_extractor(name, device="cpu")

                def raw(path):
                    return getattr(ext, "_" + ext.method)(ext._load_gray(str(path)))
            elif name == "deit_s" and args.deit_reconstruction:
                from local_deit_reconstruction import load_reconstructed_deit, verified_state_path
                _, evidence = verified_state_path(args.deit_reconstruction)
                if evidence["embedding_sha256"] != digest(resolve(cfg["embedding_root"]) / status["dataset"] / "deit_s.npy"):
                    raise ValueError("DeiT reconstruction evidence is not bound to this embedding archive")
                report["deit_reconstruction_sha256"] = digest(args.deit_reconstruction)
                report["deit_adapter_sha256"] = digest(ROOT / "src/local_deit_reconstruction.py")
                deep = load_reconstructed_deit(args.deit_reconstruction, args.device)

                def raw(path):
                    with Image.open(path) as image:
                        return deep(image.convert("RGB"))
            else:
                deep = extractor(name, args.device)

                def raw(path):
                    with Image.open(path) as image:
                        return deep(image.convert("RGB"))
            checks = []
            for position, idx in enumerate(selected):
                value = np.asarray(raw(paths[int(idx)]), dtype=np.float32).ravel()
                value /= max(float(np.linalg.norm(value)), 1e-12)
                target = ng_selected[position] if name == ng.name else cache[name][idx]
                check = compare_vectors(value, target)
                checks.append({"row_index": int(idx), **check})
                if not check["pass"]:
                    report["blocks"].append({"block": name, "checks": checks})
                    raise ValueError(f"feature parity failed: {name}/{idx}: {check}")
                vectors[int(idx)][name] = value
            report["blocks"].append({"block": name, "checks": checks})
            save()
            del raw, ext
            if name != ng.name and legacy.EXTRACTORS.get(name, {}).get("type") != "classical":
                del deep
            gc.collect()
            if args.device == "cuda":
                torch.cuda.empty_cache()
        route_results = []
        for policy, recipe in heads["recipes"].items():
            for position, idx in enumerate(selected):
                def score(member, x):
                    model, scale = heads["models"][member]
                    return decision_scores(model, x, scale)

                online = evaluate_route(recipe, lambda n: vectors[int(idx)][n], score, heads["labels"])
                cached = evaluate_route(recipe, lambda n: ng_selected[position] if n == ng.name else cache[n][idx], score, heads["labels"])
                if online["prediction"] != cached["prediction"] or online["escalated"] != cached["escalated"]:
                    raise ValueError(f"online class/gate mismatch: {policy}/{idx}")
                route_results.append({"policy": policy, "row_index": int(idx), "prediction": online["prediction"], "escalated": online["escalated"]})
        report.update(status="two_row_online_parity_complete", route_results=route_results,
            limitation="two fixed images only; not the timed population, not latency validation")
        save()
    except Exception as exc:
        report.update(status="blocked_online_parity_or_runtime", error=f"{type(exc).__name__}: {exc}")
        save()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--deit-reconstruction", type=Path)
    args = parser.parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    run(args)
