"""
09_mlp_head.py
==============
Compara SVM lineal (baseline) vs MLP head como clasificador sobre los embeddings concatenados.

Configuración del MLP (intencionalmente minimal):
  - 1 hidden layer, 256 unidades
  - activation=relu, dropout 0.5 (via alpha L2)
  - solver=adam, lr=1e-3 (default)
  - early_stopping=True, validation_fraction=0.15
  - max_iter=300

Compara:
  1. Linear SVM (baseline, lo que hemos usado)
  2. MLP 256 (1 hidden layer)
  3. MLP 512 (más capacidad, riesgo overfit)

Sobre:
  - GFS optimal subset por dataset (el que ganó la comparación previa)
  - Full concat (k=13, todos los extractores)
  - DINOv2-large solo (referencia)

Output: results/tables/mlp_{dataset}.csv + results/tables/mlp_summary.csv
"""

import argparse
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

warnings.filterwarnings("ignore")

EMBEDDINGS_ROOT = Path("embeddings")
RESULTS_DIR = Path("results")
TABLES_DIR = RESULTS_DIR / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

CV_SPLITS = 5
CV_SEED = 42

# Subsets óptimos GFS (de greedy_summary.csv)
GFS_SUBSETS = {
    "DTD": ["dinov2", "resnet50", "dinov2_large", "glcm"],
    "FMD": ["dinov2", "dinov2_large"],
    "KTH-TIPS2": ["dinov2", "swin_t", "dinov2_large"],
    "HVD_glaucoma": ["swin_t", "deit_s", "convnext_v2_t", "vit_b16", "resnet50", "gabor", "glcm"],
    "ocular_toxoplasmosis": ["swin_t", "dinov2_large", "efficientnet_b0", "deit_s"],
}

ALL_EXTRACTORS = [
    "vit_b16", "swin_t", "deit_s", "dinov2", "dinov2_large",
    "resnet50", "convnext_v2_t", "efficientnet_b0",
    "lbp", "glcm", "gabor", "hog", "drlbp",
]

CLASSIFIERS = {
    "svm_linear": lambda: SVC(kernel="linear", C=1.0, random_state=CV_SEED),
    "mlp_256": lambda: MLPClassifier(
        hidden_layer_sizes=(256,),
        activation="relu",
        solver="adam",
        alpha=0.01,             # L2 regularization
        learning_rate_init=1e-3,
        max_iter=300,
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=20,
        random_state=CV_SEED,
    ),
    "mlp_512": lambda: MLPClassifier(
        hidden_layer_sizes=(512,),
        activation="relu",
        solver="adam",
        alpha=0.01,
        learning_rate_init=1e-3,
        max_iter=300,
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=20,
        random_state=CV_SEED,
    ),
}


def load_embeddings(dataset, extractor):
    base = EMBEDDINGS_ROOT / dataset
    emb = np.load(base / f"{extractor}.npy")
    labels = np.load(base / f"{extractor}_labels.npy")
    return emb, labels


def normalize_l2(X):
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return X / norms


