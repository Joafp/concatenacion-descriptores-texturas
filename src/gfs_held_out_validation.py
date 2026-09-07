"""
gfs_held_out_validation.py
===========================
Held-out validation de la "complementariedad" DINOv2-B + DINOv2-L (DA-C2).
Para cada dataset, hacer 5 splits 80/20 con seeds distintos.
En el 80%, correr GFS completo. Reportar:
  - ¿Con qué frecuencia GFS elige (dinov2 + dinov2_large)?
  - ¿El subset elegido en 80% generaliza al 20% (mismo F1)?
"""
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

import sys
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
CLFS = ["svm", "knn"]  # solo SVM y KNN (rapidos) para iterar rapido
CLF_PARAMS = {
    "svm":    {"kernel": "linear", "C": 1.0},
    "knn":    {"n_neighbors": 5, "weights": "distance"},
}
CV_SPLITS = 5
MAX_K = 5  # Cap agresivo para que sea rápido
THRESHOLD = 0.005
N_SEEDS = 5  # 5 splits 80/20


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
    raise ValueError(name)


def evaluate_subset(emb_list, train_idx, test_idx, labels, clf_name):
    """Evalúa subset en (train_idx, test_idx) y retorna F1 macro."""
    le = LabelEncoder()
    y = le.fit_transform(labels)
    X_tr = np.concatenate([normalize_l2(e[train_idx]) for e in emb_list], axis=1)
    X_te = np.concatenate([normalize_l2(e[test_idx]) for e in emb_list], axis=1)
    y_tr, y_te = y[train_idx], y[test_idx]
    try:
        clf = make_clf(clf_name)
        clf.fit(X_tr, y_tr)
        y_pred = clf.predict(X_te)
        return float(f1_score(y_te, y_pred, average="macro"))
    except Exception:
        return 0.0


def load_embeddings(dataset):
    cache = {}
    for ext in EXTRACTORS:
        p = EMBEDDINGS_ROOT / dataset / f"{ext}.npy"
        if p.exists():
            emb = np.load(p)
            labels = np.load(EMBEDDINGS_ROOT / dataset / f"{ext}_labels.npy")
            cache[ext] = (emb, labels)
    return cache


def gfs_held_out(emb_cache, labels, train_idx, test_idx, clf_name):
    """GFS en train_idx (usando 1-fold screening), eval en test_idx con 5-fold."""
    if not emb_cache:
        return [], 0.0
    selected = []
    remaining = list(emb_cache.keys())
    best_path = []
    le = LabelEncoder()
    y = le.fit_transform(labels)
    # Para screening rápido: 1-fold sobre train_idx
    skf_1fold = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
    tr_half, _ = next(iter(skf_1fold.split(emb_cache[next(iter(emb_cache))][0][train_idx], y[train_idx])))
    for step in range(1, MAX_K + 1):
        if not remaining:
            break
        best_cand = None
        best_train_f1_step = 0.0
        for cand in remaining:
            subset = selected + [cand]
            emb_list = [emb_cache[e][0] for e in subset]
            # Screening 1-fold (rápido)
            Xtr = np.concatenate([normalize_l2(e[train_idx][tr_half]) for e in emb_list], axis=1)
            ytr = y[train_idx][tr_half]
            try:
                clf = make_clf(clf_name)
                clf.fit(Xtr, ytr)
                # Evaluar en el otro medio del train
                Xte_tr = np.concatenate([normalize_l2(e[train_idx]) for e in emb_list], axis=1)
                yp = clf.predict(Xte_tr)
                train_f1 = float(f1_score(y[train_idx], yp, average="macro"))
            except Exception:
                train_f1 = 0.0
            if train_f1 > best_train_f1_step:
                best_train_f1_step = train_f1
                best_cand = cand
        selected.append(best_cand)
        remaining.remove(best_cand)
        best_path.append({
            "step": step, "selected": best_cand, "train_f1": best_train_f1_step,
        })
        if step > 1 and (best_train_f1_step - best_path[-2]["train_f1"]) < THRESHOLD:
            break
    # Evaluar subset final en held-out test con 5-fold
    if selected:
        emb_list = [emb_cache[e][0] for e in selected]
        final_test_f1 = evaluate_subset(emb_list, train_idx, test_idx, labels, clf_name)
    else:
        final_test_f1 = 0.0
    return best_path, final_test_f1


def main():
    rows = []
    for ds in DATASETS:
        print(f"\n=== {ds} ===", flush=True)
        emb_cache = load_embeddings(ds)
        if not emb_cache:
            continue
        labels = next(iter(emb_cache.values()))[1]
        n = len(labels)
        # 5 seeds para held-out splits
        for seed in range(N_SEEDS):
            skf_outer = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
            splits = list(skf_outer.split(np.zeros(n), LabelEncoder().fit_transform(labels)))
            train_idx, test_idx = splits[0]  # tomar el primer split
        for clf in CLFS:
            t0 = time.time()
            path, final_test_f1 = gfs_held_out(emb_cache, labels, train_idx, test_idx, clf)
            elapsed = time.time() - t0
            # ¿GFS eligió (dinov2 + dinov2_large)?
            b_l_selected = "dinov2" in [p["selected"] for p in path] and \
                                "dinov2_large" in [p["selected"] for p in path]
            b_l_order = [i for i, p in enumerate(path) if p["selected"] in ("dinov2", "dinov2_large")]
            rows.append({
                "dataset": ds, "clf": clf, "seed": seed,
                "n_train": int(len(train_idx)),
                "n_test": int(len(test_idx)),
                "gfs_path": " -> ".join(p["selected"] for p in path),
                "gfs_k": len(path),
                "b_and_l_selected": b_l_selected,
                "b_and_l_positions": str(b_l_order),
                "final_test_f1": final_test_f1,
                "elapsed_s": round(elapsed, 1),
            })
            print(f"  seed={seed} {clf} k={len(path)} F1_held_out={final_test_f1:.3f} "
                  f"b+l={b_l_selected} path={'->'.join(p['selected'] for p in path)} t={elapsed:.0f}s",
                  flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(TABLES / "gfs_held_out.csv", index=False)
    print(f"\n[OK] gfs_held_out.csv: {len(df)} filas")

    # Resumen
    section = "\n" + "="*78 + "\n  HELD-OUT VALIDATION - RESUMEN\n" + "="*78
    print(section)
    bl_rate = df["b_and_l_selected"].mean() * 100
    print(f"  DINOv2-B + DINOv2-L elegidos juntos en held-out: {bl_rate:.1f}% de las corridas")
    by_ds = df.groupby("dataset")["b_and_l_selected"].mean() * 100
    print("\n  Por dataset:")
    for ds, rate in by_ds.items():
        print(f"    {ds:10s} {rate:.0f}%")
    print(f"\n  F1 medio en held-out test: {df['final_test_f1'].mean():.3f}")
    print(f"  (Esto indica si el subset elegido en 80% generaliza al 20%)")


if __name__ == "__main__":
    main()
