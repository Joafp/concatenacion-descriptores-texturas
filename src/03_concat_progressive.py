"""
03_concat_progressive.py
=========================
Concatena embeddings progresivamente en orden canónico y mide la métrica
en cada paso. Genera las curvas de saturación del Cap. 4.

Orden canónico: [LBP, GLCM, Gabor, HOG, DRLBP, ConvNeXt V2-T, EfficientNet-B0,
                  ViT-B/16, Swin-T, DeiT-S, VMamba-T]
(Fase 1 ViTs: solo se incluyen los 3 ViTs disponibles — el resto se saltan con warning)

Curvas generadas:
  results/figures/saturation_{dataset}_{clf}.png
  results/tables/concat_{dataset}.csv
  results/tables/concat_summary.csv
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
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

sys.path.insert(0, str(Path(__file__).parent))
from resmlp_classifier import ResMLPClassifier

warnings.filterwarnings("ignore")


# ---------------- Configuración ----------------

EMBEDDINGS_ROOT = Path("embeddings")
RESULTS_DIR = Path("results")
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Orden canónico de extractores
# Narrativa: de clásico → CNN → ViT → SSL-ViT (de simple a complejo, supervisado → self-supervised)
CANONICAL_ORDER = [
    "lbp",              # Clásico 1: LBP multi-escala
    "glcm",             # Clásico 2: GLCM
    "gabor",            # Clásico 3: Gabor
    "hog",              # Clásico 4: HOG
    "drlbp",            # Clásico 5: DRLBP
    "vgg16",            # CNN 1: VGG16 (clásico)
    "resnet50",         # CNN 2: ResNet-50
    "resnet101",        # CNN 3: ResNet-101
    "densenet121",      # CNN 4: DenseNet-121
    "convnext_v2_t",    # CNN 5: ConvNeXt V2-T (moderno + SSL)
    "efficientnet_b0",  # CNN 6: EfficientNet-B0
    "vit_b16",          # ViT 1: ViT-B/16 (supervisado)
    "swin_t",           # ViT 2: Swin-T (jerárquico)
    "deit_s",           # ViT 3: DeiT-S (distillation)
    "dinov2_small",     # SSL 1: DINOv2-S (384d)
    "dinov2",           # SSL 2: DINOv2-B (768d)
    "dinov2_large",     # SSL 3: DINOv2-L (1024d)
]

DATASETS = ["DTD", "FMD", "CUReT", "Soil", "VisTex"]

# Hiperparámetros fijos (los best del baseline)
# Para SVM, usamos linear porque con dim > 2000 el rbf se vuelve prohibitivamente lento
# y la performance de linear en alta dim suele ser similar o mejor
BEST_PARAMS = {
    "svm":    {"kernel": "linear", "C": 1.0},
    "knn":    {"n_neighbors": 5, "weights": "distance"},
    "rf":     {"n_estimators": 300, "max_depth": None},
    "mlp":    {"hidden_layer_sizes": (256,), "max_iter": 100, "alpha": 1e-3, "early_stopping": True},
    "resmlp": {"hidden_dim": 256, "n_blocks": 3, "dropout": 0.1, "max_epochs": 100, "patience": 10, "batch_size": 256},
}

CV_SPLITS = 5
CV_SEED = 42


def load_embeddings(dataset: str, extractor: str) -> tuple[np.ndarray, np.ndarray]:
    base = EMBEDDINGS_ROOT / dataset
    emb = np.load(base / f"{extractor}.npy")
    labels = np.load(base / f"{extractor}_labels.npy")
    return emb, labels


def normalize_l2(X: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return X / norms


def make_clf(name: str):
    if name == "svm":
        return SVC(**BEST_PARAMS["svm"])
    if name == "knn":
        return KNeighborsClassifier(**BEST_PARAMS["knn"])
    if name == "rf":
        return RandomForestClassifier(random_state=CV_SEED, n_jobs=-1, **BEST_PARAMS["rf"])
    if name == "mlp":
        return MLPClassifier(random_state=CV_SEED, **BEST_PARAMS["mlp"])
    if name == "resmlp":
        return ResMLPClassifier(random_state=CV_SEED, **BEST_PARAMS["resmlp"])
    raise ValueError(name)


def evaluate_concat(emb_list: list[np.ndarray], labels: np.ndarray, clf_name: str) -> dict:
    le = LabelEncoder()
    y = le.fit_transform(labels)
    skf = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_SEED)
    accs, f1s = [], []
    for tr_idx, te_idx in skf.split(emb_list[0], y):
        # Concatenar SOLO en train y test (no pre-concatenar)
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
        "per_fold_acc": accs,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=DATASETS)
    parser.add_argument("--extractors", nargs="+", default=CANONICAL_ORDER)
    parser.add_argument("--clfs", nargs="+", default=["svm", "knn", "rf", "mlp", "resmlp"])
    args = parser.parse_args()

    print(f"Orden canónico: {args.extractors}")
    print(f"Datasets: {args.datasets}")
    print(f"Clfs: {args.clfs}\n")

    all_results = []

    for dataset in args.datasets:
        print(f"=== Dataset: {dataset} ===")
        # Cargar todos los embeddings disponibles
        available = []
        for ext in args.extractors:
            try:
                emb, lab = load_embeddings(dataset, ext)
                available.append((ext, emb, lab))
            except FileNotFoundError:
                print(f"  [WARN] {ext} no disponible para {dataset}, se omite")
        if not available:
            print(f"  [SKIP] Sin embeddings, saltando {dataset}\n")
            continue

        ds_results = []
        # Curva: para k=1..N, concatenar primeros k
        for k in range(1, len(available) + 1):
            subset = available[:k]
            emb_list = [e[1] for e in subset]
            label = subset[0][2]  # labels son los mismos
            dim = sum(e.shape[1] for e in emb_list)
            descr = " + ".join(s[0] for s in subset)
            for clf_name in args.clfs:
                t0 = time.time()
                r = evaluate_concat(emb_list, label, clf_name)
                elapsed = time.time() - t0
                row = {
                    "dataset": dataset,
                    "k": k,
                    "extractors": descr,
                    "clf": clf_name,
                    "dim": dim,
                    "mean_accuracy": r["mean_accuracy"],
                    "std_accuracy": r["std_accuracy"],
                    "mean_f1": r["mean_f1"],
                    "std_f1": r["std_f1"],
                    "time_s": round(elapsed, 1),
                }
                ds_results.append(row)
                all_results.append(row)
                print(f"  k={k} [{descr:30s}] {clf_name:4s}  f1={r['mean_f1']:.3f}±{r['std_f1']:.3f}  ({elapsed:.1f}s)")

        # CSV per dataset
        if ds_results:
            pd.DataFrame(ds_results).to_csv(TABLES_DIR / f"concat_{dataset}.csv", index=False)
            # Per-fold para diff sig
            with open(TABLES_DIR / f"perfold_concat_{dataset}.jsonl", "w") as fp:
                for r in ds_results:
                    fp.write(json.dumps({
                        "dataset": r["dataset"], "k": r["k"], "extractors": r["extractors"],
                        "clf": r["clf"], "per_fold_f1": r["per_fold_f1"],
                    }) + "\n")
            print(f"  -> Saved results/tables/concat_{dataset}.csv + perfold_concat_{dataset}.jsonl")

        # Figura: 1 por dataset, 3 curvas (1 por clf)
        if ds_results:
            fig, ax = plt.subplots(figsize=(8, 5))
            for clf_name in args.clfs:
                sub = [r for r in ds_results if r["clf"] == clf_name]
                ks = [r["k"] for r in sub]
                f1s = [r["mean_f1"] for r in sub]
                f1s_std = [r["std_f1"] for r in sub]
                ax.plot(ks, f1s, marker="o", label=f"{clf_name}", linewidth=2)
                ax.fill_between(ks,
                                [f - s for f, s in zip(f1s, f1s_std)],
                                [f + s for f, s in zip(f1s, f1s_std)],
                                alpha=0.15)
            ax.set_xlabel("k = # extractores concatenados")
            ax.set_ylabel("macro-F1 (5-fold CV)")
            ax.set_title(f"Saturación por concatenación: {dataset}")
            ax.set_xticks(range(1, len(available) + 1))
            ax.set_xticklabels([f"{i+1}\n{'+'.join(s[0].split('_')[0] for s in available[:i+1])}" for i in range(len(available))],
                               rotation=0, fontsize=8)
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 1.05)
            plt.tight_layout()
            out_path = FIGURES_DIR / f"saturation_{dataset}.png"
            plt.savefig(out_path, dpi=120)
            plt.close()
            print(f"  -> Saved {out_path}\n")

    # Summary consolidado
    if all_results:
        pd.DataFrame(all_results).to_csv(TABLES_DIR / "concat_summary.csv", index=False)
        print(f"=== Summary: results/tables/concat_summary.csv ===")

        # Tabla pivot: mejor f1 por (dataset, k)
        df = pd.DataFrame(all_results)
        best_per_k = df.loc[df.groupby(["dataset", "k"])["mean_f1"].idxmax()]
        pivot = best_per_k.pivot(index="dataset", columns="k", values="mean_f1")
        print("\nMejor macro-F1 por (dataset, k):")
        print(pivot.round(3).to_string())


if __name__ == "__main__":
    main()
