"""
12_nested_cv.py
================
Implementa nested CV para GFS: outer 5-fold para evaluación final,
inner 5-fold para la búsqueda greedy. Compara con GFS naive (mismo
fold para selección y evaluación) para cuantificar el sesgo optimista.

Output: results/tables/nested_cv_{dataset}.csv + nested_cv_summary.csv
"""

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

warnings.filterwarnings("ignore")

EMBEDDINGS_ROOT = Path("embeddings")
RESULTS_DIR = Path("results")
TABLES_DIR = RESULTS_DIR / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

OUTER_SPLITS = 5
INNER_SPLITS = 5
SEED = 42

# GFS subsets (los que ganó la selección naive)
GFS_SUBSETS_NAIVE = {
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


def load_embeddings(dataset, extractor):
    base = EMBEDDINGS_ROOT / dataset
    emb = np.load(base / f"{extractor}.npy")
    labels = np.load(base / f"{extractor}_labels.npy")
    return emb, labels


def normalize_l2(X):
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return X / norms


def make_clf():
    return SVC(kernel="linear", C=1.0, random_state=SEED)


def evaluate_subset(emb_arrays_train, emb_arrays_test, y_train, y_test):
    X_tr = np.concatenate([normalize_l2(e) for e in emb_arrays_train], axis=1)
    X_te = np.concatenate([normalize_l2(e) for e in emb_arrays_test], axis=1)
    clf = make_clf()
    clf.fit(X_tr, y_train)
    y_pred = clf.predict(X_te)
    return f1_score(y_test, y_pred, average="macro"), accuracy_score(y_test, y_pred)


def gfs_inner_cv(emb_cache, y_train):
    """GFS usando inner 5-fold CV sobre el training set del outer fold.
    Devuelve la mejor subset encontrada.
    """
    n_ext = len(emb_cache)
    selected = []
    remaining = list(emb_cache.keys())
    best_f1 = 0.0
    history = []

    for step in range(1, n_ext + 1):
        if not remaining:
            break
        # Evaluar todos los candidatos con inner CV
        results = Parallel(n_jobs=8)(
            delayed(_eval_subset_inner)(
                selected + [cand], emb_cache, y_train
            )
            for cand in remaining
        )
        best_idx = max(range(len(remaining)), key=lambda i: results[i])
        best_cand = remaining[best_idx]
        best_f1_step = results[best_idx]

        selected.append(best_cand)
        remaining.remove(best_cand)
        history.append((step, best_cand, best_f1_step))
        best_f1 = best_f1_step

        if step > 1 and (best_f1_step - history[-2][2]) < 1e-4:
            break

    return selected, history


def _eval_subset_inner(subset, emb_cache, y_train):
    """Evalúa un subset con inner 5-fold CV."""
    inner_skf = StratifiedKFold(n_splits=INNER_SPLITS, shuffle=True, random_state=SEED)
    f1s = []
    for tr_in, va_in in inner_skf.split(emb_cache[subset[0]], y_train):
        emb_tr_in = [emb_cache[e][tr_in] for e in subset]
        emb_va_in = [emb_cache[e][va_in] for e in subset]
        le = LabelEncoder()
        y_tr_in_enc = le.fit_transform(y_train[tr_in])
        y_va_in = le.transform(y_train[va_in])
        f1, _ = evaluate_subset(emb_tr_in, emb_va_in, y_tr_in_enc, y_va_in)
        f1s.append(f1)
    return float(np.mean(f1s))


def main():
    all_results = []

    for dataset, naive_subset in GFS_SUBSETS_NAIVE.items():
        print(f"\n=== {dataset} (naive subset: {naive_subset}) ===")
        # Cargar todos los embeddings
        emb_cache_full = {}
        for ext in ALL_EXTRACTORS:
            try:
                emb, lab = load_embeddings(dataset, ext)
                emb_cache_full[ext] = emb
            except FileNotFoundError:
                pass
        if not emb_cache_full:
            print(f"  [SKIP] sin embeddings\n")
            continue
        y_all = lab
        n_total = len(y_all)

        # Cargar naive subset F1 (de los experimentos anteriores)
        naive_emb_list = [emb_cache_full[e] for e in naive_subset]
        le = LabelEncoder()
        y_all_enc = le.fit_transform(y_all)
        naive_skf = StratifiedKFold(n_splits=OUTER_SPLITS, shuffle=True, random_state=SEED)
        naive_f1s = []
        for tr_idx, te_idx in naive_skf.split(naive_emb_list[0], y_all_enc):
            y_tr_enc = y_all_enc[tr_idx]
            y_te = y_all_enc[te_idx]
            emb_tr = [e[tr_idx] for e in naive_emb_list]
            emb_te = [e[te_idx] for e in naive_emb_list]
            f1, _ = evaluate_subset(emb_tr, emb_te, y_tr_enc, y_te)
            naive_f1s.append(f1)
        naive_mean = float(np.mean(naive_f1s))
        naive_std = float(np.std(naive_f1s))
        print(f"  Naive GFS F1 = {naive_mean:.3f}±{naive_std:.3f}")

        # Nested CV: para cada outer fold, hacer inner GFS en train y evaluar en test
        nested_f1s = []
        nested_subsets = []
        for outer_fold, (tr_idx, te_idx) in enumerate(naive_skf.split(naive_emb_list[0], y_all_enc)):
            print(f"  Outer fold {outer_fold+1}/5...", end="", flush=True)
            # Subset training/val del outer fold
            y_tr = y_all_enc[tr_idx]
            y_te = y_all_enc[te_idx]
            emb_cache_train = {e: v[tr_idx] for e, v in emb_cache_full.items()}

            # Inner GFS sobre el training set
            selected, history = gfs_inner_cv(emb_cache_train, y_all[tr_idx])

            # Evaluar subset seleccionado en el test set del outer fold
            emb_arrays_test = [emb_cache_full[e][te_idx] for e in selected]
            emb_arrays_train = [emb_cache_full[e][tr_idx] for e in selected]
            f1, _ = evaluate_subset(emb_arrays_train, emb_arrays_test, y_tr, y_te)
            nested_f1s.append(f1)
            nested_subsets.append(selected)
            print(f"  f1={f1:.3f}  selected={selected}")

        nested_mean = float(np.mean(nested_f1s))
        nested_std = float(np.std(nested_f1s))
        print(f"  Nested CV GFS F1 = {nested_mean:.3f}±{nested_std:.3f}")
        print(f"  Naive  CV GFS F1 = {naive_mean:.3f}±{naive_std:.3f}")
        print(f"  Optimism gap     = {naive_mean - nested_mean:+.4f}")

        all_results.append({
            "dataset": dataset,
            "naive_f1_mean": naive_mean,
            "naive_f1_std": naive_std,
            "nested_f1_mean": nested_mean,
            "nested_f1_std": nested_std,
            "optimism_gap": naive_mean - nested_mean,
            "naive_subset": str(naive_subset),
            "nested_subsets": str(nested_subsets),
        })

    if all_results:
        pd.DataFrame(all_results).to_csv(TABLES_DIR / "nested_cv_summary.csv", index=False)
        print("\n=== Summary: results/tables/nested_cv_summary.csv ===\n")
        print("Optimism gap = naive F1 - nested F1 (positive = naive is optimistic)")
        for r in all_results:
            print(f"  {r['dataset']:25s}  naive={r['naive_f1_mean']:.3f}  nested={r['nested_f1_mean']:.3f}  gap={r['optimism_gap']:+.4f}")


if __name__ == "__main__":
    main()
