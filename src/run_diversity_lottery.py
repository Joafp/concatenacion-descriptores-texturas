#!/usr/bin/env python3
"""Sampling that favours blocks unlike the ones already chosen.

Top-k ranks blocks by their individual inner score and takes the best k, a rule
blind to overlap: on Outex the mean CKA inside the Top-k is 0.890 against 0.638
for random subsets of the same size, with three DINOv2 variants occupying three
of eight slots.  Budget spent on near-copies buys little.

Here a block's utility is its relevance discounted by how much it repeats what
is already selected,

    u_i = relevance_i - lambda * mean_{j in chosen} CKA(i, j)

recomputed at every step, so diversity is measured against the growing subset
rather than globally.  Candidates are then ranked by utility and sampled with
the weight ``(n - rank + 1) ** beta`` of the companion rank lottery, which makes
``lambda = 0`` reproduce that method exactly and ``beta -> inf`` the greedy
deterministic rule in the spirit of mRMR (Peng, Long & Ding, 2005, IEEE TPAMI
27(8), 1226-1238).

Relevance, CKA and every draw use the outer training rows only.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.metrics import accuracy_score, f1_score

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from run_confirmatory_nested import (  # noqa: E402
    audit_gate, fit_score_foldaware, inner_score, load_dataset, load_manifest,
    make_model, manifest_groups,
)
from run_topk_individual_control import archived_k, outer_indices  # noqa: E402
from analyze_block_redundancy import linear_cka  # noqa: E402

REPO = SRC.parent


def metrics(y_true, y_pred, labels) -> dict:
    return {"macro_f1": float(f1_score(y_true, y_pred, labels=labels,
                                       average="macro", zero_division=0)),
            "accuracy": float(accuracy_score(y_true, y_pred))}


def decision_scores(model, x) -> np.ndarray:
    scores = np.asarray(model.decision_function(x))
    if scores.ndim == 1:
        scores = np.column_stack([-scores, scores])
    sd = scores.std()
    return scores / sd if sd > 0 else scores


def utilities(names, relevance, cka, chosen, lam):
    """Relevance discounted by mean similarity to what is already chosen."""
    if not chosen:
        return {n: relevance[n] for n in names}
    return {n: relevance[n] - lam * float(np.mean([cka[(n, c)] for c in chosen]))
            for n in names}


def draw_subset(names, relevance, cka, lam, beta, k, rng):
    """Sample k blocks, re-ranking by utility after each pick."""
    remaining, chosen = list(names), []
    while len(chosen) < k:
        util = utilities(remaining, relevance, cka, chosen, lam)
        order = sorted(remaining, key=lambda n: (-util[n], n))
        n = len(order)
        w = (np.arange(n, 0, -1, dtype=float)) ** beta
        pick = order[int(rng.choice(n, p=w / w.sum()))]
        chosen.append(pick)
        remaining.remove(pick)
    return sorted(chosen)


def greedy_subset(names, relevance, cka, lam, k):
    """The deterministic limit: always take the highest utility."""
    remaining, chosen = list(names), []
    while len(chosen) < k:
        util = utilities(remaining, relevance, cka, chosen, lam)
        pick = min(remaining, key=lambda n: (-util[n], n))
        chosen.append(pick)
        remaining.remove(pick)
    return sorted(chosen)


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
    parser.add_argument("--invert-official-split", action="store_true")
    parser.add_argument("--inner-group-column")
    parser.add_argument("--exclude-extractors", nargs="*", default=[])
    parser.add_argument("--draws", type=int, default=15)
    parser.add_argument("--lambdas", type=float, nargs="+", default=[0.0, 0.5, 1.0])
    parser.add_argument("--betas", type=float, nargs="+", default=[2.0, 8.0])
    parser.add_argument("--n-jobs", type=int, default=10)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--results-root", type=Path)
    parser.add_argument("--ngram-result-subdir", default="ngram22_beitv2")
    parser.add_argument("--embedding-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.dataset == "CUReT" and not args.curet_direction:
        parser.error("CUReT requires --curet-direction")

    started = time.perf_counter()
    audit_root, manifest_root, output = (p.resolve() for p in
                                         (args.audit_root, args.manifest_root, args.output))
    embedding_root = args.embedding_root.resolve() if args.embedding_root else None
    audit_gate(audit_root, args.dataset)
    cache, y = load_dataset(REPO, args.dataset, embedding_root=embedding_root)
    for name in args.exclude_extractors:
        cache.pop(name, None)
    groups, rows = load_manifest(manifest_root, args.dataset, y)
    train, test = outer_indices(args.dataset, args.seed, args.fold, y, groups, rows,
                                args.official_split, args.curet_direction,
                                args.invert_official_split)
    if set(groups[train]).intersection(groups[test]):
        raise AssertionError("outer group leakage")
    inner_groups = (groups if args.inner_group_column is None
                    else manifest_groups(rows, args.inner_group_column))
    fold = (args.official_split - 1 if args.official_split is not None
            else {"a_to_b": 0, "b_to_a": 1}[args.curet_direction]
            if args.curet_direction is not None else args.fold)
    k = archived_k((args.results_root or args.audit_root).resolve(), args.dataset,
                   args.classifier, args.seed, fold, include_rgb_ngram=True,
                   ngram_result_subdir=args.ngram_result_subdir)

    names = sorted(cache)
    jobs = args.n_jobs if args.classifier == "svm" else 1
    scores = Parallel(n_jobs=jobs, prefer="threads")(
        delayed(inner_score)(cache, [n], train, y, inner_groups,
                             args.classifier, args.seed) for n in names)
    singles = dict(zip(names, scores))
    # Relevance on [0, 1] so lambda trades against CKA on a comparable scale.
    lo, hi = min(singles.values()), max(singles.values())
    span = (hi - lo) or 1.0
    relevance = {n: (v - lo) / span for n, v in singles.items()}

    mats = {n: cache[n][train].astype(np.float64) for n in names}
    pairs = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]]
    vals = Parallel(n_jobs=jobs, prefer="threads")(
        delayed(linear_cka)(mats[a], mats[b]) for a, b in pairs)
    cka = {(a, b): v for (a, b), v in zip(pairs, vals)}
    cka.update({(b, a): v for (a, b), v in zip(pairs, vals)})
    del mats

    order = [n for n, _ in sorted(singles.items(), key=lambda kv: (-kv[1], kv[0]))]
    topk = order[:k]
    topk_f1, topk_acc, _ = fit_score_foldaware(cache, topk, train, test, y,
                                               args.classifier, args.seed)
    labels, y_test = np.unique(y), y[test]

    def external(subset):
        x = np.concatenate([cache[b] for b in subset], axis=1)
        model = make_model(args.classifier, args.seed)
        model.fit(x[train], y[train])
        pred = np.asarray(model.predict(x[test]))
        return pred, decision_scores(model, x[test]), metrics(y_test, pred, labels)

    def mean_cka(subset):
        v = [cka[(a, b)] for i, a in enumerate(subset) for b in subset[i + 1:]]
        return float(np.mean(v)) if v else float("nan")

    report = {"dataset": args.dataset, "classifier": args.classifier,
              "seed": args.seed, "outer_fold": fold, "k": k, "draws": args.draws,
              "n_candidates": len(names),
              "inner_group_column": args.inner_group_column or "group",
              "topk": {"subset": topk, "macro_f1": topk_f1, "accuracy": topk_acc,
                       "mean_cka": mean_cka(topk)},
              "cells": []}

    print(f"{args.dataset} {args.classifier} fold {fold}   k={k}")
    print(f"  Top-k: macro-F1 {topk_f1:.4f}  (CKA interno {mean_cka(topk):.3f})")
    print(f"\n  {'lambda':>7}{'beta':>6}{'greedy':>9}{'sorteo':>9}{'ens.suave':>11}"
          f"{'ens.voto':>10}{'CKA medio':>11}{'bloques':>9}")

    flat = []
    for lam in args.lambdas:
        greedy = greedy_subset(names, relevance, cka, lam, k)
        g_pred, _, g_met = external(greedy)
        for beta in args.betas:
            rng = np.random.default_rng(args.seed * 1000 + fold * 10
                                        + int(lam * 7) + int(beta))
            subsets = [draw_subset(names, relevance, cka, lam, beta, k, rng)
                       for _ in range(args.draws)]
            evald = Parallel(n_jobs=jobs, prefer="threads")(
                delayed(external)(s) for s in subsets)
            f1s = np.array([m["macro_f1"] for _, _, m in evald])
            soft = np.mean([s for _, s, _ in evald], axis=0)
            soft_pred = labels[np.argmax(soft, axis=1)]
            votes = np.stack([p for p, _, _ in evald])
            hard_pred = labels[[np.bincount(np.searchsorted(labels, votes[:, i]),
                                            minlength=len(labels)).argmax()
                                for i in range(votes.shape[1])]]
            ens_soft = metrics(y_test, soft_pred, labels)
            ens_hard = metrics(y_test, hard_pred, labels)
            union = sorted({b for s in subsets for b in s})
            cell = {"lambda": lam, "beta": beta,
                    "greedy": {"subset": greedy, **g_met, "mean_cka": mean_cka(greedy)},
                    "single": {"mean_macro_f1": float(f1s.mean()),
                               "sd": float(f1s.std(ddof=1))},
                    "ensemble_soft": ens_soft, "ensemble_hard": ens_hard,
                    "mean_cka_drawn": float(np.mean([mean_cka(s) for s in subsets])),
                    "union_blocks": len(union), "union": union,
                    "subsets": subsets}
            report["cells"].append(cell)
            print(f"  {lam:>7.1f}{beta:>6.1f}{g_met['macro_f1']:>9.4f}"
                  f"{f1s.mean():>9.4f}{ens_soft['macro_f1']:>11.4f}"
                  f"{ens_hard['macro_f1']:>10.4f}{cell['mean_cka_drawn']:>11.3f}"
                  f"{len(union):>9}")
            base = {"dataset": args.dataset, "classifier": args.classifier,
                    "seed": args.seed, "outer_fold": fold, "k": k,
                    "lambda": lam, "beta": beta}
            for v, val in (("greedy", g_met), ("single_mean",
                           {"macro_f1": f1s.mean(), "accuracy": np.nan}),
                           ("ensemble_soft", ens_soft), ("ensemble_hard", ens_hard)):
                flat.append({**base, "variant": v, "macro_f1": val["macro_f1"],
                             "accuracy": val.get("accuracy", np.nan),
                             "union_blocks": len(union),
                             "mean_cka": cell["mean_cka_drawn"]})
    flat.append({"dataset": args.dataset, "classifier": args.classifier,
                 "seed": args.seed, "outer_fold": fold, "k": k, "lambda": "",
                 "beta": "", "variant": "topk_deterministic", "macro_f1": topk_f1,
                 "accuracy": topk_acc, "union_blocks": k,
                 "mean_cka": report["topk"]["mean_cka"]})

    report["duration_seconds"] = time.perf_counter() - started
    output.mkdir(parents=True, exist_ok=True)
    tag = (f"official{args.official_split}"
           + ("_inverted" if args.invert_official_split else "")
           if args.official_split is not None
           else args.curet_direction or f"f{args.fold}")
    stem = f"{args.dataset}_{args.classifier}_s{args.seed}_{tag}_diversity"
    (output / f"{stem}.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    path = output / "diversity_rows.csv"
    pd.DataFrame(flat).to_csv(path, mode="a", header=not path.exists(), index=False)
    print(f"\n  escrito en {output}  ({report['duration_seconds']:.0f}s)")


if __name__ == "__main__":
    main()
