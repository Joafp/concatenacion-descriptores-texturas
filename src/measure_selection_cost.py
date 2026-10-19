#!/usr/bin/env python3
"""Wall-clock cost of selecting four blocks against concatenating all of them.

Fewer dimensions make each model cheaper, but choosing the blocks is not free:
Top-4 needs the inner ranking of every block (one inner cross-validation per
block), and the diversity sampling also needs the CKA between every pair of
blocks.  This script times, on one external condition, the whole training path
of each method from the cached embeddings:

``top4``        inner ranking + one model on four blocks;
``all21``       one model on the 21 stored blocks, the full concatenation
                without the colour block, which is rebuilt per fold and is not
                part of the embeddings;
``tombola``     inner ranking + one model per distinct subset of the 15 draws;
``diversidad``  inner ranking + CKA + one model per distinct subset.

Everything runs sequentially (``n_jobs = 1``) so the times add up to the work
done.  The ranking is recomputed in a temporary directory instead of read from
the cache.  Prediction time covers the external test images.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analyze_block_redundancy import linear_cka  # noqa: E402
from run_confirmatory_nested import (  # noqa: E402
    audit_gate, load_dataset, load_manifest, make_model, manifest_groups,
)
from run_diversity_lottery import draw_subset  # noqa: E402
from run_topk_individual_control import outer_indices  # noqa: E402
from run_weighted_lottery_selection import rank_weights  # noqa: E402
from singleton_ranking import condition_key, ranked_singletons  # noqa: E402

REPO = SRC.parent
BETA, LAMBDA, DRAWS = 8.0, 0.25, 15


def parameters(model) -> int:
    if hasattr(model, "net_"):
        return int(sum(p.numel() for p in model.net_.parameters()))
    return int(model.coef_.size + np.size(model.intercept_))


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
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--embedding-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.dataset == "CUReT" and not args.curet_direction:
        parser.error("CUReT requires --curet-direction")

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
    inner_groups = (groups if args.inner_group_column is None
                    else manifest_groups(rows, args.inner_group_column))
    fold = (args.official_split - 1 if args.official_split is not None
            else {"a_to_b": 0, "b_to_a": 1}[args.curet_direction]
            if args.curet_direction is not None else args.fold)
    names = sorted(cache)

    with tempfile.TemporaryDirectory() as tmp:
        t0 = time.perf_counter()
        singles = ranked_singletons(cache, train, y, inner_groups, args.classifier,
                                    args.seed, condition_key(args), n_jobs=1,
                                    cache_dir=Path(tmp))
        ranking_s = time.perf_counter() - t0
    order = [n for n, _ in sorted(singles.items(), key=lambda kv: (-kv[1], kv[0]))]

    t0 = time.perf_counter()
    mats = {n: cache[n][train].astype(np.float64) for n in names}
    cka = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            cka[(a, b)] = cka[(b, a)] = linear_cka(mats[a], mats[b])
    del mats
    cka_s = time.perf_counter() - t0

    rng = np.random.default_rng(args.seed * 1000 + fold * 10 + int(BETA * 2))
    probs = rank_weights(order, BETA)
    lottery = [sorted(order[i] for i in rng.choice(len(order), size=args.k, replace=False,
                                                   p=probs)) for _ in range(DRAWS)]
    lo, hi = min(singles.values()), max(singles.values())
    relevance = {n: (v - lo) / ((hi - lo) or 1.0) for n, v in singles.items()}
    rng = np.random.default_rng(args.seed * 1000 + fold * 10 + int(LAMBDA * 7) + int(BETA))
    diversity = [draw_subset(names, relevance, cka, LAMBDA, BETA, args.k, rng)
                 for _ in range(DRAWS)]

    def cost(subsets):
        """Fit and predict once per distinct subset, timing each phase."""
        fit_s = predict_s = 0.0
        params, dims = 0, []
        for subset in sorted({tuple(s) for s in subsets}):
            x = np.concatenate([cache[b] for b in subset], axis=1)
            x_train, x_test = np.ascontiguousarray(x[train]), np.ascontiguousarray(x[test])
            model = make_model(args.classifier, args.seed)
            t0 = time.perf_counter()
            model.fit(x_train, y[train])
            fit_s += time.perf_counter() - t0
            t0 = time.perf_counter()
            model.predict(x_test)
            predict_s += time.perf_counter() - t0
            params += parameters(model)
            dims.append(x.shape[1])
        return {"models": len(dims), "dimensions": float(np.mean(dims)), "parameters": params,
                "fit_seconds": fit_s, "predict_seconds": predict_s}

    methods = {
        "top4": {**cost([order[:args.k]]), "selection_seconds": ranking_s},
        "all21": {**cost([order]), "selection_seconds": 0.0},
        "tombola": {**cost(lottery), "selection_seconds": ranking_s},
        "diversidad": {**cost(diversity), "selection_seconds": ranking_s + cka_s},
    }
    output.mkdir(parents=True, exist_ok=True)
    tag = (f"official{args.official_split}" + ("_inverted" if args.invert_official_split else "")
           if args.official_split is not None else args.curet_direction or f"f{args.fold}")
    record = {"dataset": args.dataset, "classifier": args.classifier, "seed": args.seed,
              "outer_fold": fold, "train_images": int(len(train)),
              "test_images": int(len(test)), "ranking_seconds": ranking_s,
              "cka_seconds": cka_s, "methods": methods}
    stem = f"{args.dataset}_{args.classifier}_s{args.seed}_{tag}_cost"
    (output / f"{stem}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    flat = [{"dataset": args.dataset, "classifier": args.classifier, "seed": args.seed,
             "outer_fold": fold, "method": m, **v,
             "total_train_seconds": v["selection_seconds"] + v["fit_seconds"]}
            for m, v in methods.items()]
    path = output / "cost_rows.csv"
    pd.DataFrame(flat).to_csv(path, mode="a", header=not path.exists(), index=False)
    print(f"{args.dataset} {args.classifier} {tag}: " + " | ".join(
        f"{m} sel {v['selection_seconds']:.0f}s fit {v['fit_seconds']:.1f}s "
        f"pred {v['predict_seconds']:.2f}s" for m, v in methods.items()))


if __name__ == "__main__":
    main()
