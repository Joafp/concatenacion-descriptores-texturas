"""Utilidades comunes y controles geométricos para figuras del manuscrito."""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib as mpl
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


INK = "#25364D"
MUTED = "#5B6878"
BLUE = "#DCEAF7"
TEAL = "#DDF1EC"
AMBER = "#F8ECD2"
ROSE = "#F7E3E8"
GRAY = "#F3F5F7"
ACCENT = "#176B87"


def publication_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 8.5,
            "axes.titlesize": 10,
            "figure.dpi": 300,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


@dataclass
class BoxText:
    patch: FancyBboxPatch
    text: mpl.text.Text
    name: str


class Diagram:
    def __init__(self, ax):
        self.ax = ax
        self.box_texts: list[BoxText] = []

    def box(self, x, y, w, h, label, face, *, fontsize=8.5, name="box", edge=INK, weight="normal"):
        patch = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.012,rounding_size=0.025",
            facecolor=face,
            edgecolor=edge,
            linewidth=0.9,
            zorder=2,
        )
        self.ax.add_patch(patch)
        text = self.ax.text(
            x + w / 2,
            y + h / 2,
            label,
            ha="center",
            va="center",
            fontsize=fontsize,
            fontweight=weight,
            color="#152536",
            linespacing=1.16,
            zorder=3,
        )
        self.box_texts.append(BoxText(patch, text, name))
        return patch

    def arrow(self, start, end, *, color=INK, style="-|>", connectionstyle="arc3", dashed=False):
        self.ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle=style,
                mutation_scale=10,
                linewidth=1.0,
                color=color,
                linestyle="--" if dashed else "-",
                connectionstyle=connectionstyle,
                shrinkA=3,
                shrinkB=3,
                zorder=4,
            )
        )

    def validate(self, fig, *, padding_px=3.0) -> None:
        """Falla si un texto no cabe en su caja o sale del lienzo."""
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        canvas = fig.bbox
        errors = []
        for item in self.box_texts:
            tb = item.text.get_window_extent(renderer=renderer)
            pb = item.patch.get_window_extent(renderer=renderer)
            if (
                tb.x0 < pb.x0 + padding_px
                or tb.x1 > pb.x1 - padding_px
                or tb.y0 < pb.y0 + padding_px
                or tb.y1 > pb.y1 - padding_px
            ):
                errors.append(f"texto fuera de caja: {item.name}")
        for text in self.ax.texts:
            tb = text.get_window_extent(renderer=renderer)
            if tb.x0 < canvas.x0 or tb.x1 > canvas.x1 or tb.y0 < canvas.y0 or tb.y1 > canvas.y1:
                errors.append(f"texto fuera del lienzo: {text.get_text()[:35]}")
        if errors:
            raise RuntimeError("; ".join(errors))
