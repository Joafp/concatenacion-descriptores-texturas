#!/usr/bin/env python3
"""Accuracy and training/prediction time of literature methods and ours on KTH-TIPS2-b.

Every method runs on the four RADAM splits (three physical samples train, one
tests) on the same machine, from features extracted by ``time_extraction.py``.
The extraction time per descriptor comes from that script; this one times what
happens after it.

``scabini``       Scabini et al. (J. Imaging 2025): BEiTv2-B/16 ImageNet-21k
                  features, raw, classified by untuned scikit-learn KNN (k=1),
                  LDA (lsqr, automatic shrinkage) and linear SVM (C=1); the
                  paper reports the mean accuracy of the three.
``neshov``        Neshov et al. (Electronics 2025) as transcribed in
                  ``replicate_electronics_beitv2_kth.py``: raw BEiTv2 features of
                  layers 2, 5, 8 and 11, MLP 64-BN-ReLU-Dropout(0.2), Adam,
                  batch 32, 100 epochs.
``top4``          the four best blocks of the inner ranking (thesis loader,
                  L2-normalised blocks); training includes ranking all 21 blocks.
``diversidad``    15 draws with lambda 0.25 and beta 8; training includes the
                  ranking, the CKA between blocks and one model per distinct
                  subset.
``completa22``    the 21 blocks and the RGB N-gram colour block, whose SVD is
                  fitted on the training rows of each split.

Classical classifiers run on one CPU thread; the MLPs run on the GPU.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np
import pandas as pd
import torch
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import accuracy_score, f1_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

SRC = Path(__file__).resolve().parent
REPO = SRC.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analyze_block_redundancy import linear_cka  # noqa: E402
from replicate_electronics_beitv2_kth import PaperMLP  # noqa: E402
from rgb_ngram_descriptor import RGBNgramSVDBlock, build_count_cache  # noqa: E402
from run_confirmatory_nested import (  # noqa: E402
    audit_gate, load_dataset, load_manifest, make_model, manifest_groups,
)
from run_diversity_lottery import draw_subset  # noqa: E402
from run_topk_individual_control import outer_indices  # noqa: E402
from run_weighted_lottery_selection import decision_scores  # noqa: E402
from singleton_ranking import ranked_singletons  # noqa: E402

DATASET = "KTHTIPS2b"
AUDIT = REPO / "results/extensions/kth_tips2b"
RAW = REPO / "embeddings_extensions/KTH-TIPS2-b"
LAMBDA, BETA, DRAWS, K = 0.25, 8.0, 15, 4


def scores(y_true, y_pred):
    return {"accuracy": float(accuracy_score(y_true, y_pred)),
            "macro_f1": float(f1_score(y_true, y_pred, average="macro"))}


def timed_fit_predict(model, x_train, y_train, x_test):
    t0 = time.perf_counter()
    model.fit(x_train, y_train)
    fit_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    pred = np.asarray(model.predict(x_test))
    return model, pred, fit_s, time.perf_counter() - t0


def sync():
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def neshov(x, y, train, test, seed=42):
    """Training loop of replicate_electronics_beitv2_kth.py, timed."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(seed)
    np.random.seed(seed)
    sync()
    t0 = time.perf_counter()
    loader = DataLoader(TensorDataset(torch.from_numpy(x[train]), torch.from_numpy(y[train]).long()),
                        batch_size=32, shuffle=True,
                        generator=torch.Generator().manual_seed(seed), num_workers=0)
    model = PaperMLP(x.shape[1], len(np.unique(y))).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, betas=(.9, .999), weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss()
    model.train()
    for _ in range(100):
        for bx, by in loader:
            optimizer.zero_grad(set_to_none=True)
            loss_fn(model(bx.to(device)), by.to(device)).backward()
            optimizer.step()
    sync()
    fit_s = time.perf_counter() - t0
    model.eval()
    t0 = time.perf_counter()
    with torch.inference_mode():
        pred = model(torch.from_numpy(x[test]).to(device)).argmax(dim=1).cpu().numpy()
    sync()
    return pred, fit_s, time.perf_counter() - t0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--splits", type=int, nargs="+", default=[1, 2, 3, 4])
    parser.add_argument("--scabini-features", type=Path,
                        default=REPO / "embeddings_extensions/KTH-TIPS2-b_sota/beitv2_scabini.npy")
    parser.add_argument("--output", type=Path, default=REPO / "results/exploratory/sota_timing/kth")
    args = parser.parse_args()

    audit_gate(AUDIT, DATASET)
    cache, y = load_dataset(REPO, DATASET, embedding_root=REPO / "embeddings_extensions")
    cache.pop("beitv2_base_multilayer", None)
    groups, rows = load_manifest(AUDIT, DATASET, y)
    inner_groups = manifest_groups(rows, "sample")
    names = sorted(cache)
    if len(names) != 21:
        raise AssertionError(f"expected the 21 stored blocks, found {len(names)}")
    x_scabini = np.load(args.scabini_features).astype(np.float32)
    x_neshov = np.load(RAW / "beitv2_base_multilayer.npy").astype(np.float32)
    counts = build_count_cache(rows, REPO, AUDIT / "rgb_ngram_count_cache" / DATASET / "rgb_ngram_impl1")
    labels = np.unique(y)
    records = []

    for split in args.splits:
        train, test = outer_indices(DATASET, 42, 0, y, groups, rows, split, None, True)
        if set(groups[train]).intersection(groups[test]):
            raise AssertionError("outer group leakage")
        y_tr, y_te = y[train], y[test]

        def add(method, classifier, pred, fit_s, predict_s, selection_s=0.0, models=1, dims=0,
                blocks=()):
            # blocks: the descriptors the trained method extracts from a new image.
            records.append({"split": split, "method": method, "classifier": classifier,
                            "blocks": "+".join(sorted(blocks)),
                            **scores(y_te, pred), "selection_seconds": selection_s,
                            "fit_seconds": fit_s, "train_seconds": selection_s + fit_s,
                            "predict_seconds": predict_s, "models": models, "dimensions": dims})
            r = records[-1]
            print(f"split {split} {method:<11} {classifier:<6} acc {r['accuracy']:.4f} "
                  f"entrenar {r['train_seconds']:8.1f} s  predecir {predict_s:.3f} s", flush=True)

        # Scabini: three untuned classifiers on raw ImageNet-21k BEiTv2 features.
        preds = {}
        for clf, model in (("knn", KNeighborsClassifier(n_neighbors=1)),
                           ("lda", LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")),
                           ("svm", SVC(kernel="linear", C=1.0))):
            _, pred, fit_s, pred_s = timed_fit_predict(model, x_scabini[train], y_tr, x_scabini[test])
            preds[clf] = (pred, fit_s, pred_s)
            add("scabini", clf, pred, fit_s, pred_s, dims=x_scabini.shape[1],
                blocks=["beitv2_scabini"])

        pred, fit_s, pred_s = neshov(x_neshov, y, train, test)
        add("neshov", "mlp", pred, fit_s, pred_s, dims=x_neshov.shape[1],
            blocks=["beitv2_base_multilayer"])

        # Our methods: the ranking is recomputed, not read from the cache.
        for clf in ("svm", "resmlp"):
            with tempfile.TemporaryDirectory() as tmp:
                sync()
                t0 = time.perf_counter()
                singles = ranked_singletons(cache, train, y, inner_groups, clf, 42,
                                            f"bench_{clf}_{split}", n_jobs=1, cache_dir=Path(tmp))
                sync()
                ranking_s = time.perf_counter() - t0
            order = [n for n, _ in sorted(singles.items(), key=lambda kv: (-kv[1], kv[0]))]

            def fit_subset(subset):
                x = np.concatenate([cache[b] for b in subset], axis=1)
                sync()
                model, pred, fit_s, pred_s = timed_fit_predict(make_model(clf, 42), x[train], y_tr,
                                                               x[test])
                sync()
                return model, x, pred, fit_s, pred_s

            _, x4, pred, fit_s, pred_s = fit_subset(order[:K])
            add("top4", clf, pred, fit_s, pred_s, ranking_s, dims=x4.shape[1], blocks=order[:K])

            t0 = time.perf_counter()
            mats = {n: cache[n][train].astype(np.float64) for n in names}
            cka = {}
            for i, a in enumerate(names):
                for b in names[i + 1:]:
                    cka[(a, b)] = cka[(b, a)] = linear_cka(mats[a], mats[b])
            del mats
            cka_s = time.perf_counter() - t0
            lo, hi = min(singles.values()), max(singles.values())
            relevance = {n: (v - lo) / ((hi - lo) or 1.0) for n, v in singles.items()}
            rng = np.random.default_rng(42 * 1000 + (split - 1) * 10 + int(LAMBDA * 7) + int(BETA))
            subsets = [draw_subset(names, relevance, cka, LAMBDA, BETA, K, rng) for _ in range(DRAWS)]
            fit_total = pred_total = 0.0
            member = {}
            for subset in sorted({tuple(s) for s in subsets}):
                model, x, _, fit_s, _ = fit_subset(list(subset))
                t0 = time.perf_counter()
                member[subset] = decision_scores(model, x[test])
                pred_total += time.perf_counter() - t0
                fit_total += fit_s
            t0 = time.perf_counter()
            soft = np.mean([member[tuple(s)] for s in subsets], axis=0)
            pred = labels[np.argmax(soft, axis=1)]
            pred_total += time.perf_counter() - t0
            union = {b for s in subsets for b in s}
            add("diversidad", clf, pred, fit_total, pred_total, ranking_s + cka_s,
                models=len(member), dims=int(sum(cache[b].shape[1] for b in union)), blocks=union)

            # Completa-22: the colour block's SVD is part of training.
            block = RGBNgramSVDBlock(counts)
            t0 = time.perf_counter()
            ng_train, ng_test, _ = block.transform(train, test)
            svd_s = time.perf_counter() - t0
            x_tr = np.concatenate([cache[n][train] for n in names] + [ng_train], axis=1)
            x_te = np.concatenate([cache[n][test] for n in names] + [ng_test], axis=1)
            sync()
            _, pred, fit_s, pred_s = timed_fit_predict(make_model(clf, 42), x_tr, y_tr, x_te)
            sync()
            add("completa22", clf, pred, svd_s + fit_s, pred_s, dims=x_tr.shape[1],
                blocks=names + ["rgb_ngram_counts"])

    args.output.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(records)
    frame.to_csv(args.output / "method_runs.csv", index=False)
    summary = frame.groupby(["method", "classifier"]).agg(
        accuracy=("accuracy", "mean"), macro_f1=("macro_f1", "mean"),
        train_seconds=("train_seconds", "sum"), predict_seconds=("predict_seconds", "sum"),
        models=("models", "mean"), dimensions=("dimensions", "mean")).reset_index()
    summary.to_csv(args.output / "method_summary.csv", index=False)
    print(summary.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
