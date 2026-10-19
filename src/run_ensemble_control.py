#!/usr/bin/env python3
"""Is the gain of the sampling ensembles about the subsets or about voting?

The rank lottery and the diversity sampling combine 15 classifiers, each trained
on a different 4-block subset.  Any ensemble of 15 classifiers can beat a single
one simply by averaging out its errors, so the comparison with Top-4 alone does
not show that drawing different subsets matters.  This control keeps the subset
fixed at Top-4 and varies everything else:

``seed_ensemble``     15 models on the same rows and blocks, differing only in
                      the random seed (for ResMLP, initialisation and batch
                      order; a linear SVM is close to deterministic, so for it
                      this ensemble is expected to collapse to Top-4);
``bagging_ensemble``  15 models on the same blocks, each trained on a
                      class-stratified bootstrap resample of the training rows,
                      which is the classical way to decorrelate members.

If the sampling ensembles beat both, the subsets carry the gain.  The members
are combined exactly as in the sampling ensembles: standardised decision values
(log-probabilities for ResMLP) averaged across members.
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
    audit_gate, load_dataset, load_manifest, make_model, manifest_groups,
)
from run_topk_individual_control import outer_indices  # noqa: E402
from singleton_ranking import condition_key, ranked_singletons  # noqa: E402

REPO = SRC.parent


def metrics(y_true, y_pred, labels) -> dict:
    return {"macro_f1": float(f1_score(y_true, y_pred, labels=labels,
                                       average="macro", zero_division=0)),
            "accuracy": float(accuracy_score(y_true, y_pred))}


def decision_scores(model, x) -> np.ndarray:
    if hasattr(model, "decision_function"):
        scores = np.asarray(model.decision_function(x))
    else:
        scores = np.log(np.clip(np.asarray(model.predict_proba(x)), 1e-12, None))
    if scores.ndim == 1:
        scores = np.column_stack([-scores, scores])
    sd = scores.std()
    return scores / sd if sd > 0 else scores


def stratified_bootstrap(train: np.ndarray, y: np.ndarray, rng) -> np.ndarray:
    """Resample with replacement inside each class, keeping its count."""
    parts = []
    for c in np.unique(y[train]):
        members = train[y[train] == c]
        parts.append(rng.choice(members, size=len(members), replace=True))
    return np.concatenate(parts)


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
    parser.add_argument("--members", type=int, default=15)
    parser.add_argument("--n-jobs", type=int, default=6)
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

    jobs = args.n_jobs if args.classifier == "svm" else 1
    singles = ranked_singletons(cache, train, y, inner_groups, args.classifier,
                                args.seed, condition_key(args), n_jobs=jobs)
    order = [n for n, _ in sorted(singles.items(), key=lambda kv: (-kv[1], kv[0]))]
    subset = order[:args.k]
    x = np.concatenate([cache[b] for b in subset], axis=1)
    labels, y_test = np.unique(y), y[test]

    def member(rows_idx, seed):
        model = make_model(args.classifier, seed)
        model.fit(x[rows_idx], y[rows_idx])
        if not np.array_equal(np.asarray(model.classes_), labels):
            raise RuntimeError("member did not see every class")
        return np.asarray(model.predict(x[test])), decision_scores(model, x[test])

    single_pred, _ = member(train, args.seed)
    rng = np.random.default_rng(args.seed * 1000 + fold)
    boots = [stratified_bootstrap(train, y, rng) for _ in range(args.members)]
    plans = {"seed_ensemble": [(train, args.seed + 1 + m) for m in range(args.members)],
             "bagging_ensemble": [(b, args.seed) for b in boots]}

    record = {"dataset": args.dataset, "classifier": args.classifier, "seed": args.seed,
              "outer_fold": fold, "k": args.k, "members": args.members,
              "subset": subset, "inner_group_column": args.inner_group_column or "group",
              "top4_single": metrics(y_test, single_pred, labels), "variants": {}}
    flat = [{"dataset": args.dataset, "classifier": args.classifier, "seed": args.seed,
             "outer_fold": fold, "variant": "top4_single", **record["top4_single"]}]
    for name, plan in plans.items():
        results = Parallel(n_jobs=jobs, prefer="threads")(
            delayed(member)(r, s) for r, s in plan)
        soft = np.mean([s for _, s in results], axis=0)
        pred = labels[np.argmax(soft, axis=1)]
        met = metrics(y_test, pred, labels)
        agree = float(np.mean([np.mean(p == single_pred) for p, _ in results]))
        record["variants"][name] = {**met, "mean_agreement_with_single": agree}
        flat.append({"dataset": args.dataset, "classifier": args.classifier,
                     "seed": args.seed, "outer_fold": fold, "variant": name, **met})
    record["duration_seconds"] = time.perf_counter() - started

    output.mkdir(parents=True, exist_ok=True)
    tag = (f"official{args.official_split}" + ("_inverted" if args.invert_official_split else "")
           if args.official_split is not None else args.curet_direction or f"f{args.fold}")
    stem = f"{args.dataset}_{args.classifier}_s{args.seed}_{tag}_control"
    (output / f"{stem}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    path = output / "control_rows.csv"
    pd.DataFrame(flat).to_csv(path, mode="a", header=not path.exists(), index=False)
    print(f"{args.dataset} {args.classifier} {tag}: Top-4 {record['top4_single']['macro_f1']:.4f} | "
          + " | ".join(f"{n} {v['macro_f1']:.4f}" for n, v in record["variants"].items())
          + f"  ({record['duration_seconds']:.0f}s)")


if __name__ == "__main__":
    main()
