#!/usr/bin/env python3
"""Top-k cost-aware cascade with a cheap stage selected on outer-training data.

PROTOCOL (fixed on 2026-10-10 before any outer-test evaluation of this variant):
- Top-k blocks: the archived, training-selected Top-k of each condition
  (``results/exploratory/topk_cascade/*/exact_archive``); not changed here.
- Cheap-stage candidates: resnet50, siglip_base, beitv2_base_final, convnext_v2_t.
  A candidate is used only if a measured cost exists in the cost profile of
  that dataset (KTH: KTH timing; others: Outex training-image timing proxy).
- Routes: Top-k direct, or cascade(cheap, q) with q in {0.25, 0.5, 0.75}.
  The threshold is the q-quantile of grouped OOF cheap-stage margins.
- Selection (outer-training OOF only): among routes whose OOF macro-F1 is at
  least OOF Top-k macro-F1 - 0.005, choose the lowest projected component
  cost; ties prefer Top-k direct, then resnet50. The 0.005 tolerance is the
  one already used by ``run_train_selected_topk_cascade.py`` (itself fixed
  after earlier exploratory analysis; not independent confirmation).
- Comparator: the same rule restricted to the resnet50 cheap stage
  (the current thesis cascade), recomputed here with identical code.
- Outer test is opened only after both selection objects exist, and only for
  the selected route, the resnet50-only route and Top-k direct.
- Costs are cached-embedding component proxies, NOT online latency.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
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
from report_cost_aware_topk import CASCADE, DEFAULT_KTH_COST, DEFAULT_PROXY_COST, SOURCES, component_costs  # noqa: E402
from run_train_selected_topk_cascade import outer_split, result_root  # noqa: E402

CHEAP_CANDIDATES = ("resnet50", "siglip_base", "beitv2_base_final", "convnext_v2_t")
BUDGETS = (0.25, 0.5, 0.75)
F1_TOLERANCE = 0.005
EXPECTED = {"DTD": 10, "FMD": 5, "CUReT": 2, "Outex13Official1360": 1, "SoilOriginal": 5, "KTHTIPS2b": 4}


def macro_f1(y_true: np.ndarray, pred: np.ndarray, labels: np.ndarray) -> float:
    return float(f1_score(y_true, pred, labels=labels, average="macro", zero_division=0))


def stack(cache: dict, blocks: list[str]) -> np.ndarray:
    return np.concatenate([cache[b] for b in blocks], axis=1)


def oof_for_blocks(cache: dict, blocks: list[str], train: np.ndarray, y: np.ndarray,
                   groups: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Grouped OOF predictions and margins over outer-training rows (same splitter as archive)."""
    n_splits = min(4, len(np.unique(groups[train])))
    if n_splits < 2:
        raise ValueError("inner grouping leaves fewer than two folds")
    x = stack(cache, blocks)
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed + 1)
    pred = np.full(len(train), -1, dtype=int)
    marg = np.full(len(train), np.nan)
    for rel_fit, rel_val in splitter.split(x[train], y[train], groups[train]):
        model = make_model("svm", seed)
        model.fit(x[train[rel_fit]], y[train[rel_fit]])
        pred[rel_val] = model.predict(x[train[rel_val]])
        marg[rel_val] = margin(model, x[train[rel_val]])
    if (pred < 0).any() or not np.isfinite(marg).all():
        raise ValueError("incomplete OOF coverage")
    return pred, marg


def route_costs(cheap: str, topk: list[str], costs: dict[str, float]) -> tuple[float, float, float]:
    base = costs[cheap]
    incremental = sum(costs[b] for b in set(topk) - {cheap})
    direct = sum(costs[b] for b in set(topk))
    return base, incremental, direct


