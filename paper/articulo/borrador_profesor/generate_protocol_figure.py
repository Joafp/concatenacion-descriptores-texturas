"""Figura 3: protocolo anidado con frontera externa inequívoca."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

from figure_quality import AMBER, BLUE, Diagram, GRAY, INK, MUTED, ROSE, TEAL, publication_style


OUT = Path(__file__).parent / "figures" / "protocolo_anidado.pdf"


def main():
    publication_style()
    fig, ax = plt.subplots(figsize=(6.9, 4.25))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    d = Diagram(ax)

    # Marco exterior: una partición de evaluación completa.
    outer = FancyBboxPatch(
        (0.25, 0.45), 9.50, 5.25,
        boxstyle="round,pad=0.02,rounding_size=0.035",
        facecolor="white", edgecolor="#738395", linewidth=1.0, linestyle="--", zorder=0,
    )
    ax.add_patch(outer)
    ax.text(0.48, 5.42, "Partición externa", ha="left", va="center", fontsize=9.3,
            fontweight="bold", color=INK)

    d.box(0.70, 3.95, 5.70, 0.90,
          "Entrenamiento externo", BLUE, fontsize=9.0, weight="bold", name="train externo")
    d.box(7.05, 3.95, 2.15, 0.90,
          "Test externo\nreservado", ROSE, fontsize=8.8, weight="bold", name="test externo")
    ax.text(8.125, 3.63, "sin acceso durante la selección", ha="center", va="center",
            fontsize=7.8, color="#9B3158")

    # Folds internos visibles, con el fold de validación marcado por contorno.
    d.box(0.70, 1.25, 3.05, 1.85, "", GRAY, name="validacion interna")
    ax.text(2.225, 2.82, "Validación interna · 4 folds", ha="center", va="center",
            fontsize=8.4, fontweight="bold", color=INK)
    fold_colors = ["#C7DCEF", "#C7DCEF", "#C7DCEF", "#F0C98E"]
    for i, color in enumerate(fold_colors):
        ax.add_patch(Rectangle((0.98 + i * 0.55, 2.10), 0.44, 0.36,
                               facecolor=color, edgecolor=INK if i == 3 else "white",
                               linewidth=1.0 if i == 3 else 0.4))
        ax.text(1.20 + i * 0.55, 2.28, f"F{i+1}", ha="center", va="center", fontsize=7.3, color=INK)
    ax.text(2.225, 1.66, "selección y ajuste internos", ha="center", va="center",
            fontsize=7.7, color=MUTED)

    d.box(4.18, 1.50, 1.70, 1.35,
          "Estrategia\nelegida\n$S^*$", AMBER, fontsize=8.5, name="estrategia")
    d.box(6.35, 1.50, 2.00, 1.35,
          "Ajuste final\ncon todo el\nentrenamiento", TEAL, fontsize=8.3, name="ajuste final")

    d.arrow((3.76, 2.18), (4.17, 2.18))
    d.arrow((5.89, 2.18), (6.34, 2.18))
    d.arrow((7.35, 2.86), (7.35, 3.94))
    ax.text(8.62, 3.33, "una sola evaluación", ha="center", va="center", fontsize=7.7,
            color=INK)

    ax.text(5.0, 0.77,
            "Selección interna  →  ajuste final  →  evaluación externa",
            ha="center", va="center", fontsize=8.5, fontweight="bold", color=INK)

    d.validate(fig)
    fig.savefig(OUT, bbox_inches="tight", pad_inches=0.04)


if __name__ == "__main__":
    main()
