"""Figura 2: algoritmo GFS con bucle y regla de parada explícitos."""

from pathlib import Path

import matplotlib.pyplot as plt

from figure_quality import AMBER, BLUE, Diagram, GRAY, INK, MUTED, TEAL, publication_style


OUT = Path(__file__).parent / "figures" / "gfs_pasos.pdf"


def main():
    publication_style()
    fig, ax = plt.subplots(figsize=(6.9, 3.75))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.4)
    ax.axis("off")
    d = Diagram(ax)

    d.box(0.35, 2.15, 1.50, 1.40, "Subconjunto\nactual\n$S_{t-1}$", BLUE,
          fontsize=8.5, name="subconjunto")
    d.box(2.20, 1.65, 2.55, 2.40,
          "Evaluar candidatos\n\n" + r"Para cada $j\notin S_{t-1}$:" + "\n" +
          r"concatenar $S_{t-1}\cup\{j\}$" + "\ny validar en 4 folds",
          AMBER, fontsize=8.1, name="candidatos")
    d.box(5.10, 1.95, 1.95, 1.80,
          "Elegir $j_t$\n\nMayor macro-F1\nmedia interna",
          TEAL, fontsize=8.4, name="eleccion")
    d.box(7.55, 2.15, 1.75, 1.40,
          "Actualizar\n\n" + r"$S_t=S_{t-1}\cup\{j_t\}$",
          BLUE, fontsize=8.4, name="actualizacion")

    d.arrow((1.86, 2.85), (2.19, 2.85))
    d.arrow((4.76, 2.85), (5.09, 2.85))
    d.arrow((7.06, 2.85), (7.54, 2.85))

    # El retorno expresa la iteración; la salida inferior expresa la parada.
    d.arrow((8.42, 3.56), (3.50, 3.98), connectionstyle="arc3,rad=0.22", dashed=True)
    ax.text(6.02, 4.43, "si continúa la búsqueda", ha="center", va="center",
            fontsize=8.0, color=MUTED)

    d.box(2.65, 0.18, 4.70, 1.08,
          "Parar si $k=8$ o si hay dos mejoras\nconsecutivas $<0{,}001$\nSalida: mejor paso histórico $S^*$",
          GRAY, fontsize=8.1, name="parada")
    d.arrow((6.08, 1.94), (5.55, 1.17))
    ax.text(6.50, 1.42, "si se detiene", ha="center", va="center", fontsize=8.0, color=MUTED)

    ax.text(5.0, 5.02,
            "El test externo no interviene en candidatos, puntuaciones ni parada.",
            ha="center", va="center", fontsize=8.4, fontweight="bold", color=INK)

    d.validate(fig)
    fig.savefig(OUT, bbox_inches="tight", pad_inches=0.04)


if __name__ == "__main__":
    main()
