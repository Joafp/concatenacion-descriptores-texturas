"""
02_baseline_individual.py
=========================
Para cada (dataset, extractor) ejecuta linear probing con SVM, KNN, RF y MLP
usando 5-fold stratified cross-validation. Reporta accuracy + macro-F1.

Lee embeddings de embeddings/{dataset}/{extractor}.npy
Guarda resultados en results/tables/baseline_{dataset}.csv
Más un summary consolidado en results/tables/baseline_summary.csv
"""

import argparse
import json
import sys
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

sys.path.insert(0, str(Path(__file__).parent))
from resmlp_classifier import ResMLPClassifier

warnings.filterwarnings("ignore")  # silencia ConvergenceWarning de SVM


# ---------------- Configuración ----------------

EMBEDDINGS_ROOT = Path("embeddings")
RESULTS_DIR = Path("results/tables")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# 6 datasets de texturas (medical removido)
DATASETS = ["DTD", "FMD", "CUReT", "Soil", "VisTex"]
EXTRACTORS = [
    # ViTs (4)
    "vit_b16", "swin_t", "deit_s",
    # DINOv2 family (3 small/med/large)
    "dinov2_small", "dinov2", "dinov2_large",
    # SOTA 2024 (3: EVA-02, MAE, SigLIP)
    "eva02_base", "mae_base", "siglip_base",
    # CNNs (5: VGG16, ResNet50, ResNet101, DenseNet121, EfficientNet, ConvNeXt V2-T)
    "vgg16", "resnet50", "resnet101", "densenet121",
    "efficientnet_b0", "convnext_v2_t",
    # Clásicos (5)
    "lbp", "glcm", "gabor", "hog", "drlbp",
]

# Hiperparámetros por clasificador (single-config, optimizados para velocidad)
# Para Exp 1, queremos encontrar el mejor (extractor, clasificador) con defaults razonables.
# Hiperparámetros justificados en Cap. 5.11.6 del manuscrito anterior.
CLF_PARAMS = {
    "svm":   {"kernel": "linear", "C": 1.0},
    "knn":   {"n_neighbors": 5, "weights": "distance"},
    "rf":    {"n_estimators": 100, "max_depth": None, "n_jobs": -1},
    "mlp":   {"hidden_layer_sizes": (256,), "max_iter": 100, "alpha": 1e-3, "early_stopping": True},
    "resmlp":{"hidden_dim": 256, "n_blocks": 3, "dropout": 0.1, "max_epochs": 100, "patience": 10, "batch_size": 256},
}

CV_SPLITS = 5
CV_SEED = 42


