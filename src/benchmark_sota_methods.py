#!/usr/bin/env python3
"""Accuracy and training/prediction time of the literature methods on one dataset.

Scabini et al. (J. Imaging 2025) and Neshov et al. (Electronics 2025) run on
the protocol both papers state for each dataset, from the features that
``time_extraction.py`` extracted and timed on the same machine:

``DTD``        the ten official splits; train and validation fit the model,
               with the byte-identical copies of test images removed as in the
               thesis, and test is held out.  Neshov et al. use the splits "as
               provided" without saying what the validation part is for, so
               their MLP is also fitted on train alone (``neshov_train``);
``FMD``        ten repetitions of stratified 10-fold cross-validation;
               repetition r is seeded with 42 r, as Neshov et al. describe
               (Scabini et al. state the protocol without its seeds);
``KTHTIPS2b``  the four RADAM splits (``benchmark_kth_methods.py`` also runs
               the thesis methods on them);
``Outex13Official1360``  the official 680/680 split (Scabini et al. only).

``scabini``  BEiTv2-B/16 ImageNet-21k features, raw, classified by untuned
             scikit-learn KNN (k=1), LDA (lsqr, automatic shrinkage) and linear
             SVM (C=1); the paper reports the mean accuracy of the three;
``neshov``   raw BEiTv2 features of layers 2, 5, 8 and 11, MLP
             64-BN-ReLU-Dropout(0.2), Adam, batch 32, 100 epochs.

Classical classifiers run on one CPU thread; the MLP runs on the GPU.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC

SRC = Path(__file__).resolve().parent
REPO = SRC.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from benchmark_kth_methods import neshov, scores, timed_fit_predict  # noqa: E402
from run_topk_individual_control import outer_indices  # noqa: E402
from time_extraction import DATASETS  # noqa: E402

# name: (official split numbers or None for FMD's cross-validation, invert)
PROTOCOL = {"DTD": (range(1, 11), False), "FMD": (None, False),
            "KTHTIPS2b": (range(1, 5), True), "Outex13Official1360": ([1], False)}
NESHOV_DATASETS = {"DTD", "FMD", "KTHTIPS2b"}


def scabini_models():
    return (("knn", KNeighborsClassifier(n_neighbors=1)),
            ("lda", LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")),
            ("svm", SVC(kernel="linear", C=1.0)))


def features(embeddings: Path, name: str) -> np.ndarray:
    for base in (embeddings, embeddings.with_name(embeddings.name + "_sota")):
        if (base / f"{name}.npy").exists():
            return np.load(base / f"{name}.npy").astype(np.float32)
    raise FileNotFoundError(f"{name}.npy not under {embeddings}; run time_extraction.py first")


def partitions(dataset, rows, y):
    """(label, train, test, seed, train-role rows) for each evaluation of the protocol."""
    splits, invert = PROTOCOL[dataset]
    if splits is None:
        for rep in range(1, 11):
            folds = StratifiedKFold(n_splits=10, shuffle=True, random_state=42 * rep)
            for fold, (train, test) in enumerate(folds.split(np.zeros(len(y)), y), 1):
                yield f"r{rep}f{fold}", train, test, 42 * rep, None
        return
    groups = np.asarray([r["group"] for r in rows])
    for split in splits:
        train, test = outer_indices(dataset, 42, 0, y, groups, rows, split, None, invert)
        if set(groups[train]).intersection(groups[test]):
            raise AssertionError("outer group leakage")
        column = f"split_{split}" if f"split_{split}" in rows[0] else "official_split"
        roles = np.asarray([rows[i][column] for i in train])
        yield str(split), train, test, 42, train[roles == "train"] if "val" in roles else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", choices=PROTOCOL, required=True)
    parser.add_argument("--output", type=Path, help="default: results/exploratory/sota_timing/<dataset>")
    args = parser.parse_args()
    manifest, embeddings, slug = DATASETS[args.dataset]
    output = args.output or REPO / "results/exploratory/sota_timing" / slug

    with (REPO / manifest).open(newline="", encoding="utf-8") as f:
        rows = sorted(csv.DictReader(f), key=lambda r: int(r["row_id"]))
    _, y = np.unique([r["label"] for r in rows], return_inverse=True)
    x_scabini = features(REPO / embeddings, "beitv2_scabini")
    x_neshov = (features(REPO / embeddings, "beitv2_base_multilayer")
                if args.dataset in NESHOV_DATASETS else None)
    records = []

    def add(split, method, classifier, train, test, pred, fit_s, predict_s, block, dims):
        records.append({"split": split, "method": method, "classifier": classifier, "blocks": block,
                        **scores(y[test], pred), "selection_seconds": 0.0, "fit_seconds": fit_s,
                        "train_seconds": fit_s, "predict_seconds": predict_s, "models": 1,
                        "dimensions": dims, "n_train": len(train), "n_test": len(test)})
        r = records[-1]
        print(f"{split:<6} {method:<13} {classifier:<4} acc {r['accuracy']:.4f} "
              f"entrenar {fit_s:7.2f} s  predecir {predict_s:.3f} s", flush=True)

    for split, train, test, seed, train_only in partitions(args.dataset, rows, y):
        for clf, model in scabini_models():
            _, pred, fit_s, pred_s = timed_fit_predict(model, x_scabini[train], y[train],
                                                       x_scabini[test])
            add(split, "scabini", clf, train, test, pred, fit_s, pred_s, "beitv2_scabini",
                x_scabini.shape[1])
        if x_neshov is None:
            continue
        pred, fit_s, pred_s = neshov(x_neshov, y, train, test, seed)
        add(split, "neshov", "mlp", train, test, pred, fit_s, pred_s, "beitv2_base_multilayer",
            x_neshov.shape[1])
        if train_only is not None:
            pred, fit_s, pred_s = neshov(x_neshov, y, train_only, test, seed)
            add(split, "neshov_train", "mlp", train_only, test, pred, fit_s, pred_s,
                "beitv2_base_multilayer", x_neshov.shape[1])

    output.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(records)
    frame.to_csv(output / "sota_runs.csv", index=False)
    summary = frame.groupby(["method", "classifier"], sort=False).agg(
        accuracy=("accuracy", "mean"), accuracy_sd=("accuracy", "std"),
        macro_f1=("macro_f1", "mean"), fit_seconds=("fit_seconds", "mean"),
        predict_seconds=("predict_seconds", "mean"), runs=("split", "count")).reset_index()
    print(summary.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
