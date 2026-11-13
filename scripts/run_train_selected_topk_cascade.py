#!/usr/bin/env python3
"""Select a Top-k cascade budget using grouped outer-training predictions only.

This is an exploratory analysis of previously archived outer-test predictions.
The fixed 0.005 macro-F1 tolerance was chosen after earlier exploratory runs;
training-only selection prevents within-fold test leakage, but does not turn
this analysis into a preregistered or independent confirmation.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedGroupKFold

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from run_adaptive_descriptor_pilot import margin  # noqa: E402
from run_adaptive_topk_cascade import sha  # noqa: E402
from run_confirmatory_nested import audit_gate, load_dataset, load_manifest, make_model, manifest_groups  # noqa: E402
from run_topk_individual_control import outer_indices  # noqa: E402
from report_cost_aware_topk import (CASCADE, DEFAULT_KTH_COST, DEFAULT_PROXY_COST,
                                     SOURCES, component_costs)  # noqa: E402

BUDGETS = (0.25, 0.5, 0.75)


def select_route(margins: np.ndarray, cheap_pred: np.ndarray,
                 topk_pred: np.ndarray, labels: np.ndarray,
                 costs: dict[str, float], cheap: list[str], topk: list[str],
                 tolerance: float) -> dict:
    """Use only outer-training OOF predictions and a fixed cost profile."""
    if tolerance < 0 or not np.isfinite(tolerance):
        raise ValueError("tolerance must be finite and nonnegative")
    if not (len(margins) == len(cheap_pred) == len(topk_pred) == len(labels)):
        raise ValueError("OOF arrays have different lengths")
    if not np.isfinite(margins).all():
        raise ValueError("incomplete OOF margins")
    missing = (set(cheap) | set(topk)) - costs.keys()
    if missing:
        raise ValueError(f"missing measured block costs: {sorted(missing)}")
    all_labels = np.unique(labels)

    def score(pred: np.ndarray) -> float:
        return float(f1_score(labels, pred, labels=all_labels,
                              average="macro", zero_division=0))

    direct = sum(costs[name] for name in set(topk))
    base = sum(costs[name] for name in set(cheap))
    incremental = sum(costs[name] for name in set(topk) - set(cheap))
    reference_f1 = score(topk_pred)
    candidates = [{"route": "topk_direct", "budget": None, "threshold": None,
                   "oof_macro_f1": reference_f1, "oof_request_fraction": 1.0,
                   "projected_component_ms": direct, "eligible": True}]
    for budget in BUDGETS:
        threshold = float(np.quantile(margins, budget))
        request = margins <= threshold
        candidate_f1 = score(np.where(request, topk_pred, cheap_pred))
        candidates.append({
            "route": "cascade", "budget": budget, "threshold": threshold,
            "oof_macro_f1": candidate_f1,
            "oof_request_fraction": float(request.mean()),
            "projected_component_ms": base + float(request.mean()) * incremental,
            "eligible": candidate_f1 >= reference_f1 - tolerance - 1e-12,
        })
    eligible = [row for row in candidates if row["eligible"]]
    chosen = min(eligible, key=lambda row: (row["projected_component_ms"],
                                             row["route"] != "topk_direct"))
    return {"selected": chosen, "candidates": candidates,
            "oof_topk_macro_f1": reference_f1,
            "oof_cheap_macro_f1": score(cheap_pred),
            "f1_tolerance": tolerance, "base_component_ms": base,
            "incremental_component_ms": incremental,
            "topk_direct_component_ms": direct}


def oof_predictions(cache: dict, train: np.ndarray, y: np.ndarray,
                    groups: np.ndarray, cheap: list[str], topk: list[str],
                    classifier: str, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Predict each outer-training row with models that never trained on it."""
    n_splits = min(4, len(np.unique(groups[train])))
    if n_splits < 2:
        raise ValueError("inner grouping leaves fewer than two folds")
    x_cheap = np.concatenate([cache[name] for name in cheap], axis=1)
    x_topk = np.concatenate([cache[name] for name in topk], axis=1)
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True,
                                    random_state=seed + 1)
    margins = np.full(len(train), np.nan)
    pred_cheap = np.full(len(train), -1, dtype=int)
    pred_topk = np.full(len(train), -1, dtype=int)
    for rel_fit, rel_val in splitter.split(x_cheap[train], y[train], groups[train]):
        cheap_model, topk_model = make_model(classifier, seed), make_model(classifier, seed)
        cheap_model.fit(x_cheap[train[rel_fit]], y[train[rel_fit]])
        topk_model.fit(x_topk[train[rel_fit]], y[train[rel_fit]])
        margins[rel_val] = margin(cheap_model, x_cheap[train[rel_val]])
        pred_cheap[rel_val] = cheap_model.predict(x_cheap[train[rel_val]])
        pred_topk[rel_val] = topk_model.predict(x_topk[train[rel_val]])
    if (not np.isfinite(margins).all() or (pred_cheap < 0).any()
            or (pred_topk < 0).any()):
        raise ValueError("incomplete OOF prediction coverage")
    return margins, pred_cheap, pred_topk


