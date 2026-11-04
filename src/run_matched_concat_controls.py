"""Fit GFS/Top-k controls on a frozen hybrid reference's producer/inner folds."""
import argparse
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score

from run_confirmatory_nested import load_dataset, load_manifest, manifest_groups
from run_budgeted_rescue_paired import oof_scores, index_hash
from run_topk_individual_control import outer_indices
from run_rescue_nested_selection import (REPO, COMMON_21, fit_scores, load_existing_ngram,
                                        launch_provenance, sha256_file)
from static_concat_controls import greedy_selection, inherited_topk, budget_prefix


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-run", type=Path, required=True)
    parser.add_argument("--expected-images", type=int, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ref, out = args.reference_run.resolve(), args.output.resolve()
    if out.exists():
        raise FileExistsError(out)
    parent = json.loads((ref / "metadata.json").read_text())
    assert parent["status"] == "complete" and not parent["external_test_evaluated"]
    for file, expected in parent["provenance"]["source_sha256"].items():
        assert sha256_file(REPO / file) == expected, file
    cfg = parent["provenance"]["arguments"]
    assert cfg["producer_folds"] == cfg["selection_folds"] == 3
    assert cfg["budgets_ms"] == [15, 30, 60, 120]
    assert len(parent["library"]) == 22
    def resolve(value):
        if value is None:
            return None
        path = Path(value)
        return path if path.is_absolute() else REPO / path
    started = time.monotonic()
    cache, y = load_dataset(REPO, parent["dataset"], resolve(cfg["embedding_root"]))
    cache = {name: cache[name] for name in COMMON_21}
    groups, rows = load_manifest(resolve(cfg["manifest_root"]), parent["dataset"], y)
    inner_groups = manifest_groups(rows, cfg["inner_group_column"]) if cfg["inner_group_column"] else groups
    ng, ng_provenance = load_existing_ngram(rows, resolve(cfg["ngram_count_cache"]), 256, 8192, cfg["seed"])
    assert ng_provenance == parent["provenance"]["ngram_count_cache"]
    costs = parent["provenance"]["cost_profile"]["per_descriptor_latency_ms"]
    manifest = resolve(cfg["manifest_root"]) / "sample_manifests" / f"{parent['dataset']}.csv"
    provenance = launch_provenance(args, manifest, cache, y, parent["provenance"]["cost_profile"])
    for key in ("embedding_array_sha256", "labels_sha256", "manifest_sha256", "cost_profile_sha256"):
        assert provenance[key] == parent["provenance"][key], key
    for file in (Path(__file__), REPO / "src/static_concat_controls.py", REPO / "src/run_budgeted_rescue_paired.py"):
        provenance["source_sha256"][str(file.relative_to(REPO))] = sha256_file(file)
    train, external_test = outer_indices(parent["dataset"], cfg["seed"], cfg["fold"], y, groups, rows,
                                        cfg["official_split"], cfg["curet_direction"], cfg["invert_official_split"])
    assert len(train) == args.expected_images and not set(groups[train]).intersection(groups[external_test])
    assert index_hash(train) == parent["outer_train_indices_sha256"]
    assert index_hash(external_test) == parent["external_test_indices_sha256"]
    folds = [json.loads((ref / f"fold{i}.json").read_text()) for i in range(3)]
    all_val = [row for f in folds for row in f["validation_indices"]]
    assert len(all_val) == len(set(all_val)) == len(train) and set(all_val) == set(train)
    inputs = [args.protocol.resolve(), ref / "metadata.json", ref / "selection_oof_scores.npz",
              *[ref / f"fold{i}.json" for i in range(3)]]
    metadata = {"status": "running_selection", "dataset": parent["dataset"], "seed": cfg["seed"],
        "reference_run": str(ref), "expected_development_images": len(train), "external_test_evaluated": False,
        "outer_train_indices_sha256": index_hash(train), "external_test_indices_sha256": index_hash(external_test),
        "library": parent["library"], "provenance": provenance,
        "ngram_count_cache": ng_provenance, "input_sha256": {str(p.relative_to(REPO)): sha256_file(p) for p in inputs},
        "scope": "Matched development, no external test, no physical timing or population significance",
        "selection": {"max_k": 8, "min_improvement": .001, "patience": 2,
                      "criterion": "mean macro-F1 over saved three inner folds",
                      "topk_k_source": "unrestricted GFS", "budget_prefix_is_distinct": True},
        "classifier_latency_included": False}
    out.mkdir(parents=True)
    write_json(out / "metadata.json", metadata)
    saved = np.load(ref / "selection_oof_scores.npz", allow_pickle=False)
    labels = np.unique(y)
    decisions, inner_arrays = [], {}
    for f, record in enumerate(folds):
        fit, val = np.asarray(record["fit_indices"]), np.asarray(record["validation_indices"])
        assert not set(inner_groups[fit]).intersection(inner_groups[val])
        assert np.array_equal(saved[f"fold{f}_rows"], fit) and np.array_equal(saved[f"fold{f}_labels"], y[fit])
        split_log = record["selection_splits"]
        assert len(split_log) == 3
        positions = []
        for split in split_log:
            a, b = np.array(split["fit_indices"]), np.array(split["validation_indices"])
            assert set(a) | set(b) == set(fit) and not set(a).intersection(b)
            assert not set(inner_groups[a]).intersection(inner_groups[b])
            positions.append(np.isin(fit, b))
        assert np.all(np.sum(positions, axis=0) == 1)
        scores = {(name,): saved[f"fold{f}_single_scores"][i] for i, name in enumerate(record["library_order"])}
        scores.update({tuple(member): saved[f"fold{f}_member_scores"][i]
                       for i, member in enumerate(record["candidate_order"])})
        qualities, fresh = {}, 0
        def evaluate(subset):
            nonlocal fresh
            if subset not in qualities:
                if subset not in scores:
                    value, log = oof_scores(cache, [subset], fit, y, inner_groups, labels,
                                            cfg["seed"], 3, ng)
                    assert log == split_log
                    scores[subset] = value[subset]
                    fresh += 1
                    print(f"fold {f}: new inner candidate {fresh}: {'+'.join(subset)}", flush=True)
                pred = labels[np.argmax(scores[subset], axis=1)]
                qualities[subset] = float(np.mean([f1_score(y[fit][pos], pred[pos], average="macro", zero_division=0)
                                                   for pos in positions]))
            return qualities[subset]
        for name in record["library_order"]:
            assert abs(evaluate((name,)) - record["ranking"][name]) < 1e-12
        choices = {"gfs": greedy_selection(record["library_order"], evaluate, costs)}
        choices["topk_gfs_size"] = inherited_topk(record["ranked_blocks"], choices["gfs"], evaluate, costs)
        for budget in cfg["budgets_ms"]:
            choices[f"gfs_budget_B{budget:g}"] = greedy_selection(record["library_order"], evaluate, costs, budget=budget)
            choices[f"top_prefix_budget_B{budget:g}"] = budget_prefix(record["ranked_blocks"], evaluate, costs, budget)
        order = sorted(qualities)
        inner_arrays[f"fold{f}_candidate_order"] = np.array([json.dumps(member) for member in order])
        inner_arrays[f"fold{f}_scores"] = np.stack([scores[member] for member in order])
        inner_arrays[f"fold{f}_rows"] = fit
        inner_arrays[f"fold{f}_labels"] = y[fit]
        decisions.append({"producer_fold": f, "fit_indices": fit.tolist(), "validation_indices": val.tolist(),
                          "selection_splits": split_log, "ranked_blocks": record["ranked_blocks"],
                          "choices": choices, "fresh_inner_subsets": fresh})
        print(f"fold {f}: all static choices selected; no producer validation used", flush=True)
    write_json(out / "decisions.json", decisions)
    np.savez_compressed(out / "selection_oof_scores.npz", **inner_arrays)
    metadata.update(status="decisions_frozen", decisions_sha256=sha256_file(out / "decisions.json"))
    write_json(out / "metadata.json", metadata)
    print("All 30 policy/fold decisions frozen before producer validation", flush=True)
    predictions, validation = [], {}
    for f, record in enumerate(decisions):
        fit, val = np.array(record["fit_indices"]), np.array(record["validation_indices"])
        subsets = sorted({tuple(c["selected"]["blocks"]) for c in record["choices"].values() if c["feasible"]})
        scores = {s: fit_scores(cache, list(s), fit, val, y, labels, cfg["seed"], ng)[0] for s in subsets}
        validation[f"fold{f}_candidate_order"] = np.array([json.dumps(s) for s in subsets])
        validation[f"fold{f}_scores"] = np.stack([scores[s] for s in subsets])
        validation[f"fold{f}_rows"] = val
        for policy, choice in record["choices"].items():
            if not choice["feasible"]:
                continue
            selected = choice["selected"]
            pred = labels[np.argmax(scores[tuple(selected["blocks"])] , axis=1)]
            for i, index in enumerate(val):
                predictions.append({"row_index": int(index), "producer_fold": f, "policy": policy,
                    "label": int(y[index]), "prediction": int(pred[i]), "k": selected["k"],
                    "projected_ms": selected["projected_ms"], "classifier_calls": 1})
        print(f"fold {f}: producer predictions complete", flush=True)
    frame = pd.DataFrame(predictions)
    results = []
    for policy in decisions[0]["choices"]:
        part = frame[frame.policy == policy]
        complete = len(part) == part.row_index.nunique() == len(train)
        results.append({"policy": policy, "complete_oof_coverage": complete,
            "feasible_producer_folds": sum(d["choices"][policy]["feasible"] for d in decisions), "n": len(part),
            "macro_f1": f1_score(part.label, part.prediction, average="macro", zero_division=0) if complete else None,
            "accuracy": accuracy_score(part.label, part.prediction) if complete else None,
            "projected_ms": part.projected_ms.mean() if complete else None})
    assert sha256_file(out / "decisions.json") == metadata["decisions_sha256"]
    frame.to_csv(out / "predictions.csv", index=False)
    pd.DataFrame(results).to_csv(out / "results.csv", index=False)
    np.savez_compressed(out / "validation_scores.npz", **validation)
    audits = ng.transformation_audits()
    for audit in audits:
        a, b = set(audit["train_indices"]), set(audit["evaluation_indices"])
        assert not a.intersection(b) and a | b <= set(train)
    write_json(out / "ngram_transforms.json", audits)
    for relative, expected in metadata["input_sha256"].items():
        assert sha256_file(REPO / relative) == expected, relative
    for relative, expected in provenance["source_sha256"].items():
        assert sha256_file(REPO / relative) == expected, relative
    metadata.update(status="complete", elapsed_seconds=time.monotonic() - started,
                    output_sha256={p.name: sha256_file(p) for p in out.iterdir() if p.name != "metadata.json"})
    write_json(out / "metadata.json", metadata)
    print(pd.DataFrame(results).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
