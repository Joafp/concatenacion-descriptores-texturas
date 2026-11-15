#!/usr/bin/env python3
"""E1 fixed-four cascade and E2 confidence controls, accuracy-primary reporting.

Historical training selection remains macro-F1 with tolerance .005; it is not
silently replaced by the newly requested reporting metric. Costs are component
projections. Failed scientific cases are recorded once, never retried.
"""
from __future__ import annotations
import argparse
import csv
import fcntl
import gzip
import importlib.metadata
import json
from pathlib import Path
import sys
import time
import traceback
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import numpy as np
import joblib
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from threadpoolctl import threadpool_limits
from run_confirmatory_nested import canonical_labels, l2_rows, make_model
from run_cheap_stage_selected_cascade import select
from prepare_top4_fixed_cascade import sha256

METRICS = ["accuracy", "precision_macro", "recall_macro", "macro_f1"]


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def metrics(y, pred, labels):
    return dict(accuracy=float(accuracy_score(y, pred)),
                precision_macro=float(precision_score(y, pred, labels=labels, average="macro", zero_division=0)),
                recall_macro=float(recall_score(y, pred, labels=labels, average="macro", zero_division=0)),
                macro_f1=float(f1_score(y, pred, labels=labels, average="macro", zero_division=0)))


def score_matrix(model, x, labels):
    if not np.array_equal(model.classes_, labels):
        raise ValueError("classifier class order differs from frozen class order")
    scores = np.asarray(model.decision_function(x), dtype=float)
    if scores.ndim == 1:
        scores = np.column_stack([-scores / 2, scores / 2])
    if scores.shape != (len(x), len(labels)) or not np.isfinite(scores).all():
        raise ValueError("invalid score shape or values")
    return scores


def confidence(scores, gate):
    if gate == "margin":
        ordered = np.sort(scores, axis=1)
        return ordered[:, -1] - ordered[:, -2]
    if gate == "maximum_score":
        return np.max(scores, axis=1)
    if gate == "softmax_entropy":
        shifted = scores - scores.max(axis=1, keepdims=True)
        logp = shifted - np.log(np.exp(shifted).sum(axis=1, keepdims=True))
        return -np.sum(np.exp(logp) * logp, axis=1)
    raise ValueError(gate)


def gate_mask(oof_scores, test_scores, q, gate):
    train_value, test_value = confidence(oof_scores, gate), confidence(test_scores, gate)
    threshold = float(np.quantile(train_value, 1 - q if gate == "softmax_entropy" else q))
    mask = test_value >= threshold if gate == "softmax_entropy" else test_value <= threshold
    return mask, threshold


def exact_budget_mask(scores, count, gate):
    values = confidence(scores, gate)
    order = np.argsort(-values if gate == "softmax_entropy" else values, kind="stable")
    mask = np.zeros(len(scores), dtype=bool)
    mask[order[:count]] = True
    return mask


def random_control(y, cheap_pred, direct_pred, mask, labels, seed):
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(100):
        random_mask = np.zeros(len(y), dtype=bool)
        random_mask[rng.choice(len(y), size=int(mask.sum()), replace=False)] = True
        values.append(metrics(y, np.where(random_mask, direct_pred, cheap_pred), labels))
    return {name: {"mean": float(np.mean([v[name] for v in values])),
                   "std": float(np.std([v[name] for v in values], ddof=1))} for name in METRICS}


def projected_cost(condition, cheap, mask):
    costs = condition["component_costs_ms"]
    return costs[cheap] + float(mask.mean()) * sum(costs[b] for b in condition["top4_blocks"] if b != cheap)


