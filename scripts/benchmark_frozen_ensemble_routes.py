"""Parity-gated physical pilot for four frozen development routes, CPU or CUDA.

No model selection or test evaluation. Refuses to publish physical timings when
online vectors, cached predictions or gate decisions fail parity. New outputs only.
"""
import argparse
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def run(args):
    import numpy as np
    import pandas as pd
    import torch
    from PIL import Image
    from sklearn.decomposition import TruncatedSVD
    from sklearn.preprocessing import normalize
    from scipy import sparse
    from ensemble_scoring import decision_scores, training_score_scale
    from frozen_ensemble_route import evaluate_route, feature_order
    from run_confirmatory_nested import load_dataset, load_manifest, make_model
    from run_rescue_nested_selection import block_matrices, load_existing_ngram

    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    protocol = ROOT / "docs/fsc_tex/PROTOCOLO_FISICO_ENSAMBLES_2026-10-26.md"
    report = {"status": "preflight", "condition": args.condition, "producer_fold": args.fold,
              "device": args.device, "physical_timing_validated": False,
              "external_test_evaluated": False, "new_inferential_tests": 0,
              "protocol_sha256": digest(protocol), "source_sha256": digest(__file__),
              "route_source_sha256": digest(ROOT / "src/frozen_ensemble_route.py")}
    def save():
        (out / "status.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    save()
    try:
        audit_path = ROOT / f"results/analysis/mesa_replication_20261026/{args.condition}.json"
        audit = read(audit_path)
        assert audit["status"] == "ANALYZED"
        for name, expected in audit["input_sha256"].items():
            assert digest(ROOT / name) == expected, name
        suite = ROOT / "results/exploratory/integration_v11/replication_20261026" / args.condition
        hybrid = suite / "hybrid"
        hm = read(hybrid / "metadata.json")
        ref, carlos = Path(hm["reference_run"]), Path(hm["carlos_run"])
        static = suite / ("static_recovery" if (suite / "static_recovery").is_dir() else "static")
        rm = read(ref / "metadata.json")
        cfg = rm["provenance"]["arguments"]
        fold = read(ref / f"fold{args.fold}.json")
        fit, val = np.array(fold["fit_indices"]), np.array(fold["validation_indices"])
        assert not set(fit) & set(val)
        records = read(carlos / "folds.json")
        record = next(r for r in records if r["producer_fold"] == args.fold)
        assert record["fit_indices"] == fit.tolist() and record["validation_indices"] == val.tolist()
        def chosen(folder, policy):
            return next(p["selected"] for p in read(folder / "selections.json")
                        if p["producer_fold"] == args.fold and p["policy"] == policy)
        static_decision = next(p for p in read(static / "decisions.json") if p["producer_fold"] == args.fold)
        recipes = {"carlos_permanent": {"members": record["diversity_members"]},
            "static_B60": static_decision["budget_selections"]["60.0"]["selected"],
            "previous_pool_B60": chosen(ref, "relevance_B60"),
            "hybrid_carlos_B60": chosen(hybrid, "pruned_relevance_B60")}
        indices = val[np.linspace(0, len(val) - 1, min(args.n, len(val)), dtype=int)]
        report.update(status="frozen_before_physical_extraction", recipes=recipes, rows=indices.tolist(),
                      fit_indices_sha256=fold["fit_indices_sha256"], audit_sha256=digest(audit_path),
                      repeats=args.repeats, seed=cfg["seed"], warmup_rows=2,
                      sample_rule="linspace in producer validation order, without score or label filtering",
                      timing_scope="batch1 image decode/preprocessing/extraction/transfer/scoring/routing; resident CPU models; model load and SVM fit excluded")
        save()
        def resolve(path):
            p = Path(path)
            return p if p.is_absolute() else ROOT / p
        cache, y = load_dataset(ROOT, rm["dataset"], resolve(cfg["embedding_root"]))
        _, rows = load_manifest(resolve(cfg["manifest_root"]), rm["dataset"], y)
        paths = {}
        for idx in indices:
            row = rows[int(idx)]
            path = resolve(row.get("source_path") or row["path"])
            assert digest(path) == (row.get("source_sha256") or row.get("sha256")), path
            paths[int(idx)] = path
        models = {}
        members = {tuple(m) for recipe in recipes.values() for m in recipe["members"]}
        members.update((recipe["base"],) for recipe in recipes.values() if recipe.get("base"))
        blocks = sorted({name for member in members for name in member})
        ng = None
        if "rgb_ngram_svd" in blocks:
            ng, _ = load_existing_ngram(rows, resolve(cfg["ngram_count_cache"]), 256, 8192, cfg["seed"])
        labels = np.unique(y)
        for member in sorted(members):
            xfit, _ = block_matrices(cache, member, fit, val, ng)
            model = make_model("svm", cfg["seed"])
            model.fit(xfit, y[fit])
            models[member] = (model, training_score_scale(model, xfit))
        def score(member, x):
            model, scale = models[member]
            return decision_scores(model, x, scale)
        cached_ng = ng.transform(fit, val)[1] if ng else None
        def cached(idx, name):
            return cached_ng[np.flatnonzero(val == idx)[0]] if name == "rgb_ngram_svd" else cache[name][idx]
        expected = {}
        for key, recipe in recipes.items():
            folder, policy = {"carlos_permanent": (hybrid, "carlos_diversity15_always"),
                "static_B60": (static, "static_B60"), "previous_pool_B60": (ref, "relevance_B60"),
                "hybrid_carlos_B60": (hybrid, "pruned_relevance_B60")}[key]
            archived = pd.read_csv(folder / "predictions.csv")
            archived = archived[(archived.policy == policy) & (archived.producer_fold == args.fold)].set_index("row_index")
            for idx in indices:
                replay = evaluate_route(recipe, lambda n: cached(idx, n), score, labels)
                assert replay["prediction"] == int(archived.loc[idx, "prediction"]), (key, int(idx), "cached replay")
                if recipe.get("base"):
                    assert replay["escalated"] == bool(archived.loc[idx, "escalated"]), (key, int(idx), "gate")
                expected[key, int(idx)] = replay
        report.update(status="cached_predictions_replayed", required_blocks=blocks, fitted_models=len(models))
        save()
        print(f"Cached predictions replayed; loading {len(blocks)} extractors offline on {args.device}", flush=True)
        legacy = module("physical_legacy", ROOT / "src/01_extract_features.py")
        from benchmark_cascade_multidataset import extractor as deep_extractor
        fns = {}
        for name in blocks:
            print(f"Loading/parity: {name}", flush=True)
            if name == "rgb_ngram_svd":
                svd = TruncatedSVD(n_components=min(256, len(fit) - 1, 8191), n_iter=5, random_state=cfg["seed"])
                svd.fit_transform(ng._hashed_rows(fit))
                from run_rgb_ngram_outex13_official import count_image
                def raw(path, svd=svd):
                    with Image.open(path) as im:
                        keys, values = count_image(np.asarray(im.convert("RGB"), dtype=np.uint8), "rgb_ngram_impl1")
                    bins = np.asarray(keys, dtype=np.uint64) % np.uint64(8192)
                    order = np.argsort(bins, kind="stable")
                    bins, values = bins[order], np.asarray(values, dtype=np.float32)[order]
                    unique, starts = np.unique(bins, return_index=True)
                    row = sparse.csr_matrix((np.add.reduceat(values, starts), unique, [0, len(unique)]), shape=(1, 8192), dtype=np.float32)
                    return normalize(svd.transform(row).astype(np.float32), norm="l2")[0]
            elif legacy.EXTRACTORS.get(name, {}).get("type") == "classical":
                ext = legacy.get_extractor(name, device=args.device)
                def raw(path, ext=ext):
                    gray = ext._load_gray(str(path))
                    return getattr(ext, "_" + ext.method)(gray)
            else:
                fn = deep_extractor(name, args.device)
                def raw(path, fn=fn):
                    with Image.open(path) as im:
                        return fn(im.convert("RGB"))
            def normalized(path, raw=raw):
                value = np.asarray(raw(path), dtype=np.float32).ravel()
                return value / max(float(np.linalg.norm(value)), 1e-12)
            fns[name] = normalized
            checks = []
            for idx in indices[:2]:
                online, target = normalized(paths[int(idx)]), cached(idx, name)
                error = float(np.max(np.abs(online - target)))
                checks.append(error)
                assert online.shape == target.shape and error <= 1e-4, (name, int(idx), "embedding parity", error)
            report.setdefault("extractor_max_abs_error", {})[name] = max(checks)
            save()
        def sync():
            if args.device == "cuda":
                torch.cuda.synchronize()
        for recipe in recipes.values():
            for idx in indices[:2]:
                evaluate_route(recipe, lambda n: fns[n](paths[int(idx)]), score, labels)
        timings = []
        rng = np.random.default_rng(20261026)
        for repeat in range(args.repeats):
            for idx in indices:
                for key in rng.permutation(list(recipes)):
                    sync()
                    start = time.perf_counter()
                    result = evaluate_route(recipes[key], lambda n: fns[n](paths[int(idx)]), score, labels)
                    sync()
                    duration = 1000 * (time.perf_counter() - start)
                    assert result["prediction"] == expected[key, int(idx)]["prediction"], (key, int(idx), "online prediction")
                    assert result["escalated"] == expected[key, int(idx)]["escalated"], (key, int(idx), "online gate")
                    timings.append({"repeat": repeat, "row_index": int(idx), "policy": str(key), "ms": duration, **result})
            print(f"Paired timing repetition {repeat + 1}/{args.repeats} complete", flush=True)
        frame = pd.DataFrame(timings)
        frame.to_csv(out / "paired_timings.csv", index=False)
        report.update(status="physical_pilot_complete", physical_timing_validated=True,
            measured_rows=len(indices), scope="small deterministic development timing pilot, no quality generalization",
            timings={key: {"mean_ms": float(g.ms.mean()), "median_ms": float(g.ms.median()),
                          "p95_ms": float(g.ms.quantile(.95))} for key, g in frame.groupby("policy")},
            packages={"torch": torch.__version__, "numpy": np.__version__})
        save()
    except Exception as exc:
        report.update(status="blocked_parity_or_runtime", error=f"{type(exc).__name__}: {exc}", physical_timing_validated=False)
        save()
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--condition", choices=("FMD_s42", "Outex_s123"), required=True)
    p.add_argument("--fold", type=int, choices=range(3), default=0)
    p.add_argument("--n", type=int, default=6)
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.n < 2 or args.repeats < 1:
        p.error("n >= 2 and repeats >= 1 required")
    # Never download checkpoints as a side effect of this timing pilot.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    run(args)
