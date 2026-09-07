"""Compromiso de GFS frente a concatenar todos los bloques."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd

from figure_quality import INK, MUTED, publication_style


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent / "figures" / "pareto_desempeno_dimension.pdf"


def paired_summary():
    paths = [
        ROOT / "results/confirmatory/nested_fold_results.csv",
        ROOT / "results/extensions/outex13_official1360/nested_fold_results.csv",
    ]
    data = pd.concat((pd.read_csv(p) for p in paths), ignore_index=True)
    data["dataset"] = data["dataset"].replace({"Outex13Official1360": "Outex"})
    keys = ["dataset", "classifier", "seed", "outer_fold"]
    gfs = data[data.method == "gfs"][keys + ["macro_f1", "dimensions"]]
    full = data[data.method == "full_concat"][keys + ["macro_f1", "dimensions"]]
    paired = gfs.merge(full, on=keys, suffixes=("_gfs", "_full"), validate="one_to_one")
    paired["delta_f1"] = paired.macro_f1_gfs - paired.macro_f1_full
    paired["reduction"] = 100 * (1 - paired.dimensions_gfs / paired.dimensions_full)
    return (
        paired.groupby(["dataset", "classifier"], as_index=False)
        .agg(reduction=("reduction", "mean"), delta=("delta_f1", "mean"),
             delta_sd=("delta_f1", "std"))
        .fillna({"delta_sd": 0.0})
    )


def main():
    publication_style()
    summary = paired_summary()
    colors = {"DTD": "#0072B2", "FMD": "#D55E00", "CUReT": "#009E73", "Outex": "#8E6BBE"}
    markers = {"svm": "o", "resmlp": "D"}
    offsets = {
        ("DTD", "svm"): (7, 7), ("DTD", "resmlp"): (-64, 12),
        ("FMD", "svm"): (-62, -17), ("FMD", "resmlp"): (-67, 10),
        ("CUReT", "svm"): (7, 10), ("CUReT", "resmlp"): (7, -13),
        ("Outex", "svm"): (7, 7), ("Outex", "resmlp"): (7, -13),
    }

    fig, ax = plt.subplots(figsize=(6.9, 3.85))
    ax.axhspan(-0.01, 0.01, color="#E8EEF4", zorder=0)
    ax.axhline(0, color="#52616B", linewidth=0.9, zorder=1)
    for row in summary.itertuples():
        ax.errorbar(row.reduction, row.delta, yerr=row.delta_sd,
                    marker=markers[row.classifier], markersize=7.0,
                    color=colors[row.dataset], markeredgecolor="white",
                    markeredgewidth=0.7, capsize=2.5, elinewidth=0.9,
                    linestyle="none", zorder=3)
        dx, dy = offsets[(row.dataset, row.classifier)]
        ax.annotate(f"{row.dataset}–{'SVM' if row.classifier == 'svm' else 'ResMLP'}",
                    (row.reduction, row.delta), xytext=(dx, dy), textcoords="offset points",
                    fontsize=7.8, color=INK)

    ax.text(0.985, 0.93, "GFS mejora", transform=ax.transAxes, ha="right", va="center",
            fontsize=8.2, fontweight="bold", color="#20705A")
    ax.text(0.985, 0.08, "Completa mejora", transform=ax.transAxes, ha="right", va="center",
            fontsize=8.2, fontweight="bold", color="#9B3158")
    ax.text(0.015, 0.505, "margen práctico ±0,01", transform=ax.transAxes, ha="left", va="bottom",
            fontsize=7.5, color=MUTED)
    ax.set_xlabel("Reducción dimensional de GFS respecto de la concatenación completa (%)")
    ax.set_ylabel(r"$\Delta$ macro-F1 (GFS $-$ completa)")
    ax.grid(axis="both", color="#D9E2EC", linewidth=0.55, alpha=0.85)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.margins(x=0.12, y=0.22)

    handles = [Line2D([0], [0], marker="o", linestyle="none", color=INK,
                      markerfacecolor=INK, markersize=6, label="SVM lineal"),
               Line2D([0], [0], marker="D", linestyle="none", color=INK,
                      markerfacecolor=INK, markersize=6, label="ResMLP")]
    ax.legend(handles=handles, loc="upper left", frameon=False, ncol=2,
              columnspacing=1.4, handletextpad=0.45)
    fig.tight_layout(pad=0.7)
    fig.savefig(OUT, bbox_inches="tight", pad_inches=0.04)
    fig.savefig(OUT.with_suffix(".png"), dpi=220, bbox_inches="tight", pad_inches=0.04)


if __name__ == "__main__":
    main()
