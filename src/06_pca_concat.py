"""
06_pca_concat.py
================
Aplica PCA a cada embedding antes de concatenar, y compara con concat crudo.

Hipótesis: los embeddings tienen dim redundante. PCA quita ruido y
mantiene el 95% de la varianza con menos dims.

Para cada (dataset, clf), evalúa:
  1. Concat crudo (línea base, ya en concat_summary.csv)
  2. Concat con PCA(k=100) por extractor
  3. Concat con PCA(k=200) por extractor
  4. Concat con PCA(k=500) por extractor

Output: results/tables/pca_{dataset}.csv + results/tables/pca_summary.csv
"""

import argparse
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

warnings.filterwarnings("ignore")

EMBEDDINGS_ROOT = Path("embeddings")
RESULTS_DIR = Path("results")
TABLES_DIR = RESULTS_DIR / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = ["DTD", "FMD", "KTH-TIPS2", "HVD_glaucoma", "ocular_toxoplasmosis"]
ALL_EXTRACTORS = [
    "vit_b16", "swin_t", "deit_s", "dinov2",
    "resnet50", "convnext_v2_t", "efficientnet_b0",
    "lbp", "glcm", "gabor", "hog", "drlbp",
]

CLF_PARAMS = {
    "svm": {"kernel": "linear", "C": 1.0},
    "knn": {"n_neighbors": 5, "weights": "distance"},
    "rf": {"n_estimators": 300, "max_depth": None},
}

PCA_LEVELS = [100, 200, 500]
CV_SPLITS = 5
CV_SEED = 42


def load_embeddings(dataset, extractor):
    base = EMBEDDINGS_ROOT / dataset
    emb = np.load(base / f"{extractor}.npy")
    labels = np.load(base / f"{extractor}_labels.npy")
    return emb, labels


def normalize_l2(X):
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return X / norms


def make_clf(name):
    if name == "svm":
        return SVC(**CLF_PARAMS["svm"])
    if name == "knn":
        return KNeighborsClassifier(**CLF_PARAMS["knn"])
    if name == "rf":
        return RandomForestClassifier(random_state=CV_SEED, n_jobs=-1, **CLF_PARAMS["rf"])
    raise ValueError(name)


def pca_reduce(X_train, X_test, n_components):
    """Ajusta PCA en train, transforma train y test."""
    n_components = min(n_components, X_train.shape[0] - 1, X_train.shape[1])
    pca = PCA(n_components=n_components, random_state=CV_SEED)
    pca.fit(X_train)
    return pca.transform(X_train), pca.transform(X_test)


def evaluate(emb_arrays, labels, clf_name, use_pca=None):
    """Evalúa concat con o sin PCA. use_pca=None significa sin PCA."""
    le = LabelEncoder()
    y = le.fit_transform(labels)
    skf = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_SEED)
    accs, f1s = [], []
    for tr_idx, te_idx in skf.split(emb_arrays[0], y):
        if use_pca is None:
            X_tr = np.concatenate([normalize_l2(e[tr_idx]) for e in emb_arrays], axis=1)
            X_te = np.concatenate([normalize_l2(e[te_idx]) for e in emb_arrays], axis=1)
        else:
            parts_tr, parts_te = [], []
            for e in emb_arrays:
                tr_p, te_p = pca_reduce(normalize_l2(e[tr_idx]), normalize_l2(e[te_idx]), use_pca)
                parts_tr.append(tr_p)
                parts_te.append(te_p)
            X_tr = np.concatenate(parts_tr, axis=1)
            X_te = np.concatenate(parts_te, axis=1)
        clf = make_clf(clf_name)
        clf.fit(X_tr, y[tr_idx])
        y_pred = clf.predict(X_te)
        accs.append(accuracy_score(y[te_idx], y_pred))
        f1s.append(f1_score(y[te_idx], y_pred, average="macro"))
    return {
        "mean_acc": float(np.mean(accs)),
        "std_acc": float(np.std(accs)),
        "mean_f1": float(np.mean(f1s)),
        "std_f1": float(np.std(f1s)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=DATASETS)
    parser.add_argument("--extractors", nargs="+", default=ALL_EXTRACTORS)
    parser.add_argument("--clfs", nargs="+", default=["svm"])
    parser.add_argument("--pca-levels", nargs="+", type=int, default=PCA_LEVELS)
    args = parser.parse_args()

    print(f"PCA concat: datasets={args.datasets}, pca_levels={args.pca_levels}, clfs={args.clfs}\n")

    all_results = []

    for dataset in args.datasets:
        print(f"=== Dataset: {dataset} ===")
        # Cargar embeddings
        emb_cache = {}
        for ext in args.extractors:
            try:
                emb, lab = load_embeddings(dataset, ext)
                emb_cache[ext] = emb
            except FileNotFoundError:
                pass
        if not emb_cache:
            print(f"  [SKIP] sin embeddings\n")
            continue
        labels = lab

        ds_results = []
        emb_arrays_full = [emb_cache[e] for e in args.extractors if e in emb_cache]

        for clf_name in args.clfs:
            # Baseline: concat crudo (k=12)
            t0 = time.time()
            r_raw = evaluate(emb_arrays_full, labels, clf_name, use_pca=None)
            elapsed = time.time() - t0
            dim_raw = sum(e.shape[1] for e in emb_arrays_full)
            row = {
                "dataset": dataset,
                "clf": clf_name,
                "pca": 0,
                "f1": r_raw["mean_f1"],
                "std_f1": r_raw["std_f1"],
                "acc": r_raw["mean_acc"],
                "dim": dim_raw,
                "time_s": round(elapsed, 1),
            }
            ds_results.append(row)
            all_results.append(row)
            print(f"  sin PCA (dim={dim_raw:5d})  f1={r_raw['mean_f1']:.3f}±{r_raw['std_f1']:.3f}  ({elapsed:.1f}s)", flush=True)

            for pca_n in args.pca_levels:
                t0 = time.time()
                r_pca = evaluate(emb_arrays_full, labels, clf_name, use_pca=pca_n)
                elapsed = time.time() - t0
                dim_pca = pca_n * len(emb_arrays_full)
                row = {
                    "dataset": dataset,
                    "clf": clf_name,
                    "pca": pca_n,
                    "f1": r_pca["mean_f1"],
                    "std_f1": r_pca["std_f1"],
                    "acc": r_pca["mean_acc"],
                    "dim": dim_pca,
                    "time_s": round(elapsed, 1),
                }
                ds_results.append(row)
                all_results.append(row)
                delta = r_pca["mean_f1"] - r_raw["mean_f1"]
                print(f"  PCA({pca_n:3d}) (dim={dim_pca:5d})  f1={r_pca['mean_f1']:.3f}±{r_pca['std_f1']:.3f}  Δ={delta:+.3f}  ({elapsed:.1f}s)", flush=True)
        print()
        if ds_results:
            pd.DataFrame(ds_results).to_csv(TABLES_DIR / f"pca_{dataset}.csv", index=False)

    if all_results:
        pd.DataFrame(all_results).to_csv(TABLES_DIR / "pca_summary.csv", index=False)
        print(f"=== Summary: results/tables/pca_summary.csv ===\n")
        # Pivot
        df = pd.DataFrame(all_results)
        pivot = df.pivot(index="dataset", columns="pca", values="f1")
        print("Mejor F1 por (dataset, nivel PCA):")
        print(pivot.round(3).to_string())


if __name__ == "__main__":
    main()
