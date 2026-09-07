"""
run_exp1_missing.py
====================
Completa Exp 1 (individual) corriendo SOLO las combinaciones (dataset, extractor, clf)
que faltan en perfold_*.jsonl. Merges con los resultados existentes.

Estrategia:
- Lee perfold_{ds}.jsonl existentes
- Calcula el set de combinaciones ya presentes
- Corre las que faltan usando 5-fold CV (mismo protocolo que 02_baseline_individual.py)
- Hace append al JSONL y al CSV por dataset
"""
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

import sys
sys.path.insert(0, str(Path(__file__).parent))
from resmlp_classifier import ResMLPClassifier

warnings.filterwarnings("ignore")

EMBEDDINGS_ROOT = Path("embeddings")
RESULTS_DIR = Path("results/tables")

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
    "rf":     {"n_estimators": 100, "max_depth": None, "n_jobs": -1},
    "mlp":    {"hidden_layer_sizes": (256,), "max_iter": 100, "alpha": 1e-3, "early_stopping": True},
    "resmlp": {"hidden_dim": 256, "n_blocks": 3, "dropout": 0.1, "max_epochs": 100, "patience": 10, "batch_size": 256},
}

CV_SPLITS = 5
CV_SEED = 42


def normalize_l2(X: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return X / norms


def make_clf(name: str):
    p = CLF_PARAMS[name]
    if name == "svm":
        return SVC(**p)
    if name == "knn":
        return KNeighborsClassifier(**p)
    if name == "rf":
        return RandomForestClassifier(random_state=CV_SEED, **p)
    if name == "mlp":
        return MLPClassifier(random_state=CV_SEED, **p)
    if name == "resmlp":
        return ResMLPClassifier(random_state=CV_SEED, **p)
    raise ValueError(name)


def load_embeddings(dataset: str, extractor: str):
    base = EMBEDDINGS_ROOT / dataset
    emb = np.load(base / f"{extractor}.npy")
    labels = np.load(base / f"{extractor}_labels.npy")
    with open(base / f"{extractor}_classes.json") as f:
        classes = json.load(f)
    return emb, labels, classes


def evaluate_one(emb: np.ndarray, labels: np.ndarray, clf_name: str) -> dict:
    le = LabelEncoder()
    y = le.fit_transform(labels)
    skf = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_SEED)
    splits = list(skf.split(emb, y))
    accs, f1s = [], []
    for tr_idx, te_idx in splits:
        X_tr, X_te = emb[tr_idx], emb[te_idx]
        y_tr, y_te = y[tr_idx], y[te_idx]
        try:
            clf = make_clf(clf_name)
            clf.fit(X_tr, y_tr)
            y_pred = clf.predict(X_te)
            accs.append(accuracy_score(y_te, y_pred))
            f1s.append(f1_score(y_te, y_pred, average="macro"))
        except Exception as e:
            print(f"      [ERR] {clf_name} fold: {e}")
            accs.append(0.0)
            f1s.append(0.0)
    return {
        "mean_accuracy": float(np.mean(accs)),
        "std_accuracy": float(np.std(accs)),
        "mean_f1": float(np.mean(f1s)),
        "std_f1": float(np.std(f1s)),
        "per_fold_f1": f1s,
        "per_fold_acc": accs,
    }


def load_existing_keys(dataset: str) -> set:
    p = RESULTS_DIR / f"perfold_{dataset}.jsonl"
    if not p.exists():
        return set()
    keys = set()
    with open(p) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            keys.add((r["extractor"], r["clf"]))
    return keys