def load_embeddings(dataset: str, extractor: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    base = EMBEDDINGS_ROOT / dataset
    emb = np.load(base / f"{extractor}.npy")
    labels = np.load(base / f"{extractor}_labels.npy")
    with open(base / f"{extractor}_classes.json") as f:
        classes = json.load(f)
    return emb, labels, classes


def normalize_l2(X: np.ndarray) -> np.ndarray:
    """L2 normalize por fila (cada embedding a unit norm)."""
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return X / norms


def make_clf(name: str, **kwargs):
    if name == "svm":
        return SVC(**kwargs)
    if name == "knn":
        return KNeighborsClassifier(**kwargs)
    if name == "rf":
        return RandomForestClassifier(random_state=CV_SEED, **kwargs)
    if name == "mlp":
        return MLPClassifier(random_state=CV_SEED, **kwargs)
    if name == "resmlp":
        return ResMLPClassifier(random_state=CV_SEED, **kwargs)
    raise ValueError(name)


def grid_iter(grid: dict):
    """Iterador dummy: retorna una sola combinación (sin grid search)."""
    yield grid


def evaluate_one(emb: np.ndarray, labels: np.ndarray, clf_name: str) -> dict:
    """5-fold CV con hiperparámetros fijos. Devuelve mean macro-F1."""
    le = LabelEncoder()
    y = le.fit_transform(labels)

    skf = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_SEED)
    splits = list(skf.split(emb, y))

    accs, f1s = [], []
    for tr_idx, te_idx in splits:
        X_tr, X_te = emb[tr_idx], emb[te_idx]
        y_tr, y_te = y[tr_idx], y[te_idx]
        try:
            clf = make_clf(clf_name, **CLF_PARAMS[clf_name])
            clf.fit(X_tr, y_tr)
            y_pred = clf.predict(X_te)
            accs.append(accuracy_score(y_te, y_pred))
            f1s.append(f1_score(y_te, y_pred, average="macro"))
        except Exception as e:
            accs.append(0.0)
            f1s.append(0.0)

    return {
        "clf": clf_name,
        "best_params": CLF_PARAMS[clf_name],
        "mean_accuracy": float(np.mean(accs)),
        "std_accuracy": float(np.std(accs)),
        "mean_f1": float(np.mean(f1s)),
        "std_f1": float(np.std(f1s)),
        "per_fold_f1": f1s,            # lista de 5 f1 (uno por fold)
        "per_fold_acc": accs,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=DATASETS)
    parser.add_argument("--extractors", nargs="+", default=EXTRACTORS)
    parser.add_argument("--clfs", nargs="+", default=["svm", "knn", "rf", "resmlp"])
    parser.add_argument("--no-normalize", action="store_true",
                        help="Skip L2 normalization (no recomendado para concatenar)")
    args = parser.parse_args()

    print(f"Config: datasets={args.datasets}, extractors={args.extractors}, clfs={args.clfs}, l2_norm={not args.no_normalize}\n")

    all_results = []

    for dataset in args.datasets:
        print(f"=== Dataset: {dataset} ===")
        ds_results = []
        for extractor in args.extractors:
            try:
                emb, labels, classes = load_embeddings(dataset, extractor)
            except FileNotFoundError as e:
                print(f"  [SKIP] {extractor}: {e}")
                continue
            if not args.no_normalize:
                emb = normalize_l2(emb)

            for clf_name in args.clfs:
                t0 = time.time()
                r = evaluate_one(emb, labels, clf_name)
                elapsed = time.time() - t0
                r["dataset"] = dataset
                r["extractor"] = extractor
                r["n_samples"] = int(emb.shape[0])
                r["n_classes"] = len(classes)
                r["emb_dim"] = int(emb.shape[1])
                r["time_s"] = round(elapsed, 1)
                ds_results.append(r)
                all_results.append(r)
                print(f"  {extractor:10s} + {clf_name:4s}  acc={r['mean_accuracy']:.3f}±{r['std_accuracy']:.3f}  f1={r['mean_f1']:.3f}±{r['std_f1']:.3f}  ({elapsed:.1f}s)")

        # Per-dataset CSV (sin per_fold por JSON-safety)
        if ds_results:
            df = pd.DataFrame(ds_results)
            cols = ["dataset", "extractor", "clf", "n_samples", "n_classes", "emb_dim",
                    "mean_accuracy", "std_accuracy", "mean_f1", "std_f1", "best_params", "time_s"]
            df[cols].to_csv(RESULTS_DIR / f"baseline_{dataset}.csv", index=False)
            # Per-fold scores: archivo JSONL (1 línea por (ext, clf))
            with open(RESULTS_DIR / f"perfold_{dataset}.jsonl", "w") as fp:
                for r in ds_results:
                    fp.write(json.dumps({
                        "dataset": r["dataset"], "extractor": r["extractor"], "clf": r["clf"],
                        "per_fold_f1": r["per_fold_f1"], "per_fold_acc": r["per_fold_acc"],
                    }) + "\n")
            print(f"  -> Saved results/tables/baseline_{dataset}.csv + perfold_{dataset}.jsonl\n")

    # Summary consolidado
    if all_results:
        df = pd.DataFrame(all_results)
        cols = ["dataset", "extractor", "clf", "n_samples", "n_classes", "emb_dim",
                "mean_accuracy", "std_accuracy", "mean_f1", "std_f1", "best_params", "time_s"]
        df[cols].to_csv(RESULTS_DIR / "baseline_summary.csv", index=False)
        # Per-fold consolidado
        with open(RESULTS_DIR / "perfold_all.jsonl", "w") as fp:
            for r in all_results:
                fp.write(json.dumps({
                    "dataset": r["dataset"], "extractor": r["extractor"], "clf": r["clf"],
                    "per_fold_f1": r["per_fold_f1"], "per_fold_acc": r["per_fold_acc"],
                }) + "\n")
        print(f"=== Summary: results/tables/baseline_summary.csv + perfold_all.jsonl ===")
        # Pivot: mejores por (dataset, extractor)
        print("\nMejor macro-F1 por (dataset, extractor):")
        best = df.loc[df.groupby(["dataset", "extractor"])["mean_f1"].idxmax()]
        pivot = best.pivot(index="dataset", columns="extractor", values="mean_f1")
        print(pivot.round(3).to_string())


if __name__ == "__main__":
    main()
