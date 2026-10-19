#!/usr/bin/env python3
"""External performance of the Top-k rule for every k, not just the archived one.

The Top-k control inherits its subset size from the GFS run of the same
condition, so each dataset contributes a single point on the accuracy-versus-size
plane.  Sweeping k from one block to the whole library traces the curve instead,
which is what an efficiency claim needs: how much of the full concatenation's
accuracy a given fraction of its dimensions buys.

The ranking is the same one Top-k uses and comes from the inner folds of the
outer training partition; only the final evaluation of each prefix touches the
external test.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from run_confirmatory_nested import (  # noqa: E402
    audit_gate, fit_score_foldaware, inner_score, load_dataset, load_manifest,
    manifest_groups,
)
from run_topk_individual_control import outer_indices  # noqa: E402
from singleton_ranking import condition_key, ranked_singletons  # noqa: E402

REPO = SRC.parent


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
    parser.add_argument("--n-jobs", type=int, default=10)
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

    names = sorted(cache)
    jobs = args.n_jobs if args.classifier == "svm" else 1
    singles = ranked_singletons(cache, train, y, inner_groups, args.classifier,
                                args.seed, condition_key(args), n_jobs=jobs)
    order = [n for n, _ in sorted(singles.items(), key=lambda kv: (-kv[1], kv[0]))]

    def evaluate(k):
        subset = order[:k]
        f1, acc, seconds = fit_score_foldaware(cache, subset, train, test, y,
                                               args.classifier, args.seed)
        return {"dataset": args.dataset, "classifier": args.classifier,
                "seed": args.seed, "outer_fold": fold, "k": k,
                "macro_f1": f1, "accuracy": acc,
                "dimensions": int(sum(cache[b].shape[1] for b in subset)),
                "added": order[k - 1], "fit_seconds": seconds,
                "selected": "+".join(subset)}

    # Sequential on purpose: the prefix at large k is the whole library, so a
    # parallel sweep holds several full concatenations at once and exhausts
    # memory on the larger datasets.  The per-fit cost dominates anyway.
    frame = pd.DataFrame([evaluate(k) for k in range(1, len(order) + 1)])
    full_dims = frame["dimensions"].iloc[-1]
    frame["pct_dimensions"] = 100 * frame["dimensions"] / full_dims

    output.mkdir(parents=True, exist_ok=True)
    path = output / "k_sweep.csv"
    frame.to_csv(path, mode="a", header=not path.exists(), index=False)

    best = frame.loc[frame["macro_f1"].idxmax()]
    full = frame.iloc[-1]
    print(f"{args.dataset} {args.classifier} fold {fold}  ({len(order)} bloques)")
    print(f"  {'k':>3}{'macro-F1':>10}{'exactitud':>11}{'dims':>8}{'% total':>9}  bloque agregado")
    for _, r in frame.iterrows():
        mark = " <- maximo" if r["k"] == best["k"] else ""
        print(f"  {int(r['k']):>3}{r['macro_f1']:>10.4f}{r['accuracy']:>11.4f}"
              f"{int(r['dimensions']):>8}{r['pct_dimensions']:>8.0f}%  {r['added']}{mark}")
    print(f"\n  maximo en k={int(best['k'])}: {best['macro_f1']:.4f} "
          f"con {best['pct_dimensions']:.0f}% de las dimensiones")
    print(f"  biblioteca completa : {full['macro_f1']:.4f}")
    print(f"  diferencia          : {best['macro_f1'] - full['macro_f1']:+.4f}")
    print(f"  ({time.perf_counter() - started:.0f}s)")


if __name__ == "__main__":
    main()