def run_condition(c, folder):
    folder.mkdir(parents=True, exist_ok=False)
    dump(folder / "status.json", {"status": "running", "id": c["id"]})
    start = time.perf_counter()
    try:
        if c["missing_component_costs"]:
            raise ArithmeticError("unavailable faithful KTH costs: " + ",".join(c["missing_component_costs"]))
        train, test = np.asarray(c["train_indices"]), np.asarray(c["test_indices"])
        cache = {}
        y = None
        for block in sorted(set(c["cheap_candidates"] + c["top4_blocks"])):
            base = ROOT / c["embedding_directory"]
            labels = canonical_labels(np.load(base / f"{block}_labels.npy", allow_pickle=False))
            if y is not None and not np.array_equal(y, labels):
                raise ValueError("cache labels differ")
            y = labels
            x = np.load(base / f"{block}.npy", allow_pickle=False)
            if not np.isfinite(x).all():
                raise ValueError("nonfinite embedding")
            cache[block] = l2_rows(x)
        labels = np.unique(y)
        global_to_train = {int(g): i for i, g in enumerate(train)}
        oof, test_scores, preds, models = {}, {}, {}, {}
        specifications = {b: [b] for b in c["cheap_candidates"]}
        specifications["top4_direct"] = c["top4_blocks"]
        # OOF phase: no test score or model evaluation until both selections exist.
        for name, blocks in specifications.items():
            matrix = np.concatenate([cache[b] for b in blocks], axis=1)
            scores = np.full((len(train), len(labels)), np.nan)
            for fold in c["inner_folds"]:
                fit, val = np.asarray(fold["fit_indices"]), np.asarray(fold["validation_indices"])
                model = make_model("svm", 42)
                model.fit(matrix[fit], y[fit])
                scores[[global_to_train[int(g)] for g in val]] = score_matrix(model, matrix[val], labels)
            if not np.isfinite(scores).all():
                raise ValueError("incomplete OOF score coverage")
            oof[name] = scores
            print(f"  {c['id']} OOF {name}", flush=True)
        candidates = {b: (labels[np.argmax(oof[b], axis=1)], confidence(oof[b], "margin"))
                      for b in c["cheap_candidates"]}
        top4_oof = labels[np.argmax(oof["top4_direct"], axis=1)]
        selected = select(candidates, top4_oof, y[train], labels, c["top4_blocks"],
                          c["component_costs_ms"], c["cheap_candidates"])
        restricted = select(candidates, top4_oof, y[train], labels, c["top4_blocks"],
                            c["component_costs_ms"], ["resnet50"])
        dump(folder / "selection_pretest.json", {"selected": selected, "resnet50_only": restricted,
              "selection_metric": "macro_f1", "reporting_primary_metric": "accuracy"})
        for name, blocks in specifications.items():
            matrix = np.concatenate([cache[b] for b in blocks], axis=1)
            model = make_model("svm", 42)
            model.fit(matrix[train], y[train])
            test_scores[name] = score_matrix(model, matrix[test], labels)
            preds[name] = labels[np.argmax(test_scores[name], axis=1)]
            models[name] = model
        joblib.dump(models, folder / "models.joblib", compress=3)
        result = {"id": c["id"], "dataset": c["dataset"], "protocol": c["protocol"],
                  "top4_blocks": c["top4_blocks"], "n_test": len(test), "primary_metric": "accuracy",
                  "metric_scope": "same cached predictions; costs projected, no online latency",
                  "metrics": {name: metrics(y[test], pred, labels) for name, pred in preds.items()}}
        masks = {}
        for route_name, selection in [("selected_cascade", selected), ("resnet50_route", restricted)]:
            chosen = selection["selected"]
            base = chosen["cheap"]
            if chosen["route"] == "topk_direct":
                mask = np.ones(len(test), dtype=bool)
                pred = preds["top4_direct"].copy()
                cost = sum(c["component_costs_ms"][b] for b in c["top4_blocks"])
            else:
                mask = confidence(test_scores[base], "margin") <= chosen["threshold"]
                pred = np.where(mask, preds["top4_direct"], preds[base])
                cost = projected_cost(c, base, mask)
            preds[route_name], masks[route_name] = pred, mask
            result[route_name] = dict(route=chosen["route"], cheap=base, q=chosen["budget"],
                                     request_fraction=float(mask.mean()), projected_component_ms=float(cost),
                                     metrics=metrics(y[test], pred, labels))
        result["direct_projected_component_ms"] = sum(c["component_costs_ms"][b] for b in c["top4_blocks"])
        chosen_base = selected["selected"]["cheap"] or "resnet50"
        result["random_selected_route"] = random_control(y[test], preds[chosen_base], preds["top4_direct"],
                                                         masks["selected_cascade"], labels, 420000 + c["outer_fold"])
        e2 = []
        for q in (.25, .5, .75):
            margin_mask, _ = gate_mask(oof[chosen_base], test_scores[chosen_base], q, "margin")
            for gate in ("margin", "maximum_score", "softmax_entropy"):
                mask, threshold = gate_mask(oof[chosen_base], test_scores[chosen_base], q, gate)
                for mode, active in [("oof_quantile", mask),
                                     ("matched_test_count_diagnostic", exact_budget_mask(test_scores[chosen_base], int(margin_mask.sum()), gate))]:
                    pred = np.where(active, preds["top4_direct"], preds[chosen_base])
                    e2.append({"dataset": c["dataset"], "id": c["id"], "q": q, "gate": gate,
                               "base": chosen_base, "mode": mode, "threshold_oof": threshold,
                               "request_fraction": float(active.mean()), "metrics": metrics(y[test], pred, labels),
                               "projected_component_ms": projected_cost(c, chosen_base, active)})
            res_mask, _ = gate_mask(oof["resnet50"], test_scores["resnet50"], q, "margin")
            result.setdefault("resnet50_q_random", {})[str(q)] = random_control(
                y[test], preds["resnet50"], preds["top4_direct"], res_mask, labels, 420100 + int(q * 100) + c["outer_fold"])
        dump(folder / "e2.json", e2)
        dump(folder / "result.json", result)
        payload = {"class_order": labels.tolist(), "test_indices": test.tolist(), "y_true": y[test].tolist(),
                   "predictions": {k: v.tolist() for k, v in preds.items()},
                   "request_masks": {k: v.tolist() for k, v in masks.items()},
                   "oof_scores": {k: v.tolist() for k, v in oof.items()},
                   "test_scores": {k: v.tolist() for k, v in test_scores.items()}}
        with gzip.open(folder / "scores_predictions.json.gz", "wt", encoding="utf-8") as handle:
            json.dump(payload, handle, separators=(",", ":"), allow_nan=False)
        checksums = {p.name: sha256(p) for p in folder.iterdir() if p.is_file() and p.name != "status.json"}
        dump(folder / "status.json", {"status": "complete", "id": c["id"], "seconds": time.perf_counter() - start,
                                    "sha256": checksums})
        print(f"DONE {c['id']}: acc direct={result['metrics']['top4_direct']['accuracy']:.6f}, cascade={result['selected_cascade']['metrics']['accuracy']:.6f}", flush=True)
        return "complete"
    except Exception as exc:
        dump(folder / "status.json", {"status": "requires_review", "id": c["id"],
                                      "error": str(exc), "traceback": traceback.format_exc(), "retry_allowed": False})
        print(f"REQUIRES_REVIEW {c['id']}: {exc}", flush=True)
        return "requires_review"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    prep = ROOT / "results/analysis/top4_fixed_preparation_20261114_v1"
    provenance = json.loads((prep / "provenance.json").read_text())
    for name, rec in provenance["sources"].items():
        if sha256(ROOT / name) != rec["sha256"]:
            raise ValueError(f"frozen input changed: {name}")
    conditions = json.loads((prep / "conditions.json").read_text())
    new_profile_paths = [ROOT / "results/analysis/kth_top4_component_profile_20261115_v2/status.json",
                         ROOT / "results/analysis/kth_top4_remaining_components_20261115_v1/status.json"]
    accepted = {}
    for path in new_profile_paths:
        rec = json.loads(path.read_text())
        for block, row in rec["blocks"].items():
            if row["min_reference_cosine"] >= .999:
                accepted[block] = row["mean_ms"]
    for c in conditions:
        if c["dataset"] == "KTHTIPS2b":
            needed = sorted(set(c["cheap_candidates"] + c["top4_blocks"]))
            c["component_costs_ms"] = {b: accepted.get(b) for b in needed}
            c["missing_component_costs"] = sorted(set(needed) - accepted.keys())
    recipe = {"primary_reporting_metric": "accuracy", "secondary_metrics": METRICS[1:],
              "metric_change_date": "2026-11-15", "previous_tests_already_observed": True,
              "selection_unchanged": "macro-F1 OOF tolerance .005; existing ranking and route selection",
              "fidelity_threshold": .999, "cpu_threads": 2, "random_repeats": 100,
              "seed": 42, "fixed_k": 4, "quantiles": [.25, .5, .75],
              "versions": {p: importlib.metadata.version(p) for p in ["numpy", "scipy", "scikit-learn", "pandas"]},
              "e2": "OOF thresholds primary; exact test-count ranking is a separate label-free batch diagnostic",
              "costs": "historical proxies for five datasets; new KTH profile with explicit parity failures",
              "scientific_failure_action": "requires_review, no retries, no complete means for partial datasets"}
    sources = {str(p.relative_to(ROOT)): sha256(p) for p in
               [Path(__file__), ROOT / "tests/test_top4_fixed_e1_e2.py", prep / "conditions.json",
                prep / "provenance.json", *new_profile_paths]}
    dump(output / "protocol_frozen.json", {"recipe": recipe, "conditions": conditions, "sources": sources,
                                          "original_preparation": provenance})
    report = {"status": "running", "expected": 27, "states": {}, "primary_metric": "accuracy",
              "protocol_sha256": sha256(output / "protocol_frozen.json")}
    dump(output / "status.json", report)
    with (ROOT / "results/analysis/gpu.lock").open("a") as lock, threadpool_limits(limits=2):
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            for c in conditions:
                report["states"][c["id"]] = run_condition(c, output / "conditions" / c["id"])
                dump(output / "status.json", report)
    report["status"] = "complete" if all(s == "complete" for s in report["states"].values()) else "requires_review"
    dump(output / "status.json", report)


if __name__ == "__main__":
    main()
