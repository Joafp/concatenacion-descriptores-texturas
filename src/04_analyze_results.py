"""
04_analyze_results.py
======================
Genera análisis consolidado y figuras para el Cap. 4.

Lee:
  - results/tables/baseline_{dataset}.csv
  - results/tables/concat_{dataset}.csv
  - results/tables/baseline_summary.csv
  - results/tables/concat_summary.csv

Genera:
  - results/figures/saturation_{dataset}.png  (1 por dataset, ya generadas por 03)
  - results/figures/heatmap_extractors_datasets.png  (matriz extractores vs datasets)
  - results/figures/improvement_bar.png  (mejora por concatenación, k=N vs k=1)
  - results/tables/final_summary.csv  (consolidado para el Cap. 4)
  - results/tables/best_per_dataset.csv  (mejor (extractor_subset, clf) por dataset)
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


TABLES_DIR = Path("results/tables")
FIGURES_DIR = Path("results/figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def load_all():
    concat = pd.concat([
        pd.read_csv(f) for f in TABLES_DIR.glob("concat_*.csv") if "summary" not in f.name
    ], ignore_index=True).copy()
    baseline = pd.concat([
        pd.read_csv(f) for f in TABLES_DIR.glob("baseline_*.csv") if "summary" not in f.name
    ], ignore_index=True).copy()
    return baseline, concat


def heatmap_extractors_datasets(baseline: pd.DataFrame, out_path: Path):
    """Heatmap: extractors (rows) × datasets (cols), color = mejor macro-F1."""
    best = baseline.loc[baseline.groupby(["dataset", "extractor"])["mean_f1"].idxmax()]
    pivot = best.pivot(index="extractor", columns="dataset", values="mean_f1")
    # Ordenar extractores por familia
    extractor_order = sorted(pivot.index, key=lambda e: (
        0 if e in ["lbp", "glcm", "gabor", "hog", "drlbp"] else
        1 if e in ["convnext_v2_t", "efficientnet_b0"] else
        2, e
    ))
    pivot = pivot.loc[extractor_order]
    # Ordenar datasets: texturas primero, médicos después
    ds_order = ["DTD", "FMD", "KTH-TIPS2", "HVD_glaucoma", "ocular_toxoplasmosis"]
    pivot = pivot[[d for d in ds_order if d in pivot.columns]]

    fig, ax = plt.subplots(figsize=(9, 5))
    im = ax.imshow(pivot.values, cmap="viridis", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=20, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    # Anotar cada celda
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                        color="white" if val < 0.5 else "black", fontsize=9)
    ax.set_title("Mejor macro-F1 por (extractor × dataset) — baseline individual")
    plt.colorbar(im, ax=ax, label="macro-F1")
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()
    print(f"  -> {out_path}")


def improvement_bar(concat: pd.DataFrame, out_path: Path):
    """Bar chart: mejora de k=N (concat completo) vs k=1 (mejor ViT solo) por dataset."""
    # El baseline (k=1) en concat es la primera fila por (dataset, clf)
    # k=N es la última fila
    improvements = []
    for dataset in concat["dataset"].unique():
        for clf in concat["clf"].unique():
            sub = concat[(concat["dataset"] == dataset) & (concat["clf"] == clf)].sort_values("k")
            if sub.empty:
                continue
            k1 = sub[sub["k"] == 1]["mean_f1"].max()
            kN = sub["mean_f1"].max()
            if pd.isna(k1) or pd.isna(kN):
                continue
            improvements.append({
                "dataset": dataset,
                "clf": clf,
                "k1_f1": k1,
                "kN_f1": kN,
                "delta": kN - k1,
            })
    df = pd.DataFrame(improvements)
    df.to_csv(TABLES_DIR / "improvement_summary.csv", index=False)

    # Plot: para cada dataset, el delta por clasificador
    fig, ax = plt.subplots(figsize=(10, 5))
    datasets = sorted(df["dataset"].unique())
    clfs = sorted(df["clf"].unique())
    x = np.arange(len(datasets))
    width = 0.25
    for i, clf in enumerate(clfs):
        sub = df[df["clf"] == clf].set_index("dataset").reindex(datasets)
        ax.bar(x + i * width, sub["delta"].values, width, label=clf)
    ax.set_xticks(x + width)
    ax.set_xticklabels(datasets, rotation=15, ha="right")
    ax.set_ylabel("Δ macro-F1 (k=N vs k=1)")
    ax.set_title("Mejora por concatenación progresiva (todos los extractores)")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()
    print(f"  -> {out_path}")
    return df


def best_per_dataset(concat: pd.DataFrame, baseline: pd.DataFrame, out_path: Path):
    """Para cada dataset, encuentra el mejor (k, extractors, clf) por macro-F1."""
    # Del concat
    best_concat = concat.loc[concat.groupby("dataset")["mean_f1"].idxmax()].copy()
    best_concat = best_concat[["dataset", "k", "extractors", "clf", "mean_f1", "std_f1", "dim"]]
    best_concat = best_concat.rename(columns={"mean_f1": "concat_f1", "std_f1": "concat_std", "dim": "concat_dim"})
    # Del baseline
    best_baseline = baseline.loc[baseline.groupby(["dataset"])["mean_f1"].idxmax()].copy()
    best_baseline = best_baseline[["dataset", "extractor", "clf", "mean_f1", "std_f1", "emb_dim"]]
    best_baseline = best_baseline.rename(columns={"mean_f1": "baseline_f1", "std_f1": "baseline_std", "emb_dim": "baseline_dim", "extractor": "baseline_extractor"})
    # Combinar
    merged = best_baseline.merge(best_concat, on="dataset", how="left")
    merged["delta"] = merged["concat_f1"] - merged["baseline_f1"]
    merged = merged.sort_values("delta", ascending=False)
    merged.to_csv(out_path, index=False)
    print(f"  -> {out_path}")
    return merged


def final_summary(baseline: pd.DataFrame, concat: pd.DataFrame, out_path: Path):
    """Tabla consolidada: todos los experimentos en formato largo."""
    # Renombrar columnas para consistencia
    base = baseline[["dataset", "extractor", "clf", "mean_f1", "std_f1", "emb_dim"]].copy()
    base["k"] = 1
    base["concat_dim"] = base["emb_dim"]
    base = base.rename(columns={"extractor": "extractors", "emb_dim": "single_dim"})
    base["extractors"] = base["extractors"].apply(lambda e: [e])
    con = concat[["dataset", "k", "extractors", "clf", "mean_f1", "std_f1", "dim"]].copy()
    con = con.rename(columns={"dim": "concat_dim"})
    con["single_dim"] = con["concat_dim"]
    all_df = pd.concat([base, con], ignore_index=True)
    all_df.to_csv(out_path, index=False)
    print(f"  -> {out_path}")


def main():
    print("Cargando resultados...")
    baseline, concat = load_all()
    print(f"  Baseline: {len(baseline)} filas, Concat: {len(concat)} filas\n")

    print("Generando figuras y tablas...")
    heatmap_extractors_datasets(baseline, FIGURES_DIR / "heatmap_extractors_datasets.png")
    print()
    improvement_bar(concat, FIGURES_DIR / "improvement_bar.png")
    print()
    best_per_dataset(concat, baseline, TABLES_DIR / "best_per_dataset.csv")
    print()
    final_summary(baseline, concat, TABLES_DIR / "final_summary.csv")

    print("\n=== Análisis completo ===")


if __name__ == "__main__":
    main()
