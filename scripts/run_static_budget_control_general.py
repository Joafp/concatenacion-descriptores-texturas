"""Evaluate the same static control with manifest-sized development coverage.

Reads archived internal scores, freezes every decision, then evaluates producer
validation using cached scores or same-recipe SVM refits. Never changes sources.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from static_budget_control import select_static_ensembles
from run_rescue_nested_selection import COMMON_21, fit_scores, load_existing_ngram, sha256_array
from run_confirmatory_nested import load_dataset, load_manifest, manifest_groups


def development_coverage(folds):
    indices = [int(index) for fold in folds for index in fold]
    if not indices or len(indices) != len(set(indices)):
        raise ValueError("producer validation must cover distinct development rows")
    return len(indices)

HYBRID = ROOT / "results/exploratory/integration_v8/carlos_hybrid_outex22_20261021"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    global HYBRID
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hybrid-run", type=Path, default=HYBRID)
    parser.add_argument("--expected-images", type=int, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    HYBRID = args.hybrid_run.resolve()
    out = args.output.resolve()
    if out.exists():
        raise FileExistsError(out)
    meta = json.loads((HYBRID / "metadata.json").read_text())
    ref, carlos = Path(meta["reference_run"]), Path(meta["carlos_run"])
    rm = json.loads((ref / "metadata.json").read_text())
    cfg = rm["provenance"]["arguments"]
    costs = meta["provenance"]["cost_profile"]["per_descriptor_latency_ms"]
    for name, expected in meta["input_sha256"].items():
        assert digest(ROOT / name) == expected, name
    for name, expected in meta["provenance"]["source_sha256"].items():
        assert digest(ROOT / name) == expected, name
    saved = np.load(ref / "selection_oof_scores.npz", allow_pickle=False)
    hybrid = np.load(HYBRID / "scores.npz", allow_pickle=False)
    budgets = list(cfg["budgets_ms"])
    records, decisions = [], []
    start = time.perf_counter()
    for fold_id in range(3):
        fold = json.loads((HYBRID / f"fold{fold_id}.json").read_text())
        rf = json.loads((ref / f"fold{fold_id}.json").read_text())
        fit, val = np.array(fold["fit_indices"]), np.array(fold["validation_indices"])
        assert fold["fit_indices"] == rf["fit_indices"] and fold["validation_indices"] == rf["validation_indices"]
        assert not set(fit).intersection(val)
        assert np.array_equal(saved[f"fold{fold_id}_rows"], fit)
        assert np.array_equal(hybrid[f"fold{fold_id}_rows"], fit)
        scores = {(n,): saved[f"fold{fold_id}_single_scores"][i]
                  for i, n in enumerate(rf["library_order"])}
        scores.update({tuple(m): hybrid[f"fold{fold_id}_member_scores"][i]
                       for i, m in enumerate(fold["candidate_order"])})
        y_fit = saved[f"fold{fold_id}_labels"]
        selected = select_static_ensembles(scores, y_fit, np.unique(y_fit), costs,
                                            budgets, max_members=cfg["max_members"])
        assert all(v["feasible"] for v in selected.values())
        decisions.append({"producer_fold": fold_id, "candidate_pool": [list(m) for m in sorted(scores)],
                          "fit_indices": fit.tolist(), "validation_indices": val.tolist(),
                          "budget_selections": selected})
        records.append((fold_id, fold, rf, fit, val, y_fit))
    expected_development_images = development_coverage([record[4] for record in records])
    if expected_development_images != args.expected_images:
        raise ValueError("development coverage differs from the frozen protocol")
    inputs = [args.protocol.resolve(), HYBRID / "metadata.json", HYBRID / "scores.npz", ref / "metadata.json",
              ref / "selection_oof_scores.npz", carlos / "validation_scores.npz",
              carlos / "folds.json", ROOT / "src/static_budget_control.py", Path(__file__),
              ROOT / "docs/fsc_tex/PROTOCOLO_CONTROL_ESTATICO_MESA_2026-10-25.md"]
    inputs += [root / f"fold{i}.json" for root in (HYBRID, ref) for i in range(3)]
    metadata = {"development_images": expected_development_images, "status": "decisions_frozen", "scope": "Development control; not blinded, official test or physical timing",
                "dataset": meta["dataset"], "library": meta["library"], "budgets_ms": budgets,
                "member_limit": cfg["max_members"], "cost_profile": meta["provenance"]["cost_profile"],
                "official_test_evaluated": False, "classifier_latency_included": False,
                "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in inputs},
                "packages": {n: importlib.metadata.version(n) for n in ("numpy", "pandas", "scipy", "scikit-learn")}}
    out.mkdir(parents=True)
    (out / "decisions.json").write_text(json.dumps(decisions, indent=2) + "\n")
    metadata["frozen_decisions_sha256"] = digest(out / "decisions.json")
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("All 12 selections frozen before producer-validation evaluation", flush=True)

    def resolve(value):
        p = Path(value)
        return p if p.is_absolute() else ROOT / p
    cache, y = load_dataset(ROOT, meta["dataset"], resolve(cfg["embedding_root"]))
    cache = {n: cache[n] for n in COMMON_21}
    groups, manifest_rows = load_manifest(resolve(cfg["manifest_root"]), meta["dataset"], y)
    if cfg["inner_group_column"]:
        groups = manifest_groups(manifest_rows, cfg["inner_group_column"])
    for name, expected in meta["provenance"]["embedding_array_sha256"].items():
        assert sha256_array(cache[name]) == expected, name
    assert sha256_array(y) == meta["provenance"]["labels_sha256"]
    labels = np.unique(y)
    validation = np.load(carlos / "validation_scores.npz", allow_pickle=False)
    cr = {r["producer_fold"]: r for r in json.loads((carlos / "folds.json").read_text())}
    predictions, fold_results, arrays, fresh_fits, reused = [], [], {}, 0, 0
    ng = None
    for f, fold, rf, fit, val, y_fit in records:
        assert np.array_equal(y[fit], y_fit)
        assert not set(groups[fit]).intersection(groups[val])
        vr = cr[f]
        assert vr["fit_indices"] == fit.tolist() and vr["validation_indices"] == val.tolist()
        vscore = {tuple(m): validation[f"fold{f}_scores"][i]
                  for i, m in enumerate(vr["unique_subset_order"])}
        assert np.array_equal(validation[f"fold{f}_rows"], val)
        vscore.update({(str(n),): hybrid[f"fold{f}_validation_base_scores"][i]
                       for i, n in enumerate(hybrid[f"fold{f}_validation_base_order"])})
        needed = sorted({tuple(m) for choice in decisions[f]["budget_selections"].values()
                         for m in choice["selected"]["members"]})
        reused += sum(m in vscore for m in needed)
        for member in needed:
            if member not in vscore:
                if "rgb_ngram_svd" in member and ng is None:
                    ng, ng_provenance = load_existing_ngram(manifest_rows, resolve(cfg["ngram_count_cache"]),
                                                            256, 8192, cfg["seed"])
                    assert ng_provenance == meta["provenance"]["ngram_count_cache"]
                vscore[member] = fit_scores(cache, member, fit, val, y, labels, cfg["seed"], ng)[0]
                fresh_fits += 1
        arrays[f"fold{f}_rows"] = val
        arrays[f"fold{f}_candidate_order"] = np.array([json.dumps(m) for m in needed])
        arrays[f"fold{f}_scores"] = np.stack([vscore[m] for m in needed])
        for choice in decisions[f]["budget_selections"].values():
            point = choice["selected"]
            budget = choice["budget_ms"]
            pred = labels[np.argmax(np.sum([vscore[tuple(m)] for m in point["members"]], axis=0), axis=1)]
            assert point["projected_ms"] <= budget + 1e-10
            name = f"static_B{budget:g}"
            fold_results.append({"producer_fold": f, "policy": name, "budget_ms": budget,
                "macro_f1": f1_score(y[val], pred, average="macro", zero_division=0),
                "projected_ms": point["projected_ms"], "classifier_calls": point["classifier_calls"]})
            for i, index in enumerate(val):
                predictions.append({"row_index": int(index), "producer_fold": f, "policy": name,
                    "label": int(y[index]), "prediction": int(pred[i]), "projected_ms": point["projected_ms"],
                    "classifier_calls": point["classifier_calls"]})
        print(f"Static control producer fold {f} complete", flush=True)
    p = pd.DataFrame(predictions)
    summaries = []
    for budget in budgets:
        name = f"static_B{budget:g}"
        part = p[p.policy == name]
        assert len(part) == part.row_index.nunique() == expected_development_images
        summaries.append({"policy": name, "budget_ms": budget, "n": len(part),
            "macro_f1": f1_score(part.label, part.prediction, average="macro", zero_division=0),
            "accuracy": accuracy_score(part.label, part.prediction), "projected_ms": part.projected_ms.mean(),
            "classifier_calls": part.classifier_calls.mean()})
    assert digest(out / "decisions.json") == metadata["frozen_decisions_sha256"]
    p.to_csv(out / "predictions.csv", index=False)
    pd.DataFrame(summaries).to_csv(out / "results.csv", index=False)
    pd.DataFrame(fold_results).to_csv(out / "fold_results.csv", index=False)
    np.savez_compressed(out / "validation_scores.npz", **arrays)
    metadata.update(status="complete", fresh_producer_fits=fresh_fits, reused_producer_models=reused,
                    elapsed_seconds=time.perf_counter() - start,
                    ngram_transforms=ng.transformation_audits() if ng else [],
                    output_sha256={p.name: digest(p) for p in out.iterdir() if p.name != "metadata.json"})
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(pd.DataFrame(summaries).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