def main():
    print(f"Exp 1 (individual) — 17 extractors × 4 clfs × 6 datasets")
    print(f"Solo corre combinaciones faltantes\n")

    grand_new = 0
    for dataset in DATASETS:
        existing = load_existing_keys(dataset)
        needed = set((e, c) for e in EXTRACTORS for c in CLFS)
        missing = needed - existing
        if not missing:
            print(f"=== {dataset}: ya completo ({len(existing)}/{len(needed)}) ===")
            continue
        print(f"=== {dataset}: {len(missing)}/{len(needed)} faltantes ===")

        # Cargar todas las embeddings una vez (cache)
        emb_cache = {}
        for ext in EXTRACTORS:
            try:
                emb, labels, classes = load_embeddings(dataset, ext)
                emb_cache[ext] = (emb, labels, classes)
            except FileNotFoundError:
                print(f"  [SKIP embedding] {ext} no existe")
                continue

        new_rows = []
        for ext, clf_name in sorted(missing):
            if ext not in emb_cache:
                continue
            emb, labels, classes = emb_cache[ext]
            emb_n = normalize_l2(emb)
            t0 = time.time()
            r = evaluate_one(emb_n, labels, clf_name)
            elapsed = time.time() - t0
            row = {
                "dataset": dataset, "extractor": ext, "clf": clf_name,
                "n_samples": int(emb.shape[0]), "n_classes": len(classes),
                "emb_dim": int(emb.shape[1]),
                "mean_accuracy": r["mean_accuracy"],
                "std_accuracy": r["std_accuracy"],
                "mean_f1": r["mean_f1"],
                "std_f1": r["std_f1"],
                "best_params": str(CLF_PARAMS[clf_name]),
                "time_s": round(elapsed, 1),
                "per_fold_f1": r["per_fold_f1"],
                "per_fold_acc": r["per_fold_acc"],
            }
            new_rows.append(row)
            print(f"  {ext:18s} + {clf_name:5s}  f1={r['mean_f1']:.3f}±{r['std_f1']:.3f}  ({elapsed:.1f}s)")

        # Append a perfold JSONL
        if new_rows:
            p = RESULTS_DIR / f"perfold_{dataset}.jsonl"
            with open(p, "a") as f:
                for r in new_rows:
                    f.write(json.dumps({
                        "dataset": r["dataset"], "extractor": r["extractor"], "clf": r["clf"],
                        "per_fold_f1": r["per_fold_f1"], "per_fold_acc": r["per_fold_acc"],
                    }) + "\n")
            # Append a baseline CSV (sin columnas de fold)
            csv_p = RESULTS_DIR / f"baseline_{dataset}.csv"
            csv_cols = ["dataset", "extractor", "clf", "n_samples", "n_classes", "emb_dim",
                        "mean_accuracy", "std_accuracy", "mean_f1", "std_f1", "best_params", "time_s"]
            df_new = pd.DataFrame(new_rows)[csv_cols]
            if csv_p.exists():
                df_new.to_csv(csv_p, mode="a", header=False, index=False)
            else:
                df_new.to_csv(csv_p, index=False)
            print(f"  -> {len(new_rows)} nuevas filas guardadas en {p.name} y {csv_p.name}\n")
            grand_new += len(new_rows)

    # Re-generar perfold_all.jsonl y baseline_summary.csv consolidados
    print(f"=== Regenerando consolidados ===")
    all_rows_perf = []
    all_rows_csv = []
    for dataset in DATASETS:
        p = RESULTS_DIR / f"perfold_{dataset}.jsonl"
        if not p.exists():
            continue
        for line in open(p):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            all_rows_perf.append(r)
        b = RESULTS_DIR / f"baseline_{dataset}.csv"
        if b.exists():
            df = pd.read_csv(b)
            all_rows_csv.append(df)

    with open(RESULTS_DIR / "perfold_all.jsonl", "w") as f:
        for r in all_rows_perf:
            f.write(json.dumps(r) + "\n")
    if all_rows_csv:
        df_all = pd.concat(all_rows_csv, ignore_index=True)
        csv_cols = ["dataset", "extractor", "clf", "n_samples", "n_classes", "emb_dim",
                    "mean_accuracy", "std_accuracy", "mean_f1", "std_f1", "best_params", "time_s"]
        df_all[csv_cols].to_csv(RESULTS_DIR / "baseline_summary.csv", index=False)

    print(f"[OK] Total nuevas filas: {grand_new}")
    print(f"[OK] perfold_all.jsonl: {len(all_rows_perf)} filas")
    print(f"[OK] baseline_summary.csv: {len(df_all)} filas")


if __name__ == "__main__":
    main()
