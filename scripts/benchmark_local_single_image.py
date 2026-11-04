"""Measure batch1 image-to-class routes and derive F1 from those same calls.

Frozen heads/selection; fresh image extraction per policy, no feature sharing.
Archive vector differences are diagnostics, not a claim of parity.
"""
import argparse
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args):
    import joblib
    import numpy as np
    import pandas as pd
    import torch
    from PIL import Image
    from scipy import sparse
    from sklearn.decomposition import TruncatedSVD
    from sklearn.metrics import f1_score, accuracy_score
    from sklearn.preprocessing import normalize
    from skimage.color import rgb2gray
    from benchmark_cascade_multidataset import extractor
    from ensemble_scoring import decision_scores
    from frozen_ensemble_route import evaluate_route
    from local_deit_reconstruction import load_reconstructed_deit, verified_state_path
    from reextract_confirmatory_embeddings import load_legacy_extractors
    from run_confirmatory_nested import load_dataset, load_manifest
    from run_rescue_nested_selection import load_existing_ngram

    torch.set_num_threads(2)
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"status": "preflight", "physical_latency_published": False,
        "protocol_sha256": digest(args.protocol), "source_sha256": digest(__file__),
        "archive_vector_parity_claimed": False, "method_selection_changed": False,
        "batch_size": 1, "repeats": args.repeats, "n_requested": args.n,
        "pid": os.getpid(), "model_residency": "all required GPU models resident; no silent fallback",
        "scope": "new batch1 serving evaluation of frozen heads; archived F1 remains separate"}

    def save():
        (args.output / "status.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    def gpu_snapshot():
        result = subprocess.run(["/usr/lib/wsl/lib/nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu", "--format=csv,noheader"], capture_output=True, text=True)
        return {"returncode": result.returncode, "output": result.stdout.strip()}

    save()
    try:
        quality = json.loads((args.run / "status.json").read_text())
        if quality["status"] != "external_quality_complete_timing_pending":
            raise ValueError("head quality run incomplete")
        for name in ("fitted_heads.joblib", "predictions.csv", "metrics.csv"):
            if digest(args.run / name) != quality["output_sha256"][name]:
                raise ValueError("frozen head/prediction drift")
        if digest(args.run / "frozen_decisions.json") != quality["frozen_decisions_sha256"]:
            raise ValueError("selection drift")
        cfg_path = Path(quality["provenance"]["arguments"]["reference_config"])
        cfg_path = cfg_path if cfg_path.is_absolute() else ROOT / cfg_path
        cfg = json.loads(cfg_path.read_text())["provenance"]["arguments"]

        def resolve(value):
            p = Path(value)
            return p if p.is_absolute() else ROOT / p

        heads = joblib.load(args.run / "fitted_heads.joblib")
        cache, y = load_dataset(ROOT, quality["dataset"], resolve(cfg["embedding_root"]))
        _, rows = load_manifest(resolve(cfg["manifest_root"]), quality["dataset"], y)
        train, test = heads["training_indices"], heads["external_indices"]
        indices = test if args.n == 0 else test[np.linspace(0, len(test) - 1, min(args.n, len(test)), dtype=int)]
        paths = {}
        for idx in indices:
            row = rows[int(idx)]
            path = resolve(row.get("source_path") or row["path"])
            if digest(path) != (row.get("source_sha256") or row.get("sha256")):
                raise ValueError("image source hash mismatch")
            paths[int(idx)] = path
        names = sorted({n for recipe in heads["recipes"].values() for m in recipe["members"] for n in m}
            | {r["base"] for r in heads["recipes"].values() if r.get("base")})
        free, total = torch.cuda.mem_get_info()
        report.update(status="inputs_frozen", dataset=quality["dataset"], classifier=quality["classifier"],
            seed=quality["seed"], outer_fold=quality["outer_fold"], rows=indices.tolist(),
            full_external_coverage=len(indices) == len(test), quality_status_sha256=digest(args.run / "status.json"),
            image_sha256={str(p): digest(p) for p in paths.values()}, required_blocks=names,
            gpu_before=gpu_snapshot(), gpu_free_before_bytes=free, gpu_total_bytes=total,
            gpu_name=torch.cuda.get_device_name(), root_seed=20261028,
            stochastic_policy="fixed per image and block, independent of classifier/policy; seed management timed",
            timing_scope="file open/decode/RGB, preprocess, GPU extraction/D2H, normalization, assembly, CPU head, routing/voting; resident weights; fits/loading excluded",
            source_dependencies={str(p.relative_to(ROOT)): digest(p) for p in [ROOT / "src/frozen_ensemble_route.py", ROOT / "src/ensemble_scoring.py", ROOT / "src/local_deit_reconstruction.py", ROOT / "scripts/benchmark_cascade_multidataset.py", ROOT / "src/01_extract_features.py", ROOT / "src/extract_sota_2024.py"]})
        if free < 5 * 1024**3:
            raise RuntimeError("less than 5 GiB GPU free for resident full-library pilot; no fallback")
        save()
        legacy = load_legacy_extractors()
        ng, _ = load_existing_ngram(rows, resolve(cfg["ngram_count_cache"]), 256, 8192, cfg["seed"])
        _, ng_test, _ = ng.transform(train, test)
        svd = TruncatedSVD(n_components=min(256, len(train) - 1, 8191), n_iter=5, random_state=cfg["seed"])
        svd.fit_transform(ng._hashed_rows(train))
        state_path, evidence = verified_state_path(args.deit_reconstruction)
        if evidence["embedding_sha256"] != digest(resolve(cfg["embedding_root"]) / quality["dataset"] / "deit_s.npy"):
            raise ValueError("DeiT evidence archive mismatch")
        report.update(deit_reconstruction_sha256=digest(args.deit_reconstruction), pooler_state_sha256=digest(state_path))
        functions = {}
        for name in names:
            print(f"Loading resident extractor: {name}", flush=True)
            with torch.random.fork_rng(devices=[torch.cuda.current_device()]):
                legacy.set_seed(42)
                if name == ng.name:
                    from run_rgb_ngram_outex13_official import count_image

                    def fn(image, svd=svd):
                        keys, counts = count_image(np.asarray(image, dtype=np.uint8), "rgb_ngram_impl1")
                        bins = np.asarray(keys, dtype=np.uint64) % np.uint64(8192)
                        order = np.argsort(bins, kind="stable")
                        bins, counts = bins[order], np.asarray(counts, dtype=np.float32)[order]
                        unique, starts = np.unique(bins, return_index=True)
                        row = sparse.csr_matrix((np.add.reduceat(counts, starts), unique, [0, len(unique)]), shape=(1, 8192), dtype=np.float32)
                        return normalize(svd.transform(row).astype(np.float32), norm="l2")[0]
                elif legacy.EXTRACTORS.get(name, {}).get("type") == "classical":
                    ext = legacy.get_extractor(name, device="cpu")

                    def fn(image, ext=ext):
                        resized = image.resize((ext.image_size, ext.image_size), Image.BILINEAR)
                        gray = (rgb2gray(np.asarray(resized)) * 255).astype(np.uint8)
                        return getattr(ext, "_" + ext.method)(gray)
                elif name == "deit_s":
                    fn = load_reconstructed_deit(args.deit_reconstruction, "cuda")
                else:
                    fn = extractor(name, "cuda")
            functions[name] = fn
            report.update(status="loading_models", loaded_blocks=list(functions), gpu_current=gpu_snapshot())
            save()
        labels, models = heads["labels"], heads["models"]
        block_positions = {n: i for i, n in enumerate(names)}
        expected_dimensions = {n: ng_test.shape[1] if n == ng.name else cache[n].shape[1] for n in names}

        def score(member, x):
            model, scale = models[member]
            return decision_scores(model, x, scale)

        def execute(policy, idx, inspect=False):
            with Image.open(paths[int(idx)]) as image_file:
                image = image_file.convert("RGB")
            differences = {}

            def acquire(name):
                seed = (20261028 + int(idx) * 1009 + block_positions[name]) % (2**31)
                with torch.random.fork_rng(devices=[torch.cuda.current_device()]):
                    torch.manual_seed(seed)
                    value = np.asarray(functions[name](image), dtype=np.float32).ravel()
                value = value / max(float(np.linalg.norm(value)), 1e-12)
                if value.shape != (expected_dimensions[name],) or not np.isfinite(value).all():
                    raise ValueError(f"invalid online feature: {name}")
                if inspect:
                    target = ng_test[np.flatnonzero(test == idx)[0]] if name == ng.name else cache[name][idx]
                    differences[name] = float(np.max(np.abs(value - target)))
                return value

            result = evaluate_route(heads["recipes"][policy], acquire, score, labels)
            if not heads["recipes"][policy].get("base"):
                result["escalated"] = False
            return result, differences

        # Warmup and archive comparison are explicit diagnostics, not acceptance
        # by changing 1e-4. Actual online F1 will be computed below instead.
        report["warmup_archive_differences"] = []
        for policy in heads["recipes"]:
            for idx in indices[:2]:
                result, differences = execute(policy, idx, inspect=True)
                report["warmup_archive_differences"].append({"policy": policy, "row_index": int(idx),
                    "max_abs_error_by_block": differences, "prediction": result["prediction"]})
        torch.cuda.synchronize()
        report.update(status="timing_online", gpu_after_loading=gpu_snapshot(), timing_rows_complete=0)
        save()
        records = []
        rng = np.random.default_rng(20261028)
        output_csv = args.output / "online_calls.csv"
        for repeat in range(args.repeats):
            for idx in indices:
                for policy in rng.permutation(list(heads["recipes"])):
                    torch.cuda.synchronize()
                    started = time.perf_counter_ns()
                    result, _ = execute(str(policy), idx)
                    torch.cuda.synchronize()
                    elapsed = (time.perf_counter_ns() - started) / 1e6
                    records.append({"repeat": repeat, "row_index": int(idx), "label": int(y[idx]),
                        "policy": str(policy), "ms": elapsed, **result})
                if len(records) % 50 == 0:
                    pd.DataFrame(records).to_csv(output_csv, index=False)
                    report.update(timing_rows_complete=len(records), gpu_current=gpu_snapshot())
                    save()
                    print(f"Online measured calls: {len(records)}/{len(indices) * 5 * args.repeats}", flush=True)
        frame = pd.DataFrame(records)
        frame.to_csv(output_csv, index=False)
        # Repetitions are timing observations, not independent quality samples.
        if frame.groupby(["policy", "row_index"]).prediction.nunique().max() != 1 or frame.groupby(["policy", "row_index"]).escalated.nunique().max() != 1:
            raise ValueError("online predictions or gates vary across repeated identical requests")
        unique = frame.drop_duplicates(["policy", "row_index"])
        archived = pd.read_csv(args.run / "predictions.csv")
        summaries = []
        for policy, group in unique.groupby("policy"):
            times = frame[frame.policy == policy].ms
            reference = archived[archived.policy == policy].set_index("row_index").loc[group.row_index]
            summaries.append({"policy": policy, "external_images": len(group), "timed_calls": len(times),
                "macro_f1_online": float(f1_score(group.label, group.prediction, labels=labels, average="macro", zero_division=0)),
                "accuracy_online": float(accuracy_score(group.label, group.prediction)),
                "mean_ms": float(times.mean()), "median_ms": float(times.median()), "p95_ms": float(times.quantile(.95)),
                "prediction_agreement_vs_archive": float(np.mean(reference.prediction.to_numpy() == group.prediction.to_numpy())),
                "escalation_fraction_online": float(group.escalated.mean())})
        pd.DataFrame(summaries).to_csv(args.output / "online_summary.csv", index=False)
        report.update(status="batch1_online_f1_and_timing_complete", physical_latency_published=True,
            timing_rows_complete=len(frame), summaries=summaries, gpu_after=gpu_snapshot(),
            execution_context="shared GPU observed, exploratory pilot; not an isolated hardware benchmark",
            output_sha256={n: digest(args.output / n) for n in ["online_calls.csv", "online_summary.csv"]})
        save()
        print(pd.DataFrame(summaries).to_string(index=False), flush=True)
    except Exception as exc:
        report.update(status="blocked_online_execution", error=f"{type(exc).__name__}: {exc}")
        save()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--deit-reconstruction", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--n", type=int, default=0, help="0 = every frozen external-test image")
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()
    if args.n < 0 or args.repeats < 1:
        parser.error("nonnegative n and positive repeats required")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    run(args)
