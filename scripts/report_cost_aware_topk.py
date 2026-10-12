#!/usr/bin/env python3
"""Exploratory cost-aware fallback for the archived Top-k cascades.

The route is selected from a preset training-side request budget and measured
descriptor costs, never from outer-test labels or the observed test request
fraction. Test scores and observed costs are used only for evaluation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
CASCADE = REPO / "results/exploratory/topk_cascade"
DEFAULT_KTH_COST = CASCADE / "kth_tips2b/timing/latency_KTHTIPS2b_s42_official1_n30.json"
DEFAULT_PROXY_COST = (
    REPO / "results/exploratory/adaptive_descriptor_pilot/cost_budget_comparison/"
    "primary22_e2e/Outex_official1_primary22_online_train_components.json"
)
SOURCES = {
    "DTD": "dtd",
    "FMD": "fmd",
    "CUReT": "curet",
    "Outex13Official1360": "outex13_official1360",
    "SoilOriginal": "soil_original",
    "KTHTIPS2b": "kth_tips2b",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def component_costs(path: Path) -> dict[str, float]:
    source = json.loads(path.read_text(encoding="utf-8"))
    blocks = source.get("blocks", source.get("per_descriptor_latency_ms"))
    if not isinstance(blocks, dict):
        raise ValueError(f"no descriptor timing entries in {path}")
    route_cosines: dict[str, list[float]] = {}
    for route in source.get("method_routes", {}).values():
        for name, cosine in route.get("extractor_min_cosine", {}).items():
            route_cosines.setdefault(name, []).append(float(cosine))
    costs = {}
    for name, row in blocks.items():
        checks = route_cosines.get(name, [])
        if row.get("min_reference_cosine") is not None:
            checks.append(float(row["min_reference_cosine"]))
        if checks and min(checks) < 0.999:
            continue  # Do not use a mismatched extractor as cost evidence.
        value = float(row.get("mean_ms", row.get("mean", float("nan"))))
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"invalid measured cost for {name} in {path}")
        costs[name] = value
    return costs


def choose_route(cheap: list[str], topk: list[str], costs: dict[str, float],
                 training_budget: float) -> tuple[str, float, float, float]:
    """Choose before test: use the cascade only if its projected cost is lower."""
    if not 0 < training_budget < 1 or not cheap or not topk:
        raise ValueError("invalid budget or empty route")
    missing = (set(cheap) | set(topk)) - costs.keys()
    if missing:
        raise ValueError(f"missing measured block costs: {sorted(missing)}")
    base_cost = sum(costs[name] for name in set(cheap))
    direct_cost = sum(costs[name] for name in set(topk))
    incremental_cost = sum(costs[name] for name in set(topk) - set(cheap))
    projected_cascade = base_cost + training_budget * incremental_cost
    route = "cascade" if projected_cascade < direct_cost else "topk_direct"
    return route, base_cost, incremental_cost, direct_cost


def evaluate_one(entry: dict, budget_row: dict, costs: dict[str, float]) -> dict:
    target = float(budget_row["target_budget"])
    route, base_cost, incremental_cost, direct_cost = choose_route(
        entry["cheap_blocks"], entry["expensive_blocks"], costs, target
    )
    requested = float(budget_row["observed_request_fraction"])
    cascade_cost = base_cost + requested * incremental_cost
    return {
        "dataset": entry["dataset"],
        "protocol": entry["protocol"],
        "outer_fold": int(entry["outer_fold"]),
        "target_budget": target,
        "selected_route": route,
        "observed_request_fraction": requested if route == "cascade" else 1.0,
        "macro_f1": (float(budget_row["adaptive"]["macro_f1"])
                     if route == "cascade" else float(entry["topk_always"]["macro_f1"])),
        "topk_macro_f1": float(entry["topk_always"]["macro_f1"]),
        "plain_cascade_macro_f1": float(budget_row["adaptive"]["macro_f1"]),
        "component_cost_ms": cascade_cost if route == "cascade" else direct_cost,
        "plain_cascade_component_cost_ms": cascade_cost,
        "topk_direct_component_cost_ms": direct_cost,
        "projected_cascade_component_cost_ms": base_cost + target * incremental_cost,
        "cheap_blocks": "+".join(entry["cheap_blocks"]),
        "topk_blocks": "+".join(entry["expensive_blocks"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=CASCADE)
    parser.add_argument("--kth-costs", type=Path, default=DEFAULT_KTH_COST)
    parser.add_argument("--proxy-costs", type=Path, default=DEFAULT_PROXY_COST)
    parser.add_argument("--output", type=Path, default=CASCADE / "cost_aware_primary22")
    args = parser.parse_args()
    proxy_source = json.loads(args.proxy_costs.read_text(encoding="utf-8"))
    if proxy_source.get("dataset") != "Outex13Official1360" or proxy_source.get("timing_partition") != "train":
        raise ValueError("cost calibration must use the audited Outex training partition")
    kth_costs = component_costs(args.kth_costs)
    proxy_costs = component_costs(args.proxy_costs)
    # The Outex timing implementation did not reproduce the archived ViT
    # vector; use the separately verified KTH timing for that block instead.
    if "vit_b16" not in proxy_costs and "vit_b16" in kth_costs:
        proxy_costs["vit_b16"] = kth_costs["vit_b16"]
    rows, provenance = [], []
    online_paths = sorted((args.root / "kth_tips2b/online_fair_topk").glob("*.json"))
    online = {}
    for path in online_paths:
        timing = json.loads(path.read_text(encoding="utf-8"))
        if timing.get("budget") != 0.5 or timing.get("n_images") != 30:
            continue
        if any(timing["agreement"][key] != 1.0 for key in
               ("request_decision", "adaptive_prediction", "topk_prediction")):
            raise ValueError(f"online prediction disagreement in {path}")
        online[timing["protocol"]] = (timing, path)
    for dataset, directory in SOURCES.items():
        paths = sorted((args.root / directory / "exact_archive").glob("*_topk_cascade.json"))
        expected = 10 if dataset == "DTD" else 5 if dataset in {"FMD", "SoilOriginal"} else 4 if dataset == "KTHTIPS2b" else 2 if dataset == "CUReT" else 1
        if len(paths) != expected:
            raise ValueError(f"{dataset}: expected {expected} external conditions; found {len(paths)}")
        result_root = (REPO / "results/confirmatory" if dataset in {"DTD", "FMD", "CUReT"}
                       else REPO / "results/extensions" / directory)
        control_hash = digest(result_root / "ngram22_beitv2/topk_individual_control/nested_fold_results.csv")
        manifest_hash = digest(result_root / "sample_manifests" / f"{dataset}.csv")
        audit_hash = digest(result_root / "data_audit.csv")
        for path in paths:
            entry = json.loads(path.read_text(encoding="utf-8"))
            if entry["dataset"] != dataset or entry["classifier"] != "svm" or entry["seed"] != 42:
                raise ValueError(f"unexpected condition in {path}")
            if entry["expensive_subset_derived_locally"] or abs(float(entry["reproduction_delta"])) > 1e-10:
                raise ValueError(f"non-exact archived Top-k reproduction in {path}")
            previous = entry["provenance"]
            if (previous["topk_control_sha256"] != control_hash or
                    previous["manifest_sha256"] != manifest_hash or
                    previous["audit_sha256"] != audit_hash):
                raise ValueError(f"archived input provenance changed for {path}")
            costs = kth_costs if dataset == "KTHTIPS2b" else proxy_costs
            for budget_row in entry["budgets"]:
                row = evaluate_one(entry, budget_row, costs)
                if dataset == "KTHTIPS2b" and row["target_budget"] == 0.5:
                    if entry["protocol"] not in online:
                        raise ValueError(f"missing fair online timing for {entry['protocol']}")
                    timing, timing_path = online[entry["protocol"]]
                    row["online_selected_mean_ms"] = float(
                        timing["online_adaptive"]["mean_ms"] if row["selected_route"] == "cascade"
                        else timing["online_topk_always"]["mean_ms"]
                    )
                    row["online_topk_direct_mean_ms"] = float(timing["online_topk_always"]["mean_ms"])
                    provenance.append({"path": str(timing_path), "sha256": digest(timing_path)})
                else:
                    row["online_selected_mean_ms"] = None
                    row["online_topk_direct_mean_ms"] = None
                rows.append(row)
            provenance.append({"path": str(path), "sha256": digest(path)})
    keys = {(row["dataset"], row["outer_fold"], row["target_budget"]) for row in rows}
    if len(keys) != len(rows):
        raise ValueError("duplicate dataset/fold/budget rows")
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "cost_aware_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summaries = []
    for dataset in SOURCES:
        for budget in (0.25, 0.5, 0.75):
            block = [row for row in rows if row["dataset"] == dataset and row["target_budget"] == budget]
            summaries.append({
                "dataset": dataset,
                "target_budget": budget,
                "conditions": len(block),
                "direct_fallbacks": sum(row["selected_route"] == "topk_direct" for row in block),
                "mean_macro_f1": float(np.mean([row["macro_f1"] for row in block])),
                "mean_topk_macro_f1": float(np.mean([row["topk_macro_f1"] for row in block])),
                "mean_plain_cascade_macro_f1": float(np.mean([row["plain_cascade_macro_f1"] for row in block])),
                "mean_component_cost_ms": float(np.mean([row["component_cost_ms"] for row in block])),
                "mean_topk_component_cost_ms": float(np.mean([row["topk_direct_component_cost_ms"] for row in block])),
            })
    report = {
        "status": "EXPLORATORY_COMPONENT_COST_MODEL_NOT_ONLINE_LATENCY",
        "selection_rule": "cascade iff cheap_cost + target_training_budget * incremental_topk_cost < standalone_topk_cost",
        "selection_uses_outer_test_labels_or_observed_request_fraction": False,
        "kth_component_timing": {"path": str(args.kth_costs), "sha256": digest(args.kth_costs)},
        "other_dataset_component_timing_proxy": {"path": str(args.proxy_costs), "sha256": digest(args.proxy_costs)},
        "limitations": [
            "The cost-aware route is selected using a preset training budget, not test labels; the observed test request fraction evaluates cost only.",
            "Costs are sums of measured extraction components, not end-to-end routed latency; model loading and fitting are excluded.",
            "KTH timings use KTH images; all other datasets use an Outex-measured hardware proxy, not dataset-specific timing.",
            "ViT-B/16 uses the KTH measurement across datasets because the Outex extractor did not reproduce its archived embedding.",
            "The Outex timing source samples its official training partition; applying these timings to other image domains is still an exploratory hardware proxy.",
            "Means across overlapping outer partitions are descriptive; no independent-fold statistical test is implied.",
        ],
        "summaries": summaries,
        "source_artifacts": provenance,
    }
    (args.output / "cost_aware_summary.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    for row in summaries:
        if row["target_budget"] == 0.5:
            print(f"{row['dataset']:<22} n={row['conditions']:>2} "
                  f"fallback={row['direct_fallbacks']} F1={row['mean_macro_f1']:.4f} "
                  f"Top-k={row['mean_topk_macro_f1']:.4f} "
                  f"cost={row['mean_component_cost_ms']:.1f}/"
                  f"{row['mean_topk_component_cost_ms']:.1f} ms")


if __name__ == "__main__":
    main()
