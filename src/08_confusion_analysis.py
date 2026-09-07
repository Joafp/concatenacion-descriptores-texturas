"""
08_confusion_analysis.py
=========================
Genera matrices de confusión agregadas (5-fold) para cada dataset,
comparando 3 estrategias:
  1. Mejor extractor individual (dinov2 o vit_b16 según dataset)
  2. Mejor subset GFS (k=2 a k=7 según dataset)
  3. Concat completo (k=12, todos los extractores)

Genera:
  - results/figures/confusion_{dataset}_{strategy}.png  (heatmap normalizado)
  - results/figures/confusion_compare_{dataset}.png  (3 subplots lado a lado)
  - results/tables/confusion_perclass.csv  (precision/recall por clase y estrategia)
  - results/tables/confusion_pairs.csv  (pares de clases más confundidas)
"""

import json
import warnings
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

warnings.filterwarnings("ignore")

EMBEDDINGS_ROOT = Path("embeddings")
RESULTS_DIR = Path("results")
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

CV_SPLITS = 5
CV_SEED = 42

# Estrategia por dataset: (nombre_estrategia, lista_extractores_o_None, descripción)
STRATEGIES_PER_DATASET = {
    "DTD": {
        "Mejor individual": ("dinov2", None, "Linear probing sobre DINOv2"),
        "GFS subset": ("dinov2,resnet50,glcm", "dinov2 + ResNet-50 + GLCM"),
        "Full concat": ("all", "12 extractores (k=12)"),
    },
    "FMD": {
        "Mejor individual": ("dinov2", None, "Linear probing sobre DINOv2"),
        "GFS subset": ("dinov2,convnext_v2_t", "DINOv2 + ConvNeXt V2-T (k=2)"),
        "Full concat": ("all", "12 extractores (k=12)"),
    },
    "KTH-TIPS2": {
        "Mejor individual": ("convnext_v2_t", None, "ConvNeXt V2-T (saturado)"),
        "GFS subset": ("dinov2,swin_t,resnet50", "DINOv2 + Swin-T + ResNet-50"),
        "Full concat": ("all", "12 extractores (k=12)"),
    },
    "HVD_glaucoma": {
        "Mejor individual": ("vit_b16", None, "Linear probing sobre ViT-B/16"),
        "GFS subset": ("swin_t,deit_s,convnext_v2_t,vit_b16,resnet50,gabor,glcm", "GFS 7-ext (swin+deit+convnext+vit+resnet+gabor+glcm)"),
        "Full concat": ("all", "12 extractores (k=12)"),
    },
    "ocular_toxoplasmosis": {
        "Mejor individual": ("dinov2", None, "Linear probing sobre DINOv2"),
        "GFS subset": ("swin_t,deit_s,convnext_v2_t,efficientnet_b0,gabor", "GFS 5-ext (swin+deit+convnext+effnet+gabor)"),
        "Full concat": ("all", "12 extractores (k=12)"),
    },
}

ALL_EXTRACTORS = [
    "vit_b16", "swin_t", "deit_s", "dinov2",
    "resnet50", "convnext_v2_t", "efficientnet_b0",
    "lbp", "glcm", "gabor", "hog", "drlbp",
]

CLF_PARAMS = {
    "svm": {"kernel": "linear", "C": 1.0},
}


def load_embeddings(dataset, extractor):
    base = EMBEDDINGS_ROOT / dataset
    emb = np.load(base / f"{extractor}.npy")
    labels = np.load(base / f"{extractor}_labels.npy")
    with open(base / f"{extractor}_classes.json") as f:
        classes = json.load(f)
    return emb, labels, classes


def normalize_l2(X):
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return X / norms


def make_clf():
    return SVC(**CLF_PARAMS["svm"])


