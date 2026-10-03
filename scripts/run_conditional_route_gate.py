#!/usr/bin/env python3
"""Exploratory train-fitted gate over fixed texture-descriptor routes.

All routing targets, thresholds and baseline choices use only the outer train.
The outer test is evaluated once for each prespecified acquisition budget.
Cached embeddings simulate acquisition; costs sum previously measured online
descriptor components and are *not* routed image-to-prediction wall time.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from run_confirmatory_nested import load_manifest, make_model, official_split_indices  # noqa: E402
from run_conditional_route_feasibility import (  # noqa: E402
    DATASETS, ROUTES, file_hash, load_blocks,
)

ROUTE_NAMES = tuple(ROUTES)
EXTRA_ROUTES = tuple(name for name in ROUTE_NAMES if name != "small")
DEFAULT_COST = {
    "Outex13Official1360": (
        ROOT / "results/exploratory/adaptive_descriptor_pilot/cost_budget_comparison/"
        "primary22_e2e/Outex_official1_primary22_online_components.json"
    ),
    "DTD": (
        ROOT / "results/exploratory/conditional_acquisition/timing/"
        "DTD_official1_n50_components.json"
    ),
}
BUDGETS = (0.25, 0.5, 0.75)


def load_oof(path: Path, expected_rows: np.ndarray, y: np.ndarray,
             hashes: dict[str, str], manifest_sha: str) -> dict[str, np.ndarray]:
    info = json.loads(path.read_text(encoding="utf-8"))
    if info.get("status") != "EXPLORATORY_TRAIN_ONLY":
        raise ValueError("OOF artifact has an unexpected status")
    if info.get("manifest_sha256") != manifest_sha or info.get("embedding_sha256") != hashes:
        raise ValueError("OOF provenance does not match current inputs")
    if info.get("routes") != {k: list(v) for k, v in ROUTES.items()}:
        raise ValueError("OOF routes do not match current candidates")
    with path.with_name(path.stem + "_oof.csv").open(newline="", encoding="utf-8") as handle:
        records = list(csv.DictReader(handle))
    rows = np.asarray([int(row["row_id"]) for row in records])
    labels = np.asarray([int(row["label"]) for row in records])
    if not np.array_equal(rows, expected_rows) or not np.array_equal(labels, y[expected_rows]):
        raise ValueError("OOF rows or labels differ from the purged outer training partition")
    return {name: np.asarray([int(row[name]) for row in records]) for name in ROUTE_NAMES}


def load_costs(path: Path) -> tuple[dict[str, float], dict]:
    source = json.loads(path.read_text(encoding="utf-8"))
    per_block = source["per_descriptor_latency_ms"]
    needed = {block for route in ROUTES.values() for block in route}
    if not needed.issubset(per_block):
        raise ValueError("measured component timing is absent for a route block")
    if any(
        per_block[block].get("min_reference_cosine", 1.0) < 0.999
        for block in needed
    ):
        raise ValueError("measured extractor failed cached-feature agreement")
    legacy_checks = source.get("method_routes", {}).get("Top-k22", {}).get(
        "extractor_min_cosine", {}
    )
    if any(legacy_checks.get(block, 0.0) < 0.999 for block in needed) and legacy_checks:
        raise ValueError("legacy measured extractor failed cached-feature agreement")
    route_costs = {
        name: float(sum(per_block[block]["mean"] for block in blocks))
        for name, blocks in ROUTES.items()
    }
    if any(value <= 0 for value in route_costs.values()):
        raise ValueError("nonpositive route cost")
    provenance = {
        "source": str(path),
        "sha256": file_hash(path),
        "measurement_dataset": source["dataset"],
        "measurement_protocol": source["protocol"],
        "device": source["device"],
        "model_load_excluded": source.get(
            "load_model_and_svm_fit_excluded",
            source.get("model_load_and_svm_fit_excluded"),
        ),
        "interpretation": (
            "Sums of measured per-descriptor mean extraction times; "
            "not direct routed-system latency. Check measurement_dataset "
            "before interpreting dataset-specific costs."
        ),
    }
    return route_costs, provenance


def score_features(scores: np.ndarray, embedded: np.ndarray, pca: PCA) -> np.ndarray:
    top = np.sort(np.asarray(scores), axis=1)[:, ::-1]
    scaled = scores - np.max(scores, axis=1, keepdims=True)
    probs = np.exp(scaled)
    probs /= np.sum(probs, axis=1, keepdims=True)
    entropy = -np.sum(probs * np.log(np.maximum(probs, 1e-12)), axis=1)
    stats = np.column_stack([
        top[:, 0], top[:, 1], top[:, 0] - top[:, 1],
        top[:, 1] - top[:, 2], np.std(scores, axis=1), entropy,
    ])
    return np.column_stack([stats, pca.transform(embedded)])


def base_oof_scores(base: np.ndarray, y: np.ndarray, groups: np.ndarray,
                    outer_train: np.ndarray, seed: int, n_splits: int) -> np.ndarray:
    classes = np.unique(y[outer_train])
    if len(classes) < 3:
        raise ValueError("gate score features require at least three classes")
    result = np.full((len(outer_train), len(classes)), np.nan, dtype=np.float64)
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for fit_pos, val_pos in splitter.split(
        outer_train, y[outer_train], groups[outer_train]
    ):
        fit_rows, val_rows = outer_train[fit_pos], outer_train[val_pos]
        if set(groups[fit_rows]).intersection(groups[val_rows]):
            raise AssertionError("inner group leakage")
        model = make_model("svm", seed)
        model.fit(base[fit_rows], y[fit_rows])
        if not np.array_equal(model.classes_, classes):
            raise ValueError("an inner fold lacks a class")
        result[val_pos] = model.decision_function(base[val_rows])
    if not np.isfinite(result).all():
        raise AssertionError("OOF base scores do not cover all outer-train rows")
    return result


def choose(scores: np.ndarray, budget: float, threshold: float,
           route_names: tuple[str, ...] = EXTRA_ROUTES) -> np.ndarray:
    if not 0 < budget < 1:
        raise ValueError("budget must be strictly between zero and one")
    if scores.ndim != 2 or scores.shape[1] != len(route_names):
        raise ValueError("invalid gate score shape")
    best = np.argmax(scores, axis=1)
    strength = scores[np.arange(len(scores)), best]
    return np.where(strength >= threshold, best + 1, 0)


def route_predictions(route_ids: np.ndarray, predictions: dict[str, np.ndarray]) -> np.ndarray:
    ordered = np.stack([predictions[name] for name in ROUTE_NAMES], axis=1)
    return ordered[np.arange(len(route_ids)), route_ids]


def metrics(y: np.ndarray, pred: np.ndarray, route_ids: np.ndarray,
            route_costs: dict[str, float]) -> dict:
    costs = np.asarray([route_costs[name] for name in ROUTE_NAMES])
    return {
        "macro_f1": float(f1_score(y, pred, average="macro")),
        "accuracy": float(accuracy_score(y, pred)),
        "request_fraction": float(np.mean(route_ids != 0)),
        "route_counts": {name: int(np.sum(route_ids == i)) for i, name in enumerate(ROUTE_NAMES)},
        "component_cost_mean_ms": float(np.mean(costs[route_ids])),
    }


def matched_component_sample(cost_path: Path, test_rows: np.ndarray,
                             route_ids: np.ndarray) -> dict | None:
    """Sum measured components for routes actually chosen on timed test rows."""
    source = json.loads(cost_path.read_text(encoding="utf-8"))
    timed_rows = source.get("rows", [])
    blocks = source["per_descriptor_latency_ms"]
    if not timed_rows or any("durations_ms" not in blocks[name] for name in blocks):
        return None
    if any(len(blocks[name]["durations_ms"]) != len(timed_rows) for name in blocks):
        raise ValueError("component timing length does not match timed rows")
    test_pos = {int(row_id): pos for pos, row_id in enumerate(test_rows)}
    if any(int(row_id) not in test_pos for row_id in timed_rows):
        raise ValueError("timing rows are not contained in outer test")
    per_image = []
    for timing_pos, row_id in enumerate(timed_rows):
        route = ROUTE_NAMES[route_ids[test_pos[int(row_id)]]]
        per_image.append(sum(
            float(blocks[block]["durations_ms"][timing_pos]) for block in ROUTES[route]
        ))
    return {
        "n": len(per_image),
        "mean_ms": float(np.mean(per_image)),
        "median_ms": float(np.median(per_image)),
        "p95_ms": float(np.percentile(per_image, 95)),
        "interpretation": "Measured component sums on matched timed test images; not routed wall time.",
    }


def run(dataset: str, split: int, seed: int, output: Path,
        oof_root: Path, cost_path: Path) -> dict:
    embedding_dir, result_dir = DATASETS[dataset]
    cache, y, hashes = load_blocks(embedding_dir)
    groups, rows = load_manifest(result_dir, dataset, y)
    train, test = official_split_indices(rows, split)
    manifest_sha = file_hash(result_dir / "sample_manifests" / f"{dataset}.csv")
    oof_path = oof_root / f"{dataset}_official{split}_seed{seed}.json"
    info = json.loads(oof_path.read_text(encoding="utf-8"))
    if info.get("dataset") != dataset or info.get("outer_split") != split or info.get("seed") != seed:
        raise ValueError("OOF artifact protocol does not match request")
    oof = load_oof(oof_path, train, y, hashes, manifest_sha)
    route_costs, cost_provenance = load_costs(cost_path)
    if cost_provenance["measurement_dataset"] != dataset:
        raise ValueError("component timing must come from the same dataset")
    matrices = {
        name: np.concatenate([cache[block] for block in blocks], axis=1)
        for name, blocks in ROUTES.items()
    }
    scores_train = base_oof_scores(cache["dinov2_small"], y, groups, train,
                                   seed, info["inner_folds"])
    pca = PCA(n_components=16, svd_solver="randomized", random_state=seed)
    pca.fit(cache["dinov2_small"][train])
    features_train = score_features(scores_train, cache["dinov2_small"][train], pca)
    models = {}
    base_correct = (oof["small"] == y[train]).astype(float)
    incremental_costs = np.asarray([
        route_costs[name] - route_costs["small"] for name in EXTRA_ROUTES
    ])
    if np.any(incremental_costs <= 0):
        raise ValueError("every expansion must cost more than the base")
    for name in EXTRA_ROUTES:
        target = (oof[name] == y[train]).astype(float) - base_correct
        model = make_pipeline(StandardScaler(), Ridge(alpha=50.0))
        model.fit(features_train, target)
        models[name] = model
    train_utility = np.column_stack([
        models[name].predict(features_train) for name in EXTRA_ROUTES
    ]) / incremental_costs
    route_models = {}
    test_predictions = {}
    base_model = None
    for name, x in matrices.items():
        model = make_model("svm", seed)
        model.fit(x[train], y[train])
        route_models[name] = model
        test_predictions[name] = np.asarray(model.predict(x[test]))
        if name == "small":
            base_model = model
    assert base_model is not None
    scores_test = base_model.decision_function(cache["dinov2_small"][test])
    features_test = score_features(scores_test, cache["dinov2_small"][test], pca)
    test_utility = np.column_stack([
        models[name].predict(features_test) for name in EXTRA_ROUTES
    ]) / incremental_costs
    margin_train = np.sort(scores_train, axis=1)[:, -1] - np.sort(scores_train, axis=1)[:, -2]
    margin_test = np.sort(scores_test, axis=1)[:, -1] - np.sort(scores_test, axis=1)[:, -2]
    fixed = {}
    for i, name in enumerate(ROUTE_NAMES):
        route_ids = np.full(len(test), i, dtype=int)
        fixed[name] = metrics(y[test], test_predictions[name], route_ids, route_costs)
    budgets = {}
    sample_records = []
    for q in BUDGETS:
        # Quantiles are learned only from OOF train scores. Ties may alter
        # the observed test request fraction, which is reported rather than fixed.
        threshold = float(np.quantile(np.max(train_utility, axis=1), 1 - q))
        gate_ids = choose(test_utility, q, threshold)
        gate_result = metrics(
            y[test], route_predictions(gate_ids, test_predictions), gate_ids, route_costs
        )
        margin_threshold = float(np.quantile(margin_train, q))
        margin_requests_train = margin_train <= margin_threshold
        # Select the expansion for the margin cascade from train OOF only.
        margin_candidates = {}
        for i, name in enumerate(EXTRA_ROUTES, start=1):
            pred = np.where(margin_requests_train, oof[name], oof["small"])
            gain = f1_score(y[train], pred, average="macro") - f1_score(
                y[train], oof["small"], average="macro"
            )
            margin_candidates[name] = gain / incremental_costs[i - 1]
        chosen_margin_route = max(margin_candidates, key=margin_candidates.get)
        margin_ids = np.where(margin_test <= margin_threshold,
                              ROUTE_NAMES.index(chosen_margin_route), 0)
        margin_result = metrics(
            y[test], route_predictions(margin_ids, test_predictions), margin_ids, route_costs
        )
        gate_predictions = route_predictions(gate_ids, test_predictions)
        margin_predictions = route_predictions(margin_ids, test_predictions)
        for pos, row_id in enumerate(test):
            sample_records.append({
                "budget": q,
                "row_id": int(row_id),
                "label": int(y[row_id]),
                "gate_route": ROUTE_NAMES[gate_ids[pos]],
                "gate_prediction": int(gate_predictions[pos]),
                "margin_route": ROUTE_NAMES[margin_ids[pos]],
                "margin_prediction": int(margin_predictions[pos]),
                "base_prediction": int(test_predictions["small"][pos]),
            })
        budgets[str(q)] = {
            "gate": gate_result,
            "margin_cascade": margin_result,
            "gate_matched_timing_sample": matched_component_sample(cost_path, test, gate_ids),
            "margin_matched_timing_sample": matched_component_sample(cost_path, test, margin_ids),
            "gate_train_utility_threshold": threshold,
            "margin_train_threshold": margin_threshold,
            "margin_route_selected_on_train": chosen_margin_route,
        }
    result = {
        "status": "EXPLORATORY_OUTER_TEST_EVALUATION",
        "dataset": dataset,
        "outer_split": split,
        "seed": seed,
        "n_train": len(train),
        "n_test": len(test),
        "prespecified_budgets": BUDGETS,
        "gate": (
            "Ridge(alpha=50) per expansion predicts OOF signed correctness "
            "gain from base SVM scores and train-fitted 16-PC base embeddings; "
            "choose maximum predicted gain per measured incremental component cost."
        ),
        "route_component_cost_ms": route_costs,
        "cost_provenance": cost_provenance,
        "oof_provenance": {"source": str(oof_path), "sha256": file_hash(oof_path)},
        "manifest_sha256": manifest_sha,
        "embedding_sha256": hashes,
        "fixed_routes": fixed,
        "budgets": budgets,
        "limitations": [
            "The route library was devised after exploratory work on this repository; this is not a fresh confirmatory test.",
            "Cached embeddings simulate selective acquisition; actual routed wall time is not measured here.",
            "Component time is summed from a separate 50-image online benchmark with model load excluded; see cost_provenance for its dataset.",
            "Only one outer split is evaluated; no significance claim is warranted.",
            "The gate uses an additive per-image correctness proxy, while macro-F1 is evaluated externally.",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{dataset}_official{split}_seed{seed}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with path.with_name(path.stem + "_per_sample.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_records[0]))
        writer.writeheader()
        writer.writerows(sample_records)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    parser.add_argument("--split", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--oof-root", type=Path, default=(
        ROOT / "results/exploratory/conditional_acquisition/feasibility"
    ))
    parser.add_argument("--cost", type=Path)
    parser.add_argument("--output", type=Path, default=(
        ROOT / "results/exploratory/conditional_acquisition/gate"
    ))
    args = parser.parse_args()
    result = run(args.dataset, args.split, args.seed, args.output,
                 args.oof_root, args.cost or DEFAULT_COST[args.dataset])
    print(json.dumps({
        "dataset": args.dataset,
        "fixed_routes": {k: v["macro_f1"] for k, v in result["fixed_routes"].items()},
        "budgets": {
            q: {
                "gate_macro_f1": row["gate"]["macro_f1"],
                "margin_macro_f1": row["margin_cascade"]["macro_f1"],
                "gate_component_ms": row["gate"]["component_cost_mean_ms"],
            }
            for q, row in result["budgets"].items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
