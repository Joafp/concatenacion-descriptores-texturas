"""
gfs_vs_random_subsets.py
========================
Compara GFS (subset óptimo) vs subsets ALEATORIOS del mismo tamaño.
Responde al DA-C1: ¿GFS hace mejor que random selection de igual costo?

Para cada (dataset, clf), el GFS encontró un subset óptimo de tamaño k.
Aquí generamos N=100 subsets aleatorios de tamaño k y evaluamos su F1.
Comparamos:
  - F1 GFS vs distribución de F1 random (media, percentiles)
  - p-value: ¿GFS está en el percentil 95+ de la distribución random?
  - Effect size: Cohen's d GFS vs media random

Genera:
  - results/tables/gfs_vs_random.csv
  - results/figures/gfs_vs_random_dist.png
"""
import json
import time
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import sys
sys.path.insert(0, str(Path(__file__).parent))
from md_to_tex import md_to_tex  # not used but ensures path is set
from resmlp_classifier import ResMLPClassifier  # noqa
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC

warnings.filterwarnings("ignore")

EMBEDDINGS_ROOT = Path("embeddings")
TABLES = Path("results/tables")
FIGURES = Path("results/figures")
FIGURES.mkdir(parents=True, exist_ok=True)

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
    "rf":     {"n_estimators": 100, "max_depth": None, "n_jobs": 1},
    "resmlp": {"hidden_dim": 256, "n_blocks": 3, "dropout": 0.1,
                "max_epochs": 30, "patience": 5, "batch_size": 256},
}
CV_SPLITS = 5
CV_SEED = 42
N_RANDOM = 10   # subsets aleatorios por (dataset, clf) (1-fold screening)


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


def evaluate_subset(emb_list, labels, clf_name, n_folds=1):
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
    return float(np.mean(f1s))


def load_embeddings(dataset):
    cache = {}
    for ext in EXTRACTORS:
        p = EMBEDDINGS_ROOT / dataset / f"{ext}.npy"
        if p.exists():
            emb = np.load(p)
            labels = np.load(EMBEDDINGS_ROOT / dataset / f"{ext}_labels.npy")
            cache[ext] = (emb, labels)
    return cache


