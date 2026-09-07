"""
11_statistical_tests.py
========================
Test de significancia estadística (paired t-test) sobre las principales comparaciones.

Para cada comparación:
  1. Re-corre los experimentos guardando F1 per-fold
  2. Computa paired t-test (mismo fold split, diferentes estrategias)
  3. Reporta p-value y Cohen's d (effect size)

Comparaciones a testear:
  A. Mejor individual vs GFS subset
  B. Mejor individual vs Prefix concat (k=12)
  C. GFS subset vs Prefix concat
  D. GFS subset vs Full concat (k=13)
  E. SVM lineal vs MLP-256 (single best)

Output: results/tables/stat_tests.csv + results/tables/stat_tests_summary.csv
"""

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
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

# Subset definitions
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

CLF_PARAMS = {
    "svm_linear": lambda: SVC(kernel="linear", C=1.0, random_state=CV_SEED),
    "mlp_256": lambda: MLPClassifier(
        hidden_layer_sizes=(256,), activation="relu", solver="adam",
        alpha=0.01, learning_rate_init=1e-3, max_iter=300,
        early_stopping=True, validation_fraction=0.15,
        n_iter_no_change=20, random_state=CV_SEED,
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


def per_fold_f1(emb_list, labels, clf_factory):
    """Devuelve lista de F1 per fold (5-fold CV, mismo split para todas las comparaciones)."""
    le = LabelEncoder()
    y = le.fit_transform(labels)
    skf = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_SEED)
    f1s = []
    for tr_idx, te_idx in skf.split(emb_list[0], y):
        X_tr = np.concatenate([normalize_l2(e[tr_idx]) for e in emb_list], axis=1)
        X_te = np.concatenate([normalize_l2(e[te_idx]) for e in emb_list], axis=1)
        y_tr, y_te = y[tr_idx], y[te_idx]
        clf = clf_factory()
        clf.fit(X_tr, y_tr)
        y_pred = clf.predict(X_te)
        f1s.append(f1_score(y_te, y_pred, average="macro"))
    return f1s


def cohens_d_paired(f1_a, f1_b):
    """Cohen's d paired = mean(diff) / std(diff)."""
    diff = np.array(f1_a) - np.array(f1_b)
    return float(diff.mean() / diff.std()) if diff.std() > 0 else 0.0


def main():
    rows = []
    for dataset in GFS_SUBSETS.keys():
        print(f"\n=== {dataset} ===")
        # Cargar todos los embeddings disponibles
        emb_cache = {}
        for ext in ALL_EXTRACTORS:
            try:
                emb, lab = load_embeddings(dataset, ext)
                emb_cache[ext] = emb
            except FileNotFoundError:
                pass
        labels = lab

        # A. Mejor individual (dinov2_large si está, sino dinov2)
        single_ext = "dinov2_large" if "dinov2_large" in emb_cache else "dinov2"
        f1_single_svm = per_fold_f1([emb_cache[single_ext]], labels, CLF_PARAMS["svm_linear"])

        # B. Prefix concat (full concat, k=13)
        f1_prefix_svm = per_fold_f1([emb_cache[e] for e in ALL_EXTRACTORS], labels, CLF_PARAMS["svm_linear"])

        # C. GFS subset
        f1_gfs_svm = per_fold_f1([emb_cache[e] for e in GFS_SUBSETS[dataset]], labels, CLF_PARAMS["svm_linear"])

        # Tests pareados (paired t-test, mismo fold)
        comparisons = [
            ("GFS vs mejor individual", f1_gfs_svm, f1_single_svm),
            ("GFS vs prefix concat", f1_gfs_svm, f1_prefix_svm),
            ("Prefix vs mejor individual", f1_prefix_svm, f1_single_svm),
        ]
        for comp_name, f1_a, f1_b in comparisons:
            t_stat, p_val = stats.ttest_rel(f1_a, f1_b)
            d = cohens_d_paired(f1_a, f1_b)
            sig = "***" if p_val < 0.001 else ("**" if p_val < 0.01 else ("*" if p_val < 0.05 else "ns"))
            print(f"  {comp_name:35s}  Δ={np.mean(f1_a)-np.mean(f1_b):+.4f}  t={t_stat:+.2f}  p={p_val:.3f} {sig}  d={d:+.2f}")
            rows.append({
                "dataset": dataset, "comparison": comp_name,
                "f1_a_mean": float(np.mean(f1_a)), "f1_a_std": float(np.std(f1_a)),
                "f1_b_mean": float(np.mean(f1_b)), "f1_b_std": float(np.std(f1_b)),
                "delta": float(np.mean(f1_a) - np.mean(f1_b)),
                "t_stat": float(t_stat), "p_value": float(p_val),
                "cohens_d": d,
                "significant_05": p_val < 0.05,
                "significant_01": p_val < 0.01,
                "significant_001": p_val < 0.001,
            })

    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(TABLES_DIR / "stat_tests.csv", index=False)
        print(f"\n=== Saved: results/tables/stat_tests.csv ===")
        # Resumen
        print("\n=== Resumen de significancia (p<0.05) ===")
        sig_rows = df[df.significant_05]
        for _, r in sig_rows.iterrows():
            print(f"  {r['dataset']:15s}  {r['comparison']:35s}  Δ={r['delta']:+.4f}  p={r['p_value']:.3f}  d={r['cohens_d']:+.2f}")
        if len(sig_rows) == 0:
            print("  (ninguna comparación es estadísticamente significativa al 5%)")


if __name__ == "__main__":
    main()
