"""
generate_figures.py
===================
Genera las figuras finales para el paper v2:
  - saturation curves (5 datasets)
  - GFS paths (5 datasets)
  - heatmap (extractor × dataset) de F1
  - confusion matrices
  - barplot comparativo: linear vs GFS por dataset
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

TABLES = Path("results/tables")
FIGURES = Path("results/figures")
FIGURES.mkdir(parents=True, exist_ok=True)

DATASETS = ["DTD", "FMD", "KTH-TIPS2-b", "VisTex"]  # Outex runs only through the official extension protocol


def fig_heatmap_linear():
    """Heatmap F1 por (extractor, dataset) con linear probing SVM."""
    f = TABLES / "baseline_summary.csv"
    if not f.exists():
        print(f"  [SKIP] {f} no existe")
        return
    df = pd.read_csv(f)
    df = df[df["clf"] == "svm"]
    pivot = df.pivot_table(index="extractor", columns="dataset", values="mean_f1")
    # Ordenar por F1 promedio
    pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index]
    fig, ax = plt.subplots(figsize=(10, 10))
    sns.heatmap(pivot, annot=True, fmt=".3f", cmap="viridis", ax=ax, cbar_kws={"label": "F1 macro"})
    ax.set_title("F1 macro (linear probing, SVM) por extractor × dataset", fontsize=14)
    ax.set_xlabel("Dataset")
    ax.set_ylabel("Extractor")
    plt.xticks(rotation=30, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    out = FIGURES / "heatmap_extractors_datasets_v2.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {out}")


def fig_comparison_bar():
    """Barplot: linear vs GFS por dataset."""
    linear = pd.read_csv(TABLES / "baseline_summary.csv")
    linear = linear[linear["clf"] == "svm"]
    linear_best = linear.loc[linear.groupby("dataset")["mean_f1"].idxmax()][["dataset", "extractor", "mean_f1"]]
    linear_best = linear_best.set_index("dataset")["mean_f1"]

    gfs = pd.read_csv(TABLES / "greedy_summary.csv")
    gfs_best = gfs.loc[gfs.groupby("dataset")["f1"].idxmax()][["dataset", "f1"]]
    gfs_best = gfs_best.set_index("dataset")["f1"]

    # Align datasets
    common = [ds for ds in linear_best.index if ds in gfs_best.index and ds != "GTOS-Mobile"]
    linear_vals = [linear_best[ds] for ds in common]
    gfs_vals = [gfs_best[ds] for ds in common]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(common))
    width = 0.35
    ax.bar(x - width/2, linear_vals, width, label="Linear probing (svm)", color="steelblue")
    ax.bar(x + width/2, gfs_vals, width, label="GFS concat (svm)", color="darkorange")
    ax.set_xticks(x)
    ax.set_xticklabels(common, rotation=20, ha="right")
    ax.set_ylabel("F1 macro")
    ax.set_title("Linear probing vs GFS: mejor F1 por dataset", fontsize=14)
    ax.legend()
    ax.set_ylim(0, 1.05)
    for i, (lv, gv) in enumerate(zip(linear_vals, gfs_vals)):
        ax.text(i - width/2, lv + 0.01, f"{lv:.3f}", ha="center", fontsize=9)
        ax.text(i + width/2, gv + 0.01, f"{gv:.3f}", ha="center", fontsize=9)
    plt.tight_layout()
    out = FIGURES / "comparison_linear_vs_gfs.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {out}")


def fig_gfs_paths():
    """Curvas GFS: F1 vs # extractores seleccionados por dataset."""
    f = TABLES / "greedy_summary.csv"
    if not f.exists():
        print(f"  [SKIP] {f} no existe")
        return
    df = pd.read_csv(f)
    datasets_with_gfs = df["dataset"].unique()
    n = len(datasets_with_gfs)
    cols = 3
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
    if rows == 1:
        axes = [axes] if cols == 1 else axes
    else:
        axes = axes.flatten()
    for i, ds in enumerate(datasets_with_gfs):
        sub = df[df["dataset"] == ds].sort_values("step")
        if len(sub) == 0:
            continue
        ax = axes[i]
        ax.plot(sub["step"], sub["f1"], "o-", color="darkorange", linewidth=2, markersize=8)
        ax.set_xlabel("# extractores seleccionados")
        ax.set_ylabel("F1 macro (svm)")
        ax.set_title(f"GFS: {ds}", fontsize=11)
        ax.grid(True, alpha=0.3)
        # Marcar el mejor
        best_step = sub.loc[sub["f1"].idxmax(), "step"]
        best_f1 = sub["f1"].max()
        ax.axhline(best_f1, linestyle="--", color="gray", alpha=0.5)
        ax.annotate(f"max={best_f1:.3f}\n(step {int(best_step)})",
                    xy=(best_step, best_f1), xytext=(0.5, 0.95),
                    textcoords="axes fraction", fontsize=9,
                    ha="left", va="top",
                    bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5))
    # Hide extra axes
    for j in range(i+1, len(axes)):
        axes[j].set_visible(False)
    plt.suptitle("Greedy Forward Selection paths", fontsize=14, y=1.02)
    plt.tight_layout()
    out = FIGURES / "gfs_paths_all.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {out}")


def fig_finetune_comparison():
    """Grouped bar: linear vs LoRA vs Last por dataset."""
    f = TABLES / "finetune_summary.csv"
    if not f.exists():
        print(f"  [SKIP] {f} no existe")
        return
    df = pd.read_csv(f)
    # Pivot: dataset × strategy → F1
    pivot = df.pivot_table(index="dataset", columns="strategy", values="mean_f1")
    # Add linear probing for comparison
    linear = pd.read_csv(TABLES / "baseline_summary.csv")
    linear = linear[linear["clf"] == "svm"]
    linear_best = linear.loc[linear.groupby("dataset")["mean_f1"].idxmax()][["dataset", "mean_f1"]]
    linear_best = linear_best.set_index("dataset")["mean_f1"]
    pivot["linear"] = linear_best

    # Reorder
    pivot = pivot[["linear", "lora", "last"]]
    # Drop GTOS-Mobile for visualization clarity
    pivot = pivot.drop("GTOS-Mobile", errors="ignore")

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(pivot))
    width = 0.25
    ax.bar(x - width, pivot["linear"], width, label="Linear", color="steelblue")
    ax.bar(x, pivot["lora"], width, label="LoRA r=8", color="seagreen")
    ax.bar(x + width, pivot["last"], width, label="Last-block", color="darkorange")
    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index, rotation=20, ha="right")
    ax.set_ylabel("F1 macro")
    ax.set_title("Linear probing vs Fine-tuning (DINOv2-B)", fontsize=14)
    ax.legend()
    ax.set_ylim(0, 1.05)
    for i, ds in enumerate(pivot.index):
        for j, col in enumerate(["linear", "lora", "last"]):
            v = pivot.loc[ds, col]
            if not pd.isna(v):
                ax.text(i + (j-1)*width, v + 0.005, f"{v:.3f}", ha="center", fontsize=8)
    plt.tight_layout()
    out = FIGURES / "finetune_comparison.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {out}")


def main():
    print("Generando figuras v2...")
    fig_heatmap_linear()
    fig_comparison_bar()
    fig_gfs_paths()
    fig_finetune_comparison()
    print("Done.")


if __name__ == "__main__":
    main()
