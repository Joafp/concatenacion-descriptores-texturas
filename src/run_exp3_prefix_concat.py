"""
run_exp3_prefix_concat.py
==========================
Prefix concat k=1..17 en orden canónico, 4 clfs (svm, knn, rf, resmlp).
Optimizado: RF con 100 trees (no 300) para reducir tiempo.
"""
import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

sys.path.insert(0, str(Path(__file__).parent))
from resmlp_classifier import ResMLPClassifier

warnings.filterwarnings("ignore")

EMBEDDINGS_ROOT = Path("embeddings")
TABLES_DIR = Path("results/tables")
FIGURES_DIR = Path("results/figures")
TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Orden canónico
CANONICAL_ORDER = [
    "lbp", "glcm", "gabor", "hog", "drlbp",
    "vgg16", "resnet50", "resnet101", "densenet121", "convnext_v2_t", "efficientnet_b0",
    "vit_b16", "swin_t", "deit_s",
    "dinov2_small", "dinov2", "dinov2_large",
    "eva02_base", "mae_base", "siglip_base",
]
DATASETS = ["DTD", "FMD", "CUReT", "Soil", "VisTex"]

BEST_PARAMS = {
    "svm":    {"kernel": "linear", "C": 1.0},
    "knn":    {"n_neighbors": 5, "weights": "distance"},
    "rf":     {"n_estimators": 100, "max_depth": None},  # 100 trees (no 300) para velocidad
    "resmlp": {"hidden_dim": 256, "n_blocks": 3, "dropout": 0.1, "max_epochs": 100, "patience": 10, "batch_size": 256},
}

CV_SPLITS = 5
CV_SEED = 42


def normalize_l2(X):
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return X / norms


def make_clf(name):
    p = BEST_PARAMS[name]
    if name == "svm":
        return SVC(**p)
    if name == "knn":
        return KNeighborsClassifier(**p)
    if name == "rf":
        return RandomForestClassifier(random_state=CV_SEED, n_jobs=-1, **p)
    if name == "resmlp":
        return ResMLPClassifier(random_state=CV_SEED, **p)
    raise ValueError(name)


def evaluate_concat(emb_list, labels, clf_name):
    le = LabelEncoder()
    y = le.fit_transform(labels)
    skf = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_SEED)
    accs, f1s = [], []
    for tr_idx, te_idx in skf.split(emb_list[0], y):
        X_tr = np.concatenate([normalize_l2(e[tr_idx]) for e in emb_list], axis=1)
        X_te = np.concatenate([normalize_l2(e[te_idx]) for e in emb_list], axis=1)
        y_tr, y_te = y[tr_idx], y[te_idx]
        clf = make_clf(clf_name)
        clf.fit(X_tr, y_tr)
        y_pred = clf.predict(X_te)
        accs.append(accuracy_score(y_te, y_pred))
        f1s.append(f1_score(y_te, y_pred, average="macro"))
    return {
        "mean_accuracy": float(np.mean(accs)),
        "std_accuracy": float(np.std(accs)),
        "mean_f1": float(np.mean(f1s)),
        "std_f1": float(np.std(f1s)),
        "per_fold_f1": f1s,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=DATASETS)
    parser.add_argument("--clfs", nargs="+", default=["svm", "knn", "rf", "resmlp"])
    args = parser.parse_args()

    print(f"Exp 3 (prefix concat) — clfs={args.clfs}  datasets={args.datasets}\n")

    for dataset in args.datasets:
        print(f"=== {dataset} ===")
        # Cargar todos
        available = []
        for ext in CANONICAL_ORDER:
            try:
                emb = np.load(EMBEDDINGS_ROOT / dataset / f"{ext}.npy")
                labels = np.load(EMBEDDINGS_ROOT / dataset / f"{ext}_labels.npy")
                available.append((ext, emb, labels))
            except FileNotFoundError:
                print(f"  [WARN] {ext} no existe para {dataset}")
        if not available:
            print(f"  [SKIP] sin embeddings\n")
            continue

        ds_results = []
        per_fold_records = []
        for k in range(1, len(available) + 1):
            subset = available[:k]
            emb_list = [s[1] for s in subset]
            label = subset[0][2]
            dim = sum(e.shape[1] for e in emb_list)
            descr = " + ".join(s[0] for s in subset)
            for clf_name in args.clfs:
                t0 = time.time()
                try:
                    r = evaluate_concat(emb_list, label, clf_name)
                except Exception as e:
                    print(f"    [ERR] k={k} {clf_name}: {e}")
                    continue
                elapsed = time.time() - t0
                row = {
                    "dataset": dataset, "k": k, "extractors": descr,
                    "clf": clf_name, "dim": dim,
                    "mean_accuracy": r["mean_accuracy"], "std_accuracy": r["std_accuracy"],
                    "mean_f1": r["mean_f1"], "std_f1": r["std_f1"],
                    "time_s": round(elapsed, 1),
                }
                ds_results.append(row)
                per_fold_records.append({
                    "dataset": dataset, "k": k, "extractors": descr,
                    "clf": clf_name, "per_fold_f1": r["per_fold_f1"],
                })
                print(f"  k={k:2d} dim={dim:5d}  {clf_name:5s}  f1={r['mean_f1']:.3f}±{r['std_f1']:.3f}  ({elapsed:.1f}s)")

        # Guardar CSV + JSONL
        if ds_results:
            pd.DataFrame(ds_results).to_csv(TABLES_DIR / f"concat_{dataset}.csv", index=False)
            with open(TABLES_DIR / f"perfold_concat_{dataset}.jsonl", "w") as fp:
                for rec in per_fold_records:
                    fp.write(json.dumps(rec) + "\n")
            print(f"  -> {TABLES_DIR}/concat_{dataset}.csv + perfold_concat_{dataset}.jsonl\n")

    # Summary
    all_csvs = []
    for ds in args.datasets:
        p = TABLES_DIR / f"concat_{ds}.csv"
        if p.exists():
            all_csvs.append(pd.read_csv(p))
    if all_csvs:
        df = pd.concat(all_csvs, ignore_index=True)
        df.to_csv(TABLES_DIR / "concat_summary.csv", index=False)
        print(f"=== Summary: {TABLES_DIR}/concat_summary.csv ===")


if __name__ == "__main__":
    main()
