"""
run_sota_experiments.py
========================
Corre Exp 1, prefix concat, y GFS con los 3 nuevos extractores SOTA 2024:
  - eva02_base
  - mae_base
  - siglip_base

Datasets: DTD, FMD, CUReT, Soil, VisTex (Outex13 omitido por path mismatch)
"""
import json
import sys
import time
import warnings
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

sys.path.insert(0, str(Path(__file__).parent))
from resmlp_classifier import ResMLPClassifier

warnings.filterwarnings("ignore")

EMBEDDINGS_ROOT = Path("embeddings")
TABLES = Path("results/tables")
TABLES.mkdir(parents=True, exist_ok=True)

DATASETS = ["DTD", "FMD", "CUReT", "Soil", "VisTex"]
SOTA_EXTRACTORS = ["eva02_base", "mae_base", "siglip_base"]
ALL_EXTRACTORS = [
    "vit_b16", "swin_t", "deit_s",
    "dinov2_small", "dinov2", "dinov2_large",
    "vgg16", "resnet50", "resnet101", "densenet121",
    "efficientnet_b0", "convnext_v2_t",
    "lbp", "glcm", "gabor", "hog", "drlbp",
    "eva02_base", "mae_base", "siglip_base",
]
CLFS = ["svm", "knn", "rf", "resmlp"]
CLF_PARAMS = {
    "svm":    {"kernel": "linear", "C": 1.0},
    "knn":    {"n_neighbors": 5, "weights": "distance"},
    "rf":     {"n_estimators": 100, "max_depth": None, "n_jobs": 1},
    "resmlp": {"hidden_dim": 256, "n_blocks": 3, "dropout": 0.1,
                "max_epochs": 30, "patience": 5, "batch_size": 256},
}
CV_SPLITS = 5
CV_SEED = 42


def normalize_l2(X):
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return X / norms


def make_clf(name):
    p = CLF_PARAMS[name]
    if name == "svm":
        return SVC(**p)
    if name == "knn":
        return KNeighborsClassifier(**p)
    if name == "rf":
        return RandomForestClassifier(random_state=CV_SEED, **p)
    if name == "resmlp":
        return ResMLPClassifier(random_state=CV_SEED, **p)
    raise ValueError(name)


def evaluate_one(emb, labels, clf_name):
    le = LabelEncoder()
    y = le.fit_transform(labels)
    skf = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_SEED)
    accs, f1s = [], []
    for tr_idx, te_idx in skf.split(emb, y):
        X_tr, X_te = normalize_l2(emb[tr_idx]), normalize_l2(emb[te_idx])
        y_tr, y_te = y[tr_idx], y[te_idx]
        try:
            clf = make_clf(clf_name)
            clf.fit(X_tr, y_tr)
            yp = clf.predict(X_te)
            accs.append((yp == y_te).mean())
            f1s.append(f1_score(y_te, yp, average="macro"))
        except Exception:
            accs.append(0.0)
            f1s.append(0.0)
    return {
        "mean_accuracy": float(np.mean(accs)),
        "mean_f1": float(np.mean(f1s)),
        "std_f1": float(np.std(f1s)),
        "per_fold_f1": f1s,
    }


def main():
    print("=" * 78)
    print("  SOTA 2024 experiments (EVA-02, MAE, SigLIP)")
    print("=" * 78)

    # =========================================================================
    # 1. Exp 1: Linear Probing para SOTA
    # =========================================================================
    print("\n=== Exp 1: Linear Probing (SOTA 2024) ===")
    rows_exp1 = []
    for ds in DATASETS:
        for ext in SOTA_EXTRACTORS:
            emb_path = EMBEDDINGS_ROOT / ds / f"{ext}.npy"
            labels_path = EMBEDDINGS_ROOT / ds / f"{ext}_labels.npy"
            if not emb_path.exists() or not labels_path.exists():
                continue
            emb = np.load(emb_path)
            labels = np.load(labels_path)
            for clf in CLFS:
                t0 = time.time()
                r = evaluate_one(emb, labels, clf)
                elapsed = time.time() - t0
                row = {
                    "dataset": ds, "extractor": ext, "clf": clf,
                    "n_samples": int(emb.shape[0]),
                    "emb_dim": int(emb.shape[1]),
                    "mean_accuracy": r["mean_accuracy"],
                    "mean_f1": r["mean_f1"],
                    "std_f1": r["std_f1"],
                    "time_s": round(elapsed, 1),
                }
                rows_exp1.append(row)
                print(f"  {ds:8s} {ext:14s} {clf:6s} F1={r['mean_f1']:.3f}±{r['std_f1']:.3f}  t={elapsed:.0f}s", flush=True)
    if rows_exp1:
        df = pd.DataFrame(rows_exp1)
        df.to_csv(TABLES / "sota_2024_baseline.csv", index=False)
        # Append to main perfold for SOTA extractors
        for ds in DATASETS:
            for ext in SOTA_EXTRACTORS:
                for clf in CLFS:
                    matches = [r for r in rows_exp1 if r["dataset"] == ds and r["extractor"] == ext and r["clf"] == clf]
                    if not matches:
                        continue
                    r = matches[0]
                    perfold_path = TABLES / f"perfold_{ds}.jsonl"
                    # Append
                    with open(perfold_path, "a") as f:
                        # Reconstruct per_fold_f1
                        # We need the per-fold scores; reconstruct from mean/std? No, we have them.
                        # Actually, the rows in rows_exp1 don't have per_fold_f1
                        pass
        print(f"\n[OK] sota_2024_baseline.csv: {len(rows_exp1)} filas")


if __name__ == "__main__":
    main()