def evaluate(emb_list, labels, clf_factory):
    le = LabelEncoder()
    y = le.fit_transform(labels)
    skf = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_SEED)
    f1s, accs = [], []
    for tr_idx, te_idx in skf.split(emb_list[0], y):
        X_tr = np.concatenate([normalize_l2(e[tr_idx]) for e in emb_list], axis=1)
        X_te = np.concatenate([normalize_l2(e[te_idx]) for e in emb_list], axis=1)
        y_tr, y_te = y[tr_idx], y[te_idx]
        clf = clf_factory()
        clf.fit(X_tr, y_tr)
        y_pred = clf.predict(X_te)
        f1s.append(f1_score(y_te, y_pred, average="macro"))
        accs.append(accuracy_score(y_te, y_pred))
    return {
        "mean_f1": float(np.mean(f1s)),
        "std_f1": float(np.std(f1s)),
        "mean_acc": float(np.mean(accs)),
        "std_acc": float(np.std(accs)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=list(GFS_SUBSETS.keys()))
    args = parser.parse_args()

    print(f"Comparando SVM vs MLP en 5 datasets, 3 subsets por dataset.\n")
    all_results = []

    for dataset in args.datasets:
        print(f"=== {dataset} ===")
        # Cargar embeddings disponibles
        emb_cache = {}
        for ext in ALL_EXTRACTORS:
            try:
                emb, lab = load_embeddings(dataset, ext)
                emb_cache[ext] = emb
            except FileNotFoundError:
                pass
        if not emb_cache:
            print(f"  [SKIP] sin embeddings\n")
            continue
        labels = lab

        # Tres subsets: GFS, full concat, single
        subsets = {
            "gfs_subset": GFS_SUBSETS[dataset],
            "full_concat": ALL_EXTRACTORS,
            "single_best": ["dinov2_large"] if "dinov2_large" in emb_cache else ["dinov2"],
        }

        ds_results = []
        for subset_name, ext_list in subsets.items():
            try:
                emb_list = [emb_cache[e] for e in ext_list]
            except KeyError as e:
                continue
            dim = sum(e.shape[1] for e in emb_list)

            for clf_name, clf_factory in CLASSIFIERS.items():
                t0 = time.time()
                try:
                    r = evaluate(emb_list, labels, clf_factory)
                except Exception as ex:
                    print(f"    [ERROR] {subset_name} + {clf_name}: {ex}")
                    continue
                elapsed = time.time() - t0
                row = {
                    "dataset": dataset,
                    "subset": subset_name,
                    "n_extractors": len(ext_list),
                    "dim": dim,
                    "clf": clf_name,
                    "f1": r["mean_f1"],
                    "std_f1": r["std_f1"],
                    "acc": r["mean_acc"],
                    "std_acc": r["std_acc"],
                    "time_s": round(elapsed, 1),
                }
                ds_results.append(row)
                all_results.append(row)
                print(f"  {subset_name:12s} (n={len(ext_list):2d}, dim={dim:5d})  {clf_name:10s}  f1={r['mean_f1']:.3f}±{r['std_f1']:.3f}  ({elapsed:.1f}s)", flush=True)
        print()
        if ds_results:
            pd.DataFrame(ds_results).to_csv(TABLES_DIR / f"mlp_{dataset}.csv", index=False)

    if all_results:
        pd.DataFrame(all_results).to_csv(TABLES_DIR / "mlp_summary.csv", index=False)
        print("=== Summary: results/tables/mlp_summary.csv ===\n")
        df = pd.DataFrame(all_results)
        # Pivot: subset × clf para cada dataset
        for ds in args.datasets:
            sub = df[df.dataset == ds]
            if sub.empty: continue
            print(f"\n{ds}:")
            pivot = sub.pivot_table(index="subset", columns="clf", values="f1")
            print(pivot.round(3).to_string())
        # Δ MLP vs SVM
        print("\n=== Δ MLP vs SVM (por subset) ===")
        deltas = []
        for ds in args.datasets:
            for subset in ["gfs_subset", "full_concat", "single_best"]:
                sub = df[(df.dataset == ds) & (df.subset == subset)]
                if len(sub) < 2: continue
                svm = sub[sub.clf == "svm_linear"]["f1"].values
                mlp256 = sub[sub.clf == "mlp_256"]["f1"].values
                mlp512 = sub[sub.clf == "mlp_512"]["f1"].values
                if len(svm) and len(mlp256):
                    deltas.append({
                        "dataset": ds, "subset": subset,
                        "svm": float(svm[0]),
                        "mlp_256": float(mlp256[0]),
                        "delta_256": float(mlp256[0]) - float(svm[0]),
                        "mlp_512": float(mlp512[0]) if len(mlp512) else None,
                        "delta_512": (float(mlp512[0]) - float(svm[0])) if len(mlp512) else None,
                    })
        if deltas:
            print(pd.DataFrame(deltas).to_string(index=False))


if __name__ == "__main__":
    main()
