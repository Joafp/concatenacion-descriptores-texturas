#!/usr/bin/env python3
"""Two-stage adaptive acquisition whose escalation target is the Top-k library.

The earlier pilot (``run_adaptive_cost_budget_comparison.py``) escalated from
``resnet50`` to a fixed two-block route, so its accuracy ceiling was that route
rather than the manuscript's own composition.  Here the expensive stage is the
archived ``topk_individual`` subset for the same condition, which makes the
ceiling equal to the published Top-k result and turns the question into how much
of the Top-k route's cost can be avoided at equal accuracy.

Only training-side information sets the escalation threshold: the quantiles come
from grouped out-of-fold margins computed on the outer training rows.  A random
control requests the extra stage for the same number of images, so the reported
effect is attributable to the margin rule rather than to the extra budget.

Accuracy here is a simulation over cached embeddings; it is not a latency
measurement.  Route costs enter only through ``--cheap-cost-ms`` and
``--expensive-cost-ms``, which the caller must obtain from a timing run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from run_confirmatory_nested import (  # noqa: E402
    audit_gate, fit_score_foldaware, inner_score, load_dataset, load_manifest,
    make_model, manifest_groups,
)
from run_topk_individual_control import outer_indices  # noqa: E402
from run_adaptive_descriptor_pilot import margin, metrics  # noqa: E402

BUDGETS = (0.25, 0.5, 0.75)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def archived_topk(control: Path, dataset: str, classifier: str, seed: int,
                  fold: int) -> tuple[list[str], float]:
    """Read the subset and external macro-F1 that Top-k already reported."""
    rows = pd.read_csv(control / "nested_fold_results.csv")
    match = rows[rows["dataset"].eq(dataset) & rows["classifier"].eq(classifier)
                 & rows["seed"].eq(seed) & rows["outer_fold"].eq(fold)
                 & rows["method"].eq("topk_individual") & rows["run_mode"].eq("full")]
    if len(match) != 1:
        raise ValueError(f"expected one archived Top-k row, found {len(match)}")
    row = match.iloc[0]
    return str(row["selected"]).split("+"), float(row["macro_f1"])


def derive_topk(cache: dict, train: np.ndarray, y: np.ndarray, groups: np.ndarray,
                classifier: str, seed: int, k: int) -> list[str]:
    """Re-rank the locally available singletons when the archived subset cannot
    be reproduced because a block is absent.  Same rule as the archived control.
    """
    ranked = sorted((inner_score(cache, [name], train, y, groups, classifier, seed), name)
                    for name in sorted(cache))
    return [name for _, name in ranked[-k:]][::-1]


def oof_margins(cache: dict, cheap: list[str], train: np.ndarray, y: np.ndarray,
                groups: np.ndarray, classifier: str, seed: int,
                n_splits: int = 4) -> tuple[np.ndarray, list[int]]:
    """Grouped out-of-fold margins over the outer training rows only."""
    n_splits = min(n_splits, len(np.unique(groups[train])))
    if n_splits < 2:
        raise ValueError("inner grouping leaves fewer than two folds")
    x = np.concatenate([cache[b] for b in cheap], axis=1)
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed + 1)
    out = np.full(len(train), np.nan)
    classes = []
    for rel_train, rel_val in splitter.split(x[train], y[train], groups[train]):
        model = make_model(classifier, seed)
        model.fit(x[train[rel_train]], y[train[rel_train]])
        out[rel_val] = margin(model, x[train[rel_val]])
        classes.append(int(len(np.unique(y[train[rel_train]]))))
    if not np.isfinite(out).all():
        raise ValueError("incomplete out-of-fold margin coverage")
    return out, classes


def run(args: argparse.Namespace) -> dict:
    started = time.perf_counter()
    audit_root, manifest_root, output = (p.resolve() for p in
                                         (args.audit_root, args.manifest_root, args.output))
    embedding_root = args.embedding_root.resolve() if args.embedding_root else None
    audit_gate(audit_root, args.dataset)
    cache, y = load_dataset(REPO, args.dataset, embedding_root=embedding_root)
    unknown = sorted(set(args.exclude_extractors).difference(cache))
    if unknown:
        raise ValueError(f"cannot exclude missing extractors: {unknown}")
    for name in args.exclude_extractors:
        cache.pop(name)
    groups, rows = load_manifest(manifest_root, args.dataset, y)
    train, test = outer_indices(args.dataset, args.seed, args.fold, y, groups, rows,
                                args.official_split, args.curet_direction,
                                args.invert_official_split)
    if set(groups[train]).intersection(groups[test]):
        raise AssertionError("outer group leakage")
    # The threshold is a quantile of training margins, so the inner folds must
    # pose the same task as the external test.  When the external protocol holds
    # out a whole physical sample, splitting images at random inside training
    # makes the inner task easier, the margins larger and the threshold too
    # permissive -- the same defect diagnosed for the selection criterion.
    inner_groups = (groups if args.inner_group_column is None
                    else manifest_groups(rows, args.inner_group_column))

    fold = (args.official_split - 1 if args.official_split is not None
            else {"a_to_b": 0, "b_to_a": 1}[args.curet_direction]
            if args.curet_direction is not None else args.fold)
    subset, archived_f1 = archived_topk(args.topk_control.resolve(), args.dataset,
                                        args.classifier, args.seed, fold)
    missing = [b for b in subset if b not in cache]
    derived = False
    if missing:
        if not args.derive_topk:
            raise ValueError(
                f"archived Top-k subset needs absent blocks {missing}; rerun with "
                "--derive-topk to re-rank the available library instead, which "
                "reports a different composition than the manuscript")
        subset = derive_topk(cache, train, y, groups, args.classifier, args.seed, len(subset))
        derived = True

    cheap = args.cheap_blocks
    absent_cheap = [b for b in cheap if b not in cache]
    if absent_cheap:
        raise ValueError(f"cheap stage needs absent blocks {absent_cheap}")

    x_cheap = np.concatenate([cache[b] for b in cheap], axis=1)
    cheap_model = make_model(args.classifier, args.seed)
    cheap_model.fit(x_cheap[train], y[train])
    pred_cheap = np.asarray(cheap_model.predict(x_cheap[test]))
    test_margin = margin(cheap_model, x_cheap[test])

    # The expensive stage is the Top-k route itself, fold-aware like the control.
    exp_f1, exp_acc, exp_seconds = fit_score_foldaware(
        cache, subset, train, test, y, args.classifier, args.seed)
    x_exp = np.concatenate([cache[b] for b in subset], axis=1)
    exp_model = make_model(args.classifier, args.seed)
    exp_model.fit(x_exp[train], y[train])
    pred_exp = np.asarray(exp_model.predict(x_exp[test]))

    oof, inner_classes = oof_margins(cache, cheap, train, y, inner_groups,
                                     args.classifier, args.seed)
    labels = np.unique(y)
    cheap_metrics = metrics(y[test], pred_cheap, labels)
    exp_metrics = metrics(y[test], pred_exp, labels)

    result = {
        "dataset": args.dataset, "classifier": args.classifier, "seed": args.seed,
        "protocol": ((f"official{args.official_split}"
                      + ("_inverted" if args.invert_official_split else ""))
                     if args.official_split is not None
                     else f"curet_half_indices:{args.curet_direction}"
                     if args.curet_direction else f"stratified_group_kfold5_fold{args.fold}"),
        "inner_group_column": args.inner_group_column or "group",
        "excluded_extractors": args.exclude_extractors,
        "outer_fold": fold, "n_train": int(len(train)), "n_test": int(len(test)),
        "n_classes": int(len(labels)), "inner_folds": len(inner_classes),
        "inner_train_classes": inner_classes, "groups_intersection": 0,
        "threshold_source": ("quantiles of grouped out-of-fold margins over the "
                             "outer training rows only"),
        "cheap_blocks": cheap,
        "cheap_dimensions": int(x_cheap.shape[1]),
        "expensive_blocks": subset,
        "expensive_dimensions": int(x_exp.shape[1]),
        "expensive_subset_derived_locally": derived,
        "archived_topk_macro_f1": archived_f1,
        "reproduced_topk_macro_f1": exp_f1,
        "reproduction_delta": exp_f1 - archived_f1,
        "cheap_only": cheap_metrics,
        "topk_always": exp_metrics,
        "topk_always_fit_seconds": exp_seconds,
        "budgets": [],
        "latency": "NOT_MEASURED: cached embeddings; cost enters only via --*-cost-ms",
    }

    samples = []
    rng = np.random.default_rng(args.seed + 1000 * fold)
    for quantile in BUDGETS:
        threshold = float(np.quantile(oof, quantile))
        request = test_margin <= threshold
        pred = np.where(request, pred_exp, pred_cheap)
        n_request = int(request.sum())
        draws = []
        for _ in range(args.repeats):
            mask = np.zeros(len(test), dtype=bool)
            mask[rng.choice(len(test), n_request, replace=False)] = True
            draws.append(metrics(y[test], np.where(mask, pred_exp, pred_cheap), labels))
        fraction = float(request.mean())
        adaptive = metrics(y[test], pred, labels)
        row = {
            "target_budget": quantile, "threshold": threshold,
            "observed_request_fraction": fraction,
            "n_requested": n_request,
            "adaptive": adaptive,
            "random_same_count_mean_macro_f1": float(np.mean([d["macro_f1"] for d in draws])),
            "random_same_count_sd_macro_f1": float(np.std([d["macro_f1"] for d in draws], ddof=1)),
            "random_repeats": args.repeats,
            "gap_to_topk_always": adaptive["macro_f1"] - exp_metrics["macro_f1"],
        }
        if args.cheap_cost_ms is not None and args.expensive_cost_ms is not None:
            mean_cost = (1 - fraction) * args.cheap_cost_ms + fraction * args.expensive_cost_ms
            row["cost_model"] = {
                "cheap_route_ms": args.cheap_cost_ms,
                "expensive_route_ms": args.expensive_cost_ms,
                "mean_cost_ms": mean_cost,
                "fraction_of_topk_always_cost": mean_cost / args.expensive_cost_ms,
                "note": ("upper bound: assumes the cheap stage is discarded on "
                         "escalation, so shared blocks are charged twice"),
            }
        result["budgets"].append(row)
        for position, index in enumerate(test):
            samples.append({
                "budget": quantile, "row_id": int(index), "label": int(y[index]),
                "cheap_pred": int(pred_cheap[position]), "topk_pred": int(pred_exp[position]),
                "adaptive_pred": int(pred[position]), "margin": float(test_margin[position]),
                "request_extra": int(request[position]),
            })

    dataset_dir = {"KTHTIPS2b": "KTH-TIPS2-b"}.get(args.dataset, args.dataset)
    emb = (embedding_root or REPO / "embeddings") / dataset_dir
    used = sorted(set(cheap) | set(subset))
    result["provenance"] = {
        "audit_sha256": sha(audit_root / "data_audit.csv"),
        "manifest_sha256": sha(manifest_root / "sample_manifests" / f"{args.dataset}.csv"),
        "topk_control_sha256": sha(args.topk_control.resolve() / "nested_fold_results.csv"),
        "runner_sha256": sha(Path(__file__)),
        "blocks_sha256": {name: sha(emb / f"{name}.npy") for name in used},
        "labels_sha256": sha(emb / f"{used[0]}_labels.npy"),
    }
    result["duration_seconds"] = time.perf_counter() - started

    output.mkdir(parents=True, exist_ok=True)
    tag = (f"official{args.official_split}"
           + ("_inverted" if args.invert_official_split else "")
           if args.official_split is not None
           else args.curet_direction or f"f{args.fold}")
    if args.inner_group_column:
        tag += f"_innergrp-{args.inner_group_column}"
    stem = f"{args.dataset}_{args.classifier}_s{args.seed}_{tag}_topk_cascade"
    (output / f"{stem}.json").write_text(json.dumps(result, indent=2) + "\n",
                                         encoding="utf-8")
    with (output / f"{stem}_per_sample.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(samples[0]))
        writer.writeheader()
        writer.writerows(samples)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--classifier", choices=("svm", "resmlp"), default="svm")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fold", type=int, default=0, choices=range(5))
    split = parser.add_mutually_exclusive_group()
    split.add_argument("--official-split", type=int, choices=range(1, 11))
    split.add_argument("--curet-direction", choices=("a_to_b", "b_to_a"))
    parser.add_argument("--cheap-blocks", nargs="+", default=["resnet50"])
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--topk-control", type=Path, required=True,
                        help="directory holding the archived topk_individual results")
    parser.add_argument("--embedding-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--invert-official-split", action="store_true",
                        help="swap the official train/test roles, as the archived "
                             "KTH-TIPS2-b runs do to train on three samples")
    parser.add_argument("--inner-group-column",
                        help="manifest column grouping the inner folds that derive "
                             "the threshold; defaults to the manifest 'group'")
    parser.add_argument("--exclude-extractors", nargs="*", default=[])
    parser.add_argument("--repeats", type=int, default=100)
    parser.add_argument("--derive-topk", action="store_true",
                        help="re-rank the available library when the archived "
                             "subset needs a block that is absent locally")
    parser.add_argument("--cheap-cost-ms", type=float)
    parser.add_argument("--expensive-cost-ms", type=float)
    args = parser.parse_args()
    if args.dataset == "CUReT" and not args.curet_direction:
        parser.error("CUReT requires --curet-direction")
    result = run(args)

    print(f"\n{args.dataset} {args.classifier} {result['protocol']}")
    print(f"  etapa barata  : {'+'.join(result['cheap_blocks'])} "
          f"({result['cheap_dimensions']}d)  macro-F1 {result['cheap_only']['macro_f1']:.4f}")
    print(f"  etapa Top-k   : {'+'.join(result['expensive_blocks'])} "
          f"({result['expensive_dimensions']}d)  macro-F1 {result['topk_always']['macro_f1']:.4f}")
    flag = "  [derivado localmente]" if result["expensive_subset_derived_locally"] else ""
    print(f"  Top-k archivado {result['archived_topk_macro_f1']:.4f}  "
          f"delta {result['reproduction_delta']:+.4f}{flag}")
    print(f"\n  {'objetivo':>9}{'pedido':>9}{'adaptativa':>12}{'aleatoria':>11}"
          f"{'vs Top-k':>10}{'costo medio':>15}")
    for row in result["budgets"]:
        cost = (f"{row['cost_model']['mean_cost_ms']:.1f} ms "
                f"({100 * row['cost_model']['fraction_of_topk_always_cost']:.0f}%)"
                if "cost_model" in row else "-")
        print(f"  {row['target_budget']:>9.2f}{row['observed_request_fraction']:>9.1%}"
              f"{row['adaptive']['macro_f1']:>12.4f}"
              f"{row['random_same_count_mean_macro_f1']:>11.4f}"
              f"{row['gap_to_topk_always']:>+10.4f}{cost:>15}")


if __name__ == "__main__":
    main()
