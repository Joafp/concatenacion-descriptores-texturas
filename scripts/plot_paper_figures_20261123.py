"""Plot archival results for the paper on direct and margin-gated Top-4."""
from argparse import ArgumentParser
from collections import defaultdict
from csv import DictReader
from pathlib import Path
from statistics import mean

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "results/analysis"
CURVES = ANALYSIS / "thesis_accuracy_primary_20261115_v3/curves.csv"
INNER = ROOT / "results/exploratory/k_sweep"
E1 = ANALYSIS / "top4_fixed_kth_completion_audit_20261115_v1/e1_complete_dataset_means.csv"
DATASETS = {
    "DTD": "DTD",
    "FMD": "FMD",
    "CUReT": "CUReT",
    "Outex13Official1360": "Outex",
    "SoilOriginal": "Soil",
    "KTHTIPS2b": "KTH-TIPS2-b",
}
DIRECT = "#1b416c"
MARGIN = "#087b76"
ALT = "#a14b18"
INK = "#1d2938"
GUIDE = "#ced9e3"


def rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(DictReader(stream))


def comma(value, places):
    return f"{value:.{places}f}".replace(".", ",").replace("-", "−")


def write_figure(fig, folder, name):
    fig.savefig(folder / f"{name}.pdf", facecolor="white")
    fig.savefig(folder / f"{name}.png", facecolor="white", dpi=250)
    plt.close(fig)


def plot_curves(folder):
    data = rows(CURVES)
    panels = {head: sorted((int(r["k"]), 100 * float(r["accuracy"]))
                           for r in data if r["classifier"] == head) for head in ("svm", "resmlp")}
    assert all([k for k, _ in values] == list(range(1, 22)) for values in panels.values())
    grouped = defaultdict(lambda: defaultdict(list))
    for file in sorted(INNER.glob("*/k_sweep_inner.csv")):
        for row in rows(file):
            assert row["classifier"] == "svm"
            grouped[int(row["k"])][row["dataset"]].append(float(row["inner_f1"]))
    assert set(grouped) == set(range(1, 22))
    assert all(set(dataset_rows) == set(DATASETS) and sum(map(len, dataset_rows.values())) == 47
               for dataset_rows in grouped.values())
    inner = [(k, 100 * mean(mean(values) for values in grouped[k].values())) for k in range(1, 22)]

    fig, (left, right) = plt.subplots(1, 2, figsize=(6.0, 2.62))
    fig.subplots_adjust(left=.106, right=.978, bottom=.207, top=.865, wspace=.38)
    for ax in (left, right):
        ax.set_xlim(.65, 21.35)
        ax.set_xticks([1, 4, 8, 12, 16, 21])
        ax.set_xlabel("Número de bloques ($k$)")
        ax.grid(axis="y", alpha=.77)
        ax.axvline(4, color="#677382", lw=1.0, ls=(0, (3, 2)), zorder=1)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: comma(v, 1)))

    for head, label, color, marker, dash in (
        ("svm", "SVM", DIRECT, "o", "-"),
        ("resmlp", "ResMLP", ALT, "s", "--"),
    ):
        x, y = zip(*panels[head])
        left.plot(x, y, label=label, color=color, marker=marker, ls=dash)
        left.plot(x[3], y[3], color=color, marker=marker, ls="none", ms=5.0,
                  mec="white", mew=.75, zorder=4)
    left.set_title("(a) Prueba externa", loc="left")
    left.set_ylabel("Accuracy media (%)")
    left.set_ylim(92.35, 95.35)
    left.set_yticks([92.5, 93.0, 93.5, 94.0, 94.5, 95.0])
    left.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="none", fontsize=7.3)

    x, y = zip(*inner)
    right.plot(x, y, color=DIRECT, marker="o")
    right.plot(x[3], y[3], color=DIRECT, marker="o", ms=5.0, mec="white", mew=.75, zorder=4)
    peak = max(inner, key=lambda t: t[1])
    right.annotate("Máximo en $k=6$", xy=peak, xytext=(10.5, 92.46),
                   ha="left", va="center", fontsize=7.1,
                   arrowprops={"arrowstyle": "-", "color": INK, "lw": .65})
    right.set_title("(b) Validación interna de SVM", loc="left")
    right.set_ylabel("Macro-F1 medio (%)")
    right.set_ylim(90.75, 92.61)
    right.set_yticks([91.0, 91.5, 92.0, 92.5])
    write_figure(fig, folder, "curva_k")


def plot_paired_e1(folder):
    data = {row["dataset"]: row for row in rows(E1)}
    assert set(data) == set(DATASETS)
    y = list(range(len(DATASETS)))
    delta = [100 * (float(data[d]["cascade_accuracy"]) - float(data[d]["direct_accuracy"])) for d in DATASETS]
    cost_direct = [float(data[d]["direct_projected_ms"]) for d in DATASETS]
    cost_margin = [float(data[d]["cascade_projected_ms"]) for d in DATASETS]

    fig, (left, right) = plt.subplots(1, 2, sharey=True, figsize=(6.0, 2.68),
                                      gridspec_kw={"width_ratios": [1, 1.18]})
    fig.subplots_adjust(left=.161, right=.977, bottom=.235, top=.86, wspace=.15)
    for ax in (left, right):
        ax.set_axisbelow(True)
        ax.grid(axis="x", alpha=.8)
        ax.set_ylim(len(DATASETS)-.45, -.55)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
    left.set_yticks(y, list(DATASETS.values()))
    left.set_title("(a) Cambio de accuracy", loc="left")
    left.axvline(0, color="#677382", lw=1.05, zorder=0)
    left.hlines(y, [min(0, d) for d in delta], [max(0, d) for d in delta], color=GUIDE, lw=1.4)
    left.scatter(delta, y, color=MARGIN, marker="D", s=18, zorder=3)
    left.set_xlim(-.348, .35)
    left.set_xticks([-.3, -.15, 0, .15, .3])
    left.xaxis.set_major_formatter(FuncFormatter(lambda v, _: "0" if not v else comma(v, 2)))
    left.set_xlabel("Margen − directo (pp)")

    right.set_title("(b) Costo proyectado", loc="left")
    right.hlines(y, cost_margin, cost_direct, color=GUIDE, lw=1.55)
    right.scatter(cost_direct, y, color=DIRECT, marker="o", s=20, label="Top-4 directo", zorder=3)
    right.scatter(cost_margin, y, color=MARGIN, marker="D", s=18, label="Cascada Top-4", zorder=3)
    right.set_xlim(0, 680)
    right.set_xticks([0, 150, 300, 450, 600])
    right.tick_params(axis="y", labelleft=False)
    right.set_xlabel("Milisegundos por imagen")
    right.legend(loc="upper center", bbox_to_anchor=(.50, -.252), ncol=2, frameon=False,
                 fontsize=6.9, borderaxespad=0, columnspacing=.9, handletextpad=.38)
    write_figure(fig, folder, "comparacion_pareada_e1")


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Folder for the figure PDFs and PNGs")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8,
        "axes.titlesize": 8.7, "axes.titleweight": "bold", "axes.labelsize": 7.7,
        "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#788494",
        "axes.linewidth": .75, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": INK, "ytick.color": INK, "xtick.labelsize": 7.1, "ytick.labelsize": 7.2,
        "grid.color": GUIDE, "grid.linewidth": .55, "lines.linewidth": 1.35,
        "lines.markersize": 2.5, "pdf.fonttype": 42,
    })
    plot_curves(args.output)
    plot_paired_e1(args.output)


if __name__ == "__main__":
    main()
