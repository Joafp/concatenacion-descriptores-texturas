"""
10_fusion_strategies.py
========================
Compara estrategias de fusión ALTERNATIVAS a la concatenación simple.

Hipótesis: concat es estándar pero quizás no óptimo. Otras opciones:
  1. Concat (baseline, L2 normalize per extractor + concatenate)
  2. Sum (PCA-equalize to k components, then sum) — dim=k
  3. Weighted sum (PCA-equalize + learn per-extractor weights) — dim=k
  4. Bilinear top-2 (outer product of top 2 extractors) — captures interactions

Estrategia experimental:
  - Para cada dataset, usar el GFS subset conocido
  - Proyectar cada extractor a k=128 componentes via PCA
  - Aplicar 4 estrategias de fusión
  - Comparar F1 con 5-fold CV + SVM lineal

Output: results/tables/fusion_{dataset}.csv + results/tables/fusion_summary.csv
"""

import argparse
import json
import time
import warnings
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

warnings.filterwarnings("ignore")

EMBEDDINGS_ROOT = Path("embeddings")
RESULTS_DIR = Path("results")
TABLES_DIR = RESULTS_DIR / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

CV_SPLITS = 5
CV_SEED = 42
PCA_K_TARGET = 128  # componentes por extractor (ajustado si extractor < k)


# GFS optimal subsets (de greedy_summary.csv)
GFS_SUBSETS = {
    "DTD": ["dinov2", "resnet50", "dinov2_large", "glcm"],
    "FMD": ["dinov2", "dinov2_large"],
    "KTH-TIPS2": ["dinov2", "swin_t", "dinov2_large"],
    "HVD_glaucoma": ["swin_t", "deit_s", "convnext_v2_t", "vit_b16", "resnet50", "gabor", "glcm"],
    "ocular_toxoplasmosis": ["swin_t", "dinov2_large", "efficientnet_b0", "deit_s"],
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


def pca_fit_transform(X_train, X_test, k):
    k = min(k, X_train.shape[0] - 1, X_train.shape[1])
    pca = PCA(n_components=k, random_state=CV_SEED)
    pca.fit(X_train)
    return pca.transform(X_train), pca.transform(X_test)


def evaluate(X_tr, X_te, y_tr, y_te):
    clf = SVC(kernel="linear", C=1.0, random_state=CV_SEED)
    clf.fit(X_tr, y_tr)
    y_pred = clf.predict(X_te)
    return f1_score(y_te, y_pred, average="macro"), accuracy_score(y_te, y_pred)


def cv_fusion_strategy(emb_arrays, labels, strategy="concat", weights=None):
    """
    Para cada fold, aplica la estrategia de fusión con PCA + SVM lineal.
    """
    n_ext = len(emb_arrays)
    le = LabelEncoder()
    y = le.fit_transform(labels)
    skf = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_SEED)

    f1s, accs = [], []
    for tr_idx, te_idx in skf.split(emb_arrays[0], y):
        # Paso 1: L2 normalize per extractor
        emb_tr_l2 = [normalize_l2(e[tr_idx]) for e in emb_arrays]
        emb_te_l2 = [normalize_l2(e[te_idx]) for e in emb_arrays]

        if strategy == "concat":
            X_tr = np.concatenate(emb_tr_l2, axis=1)
            X_te = np.concatenate(emb_te_l2, axis=1)

        elif strategy in ("sum", "weighted_sum"):
            # Paso 2: PCA-equalize to PCA_K_TARGET components (puede ser menor si el extractor es < k)
            pca_k = min(PCA_K_TARGET, min(e.shape[1] for e in emb_arrays))
            pca_tr, pca_te = [], []
            for e_tr, e_te in zip(emb_tr_l2, emb_te_l2):
                p_tr, p_te = pca_fit_transform(e_tr, e_te, pca_k)
                pca_tr.append(p_tr)
                pca_te.append(p_te)
            if strategy == "sum":
                # Sum explícito (suma elemento a elemento)
                X_tr = np.zeros_like(pca_tr[0])
                X_te = np.zeros_like(pca_te[0])
                for p in pca_tr:
                    X_tr = X_tr + p
                for p in pca_te:
                    X_te = X_te + p
            else:  # weighted_sum
                w = np.array(weights) / np.sum(weights)  # normalizar a suma 1
                X_tr = np.zeros_like(pca_tr[0])
                X_te = np.zeros_like(pca_te[0])
                for i, p in enumerate(pca_tr):
                    X_tr = X_tr + w[i] * p
                for i, p in enumerate(pca_te):
                    X_te = X_te + w[i] * p

        elif strategy == "bilinear":
            # Bilinear: outer product de los 2 mejores extractores (PCA-equalized)
            # Solo usar los top 2
            pca_k = min(PCA_K_TARGET, min(e.shape[1] for e in emb_arrays[:2]))
            pca_tr, pca_te = [], []
            for e_tr, e_te in zip(emb_tr_l2[:2], emb_te_l2[:2]):
                p_tr, p_te = pca_fit_transform(e_tr, e_te, pca_k)
                pca_tr.append(p_tr)
                pca_te.append(p_te)
            # Outer product: (B, k) x (B, k) -> (B, k, k) -> flatten -> (B, k*k)
            X_tr = np.einsum('bi,bj->bij', pca_tr[0], pca_tr[1]).reshape(len(tr_idx), -1)
            X_te = np.einsum('bi,bj->bij', pca_te[0], pca_te[1]).reshape(len(te_idx), -1)

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        f1, acc = evaluate(X_tr, X_te, y[tr_idx], y[te_idx])
        f1s.append(f1)
        accs.append(acc)

    return float(np.mean(f1s)), float(np.std(f1s)), float(np.mean(accs))


