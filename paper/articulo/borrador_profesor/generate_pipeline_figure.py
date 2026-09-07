"""Figura 1: pipeline completo a tamaño editorial real."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from figure_quality import ACCENT, AMBER, BLUE, Diagram, GRAY, INK, MUTED, TEAL, publication_style


OUT = Path(__file__).parent / "figures" / "pipeline.pdf"


def main():
    publication_style()
    fig, ax = plt.subplots(figsize=(6.9, 3.55))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    d = Diagram(ax)

    # Entrada: una textura simbólica, sin pretender pertenecer a un dataset concreto.
    palette = ["#176B87", "#64AFC3", "#DCEAF7", "#E7A24B"]
    for r in range(6):
        for c in range(6):
            ax.add_patch(
                Rectangle(
                    (0.28 + c * 0.105, 2.16 + r * 0.105),
                    0.099,
                    0.099,
                    facecolor=palette[(2 * r + c) % len(palette)],
                    edgecolor="white",
                    linewidth=0.25,
                )
            )
    ax.add_patch(Rectangle((0.28, 2.16), 0.63, 0.63, fill=False, edgecolor=INK, linewidth=0.8))
    ax.text(0.595, 1.86, "imagen $x_i$", ha="center", va="center", fontsize=8.5, color=INK)

    # La biblioteca se abre en familias porque su heterogeneidad es parte de la hipótesis.
    d.box(1.28, 1.35, 2.28, 2.45, "", BLUE, name="biblioteca")
    ax.text(2.42, 3.57, "Biblioteca congelada", ha="center", va="center", fontsize=8.0,
            fontweight="bold", color=INK)
    ax.text(2.42, 3.34, "20 bloques", ha="center", va="center", fontsize=7.8,
            fontweight="bold", color=INK)
    families = [
        ("Clásicos", "5", "#5B8DB8"),
        ("CNN", "6", "#E69F00"),
        ("Transformers", "4", "#8E6BBE"),
        ("Autoenc. / VL", "5", "#169C83"),
    ]
    for idx, (name, count, color) in enumerate(families):
        y = 3.05 - idx * 0.43
        ax.add_patch(Rectangle((1.48, y - 0.13), 0.12, 0.26, facecolor=color, edgecolor="none"))
        ax.text(1.70, y, name, ha="left", va="center", fontsize=7.7, color=INK)
        ax.text(3.34, y, count, ha="right", va="center", fontsize=8.1, fontweight="bold", color=INK)

    d.box(3.72, 1.70, 1.72, 1.75, "Normalización\n$L_2$ por bloque", GRAY,
          fontsize=8.5, name="normalizacion")
    d.box(5.72, 1.30, 2.18, 2.55, "Construcción de $S$\n\nIndividual\nCompleta\nGFS / top-$k$\nFamilia homogénea",
          AMBER, fontsize=8.1, name="composicion")
    d.box(8.30, 1.70, 1.45, 1.75, "Clasificador\n\nSVM lineal\no ResMLP", TEAL,
          fontsize=8.2, name="clasificador")

    d.arrow((0.95, 2.48), (1.34, 2.48))
    d.arrow((3.57, 2.48), (3.71, 2.48))
    d.arrow((5.45, 2.48), (5.71, 2.48))
    d.arrow((7.91, 2.48), (8.29, 2.48))
    d.arrow((9.76, 2.48), (9.96, 2.48))
    ax.text(9.72, 1.45, r"clase $\hat y_i$", ha="center", va="center", fontsize=8.5,
            fontweight="bold", color=ACCENT)

    ax.text(5.0, 0.62,
            "La selección usa sólo el entrenamiento externo; el test se reserva para medir macro-F1.",
            ha="center", va="center", fontsize=8.2, color=MUTED)

    d.validate(fig)
    fig.savefig(OUT, bbox_inches="tight", pad_inches=0.04)


if __name__ == "__main__":
    main()
