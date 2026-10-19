#!/usr/bin/env python3
"""The inner-criterion curve over k, to decide k without the external test.

``run_k_sweep.py`` traces how external macro-F1 varies with the number of
concatenated blocks, and that curve flattens around four blocks.  Reading k off
it, however, means reading it off the external test.  This script computes the
same prefixes scored on the inner folds of the outer training partition, so a
rule applied to that curve chooses k from training information alone.

Whether such a rule lands near the external optimum is the open question: this
repository already documents that the inner criterion predicts external
performance poorly once a subset is large enough, so the curves may well
disagree.  The companion analysis compares them.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from run_confirmatory_nested import (  # noqa: E402
    audit_gate, inner_score, load_dataset, load_manifest, manifest_groups,
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

    # Sequential for the same reason as the external sweep: the large prefixes
    # are the whole library and several at once exhaust memory.
    records = []
    for k in range(1, len(order) + 1):
        subset = order[:k]
        value = inner_score(cache, subset, train, y, inner_groups,
                            args.classifier, args.seed)
        records.append({"dataset": args.dataset, "classifier": args.classifier,
                        "seed": args.seed, "outer_fold": fold, "k": k,
                        "inner_f1": value,
                        "dimensions": int(sum(cache[b].shape[1] for b in subset)),
                        "added": order[k - 1], "selected": "+".join(subset)})
    frame = pd.DataFrame(records)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "k_sweep_inner.csv"
    frame.to_csv(path, mode="a", header=not path.exists(), index=False)

    best = frame.loc[frame["inner_f1"].idxmax()]
    print(f"{args.dataset} {args.classifier} fold {fold}  ({len(order)} bloques)")
    for _, r in frame.iterrows():
        mark = " <- maximo interno" if r["k"] == best["k"] else ""
        print(f"  k={int(r['k']):>2}  inner-F1 {r['inner_f1']:.4f}  {r['added']}{mark}")
    print(f"  maximo interno en k={int(best['k'])}  ({time.perf_counter() - started:.0f}s)")


if __name__ == "__main__":
    main()
