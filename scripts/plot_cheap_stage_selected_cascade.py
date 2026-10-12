#!/usr/bin/env python3
"""Generación de Figuras de Publicación para la Cascada Adaptativa Costo-Consciente.

Genera tres figuras clave para el manuscrito y la defensa de tesis:
1. `pareto_frontier_adaptive_cascade`: Frontera de Pareto (Macro-F1 vs costo proyectado en ms)
2. `cascade_routing_efficiency`: Eficiencia de enrutamiento (% resuelto en Etapa 1 vs Etapa 2)
3. `multidataset_speedup_accuracy`: Comparativa de ganancia en velocidad y preservación de F1
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns

REPO = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO / "results/exploratory/topk_cascade/cheap_stage_selected_primary22"
LEDGER_CSV = REPO / "results/exploratory/fsc_tex/CANONICAL_22_REFERENCE_LEDGER.csv"
OUTPUT_DIR = REPO / "paper/figures"

DATASET_ORDER = [
    "DTD",
    "FMD",
    "CUReT",
    "Outex13Official1360",
    "SoilOriginal",
    "KTHTIPS2b",
]

PRETTY_NAMES = {
    "DTD": "DTD",
    "FMD": "FMD",
    "CUReT": "CUReT",
    "Outex13Official1360": "Outex-13",
    "SoilOriginal": "Soil",
    "KTHTIPS2b": "KTH-TIPS-2b (Top-k previo)",
}

# Estilo profesional de publicación
sns.set_theme(style="whitegrid", font="sans-serif")
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def plot_pareto_frontier(rows: pd.DataFrame, out_dir: Path) -> None:
    """Grafica la frontera de Pareto precisión vs latencia comparando las estrategias."""
    agg = rows.groupby("dataset")[["new_f1", "resnet_f1", "topk_f1", "new_ms", "resnet_ms", "topk_ms"]].mean()

    fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    axes = axes.flatten()

    colors = {
        "Adaptive Cascade": "#1f77b4",  # Azul fuerte
        "ResNet-50 Cascade": "#ff7f0e",  # Naranja
        "Canonical Top-k 22": "#2ca02c",  # Verde
    }
    markers = {
        "Adaptive Cascade": "o",
        "ResNet-50 Cascade": "s",
        "Canonical Top-k 22": "^",
    }

    for idx, ds in enumerate(DATASET_ORDER):
        ax = axes[idx]
        d_sub = agg.loc[ds]

        # Puntos
        p_adapt = (d_sub["new_ms"], d_sub["new_f1"])
        p_resnet = (d_sub["resnet_ms"], d_sub["resnet_f1"])
        p_topk = (d_sub["topk_ms"], d_sub["topk_f1"])

        ax.scatter(*p_adapt, color=colors["Adaptive Cascade"], marker=markers["Adaptive Cascade"], s=130, label="Cascada Adaptativa", zorder=5)
        ax.scatter(*p_resnet, color=colors["ResNet-50 Cascade"], marker=markers["ResNet-50 Cascade"], s=110, label="Cascada ResNet-50", zorder=4)
        ax.scatter(*p_topk, color=colors["Canonical Top-k 22"], marker=markers["Canonical Top-k 22"], s=110, label="Top-k de origen", zorder=4)

        # Flecha de aceleración desde Top-k hasta Adaptativa
        ax.annotate(
            "",
            xy=p_adapt,
            xytext=p_topk,
            arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=1.8, ls="--", alpha=0.8),
        )
        ahorro = (1.0 - d_sub["new_ms"] / d_sub["topk_ms"]) * 100.0
        ax.text(
            0.5,
            0.10,
            f"-{ahorro:.1f}% costo proyectado",
            transform=ax.transAxes,
            color="#1f77b4",
            fontweight="bold",
            fontsize=9.5,
            ha="center",
        )

        ax.set_title(PRETTY_NAMES.get(ds, ds), fontweight="bold")
        ax.set_xlabel("Costo proyectado medio (ms)")
        ax.set_ylabel("Macro-F1")

        # Margen dinámico
        f1_vals = [p_adapt[1], p_resnet[1], p_topk[1]]
        ax.set_ylim(max(0, min(f1_vals) - 0.015), min(1, max(f1_vals) + 0.012))

    # Leyenda única
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.05), ncol=3, frameon=True, fontsize=12)

    for ext in ("pdf", "png"):
        p = out_dir / f"pareto_frontier_adaptive_cascade.{ext}"
        fig.savefig(p, dpi=300, bbox_inches="tight")
        print(f"Guardado: {p}")
    plt.close(fig)


def plot_routing_efficiency(res_dir: Path, out_dir: Path) -> None:
    """Unweighted condition means; classify direct Top-k separately from escalation."""
    by_ds = {}
    for path in res_dir.glob("*_result.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        selected = data["selected_cheap_stage"]
        if selected["route"] == "topk_direct":
            fractions = (0.0, 0.0, 1.0)
        else:
            frac = selected["request_fraction"]
            fractions = (1.0 - frac, frac, 0.0)
        by_ds.setdefault(data["dataset"], []).append(fractions)
    values = np.array([np.mean(by_ds[ds], axis=0) * 100 for ds in DATASET_ORDER])
    fig, ax = plt.subplots(figsize=(11, 6), constrained_layout=True)
    y = np.arange(len(DATASET_ORDER))
    left = np.zeros(len(y))
    for index, (label, color) in enumerate([
        ("Salida económica (no implica acierto)", "#2ca02c"),
        ("Escalamiento a Top-k", "#d62728"),
        ("Top-k directo, sin etapa económica", "#7f7f7f"),
    ]):
        width = values[:, index]
        ax.barh(y, width, 0.55, left=left, label=label, color=color, alpha=0.85)
        for j, v in enumerate(width):
            if v > 10:
                ax.text(left[j] + v/2, j, f"{v:.1f}%", ha="center", va="center", color="white")
        left += width
    ax.set_yticks(y, [PRETTY_NAMES[d] for d in DATASET_ORDER])
    ax.set_xlabel("Fracción de test simulada; media por condición (%)")
    ax.set_title("Rutas seleccionadas sobre embeddings")
    ax.set_xlim(0, 100)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=1)
    for ext in ("pdf", "png"):
        fig.savefig(out_dir / f"cascade_routing_efficiency.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_speedup_accuracy_bars(rows: pd.DataFrame, out_dir: Path) -> None:
    """Grafica la aceleración (Speedup X) y delta F1 frente a Top-k de origen."""
    agg = rows.groupby("dataset")[["new_f1", "topk_f1", "new_ms", "topk_ms"]].mean()

    labels = [PRETTY_NAMES[d] for d in DATASET_ORDER]
    speedups = [agg.loc[d, "topk_ms"] / agg.loc[d, "new_ms"] for d in DATASET_ORDER]
    delta_f1s = [(agg.loc[d, "new_f1"] - agg.loc[d, "topk_f1"]) * 100.0 for d in DATASET_ORDER]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)

    # Panel 1: Factor de Aceleración
    colors_spd = ["#1f77b4" if s > 1.0 else "#7f7f7f" for s in speedups]
    bars1 = ax1.bar(labels, speedups, color=colors_spd, width=0.55, alpha=0.9)
    ax1.axhline(1.0, color="gray", linestyle="--", linewidth=1.2)
    ax1.set_ylabel("Razón de costos proyectados", fontweight="bold")
    ax1.set_title("Costo relativo: Top-k de origen / cascada", fontweight="bold")
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, f"{yval:.2f}x", ha="center", va="bottom", fontweight="bold")
    ax1.set_ylim(0, max(speedups) + 0.8)
    ax1.set_xticks(range(len(labels)))
    ax1.set_xticklabels(labels, rotation=20, ha="right", fontweight="bold")

    # Panel 2: Delta Macro-F1 (puntos porcentuales)
    colors_f1 = ["#2ca02c" if d >= 0 else "#d62728" for d in delta_f1s]
    bars2 = ax2.bar(labels, delta_f1s, color=colors_f1, width=0.55, alpha=0.9)
    ax2.axhline(0.0, color="black", linestyle="-", linewidth=1.0)
    ax2.set_ylabel(r"$\Delta$ Macro-F1 (puntos porcentuales)", fontweight="bold")
    ax2.set_title("Cambio de Macro-F1 frente a Top-k de origen", fontweight="bold")
    for bar in bars2:
        yval = bar.get_height()
        offset = 0.06 if yval >= 0 else -0.15
        ax2.text(bar.get_x() + bar.get_width() / 2, yval + offset, f"{yval:+.2f} pp", ha="center", va="bottom", fontweight="bold")
    ax2.set_ylim(min(delta_f1s) - 0.4, max(delta_f1s) + 0.4)
    ax2.set_xticks(range(len(labels)))
    ax2.set_xticklabels(labels, rotation=20, ha="right", fontweight="bold")

    for ext in ("pdf", "png"):
        p = out_dir / f"multidataset_speedup_accuracy.{ext}"
        fig.savefig(p, dpi=300, bbox_inches="tight")
        print(f"Guardado: {p}")
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows_path = RESULTS_DIR / "rows.csv"
    if not rows_path.exists():
        raise FileNotFoundError(f"No se encuentra {rows_path}")

    rows = pd.read_csv(rows_path)
    print(f"Generando figuras en: {OUTPUT_DIR}")

    plot_pareto_frontier(rows, OUTPUT_DIR)
    plot_routing_efficiency(RESULTS_DIR, OUTPUT_DIR)
    plot_speedup_accuracy_bars(rows, OUTPUT_DIR)

    print("\n¡Todas las figuras fueron generadas exitosamente!")


if __name__ == "__main__":
    main()