def select(candidates_oof: dict, topk_pred: np.ndarray, y_tr: np.ndarray, labels: np.ndarray,
           topk: list[str], costs: dict[str, float], allowed: list[str]) -> dict:
    ref = macro_f1(y_tr, topk_pred, labels)
    direct = sum(costs[b] for b in set(topk))
    rows = [{"route": "topk_direct", "cheap": None, "budget": None, "threshold": None,
             "oof_macro_f1": ref, "oof_request_fraction": 1.0,
             "projected_component_ms": direct, "eligible": True}]
    for cheap in allowed:
        c_pred, c_marg = candidates_oof[cheap]
        base, inc, _ = route_costs(cheap, topk, costs)
        for q in BUDGETS:
            thr = float(np.quantile(c_marg, q))
            req = c_marg <= thr
            f1 = macro_f1(y_tr, np.where(req, topk_pred, c_pred), labels)
            rows.append({"route": "cascade", "cheap": cheap, "budget": q, "threshold": thr,
                         "oof_macro_f1": f1, "oof_cheap_macro_f1": macro_f1(y_tr, c_pred, labels),
                         "oof_request_fraction": float(req.mean()),
                         "projected_component_ms": base + float(req.mean()) * inc,
                         "eligible": f1 >= ref - F1_TOLERANCE - 1e-12})
    eligible = [r for r in rows if r["eligible"]]
    chosen = min(eligible, key=lambda r: (r["projected_component_ms"], r["route"] != "topk_direct",
                                          r["cheap"] != "resnet50"))
    return {"selected": chosen, "candidates": rows, "oof_topk_macro_f1": ref, "allowed_cheap": allowed}