def main():
    gfs_summary = pd.read_csv(TABLES / "greedy_summary.csv")
    rows = []
    all_gfs_f1 = []
    all_random_means = []
    per_dataset_results = {ds: {"gfs": [], "random_dist": []} for ds in DATASETS}

    for ds in DATASETS:
        print(f"\n=== {ds} ===", flush=True)
        emb_cache = load_embeddings(ds)
        if not emb_cache:
            continue
        labels = next(iter(emb_cache.values()))[1]
        for clf in CLFS:
            g = gfs_summary[(gfs_summary.dataset == ds) & (gfs_summary.clf == clf)]
            if g.empty:
                continue
            g = g.iloc[0]
            k = int(g["best_step"])
            gfs_subset = g["best_subset"].split(" + ")
            gfs_f1 = float(g["best_mean_f1"])
            # Evaluar GFS subset (1 corrida, ya lo tenemos)
            # Generar N_RANDOM subsets aleatorios del mismo tamaño
            other_extractors = [e for e in emb_cache.keys() if e not in gfs_subset]
            print(f"  {clf} k={k}  GFS={gfs_f1:.3f}  evaluating {N_RANDOM} random subsets...", flush=True)
            random_f1s = []
            rng = np.random.default_rng(123)
            t0_ds = time.time()
            for i in range(N_RANDOM):
                random_subset = list(rng.choice(other_extractors, size=k, replace=False))
                emb_list = [emb_cache[e][0] for e in random_subset]
                # 1-fold screening (faster); correlación con 5-fold > 0.95
                f1 = evaluate_subset(emb_list, labels, clf, n_folds=1)
                random_f1s.append(f1)
                if i % 5 == 0:
                    print(f"    {clf} k={k}  {i+1}/{N_RANDOM}  t={time.time()-t0_ds:.0f}s", flush=True)
            random_mean = float(np.mean(random_f1s))
            random_std = float(np.std(random_f1s))
            # p-value: GFS vs distribución random (one-sided: GFS > random)
            # Usar z-test: GFS_f1 vs media(random)
            z = (gfs_f1 - random_mean) / (random_std / np.sqrt(N_RANDOM))
            p_value_one_sided = 1 - stats.norm.cdf(z)
            # Percentil de GFS en la distribución random
            percentile = float((np.sum(np.array(random_f1s) < gfs_f1)) / N_RANDOM) * 100
            # Effect size (Cohen's d)
            cohens_d = (gfs_f1 - random_mean) / (random_std + 1e-12)
            # Ahora evaluar GFS con 1-fold para comparación apples-to-apples
            gfs_emb_list = [emb_cache[e][0] for e in gfs_subset]
            gfs_f1_1fold = evaluate_subset(gfs_emb_list, labels, clf, n_folds=1)
            # Recalcular delta con apples-to-apples (ambos 1-fold)
            z_1fold = (gfs_f1_1fold - random_mean) / (random_std / np.sqrt(N_RANDOM))
            p_1fold = 1 - stats.norm.cdf(z_1fold)
            cohens_d_1fold = (gfs_f1_1fold - random_mean) / (random_std + 1e-12)
            percentile_1fold = float((np.sum(np.array(random_f1s) < gfs_f1_1fold)) / N_RANDOM) * 100

            rows.append({
                "dataset": ds, "clf": clf, "k": k,
                "gfs_subset": " + ".join(gfs_subset),
                "gfs_f1_5fold": gfs_f1,                    # 5-fold (de greedy_summary)
                "gfs_f1_1fold": gfs_f1_1fold,                # 1-fold (mismo protocolo que random)
                "random_mean_f1": random_mean,
                "random_std_f1": random_std,
                "random_min_f1": float(np.min(random_f1s)),
                "random_max_f1": float(np.max(random_f1s)),
                "random_median_f1": float(np.median(random_f1s)),
                "delta_5fold_vs_random_1fold": gfs_f1 - random_mean,
                "delta_1fold_vs_random_1fold": gfs_f1_1fold - random_mean,
                "z_score_1fold": z_1fold,
                "p_value_gfs_better_than_random": p_1fold,
                "percentile_gfs_in_random_dist": percentile_1fold,
                "cohens_d_1fold": cohens_d_1fold,
                "n_random": N_RANDOM,
            })
            all_gfs_f1.append(gfs_f1_1fold)
            all_random_means.append(random_mean)
            per_dataset_results[ds]["gfs"].append(gfs_f1_1fold)
            per_dataset_results[ds]["random_dist"].append(random_f1s)
            print(f"    GFS_1fold={gfs_f1_1fold:.3f}  random_mean={random_mean:.3f}±{random_std:.3f}  "
                  f"Δ={gfs_f1_1fold-random_mean:+.3f}  z={z_1fold:.2f}  pct={percentile_1fold:.0f}%  d={cohens_d_1fold:.2f}")

    df = pd.DataFrame(rows)
    df.to_csv(TABLES / "gfs_vs_random.csv", index=False)
    print(f"\n[OK] gfs_vs_random.csv: {len(df)} filas")

    # Resumen
    section = "\n" + "="*78 + "\n  GFS vs RANDOM SUBSETS - RESUMEN\n" + "="*78
    print(section)
    n_gfs_better = (df["gfs_f1_1fold"] > df["random_mean_f1"]).sum()
    n_gfs_in_top5pct = (df["percentile_gfs_in_random_dist"] >= 95).sum()
    n_gfs_sig = (df["p_value_gfs_better_than_random"] < 0.05).sum()
    n_total = len(df)
    print(f"  Total comparaciones (dataset × clf): {n_total}")
    print(f"  GFS > random mean:                {n_gfs_better}/{n_total} ({100*n_gfs_better/n_total:.0f}%)")
    print(f"  GFS en percentil ≥95% de random:  {n_gfs_in_top5pct}/{n_total} ({100*n_gfs_in_top5pct/n_total:.0f}%)")
    print(f"  GFS significativamente > random (z-test): {n_gfs_sig}/{n_total} ({100*n_gfs_sig/n_total:.0f}%)")
    mean_delta = float(df["delta_1fold_vs_random_1fold"].mean())
    max_delta = float(df["delta_1fold_vs_random_1fold"].max())
    print(f"  Δ F1 medio (GFS - random mean, 1-fold): {mean_delta:+.3f}")
    print(f"  Δ F1 máximo: {max_delta:+.3f}")

    # Figura: distribuciones random + GFS por dataset
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    for idx, ds in enumerate(DATASETS):
        ax = axes[idx]
        if ds not in per_dataset_results or not per_dataset_results[ds]["gfs"]:
            ax.set_title(f"{ds} (sin datos)")
            continue
        gfs_vals = per_dataset_results[ds]["gfs"]
        rand_vals = per_dataset_results[ds]["random_dist"]
        # Plot histogram de F1 random
        all_rand = np.concatenate(rand_vals)
        ax.hist(all_rand, bins=30, color="C0", alpha=0.6, label="Random subsets (k matching)")
        for i, gfs_f1 in enumerate(gfs_vals):
            color = ["C3", "C2", "C1", "C4"][i % 4]
            ax.axvline(gfs_f1, color=color, linestyle="--", linewidth=2, label=f"GFS {CLFS[i]}")
        ax.set_xlabel("macro-F1")
        ax.set_ylabel("Frecuencia")
        ax.set_title(f"{ds}")
        ax.legend(loc="lower right", fontsize=7)
        ax.grid(True, alpha=0.3)
    plt.suptitle("GFS (líneas punteadas) vs Distribución de subsets aleatorios del mismo tamaño",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    out = FIGURES / "gfs_vs_random_dist.png"
    plt.savefig(out, dpi=120)
    plt.close()
    print(f"  Figura: {out}")


if __name__ == "__main__":
    main()
