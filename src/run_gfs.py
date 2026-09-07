"""
run_gfs.py
==========
Greedy Forward Selection (GFS) para los 6 datasets × 4 clfs.
En cada step, evalúa TODOS los candidatos restantes (en paralelo) y se queda con el que más sube F1.
Early stopping si mejora < threshold.

Lee:
  - embeddings/{dataset}/{extractor}.npy
  - perfold_{dataset}.jsonl  (para step 1, ya calculado)

Guarda:
  - results/tables/perfold_greedy_{dataset}.jsonl
  - results/tables/greedy_summary.csv
  - results/tables/greedy_path_{dataset}.csv (F1 por step)
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
]
CLFS = ["svm", "knn", "rf", "resmlp"]
CLF_PARAMS = {
    "svm":    {"kernel": "linear", "C": 1.0},
    "knn":    {"n_neighbors": 5, "weights": "distance"},
    "rf":     {"n_estimators": 100, "max_depth": None, "n_jobs": 1},  # 1 job: ya paralelizamos fuera
    "resmlp": {"hidden_dim": 256, "n_blocks": 3, "dropout": 0.1, "max_epochs": 50, "patience": 8, "batch_size": 256},
}
CV_SPLITS = 5
CV_SEED = 42
MAX_K = 15          # Stop en k=15 (la mayoría saturan)
THRESHOLD = 0.001   # Early stopping si mejora < 0.001


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


def evaluate_subset(emb_list, labels, clf_name):
    """Evalúa un subset (lista de embeddings ya cargados) con 5-fold CV."""
    le = LabelEncoder()
    y = le.fit_transform(labels)
    skf = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_SEED)
    f1s = []
    for tr_idx, te_idx in skf.split(emb_list[0], y):
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
    """Carga todos los embeddings disponibles para el dataset (cache)."""
    cache = {}
    for ext in EXTRACTORS:
        p = EMBEDDINGS_ROOT / dataset / f"{ext}.npy"
        if p.exists():
            emb = np.load(p)
            labels = np.load(EMBEDDINGS_ROOT / dataset / f"{ext}_labels.npy")
            cache[ext] = (emb, labels)
    return cache


def gfs_one(dataset, clf_name, emb_cache):
    """GFS para un (dataset, clf). Retorna path con F1 por step."""
    n_ext = len(emb_cache)
    if n_ext == 0:
        return []

    labels = next(iter(emb_cache.values()))[1]  # todos los labels son los mismos
    path = []
    selected = []
    remaining = list(emb_cache.keys())
    best_f1 = 0.0

    # Step 1: probar cada uno individualmente (puede usar cache si clf es svm/knn/rf/resmlp)
    # Pero para consistencia, evaluar siempre
    step = 0
    while step < MAX_K and remaining:
        step += 1
        best_cand = None
        best_cand_f1 = None
        best_cand_f1s = None

        # Evaluar cada candidato en serie (más simple, suficiente)
        # Si fuera muy lento, paralelizar con joblib
        for cand in remaining:
            subset = selected + [cand]
            emb_list = [emb_cache[e][0] for e in subset]
            t0 = time.time()
            f1s = evaluate_subset(emb_list, labels, clf_name)
            mean_f1 = float(np.mean(f1s))
            elapsed = time.time() - t0
            if best_cand is None or mean_f1 > best_cand_f1:
                best_cand = cand
                best_cand_f1 = mean_f1
                best_cand_f1s = f1s
            if step == 1 and len(remaining) <= 5:
                print(f"      [step {step}] cand={cand:18s} f1={mean_f1:.3f} ({elapsed:.1f}s)")

        path.append({
            "step": step,
            "selected": best_cand,
            "selected_subset": selected + [best_cand],
            "mean_f1": best_cand_f1,
            "std_f1": float(np.std(best_cand_f1s)),
            "per_fold_f1": best_cand_f1s,
            "dim": int(sum(emb_cache[e][0].shape[1] for e in selected + [best_cand])),
        })
        selected.append(best_cand)
        remaining.remove(best_cand)
        delta = best_cand_f1 - best_f1
        print(f"    step={step:2d}  add={best_cand:18s}  f1={best_cand_f1:.3f}  Δ={delta:+.3f}")
        # Early stopping
        if step > 1 and delta < THRESHOLD:
            print(f"    [stop] Δ={delta:.4f} < {THRESHOLD}")
            break
        best_f1 = best_cand_f1

    return path


def main():
    print(f"GFS — {len(DATASETS)} datasets × {len(CLFS)} clfs, MAX_K={MAX_K}, threshold={THRESHOLD}\n")
    grand_total = time.time()
    for dataset in DATASETS:
        print(f"\n=== {dataset} ===")
        t_ds = time.time()
        emb_cache = load_embeddings(dataset)
        if not emb_cache:
            print(f"  [SKIP] sin embeddings")
            continue
        print(f"  {len(emb_cache)} extractores cargados")

        all_per_fold = []
        all_path_rows = []
        for clf in CLFS:
            print(f"  --- {clf} ---")
            t0 = time.time()
            path = gfs_one(dataset, clf, emb_cache)
            elapsed = time.time() - t0
            print(f"    [done] {len(path)} steps en {elapsed:.0f}s")
            if not path:
                continue
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
        # Guardar
        if all_per_fold:
            p_perf = TABLES / f"perfold_greedy_{dataset}.jsonl"
            with open(p_perf, "w") as f:
                for r in all_per_fold:
                    f.write(json.dumps(r) + "\n")
            p_path = TABLES / f"greedy_path_{dataset}.csv"
            pd.DataFrame(all_path_rows).to_csv(p_path, index=False)
            print(f"  [saved] {p_perf.name} + {p_path.name} en {time.time()-t_ds:.0f}s total")
    # Summary
    print("\n=== Generando greedy_summary.csv ===")
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
    print(pd.DataFrame(rows).to_string(index=False))
    print(f"\n[OK] GFS completo. Tiempo total: {time.time()-grand_total:.0f}s")


if __name__ == "__main__":
    main()