def predict_with_cv(emb_list, labels, n_classes, classes):
    """5-fold CV. Devuelve (y_true_concat, y_pred_concat, f1_mean, acc_mean)."""
    le = LabelEncoder()
    y = le.fit_transform(labels)
    skf = StratifiedKFold(n_splits=CV_SPLITS, shuffle=True, random_state=CV_SEED)
    y_true_all, y_pred_all = [], []
    for tr_idx, te_idx in skf.split(emb_list[0], y):
        X_tr = np.concatenate([normalize_l2(e[tr_idx]) for e in emb_list], axis=1)
        X_te = np.concatenate([normalize_l2(e[te_idx]) for e in emb_list], axis=1)
        clf = make_clf()
        clf.fit(X_tr, y[tr_idx])
        preds = clf.predict(X_te)
        y_true_all.append(y[te_idx])
        y_pred_all.append(preds)
    y_true_all = np.concatenate(y_true_all)
    y_pred_all = np.concatenate(y_pred_all)
    f1 = f1_score(y_true_all, y_pred_all, average="macro")
    acc = accuracy_score(y_true_all, y_pred_all)
    return y_true_all, y_pred_all, f1, acc


def make_confusion_figure(y_true, y_pred, classes, dataset, strategy, f1, acc, out_path):
    """Genera heatmap normalizado por fila (recall per class)."""
    n = len(classes)
    cm = confusion_matrix(y_true, y_pred, labels=list(range(n)))
    # Normalizar por fila (recall)
    row_sums = cm.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1, row_sums)
    cm_norm = cm / row_sums

    fig, ax = plt.subplots(figsize=(max(6, n * 0.6), max(5, n * 0.55)))
    im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    if n > 20:
        # Si hay muchas clases, rotar labels
        ax.set_xticklabels(classes, rotation=90, fontsize=7)
        ax.set_yticklabels(classes, fontsize=7)
    else:
        ax.set_xticklabels(classes, rotation=45, ha="right", fontsize=9)
        ax.set_yticklabels(classes, fontsize=9)
    # Anotar celdas con valor si > 0.05
    for i in range(n):
        for j in range(n):
            v = cm_norm[i, j]
            if v > 0.05:
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        color="white" if v > 0.5 else "black", fontsize=7)
    ax.set_xlabel("Predicho")
    ax.set_ylabel("Real")
    ax.set_title(f"{dataset} — {strategy}\nF1={f1:.3f}, Acc={acc:.3f}")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Recall")
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()


def make_compare_figure(per_strategy_results, classes, dataset, out_path):
    """Compara 3 estrategias lado a lado."""
    n = len(classes)
    n_strats = len(per_strategy_results)
    fig, axes = plt.subplots(1, n_strats, figsize=(5.5 * n_strats, 5.5), squeeze=False)
    for idx, (strategy, (y_true, y_pred, f1, acc)) in enumerate(per_strategy_results.items()):
        ax = axes[0][idx]
        cm = confusion_matrix(y_true, y_pred, labels=list(range(n)))
        row_sums = cm.sum(axis=1, keepdims=True)
        row_sums = np.where(row_sums == 0, 1, row_sums)
        cm_norm = cm / row_sums
        im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        if n > 20:
            ax.set_xticklabels(classes, rotation=90, fontsize=6)
            ax.set_yticklabels(classes, fontsize=6)
        else:
            ax.set_xticklabels(classes, rotation=45, ha="right", fontsize=7)
            ax.set_yticklabels(classes, fontsize=7)
        for i in range(n):
            for j in range(n):
                v = cm_norm[i, j]
                if v > 0.05:
                    ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                            color="white" if v > 0.5 else "black", fontsize=6)
        ax.set_xlabel("Predicho")
        ax.set_ylabel("Real" if idx == 0 else "")
        ax.set_title(f"{strategy}\nF1={f1:.3f}")
    plt.suptitle(f"Comparación de estrategias: {dataset}", y=1.02, fontsize=12)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close()


def analyze_confusions(y_true, y_pred, classes):
    """Identifica pares de clases más confundidos y per-class precision/recall."""
    n = len(classes)
    cm = confusion_matrix(y_true, y_pred, labels=list(range(n)))
    # Pares confundidos: off-diagonal normalizado por row sum
    pairs = []
    for i in range(n):
        row_total = cm[i].sum()
        if row_total == 0:
            continue
        for j in range(n):
            if i == j or cm[i, j] == 0:
                continue
            rate = cm[i, j] / row_total
            pairs.append({
                "true_class": classes[i],
                "pred_class": classes[j],
                "count": int(cm[i, j]),
                "row_total": int(row_total),
                "rate": rate,
            })
    pairs.sort(key=lambda x: -x["rate"])

    # Per-class metrics
    prec, rec, f1, sup = precision_recall_fscore_support(y_true, y_pred, labels=list(range(n)))
    perclass = []
    for i in range(n):
        perclass.append({
            "class": classes[i],
            "support": int(sup[i]),
            "precision": float(prec[i]),
            "recall": float(rec[i]),
            "f1": float(f1[i]),
        })
    return pairs, perclass


