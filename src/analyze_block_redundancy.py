#!/usr/bin/env python3
"""How much do the best-ranked descriptor blocks repeat each other?

Top-k concatenates the k blocks with the highest individual inner score, a rule
that never asks whether those blocks carry the same information.  If the top of
the ranking is dominated by variants of one backbone, part of the budget buys
nothing, and a rule that favours dissimilar blocks has room to help.  If the top
blocks are already diverse, it has none.

Similarity is linear Centered Kernel Alignment (Kornblith et al., 2019), computed
on the outer training rows only:

    CKA(X, Y) = ||Y^T X||_F^2 / (||X^T X||_F * ||Y^T Y||_F)

with both matrices column-centred.  CKA is invariant to orthogonal transforms and
isotropic scaling, which is what makes it comparable across blocks of different
width.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from run_confirmatory_nested import (  # noqa: E402
    audit_gate, inner_score, load_dataset, load_manifest, manifest_groups,
)
from run_topk_individual_control import archived_k, outer_indices  # noqa: E402

REPO = SRC.parent


def linear_cka(x: np.ndarray, y: np.ndarray) -> float:
    """Linear CKA between two centred representations of the same rows."""
    x = x - x.mean(axis=0, keepdims=True)
    y = y - y.mean(axis=0, keepdims=True)
    cross = np.linalg.norm(y.T @ x, ord="fro") ** 2
    denom = (np.linalg.norm(x.T @ x, ord="fro")
             * np.linalg.norm(y.T @ y, ord="fro"))
    return float(cross / denom) if denom > 0 else 0.0


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
    parser.add_argument("--results-root", type=Path)
    parser.add_argument("--ngram-result-subdir", default="ngram22_beitv2")
    parser.add_argument("--embedding-root", type=Path)
    parser.add_argument("--output", type=Path,
                        default=REPO / "results/analysis/block_redundancy")
    args = parser.parse_args()
    if args.dataset == "CUReT" and not args.curet_direction:
        parser.error("CUReT requires --curet-direction")

    audit_root, manifest_root = args.audit_root.resolve(), args.manifest_root.resolve()
    embedding_root = args.embedding_root.resolve() if args.embedding_root else None
    audit_gate(audit_root, args.dataset)
    cache, y = load_dataset(REPO, args.dataset, embedding_root=embedding_root)
    for name in args.exclude_extractors:
        cache.pop(name, None)
    groups, rows = load_manifest(manifest_root, args.dataset, y)
    train, _ = outer_indices(args.dataset, args.seed, args.fold, y, groups, rows,
                             args.official_split, args.curet_direction,
                             args.invert_official_split)
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
    order = [n for n, _ in sorted(singles.items(), key=lambda kv: (-kv[1], kv[0]))]

    mats = {n: cache[n][train].astype(np.float64) for n in names}
    pairs = [(a, b) for i, a in enumerate(order) for b in order[i + 1:]]
    values = Parallel(n_jobs=jobs, prefer="threads")(
        delayed(linear_cka)(mats[a], mats[b]) for a, b in pairs)
    cka = {(a, b): v for (a, b), v in zip(pairs, values)}
    cka.update({(b, a): v for (a, b), v in zip(pairs, values)})

    def mean_pairwise(subset):
        vals = [cka[(a, b)] for i, a in enumerate(subset) for b in subset[i + 1:]]
        return float(np.mean(vals)) if vals else float("nan")

    topk = order[:k]
    rest = order[k:]
    rng = np.random.default_rng(args.seed)
    random_sets = [sorted(rng.choice(names, size=k, replace=False).tolist())
                   for _ in range(200)]
    random_mean = float(np.mean([mean_pairwise(s) for s in random_sets]))

    print(f"{args.dataset} {args.classifier} fold {fold}   k={k}, {len(names)} bloques\n")
    print("ranking individual (interno) y su CKA medio con los demas del top-k:")
    for i, n in enumerate(topk, 1):
        others = [m for m in topk if m != n]
        avg = float(np.mean([cka[(n, m)] for m in others])) if others else float("nan")
        print(f"  {i:>2}. {n:<22} inner={singles[n]:.4f}   CKA medio en el top-k = {avg:.3f}")

    print(f"\nCKA medio dentro del Top-k      : {mean_pairwise(topk):.3f}")
    print(f"CKA medio de subconjuntos al azar: {random_mean:.3f}")
    print(f"CKA medio entre todos los pares  : "
          f"{float(np.mean(list({frozenset(p): v for p, v in cka.items()}.values()))):.3f}")

    print("\npares mas redundantes de toda la biblioteca:")
    uniq = sorted({(frozenset([a, b]), v) for (a, b), v in cka.items()},
                  key=lambda kv: -kv[1])[:8]
    for pair, v in uniq:
        a, b = sorted(pair)
        mark = "  <- ambos en el Top-k" if a in topk and b in topk else ""
        print(f"  {v:.3f}  {a} ~ {b}{mark}")

    args.output.mkdir(parents=True, exist_ok=True)
    tag = (f"official{args.official_split}" if args.official_split is not None
           else args.curet_direction or f"f{args.fold}")
    payload = {
        "dataset": args.dataset, "classifier": args.classifier, "outer_fold": fold,
        "k": k, "blocks": names,
        "ranking": [{"block": n, "inner_f1": singles[n]} for n in order],
        "topk": topk,
        "cka_mean_within_topk": mean_pairwise(topk),
        "cka_mean_random_subsets": random_mean,
        "cka_matrix": {f"{a}|{b}": v for (a, b), v in cka.items() if a < b},
    }
    (args.output / f"{args.dataset}_{args.classifier}_{tag}_cka.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nescrito en {args.output}")


if __name__ == "__main__":
    main()
