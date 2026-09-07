"""
run_gfs_fast.py
===============
GFS optimizado: max_k=8, threshold=0.005, screening con 1-fold + verificación 5-fold en top-3.
Para acelerar: hace 1-fold ranking primero (rápido), luego 5-fold solo en top-3.
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

DATASETS = ["DTD", "FMD", "CUReT", "Soil", "VisTex"]
EXTRACTORS = [
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
    "rf":     {"n_estimators": 50, "max_depth": None, "n_jobs": 1},  # 50 trees (más rápido)
    "resmlp": {"hidden_dim": 256, "n_blocks": 3, "dropout": 0.1, "max_epochs": 30, "patience": 5, "batch_size": 256},
}
CV_SPLITS = 5
CV_SEED = 42
MAX_K = 8                # Cap agresivo — la mayoría satura antes
THRESHOLD = 0.005        # Early stopping más laxo
TOP_K_VERIFY = 3         # Verificar top-3 con 5-fold


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


def evaluate_subset_nfolds(emb_list, labels, clf_name, n_folds=1):
    """Evalúa con n_folds (1 para screening rápido, 5 para verificación)."""
    le = LabelEncoder()
    y = le.fit_transform(labels)
    skf = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_SEED)
    f1s = []
    for i, (tr_idx, te_idx) in enumerate(skf.split(emb_list[0], y)):
        if i >= n_folds:
            break
        X_tr = np.concatenate([normalize_l2(e[tr_idx]) for e in emb_list], axis=1)
        X_te = np.concatenate([normalize_l2(e[te_idx]) for e in emb_list], axis=1)
        y_tr, y_te = y[tr_idx], y[te_idx]
        try:
            clf = make_clf(clf_name)
            clf.fit(X_tr, y_tr)
            y_pred = clf.predict(X_te)
            f1s.append(float(f1_score(y_te, y_pred, average="macro")))
        except Exception:
            f1s.append(0.0)
    return f1s


def load_embeddings(dataset):
    cache = {}
    for ext in EXTRACTORS:
        p = EMBEDDINGS_ROOT / dataset / f"{ext}.npy"
        if p.exists():
            emb = np.load(p)
            labels = np.load(EMBEDDINGS_ROOT / dataset / f"{ext}_labels.npy")
            cache[ext] = (emb, labels)
    return cache


def gfs_one(dataset, clf_name, emb_cache):
    """GFS optimizado: 1-fold screening + 5-fold verify."""
    if not emb_cache:
        return []
    labels = next(iter(emb_cache.values()))[1]
    path = []
    selected = []
    remaining = list(emb_cache.keys())
    best_f1 = 0.0

    for step in range(1, MAX_K + 1):
        if not remaining:
            break
        # Fase 1: 1-fold screening
        screen_results = []
        for cand in remaining:
            subset = selected + [cand]
            emb_list = [emb_cache[e][0] for e in subset]
            f1s_1f = evaluate_subset_nfolds(emb_list, labels, clf_name, n_folds=1)
            screen_results.append((cand, f1s_1f[0]))
        # Top-K por 1-fold
        screen_results.sort(key=lambda x: -x[1])
        top = screen_results[:TOP_K_VERIFY]
        # Fase 2: 5-fold verify de top-K
        verify_results = []
        for cand, _ in top:
            subset = selected + [cand]
            emb_list = [emb_cache[e][0] for e in subset]
            f1s_5f = evaluate_subset_nfolds(emb_list, labels, clf_name, n_folds=5)
            verify_results.append((cand, f1s_5f))
        # Best
        verify_results.sort(key=lambda x: -np.mean(x[1]))
        best_cand, best_f1s = verify_results[0]
        best_mean = float(np.mean(best_f1s))

        path.append({
            "step": step,
            "selected": best_cand,
            "selected_subset": selected + [best_cand],
            "mean_f1": best_mean,
            "std_f1": float(np.std(best_f1s)),
            "per_fold_f1": best_f1s,
            "dim": int(sum(emb_cache[e][0].shape[1] for e in selected + [best_cand])),
        })
        selected.append(best_cand)
        remaining.remove(best_cand)
        delta = best_mean - best_f1
        print(f"    step={step}  add={best_cand:18s}  f1={best_mean:.3f}  Δ={delta:+.3f}", flush=True)
        if step > 1 and delta < THRESHOLD:
            print(f"    [stop] Δ={delta:.4f} < {THRESHOLD}", flush=True)
            break
        best_f1 = best_mean
    return path


def main():
    print(f"GFS FAST — {len(DATASETS)} ds × {len(CLFS)} clfs, MAX_K={MAX_K}, threshold={THRESHOLD}\n", flush=True)
    grand_total = time.time()
    for dataset in DATASETS:
        print(f"\n=== {dataset} ===", flush=True)
        t_ds = time.time()
        emb_cache = load_embeddings(dataset)
        if not emb_cache:
            print(f"  [SKIP] sin embeddings", flush=True)
            continue

        all_per_fold = []
        all_path_rows = []
        for clf in CLFS:
            print(f"  --- {clf} ---", flush=True)
            t0 = time.time()
            path = gfs_one(dataset, clf, emb_cache)
            elapsed = time.time() - t0
            print(f"    [done] {len(path)} steps en {elapsed:.0f}s", flush=True)
            for p in path:
                all_per_fold.append({
                    "dataset": dataset, "clf": clf, "step": p["step"],
                    "selected_extractor": p["selected"],
                    "selected_subset": " + ".join(p["selected_subset"]),
                    "dim": p["dim"],
                    "mean_f1": p["mean_f1"], "std_f1": p["std_f1"],
                    "per_fold_f1": p["per_fold_f1"],
                })
                all_path_rows.append({
                    "dataset": dataset, "clf": clf, "step": p["step"],
                    "selected_extractor": p["selected"],
                    "selected_subset": " + ".join(p["selected_subset"]),
                    "dim": p["dim"],
                    "mean_f1": p["mean_f1"], "std_f1": p["std_f1"],
                })
        if all_per_fold:
            p_perf = TABLES / f"perfold_greedy_{dataset}.jsonl"
            with open(p_perf, "w") as f:
                for r in all_per_fold:
                    f.write(json.dumps(r) + "\n")
            p_path = TABLES / f"greedy_path_{dataset}.csv"
            pd.DataFrame(all_path_rows).to_csv(p_path, index=False)
            print(f"  [saved] {p_perf.name} + {p_path.name} en {time.time()-t_ds:.0f}s", flush=True)
    # Summary
    print("\n=== greedy_summary.csv ===", flush=True)
    rows = []
    for ds in DATASETS:
        p = TABLES / f"greedy_path_{ds}.csv"
        if not p.exists():
            continue
        df = pd.read_csv(p)
        for clf in CLFS:
            sub = df[df.clf == clf]
            if sub.empty:
                continue
            best_idx = sub["mean_f1"].idxmax()
            best = sub.loc[best_idx]
            rows.append({
                "dataset": ds, "clf": clf,
                "best_step": int(best["step"]),
                "best_subset": best["selected_subset"],
                "best_dim": int(best["dim"]),
                "best_mean_f1": float(best["mean_f1"]),
                "best_std_f1": float(best["std_f1"]),
            })
    pd.DataFrame(rows).to_csv(TABLES / "greedy_summary.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False), flush=True)
    print(f"\n[OK] GFS FAST completo. Tiempo total: {time.time()-grand_total:.0f}s", flush=True)


if __name__ == "__main__":
    main()
