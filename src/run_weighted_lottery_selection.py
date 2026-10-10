#!/usr/bin/env python3
"""Rank-weighted sampling of descriptor blocks, between random and Top-k.

Top-k concatenates the k best-ranked blocks deterministically; the archived
random control draws k blocks with uniform probability.  Both are endpoints of
one family: give block of rank r the weight

    w_r = (n - r + 1) ** beta

and sample k blocks without replacement.  ``beta = 0`` makes every block equally
likely, which is the uniform control; as ``beta`` grows the mass concentrates on
the best-ranked blocks until the draw is Top-k with probability one.  The
intermediate values are the heuristic this script evaluates.

A single weighted draw is worse than Top-k in expectation -- it sometimes takes
a lower-ranked block over a better one -- so the draws are read three ways:

``single``    the distribution over draws, which is what a one-shot heuristic
              actually delivers;
``best_inner``the draw whose inner criterion is highest, i.e. randomised search
              over the same criterion;
``ensemble``  one classifier per draw, their predictions combined, which gains
              from decorrelated errors rather than from searching harder
              (Ho, 1998, Random Subspace Method, IEEE TPAMI 20(8):832-844).

Ranking, weights, k and every draw come from the outer training partition only;
the external test is touched once per reported subset.
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

REPO = SRC.parent
BETAS = (0.0, 0.5, 1.0, 2.0, 4.0, 8.0)


def rank_weights(order: list[str], beta: float) -> np.ndarray:
    """Weight of each block by its position, best first."""
    n = len(order)
    ranks = np.arange(1, n + 1)
    weights = (n - ranks + 1.0) ** beta
    return weights / weights.sum()


def metrics(y_true, y_pred, labels) -> dict:
    return {"macro_f1": float(f1_score(y_true, y_pred, labels=labels,
                                       average="macro", zero_division=0)),
            "accuracy": float(accuracy_score(y_true, y_pred))}


def decision_scores(model, x: np.ndarray) -> np.ndarray:
    """Standardised decision values so members contribute on a common scale."""
    scores = np.asarray(model.decision_function(x))
    if scores.ndim == 1:
        scores = np.column_stack([-scores, scores])
    sd = scores.std()
    return scores / sd if sd > 0 else scores


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
    parser.add_argument("--draws", type=int, default=25,
                        help="subsets sampled per beta")
    parser.add_argument("--betas", type=float, nargs="+", default=list(BETAS))
    parser.add_argument("--k", type=int,
                        help="subset size; defaults to the archived GFS k, which "
                             "is what the Top-k control uses")
    parser.add_argument("--results-root", type=Path,
                        help="directory holding the archived nested_fold_results.csv "
                             "that supplies k (defaults to --audit-root)")
    parser.add_argument("--ngram-result-subdir", default="ngram22_beitv2")
    parser.add_argument("--n-jobs", type=int, default=10)
    parser.add_argument("--skip-draw-inner", action="store_true",
                        help="do not score each draw on the inner folds; drops "
                             "the best_inner variant and about four fifths of "
                             "the cost")
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--manifest-root", type=Path, required=True)
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
    inner_groups = (groups if args.inner_group_column is None
                    else manifest_groups(rows, args.inner_group_column))
    fold = (args.official_split - 1 if args.official_split is not None
            else {"a_to_b": 0, "b_to_a": 1}[args.curet_direction]
            if args.curet_direction is not None else args.fold)

    k = args.k
    if k is None:
        root = (args.results_root or args.audit_root).resolve()
        k = archived_k(root, args.dataset, args.classifier, args.seed, fold,
                       include_rgb_ngram=True,
                       ngram_result_subdir=args.ngram_result_subdir)

    # Rank the singletons exactly as the Top-k control does.
    names = sorted(cache)
    jobs = args.n_jobs if args.classifier == "svm" else 1
    single_scores = Parallel(n_jobs=jobs, prefer="threads")(
        delayed(inner_score)(cache, [n], train, y, inner_groups,
                             args.classifier, args.seed) for n in names)
    singles = dict(zip(names, single_scores))
    order = [n for n, _ in sorted(singles.items(), key=lambda kv: (-kv[1], kv[0]))]
    topk_subset = order[:k]
    topk_f1, topk_acc, _ = fit_score_foldaware(
        cache, topk_subset, train, test, y, args.classifier, args.seed)

    labels = np.unique(y)
    y_test = y[test]

    def external(subset):
        x = np.concatenate([cache[b] for b in subset], axis=1)
        model = make_model(args.classifier, args.seed)
        model.fit(x[train], y[train])
        pred = np.asarray(model.predict(x[test]))
        return pred, decision_scores(model, x[test]), metrics(y_test, pred, labels)

    report = {
        "dataset": args.dataset, "classifier": args.classifier, "seed": args.seed,
        "outer_fold": fold, "k": k, "draws": args.draws,
        "n_candidates": len(names),
        "inner_group_column": args.inner_group_column or "group",
        "ranking": [{"block": n, "inner_f1": singles[n]} for n in order],
        "topk": {"subset": topk_subset, "macro_f1": topk_f1, "accuracy": topk_acc,
                 "dimensions": int(sum(cache[b].shape[1] for b in topk_subset))},
        "betas": [],
        "weight_scheme": "w_r = (n - r + 1) ** beta over the inner ranking",
    }

    print(f"{args.dataset} {args.classifier} fold {fold}   k={k}, {args.draws} sorteos")
    print(f"  Top-k (determinista): macro-F1 {topk_f1:.4f}")
    print(f"\n  {'beta':>6}{'sorteo medio':>14}{'sd':>8}{'peor':>8}{'mejor':>8}"
          f"{'mejor-inner':>13}{'ensamble':>10}{'ens.voto':>10}{'dims':>8}")

    for beta in args.betas:
        # Draw sequentially so the sample is reproducible, then evaluate the
        # independent draws in parallel.
        rng = np.random.default_rng(args.seed * 1000 + fold * 10 + int(beta * 2))
        probs = rank_weights(order, beta)
        subsets = [sorted(order[i] for i in
                          rng.choice(len(order), size=k, replace=False, p=probs))
                   for _ in range(args.draws)]

        def evaluate_draw(subset):
            pred, scores, met = external(subset)
            inner = (inner_score(cache, subset, train, y, inner_groups,
                                 args.classifier, args.seed)
                     if not args.skip_draw_inner else float("nan"))
            return {"subset": subset, "inner_f1": inner, **met,
                    "dimensions": int(sum(cache[b].shape[1] for b in subset)),
                    "_pred": pred, "_scores": scores}

        draws = Parallel(n_jobs=jobs, prefer="threads")(
            delayed(evaluate_draw)(s) for s in subsets)
        seen = {tuple(s) for s in subsets}

        f1s = np.array([d["macro_f1"] for d in draws])
        best_inner = max(draws, key=lambda d: d["inner_f1"])
        # Soft ensemble: average standardised decision values across members.
        soft = np.mean([d["_scores"] for d in draws], axis=0)
        soft_pred = labels[np.argmax(soft, axis=1)] if soft.shape[1] == len(labels) \
            else np.asarray([draws[0]["_pred"][i] for i in range(len(y_test))])
        ens_soft = metrics(y_test, soft_pred, labels)
        # Hard ensemble: majority vote over member predictions.
        votes = np.stack([d["_pred"] for d in draws])
        hard_pred = np.asarray([np.bincount(
            np.searchsorted(labels, votes[:, i]), minlength=len(labels)).argmax()
            for i in range(votes.shape[1])])
        ens_hard = metrics(y_test, labels[hard_pred], labels)

        entry = {
            "beta": beta,
            "unique_subsets": len(seen),
            "single": {"mean_macro_f1": float(f1s.mean()), "sd": float(f1s.std(ddof=1)),
                       "min": float(f1s.min()), "max": float(f1s.max())},
            "best_inner": {"subset": best_inner["subset"],
                           "inner_f1": best_inner["inner_f1"],
                           "macro_f1": best_inner["macro_f1"]},
            "ensemble_soft": ens_soft, "ensemble_hard": ens_hard,
            "mean_dimensions": float(np.mean([d["dimensions"] for d in draws])),
            "draws": [{kk: vv for kk, vv in d.items() if not kk.startswith("_")}
                      for d in draws],
        }
        report["betas"].append(entry)
        print(f"  {beta:>6.1f}{f1s.mean():>14.4f}{f1s.std(ddof=1):>8.4f}"
              f"{f1s.min():>8.4f}{f1s.max():>8.4f}"
              f"{best_inner['macro_f1']:>13.4f}{ens_soft['macro_f1']:>10.4f}"
              f"{ens_hard['macro_f1']:>10.4f}{entry['mean_dimensions']:>8.0f}")

    report["duration_seconds"] = time.perf_counter() - started
    output.mkdir(parents=True, exist_ok=True)
    tag = (f"official{args.official_split}"
           + ("_inverted" if args.invert_official_split else "")
           if args.official_split is not None
           else args.curet_direction or f"f{args.fold}")
    stem = f"{args.dataset}_{args.classifier}_s{args.seed}_{tag}_lottery"
    (output / f"{stem}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)
                                         + "\n", encoding="utf-8")

    flat = []
    for entry in report["betas"]:
        base = {"dataset": args.dataset, "classifier": args.classifier,
                "seed": args.seed, "outer_fold": fold, "k": k, "beta": entry["beta"]}
        flat.append({**base, "variant": "single_mean",
                     "macro_f1": entry["single"]["mean_macro_f1"],
                     "sd": entry["single"]["sd"],
                     "dimensions": entry["mean_dimensions"]})
        flat.append({**base, "variant": "best_inner",
                     "macro_f1": entry["best_inner"]["macro_f1"], "sd": "",
                     "dimensions": entry["mean_dimensions"]})
        flat.append({**base, "variant": "ensemble_soft",
                     "macro_f1": entry["ensemble_soft"]["macro_f1"], "sd": "",
                     "dimensions": entry["mean_dimensions"]})
        flat.append({**base, "variant": "ensemble_hard",
                     "macro_f1": entry["ensemble_hard"]["macro_f1"], "sd": "",
                     "dimensions": entry["mean_dimensions"]})
    flat.append({"dataset": args.dataset, "classifier": args.classifier,
                 "seed": args.seed, "outer_fold": fold, "k": k, "beta": "",
                 "variant": "topk_deterministic", "macro_f1": topk_f1, "sd": "",
                 "dimensions": report["topk"]["dimensions"]})
    path = output / "lottery_rows.csv"
    pd.DataFrame(flat).to_csv(path, mode="a", header=not path.exists(), index=False)
    print(f"\n  escrito en {output}  ({report['duration_seconds']:.0f}s)")


if __name__ == "__main__":
    main()
