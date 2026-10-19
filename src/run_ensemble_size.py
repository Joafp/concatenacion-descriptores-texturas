#!/usr/bin/env python3
"""How many members does a sampling ensemble need?

The rank lottery and the diversity sampling were reported with 15 members.  This
script draws a longer sequence of subsets for the two reported configurations
(lottery with ``beta = 8``; diversity with ``lambda = 0.25`` and ``beta = 8``)
using the same generators and seeds as the original runs, so the first 15 draws
are exactly the subsets those runs used.  Every prefix of the sequence is then
scored as a soft ensemble, which gives the accuracy as a function of the number
of members on one nested sample, as is usual for ensemble-size curves.

A subset drawn twice yields the same model, because members share the
classifier seed; each distinct subset is therefore trained once and its
decision values reused.
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

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analyze_block_redundancy import linear_cka  # noqa: E402
from run_confirmatory_nested import (  # noqa: E402
    audit_gate, load_dataset, load_manifest, make_model, manifest_groups,
)
from run_diversity_lottery import draw_subset  # noqa: E402
from run_topk_individual_control import outer_indices  # noqa: E402
from run_weighted_lottery_selection import decision_scores, metrics, rank_weights  # noqa: E402
from singleton_ranking import condition_key, ranked_singletons  # noqa: E402

REPO = SRC.parent
BETA, LAMBDA = 8.0, 0.25


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
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--members", type=int, default=50)
    parser.add_argument("--sizes", type=int, nargs="+", default=[1, 3, 5, 10, 15, 25, 50])
    parser.add_argument("--n-jobs", type=int, default=6)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--embedding-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.dataset == "CUReT" and not args.curet_direction:
        parser.error("CUReT requires --curet-direction")
    if max(args.sizes) > args.members:
        parser.error("every size must be at most --members")

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
    k = args.k

    # Lottery: the generator and draw loop of run_weighted_lottery_selection.
    rng = np.random.default_rng(args.seed * 1000 + fold * 10 + int(BETA * 2))
    probs = rank_weights(order, BETA)
    lottery = [sorted(order[i] for i in rng.choice(len(order), size=k, replace=False, p=probs))
               for _ in range(args.members)]

    # Diversity: relevance, CKA and generator of run_diversity_lottery.
    lo, hi = min(singles.values()), max(singles.values())
    relevance = {n: (v - lo) / ((hi - lo) or 1.0) for n, v in singles.items()}
    mats = {n: cache[n][train].astype(np.float64) for n in names}
    pairs = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]]
    vals = Parallel(n_jobs=jobs, prefer="threads")(
        delayed(linear_cka)(mats[a], mats[b]) for a, b in pairs)
    cka = {(a, b): v for (a, b), v in zip(pairs, vals)}
    cka.update({(b, a): v for (a, b), v in zip(pairs, vals)})
    del mats
    rng = np.random.default_rng(args.seed * 1000 + fold * 10 + int(LAMBDA * 7) + int(BETA))
    diversity = [draw_subset(names, relevance, cka, LAMBDA, BETA, k, rng)
                 for _ in range(args.members)]

    labels, y_test = np.unique(y), y[test]

    def member(subset):
        x = np.concatenate([cache[b] for b in subset], axis=1)
        model = make_model(args.classifier, args.seed)
        model.fit(x[train], y[train])
        pred = np.asarray(model.predict(x[test]))
        return decision_scores(model, x[test]), metrics(y_test, pred, labels)

    distinct = sorted({tuple(s) for s in lottery + diversity})
    fitted = dict(zip(distinct, Parallel(n_jobs=jobs, prefer="threads")(
        delayed(member)(list(s)) for s in distinct)))

    record = {"dataset": args.dataset, "classifier": args.classifier, "seed": args.seed,
              "outer_fold": fold, "k": k, "members": args.members, "beta": BETA,
              "lambda": LAMBDA, "distinct_subsets_fitted": len(distinct), "methods": {}}
    flat = []
    for method, subsets in (("tombola", lottery), ("diversidad", diversity)):
        curve = {}
        for m in args.sizes:
            soft = np.mean([fitted[tuple(s)][0] for s in subsets[:m]], axis=0)
            met = metrics(y_test, labels[np.argmax(soft, axis=1)], labels)
            curve[m] = {**met, "distinct": len({tuple(s) for s in subsets[:m]})}
            flat.append({"dataset": args.dataset, "classifier": args.classifier,
                         "seed": args.seed, "outer_fold": fold, "method": method,
                         "members": m, **met, "distinct": curve[m]["distinct"]})
        record["methods"][method] = {
            "subsets": subsets, "curve": curve,
            "member_macro_f1": [fitted[tuple(s)][1]["macro_f1"] for s in subsets]}
    record["duration_seconds"] = time.perf_counter() - started

    output.mkdir(parents=True, exist_ok=True)
    tag = (f"official{args.official_split}" + ("_inverted" if args.invert_official_split else "")
           if args.official_split is not None else args.curet_direction or f"f{args.fold}")
    stem = f"{args.dataset}_{args.classifier}_s{args.seed}_{tag}_size"
    (output / f"{stem}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    path = output / "size_rows.csv"
    pd.DataFrame(flat).to_csv(path, mode="a", header=not path.exists(), index=False)
    print(f"{args.dataset} {args.classifier} {tag}: "
          + " | ".join(f"{meth} " + " ".join(f"{m}:{v['macro_f1']:.4f}"
                                             for m, v in r["curve"].items())
                       for meth, r in record["methods"].items())
          + f"  ({len(distinct)} modelos, {record['duration_seconds']:.0f}s)")


if __name__ == "__main__":
    main()
