#!/usr/bin/env python3
"""Accuracy and training/prediction time of the thesis methods outside KTH-TIPS2-b.

Top-4, the diversity ensemble and Completa-22 (``benchmark_kth_methods.ours``)
run on the external conditions of the k=4 study, which are the protocol of the
thesis and not always the one of the papers:

``DTD``  the ten official splits, train and validation fitting the model with
         the byte-identical copies of test images removed (as the papers);
``FMD``  the five folds of StratifiedGroupKFold with seed 42 (the papers use
         ten repetitions of stratified 10-fold cross-validation);
``Outex13Official1360``  the official 680/680 split.

The 21 blocks come from the stored embeddings, which ``time_extraction.py``
checks and times; the colour block from the RGB N-gram counts that it extracts
and saves in ``<embedding dir>_sota/rgb_ngram_counts``.  Each split and
classifier is appended to ``our_runs.csv`` when it finishes, and a rerun skips
the ones already there.  Classical classifiers run on one CPU thread; the MLPs
run on the GPU.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parent
REPO = SRC.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from benchmark_kth_methods import ours, scores  # noqa: E402
from run_confirmatory_nested import audit_gate, load_dataset, load_manifest  # noqa: E402
from run_topk_individual_control import outer_indices  # noqa: E402
from time_extraction import DATASETS  # noqa: E402

# name: (audit and manifest root, official split numbers or None for five folds)
PROTOCOL = {"DTD": ("results/confirmatory", range(1, 11)),
            "FMD": ("results/confirmatory", None),
            "Outex13Official1360": ("results/extensions/outex13_official1360", [1])}
SEED = 42


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", choices=PROTOCOL, required=True)
    parser.add_argument("--classifiers", nargs="+", choices=("svm", "resmlp"),
                        default=["svm", "resmlp"])
    parser.add_argument("--output", type=Path, help="default: results/exploratory/sota_timing/<dataset>")
    args = parser.parse_args()
    audit_root, official = PROTOCOL[args.dataset]
    _, embeddings, slug = DATASETS[args.dataset]
    output = args.output or REPO / "results/exploratory/sota_timing" / slug
    out_csv = output / "our_runs.csv"

    audit_gate(REPO / audit_root, args.dataset)
    embedding_dir = REPO / embeddings
    cache, y = load_dataset(REPO, args.dataset, embedding_root=embedding_dir.parent)
    cache.pop("beitv2_base_multilayer", None)
    if len(cache) != 21:
        raise AssertionError(f"expected the 21 stored blocks, found {len(cache)}")
    groups, rows = load_manifest(REPO / audit_root, args.dataset, y)
    count_dir = embedding_dir.with_name(embedding_dir.name + "_sota") / "rgb_ngram_counts"
    counts = {n: np.load(count_dir / f"{n}.npy", mmap_mode="r") for n in ("keys", "counts", "indptr")}
    if len(counts["indptr"]) != len(y) + 1:
        raise AssertionError("RGB N-gram counts do not cover the manifest")
    done = (set(map(tuple, pd.read_csv(out_csv, dtype={"split": str})[["split", "classifier"]]
                    .values)) if out_csv.exists() else set())

    conditions = ([(str(s), s - 1, s) for s in official] if official is not None
                  else [(f"s{SEED}f{f}", f, None) for f in range(5)])
    for label, fold, split in conditions:
        train, test = outer_indices(args.dataset, SEED, fold, y, groups, rows, split)
        if set(groups[train]).intersection(groups[test]):
            raise AssertionError("outer group leakage")
        for clf in args.classifiers:
            if (label, clf) in done:
                print(f"split {label} {clf}: ya está en {out_csv.name}", flush=True)
                continue
            records = []

            def add(method, classifier, pred, fit_s, predict_s, selection_s=0.0, models=1,
                    dims=0, blocks=()):
                # blocks: the descriptors the trained method extracts from a new image.
                records.append({"split": label, "method": method, "classifier": classifier,
                                "blocks": "+".join(sorted(blocks)), **scores(y[test], pred),
                                "selection_seconds": selection_s, "fit_seconds": fit_s,
                                "train_seconds": selection_s + fit_s,
                                "predict_seconds": predict_s, "models": models,
                                "dimensions": dims, "n_train": len(train), "n_test": len(test)})
                r = records[-1]
                print(f"split {label} {method:<11} {classifier:<6} acc {r['accuracy']:.4f} "
                      f"f1 {r['macro_f1']:.4f}  entrenar {r['train_seconds']:8.1f} s  "
                      f"predecir {predict_s:.3f} s", flush=True)

            # The thesis groups its inner folds by the manifest group, as the outer split.
            ours(cache, y, train, test, groups, counts, fold, clf, add, SEED)
            output.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(records).to_csv(out_csv, mode="a", header=not out_csv.exists(),
                                         index=False)

    frame = pd.read_csv(out_csv, dtype={"split": str})
    summary = frame.groupby(["method", "classifier"]).agg(
        runs=("split", "nunique"), accuracy=("accuracy", "mean"), macro_f1=("macro_f1", "mean"),
        train_seconds=("train_seconds", "mean"), predict_seconds=("predict_seconds", "mean"))
    print(summary.round(4).to_string())


if __name__ == "__main__":
    main()