def main():
    all_perclass = []
    all_pairs = []

    for dataset, strategies in STRATEGIES_PER_DATASET.items():
        print(f"\n=== Dataset: {dataset} ===")
        # Cargar labels y classes
        _, labels, classes = load_embeddings(dataset, "dinov2")
        n_classes = len(classes)
        print(f"  {len(labels)} samples, {n_classes} classes: {classes[:5]}{'...' if n_classes>5 else ''}")

        per_strategy = {}

        for strat_name, spec_tuple in strategies.items():
            # Tuple puede ser (extractor_spec, descr) o solo (extractor_spec)
            if len(spec_tuple) == 2:
                extractor_spec, descr = spec_tuple
            else:
                extractor_spec = spec_tuple[0]
                descr = spec_tuple[1] if len(spec_tuple) > 1 else ""
            if extractor_spec == "all":
                exts = ALL_EXTRACTORS
            else:
                exts = [e.strip() for e in extractor_spec.split(",")]
            try:
                emb_list = [load_embeddings(dataset, e)[0] for e in exts]
            except FileNotFoundError as ex:
                print(f"  [SKIP] {strat_name}: {ex}")
                continue
            y_true, y_pred, f1, acc = predict_with_cv(emb_list, labels, n_classes, classes)
            per_strategy[strat_name] = (y_true, y_pred, f1, acc)
            print(f"  {strat_name:20s}  F1={f1:.3f}  Acc={acc:.3f}  (dim={sum(e.shape[1] for e in emb_list)})")
            # Figura individual
            make_confusion_figure(
                y_true, y_pred, classes, dataset, strat_name, f1, acc,
                FIGURES_DIR / f"confusion_{dataset}_{strat_name.replace(' ', '_')}.png"
            )
            # Análisis de confusiones para esta estrategia
            pairs, perclass = analyze_confusions(y_true, y_pred, classes)
            for p in pairs[:3]:
                all_pairs.append({
                    "dataset": dataset, "strategy": strat_name, **p
                })
            for pc in perclass:
                all_pc_row = {"dataset": dataset, "strategy": strat_name, **pc}
                all_perclass.append(all_pc_row)
            # Mostrar top confusiones
            print(f"    Top confusiones:")
            for p in pairs[:3]:
                print(f"      {p['true_class']:20s} → {p['pred_class']:20s}  {p['count']:3d}/{p['row_total']:3d} ({p['rate']*100:.0f}%)")
            worst = sorted(perclass, key=lambda x: x["f1"])[:3]
            print(f"    Peores clases (F1):")
            for wc in worst:
                print(f"      {wc['class']:20s}  F1={wc['f1']:.3f}  P={wc['precision']:.3f}  R={wc['recall']:.3f}  (n={wc['support']})")

        # Figura comparativa
        if per_strategy:
            make_compare_figure(per_strategy, classes, dataset,
                                FIGURES_DIR / f"confusion_compare_{dataset}.png")
            print(f"  -> {FIGURES_DIR}/confusion_compare_{dataset}.png")

    # Guardar tablas
    if all_perclass:
        pd.DataFrame(all_perclass).to_csv(TABLES_DIR / "confusion_perclass.csv", index=False)
        print(f"\n=== Per-class metrics: results/tables/confusion_perclass.csv ===")
    if all_pairs:
        pd.DataFrame(all_pairs).to_csv(TABLES_DIR / "confusion_pairs.csv", index=False)
        print(f"=== Top confusion pairs: results/tables/confusion_pairs.csv ===")
        # Mostrar top 5
        df = pd.DataFrame(all_pairs)
        print("\nTop 10 confusiones en toda la tesis:")
        print(df.head(10)[["dataset", "strategy", "true_class", "pred_class", "count", "row_total", "rate"]].to_string(index=False))


if __name__ == "__main__":
    main()