def get_pca_k_for_subset(emb_arrays, target_k=128):
    """PCA k se adapta al extractor de menor dim para que todos lleguen a la misma dim."""
    return min(target_k, min(e.shape[1] for e in emb_arrays))


def search_best_weights(emb_arrays, labels):
    """Grid search pequeño sobre pesos para weighted sum."""
    n_ext = len(emb_arrays)
    if n_ext > 4:
        # Limitar grid a 4 extractores para evitar explosión combinatoria
        return [1.0] * n_ext  # fallback: equal weights

    # Grid: cada peso ∈ {0.5, 1.0, 2.0}, normalizar después
    weight_options = [0.5, 1.0, 2.0]
    best_f1 = -1
    best_weights = [1.0] * n_ext

    for combo in product(weight_options, repeat=n_ext):
        # Skip combinaciones donde todos son iguales (caso redundante con sum)
        if len(set(combo)) == 1:
            continue
        f1, _, _ = cv_fusion_strategy(emb_arrays, labels, "weighted_sum", weights=combo)
        if f1 > best_f1:
            best_f1 = f1
            best_weights = list(combo)
    return best_weights


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=list(GFS_SUBSETS.keys()))
    parser.add_argument("--skip-bilinear", action="store_true")
    args = parser.parse_args()

    print(f"Comparando estrategias de fusión sobre GFS subsets.\n")
    all_results = []

    for dataset in args.datasets:
        print(f"=== {dataset} (GFS subset: {GFS_SUBSETS[dataset]}) ===")
        # Cargar embeddings
        emb_arrays = []
        labels = None
        for ext in GFS_SUBSETS[dataset]:
            try:
                emb, lab = load_embeddings(dataset, ext)
                emb_arrays.append(emb)
                labels = lab
            except FileNotFoundError as e:
                print(f"  [SKIP] {ext} no encontrado")

        if not emb_arrays:
            print(f"  [SKIP] sin embeddings\n")
            continue
        n_ext = len(emb_arrays)
        pca_k = get_pca_k_for_subset(emb_arrays, PCA_K_TARGET)
        print(f"  n_ext={n_ext}, pca_k={pca_k} (min dim)")

        # 1. Concat (baseline)
        t0 = time.time()
        f1, std, acc = cv_fusion_strategy(emb_arrays, labels, "concat")
        t = time.time() - t0
        dim_concat = sum(e.shape[1] for e in emb_arrays)
        all_results.append({
            "dataset": dataset, "strategy": "concat", "n_ext": n_ext,
            "dim": dim_concat, "f1": f1, "std_f1": std, "acc": acc, "time_s": round(t, 1),
        })
        print(f"  concat          (dim={dim_concat:5d})  f1={f1:.3f}±{std:.3f}  ({t:.1f}s)")

        # 2. Sum (PCA-equalized, equal weights)
        t0 = time.time()
        f1, std, acc = cv_fusion_strategy(emb_arrays, labels, "sum")
        t = time.time() - t0
        all_results.append({
            "dataset": dataset, "strategy": "sum_pca", "n_ext": n_ext,
            "dim": pca_k, "f1": f1, "std_f1": std, "acc": acc, "time_s": round(t, 1),
        })
        print(f"  sum_pca         (dim={pca_k:5d})  f1={f1:.3f}±{std:.3f}  ({t:.1f}s)")

        # 3. Weighted sum (grid search small)
        if n_ext <= 4:
            t0 = time.time()
            best_w = search_best_weights(emb_arrays, labels)
            f1, std, acc = cv_fusion_strategy(emb_arrays, labels, "weighted_sum", weights=best_w)
            t = time.time() - t0
            all_results.append({
                "dataset": dataset, "strategy": "weighted_sum_pca", "n_ext": n_ext,
                "dim": pca_k, "weights": str(best_w),
                "f1": f1, "std_f1": std, "acc": acc, "time_s": round(t, 1),
            })
            print(f"  weighted_sum    (w={best_w}, dim={pca_k:5d})  f1={f1:.3f}±{std:.3f}  ({t:.1f}s)")

        # 4. Bilinear (top 2 extractors)
        if not args.skip_bilinear and n_ext >= 2:
            t0 = time.time()
            f1, std, acc = cv_fusion_strategy(emb_arrays, labels, "bilinear")
            t = time.time() - t0
            all_results.append({
                "dataset": dataset, "strategy": "bilinear_top2", "n_ext": 2,
                "dim": pca_k * pca_k, "f1": f1, "std_f1": std, "acc": acc, "time_s": round(t, 1),
            })
            print(f"  bilinear_top2   (dim={pca_k*pca_k:5d})  f1={f1:.3f}±{std:.3f}  ({t:.1f}s)")

        print()

    if all_results:
        pd.DataFrame(all_results).to_csv(TABLES_DIR / "fusion_summary.csv", index=False)
        print("=== Summary: results/tables/fusion_summary.csv ===\n")
        df = pd.DataFrame(all_results)
        pivot = df.pivot_table(index="dataset", columns="strategy", values="f1")
        print(pivot.round(3).to_string())
        print("\n=== Δ vs concat (positive = mejor que concat) ===")
        if "concat" in pivot.columns:
            for col in pivot.columns:
                if col != "concat":
                    deltas = pivot[col] - pivot["concat"]
                    print(f"  {col:20s}  Δ mean={deltas.mean():+.3f}  Δ min={deltas.min():+.3f}  Δ max={deltas.max():+.3f}")


if __name__ == "__main__":
    main()