def result_root(dataset: str, directory: str) -> Path:
    return (REPO / "results/confirmatory" if dataset in {"DTD", "FMD", "CUReT"}
            else REPO / "results/extensions" / directory)


def outer_split(entry: dict, y: np.ndarray, groups: np.ndarray, rows: list) -> tuple[np.ndarray, np.ndarray]:
    protocol = entry["protocol"]
    official = int(protocol.removeprefix("official").split("_")[0]) if protocol.startswith("official") else None
    direction = protocol.split(":", 1)[1] if protocol.startswith("curet_half_indices:") else None
    return outer_indices(entry["dataset"], int(entry["seed"]), int(entry["outer_fold"]),
                         y, groups, rows, official, direction, "_inverted" in protocol)


def evaluate_archive(entry: dict, path: Path, selection: dict,
                     test: np.ndarray, y: np.ndarray) -> dict:
    """Open held-out predictions only after the selection object exists."""
    chosen = selection["selected"]
    with path.with_name(path.stem + "_per_sample.csv").open(newline="", encoding="utf-8") as handle:
        sample_rows = list(csv.DictReader(handle))
    budget = chosen["budget"] if chosen["budget"] is not None else BUDGETS[0]
    selected_rows = [row for row in sample_rows if float(row["budget"]) == budget]
    by_id = {int(row["row_id"]): row for row in selected_rows}
    if len(by_id) != len(test) or set(by_id) != set(map(int, test)):
        raise ValueError(f"held-out row mismatch in {path}")
    test_labels = np.array([int(by_id[int(idx)]["label"]) for idx in test])
    if not np.array_equal(test_labels, y[test]):
        raise ValueError(f"held-out label mismatch in {path}")
    key = "adaptive_pred" if chosen["route"] == "cascade" else "topk_pred"
    pred = np.array([int(by_id[int(idx)][key]) for idx in test])
    request = np.array([int(by_id[int(idx)]["request_extra"]) for idx in test])
    score = float(f1_score(y[test], pred, labels=np.unique(y),
                           average="macro", zero_division=0))
    expected = (next(row for row in entry["budgets"] if row["target_budget"] == budget)
                ["adaptive"]["macro_f1"] if chosen["route"] == "cascade"
                else entry["topk_always"]["macro_f1"])
    if abs(score - float(expected)) > 1e-10:
        raise ValueError(f"held-out score mismatch in {path}")
    fraction = float(request.mean()) if chosen["route"] == "cascade" else 1.0
    cost = (selection["base_component_ms"] + fraction * selection["incremental_component_ms"]
            if chosen["route"] == "cascade" else selection["topk_direct_component_ms"])
    return {"outer_test_macro_f1": score,
            "outer_test_topk_macro_f1": float(entry["topk_always"]["macro_f1"]),
            "outer_test_request_fraction": fraction,
            "outer_test_component_ms": cost,
            "outer_test_topk_component_ms": selection["topk_direct_component_ms"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=CASCADE)
    parser.add_argument("--kth-costs", type=Path, default=DEFAULT_KTH_COST)
    parser.add_argument("--proxy-costs", type=Path, default=DEFAULT_PROXY_COST)
    parser.add_argument("--output", type=Path, default=CASCADE / "train_selected_primary22")
    parser.add_argument("--f1-tolerance", type=float, default=0.005)
    parser.add_argument("--dataset", choices=tuple(SOURCES), help="optional one-dataset run")
    args = parser.parse_args()
    proxy_source = json.loads(args.proxy_costs.read_text(encoding="utf-8"))
    if (proxy_source.get("dataset") != "Outex13Official1360"
            or proxy_source.get("timing_partition") != "train"):
        raise ValueError("proxy timing must come from official Outex training images")
    kth_costs = component_costs(args.kth_costs)
    proxy_costs = component_costs(args.proxy_costs)
    if "vit_b16" not in proxy_costs and "vit_b16" in kth_costs:
        proxy_costs["vit_b16"] = kth_costs["vit_b16"]
    output_rows = []
    datasets = {args.dataset: SOURCES[args.dataset]} if args.dataset else SOURCES
    args.output.mkdir(parents=True, exist_ok=True)
    for dataset, directory in datasets.items():
        root = result_root(dataset, directory)
        audit_gate(root, dataset)
        embedding_root = (REPO / "embeddings_extensions" if dataset in
                          {"Outex13Official1360", "SoilOriginal", "KTHTIPS2b"}
                          else REPO / "embeddings" if dataset == "DTD"
                          else REPO / "embeddings_confirmatory")
        cache, y = load_dataset(REPO, dataset, embedding_root=embedding_root)
        groups, rows = load_manifest(root, dataset, y)
        manifest_hash = sha(root / "sample_manifests" / f"{dataset}.csv")
        audit_hash = sha(root / "data_audit.csv")
        control_hash = sha(root / "ngram22_beitv2/topk_individual_control/nested_fold_results.csv")
        paths = sorted((args.root / directory / "exact_archive").glob("*_topk_cascade.json"))
        expected = {"DTD": 10, "FMD": 5, "CUReT": 2, "Outex13Official1360": 1,
                    "SoilOriginal": 5, "KTHTIPS2b": 4}[dataset]
        if len(paths) != expected:
            raise ValueError(f"{dataset}: expected {expected} conditions, found {len(paths)}")
        for path in paths:
            entry = json.loads(path.read_text(encoding="utf-8"))
            provenance = entry["provenance"]
            if (entry["dataset"] != dataset or entry["classifier"] != "svm"
                    or entry["seed"] != 42 or entry["expensive_subset_derived_locally"]
                    or abs(float(entry["reproduction_delta"])) > 1e-10
                    or provenance["manifest_sha256"] != manifest_hash
                    or provenance["audit_sha256"] != audit_hash
                    or provenance["topk_control_sha256"] != control_hash):
                raise ValueError(f"archive/provenance mismatch in {path}")
            cheap, topk = entry["cheap_blocks"], entry["expensive_blocks"]
            for name in set(cheap) | set(topk):
                dataset_dir = "KTH-TIPS2-b" if dataset == "KTHTIPS2b" else dataset
                if provenance["blocks_sha256"][name] != sha(embedding_root / dataset_dir / f"{name}.npy"):
                    raise ValueError(f"embedding changed: {dataset}/{name}")
            first_block = sorted(set(cheap) | set(topk))[0]
            if provenance["labels_sha256"] != sha(
                    embedding_root / dataset_dir / f"{first_block}_labels.npy"):
                raise ValueError(f"embedding labels changed: {dataset}")
            train, test = outer_split(entry, y, groups, rows)
            if len(train) != entry["n_train"] or len(test) != entry["n_test"] or set(groups[train]) & set(groups[test]):
                raise ValueError(f"outer split mismatch in {path}")
            inner_groups = (groups if entry["inner_group_column"] == "group" else
                            manifest_groups(rows, entry["inner_group_column"]))
            margins, pred_cheap, pred_topk = oof_predictions(
                cache, train, y, inner_groups, cheap, topk, "svm", 42)
            costs = kth_costs if dataset == "KTHTIPS2b" else proxy_costs
            selection = select_route(margins, pred_cheap, pred_topk,
                                     y[train], costs, cheap, topk, args.f1_tolerance)
            evaluation = evaluate_archive(entry, path, selection, test, y)
            record = {"dataset": dataset, "protocol": entry["protocol"],
                      "outer_fold": int(entry["outer_fold"]), "seed": 42,
                      "classifier": "svm", "n_outer_train": len(train),
                      "n_outer_test": len(test), "cheap_blocks": cheap,
                      "topk_blocks": topk, "selection": selection,
                      "evaluation": evaluation,
                      "source_archive": {"path": str(path), "sha256": sha(path)},
                      "source_per_sample": {"path": str(path.with_name(path.stem + "_per_sample.csv")),
                                            "sha256": sha(path.with_name(path.stem + "_per_sample.csv"))}}
            (args.output / f"{dataset}_{entry['protocol']}_selection.json".replace(":", "__")).write_text(
                json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            output_rows.append({"dataset": dataset, "protocol": entry["protocol"],
                                "selected_route": selection["selected"]["route"],
                                "budget": selection["selected"]["budget"],
                                "oof_topk_f1": selection["oof_topk_macro_f1"],
                                "oof_selected_f1": selection["selected"]["oof_macro_f1"],
                                "outer_test_f1": evaluation["outer_test_macro_f1"],
                                "outer_test_topk_f1": evaluation["outer_test_topk_macro_f1"],
                                "outer_test_component_ms": evaluation["outer_test_component_ms"],
                                "outer_test_topk_component_ms": evaluation["outer_test_topk_component_ms"]})
            print(f"{dataset} {entry['protocol']}: {selection['selected']['route']} "
                  f"q={selection['selected']['budget']} test F1={evaluation['outer_test_macro_f1']:.4f}",
                  flush=True)
    with (args.output / "selected_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader(); writer.writerows(output_rows)
    summaries = []
    for dataset in datasets:
        subset = [row for row in output_rows if row["dataset"] == dataset]
        summaries.append({"dataset": dataset, "conditions": len(subset),
                          "cascade_selections": sum(row["selected_route"] == "cascade" for row in subset),
                          "mean_macro_f1": float(np.mean([row["outer_test_f1"] for row in subset])),
                          "mean_topk_macro_f1": float(np.mean([row["outer_test_topk_f1"] for row in subset])),
                          "mean_component_ms": float(np.mean([row["outer_test_component_ms"] for row in subset])),
                          "mean_topk_component_ms": float(np.mean([row["outer_test_topk_component_ms"] for row in subset]))})
    report = {"status": "EXPLORATORY_TRAIN_SELECTED_COST_PROXY_NOT_ONLINE_LATENCY",
              "selection_rule": ("lowest projected OOF component cost among q=.25,.5,.75 and "
                                 f"direct Top-k with OOF macro-F1 >= OOF Top-k minus {args.f1_tolerance}"),
              "f1_tolerance": args.f1_tolerance,
              "selection_uses_outer_test_data": False,
              "posthoc_tolerance_warning": "0.005 was fixed after earlier outer-test exploratory analysis; this is not independent confirmation",
              "kth_cost_source": {"path": str(args.kth_costs), "sha256": sha(args.kth_costs)},
              "proxy_cost_source": {"path": str(args.proxy_costs), "sha256": sha(args.proxy_costs)},
              "summaries": summaries}
    (args.output / "selected_summary.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
