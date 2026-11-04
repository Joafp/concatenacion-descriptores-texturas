"""Reconstruct local controls and select an adaptive route before external F1.

New outputs only. Does not claim online latency from cached feature scoring.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args):
    import joblib
    import numpy as np
    import pandas as pd
    import torch
    from sklearn.metrics import accuracy_score, f1_score
    from budgeted_rescue import select_policy
    from ensemble_scoring import decision_scores, legacy_batch_decision_scores
    from fsc_tex.cost_model import DEFAULT_HARDWARE_LATENCY_MS as latencies, DEFAULT_POLICY_OVERHEAD_MS as overhead
    from fsc_tex.utility import compute_margins
    from local_external_panel import fit_member, training_oof
    from run_confirmatory_nested import load_dataset, load_manifest, manifest_groups
    from run_rescue_nested_selection import COMMON_21, load_existing_ngram, block_matrices, launch_provenance
    from run_topk_individual_control import outer_indices

    torch.set_num_threads(args.threads)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {"status": "preflight", "classifier": args.classifier,
        "physical_latency_published": False, "external_test_evaluated": False,
        "protocol_sha256": digest(args.protocol), "runner_sha256": digest(__file__),
        "selection_source_sha256": digest(ROOT / "src/local_external_panel.py"),
        "reference_config_sha256": digest(args.reference_config),
        "pid": os.getpid(), "head_device": "cpu", "cpu_threads": args.threads}

    def save():
        (out / "status.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    save()
    started = time.monotonic()
    try:
        cfg = json.loads(args.reference_config.read_text())["provenance"]["arguments"]
        dataset, seed = cfg["dataset"], cfg["seed"]
        fold = (cfg["official_split"] - 1 if cfg.get("official_split") else
                {"a_to_b": 0, "b_to_a": 1}[cfg["curet_direction"]] if cfg.get("curet_direction") else cfg["fold"])
        report.update(dataset=dataset, seed=seed, outer_fold=fold)

        def resolve(value):
            p = Path(value)
            return p if p.is_absolute() else ROOT / p

        prefix = ROOT / "results/exploratory" / ("resmlp" if args.classifier == "resmlp" else "")

        def recipe(family):
            hits = []
            for path in (prefix / "k4" / family).glob("*/*.json"):
                value = json.loads(path.read_text())
                if (value.get("dataset"), value.get("classifier"), value.get("seed"), value.get("outer_fold")) == (dataset, args.classifier, seed, fold):
                    hits.append((path, value))
            if len(hits) != 1:
                raise ValueError(f"expected exactly one {family} recipe, got {len(hits)}")
            return hits[0]

        div_path, div = recipe("diversity")
        lot_path, lot = recipe("lottery")
        if div["n_candidates"] != 21 or lot["n_candidates"] != 21:
            raise ValueError("unexpected archived library")
        diversity = next(c for c in div["cells"] if c["lambda"] == .25 and c["beta"] == 8)["subsets"]
        lottery = [d["subset"] for d in next(c for c in lot["betas"] if c["beta"] == 8)["draws"]]
        if len(diversity) != 15 or len(lottery) != 15:
            raise ValueError("unexpected ensemble size")
        sweep_paths = sorted((prefix / "k_sweep").glob("*/k_sweep.csv"))
        sweep = pd.concat([pd.read_csv(p) for p in sweep_paths])
        match = sweep[(sweep.dataset == dataset) & (sweep.classifier == args.classifier)
            & (sweep.seed == seed) & (sweep.outer_fold == fold) & (sweep.k == 4)]
        if len(match) != 1:
            raise ValueError("missing or duplicate Top-4")
        top4 = match.iloc[0].selected.split("+")
        cache, y = load_dataset(ROOT, dataset, resolve(cfg["embedding_root"]))
        cache = {name: cache[name] for name in COMMON_21}
        manifest = resolve(cfg["manifest_root"])
        groups, rows = load_manifest(manifest, dataset, y)
        train, test = outer_indices(dataset, seed, cfg["fold"], y, groups, rows,
            cfg.get("official_split"), cfg.get("curet_direction"), cfg.get("invert_official_split", False))
        if set(groups[train]).intersection(groups[test]):
            raise ValueError("external source-group overlap")
        if cfg.get("inner_group_column"):
            groups = manifest_groups(rows, cfg["inner_group_column"])
            if set(groups[train]).intersection(groups[test]):
                raise ValueError("external physical-sample overlap")
        labels = np.unique(y[train])
        ng, ng_provenance = load_existing_ngram(rows, resolve(cfg["ngram_count_cache"]), 256, 8192, seed)
        library = COMMON_21 + [ng.name]
        provenance = launch_provenance(args, manifest / "sample_manifests" / f"{dataset}.csv",
            cache, y, {"per_descriptor_latency_ms": latencies, "policy_overhead_ms": overhead})
        report.update(status="training_oof", training_rows=len(train), test_rows=len(test),
            provenance=provenance, ngram_provenance=ng_provenance,
            archive_recipe_sha256={str(p.relative_to(ROOT)): digest(p) for p in [div_path, lot_path]},
            training_indices=train.tolist(), external_indices=test.tolist(),
            adaptive_base_library=library, rescue_pool_library="archived diversity-21",
            selection_budget_ms=args.budget_ms, selection_folds=3,
            external_inference_normalization="frozen training std; historical batch scale diagnostic only")
        save()
        candidates = sorted({tuple(m) for m in diversity})
        subsets = sorted(set(candidates) | {(n,) for n in library})

        def progress(number, total, subset):
            report.update(oof_subsets_complete=number, oof_subsets_total=total)
            save()
            print(f"OOF {number}/{total}: {'+'.join(subset)}", flush=True)

        scores, inner = training_oof(cache, subsets, train, y, groups, labels,
            args.classifier, seed, 3, ng, progress)
        singles = {n: scores[(n,)] for n in library}
        decision = select_policy(singles, {m: scores[m] for m in candidates}, y[train], labels,
            {n: compute_margins(v) for n, v in singles.items()}, latencies, args.budget_ms,
            quantiles=(.1, .25, .5), max_members=3, overhead=overhead, criterion="relevance")
        if not decision["feasible"]:
            raise ValueError("adaptive policy infeasible; preserve as pending, do not choose via test")
        chosen = decision["selected"]
        recipes = {"Completa-22": {"members": [library]}, "Top-4": {"members": [top4]},
            "Ens-diversidad": {"members": diversity}, "Ens-tombola": {"members": lottery},
            "Adaptive-selection-margin": chosen}
        frozen = {"recipes": recipes, "selection": decision, "inner_splits": inner,
            "scope": "selection fixed before external fitting/scoring; exploratory reconstruction, not preregistered confirmation"}
        (out / "frozen_decisions.json").write_text(json.dumps(frozen, indent=2, allow_nan=False) + "\n")
        np.savez_compressed(out / "training_oof.npz", train=train, labels=y[train],
            scores=np.stack([scores[s] for s in subsets]), subset_names=np.asarray(["+".join(s) for s in subsets]))
        report.update(status="selection_frozen_before_external_scoring", frozen_decisions_sha256=digest(out / "frozen_decisions.json"))
        save()
        members = {tuple(m) for recipe in recipes.values() for m in recipe["members"]}
        members.add((chosen["base"],))
        models, external_scores, legacy = {}, {}, {}
        for number, member in enumerate(sorted(members)):
            model, scale, value = fit_member(cache, member, train, test, y, labels, args.classifier, seed, ng)
            models[member] = (model, scale)
            external_scores[member] = value
            # Diagnostic only: matches the historical batch-dependent hypothesis.
            _, xeval = block_matrices(cache, list(member), train, test, ng)
            legacy[member] = legacy_batch_decision_scores(model, xeval)
            report.update(status="external_scoring", fitted_external_models=number + 1, total_external_models=len(members))
            save()
            print(f"External fit {number + 1}/{len(members)}: {'+'.join(member)}", flush=True)
        predictions, metrics = [], []
        for policy, recipe in recipes.items():
            if recipe.get("base"):
                base = external_scores[(recipe["base"],)]
                pred = labels[np.argmax(base, axis=1)]
                margin = compute_margins(base)
                gate = margin < recipe["threshold"] if recipe["members"] else np.zeros(len(test), dtype=bool)
                if recipe["members"]:
                    rescue = np.mean([external_scores[tuple(m)] for m in recipe["members"]], axis=0)
                    pred[gate] = labels[np.argmax(rescue[gate], axis=1)]
            else:
                pred = labels[np.argmax(np.mean([external_scores[tuple(m)] for m in recipe["members"]], axis=0), axis=1)]
                gate = np.zeros(len(test), dtype=bool)
                margin = np.full(len(test), np.nan)
            metrics.append({"policy": policy, "macro_f1": float(f1_score(y[test], pred, labels=labels, average="macro", zero_division=0)),
                "accuracy": float(accuracy_score(y[test], pred)), "rows": len(test),
                "measured_ms_per_image": None, "escalation_fraction": float(gate.mean())})
            for i, row in enumerate(test):
                predictions.append({"row_index": int(row), "label": int(y[row]), "policy": policy,
                    "prediction": int(pred[i]), "escalated": bool(gate[i]), "base_margin": margin[i]})
        diagnostics = []
        for policy, members_, archived in [
            ("Ens-diversidad", diversity, next(c for c in div["cells"] if c["lambda"] == .25 and c["beta"] == 8)["ensemble_soft"]["macro_f1"]),
            ("Ens-tombola", lottery, next(c for c in lot["betas"] if c["beta"] == 8)["ensemble_soft"]["macro_f1"])]:
            pred = labels[np.argmax(np.mean([legacy[tuple(m)] for m in members_], axis=0), axis=1)]
            diagnostics.append({"policy": policy, "archived_macro_f1": archived,
                "legacy_batch_reconstruction_f1": float(f1_score(y[test], pred, labels=labels, average="macro", zero_division=0)),
                "training_scale_reconstruction_f1": next(m["macro_f1"] for m in metrics if m["policy"] == policy)})
        joblib.dump({"models": models, "labels": labels, "training_indices": train,
            "external_indices": test, "recipes": recipes}, out / "fitted_heads.joblib")
        pd.DataFrame(predictions).to_csv(out / "predictions.csv", index=False)
        pd.DataFrame(metrics).to_csv(out / "metrics.csv", index=False)
        pd.DataFrame(diagnostics).to_csv(out / "archived_scale_diagnostic.csv", index=False)
        (out / "ngram_transforms.json").write_text(json.dumps(ng.transformation_audits(), indent=2) + "\n")
        report.update(status="external_quality_complete_timing_pending", external_test_evaluated=True,
            elapsed_seconds=time.monotonic() - started, packages={"numpy": np.__version__, "torch": torch.__version__},
            output_sha256={name: digest(out / name) for name in ["fitted_heads.joblib", "predictions.csv", "metrics.csv", "training_oof.npz", "archived_scale_diagnostic.csv"]})
        save()
        print(pd.DataFrame(metrics).to_string(index=False), flush=True)
    except Exception as exc:
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}", elapsed_seconds=time.monotonic() - started)
        save()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-config", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--classifier", choices=("svm", "resmlp"), required=True)
    parser.add_argument("--budget-ms", type=float, default=60.)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.budget_ms <= 0 or args.threads < 1:
        parser.error("positive budget/threads required")
    os.environ["HF_HUB_OFFLINE"] = "1"
    run(args)