def evaluate(selection: dict, cache: dict, train: np.ndarray, test: np.ndarray, y: np.ndarray,
             labels: np.ndarray, topk_test_pred: np.ndarray, topk: list[str],
             costs: dict[str, float]) -> dict:
    chosen = selection["selected"]
    if chosen["route"] == "topk_direct":
        return {"macro_f1": macro_f1(y[test], topk_test_pred, labels), "request_fraction": 1.0,
                "component_ms": sum(costs[b] for b in set(topk)), "route": "topk_direct", "cheap": None}
    cheap = chosen["cheap"]
    model = make_model("svm", 42)
    x = stack(cache, [cheap])
    model.fit(x[train], y[train])
    c_pred = model.predict(x[test])
    req = margin(model, x[test]) <= chosen["threshold"]
    base, inc, _ = route_costs(cheap, topk, costs)
    return {"macro_f1": macro_f1(y[test], np.where(req, topk_test_pred, c_pred), labels),
            "request_fraction": float(req.mean()), "component_ms": base + float(req.mean()) * inc,
            "route": "cascade", "cheap": cheap, "budget": chosen["budget"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=CASCADE / "cheap_stage_selected_primary22")
    parser.add_argument("--dataset", choices=tuple(SOURCES))
    parser.add_argument("--limit", type=int, default=None, help="max conditions per dataset (timing pilot)")
    args = parser.parse_args()

    kth_costs = component_costs(DEFAULT_KTH_COST)
    proxy_costs = component_costs(DEFAULT_PROXY_COST)
    if "vit_b16" not in proxy_costs and "vit_b16" in kth_costs:
        proxy_costs["vit_b16"] = kth_costs["vit_b16"]
    args.output.mkdir(parents=True, exist_ok=True)
    datasets = {args.dataset: SOURCES[args.dataset]} if args.dataset else SOURCES
    out_rows = []

    for dataset, directory in datasets.items():
        root = result_root(dataset, directory)
        audit_gate(root, dataset)
        embedding_root = (REPO / "embeddings_extensions" if dataset in {"Outex13Official1360", "SoilOriginal", "KTHTIPS2b"}
                          else REPO / "embeddings" if dataset == "DTD" else REPO / "embeddings_confirmatory")
        cache, y = load_dataset(REPO, dataset, embedding_root=embedding_root)
        groups, rows = load_manifest(root, dataset, y)
        labels = np.unique(y)
        costs = kth_costs if dataset == "KTHTIPS2b" else proxy_costs
        paths = sorted((CASCADE / directory / "exact_archive").glob("*_topk_cascade.json"))
        if len(paths) != EXPECTED[dataset]:
            raise ValueError(f"{dataset}: expected {EXPECTED[dataset]} archives, found {len(paths)}")
        for path in paths[: args.limit]:
            t0 = time.perf_counter()
            entry = json.loads(path.read_text(encoding="utf-8"))
            topk = entry["expensive_blocks"]
            missing = set(topk) - costs.keys()
            if missing:
                raise ValueError(f"{path}: Top-k blocks without measured cost {sorted(missing)}")
            train, test = outer_split(entry, y, groups, rows)
            if set(groups[train]) & set(groups[test]):
                raise AssertionError("outer group leakage")
            inner_groups = groups if entry["inner_group_column"] == "group" else manifest_groups(rows, entry["inner_group_column"])
            allowed = [c for c in CHEAP_CANDIDATES if c in costs and c in cache]
            y_tr = y[train]

            # --- Training-only phase ---
            topk_oof, _ = oof_for_blocks(cache, topk, train, y, inner_groups, 42)
            cand_oof = {c: oof_for_blocks(cache, [c], train, y, inner_groups, 42) for c in allowed}
            sel_new = select(cand_oof, topk_oof, y_tr, labels, topk, costs, allowed)
            sel_resnet = select(cand_oof, topk_oof, y_tr, labels, topk, costs, ["resnet50"])
            (args.output / f"{dataset}_{entry['protocol']}_selection_pretest.json").write_text(
                json.dumps({"selected_cheap_stage": sel_new, "resnet50_only": sel_resnet}, indent=2) + "\n",
                encoding="utf-8")

            # --- Outer test opened only now ---
            xk = stack(cache, topk)
            topk_model = make_model("svm", 42)
            topk_model.fit(xk[train], y[train])
            topk_test = topk_model.predict(xk[test])
            topk_f1 = macro_f1(y[test], topk_test, labels)
            ev_new = evaluate(sel_new, cache, train, test, y, labels, topk_test, topk, costs)
            ev_res = evaluate(sel_resnet, cache, train, test, y, labels, topk_test, topk, costs)
            direct_ms = sum(costs[b] for b in set(topk))
            record = {"dataset": dataset, "protocol": entry["protocol"], "topk_blocks": topk,
                      "allowed_cheap": allowed, "topk_direct": {"macro_f1": topk_f1, "component_ms": direct_ms},
                      "topk_reproduction_delta_vs_archive": topk_f1 - float(entry["topk_always"]["macro_f1"]),
                      "selected_cheap_stage": ev_new, "resnet50_only": ev_res,
                      "seconds": time.perf_counter() - t0,
                      "source_archive": {"path": str(path), "sha256": sha(path)},
                      "cost_profile": str(DEFAULT_KTH_COST if dataset == "KTHTIPS2b" else DEFAULT_PROXY_COST)}
            (args.output / f"{dataset}_{entry['protocol']}_result.json").write_text(
                json.dumps(record, indent=2) + "\n", encoding="utf-8")
            out_rows.append({"dataset": dataset, "protocol": entry["protocol"],
                             "new_route": ev_new["route"], "new_cheap": ev_new["cheap"],
                             "new_budget": ev_new.get("budget"), "new_f1": ev_new["macro_f1"],
                             "new_ms": ev_new["component_ms"], "resnet_route": ev_res["route"],
                             "resnet_budget": ev_res.get("budget"), "resnet_f1": ev_res["macro_f1"],
                             "resnet_ms": ev_res["component_ms"], "topk_f1": topk_f1, "topk_ms": direct_ms,
                             "topk_repro_delta": record["topk_reproduction_delta_vs_archive"],
                             "seconds": record["seconds"]})
            print(f"{dataset} {entry['protocol']}: new={ev_new['route']}/{ev_new['cheap']}/q={ev_new.get('budget')} "
                  f"F1={ev_new['macro_f1']:.4f} {ev_new['component_ms']:.1f}ms | resnet={ev_res['route']} "
                  f"F1={ev_res['macro_f1']:.4f} {ev_res['component_ms']:.1f}ms | topk F1={topk_f1:.4f} "
                  f"{direct_ms:.1f}ms | {record['seconds']:.0f}s", flush=True)

    suffix = f"_{args.dataset}" if args.dataset else ""
    with (args.output / f"rows{suffix}.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)


if __name__ == "__main__":
    main()
