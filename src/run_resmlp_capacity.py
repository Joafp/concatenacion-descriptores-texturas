#!/usr/bin/env python3
"""Why does ResMLP lose with the full concatenation?

With SVM the 21-block concatenation matches Top-4, but with ResMLP it scores
below it.  The working hypothesis is overfitting: the first layer of ResMLP has
``dimensions x 256`` weights, about 5.3 million for the 21 blocks against 0.8
million for four, trained on a few thousand images.  If that is the cause, the
information is still in the 21 blocks and only the input size hurts, so

``pca``          projecting the 21 blocks onto as many principal components as
                 the Top-4 has dimensions (fitted on the training rows) should
                 recover performance, and
``regularized``  stronger dropout and weight decay on the 21 blocks should help,

while the training fit stays near perfect for every input (``train_*``).  The
manuscript classifier is used unchanged everywhere else; these variants are a
diagnostic, not a proposal.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from resmlp_classifier import ResMLPClassifier  # noqa: E402
from run_confirmatory_nested import (  # noqa: E402
    audit_gate, load_dataset, load_manifest, make_model, manifest_groups,
)
from run_topk_individual_control import outer_indices  # noqa: E402
from run_weighted_lottery_selection import metrics  # noqa: E402
from singleton_ranking import condition_key, ranked_singletons  # noqa: E402

REPO = SRC.parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fold", type=int, default=0, choices=range(5))
    split = parser.add_mutually_exclusive_group()
    split.add_argument("--official-split", type=int, choices=range(1, 11))
    split.add_argument("--curet-direction", choices=("a_to_b", "b_to_a"))
    parser.add_argument("--invert-official-split", action="store_true")
    parser.add_argument("--inner-group-column")
    parser.add_argument("--exclude-extractors", nargs="*", default=[])
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--weight-decay", type=float, default=1e-2)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--embedding-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.dataset == "CUReT" and not args.curet_direction:
        parser.error("CUReT requires --curet-direction")
    args.classifier = "resmlp"

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

    singles = ranked_singletons(cache, train, y, inner_groups, "resmlp", args.seed,
                                condition_key(args), n_jobs=1)
    order = [n for n, _ in sorted(singles.items(), key=lambda kv: (-kv[1], kv[0]))]
    labels, y_tr, y_te = np.unique(y), y[train], y[test]
    # Ranking order, as in the k sweep, so top4 and all21 reproduce its k=4 and
    # k=21 points exactly.
    x_top = np.concatenate([cache[b] for b in order[:args.k]], axis=1)
    x_all = np.concatenate([cache[b] for b in order], axis=1)
    dims = x_top.shape[1]
    pca = PCA(n_components=min(dims, len(train) - 1), svd_solver="randomized",
              random_state=args.seed).fit(x_all[train])
    x_pca = pca.transform(x_all)

    def run(model, x):
        model.fit(x[train], y_tr)
        params = sum(p.numel() for p in model.net_.parameters())
        return {"test": metrics(y_te, np.asarray(model.predict(x[test])), labels),
                "train": metrics(y_tr, np.asarray(model.predict(x[train])), labels),
                "dimensions": int(x.shape[1]), "parameters": int(params)}

    variants = {
        "top4": run(make_model("resmlp", args.seed), x_top),
        "all21": run(make_model("resmlp", args.seed), x_all),
        "all21_pca": run(make_model("resmlp", args.seed), x_pca),
        "all21_regularized": run(ResMLPClassifier(random_state=args.seed, max_epochs=100,
                                                  patience=10, dropout=args.dropout,
                                                  weight_decay=args.weight_decay), x_all),
    }
    record = {"dataset": args.dataset, "classifier": "resmlp", "seed": args.seed,
              "outer_fold": fold, "k": args.k, "subset": order[:args.k],
              "pca_components": int(pca.n_components_),
              "pca_explained_variance": float(pca.explained_variance_ratio_.sum()),
              "regularized": {"dropout": args.dropout, "weight_decay": args.weight_decay},
              "variants": variants, "duration_seconds": time.perf_counter() - started}

    output.mkdir(parents=True, exist_ok=True)
    tag = (f"official{args.official_split}" + ("_inverted" if args.invert_official_split else "")
           if args.official_split is not None else args.curet_direction or f"f{args.fold}")
    stem = f"{args.dataset}_resmlp_s{args.seed}_{tag}_capacity"
    (output / f"{stem}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    flat = [{"dataset": args.dataset, "classifier": "resmlp", "seed": args.seed,
             "outer_fold": fold, "variant": v, "macro_f1": r["test"]["macro_f1"],
             "accuracy": r["test"]["accuracy"], "train_macro_f1": r["train"]["macro_f1"],
             "train_accuracy": r["train"]["accuracy"], "dimensions": r["dimensions"],
             "parameters": r["parameters"]} for v, r in variants.items()]
    path = output / "capacity_rows.csv"
    pd.DataFrame(flat).to_csv(path, mode="a", header=not path.exists(), index=False)
    print(f"{args.dataset} {tag}: " + " | ".join(
        f"{v} {r['test']['macro_f1']:.4f} (train {r['train']['accuracy']:.3f})"
        for v, r in variants.items()) + f"  ({record['duration_seconds']:.0f}s)")


if __name__ == "__main__":
    main()
