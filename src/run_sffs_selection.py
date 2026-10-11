#!/usr/bin/env python3
"""Sequential Forward Floating Selection over descriptor blocks.

Greedy forward selection cannot discard a block once it has been added, so an
early choice that later turns out to be mediocre stays in the subset for the
rest of the search.  Pudil, Novovicova and Kittler (1994) call this the nesting
effect and answer it with a conditional backtracking step: after each inclusion,
the least significant block of the enlarged subset is removed whenever that
leaves a subset better than the best one of that size found so far.

This runner reuses the confirmatory protocol unchanged -- the same inner
criterion, the same grouped inner folds, the same classifiers, the external test
touched once at the end -- and swaps only the search.  Results are written in the
schema of ``nested_fold_results.csv`` so the existing comparisons apply.

Reference: Pudil, P., Novovicova, J. & Kittler, J. (1994). Floating search
methods in feature selection. Pattern Recognition Letters 15(11), 1119-1125.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from run_confirmatory_nested import (  # noqa: E402
    audit_gate, fit_score_foldaware, inner_score, load_dataset, load_manifest,
    manifest_groups,
)
from run_topk_individual_control import outer_indices  # noqa: E402

REPO = SRC.parent
NEG = float("-inf")


def score_subsets(cache, specs, outer_train, y, groups, classifier, seed,
                  memo, n_jobs, svm_backend, ngram_block):
    """Evaluate each candidate subset once, reusing a shared memo."""
    missing = [s for s in specs if s not in memo]
    if missing:
        effective = n_jobs if classifier == "svm" and svm_backend == "cpu" else 1
        values = Parallel(n_jobs=effective, prefer="threads")(
            delayed(inner_score)(cache, list(subset), outer_train, y, groups,
                                 classifier, seed, svm_backend=svm_backend,
                                 ngram_block=ngram_block)
            for subset in missing
        )
        memo.update(dict(zip(missing, values)))
    return {s: memo[s] for s in specs}


def sffs(cache, candidates, outer_train, y, groups, classifier, seed, max_k,
         n_jobs=2, score_cache=None, svm_backend="cpu", ngram_block=None):
    """Return the best subset the floating search reaches, and its trace.

    ``best_at`` keeps the strongest subset seen for every cardinality, which is
    what the conditional exclusion tests against: a removal is accepted only if
    the smaller subset it produces beats the best previously known subset of
    that size.
    """
    memo = {} if score_cache is None else score_cache
    pool = sorted(candidates)
    selected: list[str] = []
    best_at: dict[int, tuple[float, list[str]]] = {}
    history: list[dict] = []

    def evaluate(subsets):
        return score_subsets(cache, subsets, outer_train, y, groups, classifier,
                             seed, memo, n_jobs, svm_backend, ngram_block)

    # Every accepted exclusion strictly raises the best value known for its
    # cardinality, so the search terminates; the cap only bounds pathological
    # include/exclude cycling on near-ties.
    rounds, max_rounds = 0, 20 * max_k
    while len(selected) < max_k and rounds < max_rounds:
        rounds += 1
        remaining = [c for c in pool if c not in selected]
        if not remaining:
            break

        # --- inclusion: add the most significant remaining block ---
        specs = [tuple(sorted(selected + [c])) for c in remaining]
        scored = evaluate(specs)
        # Tie-break by name, matching the greedy runner's deterministic rule.
        value, added = max(((scored[tuple(sorted(selected + [c]))], c)
                            for c in remaining), key=lambda item: item)
        selected.append(added)
        k = len(selected)
        history.append({"step": len(history) + 1, "op": "include", "block": added,
                        "k": k, "inner_f1": value})
        if value > best_at.get(k, (NEG, None))[0]:
            best_at[k] = (value, sorted(selected))
        just_added = added

        # --- conditional exclusion: backtrack while it pays off ---
        while len(selected) > 2:
            k = len(selected)
            specs = [tuple(sorted(x for x in selected if x != drop))
                     for drop in selected]
            scored = evaluate(specs)
            value, dropped = max(
                ((scored[tuple(sorted(x for x in selected if x != drop))], drop)
                 for drop in selected), key=lambda item: item)
            if dropped == just_added:
                # Removing what was just added would only undo the inclusion.
                break
            if value <= best_at.get(k - 1, (NEG, None))[0]:
                break
            selected.remove(dropped)
            history.append({"step": len(history) + 1, "op": "exclude",
                            "block": dropped, "k": k - 1, "inner_f1": value})
            best_at[k - 1] = (value, sorted(selected))
            just_added = None

    if not best_at:
        raise RuntimeError("floating search produced no subset")
    best_value, best_subset = max(best_at.values(), key=lambda item: item[0])
    return best_subset, best_value, history, best_at


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
    parser.add_argument("--max-k", type=int, default=8)
    parser.add_argument("--n-jobs", type=int, default=2)
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

    subset, inner_f1, history, best_at = sffs(
        cache, sorted(cache), train, y, inner_groups, args.classifier, args.seed,
        args.max_k, n_jobs=args.n_jobs)
    external_f1, accuracy, seconds = fit_score_foldaware(
        cache, subset, train, test, y, args.classifier, args.seed)

    protocol = ((f"official{args.official_split}"
                 + ("_inverted" if args.invert_official_split else ""))
                if args.official_split is not None
                else f"curet:{args.curet_direction}" if args.curet_direction
                else f"skf5_fold{args.fold}")
    row = {
        "dataset": args.dataset, "classifier": args.classifier, "seed": args.seed,
        "outer_fold": fold, "run_mode": "full", "method": "sffs",
        "macro_f1": external_f1, "accuracy": accuracy, "k": len(subset),
        "dimensions": sum(cache[b].shape[1] for b in subset),
        "fit_seconds": seconds, "selected": "+".join(subset), "inner_f1": inner_f1,
    }
    output.mkdir(parents=True, exist_ok=True)
    results = output / "nested_fold_results.csv"
    write_header = not results.exists()
    with results.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    record = {
        **{k: row[k] for k in ("dataset", "classifier", "seed", "outer_fold")},
        "protocol": protocol,
        "inner_group_column": args.inner_group_column or "group",
        "max_k": args.max_k, "n_candidates": len(cache),
        "sffs": subset, "inner_f1": inner_f1,
        "n_inclusions": sum(1 for h in history if h["op"] == "include"),
        "n_exclusions": sum(1 for h in history if h["op"] == "exclude"),
        "best_per_cardinality": {str(k): {"inner_f1": v[0], "subset": v[1]}
                                 for k, v in sorted(best_at.items())},
        "history": history,
        "duration_seconds": time.perf_counter() - started,
    }
    with (output / "sffs_search.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"{args.dataset} {args.classifier} {protocol}")
    print(f"  inclusiones {record['n_inclusions']}, "
          f"exclusiones {record['n_exclusions']}  "
          f"({record['duration_seconds']:.0f}s)")
    print(f"  subconjunto k={len(subset)}: {'+'.join(subset)}")
    print(f"  inner-F1 {inner_f1:.4f}   macro-F1 externo {external_f1:.4f}")


if __name__ == "__main__":
    main()
